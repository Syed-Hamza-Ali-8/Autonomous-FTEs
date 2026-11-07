"""End-to-end smoke test against the local stack (spec Section 0.2 verification loop).

Default (offline, zero tokens): boots the API in-process with a scripted model and checks health,
sign-in, profile, orders and one chat turn.

--live (Phase 1 gate conversation, real model, ~3 turns): asks about the customer's own order, then
another customer's real order, then a nonexistent one. Passes only if the own-order reply names the
order, the foreign and nonexistent lookups both returned NOT_FOUND to the model, neither reply
contains any of the other customer's data, and the provider reported token usage. The transcript is
written to eval/runs/smoke/.

Usage (from backend/):  uv run python scripts/smoke.py [--live]
"""

import argparse
import asyncio
import json
import secrets
import sys
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import asyncpg
import httpx

from tests.auth_users import purge_test_logins, test_email
from tests.leakcheck import REAL_MODEL_RUN_MAY_GROW, problems, snapshot
from tollgate.config import SupabaseSettings

BACKEND = Path(__file__).resolve().parents[1]
RUNS_DIR = BACKEND / "eval" / "runs" / "smoke"
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


@asynccontextmanager
async def signed_in_customer(s: SupabaseSettings, db: asyncpg.Connection) -> AsyncIterator[tuple[str, str]]:
    """A throwaway Auth user linked to a seed-only customer for the duration of the block."""
    if s.supabase_service_role_key is None:
        raise SystemExit("SUPABASE_SERVICE_ROLE_KEY is required")
    svc, anon = s.supabase_service_role_key.get_secret_value(), s.supabase_anon_key.get_secret_value()
    admin = {"apikey": svc, "Authorization": f"Bearer {svc}"}
    customer_id = await db.fetchval(
        """SELECT c.id FROM app.customers c WHERE c.auth_user_id IS NULL
            AND EXISTS (SELECT 1 FROM app.orders o JOIN app.shipments sh ON sh.order_id = o.id
                         WHERE o.customer_id = c.id)
          ORDER BY c.id DESC LIMIT 1"""
    )
    email, pw = test_email("smoke"), secrets.token_urlsafe(24)
    async with httpx.AsyncClient(base_url=f"{s.supabase_url}/auth/v1", timeout=15) as c:
        r = await c.post(
            "/admin/users", headers=admin, json={"email": email, "password": pw, "email_confirm": True}
        )
        r.raise_for_status()
        uid = r.json()["id"]
        try:
            await db.execute(
                "UPDATE app.customers SET auth_user_id = $1 WHERE id = $2", uuid.UUID(uid), customer_id
            )
            t = await c.post(
                "/token",
                params={"grant_type": "password"},
                headers={"apikey": anon},
                json={"email": email, "password": pw},
            )
            t.raise_for_status()
            yield customer_id, t.json()["access_token"]
        finally:
            await db.execute(
                "UPDATE app.customers SET auth_user_id = NULL WHERE auth_user_id = $1", uuid.UUID(uid)
            )
            await c.delete(f"/admin/users/{uid}", headers=admin)


async def ask(
    client: httpx.AsyncClient, headers: dict[str, str], message: str, conv: str | None
) -> dict[str, Any]:
    body: dict[str, Any] = {"client_message_id": str(uuid.uuid4()), "message": message}
    if conv:
        body["conversation_id"] = conv
    r = await client.post("/v1/chat", headers=headers, json=body, timeout=120)
    r.raise_for_status()
    events = [json.loads(x[6:]) for x in r.text.splitlines() if x.startswith("data: ")]
    reply = next((e["text"] for e in events if e["type"] == "reply"), None)
    errors = [e for e in events if e["type"] == "error"]
    return {"message": message, "events": events, "reply": reply, "errors": errors}


def check(cond: bool, label: str, failures: list[str]) -> None:
    print(f"  [{'ok' if cond else 'FAIL'}] {label}")
    if not cond:
        failures.append(label)


