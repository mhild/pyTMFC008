"""Revision history (HISTORY_ENABLED) against a running API; backend-agnostic.

The tests that need history skip when the API runs without it (the disabled behaviour is tested separately).
"""
import uuid
from datetime import datetime, timedelta

import pytest

from test_api import MERGE, make_service


@pytest.fixture(scope="module")
def run_id():
    return uuid.uuid4().hex[:12]


@pytest.fixture(scope="module")
def history_enabled(client):
    r = client.get("/service", params={"includeHistory": "true", "limit": 1})
    return r.status_code in (200, 206)


@pytest.fixture
def enabled(history_enabled):
    if not history_enabled:
        pytest.skip("API runs without HISTORY_ENABLED")


def patch(client, service_id, body):
    r = client.patch(f"/service/{service_id}", json=body, headers=MERGE)
    assert r.status_code == 200, r.text
    return r.json()


def revisions(client, kind, **params):
    r = client.get("/service", params={"serviceType": kind, "includeHistory": "true", **params})
    assert r.status_code in (200, 206), r.text
    return r.json()


@pytest.fixture
def changed(client, run_id, enabled):
    """A service with two changes: revision 1 (active, original name), 2 (inactive), current 3 (renamed)."""
    marker = uuid.uuid4().hex[:8]
    created = client.post(
        "/service", json=make_service(run_id, f"aa:{marker}", name=f"orig-{marker}", serviceType=f"Hist-{marker}")
    ).json()
    patch(client, created["id"], {"state": "inactive"})
    patch(client, created["id"], {"name": f"renamed-{marker}"})
    yield created["id"], marker
    client.delete(f"/service/{created['id']}")


def own(docs, service_id):
    return [d for d in docs if d["id"] == service_id]


def test_disabled_rejects_include_history(client, history_enabled):
    if history_enabled:
        pytest.skip("API runs with HISTORY_ENABLED")
    assert client.get("/service", params={"includeHistory": "true"}).status_code == 400
    assert client.get("/service", params={"includeHistory": "false", "limit": 1}).status_code in (200, 206)


def test_current_version_is_clean(client, changed):
    service_id, marker = changed
    current = client.get(f"/service/{service_id}").json()
    assert "revision" not in current
    assert current["name"] == f"renamed-{marker}" and current["state"] == "inactive"


def test_list_with_history(client, changed):
    service_id, marker = changed
    kind = f"Hist-{marker}"
    docs = own(revisions(client, kind), service_id)
    assert [d.get("revision", {}).get("id") for d in docs] == [1, 2, None]  # oldest first, the current one last
    first, second, current = docs
    assert (first["state"], second["state"], current["state"]) == ("active", "inactive", "inactive")
    assert first["name"] == f"orig-{marker}" and second["name"] == f"orig-{marker}"
    assert current["name"] == f"renamed-{marker}" and "revision" not in current
    # revisions follow each other without a gap
    assert first["revision"]["endTimestamp"] == second["revision"]["startTimestamp"]
    assert second["revision"]["endTimestamp"] > second["revision"]["startTimestamp"]


def test_list_without_include_history_is_current_only(client, changed):
    service_id, marker = changed
    kind = f"Hist-{marker}"
    r = client.get("/service", params={"serviceType": kind, "includeHistory": "false"})
    assert len(own(r.json(), service_id)) == 1
    r = client.get("/service", params={"serviceType": kind})
    assert len(own(r.json(), service_id)) == 1


def test_filters_apply_to_each_revision(client, changed):
    service_id, marker = changed
    kind = f"Hist-{marker}"
    docs = own(revisions(client, kind, state="active"), service_id)
    assert [d["revision"]["id"] for d in docs] == [1]
    docs = own(revisions(client, kind, name=f"renamed-{marker}"), service_id)
    assert len(docs) == 1 and "revision" not in docs[0]
    docs = own(revisions(client, kind, **{"serviceCharacteristic.value": f"aa:{marker}"}), service_id)
    assert len(docs) == 3


def test_count_paging_and_sort_include_revisions(client, changed):
    service_id, marker = changed
    kind = f"Hist-{marker}"
    params = {"serviceType": kind, "includeHistory": "true"}
    r = client.get("/service", params={**params, "limit": 2})
    assert r.status_code == 206 and r.headers["X-Total-Count"] == "3" and r.headers["X-Result-Count"] == "2"
    r = client.get("/service", params={**params, "limit": 2, "offset": 2})
    assert r.status_code == 200 and len(r.json()) == 1 and "revision" not in r.json()[0]
    r = client.get("/service", params={**params, "sort": "-state"})
    assert [d["state"] for d in r.json()] == ["inactive", "inactive", "active"]


def test_fields_keep_the_revision(client, changed):
    service_id, marker = changed
    kind = f"Hist-{marker}"
    docs = own(revisions(client, kind, fields="state"), service_id)
    assert set(docs[0]) == {"id", "href", "@type", "state", "revision"}
    assert set(docs[2]) == {"id", "href", "@type", "state"}


