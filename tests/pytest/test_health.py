"""Liveness and readiness endpoints (operational, not part of TMF638)."""


def test_livez(client):
    r = client.get("/livez")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_readyz(client):
    r = client.get("/readyz")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_not_in_the_openapi_document(client):
    assert not {"/livez", "/readyz"} & set(client.get("/openapi.json").json()["paths"])