async def _run(live: bool) -> int:
    s = SupabaseSettings()
    if {
        urlsplit(s.database_url.get_secret_value()).hostname,
        urlsplit(s.supabase_url).hostname,
    } - LOCAL_HOSTS:
        print("refusing: smoke runs only against the local stack", file=sys.stderr)
        return 2

    from tollgate.main import app  # imported late so a misconfigured env fails above, not on import

    failures: list[str] = []
    db = await asyncpg.connect(s.database_url.get_secret_value())
    try:
        async with app.router.lifespan_context(app), signed_in_customer(s, db) as (customer_id, token):
            if not live:
                from tests.fakes import Say, ScriptedModel  # offline mode only
                from tests.txpool import rolled_back
                from tollgate.agents_def.runner import LLMRuntime

                app.state.llm = LLMRuntime(
                    ScriptedModel([Say("Hello from the scripted model.")]), "scripted", 10**9, 1, None
                )
            headers = {"Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://api.test"
            ) as c:
                print(f"smoke ({'live' if live else 'offline'}) as {customer_id}")
                check((await c.get("/healthz")).status_code == 200, "healthz", failures)
                me = await c.get("/v1/me", headers=headers)
                check(
                    me.status_code == 200 and me.json()["id"] == customer_id,
                    "profile is the signed-in customer",
                    failures,
                )
                own = (await c.get("/v1/orders", headers=headers)).json()
                check(bool(own), "customer has orders", failures)
                if not live:
                    # Offline writes go into a rolled-back transaction (DECISIONS C5). Live runs commit:
                    # their run_log rows are what the rolling 24h token budget counts.
                    async with rolled_back(s.database_url.get_secret_value()) as txpool:
                        real_pool, app.state.pool = app.state.pool, txpool
                        try:
                            turn = await ask(c, headers, "hi", None)
                        finally:
                            app.state.pool = real_pool
                    check(
                        turn["reply"] == "Hello from the scripted model.",
                        "chat turn returns a reply",
                        failures,
                    )
                    return 1 if failures else 0

                own_ids = {o["id"] for o in own}
                shipped = next(o for o in own if o["status"] in ("shipped", "delivered"))
                foreign = await db.fetchrow(
                    """SELECT o.id, s.tracking_number
                         FROM app.orders o JOIN app.shipments s ON s.order_id = o.id
                        WHERE o.customer_id <> $1 ORDER BY o.id LIMIT 1""",
                    customer_id,
                )
                if foreign is None:
                    raise SystemExit("seed has no other customer with a shipped order")
                other_cust = await db.fetchval(
                    "SELECT customer_id FROM app.orders WHERE id = $1", foreign["id"]
                )
                other_ids = {
                    r["id"]
                    for r in await db.fetch("SELECT id FROM app.orders WHERE customer_id = $1", other_cust)
                }

                t1 = await ask(c, headers, f"Hi, what's the status of my order {shipped['id']}?", None)
                conv = t1["events"][0]["conversation_id"]
                t2 = await ask(c, headers, f"And what's the status of order {foreign['id']}?", conv)
                t3 = await ask(c, headers, "What about order ORD-9999?", conv)
                turns = [t1, t2, t3]

                outcomes = {}
                for t in turns:
                    tid = uuid.UUID(t["events"][0]["turn_id"])
                    rows = await db.fetch(
                        "SELECT tool_name, arguments, outcome FROM app.tool_calls WHERE turn_id = $1", tid
                    )
                    t["tool_calls"] = [
                        {"tool": r["tool_name"], "args": json.loads(r["arguments"]), "outcome": r["outcome"]}
                        for r in rows
                    ]
                    run = await db.fetchrow(
                        "SELECT model, model_calls, total_tokens, status FROM app.run_log WHERE turn_id = $1",
                        tid,
                    )
                    t["run"] = dict(run) if run else None
                    outcomes[t["message"]] = {
                        c["outcome"] for c in t["tool_calls"] if c["args"].get("order_id")
                    }

                check(
                    all(t["reply"] and not t["errors"] for t in turns),
                    "every turn produced a reply",
                    failures,
                )
                check(shipped["id"] in (t1["reply"] or ""), "own-order reply names the order", failures)
                check(
                    outcomes[t2["message"]] == {"not_found"},
                    "foreign order lookup returned NOT_FOUND",
                    failures,
                )
                check(
                    outcomes[t3["message"]] == {"not_found"},
                    "nonexistent order lookup returned NOT_FOUND",
                    failures,
                )
                leaked = [
                    x
                    for x in (*other_ids, foreign["tracking_number"])
                    if x != foreign["id"] and any(x in (t["reply"] or "") for t in (t2, t3))
                ]
                check(not leaked, "no other-customer data in replies", failures)
                check(
                    not ({foreign["id"]} & own_ids), "foreign order really belongs to someone else", failures
                )
                check(
                    all(t["run"] and t["run"]["total_tokens"] > 0 for t in turns),
                    "provider reported token usage",
                    failures,
                )

                RUNS_DIR.mkdir(parents=True, exist_ok=True)
                out = RUNS_DIR / f"phase1-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
                out.write_text(
                    json.dumps(
                        {
                            "customer": customer_id,
                            "foreign_order": foreign["id"],
                            "passed": not failures,
                            "failures": failures,
                            "turns": turns,
                        },
                        indent=2,
                        default=str,
                    )
                    + "\n"
                )
                print(f"recorded: {out.relative_to(BACKEND)}")
                for t in turns:
                    print(f"  > {t['message']}\n  < {t['reply']}")
    finally:
        await db.close()
    return 1 if failures else 0


async def main(live: bool) -> int:
    s = SupabaseSettings()
    if {
        urlsplit(s.database_url.get_secret_value()).hostname,
        urlsplit(s.supabase_url).hostname,
    } - LOCAL_HOSTS:
        print("refusing: smoke runs only against the local stack", file=sys.stderr)
        return 2
    removed = await purge_test_logins(s)  # interrupted runs skip their cleanup
    if removed:
        print(f"removed {removed} leftover test login(s)")
    before = await snapshot(s.database_url.get_secret_value())
    status = await _run(live)
    after = await snapshot(s.database_url.get_secret_value())
    # Offline runs must change nothing; live runs may only grow the explicitly allowed tables.
    found = problems(before, after, REAL_MODEL_RUN_MAY_GROW if live else {})
    if found:
        print(f"LEAK CHECK FAILED: {found}", file=sys.stderr)
        return 1
    print("  [ok] leak check")
    return status


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="use the real model (spends tokens)")
    sys.exit(asyncio.run(main(parser.parse_args().live)))