def test_timestamp_range(client, changed):
    service_id, marker = changed
    kind = f"Hist-{marker}"
    docs = own(revisions(client, kind), service_id)
    end_of_first = datetime.fromisoformat(docs[0]["revision"]["endTimestamp"].rstrip("Z"))
    micro = timedelta(microseconds=1)

    def ids(**params):
        return [d.get("revision", {}).get("id") for d in own(revisions(client, kind, **params), service_id)]

    stamp = lambda moment: moment.isoformat(timespec="microseconds") + "Z"  # noqa: E731
    assert ids(revisionStartTimestamp=stamp(end_of_first + micro)) == [2, None]  # revision 1 ended before
    assert ids(revisionEndTimestamp=stamp(end_of_first - micro)) == [1]  # the others started later
    assert ids(revisionStartTimestamp=stamp(end_of_first), revisionEndTimestamp=stamp(end_of_first)) == [1, 2]
    assert ids(revisionStartTimestamp="2999-01-01T00:00:00Z") == [None]  # the current one has no end


def test_unchanged_patch_creates_no_revision(client, changed):
    service_id, marker = changed
    kind = f"Hist-{marker}"
    patch(client, service_id, {"name": f"renamed-{marker}"})
    assert len(own(revisions(client, kind), service_id)) == 3


def test_retrieve_a_revision(client, changed):
    service_id, marker = changed
    r = client.get(f"/service/{service_id}", params={"includeHistory": "true", "revision": 1})
    assert r.status_code == 200
    assert r.json()["state"] == "active" and r.json()["revision"]["id"] == 1 and "startTimestamp" in r.json()["revision"]
    r = client.get(f"/service/{service_id}", params={"includeHistory": "true", "revision": 3})
    assert r.status_code == 200 and r.json()["name"] == f"renamed-{marker}" and "revision" not in r.json()


@pytest.mark.parametrize(
    "params, status",
    [
        ({"includeHistory": "true"}, 400),  # the revision has to be named
        ({"revision": "1"}, 400),
        ({"includeHistory": "false", "revision": "1"}, 400),
        ({"includeHistory": "true", "revision": "0"}, 400),
        ({"includeHistory": "true", "revision": "x"}, 400),
        ({"includeHistory": "maybe", "revision": "1"}, 400),
        ({"includeHistory": "true", "revision": "9"}, 404),
    ],
)
def test_retrieve_a_revision_needs_a_valid_combination(client, changed, params, status):
    service_id, _ = changed
    assert client.get(f"/service/{service_id}", params=params).status_code == status


def test_invalid_list_parameters(client, enabled):
    assert client.get("/service", params={"includeHistory": "maybe"}).status_code == 400
    assert client.get("/service", params={"revisionStartTimestamp": "2020-01-01T00:00:00Z"}).status_code == 400
    assert client.get("/service", params={"revisionEndTimestamp": "2020-01-01T00:00:00Z"}).status_code == 400
    r = client.get("/service", params={"includeHistory": "true", "revisionStartTimestamp": "yesterday"})
    assert r.status_code == 400
    r = client.get("/service", params={"includeHistory": "true", "serviceRelationship.service.state": "active"})
    assert r.status_code == 400  # filters through references are not supported on history


def test_delete_keeps_the_revisions(client, run_id, enabled):
    marker = uuid.uuid4().hex[:8]
    kind = f"Hist-{marker}"
    service_id = client.post("/service", json=make_service(run_id, f"bb:{marker}", name=f"del-{marker}", serviceType=kind)).json()["id"]
    patch(client, service_id, {"state": "terminated"})
    assert client.delete(f"/service/{service_id}").status_code == 204
    assert client.get(f"/service/{service_id}").status_code == 404
    docs = own(revisions(client, kind, name=f"del-{marker}"), service_id)
    assert [(d["revision"]["id"], d["state"]) for d in docs] == [(1, "active"), (2, "terminated")]
    r = client.get(f"/service/{service_id}", params={"includeHistory": "true", "revision": 2})
    assert r.status_code == 200 and r.json()["state"] == "terminated"
    assert client.get(f"/service/{service_id}", params={"includeHistory": "true", "revision": 3}).status_code == 404


def test_new_service_has_no_history_yet(client, run_id, enabled):
    marker = uuid.uuid4().hex[:8]
    kind = f"Hist-{marker}"
    service_id = client.post("/service", json=make_service(run_id, f"cc:{marker}", serviceType=kind)).json()["id"]
    try:
        docs = own(revisions(client, kind), service_id)
        assert len(docs) == 1 and "revision" not in docs[0]
        r = client.get(f"/service/{service_id}", params={"includeHistory": "true", "revision": 1})
        assert r.status_code == 200 and "revision" not in r.json()  # revision 1 is the current one
    finally:
        client.delete(f"/service/{service_id}")
