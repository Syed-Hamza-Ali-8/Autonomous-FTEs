"""The customer's own action requests, for ActionCards (DECISIONS C2). Filtered by owner in SQL (invariant 3);
a missing request and another customer's look the same (invariant 8). A pending request past approval expiry
reads as `closed` whether or not the expiry has been written yet (J8)."""

import json
from datetime import datetime
from typing import Any

from tollgate.actions import cards
from tollgate.approvals import expiry
from tollgate.db import Conn
from tollgate.domain.models import ActionRecord, ActionState, Address, Money

STATE: dict[str, ActionState] = {
    "executed": "completed",
    "approved": "completed",
    "pending_approval": "waiting_for_approval",
    "rejected": "not_allowed",
    "expired": "closed",
}


def _closed(status: str, created_at: datetime, now: datetime) -> bool:
    """R1 of the derived expiry predicate (J8); its own seam for mutation M39."""
    return status == "pending_approval" and expiry.is_expired(created_at, now)


async def get_action(conn: Conn, customer_id: str, reference: str, now: datetime) -> ActionRecord | None:
    row = await conn.fetchrow(
        """
        SELECT a.id, a.action, a.status, a.order_id, a.amount_cents, a.currency, a.args, a.created_at,
               a.decided_at, p.decision
          FROM app.action_requests a
          LEFT JOIN app.approvals p ON p.action_request_id = a.id
         WHERE a.id = $1 AND a.customer_id = $2
        """,
        reference,
        customer_id,
    )
    if row is None:
        return None
    args: dict[str, Any] = json.loads(row["args"]) if isinstance(row["args"], str) else row["args"]
    address = args.get("new_address") if row["action"] == "update_shipping_address" else None
    changed = set(args.get("changed", []))
    state = "closed" if _closed(row["status"], row["created_at"], now) else STATE[row["status"]]
    if row["decision"] == "failed_recheck":
        state = "not_completed"  # stored as rejected, but nobody decided against it (J10)
    amount = (
        Money(amount_cents=row["amount_cents"], currency=row["currency"]) if row["amount_cents"] else None
    )
    return ActionRecord(
        reference=row["id"],
        action=row["action"],
        state=state,
        order_id=row["order_id"],
        amount=amount,
        explanation=cards.record_text(state, row["action"], amount),
        delivery_address=Address.model_validate(address) if address else None,
        kept_fields=[f for f in Address.model_fields if address and f not in changed],
        at=row["created_at"],
        decided_at=row["decided_at"],
    )
