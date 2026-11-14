"""Turn an Action Gateway result into the customer's ActionCard (spec 13.3; DECISIONS C1).

Cards are built from the gateway's own outcome, so what the chat shows is what the action log says, whatever
the model writes. Only policy outcomes get a card: executed, queued, denied and not found. A schema rejection,
an invalid request or an internal error is the model's or the system's problem, not a decision about the
customer's request, and a replay repeats a card already shown this turn.
"""

from datetime import datetime
from typing import Any, get_args

from tollgate.actions import hints
from tollgate.domain.models import ActionCard, ActionKind, ActionState, Money
from tollgate.domain.money import format_money

DONE: dict[str, str] = {
    "request_refund": "The refund is done. It goes back to your original payment method.",
    "issue_store_credit": "The store credit is on your account.",
    "cancel_order": "The order is cancelled.",
    "update_shipping_address": "The delivery address is updated.",
    "create_ticket": "A support ticket is open. Our team will reply by email.",
    "escalate_to_human": "A member of our support team will pick this up.",
}
# Any queued action (refunds and credits, and from fraud routing also cancellations and address changes).
WAITING = (
    "This needs a quick check by our support team before it goes through. Nothing has changed yet; the"
    " outcome will show here."
)


def done_text(action: ActionKind, money: Money | None) -> str:
    if action == "cancel_order" and money is not None:
        paid = format_money(money.amount_cents, money.currency)
        return f"The order is cancelled and its payment of {paid} is refunded."
    return DONE[action]


# The explanation for each state of an action record (DECISIONS C2, J8), read live by a card.
def record_text(state: ActionState, action: ActionKind, money: Money | None) -> str:
    match state:
        case "completed":
            return done_text(action, money)
        case "waiting_for_approval":
            return WAITING
        case "not_allowed":
            return hints.NOT_APPROVED
        case "not_completed":
            return hints.NOT_COMPLETED
        case "closed":
            return hints.CLOSED


def decided_message(decision: str, reference: str, action: str) -> str:
    """The system message for a staff decision or an expiry (spec 4.5 "notify"); tier-safe (I15)."""
    text = hints.DECIDED[decision].format(reference=reference)
    if decision == "approved" and action in get_args(ActionKind):
        text = f"{text} {DONE[action]}"
    return text


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
        money = _money(result)
        return ActionCard(
            action=kind, state="completed", order_id=result.get("order_id"), amount=money,
            reference=result.get("reference"), explanation=done_text(kind, money), at=at,
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
