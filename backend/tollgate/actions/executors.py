"""Executors: the only code that moves money or changes an order (invariant 6).

Importable only by actions/gateway.py and approvals/service.py (tests/test_action_boundary.py, probe st01).
Every function runs inside the gateway's transaction, after ownership, recompute, idempotency and policy;
none re-decides anything. Amounts arrive recomputed from the database, never from the model (invariant 4),
and the refund trigger still caps succeeded refunds at the captured total (invariant 9).
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


async def sync_refund_status(conn: Conn, order_id: str | None, customer_id: str) -> str:
    """Set the order's status from its succeeded refunds, in the refund's transaction (DECISIONS I10).

    All of the captured total refunded -> refunded; part of it -> partially_refunded. A cancelled order stays
    cancelled even though its cancellation carried a full refund. Pending refunds count for nothing here.
    """
    status: str = await conn.fetchval(
        """
        UPDATE app.orders o
           SET status = CASE WHEN t.refunded >= t.captured THEN 'refunded' ELSE 'partially_refunded' END
          FROM (SELECT (SELECT coalesce(sum(amount_cents), 0) FROM app.refunds
                         WHERE order_id = $1 AND status = 'succeeded') AS refunded,
                       (SELECT coalesce(sum(amount_cents), 0) FROM app.payments
                         WHERE order_id = $1) AS captured) t
         WHERE o.id = $1 AND o.customer_id = $2 AND o.status <> 'cancelled' AND t.refunded > 0
        RETURNING o.status
        """,
        order_id,
        customer_id,
    )
    return status


async def run_money(conn: Conn, kind: MoneyAction, req: Request, reason: str) -> dict[str, Any]:
    request_id = await insert_request(conn, req)
    row_id = await insert_compensation(conn, kind, request_id, req, "succeeded", reason)
    if kind == "request_refund":
        await sync_refund_status(conn, req.order_id, req.customer_id)
        return {"reference": request_id, "refund_id": row_id}
    return {"reference": request_id, "store_credit_id": row_id}


async def run_cancel(conn: Conn, req: Request, refund_cents: int, reason: str) -> dict[str, Any]:
    """Cancel, and for a paid order refund exactly the captured total in the same transaction (H2)."""
    request_id = await insert_request(conn, req)
    await conn.execute(
        "UPDATE app.orders SET status = 'cancelled' WHERE id = $1 AND customer_id = $2",
        req.order_id,
        req.customer_id,
    )
    out: dict[str, Any] = {"reference": request_id}
    if refund_cents > 0:
        out["refund_id"] = await conn.fetchval(
            "INSERT INTO app.refunds (order_id, currency, amount_cents, status, source, action_request_id,"
            " reason, created_at) VALUES ($1, $2, $3, 'succeeded', 'action', $4, $5, $6) RETURNING id",
            req.order_id,
            req.currency,
            refund_cents,
            request_id,
            reason,
            req.now,
        )
    return out


async def run_address_change(conn: Conn, req: Request, new_address: dict[str, str]) -> dict[str, Any]:
    request_id = await insert_request(conn, req)
    await conn.execute(
        "UPDATE app.orders SET shipping_address = $3::jsonb WHERE id = $1 AND customer_id = $2",
        req.order_id,
        req.customer_id,
        json.dumps(new_address),
    )
    return {"reference": request_id}


async def run_ticket(
    conn: Conn, req: Request, kind: Literal["ticket", "escalation"], summary: str, category: str | None
) -> dict[str, Any]:
    request_id = await insert_request(conn, req)
    ticket_id = await conn.fetchval(
        "INSERT INTO app.tickets (customer_id, conversation_id, kind, category, summary, action_request_id,"
        " created_at) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id",
        req.customer_id,
        req.conversation_id,
        kind,
        category,
        summary,
        request_id,
        req.now,
    )
    return {"reference": request_id, "ticket_id": ticket_id}
