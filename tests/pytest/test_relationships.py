"""Filtering through service relationships: find service A by attributes of the service B it relates to.

Data model per test run (all scoped by serviceType "Rel-<run id>" of the referencing services):

    A  --DependentOn-->  B   (B: mac = 00:11:22:33:44:55)
    E  --ReliesOn----->  {B embedded by value, mac = 00:11:22:33:44:55}
    C  --DependentOn-->  D   (D: mac = 00:11:22:33:44:66)
    F  --DependentOn-->  G   (G: mac = aa:bb:..., but 00:11:22:33:44:55 as *serialNumber*)
    H  --supportingService--> B
"""
import uuid

import pytest

MAC = "00:11:22:33:44:55"
REF_FILTER = f"$.serviceRelationship[?(@.service.serviceCharacteristic[?(@.name=='mac' && @.value=='{MAC}')])]"


def characteristic(name, value):
    return {"name": name, "valueType": "string", "value": value, "@type": "StringCharacteristic"}


def ref(service):
    return {"id": service["id"], "href": service["href"], "@type": "ServiceRef", "@referredType": "Service"}


def relationship(service_ref_or_value, relationship_type="DependentOn"):
    return {"relationshipType": relationship_type, "service": service_ref_or_value, "@type": "ServiceRelationship"}


@pytest.fixture(scope="module")
def model(client):
    run = uuid.uuid4().hex[:12]
    created = []

    def post(**doc):
        r = client.post("/service", json={"@type": "Service", "state": "active", **doc})
        assert r.status_code == 201, r.text
        created.append(r.json())
        return r.json()

    rfs = f"RFS-{run}"
    b = post(name="B", serviceType=rfs, serviceCharacteristic=[characteristic("vlan", "12"), characteristic("mac", MAC)])
    d = post(name="D", serviceType=rfs, serviceCharacteristic=[characteristic("mac", "00:11:22:33:44:66")])
    g = post(name="G", serviceType=rfs, serviceCharacteristic=[characteristic("mac", "aa:bb:cc:dd:ee:ff"),
                                                               characteristic("serialNumber", MAC)])
    cfs = f"Rel-{run}"
    services = {
        "B": b, "D": d, "G": g,
        "A": post(name="A", serviceType=cfs, serviceRelationship=[relationship(ref(b))]),
        "E": post(name="E", serviceType=cfs, serviceRelationship=[relationship(
            {"@type": "Service", "name": "embedded B", "serviceCharacteristic": [characteristic("mac", MAC)]}, "ReliesOn")]),
        "C": post(name="C", serviceType=cfs, serviceRelationship=[relationship(ref(d))]),
        "F": post(name="F", serviceType=cfs, serviceRelationship=[relationship(ref(g))]),
        "H": post(name="H", serviceType=cfs, supportingService=[ref(b)]),
    }
    yield cfs, rfs, services
    for s in created:
        client.delete(f"/service/{s['id']}")


def names(response):
    assert response.status_code in (200, 206), response.text
    return {s["name"] for s in response.json()}


def test_attribute_filter_through_relationship(client, model):
    cfs, _, _ = model
    r = client.get("/service", params={
        "serviceType": cfs,
        "serviceRelationship.service.serviceCharacteristic.name": "mac",
        "serviceRelationship.service.serviceCharacteristic.value": MAC,
    })
    assert names(r) == {"A", "E"}  # E holds B by value


def test_jsonpath_filter_through_relationship(client, model):
    cfs, _, _ = model
    assert names(client.get("/service", params={"serviceType": cfs, "filter": REF_FILTER})) == {"A", "E"}


def test_relationship_type_applies_to_the_same_relationship(client, model):
    cfs, _, _ = model
    base = {
        "serviceType": cfs,
        "serviceRelationship.service.serviceCharacteristic.name": "mac",
        "serviceRelationship.service.serviceCharacteristic.value": MAC,
    }
    assert names(client.get("/service", params={**base, "serviceRelationship.relationshipType": "DependentOn"})) == {"A"}
    assert names(client.get("/service", params={**base, "serviceRelationship.relationshipType": "ReliesOn"})) == {"E"}


def test_characteristic_name_and_value_from_the_same_element(client, model):
    """G has a mac and the value 00:11:22:33:44:55, but not in the same characteristic -> F must not match."""
    cfs, rfs, _ = model
    r = client.get("/service", params={
        "serviceType": cfs,
        "serviceRelationship.service.serviceCharacteristic.name": "serialNumber",
        "serviceRelationship.service.serviceCharacteristic.value": MAC,
    })
    assert names(r) == {"F"}
    # same rule within a single document
    r = client.get("/service", params={"serviceType": rfs, "serviceCharacteristic.name": "vlan",
                                       "serviceCharacteristic.value": MAC})
    assert names(r) == set()


def test_repeated_parameter_means_separate_elements(client, model):
    _, rfs, _ = model
    r = client.get("/service", params=[("serviceType", rfs), ("serviceCharacteristic.name", "mac"),
                                       ("serviceCharacteristic.name", "vlan")])
    assert names(r) == {"B"}


def test_attribute_of_the_referenced_service(client, model):
    cfs, _, _ = model
    r = client.get("/service", params={"serviceType": cfs, "serviceRelationship.service.name": "D"})
    assert names(r) == {"C"}  # the references carry no name: matched via the referenced service
    r = client.get("/service", params={"serviceType": cfs, "serviceRelationship.service.state": "active"})
    assert names(r) == {"A", "C", "F"}


def test_filter_on_reference_fields_needs_no_join(client, model):
    _, _, s = model
    r = client.get("/service", params={"serviceRelationship.service.id": s["B"]["id"]})
    assert names(r) == {"A"}


def test_supporting_service(client, model):
    cfs, _, _ = model
    r = client.get("/service", params={"serviceType": cfs, "supportingService.serviceCharacteristic.value": MAC})
    assert names(r) == {"H"}


def test_no_match(client, model):
    cfs, _, _ = model
    r = client.get("/service", params={
        "serviceType": cfs,
        "serviceRelationship.service.serviceCharacteristic.name": "mac",
        "serviceRelationship.service.serviceCharacteristic.value": "ff:ff:ff:ff:ff:ff",
    })
    assert names(r) == set()


def test_pagination_header_counts_joined_matches(client, model):
    cfs, _, _ = model
    r = client.get("/service", params={"serviceType": cfs, "filter": REF_FILTER, "limit": 1})
    assert r.status_code == 206
    assert r.headers["X-Total-Count"] == "2"


def test_nested_references_are_rejected(client):
    r = client.get("/service", params={"serviceRelationship.service.serviceRelationship.service.name": "x"})
    assert r.status_code == 400
