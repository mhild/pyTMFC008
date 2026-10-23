"""Integration tests against a running TMF638 API (TMF_BASE_URL); backend-agnostic.

Every run uses a unique marker so the tests also work on a pre-filled database.
"""
import uuid

import pytest

MERGE = {"Content-Type": "application/merge-patch+json"}
JSON_PATCH = {"Content-Type": "application/json-patch+json"}


@pytest.fixture(scope="module")
def run_id():
    return uuid.uuid4().hex[:12]


def make_service(run_id, mac, party="Peter Meyer", state="active", **extra):
    return {
        "@type": "Service",
        "serviceType": f"Cloud-{run_id}",
        "name": f"vCPE {mac}",
        "state": state,
        "startDate": "2024-05-01T00:00:00Z",
        "serviceCharacteristic": [
            {"name": "vlan", "valueType": "integer", "value": 300, "@type": "IntegerCharacteristic"},
            {"name": "mac", "valueType": "string", "value": mac, "@type": "StringCharacteristic"},
        ],
        "relatedParty": [
            {"role": "user", "partyOrPartyRole": {"name": party, "@type": "PartyRef"}, "@type": "RelatedPartyRefOrPartyRoleRef"}
        ],
        **extra,
    }


@pytest.fixture(scope="module")
def services(client, run_id):
    docs = [
        make_service(run_id, "00:11:22:33:44:55"),
        make_service(run_id, "00:11:22:33:44:66", party="Anna Müller", state="inactive"),
        make_service(run_id, "00:11:22:33:44:77", party="O'Brien \"Q\""),
    ]
    created = []
    for doc in docs:
        r = client.post("/service", json=doc)
        assert r.status_code == 201, r.text
        created.append(r.json())
    yield created
    for s in created:
        client.delete(f"/service/{s['id']}")


def ids(response):
    assert response.status_code in (200, 206), response.text
    return {s["id"] for s in response.json()}


def test_create_returns_resource(services):
    s = services[0]
    assert s["href"].endswith(f"/service/{s['id']}")
    assert s["serviceCharacteristic"][1]["value"] == "00:11:22:33:44:55"


def test_retrieve(client, services):
    s = services[0]
    r = client.get(f"/service/{s['id']}")
    assert r.status_code == 200
    assert r.json() == s


def test_retrieve_with_fields(client, services):
    r = client.get(f"/service/{services[0]['id']}", params={"fields": "state"})
    assert set(r.json()) == {"id", "href", "@type", "state"}


def test_retrieve_unknown_and_invalid_id(client):
    assert client.get(f"/service/{uuid.uuid4()}").status_code == 404
    r = client.get("/service/not-a-uuid")
    assert r.status_code == 400
    assert r.json()["@type"] == "Error"


def test_attribute_filter(client, run_id, services):
    assert ids(client.get("/service", params={"serviceType": f"Cloud-{run_id}"})) == {s["id"] for s in services}
    assert ids(client.get("/service", params={"serviceType": f"Cloud-{run_id}", "state": "inactive"})) == {services[1]["id"]}
    assert ids(client.get("/service", params={"serviceType": f"Cloud-{run_id}", "state": "inactive,active"})) == {
        s["id"] for s in services
    }


def test_attribute_filter_dotted_path(client, run_id, services):
    r = client.get("/service", params={"serviceType": f"Cloud-{run_id}", "relatedParty.partyOrPartyRole.name": "Anna Müller"})
    assert ids(r) == {services[1]["id"]}


def test_attribute_filter_number(client, run_id, services):
    r = client.get("/service", params={"serviceType": f"Cloud-{run_id}", "serviceCharacteristic.value": "300"})
    assert ids(r) == {s["id"] for s in services}


def test_attribute_filter_operators(client, run_id, services):
    base = {"serviceType": f"Cloud-{run_id}"}
    assert len(ids(client.get("/service", params={**base, "startDate.gte": "2024-01-01"}))) == 3
    assert ids(client.get("/service", params={**base, "startDate.gt": "2025-01-01"})) == set()
    assert ids(client.get("/service", params={**base, "state.ne": "active"})) == {services[1]["id"]}


