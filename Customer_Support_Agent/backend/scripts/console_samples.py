"""Real staff-console data for UI screenshots, with no model and no lasting writes (spec 13.4, 13.6; Phase 4).

    uv run python scripts/console_samples.py CUS-004

Inside ONE transaction that is rolled back, so the database is unchanged afterwards:
- customer turns run through the REAL runner with a scripted model (zero tokens): messages, the tool trace and
  the gateway's own outcomes are genuine; four requests wait for staff, and two more are decided (one
  approved, one rejected) so the audit log and the decided states have content;
- for the given (e2e) customer: a request left pending past approval expiry (the closed card and the expired
  refund row, J8), and one whose approval re-check now fails (the "couldn't complete" card, J10);
- every response is then read through the REAL API (ASGI, identity fixed by dependency override, clock pinned
  to the fixture's instant, G1) and printed as JSON for Playwright to serve.

Local stack only (invariant 20).
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import asyncpg
import httpx

from tests.fakes import CallTool, Say, ScriptedModel
from tests.txpool import TxPool, rolled_back
from tollgate.actions import cards
from tollgate.agents_def.runner import ChatTurn, LLMRuntime, run_turn
from tollgate.approvals import service
from tollgate.auth.deps import CustomerContext, StaffContext, customer_context, staff_context
from tollgate.clock import FixedClock
from tollgate.config import SupabaseSettings
from tollgate.domain.conversations import OwnedConversation
from tollgate.main import app

NOW = datetime.fromisoformat(json.loads(Path("eval/fixtures/store_seed.json").read_text())["fixture_now"])
WAITING = "I've passed this to our support team for a quick review. You'll see the outcome here in the chat."


async def customer(conn: Any, customer_id: str) -> CustomerContext:
    row = await conn.fetchrow("SELECT id, name, email FROM app.customers WHERE id = $1", customer_id)
    if row is None:
        raise SystemExit(f"no customer {customer_id}")
    return CustomerContext(row["id"], uuid.uuid4(), row["name"], row["email"])


async def turn(pool: TxPool, customer_id: str, text: str, steps: list[Any], at: datetime) -> uuid.UUID:
    """One customer turn through the real runner with a scripted model; returns the conversation id."""
    conn = pool.connection
    conv: uuid.UUID = await conn.fetchval(
        "INSERT INTO app.conversations (customer_id) VALUES ($1) RETURNING id", customer_id
    )
    llm = LLMRuntime(
        model=ScriptedModel(steps), model_name="scripted", daily_budget=10**9, turn_estimate=1, ledger=None
    )
    chat = ChatTurn(
        customer=await customer(conn, customer_id),
        conversation=OwnedConversation(id=conv, order_id=None),
        client_message_id=uuid.uuid4(),
        message=text,
    )
    async for _ in run_turn(pool, llm, chat, FixedClock(at)):  # type: ignore[arg-type]
        pass
    # Sample polish only (rolled back): messages carry the turn's pinned time, not the wall clock. The tool
    # trace keeps its real times: app.tool_calls is append-only, as it should be.
    await conn.execute(
        "UPDATE app.messages SET created_at = $2::timestamptz + (id - (SELECT min(id) FROM app.messages"
        " WHERE conversation_id = $1)) * interval '20 seconds' WHERE conversation_id = $1",
        conv,
        at,
    )
    return conv


def refund(order_id: str, item: str, reason: str, cents: int | None = None) -> CallTool:
    args: dict[str, Any] = {"order_id": order_id, "items": [item], "reason": reason}
    return CallTool("request_refund", args | ({"amount_cents": cents} if cents else {}))


def credit(order_id: str, item: str, reason: str, cents: int) -> CallTool:
    args = {"order_id": order_id, "items": [item], "reason": reason, "amount_cents": cents}
    return CallTool("issue_store_credit", args)


def get(order_id: str) -> CallTool:
    return CallTool("get_order", {"order_id": order_id})


HELD = (
    "I've passed this to our support team to review before anything changes."
    " You'll see the outcome here in the chat."
)
# (customer, what they say, the scripted model's steps, how long ago). The first four wait for staff.
PENDING: list[tuple[str, str, list[Any], timedelta]] = [
    ("CUS-031", "The earbuds from ORD-1005 have no sound in one ear. Refund please.",
     [get("ORD-1005"), refund("ORD-1005", "Wireless Earbuds", "no sound in one ear"), Say(WAITING)],
     timedelta(hours=20)),
    ("CUS-047", "The 4K monitor from ORD-1161 has dead pixels. $200 in store credit would be fine.",
     [get("ORD-1161"), credit("ORD-1161", "4K Monitor 27in", "dead pixels", 20000), Say(WAITING)],
     timedelta(hours=3)),
    ("CUS-045", "Someone used my card for ORD-1159! Please cancel it.",
     [get("ORD-1159"), CallTool("cancel_order", {"order_id": "ORD-1159", "reason": "misuse"}), Say(HELD)],
     timedelta(minutes=40)),
    ("CUS-025", "Both ceramic dinner sets in ORD-1058 arrived chipped. Can I get a refund?",
     [get("ORD-1058"), refund("ORD-1058", "Ceramic Dinner Set", "arrived chipped"), Say(WAITING)],
     timedelta(minutes=12)),
]  # fmt: skip
TO_REJECT = ("CUS-017", "This charge on ORD-1042 is unauthorised, refund it.",
             [get("ORD-1042"), refund("ORD-1042", "Electric Kettle 1.7L", "unauthorised"), Say(WAITING)],
             timedelta(hours=6))  # fmt: skip
TO_APPROVE = ("CUS-019", "Both smart watches in ORD-1098 stopped working. Please refund them.",
              [get("ORD-1098"), refund("ORD-1098", "Smart Watch", "stopped working"), Say(WAITING)],
              timedelta(hours=8))  # fmt: skip


async def latest_ref(conn: Any, conv: uuid.UUID) -> str:
    ref: str = await conn.fetchval(
        "SELECT id FROM app.action_requests WHERE conversation_id = $1 ORDER BY id DESC LIMIT 1", conv
    )
    return ref


async def staff_world(pool: TxPool) -> uuid.UUID:
    conn = pool.connection
    # The seeded support lead decides, if there is one (J13); otherwise a stand-in row (rolled back).
    staff_id: uuid.UUID = await conn.fetchval(
        "SELECT id FROM app.staff_users WHERE role = 'support_lead' ORDER BY created_at LIMIT 1"
    ) or await conn.fetchval(
        "INSERT INTO app.staff_users (name, email, role) VALUES ('Maya Chen', 'maya.chen@example.test',"
        " 'support_lead') RETURNING id"
    )
    for who, text, steps, ago in PENDING:
        await turn(pool, who, text, steps, NOW - ago)
    rejected = await turn(pool, *TO_REJECT[:3], NOW - TO_REJECT[3])
    approved = await turn(pool, *TO_APPROVE[:3], NOW - TO_APPROVE[3])
    note = "Customer confirmed by phone that they made the purchase; the kettle works."
    await service.reject(conn, staff_id, await latest_ref(conn, rejected), note, NOW - timedelta(hours=5))
    ref = await latest_ref(conn, approved)
    row = await conn.fetchrow("SELECT amount_cents, currency FROM app.action_requests WHERE id = $1", ref)
    if row is None:
        raise SystemExit(f"{ref} vanished")
    await service.approve(conn, staff_id, ref, row["amount_cents"], row["currency"], NOW - timedelta(hours=7))
    return staff_id


async def customer_world(pool: TxPool, customer_id: str, staff_id: uuid.UUID) -> dict[str, Any]:
    """A request pending past expiry, and one whose re-check now fails, on the customer's own order."""
    from tests.probe_harness import call_tool, new_context, new_conversation

    conn = pool.connection
    lines = await conn.fetch(
        """SELECT o.id, p.id AS product, p.name FROM app.orders o
             JOIN app.order_items i ON i.order_id = o.id JOIN app.products p ON p.id = i.product_id
            WHERE o.customer_id = $1 AND o.status IN ('delivered', 'partially_refunded')
              AND NOT p.final_sale AND NOT p.digital ORDER BY o.delivered_at DESC, i.id""",
        customer_id,
    )
    for line in lines:
        made: list[tuple[dict[str, Any], datetime]] = []
        for at in (NOW - timedelta(hours=49), NOW - timedelta(hours=1)):
            conv = await new_conversation(conn, customer_id)
            ctx = await new_context(conn, pool, customer_id, uuid.uuid4(), conv)
            ctx.clock, ctx.fraud_signal = FixedClock(at), True  # any refund in a flagged turn waits for staff
            args = {"order_id": line["id"], "items": [line["name"]], "reason": "arrived damaged"}
            result = await call_tool(ctx, "request_refund", args)
            if result.get("status") != "pending_approval":
                break
            made.append((result, at))
        if len(made) == 2:
            closed, stale = made[0][0], made[1][0]
            # The re-check now fails: the item became final sale after the request (all rolled back).
            await conn.execute("UPDATE app.products SET final_sale = true WHERE id = $1", line["product"])
            await service.approve(
                conn, staff_id, stale["reference"], stale["amount_cents"], stale["currency"], NOW
            )
            await conn.execute("UPDATE app.products SET final_sale = false WHERE id = $1", line["product"])
            shown = [cards.card_for("request_refund", "queued", r, line["id"], at) for r, at in made]
            return {
                "order_id": line["id"],
                "cards": [c.model_dump(mode="json") for c in shown if c is not None],
                "refs": [closed["reference"], stale["reference"]],
            }
    raise SystemExit(f"{customer_id} has no delivered line that can wait for staff")


