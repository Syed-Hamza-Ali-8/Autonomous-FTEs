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
from typing import get_args

import pytest

from eval.verify_scenarios import load
from tollgate.actions import cards, gateway, hints
from tollgate.agents_def.events import FRIENDLY
from tollgate.domain.models import ActionState
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
    # Phase 4 (4.7): the system messages staff decisions post into the conversation, as approvals/service.py
    # composes them (an approval adds the action's completed text).
    texts += [cards.decided_message(d, "ACT-000001", a) for d in hints.DECIDED for a in cards.DONE]
    # what a polled card says in each state (C2, J8)
    texts += [cards.record_text(state, a, None) for state in get_args(ActionState) for a in cards.DONE]
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


def test_expiry_wording_offers_a_next_step_and_never_states_the_limit() -> None:
    """J8: not reviewed in time, ask again or be passed to a person; the 48-hour figure is tier C."""
    for text in (hints.CLOSED, cards.decided_message("expired", "ACT-000001", "request_refund")):
        assert "wasn't reviewed in time" in text and "ask again" in text and "support team" in text
        assert not re.search(r"\b48\b|hour|two days|2 days", text), text


def test_a_failed_recheck_never_reads_as_a_rejection() -> None:
    """J10: nobody decided against a request that went stale. The two outcomes differ in the system message
    and on the card, and neither text names a rule, a threshold or a reason code."""
    message = {
        d: cards.decided_message(d, "ACT-000001", "request_refund") for d in ("rejected", "failed_recheck")
    }
    card = {
        "rejected": cards.record_text("not_allowed", "request_refund", None),
        "failed_recheck": cards.record_text("not_completed", "request_refund", None),
    }
    assert message["rejected"] != message["failed_recheck"]
    assert card["rejected"] != card["failed_recheck"]
    codes = (*hints.REASON_CODES, *hints.RECHECK_CODES)
    for text in (*message.values(), *card.values()):
        assert find(text) == [], text
        assert not any(code in text for code in codes), text
        assert not re.search(r"\d", text.replace("ACT-000001", "")), text  # no figure of any kind
    for stale in (message["failed_recheck"], card["failed_recheck"]):
        assert "changed after you asked" in stale and "ask again" in stale and "support team" in stale
        assert not re.search(r"approv|reject|review|declin|den(y|ied)", stale, re.IGNORECASE), stale


@pytest.mark.parametrize("code", hints.RECHECK_CODES)
def test_recheck_only_reason_codes_are_group_c(code: str) -> None:
    """Liveness: the re-check codes are caught like every other reason code."""
    assert find(f"We couldn't complete it: {code}") != []
