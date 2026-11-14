"""K7 fabricated-contact check: probes fc01-fc13 and mutations M55-M57, M64 (Phases 5+6 pre-registration
section 6; DECISIONS K7, L13, L16). Committed BEFORE the code they test: until `guardrails/facts.py` exists,
this module fails at import, which is the expected state of the pre-registration commit.

The check is deterministic and runs on every customer-facing reply beside the claim check. There is no prompt
line (L16): the check is the guarantee.
- Any email address, phone number or URL must be in the allowlist: the customer's own email and any contact
  detail present in this turn's tool results.
- A named unit ("[name] team / department / desk / unit / division") must be on the unit allowlist.
- A failing reply is replaced WHOLE (L13, Q14) by a correction COMPOSED from this turn's action log (owner,
  2026-11-13, after review found the fixed text dropped an executed escalation in e03/f01): if actions
  SUCCEEDED this turn it states ONLY them, in the action cards' own words, with no refusal opening (the
  customer may never have asked for a detail: e03 and f01 reported fraud) (fc14, fc17); if none did, it opens
  with the refusal and offers the next step, in exactly the text pinned by fc15; it never offers an action
  that already succeeded (fc14, fc17); it causes no under-claim (fc18); and it carries no contact detail of
  any kind (fc09, fc13).

fc10-fc13 were added while writing the kill table, so that every mutation is killed by at least two probes
(K5). Adding probes tightens; nothing pre-registered was removed or loosened.
"""

import re
from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from tollgate.actions import cards
from tollgate.domain.models import ActionCard, ActionKind
from tollgate.guardrails import claims, facts

CUSTOMER_EMAIL = "amina.khan@example.com"
TRACKING = "NW9585258397"  # a real fixture tracking number (ORD-1042): digits that look like a phone number

# Broad patterns, deliberately independent of the module's own: the correction must match none of them.
ANY_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
ANY_PHONE = re.compile(r"(?:\+?\d[\d\s().-]{6,}\d|\b1-8\d\d-[\dA-Z-]{7,}\b)")
ANY_URL = re.compile(r"(?i)\b(?:https?://|www\.)\S+|\b[\w-]+\.(?:com|net|org|io|co|example)\b")
ANY_POSTAL = re.compile(r"(?i)\b\d{1,5}\s+\w+(?:\s+\w+)?\s+(?:street|st|road|rd|avenue|ave|lane|ln|blvd)\b")


OFFER = re.compile(
    r"(?i)\bI can (?:open|pass|escalate|connect|hand)\b|\bjust say which\b|\bwould you like me to\b"
)
KINDS: tuple[ActionKind, ...] = (
    "request_refund", "issue_store_credit", "cancel_order", "update_shipping_address", "create_ticket",
    "escalate_to_human",
)  # fmt: skip


NO_ACTION_TEXT = (
    "I'm sorry, I don't have that detail to give you. I can open a support ticket for you, or pass you to a "
    "member of our support team. Just say which."
)


def done(action: ActionKind) -> ActionCard:
    """A completed card, built as the gateway builds one (cards.DONE is its explanation)."""
    return ActionCard(
        action=action,
        state="completed",
        order_id="ORD-1042",
        reference="ACT-000001",
        explanation=cards.DONE[action],
        at=datetime(2026, 11, 7, tzinfo=UTC),
    )


def fires(reply: str, allowed: tuple[str, ...] = ()) -> bool:
    return not facts.check_facts(reply, allowed_contacts=allowed).passed


def expect(label: str, got: object, want: object) -> list[str]:
    return [] if got == want else [f"{label}: got {got!r}, expected {want!r}"]


# -- should fire ---------------------------------------------------------------------------------------------


def fc01() -> list[str]:
    return expect("fires", fires("You can email business-sales@northwindgoods.com to set that up."), True)


def fc02() -> list[str]:
    """A vanity phone number, as e02 gave in the Phase 4 run."""
    return expect("fires", fires("Call our wholesale line on 1-800-555-WHLS any weekday."), True)


def fc03() -> list[str]:
    return expect(
        "fires", fires("Fill in the form at https://northwind-wholesale.example/apply and we'll reply."), True
    )


def fc04() -> list[str]:
    """A unit the store doesn't have, as e03 and f01 named in the Phase 4 run."""
    return expect("fires", fires("I've passed this to our fraud team, who will be in touch."), True)


def fc05() -> list[str]:
    return expect("fires", fires("Our billing department can look into that charge for you."), True)


def fc10() -> list[str]:
    """An email in angle brackets, mixed case."""
    return expect("fires", fires("Write to <Partners@NorthwindGoods.COM> for an account."), True)


def fc11() -> list[str]:
    """A URL without a scheme."""
    return expect("fires", fires("Everything is explained at www.northwind-help.com/wholesale."), True)


def fc12() -> list[str]:
    """The same invented unit, capitalised and as the sentence subject."""
    return expect("fires", fires("The Fraud Team will call you within a day."), True)


# -- should not fire ---------------------------------------------------------------------------------------


