"""Integration tests against a running TMF638 API (TMF_BASE_URL); backend-agnostic.

Every run uses a unique marker so the tests also work on a pre-filled database.
"""
import uuid
from pathlib import Path

import pytest
import yaml

MERGE = {"Content-Type": "application/merge-patch+json"}
SPEC_FILE = Path(__file__).resolve().parents[2] / "api_specs" / "TMF638-Service_Inventory_Management-v5.0.0.oas.yaml"
SPEC_REF = {"id": "vcpe-spec-1", "name": "vCPE", "@type": "ServiceSpecificationRef"}
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
        "serviceSpecification": SPEC_REF,
        "serviceCharacteristic": [
            {"name": "vlan", "valueType": "integer", "value": 300, "@type": "IntegerCharacteristic"},
            {"name": "mac", "valueType": "string", "value": mac, "@type": "StringCharacteristic"},
        ],
        "relatedParty": [
            {"role": "user", "partyOrPartyRole": {"id": f"party-{party}", "name": party, "@type": "PartyRef"}, "@type": "RelatedPartyRefOrPartyRoleRef"}
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
    assert r.status_code == 404
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


# --------------------------------------------------------------------------- #
# Validation against the TMF638 schemas
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "change, error_path",
    [
        ({"state": "running"}, "$.state"),
        ({"startDate": "2024-05-01"}, "$.startDate"),  # date-time required
        ({"isStateful": "yes"}, "$.isStateful"),
        ({"serviceSpecification": None}, "'serviceSpecification' is a required property"),
        ({"relatedParty": [{"role": "user", "partyOrPartyRole": {"name": "x", "@type": "PartyRef"},
                            "@type": "RelatedPartyRefOrPartyRoleRef"}]}, "$.relatedParty[0].partyOrPartyRole"),
    ],
)
def test_create_rejects_invalid_service(client, run_id, change, error_path):
    doc = {**make_service(run_id, "ff:ff"), **change}
    doc = {k: v for k, v in doc.items() if v is not None}
    r = client.post("/service", json=doc)
    assert r.status_code == 400, r.text
    assert error_path in r.json()["reason"]


def test_create_accepts_spec_example(client):
    with open(SPEC_FILE, encoding="utf-8") as f:
        example = yaml.safe_load(f)["components"]["examples"]["Create_Service_request"]["value"]
    r = client.post("/service", json=example)
    assert r.status_code == 201, r.text
    client.delete(f"/service/{r.json()['id']}")


def test_patch_must_keep_the_service_valid(client, services):
    s = services[1]
    before = client.get(f"/service/{s['id']}").json()
    assert client.patch(f"/service/{s['id']}", json={"state": "running"}, headers=MERGE).status_code == 400
    assert client.patch(f"/service/{s['id']}", json={"@type": None}, headers=MERGE).status_code == 400
    assert client.get(f"/service/{s['id']}").json() == before


# --------------------------------------------------------------------------- #
# Object-valued characteristics (Oracle: indexed via the `search` shadow column)
# --------------------------------------------------------------------------- #

def object_characteristic(name, value):
    return {"name": name, "valueType": "object", "value": value, "@type": "ObjectCharacteristic"}


@pytest.fixture(scope="module")
def with_objects(client, run_id):
    vcpe = {"@type": "VCPE", "vCPE_IP": f"10.0.0.1-{run_id}", "MaxTxRate": 300}
    docs = [
        make_service(run_id, f"o1-{run_id}", serviceType=f"Obj-{run_id}",
                     serviceCharacteristic=[object_characteristic("vCPE", vcpe),
                                            {"name": "mac", "value": f"o1-{run_id}", "@type": "StringCharacteristic"}]),
        make_service(run_id, f"o2-{run_id}", serviceType=f"Obj-{run_id}",
                     serviceCharacteristic=[{"name": "tags", "value": [f"t-{run_id}", {"x": 1}], "@type": "Characteristic"}]),
    ]
    created = []
    for doc in docs:
        r = client.post("/service", json=doc)
        assert r.status_code == 201, r.text
        created.append(r.json())
    yield created
    for s in created:
        client.delete(f"/service/{s['id']}")


