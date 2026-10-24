"""Event subscriptions (hub) and notifications against a running TMF638 API.

The test starts an HTTP listener; the API must be able to reach it under
TMF_CALLBACK_HOST (default 127.0.0.1 - set e.g. host.docker.internal when the
API runs in a container).
"""
import json
import os
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from test_api import MERGE, make_service

CALLBACK_HOST = os.environ.get("TMF_CALLBACK_HOST", "127.0.0.1")


class Listener:
    def __init__(self):
        self.received = []  # (path, event)
        self.lock = threading.Lock()
        listener = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                with listener.lock:
                    listener.received.append((self.path, json.loads(body)))
                self.send_response(204)
                self.end_headers()

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("0.0.0.0", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def callback(self, name):
        return f"http://{CALLBACK_HOST}:{self.server.server_port}/{name}"

    def events(self, name, count, timeout=10.0):
        """Events received by callback `name`; waits until there are `count` of them."""
        deadline = time.monotonic() + timeout
        while True:
            with self.lock:
                found = [(path, e) for path, e in self.received if path.startswith(f"/{name}/")]
            if len(found) >= count or time.monotonic() > deadline:
                return found
            time.sleep(0.05)


@pytest.fixture(scope="module")
def listener():
    listener = Listener()
    yield listener
    listener.server.shutdown()


@pytest.fixture
def hub(client):
    created = []

    def register(callback, query=None):
        body = {"callback": callback, **({"query": query} if query else {})}
        r = client.post("/hub", json=body)
        assert r.status_code == 201, r.text
        created.append(r.json()["id"])
        return r.json()

    yield register
    for hub_id in created:
        client.delete(f"/hub/{hub_id}")


def test_hub_lifecycle(client):
    r = client.post("/hub", json={"callback": "http://127.0.0.1:9/listener", "query": "eventType=ServiceCreateEvent"})
    assert r.status_code == 201, r.text
    hub = r.json()
    assert r.headers["Location"] == hub["href"]
    assert (hub["callback"], hub["query"], hub["@type"]) == ("http://127.0.0.1:9/listener", "eventType=ServiceCreateEvent", "Hub")
    assert client.get(f"/hub/{hub['id']}").json() == hub
    assert client.delete(f"/hub/{hub['id']}").status_code == 204
    assert client.get(f"/hub/{hub['id']}").status_code == 404
    assert client.delete(f"/hub/{hub['id']}").status_code == 404


@pytest.mark.parametrize("body", [{}, {"callback": "not-a-url"}, {"callback": "http://x", "query": "noequalsign"}])
def test_invalid_hub_is_bad_request(client, body):
    r = client.post("/hub", json=body)
    assert r.status_code == 400, r.text
    assert r.json()["@type"] == "Error"


def test_service_lifecycle_events(client, listener, hub):
    run = uuid.uuid4().hex[:12]
    name = f"all-{run}"
    hub(listener.callback(name), f"event.service.serviceType=Ev-{run}")

    service = client.post("/service", json=make_service(run, "e1", serviceType=f"Ev-{run}")).json()
    sid = service["id"]
    assert client.patch(f"/service/{sid}", json={"state": "suspended"}, headers=MERGE).status_code == 200
    assert client.patch(f"/service/{sid}", json={"description": "new"}, headers=MERGE).status_code == 200
    assert client.patch(f"/service/{sid}", json={"operatingStatus": "running"}, headers=MERGE).status_code == 200
    assert client.delete(f"/service/{sid}").status_code == 204

    received = listener.events(name, 5)
    assert [path for path, _ in received] == [
        f"/{name}/listener/serviceCreateEvent",
        f"/{name}/listener/serviceStateChangeEvent",
        f"/{name}/listener/serviceAttributeValueChangeEvent",
        f"/{name}/listener/serviceOperatingStatusChangeEvent",
        f"/{name}/listener/serviceDeleteEvent",
    ]
    for path, event in received:
        assert event["@type"] == event["eventType"]
        assert event["eventId"] and event["eventTime"]
        assert event["event"]["service"]["id"] == sid
    assert received[1][1]["event"]["service"]["state"] == "suspended"
    assert received[4][1]["event"]["service"]["operatingStatus"] == "running"  # last state of the deleted service


def test_hub_query_selects_event_types(client, listener, hub):
    run = uuid.uuid4().hex[:12]
    hub(listener.callback(f"del-{run}"), f"eventType=ServiceDeleteEvent,ServiceStateChangeEvent&event.service.serviceType=Ev-{run}")
    hub(listener.callback(f"other-{run}"), "event.service.serviceType=SomethingElse")

    sid = client.post("/service", json=make_service(run, "e2", serviceType=f"Ev-{run}")).json()["id"]
    client.patch(f"/service/{sid}", json={"description": "x"}, headers=MERGE)
    client.delete(f"/service/{sid}")

    assert [e["eventType"] for _, e in listener.events(f"del-{run}", 1)] == ["ServiceDeleteEvent"]
    assert listener.events(f"other-{run}", 1, timeout=0.5) == []


def test_no_events_after_hub_deletion(client, listener):
    run = uuid.uuid4().hex[:12]
    r = client.post("/hub", json={"callback": listener.callback(f"gone-{run}")})
    client.delete(f"/hub/{r.json()['id']}")
    sid = client.post("/service", json=make_service(run, "e3")).json()["id"]
    client.delete(f"/service/{sid}")
    assert listener.events(f"gone-{run}", 1, timeout=1.0) == []
