import base64
import os

import httpx
import pytest

BASE_URL = os.environ.get("TMF_BASE_URL", "http://127.0.0.1:8080")

# Credentials for an API that runs with AUTH_MODE=basic / oauth2 (see README, *Authentication*). A role is
# `reader` (role read) or `writer` (read + write); all the other tests run as `writer`.
#   TMF_READER_BASIC=user:password        TMF_WRITER_BASIC=user:password
#   TMF_TOKEN_URL=<token endpoint>        TMF_READER_CLIENT=id:secret   TMF_WRITER_CLIENT=id:secret   (client credentials)


def auth_headers(who: str) -> dict:
    """Authorization header of `who` ('reader' or 'writer'); empty if the environment has no credentials for it."""
    basic = os.environ.get(f"TMF_{who.upper()}_BASIC")
    if basic:
        return {"Authorization": "Basic " + base64.b64encode(basic.encode()).decode()}
    client = os.environ.get(f"TMF_{who.upper()}_CLIENT")
    if client and os.environ.get("TMF_TOKEN_URL"):
        client_id, secret = client.split(":", 1)
        r = httpx.post(
            os.environ["TMF_TOKEN_URL"],
            data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": secret},
            timeout=30,
        )
        r.raise_for_status()
        return {"Authorization": "Bearer " + r.json()["access_token"]}
    return {}


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=30, headers=auth_headers("writer")) as c:
        try:
            c.get("/service", params={"limit": 1})
        except httpx.TransportError:
            pytest.skip(f"TMF638 API not reachable at {BASE_URL} (set TMF_BASE_URL)")
        yield c
