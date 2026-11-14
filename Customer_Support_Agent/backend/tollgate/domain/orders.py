"""Order reads. Every query is filtered by the authenticated customer IN SQL (invariant 3).

`customer_id` always comes from CustomerContext, never from a request body or the model (invariant 2).
A missing order and another customer's order both return None, so callers cannot tell them apart
(invariant 8). Order notes are deliberately not returned: they are free text that may carry
injection payloads, and nothing in the customer flows needs them.
"""

import json
from datetime import datetime
from typing import Any

from tollgate.approvals import expiry
from tollgate.db import Conn
from tollgate.domain.models import (
    Address,
    Money,
    OrderDetail,
    OrderItem,
    OrderStatus,
    OrderSummary,
    Refund,
    Shipment,
    ShipmentEvent,
)


async def list_orders(conn: Conn, customer_id: str, status: OrderStatus | None = None) -> list[OrderSummary]:
    rows = await conn.fetch(
        """
        SELECT o.id, o.status, o.currency, o.total_cents, o.placed_at, o.delivered_at,
               (SELECT count(*) FROM app.order_items i WHERE i.order_id = o.id) AS item_count,
               (SELECT p.name FROM app.order_items i JOIN app.products p ON p.id = i.product_id
                 WHERE i.order_id = o.id ORDER BY i.id LIMIT 1) AS first_item_name
          FROM app.orders o
         WHERE o.customer_id = $1 AND ($2::text IS NULL OR o.status = $2)
         ORDER BY o.placed_at DESC, o.id DESC
        """,
        customer_id,
        status,
    )
    return [
        OrderSummary(
            id=r["id"],
            status=r["status"],
            total=Money(amount_cents=r["total_cents"], currency=r["currency"]),
            placed_at=r["placed_at"],
            delivered_at=r["delivered_at"],
            item_count=r["item_count"],
            first_item_name=r["first_item_name"],
        )
        for r in rows
    ]


async def get_order(conn: Conn, customer_id: str, order_id: str, now: datetime) -> OrderDetail | None:
    order = await conn.fetchrow(
        """
        SELECT id, status, currency, total_cents, placed_at, paid_at, packed_at, delivered_at,
               shipping_address
          FROM app.orders
         WHERE id = $1 AND customer_id = $2
        """,
        order_id,
        customer_id,
    )
    if order is None:
        return None
    ccy = order["currency"]
    # Every child query re-applies the ownership filter through the order join.
    items = await conn.fetch(
        """
        SELECT i.product_id, p.name, p.category, i.quantity, i.unit_price_cents, p.final_sale, p.digital
          FROM app.order_items i
          JOIN app.orders o ON o.id = i.order_id
          JOIN app.products p ON p.id = i.product_id
         WHERE i.order_id = $1 AND o.customer_id = $2
         ORDER BY i.id
        """,
        order_id,
        customer_id,
    )
    totals = await conn.fetchrow(
        """
        SELECT (SELECT coalesce(sum(p.amount_cents), 0) FROM app.payments p
                 WHERE p.order_id = o.id) AS captured,
               (SELECT coalesce(sum(r.amount_cents), 0) FROM app.refunds r
                 WHERE r.order_id = o.id AND r.status = 'succeeded') AS refunded
          FROM app.orders o
         WHERE o.id = $1 AND o.customer_id = $2
        """,
        order_id,
        customer_id,
    )
    refunds = await _refunds(conn, customer_id, order_id, now)
    shipment = await get_shipment(conn, customer_id, order_id)
    return OrderDetail(
        id=order["id"],
        status=order["status"],
        total=Money(amount_cents=order["total_cents"], currency=ccy),
        placed_at=order["placed_at"],
        paid_at=order["paid_at"],
        packed_at=order["packed_at"],
        delivered_at=order["delivered_at"],
        shipping_address=Address.model_validate(_json(order["shipping_address"])),
        items=[
            OrderItem(
                product_id=i["product_id"],
                name=i["name"],
                category=i["category"],
                quantity=i["quantity"],
                unit_price=Money(amount_cents=i["unit_price_cents"], currency=ccy),
                line_total=Money(amount_cents=i["unit_price_cents"] * i["quantity"], currency=ccy),
                final_sale=i["final_sale"],
                digital=i["digital"],
            )
            for i in items
        ],
        captured=Money(amount_cents=totals["captured"] if totals else 0, currency=ccy),
        refunded=Money(amount_cents=totals["refunded"] if totals else 0, currency=ccy),
        refunds=refunds,
        shipment=shipment,
    )


async def get_shipment(conn: Conn, customer_id: str, order_id: str) -> Shipment | None:
    row = await conn.fetchrow(
        """
        SELECT s.carrier, s.tracking_number, s.status, s.shipped_at, s.delivered_at, s.events
          FROM app.shipments s
          JOIN app.orders o ON o.id = s.order_id
         WHERE s.order_id = $1 AND o.customer_id = $2
        """,
        order_id,
        customer_id,
    )
    if row is None:
        return None
    events = [ShipmentEvent(at=e["at"], description=e["description"]) for e in _json(row["events"])]
    return Shipment(
        carrier=row["carrier"],
        tracking_number=row["tracking_number"],
        status=row["status"],
        shipped_at=row["shipped_at"],
        delivered_at=row["delivered_at"],
        events=events,
    )


async def get_refund_history(
    conn: Conn, customer_id: str, order_id: str, now: datetime
) -> list[Refund] | None:
    """None when the order is not this customer's (or doesn't exist); [] when it has no refunds."""
    owned = await conn.fetchval(
        "SELECT 1 FROM app.orders WHERE id = $1 AND customer_id = $2", order_id, customer_id
    )
    if owned is None:
        return None
    return await _refunds(conn, customer_id, order_id, now)


DECIDED_AS = {"failed_recheck": "not_completed", "expired": "expired"}


def _refund_status(status: str, created_at: datetime, now: datetime) -> str:
    """R2 of the derived expiry predicate (J8): a refund still pending past approval expiry reads as expired.
    Its own seam for mutation M40. (Executed and historical refunds are never pending.)"""
    return "expired" if status == "pending_approval" and expiry.is_expired(created_at, now) else status


async def _refunds(conn: Conn, customer_id: str, order_id: str, now: datetime) -> list[Refund]:
    rows = await conn.fetch(
        """
        SELECT r.id, r.amount_cents, r.currency, r.status, r.reason, r.created_at, p.decision
          FROM app.refunds r
          JOIN app.orders o ON o.id = r.order_id
          LEFT JOIN app.approvals p ON p.action_request_id = r.action_request_id
         WHERE r.order_id = $1 AND o.customer_id = $2
         ORDER BY r.created_at, r.id
        """,
        order_id,
        customer_id,
    )
    return [
        Refund(
            id=r["id"],
            amount=Money(amount_cents=r["amount_cents"], currency=r["currency"]),
            # Stored as rejected, but neither is a rejection: a failed re-check (J10), and an expiry whose
            # lazy write has happened (it must read the same as before the write, J8).
            status=DECIDED_AS.get(r["decision"]) or _refund_status(r["status"], r["created_at"], now),
            reason=r["reason"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


def _json(value: Any) -> Any:
    return json.loads(value) if isinstance(value, str) else value