def fc06() -> list[str]:
    """The customer's own email repeated back is allowed."""
    reply = f"I've noted that updates go to {CUSTOMER_EMAIL}."
    return expect("fires", fires(reply, allowed=(CUSTOMER_EMAIL,)), False)


def fc07() -> list[str]:
    """A tracking number from this turn's tool results is allowed, even though it looks like digits."""
    reply = f"Your parcel's tracking number is {TRACKING}, with SwiftShip."
    return expect("fires", fires(reply, allowed=(TRACKING,)), False)


def fc08() -> list[str]:
    return expect(
        "fires", fires("I've passed this to a member of our support team, who will reply here."), False
    )


# -- the composed correction (L13, Q14; composed from the action log, owner 2026-11-13) ------------------


def fc09() -> list[str]:
    """No correction, with or without completed actions, contains a contact detail of any kind; the one for a
    turn with no completed action offers a real next step."""
    out: list[str] = []
    for actions in ([], *([done(k)] for k in KINDS)):
        text = facts.compose_correction(actions)
        found = [rx.pattern for rx in (ANY_EMAIL, ANY_PHONE, ANY_URL, ANY_POSTAL) if rx.search(text)]
        out += expect(f"contact details ({[a.action for a in actions]})", found, [])
        out += expect(f"passes its own check ({[a.action for a in actions]})", fires(text), False)
    text = facts.compose_correction([])
    return out + expect(
        "offers a ticket or a person", bool(re.search(r"(?i)\bticket\b|\bperson\b|support team", text)), True
    )


def fc14() -> list[str]:
    """A reply replaced in a turn where an escalation SUCCEEDED mentions the escalation and does not offer to
    escalate again (e03, f01)."""
    result = facts.check_facts("I've escalated this to our fraud team.", (), [done("escalate_to_human")])
    out = expect("replaced", result.passed, False)
    out += expect("only the escalation, no opening", result.text, cards.DONE["escalate_to_human"])
    return out + expect("offers it again", bool(OFFER.search(result.text)), False)


def fc15() -> list[str]:
    """A reply replaced in a turn with no successful action opens with the refusal and offers the next step,
    in the text approved on 2026-11-13 (pinned: unchanged by the owner's polish of the succeeded case)."""
    result = facts.check_facts("Our fraud team will call you.", (), [])
    out = expect("replaced", result.passed, False)
    out += expect("offers the next step", bool(OFFER.search(result.text)), True)
    return out + expect("unchanged text", result.text, NO_ACTION_TEXT)


def fc17() -> list[str]:
    """The same for a ticket opened this turn: stated, not offered again."""
    result = facts.check_facts("Our billing department will email you.", (), [done("create_ticket")])
    out = expect("replaced", result.passed, False)
    out += expect("only the ticket, no opening", result.text, cards.DONE["create_ticket"])
    return out + expect("offers it again", bool(OFFER.search(result.text)), False)


def fc18() -> list[str]:
    """A composed correction causes no under-claim for any completed action: it states every one, and its
    refusal does not read as denying them (the under-claim counter runs on the delivered text)."""
    out: list[str] = []
    for kind in KINDS:
        card = done(kind)
        out += expect(kind, claims.under_claims(facts.compose_correction([card]), [card]), [])
    return out


def fc13() -> list[str]:
    """What a failing reply is replaced WITH carries no contact detail: the whole reply is replaced (Q14)."""
    result = facts.check_facts(
        "Email business-sales@northwindgoods.com or call 1-800-555-WHLS.", allowed_contacts=()
    )
    found = [rx.pattern for rx in (ANY_EMAIL, ANY_PHONE, ANY_URL, ANY_POSTAL) if rx.search(result.text)]
    return expect("failed", result.passed, False) + expect("contact details in what is shown", found, [])


# -- L19: the offer reads the whole conversation; what the reply CLAIMS stays this turn's (PHASE7 item 2) -------

OPENING = "I'm sorry, I don't have that detail to give you."
ESCALATED_EARLIER_TEXT = f"{OPENING} I can open a support ticket for you, if you'd like."
TICKET_EARLIER_TEXT = f"{OPENING} I can pass you to a member of our support team, if you'd like."
BOTH_EARLIER_TEXT = (
    f"{OPENING} A support ticket has already been opened for you, and this is already with a member of our "
    "support team."
)
ESCALATION_OFFER = re.compile(r"(?i)\bI can (?:pass|escalate|connect|hand)\b|\bjust say which\b")
TICKET_OFFER = re.compile(r"(?i)\bI can (?:also )?open a support ticket\b|\bjust say which\b")


def _no_action_turn(already_done: set[ActionKind]) -> facts.FactCheck:
    return facts.check_facts("Our fraud team will call you.", (), [], already_done=already_done)


def _claims_nothing(text: str) -> list[str]:
    """Invariant 10 unchanged: with no action this turn, the delivered text passes the claim check as is."""
    return expect("claim check on the delivered text", claims.check_reply(text, []).passed, True)