async def read_api(
    pool: TxPool, staff_id: uuid.UUID, customer_id: str, mine: dict[str, Any]
) -> dict[str, Any]:
    conn = pool.connection
    app.state.pool, app.state.clock = pool, FixedClock(NOW)
    app.dependency_overrides[staff_context] = lambda: StaffContext(
        staff_id, uuid.uuid4(), "Maya Chen", "maya.chen@example.test", "support_lead"
    )
    me = await customer(conn, customer_id)
    app.dependency_overrides[customer_context] = lambda: me
    out: dict[str, Any] = {}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://api.test") as c:

        async def get(path: str) -> Any:
            r = await c.get(path)
            r.raise_for_status()
            return r.json()

        queue = await get("/v1/staff/approvals")
        decided = [
            r["id"] for r in await conn.fetch("SELECT action_request_id AS id FROM app.approvals ORDER BY id")
        ]
        refs = [i["reference"] for i in queue["items"]] + decided
        details = {ref: await get(f"/v1/staff/approvals/{ref}") for ref in refs}
        convs = {
            d["approval"]["conversation_id"] for d in details.values() if d["approval"]["conversation_id"]
        }
        out["staff"] = {
            "profile": await get("/v1/staff/me"),
            "queue": queue,
            "details": details,
            "audit": await get("/v1/staff/audit?page=1&page_size=25"),
            "conversations": {cid: await get(f"/v1/staff/conversations/{cid}") for cid in convs},
        }
        out["customer"] = {
            "cards": mine["cards"],
            "records": {ref: await get(f"/v1/actions/{ref}") for ref in mine["refs"]},
            "order_id": mine["order_id"],
            "order": await get(f"/v1/orders/{mine['order_id']}"),
        }
    app.dependency_overrides.clear()
    return out


async def main(customer_id: str) -> int:
    dsn = SupabaseSettings().database_url.get_secret_value()
    if urlsplit(dsn).hostname not in ("localhost", "127.0.0.1", "::1"):
        print("refusing: local stack only", file=sys.stderr)
        return 2
    async with rolled_back(dsn) as pool:
        staff_id = await staff_world(pool)
        mine = await customer_world(pool, customer_id, staff_id)
        data = await read_api(pool, staff_id, customer_id, mine)
    print(json.dumps(data))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    try:
        sys.exit(asyncio.run(main(sys.argv[1])))
    except asyncpg.PostgresError as exc:
        print(f"database error: {exc}", file=sys.stderr)
        sys.exit(1)
