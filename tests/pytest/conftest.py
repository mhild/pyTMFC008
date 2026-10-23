import os

import httpx
import pytest

BASE_URL = os.environ.get("TMF_BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=30) as c:
        try:
            c.get("/service", params={"limit": 1})
        except httpx.TransportError:
            pytest.skip(f"TMF638 API not reachable at {BASE_URL} (set TMF_BASE_URL)")
        yield c
