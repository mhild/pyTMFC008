"""Deterministic generator for realistic TMF638 Service documents (seed + benchmark)."""
import random
import uuid
from datetime import date, timedelta

# same people as the Bruno collection (tests/TMFC008/collection.bru)
PARTIES = [
    "Anna Müller", "Thomas Schmidt", "Julia Schneider", "Michael Fischer", "Sabine Weber",
    "Peter Meyer", "Claudia Wagner", "Daniel Becker", "Laura Hoffmann", "Andreas Wolf",
]
SERVICE_TYPES = ["Cloud", "Broadband", "Mobile", "IPTV", "VoIP"]
STATES = ["active", "active", "active", "inactive", "suspended", "terminated"]
FEATURES = ["ElasticBandwith", "StaticIP", "ParentalControl", "QoS", "IPv6"]

SEED_NAMESPACE = uuid.UUID("6c1d7b4e-3a52-4c8e-9f77-1f0b9d2e5a10")


def service_id(i: int) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, str(i))


def mac_for(i: int) -> str:
    """Unique MAC address of service #i (02: = locally administered)."""
    h = f"{i:010x}"
    return "02:" + ":".join(h[k:k + 2] for k in range(0, 10, 2))


def party_for(i: int) -> str:
    """Rare customer names (one per 10 000 services) for selective searches."""
    return f"Customer {i // 10_000:05d}" if i % 997 == 0 else PARTIES[i % len(PARTIES)]


def make_service(i: int, href_base: str = "http://localhost/service") -> dict:
    rnd = random.Random(i)
    sid = service_id(i)
    start = date(2020, 1, 1) + timedelta(days=rnd.randrange(2000))
    characteristics = [
        {"name": "mac", "valueType": "string", "value": mac_for(i), "@type": "StringCharacteristic"},
        {"name": "vlan", "valueType": "integer", "value": rnd.randrange(1, 4095), "@type": "IntegerCharacteristic"},
        {"name": "bandwidth", "valueType": "integer", "value": rnd.choice([50, 100, 250, 500, 1000]),
         "@type": "IntegerCharacteristic"},
        {"name": "ipAddress", "valueType": "string",
         "value": f"10.{rnd.randrange(256)}.{rnd.randrange(256)}.{rnd.randrange(1, 255)}", "@type": "StringCharacteristic"},
        {"name": "serialNumber", "valueType": "string", "value": f"SN{i:09d}", "@type": "StringCharacteristic"},
    ]
    rnd.shuffle(characteristics)
    doc = {
        "id": str(sid),
        "href": f"{href_base}/{sid}",
        "@type": "Service",
        "name": f"vCPE serial {i}",
        "description": "Instantiation of vCPE",
        "serviceType": rnd.choice(SERVICE_TYPES),
        "state": rnd.choice(STATES),
        "category": rnd.choice(["CFS", "RFS"]),
        "startDate": f"{start.isoformat()}T00:00:00Z",
        "serviceSpecification": {
            "id": str(1200 + i % 20), "name": "vCPE", "version": "1.0.0",
            "@type": "ServiceSpecificationRef", "@referredType": "ServiceSpecification",
        },
        "feature": [
            {"id": f"Feat{k}", "isEnabled": rnd.random() < 0.7, "name": name, "@type": "Feature"}
            for k, name in enumerate(rnd.sample(FEATURES, 2))
        ],
        "serviceCharacteristic": characteristics,
        "relatedParty": [
            {"role": "user", "partyOrPartyRole": {"id": str(100 + i % 1000), "name": party_for(i), "@type": "PartyRef"},
             "@type": "RelatedPartyRefOrPartyRoleRef"},
        ],
    }
    if i % 2:  # every odd service (CFS) depends on the even one before it (RFS)
        rid = service_id(i - 1)
        doc["serviceRelationship"] = [{
            "relationshipType": "DependentOn",
            "service": {"id": str(rid), "href": f"{href_base}/{rid}", "@type": "ServiceRef", "@referredType": "Service"},
            "@type": "ServiceRelationship",
        }]
    return doc
