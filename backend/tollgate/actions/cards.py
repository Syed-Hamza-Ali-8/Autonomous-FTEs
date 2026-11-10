"""Turn an Action Gateway result into the customer's ActionCard (spec 13.3; DECISIONS C1).

Cards are built from the gateway's own outcome, so what the chat shows is what the action log says, whatever
the model writes. Only policy outcomes get a card: executed, queued, denied and not found. A schema rejection,
an invalid request or an internal error is the model's or the system's problem, not a decision about the
customer's request, and a replay repeats a card already shown this turn.
"""

from datetime import datetime
from typing import Any, get_args

from tollgate.actions import hints
from tollgate.domain.models import ActionCard, ActionKind, Money
from tollgate.domain.money import format_money

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


def _money(result: dict[str, Any]) -> Money | None:
    if isinstance(result.get("amount_cents"), int):
        return Money(amount_cents=result["amount_cents"], currency=result["currency"])
    refund = result.get("refund")
    if isinstance(refund, dict):
        return Money(amount_cents=refund["amount_cents"], currency=refund["currency"])
    return None


def card_for(
    action: str,
    outcome: str,
    result: dict[str, Any],
    target: str | None,
    at: datetime,
    audit_ref: str | None = None,
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
        # The same tier-safe sentence the model was given (hints.py; DECISIONS I15), plus the audit reference.
        return ActionCard(
            action=kind,
            state="not_allowed",
            order_id=None if outcome == "not_found" else target,
            reference=audit_ref,
            explanation=result.get("customer_message_hint") or hints.hint("not_found"),
            at=at,
        )
    return None
