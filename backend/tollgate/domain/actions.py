"""The customer's own action requests, for ActionCards (DECISIONS C2). Filtered by owner in SQL (invariant 3);
a missing request and another customer's look the same (invariant 8)."""

import json
from typing import Any

from tollgate.db import Conn
from tollgate.domain.models import ActionRecord, ActionState, Address, Money

STATE: dict[str, ActionState] = {
    "executed": "completed",
    "approved": "completed",
    "pending_approval": "waiting_for_approval",
    "rejected": "not_allowed",
    "expired": "not_allowed",
}


async def get_action(conn: Conn, customer_id: str, reference: str) -> ActionRecord | None:
    row = await conn.fetchrow(
        """
        SELECT id, action, status, order_id, amount_cents, currency, args, created_at, decided_at
          FROM app.action_requests
         WHERE id = $1 AND customer_id = $2
        """,
        reference,
        customer_id,
    )
    if row is None:
        return None
    args: dict[str, Any] = json.loads(row["args"]) if isinstance(row["args"], str) else row["args"]
    address = args.get("new_address") if row["action"] == "update_shipping_address" else None
    changed = set(args.get("changed", []))
    return ActionRecord(
        reference=row["id"],
        action=row["action"],
        state=STATE[row["status"]],
        order_id=row["order_id"],
        amount=Money(amount_cents=row["amount_cents"], currency=row["currency"])
        if row["amount_cents"]
        else None,
        delivery_address=Address.model_validate(address) if address else None,
        kept_fields=[f for f in Address.model_fields if address and f not in changed],
        at=row["created_at"],
        decided_at=row["decided_at"],
    )
