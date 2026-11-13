"""Throwaway sign-ins for Playwright (LOCAL stack only, invariant 20).

  uv run python scripts/e2e_users.py create <out.json>    # 2 customers (seed-only, linked); checks the lead
  uv run python scripts/e2e_users.py teardown <out.json>  # unlink and delete them

Picks the seed-only customers with the most orders (so pages have content), creates fresh Auth users
with random passwords, links them, and writes {email, password, customer_id, order_ids} to <out.json>.
That file is git-ignored; the passwords are single-use and die at teardown.
"""

import asyncio
import json
import secrets
import sys
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import asyncpg
import httpx
from pydantic_settings import BaseSettings

from tests.auth_users import purge_test_logins, test_email
from tests.leakcheck import REAL_MODEL_RUN_MAY_GROW, problems, snapshot
from tollgate.config import _COMMON, SupabaseSettings


class StaffSettings(BaseSettings):
    model_config = _COMMON
    demo_staff_email: str = "maya.chen@northwind.example"


LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


async def create() -> dict[str, object]:
    s = SupabaseSettings()
    if s.supabase_service_role_key is None:
        raise SystemExit("SUPABASE_SERVICE_ROLE_KEY is required")
    svc = s.supabase_service_role_key.get_secret_value()
    admin = {"apikey": svc, "Authorization": f"Bearer {svc}"}
    db = await asyncpg.connect(s.database_url.get_secret_value())
    try:
        # The REAL support lead, seeded by seed_store.py from .env (DECISIONS J13). Only its email is written
        # here; the console tests read the password from .env at run time, so it is never copied.
        staff_email = StaffSettings().demo_staff_email.strip().lower()
        if not await db.fetchval(
            "SELECT 1 FROM app.staff_users WHERE email = $1 AND auth_user_id IS NOT NULL", staff_email
        ):
            raise SystemExit(
                "the support lead is not seeded: set DEMO_STAFF_PASSWORD in .env, then run"
                " `uv run python scripts/seed_store.py staff`"
            )
        picks = await db.fetch(
            """SELECT c.id, c.name FROM app.customers c
                WHERE c.auth_user_id IS NULL
                  AND EXISTS (SELECT 1 FROM app.orders o JOIN app.refunds r ON r.order_id = o.id
                               WHERE o.customer_id = c.id)
                ORDER BY (SELECT count(*) FROM app.orders o WHERE o.customer_id = c.id) DESC, c.id
                LIMIT 2"""
        )
        if len(picks) < 2:
            raise SystemExit("need two seed-only customers with refunded orders")
        people = []
        async with httpx.AsyncClient(base_url=f"{s.supabase_url}/auth/v1", headers=admin, timeout=15) as c:
            for row in picks:
                email, pw = test_email("e2e"), secrets.token_urlsafe(24)
                r = await c.post("/admin/users", json={"email": email, "password": pw, "email_confirm": True})
                r.raise_for_status()
                uid = r.json()["id"]
                await db.execute(
                    "UPDATE app.customers SET auth_user_id = $1 WHERE id = $2", uuid.UUID(uid), row["id"]
                )
                ids = [
                    r["id"]
                    for r in await db.fetch(
                        "SELECT id FROM app.orders WHERE customer_id = $1 ORDER BY placed_at DESC", row["id"]
                    )
                ]
                featured = await db.fetchval(
                    """SELECT o.id FROM app.orders o JOIN app.shipments sh ON sh.order_id = o.id
                        WHERE o.customer_id = $1
                          AND EXISTS (SELECT 1 FROM app.refunds r WHERE r.order_id = o.id)
                        ORDER BY o.placed_at DESC LIMIT 1""",
                    row["id"],
                )
                people.append(
                    {
                        "auth_user_id": uid,
                        "email": email,
                        "password": pw,
                        "customer_id": row["id"],
                        "name": row["name"],
                        "order_ids": ids,
                        "featured_order": featured,
                    }
                )
        print(f"created {len(people)} e2e customers: {[p['customer_id'] for p in people]}")
        return {"customers": people, "staff": {"email": staff_email}}
    finally:
        await db.close()


async def teardown(people: list[dict[str, str]]) -> None:
    s = SupabaseSettings()
    if s.supabase_service_role_key is None:
        raise SystemExit("SUPABASE_SERVICE_ROLE_KEY is required")
    svc = s.supabase_service_role_key.get_secret_value()
    db = await asyncpg.connect(s.database_url.get_secret_value())
    try:
        async with httpx.AsyncClient(
            base_url=f"{s.supabase_url}/auth/v1",
            headers={"apikey": svc, "Authorization": f"Bearer {svc}"},
            timeout=15,
        ) as c:
            for p in people:
                await db.execute(
                    "UPDATE app.customers SET auth_user_id = NULL WHERE auth_user_id = $1",
                    uuid.UUID(p["auth_user_id"]),
                )
                await c.delete(f"/admin/users/{p['auth_user_id']}")
    finally:
        await db.close()
    print(f"removed {len(people)} e2e customers")


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("create", "teardown"):
        print(__doc__, file=sys.stderr)
        return 2
    s = SupabaseSettings()
    if {
        urlsplit(s.database_url.get_secret_value()).hostname,
        urlsplit(s.supabase_url).hostname,
    } - LOCAL_HOSTS:
        print("refusing: e2e users are created only on the local stack", file=sys.stderr)
        return 2
    out = Path(sys.argv[2]).resolve()
    baseline = out.with_name("db-before.json")
    if sys.argv[1] == "create":
        removed = asyncio.run(purge_test_logins(s))  # interrupted runs skip their teardown
        if removed:
            print(f"removed {removed} leftover test login(s)")
        baseline.parent.mkdir(parents=True, exist_ok=True)
        baseline.write_text(json.dumps(asyncio.run(snapshot(s.database_url.get_secret_value()))))
        out.write_text(json.dumps(asyncio.run(create()), indent=2))
        return 0
    if out.exists():
        asyncio.run(teardown(json.loads(out.read_text())["customers"]))  # the support lead stays (seeded)
        out.unlink()
    if baseline.exists():
        # Playwright runs make real model calls: only the explicitly allowed tables may grow.
        found = problems(
            json.loads(baseline.read_text()),
            asyncio.run(snapshot(s.database_url.get_secret_value())),
            REAL_MODEL_RUN_MAY_GROW,
        )
        baseline.unlink()
        if found:
            print(f"LEAK CHECK FAILED: {found}", file=sys.stderr)
            return 1
        print("leak check: only allowed tables grew")
    return 0


if __name__ == "__main__":
    sys.exit(main())
