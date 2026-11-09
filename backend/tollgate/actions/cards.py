"""Turn an Action Gateway result into the customer's ActionCard (spec 13.3; DECISIONS C1).

Cards are built from the gateway's own outcome, so what the chat shows is what the action log says, whatever
the model writes. Only policy outcomes get a card: executed, queued, denied and not found. A schema rejection,
an invalid request or an internal error is the model's or the system's problem, not a decision about the
customer's request, and a replay repeats a card already shown this turn.
"""

from datetime import datetime
from typing import Any, get_args

from tollgate.domain.models import ActionCard, ActionKind, Money
from tollgate.domain.money import format_money
from tollgate.policy import engine

DONE: dict[str, str] = {
    "request_refund": "The refund is done. It goes back to your original payment method.",
    "issue_store_credit": "The store credit is on your account.",
    "cancel_order": "The order is cancelled.",
    "update_shipping_address": "The delivery address is updated.",
    "create_ticket": "A support ticket is open. Our team will reply by email.",
    "escalate_to_human": "A member of our support team will pick this up.",
}
WAITING = (
    "This needs a quick check by our support team before it goes through. Nothing has been refunded or"
    " credited yet; the outcome will show here."
)


def not_allowed_text(reason: str) -> str:
    days = engine.load_rules().return_window_days
    return {
        "not_found": "No order with that number was found on your account.",
        "item_not_in_order": "That item isn't part of this order.",
        "status_not_refundable": "This order can't be refunded in its current state.",
        "status_not_cancellable": "This order can no longer be cancelled.",
        "status_not_addressable": "The delivery address can't be changed once an order has shipped.",
        "outside_return_window": f"This order is past the {days}-day return window.",
        "final_sale": "Final-sale items can't be refunded.",
        "digital_downloaded": "Digital items that have been downloaded can't be refunded.",
        "line_already_compensated": "This item already has a refund or store credit.",
        "exceeds_refundable_remainder": "That's more than what's left to refund on this order.",
        "above_approval_max": (
            "This is more than can be refunded through chat. Our support team can review it."
        ),
    }.get(reason, "This request can't be completed through chat.")


def _money(result: dict[str, Any]) -> Money | None:
    if isinstance(result.get("amount_cents"), int):
        return Money(amount_cents=result["amount_cents"], currency=result["currency"])
    refund = result.get("refund")
    if isinstance(refund, dict):
        return Money(amount_cents=refund["amount_cents"], currency=refund["currency"])
    return None


def card_for(
    action: str, outcome: str, result: dict[str, Any], target: str | None, at: datetime
) -> ActionCard | None:
    if action not in get_args(ActionKind):
        return None
    kind: ActionKind = action  # type: ignore[assignment]
    if outcome == "executed":
        text = DONE[kind]
        money = _money(result)
        if kind == "cancel_order" and money is not None:
            paid = format_money(money.amount_cents, money.currency)
            text = f"The order is cancelled and its payment of {paid} is refunded."
        return ActionCard(
            action=kind, state="completed", order_id=result.get("order_id"), amount=money,
            reference=result.get("reference"), explanation=text, at=at,
        )  # fmt: skip
    if outcome == "queued":
        return ActionCard(
            action=kind, state="waiting_for_approval", order_id=result.get("order_id"), amount=_money(result),
            reference=result.get("reference"), explanation=WAITING, at=at,
        )  # fmt: skip
    if outcome in ("denied", "not_found"):
        reason = (result.get("reasons") or ["not_found"])[0]
        order_id = None if outcome == "not_found" else target
        return ActionCard(
            action=kind, state="not_allowed", order_id=order_id, explanation=not_allowed_text(reason), at=at
        )
    return None
