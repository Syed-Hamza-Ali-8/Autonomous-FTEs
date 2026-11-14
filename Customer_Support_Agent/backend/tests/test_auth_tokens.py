"""Supabase access-token verification (spec Section 2.4; DECISIONS C4; owner Phase 1 gate items).

Unit tests sign with a throwaway EC key served as a static JWKS, so expired, mis-addressed and
forged tokens can be minted. Integration tests use real tokens from the local Auth server.
scripts/mutation_auth.py removes each check and shows the targeted test fails.
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from pydantic import ValidationError

from tests.auth_users import test_email
from tollgate.auth.supabase_jwt import TokenVerifier
from tollgate.config import AuthSettings, SupabaseSettings
from tollgate.errors import AuthError, AuthUnavailableError

ISS = "http://127.0.0.1:54321/auth/v1"
KID = "test-key-1"


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


@pytest.fixture(scope="module")
def ec_key() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(scope="module")
def jwks(ec_key: ec.EllipticCurvePrivateKey) -> dict[str, Any]:
    jwk = json.loads(jwt.algorithms.ECAlgorithm.to_jwk(ec_key.public_key()))
    return {"keys": [{**jwk, "kid": KID, "alg": "ES256", "use": "sig"}]}


@pytest.fixture(scope="module")
def verifier(jwks: dict[str, Any]) -> TokenVerifier:
    settings = AuthSettings(supabase_url="http://127.0.0.1:54321", auth_jwt_mode="jwks")
    return TokenVerifier(settings, jwks=jwks)


def claims(**over: Any) -> dict[str, Any]:
    # Issued 30s in the past: a wall clock that steps backwards (seen on WSL2) must not make a
    # test token look issued-in-the-future and get rejected for an unrelated reason.
    now = int(time.time()) - 30
    base = {
        "sub": str(uuid.uuid4()),
        "aud": "authenticated",
        "iss": ISS,
        "iat": now,
        "exp": now + 600,
        "role": "authenticated",
        "session_id": "s-1",
    }
    base.update(over)
    return {k: v for k, v in base.items() if v is not None}


def es256(key: ec.EllipticCurvePrivateKey, payload: dict[str, Any], kid: str = KID) -> str:
    return jwt.encode(payload, key, algorithm="ES256", headers={"kid": kid})


# --- accepted ----------


async def test_valid_token_is_accepted(verifier: TokenVerifier, ec_key: ec.EllipticCurvePrivateKey) -> None:
    payload = claims()
    got = await verifier.verify(es256(ec_key, payload))
    assert str(got.auth_user_id) == payload["sub"]


# --- rejected: claims ----------


async def test_expired_token_is_rejected(verifier: TokenVerifier, ec_key: ec.EllipticCurvePrivateKey) -> None:
    now = int(time.time())
    with pytest.raises(AuthError, match="expired"):
        await verifier.verify(es256(ec_key, claims(iat=now - 7200, exp=now - 3600)))


@pytest.mark.parametrize("missing", ["exp", "iat", "sub", "aud", "iss"])
async def test_token_missing_required_claim_is_rejected(
    verifier: TokenVerifier, ec_key: ec.EllipticCurvePrivateKey, missing: str
) -> None:
    with pytest.raises(AuthError, match="MissingRequiredClaimError"):
        await verifier.verify(es256(ec_key, claims(**{missing: None})))


async def test_wrong_audience_is_rejected(
    verifier: TokenVerifier, ec_key: ec.EllipticCurvePrivateKey
) -> None:
    with pytest.raises(AuthError, match="InvalidAudienceError"):
        await verifier.verify(es256(ec_key, claims(aud="anon")))


async def test_wrong_issuer_is_rejected(verifier: TokenVerifier, ec_key: ec.EllipticCurvePrivateKey) -> None:
    with pytest.raises(AuthError, match="InvalidIssuerError"):
        await verifier.verify(es256(ec_key, claims(iss="https://evil.example/auth/v1")))


async def test_non_uuid_subject_is_rejected(
    verifier: TokenVerifier, ec_key: ec.EllipticCurvePrivateKey
) -> None:
    with pytest.raises(AuthError, match="UUID"):
        await verifier.verify(es256(ec_key, claims(sub="CUS-002")))


# --- rejected: forged algorithm / key ----------


async def test_alg_none_is_rejected(verifier: TokenVerifier) -> None:
    header = b64(json.dumps({"alg": "none", "typ": "JWT", "kid": KID}).encode())
    token = f"{header}.{b64(json.dumps(claims()).encode())}."
    with pytest.raises(AuthError, match="algorithm not allowed"):
        await verifier.verify(token)


async def test_hs256_signed_with_public_key_is_rejected(
    verifier: TokenVerifier, ec_key: ec.EllipticCurvePrivateKey
) -> None:
    # Classic algorithm-confusion forgery: HMAC "signed" with the published public key as the secret.
    pem = ec_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    header = b64(json.dumps({"alg": "HS256", "typ": "JWT", "kid": KID}).encode())
    body = b64(json.dumps(claims()).encode())
    sig = b64(hmac.new(pem, f"{header}.{body}".encode(), hashlib.sha256).digest())
    with pytest.raises(AuthError, match="algorithm not allowed"):
        await verifier.verify(f"{header}.{body}.{sig}")


async def test_hs256_with_any_secret_is_rejected(verifier: TokenVerifier) -> None:
    token = jwt.encode(claims(), secrets.token_bytes(32), algorithm="HS256", headers={"kid": KID})
    with pytest.raises(AuthError, match="algorithm not allowed"):
        await verifier.verify(token)


async def test_rs256_is_rejected_when_not_configured(verifier: TokenVerifier) -> None:
    rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(claims(), rsa_key, algorithm="RS256", headers={"kid": KID})
    with pytest.raises(AuthError, match="algorithm not allowed"):
        await verifier.verify(token)


async def test_kid_algorithm_mismatch_is_rejected(jwks: dict[str, Any]) -> None:
    # Even with RS256 allowed, a token may not claim RS256 against an ES256 key.
    settings = AuthSettings(supabase_url="http://127.0.0.1:54321", auth_jwt_algorithms=["ES256", "RS256"])
    rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(claims(), rsa_key, algorithm="RS256", headers={"kid": KID})
    with pytest.raises(AuthError, match="is for ES256"):
        await TokenVerifier(settings, jwks=jwks).verify(token)


async def test_token_signed_by_other_key_is_rejected(verifier: TokenVerifier) -> None:
    attacker = ec.generate_private_key(ec.SECP256R1())
    with pytest.raises(AuthError, match="InvalidSignatureError"):
        await verifier.verify(es256(attacker, claims()))


async def test_unknown_kid_is_rejected(verifier: TokenVerifier, ec_key: ec.EllipticCurvePrivateKey) -> None:
    with pytest.raises(AuthError, match="unknown kid"):
        await verifier.verify(es256(ec_key, claims(), kid="not-published"))


async def test_missing_kid_is_rejected(verifier: TokenVerifier, ec_key: ec.EllipticCurvePrivateKey) -> None:
    token = jwt.encode(claims(), ec_key, algorithm="ES256")
    with pytest.raises(AuthError, match="missing kid"):
        await verifier.verify(token)


async def test_tampered_payload_is_rejected(
    verifier: TokenVerifier, ec_key: ec.EllipticCurvePrivateKey
) -> None:
    header, _, sig = es256(ec_key, claims()).split(".")
    forged_body = b64(json.dumps(claims(sub=str(uuid.uuid4()))).encode())
    with pytest.raises(AuthError, match="InvalidSignatureError"):
        await verifier.verify(f"{header}.{forged_body}.{sig}")


@pytest.mark.parametrize("token", ["", "abc", "a.b", "a.b.c.d", "!!.??.**"])
async def test_malformed_tokens_are_rejected(verifier: TokenVerifier, token: str) -> None:
    with pytest.raises(AuthError, match=r"malformed token|undecodable header"):
        await verifier.verify(token)


# --- configuration cannot mix modes ----------


def test_jwks_mode_refuses_symmetric_algorithms() -> None:
    with pytest.raises(ValidationError):
        AuthSettings(
            supabase_url="http://127.0.0.1:54321", auth_jwt_mode="jwks", auth_jwt_algorithms=["HS256"]
        )


def test_secret_mode_refuses_asymmetric_algorithms() -> None:
    with pytest.raises(ValidationError):
        AuthSettings(
            supabase_url="http://127.0.0.1:54321",
            auth_jwt_mode="secret",
            auth_jwt_algorithms=["ES256"],
            auth_jwt_secret="x" * 40,
        )


async def test_secret_mode_accepts_hs256_and_rejects_es256(ec_key: ec.EllipticCurvePrivateKey) -> None:
    secret = secrets.token_urlsafe(48)
    settings = AuthSettings(
        supabase_url="http://127.0.0.1:54321",
        auth_jwt_mode="secret",
        auth_jwt_algorithms=["HS256"],
        auth_jwt_secret=secret,
    )
    v = TokenVerifier(settings)
    payload = claims()
    assert (
        str((await v.verify(jwt.encode(payload, secret, algorithm="HS256"))).auth_user_id) == payload["sub"]
    )
    with pytest.raises(AuthError, match="algorithm not allowed"):
        await v.verify(es256(ec_key, claims()))


# --- integration: the real local Auth server ----------


@pytest.fixture(scope="module")
def local_verifier() -> TokenVerifier:
    return TokenVerifier(AuthSettings())


@pytest.fixture(scope="module")
async def real_user(settings: SupabaseSettings) -> AsyncIterator[tuple[str, str]]:
    """A throwaway Auth user (signup is off, so the admin API creates it). Yields (user_id, token)."""
    assert settings.supabase_service_role_key is not None
    svc = settings.supabase_service_role_key.get_secret_value()
    anon = settings.supabase_anon_key.get_secret_value()
    email, pw = test_email("token"), secrets.token_urlsafe(24)
    async with httpx.AsyncClient(base_url=f"{settings.supabase_url}/auth/v1", timeout=10) as c:
        admin = {"apikey": svc, "Authorization": f"Bearer {svc}"}
        r = await c.post(
            "/admin/users", headers=admin, json={"email": email, "password": pw, "email_confirm": True}
        )
        r.raise_for_status()
        uid = r.json()["id"]
        try:
            t = await c.post(
                "/token",
                params={"grant_type": "password"},
                headers={"apikey": anon},
                json={"email": email, "password": pw},
            )
            t.raise_for_status()
            yield uid, t.json()["access_token"]
        finally:
            await c.delete(f"/admin/users/{uid}", headers=admin)


async def test_real_supabase_token_is_accepted(
    local_verifier: TokenVerifier, real_user: tuple[str, str]
) -> None:
    uid, token = real_user
    assert str((await local_verifier.verify(token)).auth_user_id) == uid


async def test_anon_key_presented_as_token_is_rejected(
    local_verifier: TokenVerifier, settings: SupabaseSettings
) -> None:
    with pytest.raises(AuthError, match="algorithm not allowed"):
        await local_verifier.verify(settings.supabase_anon_key.get_secret_value())


async def test_service_role_key_presented_as_token_is_rejected(
    local_verifier: TokenVerifier, settings: SupabaseSettings
) -> None:
    assert settings.supabase_service_role_key is not None
    with pytest.raises(AuthError, match="algorithm not allowed"):
        await local_verifier.verify(settings.supabase_service_role_key.get_secret_value())


async def test_hs256_forged_with_anon_key_as_secret_is_rejected(
    local_verifier: TokenVerifier, settings: SupabaseSettings, real_user: tuple[str, str]
) -> None:
    uid, _ = real_user
    forged = jwt.encode(claims(sub=uid), settings.supabase_anon_key.get_secret_value(), algorithm="HS256")
    with pytest.raises(AuthError, match="algorithm not allowed"):
        await local_verifier.verify(forged)


async def test_real_token_with_broken_signature_is_rejected(
    local_verifier: TokenVerifier, real_user: tuple[str, str]
) -> None:
    _, token = real_user
    head, body, sig = token.split(".")
    flipped = sig[:-4] + ("AAAA" if not sig.endswith("AAAA") else "BBBB")
    with pytest.raises(AuthError, match="InvalidSignatureError"):
        await local_verifier.verify(f"{head}.{body}.{flipped}")


async def test_unreachable_jwks_fails_closed(ec_key: ec.EllipticCurvePrivateKey) -> None:
    dead = TokenVerifier(AuthSettings(supabase_url="http://127.0.0.1:9"))  # nothing listens on port 9
    with pytest.raises(AuthUnavailableError):
        await dead.verify(es256(ec_key, claims(iss="http://127.0.0.1:9/auth/v1")))


def test_an_internal_supabase_url_moves_only_the_key_fetch_never_the_issuer_check() -> None:
    """Phase 7 Docker (2026-11-14): inside a container, the browser's address 127.0.0.1 is not the host. An
    optional SUPABASE_INTERNAL_URL tells the API where to FETCH the signing keys; the issuer a token
    must carry stays the public SUPABASE_URL, so the token check is exactly as strict."""
    from tollgate.config import AuthSettings

    public = AuthSettings(supabase_url="http://127.0.0.1:54321")
    assert public.jwks_url == "http://127.0.0.1:54321/auth/v1/.well-known/jwks.json"
    boxed = AuthSettings(
        supabase_url="http://127.0.0.1:54321", supabase_internal_url="http://host.docker.internal:54321"
    )
    assert boxed.issuer == "http://127.0.0.1:54321/auth/v1"  # unchanged
    assert boxed.jwks_url == "http://host.docker.internal:54321/auth/v1/.well-known/jwks.json"
