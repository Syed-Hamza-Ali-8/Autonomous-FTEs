"""Throwaway Supabase Auth logins for tests, smoke runs and Playwright (LOCAL stack only).

Every test-created login uses one recognisable address pattern, so leftovers can always be found:
    tollgate-test+<purpose>-<hex>@example.test
Interrupted runs skip their teardown, so every run calls `purge_test_logins()` at its START.
Deleting an Auth user also unlinks it from app.customers (FK ON DELETE SET NULL).
"""

import re
import secrets
from urllib.parse import urlsplit

import httpx

from tollgate.config import SupabaseSettings

TEST_EMAIL = re.compile(r"^tollgate-test\+[a-z0-9-]+-[0-9a-f]{8}@example\.test$")
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def test_email(purpose: str) -> str:
    if not re.fullmatch(r"[a-z0-9-]+", purpose):
        raise ValueError("purpose must be lowercase letters, digits or dashes")
    return f"tollgate-test+{purpose}-{secrets.token_hex(4)}@example.test"


test_email.__test__ = False  # type: ignore[attr-defined]  # a helper, not a pytest test


def _admin(settings: SupabaseSettings) -> dict[str, str]:
    if urlsplit(settings.supabase_url).hostname not in LOCAL_HOSTS:
        raise SystemExit("refusing: test logins are only managed on the local stack")
    if settings.supabase_service_role_key is None:
        raise SystemExit("SUPABASE_SERVICE_ROLE_KEY is required")
    key = settings.supabase_service_role_key.get_secret_value()
    return {"apikey": key, "Authorization": f"Bearer {key}"}


async def purge_test_logins(settings: SupabaseSettings) -> int:
    """Delete every Auth user whose email matches the test pattern. Returns how many were removed."""
    headers = _admin(settings)
    removed = 0
    async with httpx.AsyncClient(
        base_url=f"{settings.supabase_url}/auth/v1", headers=headers, timeout=15
    ) as c:
        leftovers: list[str] = []
        page = 1
        while True:
            resp = await c.get("/admin/users", params={"page": page, "per_page": 200})
            resp.raise_for_status()
            users = resp.json().get("users", [])
            leftovers += [u["id"] for u in users if TEST_EMAIL.fullmatch(u.get("email") or "")]
            if len(users) < 200:
                break
            page += 1
        for uid in leftovers:
            r = await c.delete(f"/admin/users/{uid}")
            r.raise_for_status()
            removed += 1
    return removed
