"""Claim check v0 (Phase 1). Phase 6 replaces this with the pre-registered suite and its mutation check.

In Phase 1 no action can succeed, so any claim of a completed action must be replaced.
Statements about past, recorded facts (e.g. a refund last month) must pass unchanged.
"""

import pytest

from tollgate.guardrails.claims import CORRECTION, check_reply

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
    result = check_reply(reply, succeeded_actions_this_turn=0)
    assert not result.passed and result.text == CORRECTION and result.matched


@pytest.mark.parametrize("reply", TRUE_STATEMENTS)
def test_factual_statements_pass_unchanged(reply: str) -> None:
    result = check_reply(reply, succeeded_actions_this_turn=0)
    assert result.passed and result.text == reply


def test_turns_with_actions_are_not_silently_passed() -> None:
    # Until Phase 3 compares claims with the action log, a turn with actions must fail loudly.
    with pytest.raises(NotImplementedError):
        check_reply("I've refunded your order.", succeeded_actions_this_turn=1)


def test_typographic_punctuation_is_normalised_in_shown_text() -> None:
    result = check_reply("Your order ORD\u20111065 was delivered. I\u2019m glad it arrived!", 0)
    assert result.passed and result.text == "Your order ORD-1065 was delivered. I'm glad it arrived!"