def test_scalar_value_next_to_an_object_value(client, run_id, with_objects):
    mac = f"o1-{run_id}"
    assert ids(client.get("/service", params={"serviceCharacteristic.name": "mac", "serviceCharacteristic.value": mac})) == {
        with_objects[0]["id"]
    }
    r = client.get("/service", params={"filter": f"$.serviceCharacteristic[?(@.name=='mac' && @.value=='{mac}')]"})
    assert ids(r) == {with_objects[0]["id"]}


def test_scalar_in_an_array_with_objects(client, run_id, with_objects):
    assert ids(client.get("/service", params={"serviceCharacteristic.value": f"t-{run_id}"})) == {with_objects[1]["id"]}


def test_filter_inside_an_object_value(client, run_id, with_objects):
    # a path inside an object value has no index: combined with an indexed condition, otherwise it scans the table
    r = client.get("/service", params={"serviceType": f"Obj-{run_id}", "serviceCharacteristic.value.vCPE_IP": f"10.0.0.1-{run_id}"})
    assert ids(r) == {with_objects[0]["id"]}
    r = client.get("/service", params={"serviceType": f"Obj-{run_id}", "filter": "$.serviceCharacteristic[?(@.value.MaxTxRate > 200)]"})
    assert ids(r) == {with_objects[0]["id"]}


def test_patch_scalar_value_to_object(client, run_id, with_objects):
    s = with_objects[1]
    patch = {"serviceCharacteristic": [object_characteristic("tags", {"t": f"t-{run_id}"})]}
    assert client.patch(f"/service/{s['id']}", json=patch, headers=MERGE).status_code == 200
    assert ids(client.get("/service", params={"serviceCharacteristic.value": f"t-{run_id}"})) == set()
    r = client.get("/service", params={"serviceType": f"Obj-{run_id}", "serviceCharacteristic.value.t": f"t-{run_id}"})
    assert ids(r) == {s["id"]}
    patch = {"serviceCharacteristic": [{"name": "tags", "value": f"t-{run_id}", "@type": "StringCharacteristic"}]}
    assert client.patch(f"/service/{s['id']}", json=patch, headers=MERGE).status_code == 200
    assert ids(client.get("/service", params={"serviceCharacteristic.value": f"t-{run_id}"})) == {s["id"]}


# --------------------------------------------------------------------------- #
# Sorting
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def sortable(client, run_id):
    """priority 9/10/100 checks numeric order (as text, "10" < "100" < "9")."""
    docs = [
        make_service(run_id, "s1", serviceType=f"Sort-{run_id}", priority=10, startDate="2024-03-01T00:00:00Z"),
        make_service(run_id, "s2", serviceType=f"Sort-{run_id}", priority=9, startDate="2024-01-01T00:00:00Z"),
        make_service(run_id, "s3", serviceType=f"Sort-{run_id}", priority=100, startDate="2024-03-01T00:00:00Z"),
        make_service(run_id, "s4", serviceType=f"Sort-{run_id}", startDate="2024-02-01T00:00:00Z"),  # no priority
    ]
    created = [client.post("/service", json=doc).json() for doc in docs]
    yield f"Sort-{run_id}"
    for s in created:
        client.delete(f"/service/{s['id']}")


def sorted_names(client, service_type, sort, **params):
    r = client.get("/service", params={"serviceType": service_type, "sort": sort, "fields": "name", **params})
    assert r.status_code in (200, 206), r.text
    return [s["name"].removeprefix("vCPE ") for s in r.json()]


def test_sort_numbers_numerically_missing_values_last(client, sortable):
    assert sorted_names(client, sortable, "priority") == ["s2", "s1", "s3", "s4"]
    assert sorted_names(client, sortable, "-priority") == ["s3", "s1", "s2", "s4"]


def test_sort_by_several_attributes(client, sortable):
    assert sorted_names(client, sortable, "-startDate,name") == ["s1", "s3", "s4", "s2"]
    assert sorted_names(client, sortable, "-startDate,-name") == ["s3", "s1", "s4", "s2"]


def test_sort_with_pagination(client, sortable):
    assert sorted_names(client, sortable, "startDate,name", offset=1, limit=2) == ["s4", "s1"]


@pytest.mark.parametrize("sort", ["na'me", "a..b", "-", ""])
def test_invalid_sort_is_bad_request(client, sort):
    assert client.get("/service", params={"sort": sort}).status_code == 400
