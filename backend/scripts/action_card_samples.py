"""Real ActionCards for UI screenshots, with no model and no lasting writes (spec 13.6; Phase 3).

    uv run python scripts/action_card_samples.py CUS-004

For one customer, finds a request of each outcome on their OWN orders and submits it through the real
Action Gateway: completed, waiting for staff approval, not allowed. Every submission runs inside a
transaction that is rolled back, so the database is unchanged afterwards. The clock is pinned to the
fixture's instant (G1), like the seeded data. Prints {"cards": [...]} as JSON.

Local stack only (invariant 20).
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

import asyncpg

from tests.txpool import TxPool, rolled_back
from tollgate.actions import gateway
from tollgate.auth.deps import CustomerContext
from tollgate.clock import FixedClock
from tollgate.config import SupabaseSettings
from tollgate.domain import actions
from tollgate.domain.models import ActionCard, ActionRecord
from tollgate.tools.context import TurnContext

FIXTURE_NOW = datetime.fromisoformat(
    json.loads(Path("eval/fixtures/store_seed.json").read_text())["fixture_now"]
)


RECORDS: dict[str, ActionRecord] = {}  # action records read before each rollback (DECISIONS C2)


async def attempt(pool: TxPool, ctx: TurnContext, action: str, args: dict[str, Any]) -> ActionCard | None:
    async with pool.savepoint():
        ctx.actions.clear()
        await gateway.submit(ctx, action, json.dumps(args))
        card = ctx.actions[-1] if ctx.actions else None
        if card is not None and card.reference and card.reference.startswith("ACT-"):
            record = await actions.get_action(
                pool.connection, ctx.customer.customer_id, card.reference, ctx.clock.now()
            )
            if record is not None:
                RECORDS[card.reference] = record
        return card


async def samples(pool: TxPool, customer_id: str) -> list[ActionCard]:
    conn = pool.connection
    row = await conn.fetchrow("SELECT id, name, email FROM app.customers WHERE id = $1", customer_id)
    if row is None:
        raise SystemExit(f"no customer {customer_id}")
    now = FIXTURE_NOW
    conv = await conn.fetchval(
        "INSERT INTO app.conversations (customer_id) VALUES ($1) RETURNING id", customer_id
    )
    ctx = TurnContext(
        customer=CustomerContext(customer_id, uuid.uuid4(), row["name"], row["email"]),
        pool=cast(asyncpg.Pool, pool),  # TxPool stands in for a pool: every write stays in one rolled-back tx
        conversation_id=conv,
        turn_id=uuid.uuid4(),
        clock=FixedClock(now),
        prompt_version="screenshot-samples",
    )
    lines = await conn.fetch(
        """SELECT o.id, o.status, p.name FROM app.orders o
             JOIN app.order_items i ON i.order_id = o.id JOIN app.products p ON p.id = i.product_id
            WHERE o.customer_id = $1 ORDER BY o.placed_at DESC, i.id""",
        customer_id,
    )
    found: dict[str, ActionCard] = {}
    for line in lines:
        for action in ("request_refund", "issue_store_credit"):
            if {"completed", "waiting_for_approval"} <= set(found):
                break
            args = {"order_id": line["id"], "items": [line["name"]], "reason": "arrived damaged"}
            card = await attempt(pool, ctx, action, args)
            if card is not None and card.state in ("completed", "waiting_for_approval"):
                found.setdefault(card.state, card)
    # No refund or credit completes automatically for some customers (e.g. their rolling-window history):
    # any completed action shows the state, so fall back to an address change, then a ticket.
    # Only what the customer says ("14 Garden Road, Lahore"): the merge keeps the rest (DECISIONS I12).
    address = {"line1": "14 Garden Road", "city": "Lahore"}
    for line in lines:
        if "completed" not in found and line["status"] in ("pending", "paid", "packed"):
            card = await attempt(
                pool, ctx, "update_shipping_address", {"order_id": line["id"], "new_address": address}
            )
            if card is not None and card.state == "completed":
                found["completed"] = card
    if "completed" not in found:
        summary = "Please call me about my last delivery."
        card = await attempt(pool, ctx, "create_ticket", {"summary": summary, "category": "delivery"})
        if card is not None:
            found["completed"] = card
    for line in lines:
        if line["status"] in ("shipped", "delivered") and "not_allowed" not in found:
            card = await attempt(
                pool, ctx, "cancel_order", {"order_id": line["id"], "reason": "changed my mind"}
            )
            if card is not None and card.state == "not_allowed":
                found["not_allowed"] = card
    missing = {"completed", "waiting_for_approval", "not_allowed"} - set(found)
    if missing:
        raise SystemExit(f"{customer_id} has no request with outcome {sorted(missing)}")
    return [found["completed"], found["waiting_for_approval"], found["not_allowed"]]


async def main(customer_id: str) -> int:
    dsn = SupabaseSettings().database_url.get_secret_value()
    if urlsplit(dsn).hostname not in ("localhost", "127.0.0.1", "::1"):
        print("refusing: local stack only", file=sys.stderr)
        return 2
    async with rolled_back(dsn) as pool:
        cards = await samples(pool, customer_id)
    records = {
        c.reference: RECORDS[c.reference].model_dump(mode="json") for c in cards if c.reference in RECORDS
    }
    print(json.dumps({"cards": [c.model_dump(mode="json") for c in cards], "records": records}))
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