def fc19() -> list[str]:
    """adv08: replaced in a turn with no action, in a conversation whose EARLIER turn escalated: no escalation
    is offered; the ticket still is."""
    result = _no_action_turn({"escalate_to_human"})
    out = expect("replaced", result.passed, False)
    out += expect("offers escalation again", bool(ESCALATION_OFFER.search(result.text)), False)
    out += expect("text", result.text, ESCALATED_EARLIER_TEXT)
    return out + _claims_nothing(result.text)


def fc20() -> list[str]:
    """The same with an earlier ticket: no ticket is offered; escalation still is."""
    result = _no_action_turn({"create_ticket"})
    out = expect("replaced", result.passed, False)
    out += expect("offers a ticket again", bool(TICKET_OFFER.search(result.text)), False)
    out += expect("text", result.text, TICKET_EARLIER_TEXT)
    return out + _claims_nothing(result.text)


def fc21() -> list[str]:
    """Both done earlier: nothing is offered; it says so factually (the conversation's action log as fact),
    and the delivered text passes the claim check and its own check."""
    result = _no_action_turn({"create_ticket", "escalate_to_human"})
    out = expect("replaced", result.passed, False)
    out += expect("offers anything", bool(OFFER.search(result.text)), False)
    out += expect("text", result.text, BOTH_EARLIER_TEXT)
    out += expect("passes its own check", fires(result.text), False)
    return out + _claims_nothing(result.text)


def fc22() -> list[str]:
    """Earlier actions outside the offer (a refund, a cancellation) change nothing: the next step is offered
    in the pinned text."""
    return expect("text", _no_action_turn({"request_refund", "cancel_order"}).text, NO_ACTION_TEXT)


def fc23() -> list[str]:
    """What THIS turn did is still all a correction states, even when earlier turns did more (invariant 10's
    side stays turn-scoped): the escalation done now is stated in its card's words, nothing else."""
    result = facts.check_facts(
        "I've escalated this to our fraud team.", (), [done("escalate_to_human")], already_done={"create_ticket"}
    )
    return expect("text", result.text, cards.DONE["escalate_to_human"])


PROBES: dict[str, Callable[[], list[str]]] = {
    f.__name__: f
    for f in (
        fc01,
        fc02,
        fc03,
        fc04,
        fc05,
        fc06,
        fc07,
        fc08,
        fc09,
        fc10,
        fc11,
        fc12,
        fc13,
        fc14,
        fc15,
        fc17,
        fc18,
        fc19,
        fc20,
        fc21,
        fc22,
        fc23,
    )
}


# -- mutations ----------------------------------------------------------------------------------------------

Patch = Callable[[pytest.MonkeyPatch], None]
NEVER = re.compile(r"(?!x)x")


def m55(mp: pytest.MonkeyPatch) -> None:  # the email pattern is removed
    mp.setattr(facts, "EMAIL", NEVER)


def m56(mp: pytest.MonkeyPatch) -> None:  # every URL is let through
    mp.setattr(facts, "URL", NEVER)


def m57(mp: pytest.MonkeyPatch) -> None:  # "fraud team" is put on the unit allowlist
    mp.setattr(facts, "UNIT_ALLOWLIST", facts.UNIT_ALLOWLIST | {"fraud team"})


def m64(mp: pytest.MonkeyPatch) -> None:  # the correction gains a support email address
    mp.setattr(facts, "NEXT_STEP", facts.NEXT_STEP + " You can also email help@northwindgoods.example.")


FIXED = (
    "I'm sorry, I can't share that detail. I can open a support ticket for you, or pass you to a member of "
    "our support team. Just say which."
)  # the fixed correction K7 first shipped with (before the owner's review, 2026-11-13)


def m66(mp: pytest.MonkeyPatch) -> None:  # the correction reverts to fixed text, ignoring the action log
    mp.setattr(facts, "compose_correction", lambda actions=(), already_done=(): FIXED)


def m67(mp: pytest.MonkeyPatch) -> None:  # a turn with no completed action is no longer offered a next step
    mp.setattr(facts, "NEXT_STEP", "")


def m71(mp: pytest.MonkeyPatch) -> None:  # L19 reverted: the offer reads only this turn's actions again
    turn_scoped = facts.compose_correction
    mp.setattr(facts, "compose_correction", lambda actions=(), already_done=(): turn_scoped(actions))


KILLS: dict[str, tuple[Patch, tuple[str, ...]]] = {
    "M55": (m55, ("fc01", "fc10")),
    "M56": (m56, ("fc03", "fc11")),
    "M57": (m57, ("fc04", "fc12")),
    "M64": (m64, ("fc09", "fc13")),
    "M66": (m66, ("fc14", "fc17", "fc18")),  # plus test_api's fc16, through the runner
    "M67": (m67, ("fc15", "fc09")),
    "M71": (m71, ("fc19", "fc20", "fc21")),  # plus test_api's fc24, through the runner
}
OTHERS = {"fc02", "fc05"}  # positives guarded by test_probe; their patterns have no pre-registered mutation
NEGATIVES = {"fc06", "fc07", "fc08", "fc22", "fc23"}  # fc22, fc23: L19 must change nothing outside the offer


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
    assert {p for _, probes in KILLS.values() for p in probes} | OTHERS | NEGATIVES == set(PROBES)
