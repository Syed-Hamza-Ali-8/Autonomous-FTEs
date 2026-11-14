"""K7: fabricated contact details and organisational units (Phases 5+6 pre-registration section 6; DECISIONS
K7, L13, L16). Deterministic, no LLM, and no prompt line: this check is the control.

In Phase 4 the agent gave a contact email and a phone number that exist nowhere in the store's data (e02) and
named a "fraud team" the store doesn't have (e03, f01). A reply passes only if
- every email address, phone number and URL in it appears in `allowed_contacts`: the customer's own email and
  the text of this turn's tool results, so a detail the tools actually returned may be repeated; and
- every named unit ("<word> team / department / desk / unit / division") is on `UNIT_ALLOWLIST`.

A failing reply is replaced WHOLE (L13, Q14) by a correction COMPOSED from this turn's action log
(`compose_correction`; owner, 2026-11-13). If actions SUCCEEDED this turn it states only them, in the action
cards' own words, with no refusal opening: the customer may never have asked for a detail. If none did, it
opens with the refusal and offers the next step. It never offers an action already done, and carries no
contact detail of any kind (probes fc09, fc13-fc18). Whether the runner shows it or only logs the finding is
`MODE`, set by the pre-committed L13 rule.

L19 (Phase 7): only the OFFER reads the whole conversation (`already_done`: the ticket and escalation kinds
completed in any turn of it). A step done in an earlier turn is never offered again: it is stated as fact,
and only the other is offered (probes fc19-fc21, fc24). What the correction says THIS turn did stays this
turn's action log: invariant 10 is unchanged (fc22, fc23).
"""

import re
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Literal

from tollgate.domain.models import ActionCard, ActionKind
from tollgate.guardrails.claims import normalise

# Set by the L13 rule (pre-registration section 6), never by judgement after the fact. Applied 2026-11-13:
# 3 of 116 recorded replies (2.59%) fired, all true positives, accepted by the owner (eval/K7_MEASUREMENT.md).
MODE: Literal["replace", "log"] = "replace"

# The refusal avoids the under-claim counter's negation words ("can't", "unable", ...): the counter runs on
# the delivered text, and a negation just before a completed action reads as denying it (probe fc18).
OPENING = "I'm sorry, I don't have that detail to give you."
NEXT_STEP = (
    "I can open a support ticket for you, or pass you to a member of our support team. Just say which."
)


# L19: a step done in an earlier turn is never offered again. When one of the two is done, it is stated
# as fact and the other offered (owner, 2026-11-14: offering a step to someone who already has it is
# misleading by omission); when both are, both are stated and nothing is offered. These sentences report the
# conversation's action log; what THIS turn did comes only from this turn's cards (invariant 10 unchanged).
ESCALATED_FACT = "This is already with a member of our support team."
TICKET_FACT = "A support ticket has already been opened for you."
OFFER_TICKET = "I can also open a support ticket if you'd like."
OFFER_PERSON = "I can also pass you to a member of our support team if you'd like."
BOTH_DONE = (
    "A support ticket has already been opened for you, and this is already with a member of our support team."
)


def _next_step(already_done: Collection[ActionKind]) -> str:
    ticket, person = "create_ticket" in already_done, "escalate_to_human" in already_done
    if ticket and person:
        return BOTH_DONE
    if person:
        return f"{ESCALATED_FACT} {OFFER_TICKET}"
    if ticket:
        return f"{TICKET_FACT} {OFFER_PERSON}"
    return NEXT_STEP


def compose_correction(actions: Sequence[ActionCard] = (), already_done: Collection[ActionKind] = ()) -> str:
    """The replacement for a reply that failed the check. What it states comes from this turn's action log
    (the cards' source); what it offers also skips what any turn of the conversation already did (L19)."""
    done = list(dict.fromkeys(a.explanation for a in actions if a.state == "completed"))
    # When something succeeded, state only that: the customer may never have asked for a detail (e03 and f01
    # reported fraud), so a refusal opening would be a non-sequitur (owner, 2026-11-13).
    return " ".join(done) if done else f"{OPENING} {_next_step(already_done)}"


EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# A phone number: 9+ digits with the usual separators, not inside a longer token (an order ID or a tracking
# number). Vanity toll-free numbers such as 1-800-555-WHLS are their own pattern: they carry fewer digits.
PHONE = re.compile(r"(?<![\w-])\+?\(?\d[\d\s().-]{7,}\d(?![\w-])")
VANITY = re.compile(r"\b1-8\d\d-[\dA-Z]{3}-?[\dA-Z]{4}\b")
URL = re.compile(
    r"(?i)\b(?:https?://|www\.)[^\s<>()]+"
    # a bare domain, never one straight after "@": that is an email address, EMAIL's job
    r"|(?<![@\w.-])[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|io|co|uk|pk|shop|store|example)\b(?:/[^\s<>()]*)?"
)
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
UNIT = re.compile(r"(?i)\b([a-z]+)\s+(team|department|desk|unit|division)\b")
# A determiner or quantity before the noun names no particular unit ("our team", "per unit").
_GENERIC = frozenset({"our", "the", "a", "an", "your", "my", "this", "that", "per", "each", "whole"})
UNIT_ALLOWLIST: frozenset[str] = frozenset({"support team"})


@dataclass(frozen=True)
class FactCheck:
    passed: bool
    text: str  # what may be shown: the reply, or the composed correction when it fails
    matched: list[str]  # what failed, for the audit log and the measurement


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def _allowed(found: str, allowed: list[str]) -> bool:
    if "@" in found or not _digits(found):
        return any(found.lower() in a for a in allowed)
    return any(_digits(found) in _digits(a) for a in allowed)


def findings(reply: str, allowed_contacts: Collection[str] = ()) -> list[str]:
    """Every contact detail or unit in `reply` that the allowlists don't cover."""
    text = normalise(reply)
    allowed = [a.lower() for a in allowed_contacts]
    out: list[str] = []
    emails = [m.group(0) for m in EMAIL.finditer(text)]
    out += [f"email:{e}" for e in emails if not _allowed(e, allowed)]
    rest = EMAIL.sub(" ", text)  # an email's domain is not a separate URL
    for m in PHONE.finditer(rest):
        number = m.group(0).strip()
        if len(_digits(number)) >= 9 and not _DATE.match(number) and not _allowed(number, allowed):
            out.append(f"phone:{number}")
    out += [f"phone:{m.group(0)}" for m in VANITY.finditer(rest) if not _allowed(m.group(0), allowed)]
    out += [f"url:{m.group(0)}" for m in URL.finditer(rest) if not _allowed(m.group(0), allowed)]
    for m in UNIT.finditer(text):
        word, noun = m.group(1).lower(), m.group(2).lower()
        if word not in _GENERIC and f"{word} {noun}" not in UNIT_ALLOWLIST:
            out.append(f"unit:{word} {noun}")
    return out


def check_facts(
    reply: str,
    allowed_contacts: Collection[str] = (),
    actions: Sequence[ActionCard] = (),
    already_done: Collection[ActionKind] = (),
) -> FactCheck:
    found = findings(reply, allowed_contacts)
    if found:
        return FactCheck(passed=False, text=compose_correction(actions, already_done), matched=found)
    return FactCheck(passed=True, text=normalise(reply), matched=[])
