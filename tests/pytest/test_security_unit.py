"""AUTH configuration and the Basic user list (no API needed)."""
import hashlib

import pytest

from openapi_server import security
from openapi_server.security import Principal, parse_users


def test_users_and_roles():
    users = parse_users("reader:pw1:read, admin:pw2:read+write")
    assert users["reader"] == ("pw1", frozenset({"read"}))
    assert users["admin"][1] == frozenset({"read", "write"})


def test_sha256_secret():
    digest = hashlib.sha256(b"geheim").hexdigest()
    users = parse_users(f"a:sha256:{digest}:write")
    stored = users["a"][0]
    assert security._secret_matches(stored, "geheim") and not security._secret_matches(stored, "falsch")
    assert security._secret_matches("plain", "plain") and not security._secret_matches("plain", "plaiN")


@pytest.mark.parametrize("spec", ["", "a:b", "a::read", "a:b:", "a:b:admin", ":b:read", "a:b:c:d:read"])
def test_invalid_user_lists(spec):
    with pytest.raises(RuntimeError):
        parse_users(spec)


def test_write_includes_read():
    assert Principal("w", frozenset({"write"})).allows("read")
    assert not Principal("r", frozenset({"read"})).allows("write")
    assert not Principal("n").allows("read")


@pytest.mark.parametrize(
    "env", [{"AUTH_MODE": "ldap"}, {"AUTH_MODE": "basic"}, {"AUTH_MODE": "oauth2"}]
)
def test_misconfiguration_fails_at_start(env):
    with pytest.raises(RuntimeError):
        security.configure(env)


def test_none_is_default():
    assert security.configure({}) is not None
