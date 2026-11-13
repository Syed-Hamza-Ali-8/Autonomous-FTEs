"""Claim check v2: probes cc01-cc10 and mutations M58-M60 (Phases 5+6 pre-registration section 7;
DECISIONS C1, C8, I14). Committed BEFORE the code they test: v1 compares only action kinds, so the order-ID
and amount probes (cc01-cc05) fail until v2 exists, and the mutation seams (`_order_matches`,
`_amount_matches`) don't exist yet. That is the expected state of the pre-registration commit.

v2 keeps v1's signature, `check_reply(reply, actions)`, and its replacement behaviour (C1). It adds:
- a claim that names an order needs a completed or waiting action of that kind ON THAT ORDER this turn;
- a claim that states an amount must equal, in the order's currency, the recomputed amount of a matching
  action this turn ($51.00, $51 and Rs 21,980 are all parsed; the currency must match).
Order-state facts read from the order (tier A) are not claims (cc09). Under-claims stay logged, never
blocked (I14).
"""

from collections.abc import Callable
from datetime import datetime

import pytest

from tests.probe_harness import FIXTURE_NOW
from tollgate.domain.models import ActionCard, ActionKind, ActionState, Currency, Money
from tollgate.guardrails import claims
from tollgate.guardrails.claims import ClaimCheck

AT: datetime = FIXTURE_NOW


def card(
    action: ActionKind, order: str, cents: int | None = None, currency: Currency = "USD",
    state: ActionState = "completed",
) -> ActionCard:  # fmt: skip
    amount = Money(amount_cents=cents, currency=currency) if cents is not None else None
    return ActionCard(action=action, state=state, order_id=order, amount=amount, reference="ACT-000001",
                      explanation="Done.", at=AT)  # fmt: skip


def caught(reply: str, actions: list[ActionCard]) -> bool:
    return not claims.check_reply(reply, actions).passed


def expect(label: str, got: object, want: object) -> list[str]:
    return [] if got == want else [f"{label}: got {got!r}, expected {want!r}"]


REFUND_1058 = card("request_refund", "ORD-1058", 5100)
REFUND_PKR = card("request_refund", "ORD-1075", 2198000, "PKR")


# -- should be caught ----------------------------------------------------------------------------------------


def cc01() -> list[str]:
    """The right action on the wrong order."""
    return expect("caught", caught("I've refunded your order ORD-1020.", [REFUND_1058]), True)


def cc02() -> list[str]:
    """The right action on the wrong order (cancellation)."""
    return expect(
        "caught", caught("I've cancelled ORD-1100 for you.", [card("cancel_order", "ORD-1101")]), True
    )


def cc03() -> list[str]:
    """The right order with the wrong amount."""
    return expect("caught", caught("I've refunded $61.00 for ORD-1058.", [REFUND_1058]), True)


def cc04() -> list[str]:
    """The wrong amount in PKR."""
    return expect("caught", caught("I've refunded Rs 12,980 on ORD-1075.", [REFUND_PKR]), True)


def cc05() -> list[str]:
    """The right figure in the wrong currency."""
    return expect("caught", caught("I've refunded Rs 51 on ORD-1058.", [REFUND_1058]), True)


def cc06() -> list[str]:
    """A claim with no action at all (v1 already catches this; M60 must break it)."""
    return expect("caught", caught("I've refunded ORD-1058.", []), True)


# -- should not be caught ------------------------------------------------------------------------------------


def cc07() -> list[str]:
    return expect("caught", caught("I've refunded $51.00 for the earbuds on ORD-1058.", [REFUND_1058]), False)


def cc08() -> list[str]:
    """A refusal that names the order is not a claim."""
    return expect("caught", caught("I couldn't refund ORD-1058: it's outside the return window.", []), False)


def cc09() -> list[str]:
    """History read from the order (tier A) is not a claim made this turn."""
    reply = "A refund of $48.00 was already issued for ORD-1020 on 3 Oct."
    return expect("caught", caught(reply, []), False)


def cc10() -> list[str]:
    """An amount within display rounding ($51 for 5100 cents) matches."""
    return expect("caught", caught("I've refunded $51 on ORD-1058.", [REFUND_1058]), False)


PROBES: dict[str, Callable[[], list[str]]] = {
    f.__name__: f for f in (cc01, cc02, cc03, cc04, cc05, cc06, cc07, cc08, cc09, cc10)
}


# -- mutations ----------------------------------------------------------------------------------------------

Patch = Callable[[pytest.MonkeyPatch], None]


def m58(mp: pytest.MonkeyPatch) -> None:  # the order-ID comparison is skipped
    mp.setattr(claims, "_order_matches", lambda claim, card: True)


def m59(mp: pytest.MonkeyPatch) -> None:  # the amount comparison is skipped
    mp.setattr(claims, "_amount_matches", lambda claim, card: True)


def m60(mp: pytest.MonkeyPatch) -> None:  # the check is removed entirely: "proven live" (spec 9.5)
    mp.setattr(
        claims, "check_reply", lambda reply, actions=(): ClaimCheck(passed=True, text=reply, matched=None)
    )


KILLS: dict[str, tuple[Patch, tuple[str, ...]]] = {
    "M58": (m58, ("cc01", "cc02")),
    "M59": (m59, ("cc03", "cc04", "cc05")),
    "M60": (m60, ("cc01", "cc02", "cc03", "cc04", "cc05", "cc06")),
}
NEGATIVES = {"cc07", "cc08", "cc09", "cc10"}  # must pass; guarded by test_probe


def _failures(probe: str) -> list[str]:
    try:
        return PROBES[probe]()
    except Exception as exc:  # a probe that breaks under a mutation has caught it
        return [f"{type(exc).__name__}: {exc}"]


@pytest.mark.parametrize("probe", sorted(PROBES))
def test_probe(probe: str) -> None:
    assert _failures(probe) == []


@pytest.mark.parametrize("mutant", sorted(KILLS))
def test_mutation_makes_its_probes_fail(mutant: str, monkeypatch: pytest.MonkeyPatch) -> None:
    patch, probes = KILLS[mutant]
    patch(monkeypatch)
    survivors = [p for p in probes if not _failures(p)]
    assert survivors == [], f"{mutant}: these probes still pass under the mutation"


def test_every_mutation_is_killed_by_at_least_two_probes_and_every_probe_is_accounted_for() -> None:
    assert all(len(set(probes)) >= 2 for _, probes in KILLS.values())
    assert {p for _, probes in KILLS.values() for p in probes} | NEGATIVES == set(PROBES)
