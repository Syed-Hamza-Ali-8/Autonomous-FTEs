"""Claim check v0 (Phase 1). Phase 6 replaces this with the pre-registered suite and its mutation check.

In Phase 1 no action can succeed, so any claim of a completed action must be replaced.
Statements about past, recorded facts (e.g. a refund last month) must pass unchanged.
"""

from datetime import UTC, datetime

import pytest

from tollgate.domain.models import ActionCard
from tollgate.guardrails.claims import CORRECTION, CORRECTION_WITH_ACTIONS, check_reply

FALSE_CLAIMS = [
    "I've refunded your order.",
    "I have cancelled ORD-1042 for you.",
    "Done! I just processed the refund.",
    "We have issued a store credit to your account.",
    "I've updated your delivery address.",
    "Your refund has been processed.",
    "Your order has been cancelled successfully.",
    "Your address has been updated.",
    "I'll refund that for you now.",
    "I went ahead and... I've gone ahead and cancelled it.",
    "The order has been refunded for you.",
    # typographic punctuation, as real models produce it (found in the Phase 1 live smoke)
    "I\u2019ve refunded your order.",
    "Done \u2014 I\u2019ve cancelled ORD\u20111042 for you.",
    "Your\u00a0refund has been processed.",
]

TRUE_STATEMENTS = [
    "Your order ORD-1042 was delivered on 2 November.",
    "ORD-1077 was refunded on 3 October for $12.00.",
    "This order shows one refund of Rs 2,500.00, recorded last month.",
    "I can't refund orders in this chat yet.",
    "Your order is out for delivery with Parcelway.",
    "I couldn't find that order on your account. Could you check the ID?",
    "Would you like me to look up the tracking for ORD-1042?",
]


@pytest.mark.parametrize("reply", FALSE_CLAIMS)
def test_false_action_claims_are_replaced(reply: str) -> None:
    result = check_reply(reply)
    assert not result.passed and result.text == CORRECTION and result.matched


@pytest.mark.parametrize("reply", TRUE_STATEMENTS)
def test_factual_statements_pass_unchanged(reply: str) -> None:
    result = check_reply(reply)
    assert result.passed and result.text == reply


def card(action: str, state: str) -> ActionCard:
    return ActionCard(action=action, state=state, order_id="ORD-1042", explanation="x", at=datetime.now(UTC))  # type: ignore[arg-type]


REFUND_DONE = card("request_refund", "completed")
REFUND_WAITING = card("request_refund", "waiting_for_approval")
REFUND_REFUSED = card("request_refund", "not_allowed")
CREDIT_DONE = card("issue_store_credit", "completed")


@pytest.mark.parametrize(
    ("reply", "actions"),
    [
        ("I've refunded the kettle from ORD-1042.", [REFUND_DONE]),
        ("Your refund has been processed.", [REFUND_DONE]),
        ("I've submitted your refund for review by our team.", [REFUND_WAITING]),
        ("I've issued store credit for the lamp.", [CREDIT_DONE]),
    ],
)
def test_claims_backed_by_this_turns_action_log_pass(reply: str, actions: list[ActionCard]) -> None:
    assert check_reply(reply, actions).passed


@pytest.mark.parametrize(
    ("reply", "actions"),
    [
        ("Your refund has been processed.", [REFUND_WAITING]),  # waiting is not done
        ("I've refunded the kettle.", [REFUND_REFUSED]),  # refused is not done
        ("I've refunded the kettle.", [CREDIT_DONE]),  # a credit is not a refund
        ("I've cancelled ORD-1042 for you.", [REFUND_DONE]),  # wrong kind of action
        ("I've submitted the cancellation.", [REFUND_WAITING]),
    ],
)
def test_claims_the_action_log_does_not_show_are_replaced(reply: str, actions: list[ActionCard]) -> None:
    result = check_reply(reply, actions)
    assert not result.passed and result.text == CORRECTION_WITH_ACTIONS and result.matched


def test_one_false_claim_among_true_ones_fails_the_reply() -> None:
    reply = "I've refunded the kettle. I've also cancelled ORD-1050."
    assert not check_reply(reply, [REFUND_DONE]).passed


def test_typographic_punctuation_is_normalised_in_shown_text() -> None:
    result = check_reply("Your order ORD\u20111065 was delivered. I\u2019m glad it arrived!")
    assert result.passed and result.text == "Your order ORD-1065 was delivered. I'm glad it arrived!"


@pytest.mark.parametrize(
    "reply",
    ["I've also cancelled ORD-1050.", "We then refunded it.", "I've just now quickly refunded it."],
)
def test_adverbs_between_subject_and_verb_do_not_hide_a_claim(reply: str) -> None:
    assert not check_reply(reply).passed
