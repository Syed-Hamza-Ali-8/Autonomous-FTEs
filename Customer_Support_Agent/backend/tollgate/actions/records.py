"""Rows every action hangs off: the action request, and a refund or store-credit row (DECISIONS J7).

Shared by the executors (rows of an EXECUTED action) and the approval queue (rows of a PENDING one). Inserting
an undecided request is queueing, not deciding: the database refuses a request created already decided
(`action_requests_born_undecided`), and only a decision row lets one move on
(`action_requests_decision_requires_approval`). Nothing here updates a request or decides anything.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from tollgate.db import Conn

MoneyAction = Literal["request_refund", "issue_store_credit"]


@dataclass(frozen=True)
class Request:
    """The action request row every effect hangs off."""

    customer_id: str
    conversation_id: uuid.UUID | None
    turn_id: uuid.UUID
    action: str
    order_id: str | None
    decision: Literal["ALLOW", "NEEDS_APPROVAL"]
    now: datetime
    order_item_ids: tuple[int, ...] = ()
    amount_cents: int | None = None
    currency: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()


async def insert_request(conn: Conn, req: Request) -> str:
    status = "executed" if req.decision == "ALLOW" else "pending_approval"
    request_id: str = await conn.fetchval(
        "INSERT INTO app.action_requests (customer_id, conversation_id, turn_id, action, order_id,"
        " order_item_ids, amount_cents, currency, args, decision, reasons, status, created_at)"
        " VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, $11::jsonb, $12, $13) RETURNING id",
        req.customer_id,
        req.conversation_id,
        req.turn_id,
        req.action,
        req.order_id,
        list(req.order_item_ids),
        req.amount_cents,
        req.currency,
        json.dumps(req.args),
        req.decision,
        json.dumps(list(req.reasons)),
        status,
        req.now,
    )
    return request_id


async def insert_compensation(
    conn: Conn, kind: MoneyAction, request_id: str, req: Request, status: str, reason: str
) -> str:
    """A refund or store-credit row for `req` (succeeded when executed, pending_approval when queued)."""
    if kind == "request_refund":
        sql = (
            "INSERT INTO app.refunds (order_id, currency, amount_cents, status, source, action_request_id,"
            " reason, created_at) VALUES ($1, $2, $3, $4, 'action', $5, $6, $7) RETURNING id"
        )
        row_id: str = await conn.fetchval(
            sql, req.order_id, req.currency, req.amount_cents, status, request_id, reason, req.now
        )
        return row_id
    row_id = await conn.fetchval(
        "INSERT INTO app.store_credits (customer_id, order_id, currency, amount_cents, status,"
        " action_request_id, reason, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id",
        req.customer_id,
        req.order_id,
        req.currency,
        req.amount_cents,
        status,
        request_id,
        reason,
        req.now,
    )
    return row_id
