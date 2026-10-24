"""Authentication / authorization (AUTH_MODE) against a running API; skipped when the API runs without it."""
import httpx
import pytest

from conftest import BASE_URL, auth_headers
from test_api import make_service


@pytest.fixture(scope="module")
def anonymous():
    with httpx.Client(base_url=BASE_URL, timeout=30) as c:
        yield c


@pytest.fixture(scope="module")
def secured(anonymous):
    try:
        r = anonymous.get("/service", params={"limit": 1})
    except httpx.TransportError:
        pytest.skip("API not reachable")
    if r.status_code != 401:
        pytest.skip("API runs without AUTH_MODE")
    return r.headers["WWW-Authenticate"].split()[0]  # Basic | Bearer


@pytest.fixture(scope="module")
def reader(secured):
    headers = auth_headers("reader")
    if not headers:
        pytest.skip("no reader credentials in the environment")
    with httpx.Client(base_url=BASE_URL, timeout=30, headers=headers) as c:
        yield c


def test_probes_stay_open(anonymous):
    assert anonymous.get("/livez").status_code == 200
    assert anonymous.get("/readyz").status_code == 200


def test_anonymous_is_rejected_with_a_challenge(anonymous, secured):
    for method, path in (("GET", "/service"), ("POST", "/service"), ("GET", "/hub/x"), ("POST", "/hub")):
        r = anonymous.request(method, path, json={})
        assert r.status_code == 401, (method, path)
        assert r.headers["WWW-Authenticate"].startswith(secured)
        assert r.json()["@type"] == "Error"


def test_garbage_credentials_are_rejected(anonymous, secured):
    header = "Basic " + "bm9ib2R5Ok5PUEU=" if secured == "Basic" else "Bearer not.a.jwt"
    assert anonymous.get("/service", headers={"Authorization": header}).status_code == 401


def test_writer_may_everything(client, secured):
    created = client.post("/service", json=make_service("auth", "aa:00", serviceType="Auth"))
    assert created.status_code == 201
    service_id = created.json()["id"]
    assert client.get(f"/service/{service_id}").status_code == 200
    assert client.delete(f"/service/{service_id}").status_code == 204


def test_reader_reads_but_does_not_write(client, reader):
    created = client.post("/service", json=make_service("auth", "aa:00", serviceType="Auth")).json()
    try:
        assert reader.get("/service", params={"limit": 1}).status_code in (200, 206)
        assert reader.get(f"/service/{created['id']}").status_code == 200
        assert reader.post("/service", json=make_service("auth", "aa:01", serviceType="Auth")).status_code == 403
        assert reader.patch(f"/service/{created['id']}", json={"name": "y"},
                            headers={"Content-Type": "application/merge-patch+json"}).status_code == 403
        assert reader.delete(f"/service/{created['id']}").status_code == 403
    finally:
        client.delete(f"/service/{created['id']}")
    r = client.get(f"/service/{created['id']}")
    assert r.status_code == 404  # deleted by the writer, not by the reader


def test_reader_may_subscribe_to_events(reader):
    r = reader.post("/hub", json={"callback": "http://127.0.0.1:9/never"})
    assert r.status_code == 201
    assert reader.delete(f"/hub/{r.json()['id']}").status_code == 204
