"""Verify Supabase access tokens (spec Section 2.4; DECISIONS C4).

The token proves identity only: `sub` is the Supabase Auth user id. Customer/staff records and roles
are loaded from app tables on every request (invariant 22); no other claim (`role`, `email`,
metadata) is trusted.

Order of checks:
  1. shape: three dot-separated segments
  2. header `alg` in the configured allowlist, checked BEFORE any key is chosen. Rejects `none`, and
     HS256 in jwks mode (algorithm confusion), and anything not configured.
  3. key: jwks mode needs a `kid` present in the published key set (one rate-limited refresh on miss);
     secret mode uses AUTH_JWT_SECRET.
  4. signature, then required claims exp/iat/sub/aud/iss, with exp and iss/aud verified.
  5. `sub` must be a UUID.
"""

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
import jwt

from tollgate.config import AuthSettings
from tollgate.errors import AuthError, AuthUnavailableError

log = logging.getLogger(__name__)

REQUIRED_CLAIMS = ["exp", "iat", "sub", "aud", "iss"]
JWKS_MIN_REFRESH_S = 60.0


@dataclass(frozen=True)
class VerifiedToken:
    auth_user_id: uuid.UUID
    session_id: str | None
    expires_at: int


class TokenVerifier:
    def __init__(
        self,
        settings: AuthSettings,
        *,
        http: httpx.AsyncClient | None = None,
        jwks: dict[str, Any] | None = None,
    ) -> None:
        self._s = settings
        self._algorithms = list(settings.auth_jwt_algorithms)
        self._http = http
        self._keys: dict[str, jwt.PyJWK] = {}
        self._fetched_at = 0.0
        self._static_jwks = jwks is not None
        if jwks is not None:
            self._keys = self._parse_jwks(jwks)

    async def verify(self, token: str) -> VerifiedToken:
        try:
            return await self._verify(token)
        except AuthError as exc:
            log.info("token rejected: %s", exc.reason)
            raise

    async def _verify(self, token: str) -> VerifiedToken:
        if not token or token.count(".") != 2:
            raise AuthError("malformed token")
        try:
            header = jwt.get_unverified_header(token)
        except jwt.DecodeError as exc:
            raise AuthError("undecodable header") from exc

        alg = header.get("alg")
        if alg not in self._algorithms:
            raise AuthError(f"algorithm not allowed: {alg!r}")

        key: jwt.PyJWK | str
        if self._s.auth_jwt_mode == "jwks":
            key = await self._jwks_key(header.get("kid"), alg)
        else:
            if self._s.auth_jwt_secret is None:  # AuthSettings validation should make this unreachable
                raise AuthUnavailableError("secret mode without AUTH_JWT_SECRET")
            key = self._s.auth_jwt_secret.get_secret_value()

        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=[alg],
                audience=self._s.auth_audience,
                issuer=self._s.issuer,
                options={"require": REQUIRED_CLAIMS},
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthError("expired") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthError(f"invalid: {type(exc).__name__}") from exc

        try:
            sub = uuid.UUID(str(claims["sub"]))
        except ValueError as exc:
            raise AuthError("sub is not a UUID") from exc
        session = claims.get("session_id")
        return VerifiedToken(sub, str(session) if session is not None else None, int(claims["exp"]))

    async def _jwks_key(self, kid: object, alg: str) -> jwt.PyJWK:
        if not isinstance(kid, str) or not kid:
            raise AuthError("missing kid")
        key = self._keys.get(kid)
        if key is None and not self._static_jwks:
            if time.monotonic() - self._fetched_at >= JWKS_MIN_REFRESH_S or not self._keys:
                await self._refresh()
                key = self._keys.get(kid)
        if key is None:
            raise AuthError("unknown kid")
        if key.algorithm_name != alg:
            raise AuthError(f"kid {kid} is for {key.algorithm_name}, token says {alg}")
        return key

    async def _refresh(self) -> None:
        client = self._http or httpx.AsyncClient(timeout=10)
        try:
            resp = await client.get(self._s.jwks_url)
            resp.raise_for_status()
            self._keys = self._parse_jwks(resp.json())
            self._fetched_at = time.monotonic()
        except (httpx.HTTPError, ValueError) as exc:
            raise AuthUnavailableError(f"cannot load JWKS: {type(exc).__name__}") from exc
        finally:
            if self._http is None:
                await client.aclose()

    def _parse_jwks(self, data: dict[str, Any]) -> dict[str, jwt.PyJWK]:
        keys: dict[str, jwt.PyJWK] = {}
        for jwk in data.get("keys", []):
            alg = jwk.get("alg")
            kid = jwk.get("kid")
            if alg not in self._algorithms or not kid or jwk.get("use", "sig") != "sig":
                continue  # only signing keys for allowed algorithms are ever usable
            keys[kid] = jwt.PyJWK(jwk, algorithm=alg)
        return keys
