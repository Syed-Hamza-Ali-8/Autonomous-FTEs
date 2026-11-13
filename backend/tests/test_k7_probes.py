"""K7 fabricated-contact check: probes fc01-fc13 and mutations M55-M57, M64 (Phases 5+6 pre-registration
section 6; DECISIONS K7, L13, L16). Committed BEFORE the code they test: until `guardrails/facts.py` exists,
this module fails at import, which is the expected state of the pre-registration commit.

The check is deterministic and runs on every customer-facing reply beside the claim check. There is no prompt
line (L16): the check is the guarantee.
- Any email address, phone number or URL must be in the allowlist: the customer's own email and any contact
  detail present in this turn's tool results.
- A named unit ("[name] team / department / desk / unit / division") must be on the unit allowlist.
- A failing reply is replaced WHOLE by a fixed correction (L13, Q14). That correction offers a ticket or a
  person and contains no contact detail of any kind (fc09, fc13).

fc10-fc13 were added while writing the kill table, so that every mutation is killed by at least two probes
(K5). Adding probes tightens; nothing pre-registered was removed or loosened.
"""

import re
from collections.abc import Callable

import pytest

from tollgate.guardrails import facts

CUSTOMER_EMAIL = "amina.khan@example.com"
TRACKING = "NW9585258397"  # a real fixture tracking number (ORD-1042): digits that look like a phone number

# Broad patterns, deliberately independent of the module's own: the correction must match none of them.
ANY_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
ANY_PHONE = re.compile(r"(?:\+?\d[\d\s().-]{6,}\d|\b1-8\d\d-[\dA-Z-]{7,}\b)")
ANY_URL = re.compile(r"(?i)\b(?:https?://|www\.)\S+|\b[\w-]+\.(?:com|net|org|io|co|example)\b")
ANY_POSTAL = re.compile(r"(?i)\b\d{1,5}\s+\w+(?:\s+\w+)?\s+(?:street|st|road|rd|avenue|ave|lane|ln|blvd)\b")


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


# -- the fixed correction (L13, Q14) ---------------------------------------------------------------------


def fc09() -> list[str]:
    """The correction contains no contact detail of any kind, and offers a real next step."""
    text = facts.CORRECTION
    found = [rx.pattern for rx in (ANY_EMAIL, ANY_PHONE, ANY_URL, ANY_POSTAL) if rx.search(text)]
    out = expect("contact details in the correction", found, [])
    out += expect(
        "offers a ticket or a person", bool(re.search(r"(?i)\bticket\b|\bperson\b|support team", text)), True
    )
    return out + expect("passes its own check", fires(text), False)


def fc13() -> list[str]:
    """What a failing reply is replaced WITH carries no contact detail: the whole reply is replaced (Q14)."""
    result = facts.check_facts(
        "Email business-sales@northwindgoods.com or call 1-800-555-WHLS.", allowed_contacts=()
    )
    found = [rx.pattern for rx in (ANY_EMAIL, ANY_PHONE, ANY_URL, ANY_POSTAL) if rx.search(result.text)]
    return expect("failed", result.passed, False) + expect("contact details in what is shown", found, [])


PROBES: dict[str, Callable[[], list[str]]] = {
    f.__name__: f for f in (fc01, fc02, fc03, fc04, fc05, fc06, fc07, fc08, fc09, fc10, fc11, fc12, fc13)
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


def m64(mp: pytest.MonkeyPatch) -> None:  # the fixed correction gains a support email address
    mp.setattr(facts, "CORRECTION", facts.CORRECTION + " You can also email help@northwindgoods.example.")


KILLS: dict[str, tuple[Patch, tuple[str, ...]]] = {
    "M55": (m55, ("fc01", "fc10")),
    "M56": (m56, ("fc03", "fc11")),
    "M57": (m57, ("fc04", "fc12")),
    "M64": (m64, ("fc09", "fc13")),
}
OTHERS = {"fc02", "fc05"}  # positives guarded by test_probe; their patterns have no pre-registered mutation
NEGATIVES = {"fc06", "fc07", "fc08"}


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
