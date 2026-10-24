"""Authentication and authorization of the API, selected with AUTH_MODE (see README, *Authentication*).

none    no checks (default)
basic   HTTP Basic against AUTH_BASIC_USERS
oauth2  Bearer JWT of an external provider (e.g. Keycloak), verified against its JWKS

Two roles: `read` (GET, event subscriptions) and `write` (create, patch, delete; includes `read`).
/livez and /readyz are never protected.
"""
import asyncio
import hashlib
import hmac
import os
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Optional

import httpx
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials, HTTPBearer

READ, WRITE = "read", "write"
MODES = ("none", "basic", "oauth2")


@dataclass(frozen=True)
class Principal:
    name: str
    roles: FrozenSet[str] = field(default_factory=frozenset)

    def allows(self, role: str) -> bool:
        return role in self.roles or (role == READ and WRITE in self.roles)  # write includes read


def parse_users(spec: str) -> Dict[str, "tuple[str, FrozenSet[str]]"]:
    """`name:password:read+write,other:sha256:<hex>:read` -> {name: (password or sha256:<hex>, roles)}."""
    users = {}
    for entry in filter(None, (e.strip() for e in spec.split(","))):
        parts = entry.split(":")
        if len(parts) == 4 and parts[1] == "sha256":
            name, secret, roles = parts[0], "sha256:" + parts[2], parts[3]
        elif len(parts) == 3:
            name, secret, roles = parts
        else:
            raise RuntimeError("AUTH_BASIC_USERS: expected name:password:roles or name:sha256:<hex>:roles")
        granted = frozenset(r for r in roles.split("+") if r)
        if not name or not secret or not granted <= {READ, WRITE} or not granted:
            raise RuntimeError(f"AUTH_BASIC_USERS: user {name!r} needs a password and roles from read, write")
        users[name] = (secret, granted)
    if not users:
        raise RuntimeError("AUTH_MODE=basic needs AUTH_BASIC_USERS")
    return users


def _secret_matches(stored: str, given: str) -> bool:
    if stored.startswith("sha256:"):
        given = hashlib.sha256(given.encode()).hexdigest()
        stored = stored[len("sha256:"):]
    return hmac.compare_digest(stored.encode(), given.encode())


def _unauthorized(scheme: str, detail: str = "Authentication required") -> HTTPException:
    return HTTPException(status_code=401, detail=detail, headers={"WWW-Authenticate": scheme})


class BasicAuth:
    def __init__(self, users):
        self.users = users

    async def check(self, credentials: Optional[HTTPBasicCredentials]) -> Principal:
        if credentials is None:
            raise _unauthorized('Basic realm="tmf638"')
        known = self.users.get(credentials.username)
        # compare against a dummy for unknown users: same work whether the user exists or not
        stored, roles = known if known else ("-", frozenset())
        if not _secret_matches(stored, credentials.password) or known is None:
            raise _unauthorized('Basic realm="tmf638"', "Invalid credentials")
        return Principal(credentials.username, roles)


def _claim(token: dict, path: str):
    value = token
    for part in path.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value


class OAuth2Auth:
    """Resource server: validates the signature (JWKS), `iss`, `exp` and optionally `aud` of a Bearer JWT."""

    def __init__(self, issuer: str, jwks_url: Optional[str], audience: Optional[str], roles_claim: str,
                 role_read: str, role_write: str):
        self.issuer, self.audience, self.roles_claim = issuer.rstrip("/"), audience, roles_claim
        self.role_map = {role_read: READ, role_write: WRITE}
        self.jwks_url = jwks_url
        self._jwks: Optional[jwt.PyJWKClient] = None

    async def _client(self) -> jwt.PyJWKClient:
        if self._jwks is None:
            url = self.jwks_url
            if not url:  # OpenID Connect discovery
                async with httpx.AsyncClient(timeout=5) as http:
                    response = await http.get(self.issuer + "/.well-known/openid-configuration")
                    response.raise_for_status()
                url = response.json()["jwks_uri"]
            self._jwks = jwt.PyJWKClient(url, cache_jwk_set=True, lifespan=300)
        return self._jwks

    async def check(self, bearer: Optional[HTTPAuthorizationCredentials]) -> Principal:
        if bearer is None:
            raise _unauthorized("Bearer")
        challenge = 'Bearer error="invalid_token"'
        try:
            client = await self._client()
            key = await asyncio.to_thread(client.get_signing_key_from_jwt, bearer.credentials)
            token = jwt.decode(
                bearer.credentials, key.key, algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "PS256"],
                issuer=self.issuer, audience=self.audience,
                options={"require": ["exp", "iss"], "verify_aud": self.audience is not None},
            )
        except (jwt.PyJWTError, KeyError):
            raise _unauthorized(challenge, "Invalid token")
        except (httpx.HTTPError, OSError) as exc:  # provider not reachable: not the caller's fault
            raise HTTPException(status_code=503, detail=f"Identity provider not reachable ({type(exc).__name__})")
        granted = _claim(token, self.roles_claim)
        if isinstance(granted, str):  # e.g. a space-separated `scope` claim
            granted = granted.split()
        roles = frozenset(self.role_map[r] for r in (granted or []) if r in self.role_map)
        return Principal(token.get("preferred_username") or token.get("sub") or "unknown", roles)


basic_scheme = HTTPBasic(auto_error=False)  # as dependencies the schemes also appear in the OpenAPI document
bearer_scheme = HTTPBearer(auto_error=False)


def configure(env=os.environ):
    """The dependency that authenticates a request (returns a Principal, or None without authentication)."""
    mode = env.get("AUTH_MODE", "none").strip().lower() or "none"
    if mode == "none":
        async def authenticate() -> Optional[Principal]:
            return None
    elif mode == "basic":
        basic = BasicAuth(parse_users(env.get("AUTH_BASIC_USERS", "")))

        async def authenticate(credentials: Optional[HTTPBasicCredentials] = Depends(basic_scheme)) -> Optional[Principal]:
            return await basic.check(credentials)
    elif mode == "oauth2":
        if not env.get("OAUTH2_ISSUER"):
            raise RuntimeError("AUTH_MODE=oauth2 needs OAUTH2_ISSUER")
        oauth2 = OAuth2Auth(
            env["OAUTH2_ISSUER"], env.get("OAUTH2_JWKS_URL") or None, env.get("OAUTH2_AUDIENCE") or None,
            env.get("OAUTH2_ROLES_CLAIM", "realm_access.roles"),
            env.get("OAUTH2_ROLE_READ", "inventory-read"), env.get("OAUTH2_ROLE_WRITE", "inventory-write"),
        )

        async def authenticate(bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> Optional[Principal]:
            return await oauth2.check(bearer)
    else:
        raise RuntimeError(f"AUTH_MODE must be one of {', '.join(MODES)}, not {mode!r}")
    return authenticate


authenticator = configure()


def _check(principal: Optional[Principal], role: str) -> None:
    if principal is not None and not principal.allows(role):
        raise HTTPException(status_code=403, detail=f"The role '{role}' is required")


async def require_by_method(request: Request, principal: Optional[Principal] = Depends(authenticator)) -> None:
    """GET/HEAD/OPTIONS need `read`, everything else `write`."""
    _check(principal, READ if request.method in ("GET", "HEAD", "OPTIONS") else WRITE)


async def require_read(principal: Optional[Principal] = Depends(authenticator)) -> None:
    _check(principal, READ)
