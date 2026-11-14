"""Write tools (spec 6.1). Each one only hands the model's raw arguments to the Action Gateway.

- No tool accepts a customer id (invariant 2): identity comes from the run context.
- The typed parameters below exist to advertise the schema to the model. The SDK's own argument model is lax
  (it drops unknown fields and coerces "3200", 12.0 and true; docs/sdk_surface.md), so the parsed values are
  NOT used: the gateway re-validates `ToolContext.tool_arguments` strictly (DECISIONS I3).
- Calls the SDK itself rejects reach `_rejected`, which sends them to the same gateway to be audited.
- `strict_mode=False`: the advertised schema must not require the optional `items` / `amount_cents`. In strict
  mode every property is required, and the provider rejected a model call that omitted `amount_cents` (eval
  run 20261107T213633Z, p05). The schema is advice to the model; enforcement is the gateway's strict model.
- Tools import nothing from actions/ except the gateway (probe st02); executors are out of reach (st01).
"""

import json
from typing import Any

from agents import FunctionTool, RunContextWrapper, function_tool
from agents.exceptions import ModelBehaviorError
from agents.tool_context import ToolContext
from pydantic import BaseModel, Field

from tollgate.actions import gateway
from tollgate.tools.context import TurnContext


# Advertised to the model only; the gateway validates the raw arguments with its own strict model.
class ShippingAddress(BaseModel):
    name: str | None = Field(None, description="Recipient name, only if it changes.")
    line1: str | None = Field(None, description="Street address, only if it changes.")
    city: str | None = Field(None, description="City, only if it changes.")
    postal_code: str | None = Field(None, description="Postal code, only if it changes.")
    country: str | None = Field(None, description="Two-letter country code, only if it changes.")


FAILED = "The action could not be completed because of an internal error. Nothing was confirmed."


def _call(ctx: RunContextWrapper[TurnContext]) -> tuple[TurnContext, str, str]:
    if not isinstance(ctx, ToolContext):
        raise TypeError("write tools must be invoked by the SDK runner with a ToolContext")
    return ctx.context, ctx.tool_name, ctx.tool_arguments


async def _rejected(ctx: RunContextWrapper[Any], error: Exception) -> str:
    """failure_error_function: SDK argument validation failures are audited and rejected by the gateway."""
    if isinstance(ctx, ToolContext) and isinstance(error, ModelBehaviorError):
        result = await gateway.submit(ctx.context, ctx.tool_name, ctx.tool_arguments, sdk_rejected=True)
        return json.dumps(result)
    return FAILED  # the gateway already audited the failure before raising


@function_tool(failure_error_function=_rejected, strict_mode=False)
async def request_refund(
    ctx: RunContextWrapper[TurnContext],
    order_id: str,
    reason: str,
    items: list[str] | None = None,
    amount_cents: int | None = None,
) -> dict[str, Any]:
    """Refund items from one of the signed-in customer's delivered orders.

    The amount is always recomputed from the order. Small refunds complete immediately, larger ones wait
    for staff approval, and some are not allowed; the result says which.

    Args:
        order_id: The order ID, like ORD-1042.
        reason: Why the customer wants the refund, in a few words.
        items: Names of the order's items to refund, exactly as the order lists them.
        amount_cents: Optional lower amount in minor units (e.g. a partial goodwill refund). Never raises it.
    """
    del order_id, reason, items, amount_cents  # the gateway validates the raw arguments strictly
    return await gateway.submit(*_call(ctx))


@function_tool(failure_error_function=_rejected, strict_mode=False)
async def issue_store_credit(
    ctx: RunContextWrapper[TurnContext],
    order_id: str,
    reason: str,
    items: list[str] | None = None,
    amount_cents: int | None = None,
) -> dict[str, Any]:
    """Issue store credit for items from one of the signed-in customer's delivered orders.

    Args:
        order_id: The order ID, like ORD-1042.
        reason: Why the customer is being given credit, in a few words.
        items: Names of the order's items the credit is for, exactly as the order lists them.
        amount_cents: Optional lower amount in minor units. Never raises it.
    """
    del order_id, reason, items, amount_cents
    return await gateway.submit(*_call(ctx))


@function_tool(failure_error_function=_rejected, strict_mode=False)
async def cancel_order(ctx: RunContextWrapper[TurnContext], order_id: str, reason: str) -> dict[str, Any]:
    """Cancel one of the signed-in customer's orders that has not been packed yet.

    A paid order is refunded its full captured amount as part of the cancellation.

    Args:
        order_id: The order ID, like ORD-1130.
        reason: Why the customer wants to cancel, in a few words.
    """
    del order_id, reason
    return await gateway.submit(*_call(ctx))


@function_tool(failure_error_function=_rejected, strict_mode=False)
async def update_shipping_address(
    ctx: RunContextWrapper[TurnContext], order_id: str, new_address: ShippingAddress
) -> dict[str, Any]:
    """Change the delivery address of one of the signed-in customer's orders that has not shipped.

    Args:
        order_id: The order ID, like ORD-1013.
        new_address: Only the parts of the address that change; everything left out stays as it is.
    """
    del order_id, new_address
    return await gateway.submit(*_call(ctx))


@function_tool(failure_error_function=_rejected, strict_mode=False)
async def create_ticket(ctx: RunContextWrapper[TurnContext], summary: str, category: str) -> dict[str, Any]:
    """Open a support ticket for the signed-in customer.

    Args:
        summary: What the customer needs, in their own terms.
        category: A short category such as delivery, product, account or other.
    """
    del summary, category
    return await gateway.submit(*_call(ctx))


@function_tool(failure_error_function=_rejected, strict_mode=False)
async def escalate_to_human(ctx: RunContextWrapper[TurnContext], summary: str) -> dict[str, Any]:
    """Hand the conversation to a human support agent.

    Args:
        summary: What the customer needs and what has been tried so far.
    """
    del summary
    return await gateway.submit(*_call(ctx))


WRITE_TOOLS: dict[str, FunctionTool] = {
    t.name: t
    for t in (
        request_refund,
        issue_store_credit,
        cancel_order,
        update_shipping_address,
        create_ticket,
        escalate_to_human,
    )
}
