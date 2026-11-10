"""What the customer, and the model, may be told about an outcome (DECISIONS I15, three tiers).

A. Order-state facts (already shipped, already refunded, already cancelled): said plainly.
B. Published store terms (the return window, final sale, digital goods once downloaded): said plainly.
C. Internal control parameters (auto-approval limits, approval maximums, rolling-window caps and counts,
   reason codes, rule names): never said. The customer hears what happened and what to do next.

This text is the ONLY outcome detail the Action Gateway passes to the model (`customer_message_hint`), and
ActionCards use the same text, so neither can reveal a group-C value: the model can't leak what it was never
given. Reason codes stay in the audit log and the staff console.
"""

from tollgate.policy import engine

TEAM = "Our support team can take a look if you'd like; I can pass it on."

# Every reason code the gateway can produce (pre-registration section 3, amendments A1-A2).
REASON_CODES = (
    "invalid_amount", "items_required", "summary_too_long", "address_required", "address_incomplete",
    "not_found", "item_not_in_order", "status_not_refundable", "status_not_cancellable",
    "status_not_addressable", "outside_return_window", "final_sale", "digital_downloaded",
    "line_already_compensated", "exceeds_refundable_remainder", "above_approval_max", "auto_max",
    "window_count", "window_cap",
)  # fmt: skip

NOT_FOUND = "No order with that number was found on this customer's account."
PENDING = "This needs a quick review by our support team before it goes through. Nothing has changed yet."
REJECTED = "The request didn't match the tool, so nothing was done."

# Order-state facts, by the order's current status (tier A).
_NOT_REFUNDABLE = {
    "refunded": "This order has already been refunded in full.",
    "cancelled": "This order was cancelled.",
    # B3: not shipped yet, so cancelling is the way to get the money back
    "pending": "This order hasn't shipped yet, so it can be cancelled instead of refunded.",
    "paid": "This order hasn't shipped yet, so it can be cancelled instead of refunded.",
}
# B3: packed or shipped, not delivered: refused, with an escalation hint
_NOT_YET_DELIVERED = f"This order hasn't been delivered yet, so it can't be refunded yet. {TEAM}"
_NOT_CANCELLABLE = {
    "cancelled": "This order is already cancelled.",
    "packed": "This order has already been packed, so it can no longer be cancelled.",
    "shipped": "This order has already shipped, so it can no longer be cancelled.",
    "delivered": "This order has already been delivered, so it can no longer be cancelled.",
    "refunded": "This order has already been refunded.",
    "partially_refunded": "This order has already been delivered, so it can no longer be cancelled.",
}
_NOT_ADDRESSABLE = {
    "shipped": "This order has already shipped, so its delivery address can no longer be changed.",
    "delivered": "This order has already been delivered.",
    "cancelled": "This order is cancelled.",
}


def hint(reason: str, order_status: str | None = None) -> str:
    """The customer-safe sentence for an outcome's first reason. Tier C reasons get no detail at all."""
    status = order_status or ""
    match reason:
        case "not_found":
            return NOT_FOUND
        # A: order-state facts
        case "status_not_refundable":
            return _NOT_REFUNDABLE.get(status, _NOT_YET_DELIVERED)
        case "status_not_cancellable":
            return _NOT_CANCELLABLE.get(status, "This order can no longer be cancelled.")
        case "status_not_addressable":
            return _NOT_ADDRESSABLE.get(status, "This order's delivery address can no longer be changed.")
        case "line_already_compensated":
            return "That item already has a refund or store credit."
        case "exceeds_refundable_remainder":
            return "That's more than is left to refund on this order."
        case "item_not_in_order":
            return "That item isn't part of this order."
        # B: published store terms
        case "outside_return_window":
            days = engine.load_rules().return_window_days
            return f"This order is past the {days}-day return window."
        case "final_sale":
            return "Final-sale items can't be returned or refunded."
        case "digital_downloaded":
            return "Digital items can't be refunded once they've been downloaded."
        # Request problems the model can fix (no policy content)
        case "invalid_amount":
            return "The amount isn't valid."
        case "items_required":
            return "Say which items of the order this is for."
        case "summary_too_long":
            return "The summary is too long; shorten it."
        case "address_required":
            return "Say which part of the delivery address should change."
        case "address_incomplete":
            return "The new delivery address would be incomplete."
        # C: internal control parameters: what happened and what next, nothing about why
        case _:
            return f"This can't be completed through chat. {TEAM}"
