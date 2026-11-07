"""Read tools (spec Section 6.1). Thin wrappers over domain/; none accepts a customer id (invariant 2).

The customer comes from the run context, populated from the authenticated request. A malformed,
missing or other customer's order ID all produce the same NOT_FOUND result (invariant 8).
Every call is recorded in app.tool_calls.
"""

import json
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from agents import FunctionTool, RunContextWrapper, function_tool

from tollgate.domain import orders
from tollgate.domain.models import OrderDetail, OrderSummary
from tollgate.domain.money import with_display
from tollgate.tools.context import TurnContext

ORDER_ID = re.compile(r"^ORD-[0-9]{4}$")
NOT_FOUND: dict[str, Any] = {
    "found": False,
    "message": "No order with that ID was found on this customer's account.",
}
StatusFilter = Literal[
    "pending", "paid", "packed", "shipped", "delivered", "cancelled", "refunded", "partially_refunded"
]


def _normalise(order_id: str) -> str | None:
    candidate = order_id.strip().upper()
    return candidate if ORDER_ID.fullmatch(candidate) else None


async def _logged(
    ctx: TurnContext, tool: str, args: dict[str, Any], run: Callable[[], Awaitable[dict[str, Any]]]
) -> dict[str, Any]:
    started = time.perf_counter()
    outcome: str = "error"
    result: dict[str, Any] | None = None
    try:
        enriched: dict[str, Any] = with_display(await run())
        result = enriched
        outcome = "not_found" if enriched.get("found") is False else "ok"
        return enriched
    finally:
        ctx.tool_calls += 1
        await ctx.pool.execute(
            "INSERT INTO app.tool_calls (turn_id, tool_name, arguments, outcome, result, latency_ms)"
            " VALUES ($1, $2, $3::jsonb, $4, $5::jsonb, $6)",
            ctx.turn_id,
            tool,
            json.dumps(args),
            outcome,
            json.dumps(result, default=str) if result is not None else None,
            round((time.perf_counter() - started) * 1000),
        )


def _remember(ctx: TurnContext, detail: OrderDetail) -> None:
    ctx.referenced_orders[detail.id] = OrderSummary(
        id=detail.id,
        status=detail.status,
        total=detail.total,
        placed_at=detail.placed_at,
        delivered_at=detail.delivered_at,
        item_count=len(detail.items),
        first_item_name=detail.items[0].name if detail.items else "",
    )


@function_tool
async def get_my_orders(
    ctx: RunContextWrapper[TurnContext], status: StatusFilter | None = None
) -> dict[str, Any]:
    """List the signed-in customer's orders, newest first.

    Args:
        status: Only return orders with this status. Omit to list all orders.
    """
    turn = ctx.context

    async def run() -> dict[str, Any]:
        async with turn.pool.acquire() as conn:
            found = await orders.list_orders(conn, turn.customer.customer_id, status)
        return {"found": True, "orders": [o.model_dump(mode="json") for o in found]}

    return await _logged(turn, "get_my_orders", {"status": status}, run)


@function_tool
async def get_order(ctx: RunContextWrapper[TurnContext], order_id: str) -> dict[str, Any]:
    """Get one of the signed-in customer's orders: status, items, totals, refunds and shipment.

    Args:
        order_id: The order ID, for example ORD-1042.
    """
    turn = ctx.context

    async def run() -> dict[str, Any]:
        oid = _normalise(order_id)
        if oid is None:
            return NOT_FOUND
        async with turn.pool.acquire() as conn:
            detail = await orders.get_order(conn, turn.customer.customer_id, oid)
        if detail is None:
            return NOT_FOUND
        _remember(turn, detail)
        return {"found": True, "order": detail.model_dump(mode="json")}

    return await _logged(turn, "get_order", {"order_id": order_id}, run)


@function_tool
async def get_shipment(ctx: RunContextWrapper[TurnContext], order_id: str) -> dict[str, Any]:
    """Get carrier, tracking number and delivery events for one of the customer's orders.

    Args:
        order_id: The order ID, for example ORD-1042.
    """
    turn = ctx.context

    async def run() -> dict[str, Any]:
        oid = _normalise(order_id)
        if oid is None:
            return NOT_FOUND
        async with turn.pool.acquire() as conn:
            detail = await orders.get_order(conn, turn.customer.customer_id, oid)
            if detail is None:
                return NOT_FOUND
            shipment = detail.shipment
        _remember(turn, detail)
        if shipment is None:
            return {
                "found": True,
                "order_id": oid,
                "order_status": detail.status,
                "shipment": None,
                "message": "This order has not been handed to a carrier yet.",
            }
        return {
            "found": True,
            "order_id": oid,
            "order_status": detail.status,
            "shipment": shipment.model_dump(mode="json"),
        }

    return await _logged(turn, "get_shipment", {"order_id": order_id}, run)


@function_tool
async def get_refund_history(ctx: RunContextWrapper[TurnContext], order_id: str) -> dict[str, Any]:
    """List refunds recorded for one of the customer's orders.

    Args:
        order_id: The order ID, for example ORD-1042.
    """
    turn = ctx.context

    async def run() -> dict[str, Any]:
        oid = _normalise(order_id)
        if oid is None:
            return NOT_FOUND
        async with turn.pool.acquire() as conn:
            detail = await orders.get_order(conn, turn.customer.customer_id, oid)
        if detail is None:
            return NOT_FOUND
        _remember(turn, detail)
        return {
            "found": True,
            "order_id": oid,
            "captured": detail.captured.model_dump(),
            "refunded": detail.refunded.model_dump(),
            "refunds": [r.model_dump(mode="json") for r in detail.refunds],
        }

    return await _logged(turn, "get_refund_history", {"order_id": order_id}, run)


READ_TOOLS: dict[str, FunctionTool] = {
    t.name: t for t in (get_my_orders, get_order, get_shipment, get_refund_history)
}
