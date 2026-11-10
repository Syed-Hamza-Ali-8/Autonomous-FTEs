"""No customer-facing string the code controls reveals a group-C value (DECISIONS I15, three tiers).

A. Order-state facts (already shipped, already refunded): allowed. B. Published store terms (30-day return
window, final sale, digital after download): allowed. C. Internal control parameters (auto-approval limits,
approval maximums, rolling-window caps and counts, reason codes, rule names): never customer-facing.

Covers: every ActionCard text and every outcome hint (for every reason code and every order status), the
claim-check corrections, chat error messages, the gateway's constant results, and every string literal in the
frontend chat components. Model replies are controlled at their input instead (test_model_input_is_tier_safe
in test_adversarial_tools.py) and monitored in eval runs.
"""

import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from eval.verify_scenarios import load
from tollgate.actions import cards, gateway, hints
from tollgate.agents_def.events import FRIENDLY
from tollgate.guardrails import claims
from tollgate.policy.disclosure import find

FRONTEND_CHAT = Path(__file__).resolve().parents[2] / "frontend" / "src" / "components" / "chat"
STATUSES = (
    "pending",
    "paid",
    "packed",
    "shipped",
    "delivered",
    "cancelled",
    "refunded",
    "partially_refunded",
)


def customer_strings() -> list[str]:
    at = datetime(2026, 11, 7, 12, tzinfo=UTC)
    texts = [*cards.DONE.values(), cards.WAITING, hints.PENDING, hints.NOT_FOUND, hints.REJECTED, hints.TEAM]
    texts += [hints.hint(code, status) for code in hints.REASON_CODES for status in STATUSES]
    paid_cancel = {
        "reference": "ACT-000001",
        "order_id": "ORD-1159",
        "refund": {"amount_cents": 21300, "currency": "USD"},
    }
    card = cards.card_for("cancel_order", "executed", paid_cancel, "ORD-1159", at)
    assert card is not None
    texts.append(card.explanation)
    texts += [claims.CORRECTION, claims.CORRECTION_WITH_ACTIONS, *FRIENDLY.values()]
    # Only the relayable sentence; `status` is a machine token the model reads, not customer text.
    texts += [gateway.NOT_FOUND["customer_message_hint"], gateway.REJECTED["customer_message_hint"]]
    for path in sorted(FRONTEND_CHAT.glob("*.ts*")):
        if ".test." not in path.name:
            for a, b in re.findall(r'"([^"\n]{3,})"|`([^`\n]{3,})`', path.read_text()):
                texts.append(a or b)
    return texts


@pytest.mark.parametrize("text", customer_strings())
def test_no_customer_facing_string_reveals_an_internal_control(text: str) -> None:
    assert find(text) == [], f"group-C value in customer-facing text: {text!r}"


def test_state_facts_and_published_terms_are_still_said() -> None:
    """Tiers A and B are allowed and encouraged: the restored state-based wording is present."""
    assert hints.hint("status_not_cancellable", "shipped") == (
        "This order has already shipped, so it can no longer be cancelled."
    )
    assert hints.hint("status_not_refundable", "refunded") == "This order has already been refunded in full."
    assert "30-day return window" in hints.hint("outside_return_window")
    assert "Final-sale" in hints.hint("final_sale")
    allowed = (
        "This order is past the 30-day return window.",
        "Final-sale items can't be returned.",
        "Digital items can't be refunded once downloaded.",
        "This order has already shipped.",
    )
    for text in allowed:
        assert find(text) == [], text  # never flagged


def test_internal_controls_get_no_detail() -> None:
    for code in ("auto_max", "window_count", "window_cap", "above_approval_max"):
        text = hints.hint(code, "delivered")
        assert text.startswith("This can't be completed through chat."), text


def test_pre_registered_reply_facts_are_published_terms_or_state_facts() -> None:
    """r09 ("30 days") and r10 ("final sale") stay as pre-registered: no required fact is group C."""
    for s in load():
        required = s["reply"]["must_include"] + [x for group in s["reply"]["must_include_any"] for x in group]
        for fact in required:
            assert find(fact, ("term",)) == [], (s["id"], fact)


@pytest.mark.parametrize(
    "leak",
    [
        "Refunds over $50.00 need a staff check.",  # auto-approval limit
        "Anything above Rs 150,000 can't be refunded here.",  # approval maximum
        "This would be your 3rd refund in 90 days.",  # rolling-window count and length
        "You've reached the $100.00 limit for this period.",  # rolling-window cap
        "Denied: window_cap",  # reason code
        "per max_refunds_in_window_before_approval",  # rule name
    ],
)
def test_the_check_is_live(leak: str) -> None:
    """Mutation check: each kind of group-C value is caught."""
    assert find(leak) != [], leak


def test_a_different_amount_sharing_a_limits_prefix_is_not_a_match() -> None:
    assert find("Rs 15,000.01", ("limit_amount",)) == []
    assert find("$50.01", ("limit_amount",)) == []
    assert find("Rs 15,000", ("limit_amount",)) != []


def test_b3_refund_refusals_point_to_cancel_or_escalation() -> None:
    """B3: a not-yet-shipped order is cancelled instead; a packed or shipped one gets an escalation hint."""
    assert "cancelled instead of refunded" in hints.hint("status_not_refundable", "paid")
    for status in ("packed", "shipped"):
        assert hints.TEAM in hints.hint("status_not_refundable", status)
