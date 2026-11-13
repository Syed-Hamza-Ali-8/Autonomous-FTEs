"""Executors: the only code that moves money or changes an order (invariant 6).

Importable only by actions/gateway.py and approvals/service.py (tests/test_action_boundary.py, probe st01).
Every function runs inside the gateway's transaction, after ownership, recompute, idempotency and policy;
none re-decides anything. Amounts arrive recomputed from the database, never from the model (invariant 4),
and the refund trigger still caps succeeded refunds at the captured total (invariant 9).
"""

import json
from datetime import datetime
from typing import Any, Literal

from tollgate.actions.records import MoneyAction, Request, insert_compensation, insert_request
from tollgate.db import Conn
from tollgate.errors import ActionFailedError


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


# Literal SQL per table (no interpolated identifiers), so structural scans see every write.
COMPLETE_SQL: dict[MoneyAction, str] = {
    "request_refund": "UPDATE app.refunds SET status = 'succeeded' WHERE action_request_id = $1"
    " AND order_id = $2 AND status = 'pending_approval' RETURNING id",
    "issue_store_credit": "UPDATE app.store_credits SET status = 'succeeded' WHERE action_request_id = $1"
    " AND order_id = $2 AND status = 'pending_approval' RETURNING id",
}


async def complete_money(
    conn: Conn, kind: MoneyAction, request_id: str, order_id: str, customer_id: str
) -> str:
    """Pay out an APPROVED request's pending refund or credit (B6). Called only by approvals/service.py, after
    it recorded the decision: the database refuses this move unless the request is approved
    (`refunds_follow_their_request`, `store_credits_follow_their_request`; amendment A2-P4)."""
    row_id: str | None = await conn.fetchval(COMPLETE_SQL[kind], request_id, order_id)
    if row_id is None:
        raise ActionFailedError(f"{request_id}: no pending {kind} row to complete")
    if kind == "request_refund":
        await sync_refund_status(conn, order_id, customer_id)
    return row_id


async def run_cancel(conn: Conn, req: Request, refund_cents: int, reason: str) -> dict[str, Any]:
    """Cancel, and for a paid order refund exactly the captured total in the same transaction (H2)."""
    request_id = await insert_request(conn, req)
    out: dict[str, Any] = {"reference": request_id}
    refund_id = await cancel(
        conn, request_id, req.order_id, req.customer_id, req.currency, refund_cents, reason, req.now
    )
    if refund_id is not None:
        out["refund_id"] = refund_id
    return out


async def cancel(
    conn: Conn,
    request_id: str,
    order_id: str | None,
    customer_id: str,
    currency: str | None,
    refund_cents: int,
    reason: str,
    now: datetime,
) -> str | None:
    """The cancellation effect, shared by the gateway (ALLOW) and the approval path (J9): the status, and for
    a paid order its H2 refund. Returns the refund id, if any."""
    await conn.execute(
        "UPDATE app.orders SET status = 'cancelled' WHERE id = $1 AND customer_id = $2", order_id, customer_id
    )
    if refund_cents <= 0:
        return None
    refund_id: str = await conn.fetchval(
        "INSERT INTO app.refunds (order_id, currency, amount_cents, status, source, action_request_id,"
        " reason, created_at) VALUES ($1, $2, $3, 'succeeded', 'action', $4, $5, $6) RETURNING id",
        order_id,
        currency,
        refund_cents,
        request_id,
        reason,
        now,
    )
    return refund_id


async def run_address_change(conn: Conn, req: Request, new_address: dict[str, str]) -> dict[str, Any]:
    request_id = await insert_request(conn, req)
    await change_address(conn, req.order_id, req.customer_id, new_address)
    return {"reference": request_id}


async def change_address(
    conn: Conn, order_id: str | None, customer_id: str, new_address: dict[str, str]
) -> None:
    """The address effect, shared by the gateway (ALLOW) and the approval path (J9)."""
    await conn.execute(
        "UPDATE app.orders SET shipping_address = $3::jsonb WHERE id = $1 AND customer_id = $2",
        order_id,
        customer_id,
        json.dumps(new_address),
    )


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