def test_jsonpath_filter_characteristic(client, services):
    """The search the PoC is about: characteristic name AND value in the same array element."""
    r = client.get("/service", params={"filter": "$.serviceCharacteristic[?(@.name=='mac' && @.value=='00:11:22:33:44:55')]"})
    assert ids(r) == {services[0]["id"]}


def test_jsonpath_filter_does_not_mix_array_elements(client, services):
    r = client.get("/service", params={"filter": "$.serviceCharacteristic[?(@.name=='vlan' && @.value=='00:11:22:33:44:55')]"})
    assert ids(r) == set()


def test_jsonpath_filter_related_party(client, run_id, services):
    r = client.get(
        "/service",
        params={"serviceType": f"Cloud-{run_id}", "filter": "$.relatedParty[?(@.partyOrPartyRole.name=='Peter Meyer')]"},
    )
    assert ids(r) == {services[0]["id"]}


def test_quotes_in_values_are_data_not_syntax(client, run_id, services):
    r = client.get("/service", params={"relatedParty.partyOrPartyRole.name": "O'Brien \"Q\""})
    assert ids(r) == {services[2]["id"]}
    assert ids(client.get("/service", params={"name": "x' OR '1'='1"})) == set()


def test_invalid_filter_is_bad_request(client):
    r = client.get("/service", params={"filter": "$.a[?(@.b=='x'"})
    assert r.status_code == 400
    assert r.json()["@type"] == "Error"
    assert client.get("/service", params={"na'me": "x"}).status_code == 400


def test_list_fields(client, run_id, services):
    r = client.get("/service", params={"serviceType": f"Cloud-{run_id}", "fields": "name"})
    assert all(set(s) == {"id", "href", "@type", "name"} for s in r.json())


def test_pagination(client, run_id, services):
    base = {"serviceType": f"Cloud-{run_id}"}
    first = client.get("/service", params={**base, "limit": 2})
    assert first.status_code == 206
    assert first.headers["X-Total-Count"] == "3"
    assert first.headers["X-Result-Count"] == "2"
    rest = client.get("/service", params={**base, "offset": 2, "limit": 2})
    assert rest.status_code == 200
    assert rest.headers["X-Result-Count"] == "1"
    assert ids(first) | ids(rest) == {s["id"] for s in services}


def test_merge_patch(client, services):
    s = services[0]
    r = client.patch(f"/service/{s['id']}", json={"state": "suspended", "description": None}, headers=MERGE)
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "suspended"
    assert r.json()["id"] == s["id"]
    assert client.get(f"/service/{s['id']}").json()["state"] == "suspended"


def test_json_patch(client, services):
    s = services[2]
    ops = [{"op": "replace", "path": "/state", "value": "terminated"}, {"op": "add", "path": "/description", "value": "x"}]
    r = client.patch(f"/service/{s['id']}", json=ops, headers=JSON_PATCH)
    assert r.status_code == 200, r.text
    assert (r.json()["state"], r.json()["description"]) == ("terminated", "x")


def test_patch_cannot_change_id(client, services):
    s = services[1]
    r = client.patch(f"/service/{s['id']}", json={"id": "other", "href": "x"}, headers=MERGE)
    assert (r.json()["id"], r.json()["href"]) == (s["id"], s["href"])


def test_patch_errors(client, services):
    sid = services[1]["id"]
    assert client.patch(f"/service/{sid}", json={"a": 1}, headers={"Content-Type": "text/plain"}).status_code == 415
    bad = [{"op": "remove", "path": "/doesNotExist"}]
    assert client.patch(f"/service/{sid}", json=bad, headers=JSON_PATCH).status_code == 400


def test_delete(client, run_id):
    created = client.post("/service", json=make_service(run_id, "aa:bb")).json()
    r = client.delete(f"/service/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/service/{created['id']}").status_code == 404
    assert client.delete(f"/service/{created['id']}").status_code == 404
