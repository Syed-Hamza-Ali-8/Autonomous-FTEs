"""Claim check (spec Section 9.5; invariant 10; DECISIONS C1, C8). Deterministic, no LLM.

v1 (Phase 3, interim): a reply may only claim an action this turn's action log shows. The log is the
gateway's ActionCards for the turn (built from its own outcomes, never from the model's text):
- a claim that something is DONE ("I've refunded", "your refund has been processed") needs a completed card
  of that kind;
- a claim that something was SUBMITTED ("I've submitted", "I've started") needs a completed or waiting card
  of that kind;
- a claim whose kind can't be told needs at least one such card of any kind.
A reply that fails is replaced by a fixed correction before anything reaches the screen or the DB (C1).
Phase 6 replaces this with the full pre-registered check and its mutation test.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from tollgate.domain.models import ActionCard

_VERB = (
    r"(?:refunded|cancell?ed|issued|processed|credited|updated|changed|approved|initiated|submitted"
    r"|started|scheduled|arranged|reversed|returned)"
)
ACTION_CLAIM = re.compile(
    rf"""(?ix)
    \b(?:i|we)(?:'ve|\s+have|\s+just|\s+now|'ll|\s+will)?\s+(?:(?:just|now|already|successfully|also|then|quickly|gone\s+ahead\s+and|went\s+ahead\s+and)\s+){{0,3}}
      (?:{_VERB}|refund|cancel|issue|process|credit|update|change|approve|initiate|submit|start|schedule|arrange)\b
    | \byour\s+(?:refund|cancell?ation|store\s+credit|credit|address(?:\s+change)?|order)\s+
      (?:has\s+been|have\s+been|is\s+being|was\s+just|is\s+now|will\s+be)\s+(?:now\s+|successfully\s+)?{_VERB}\b
    | \b(?:has|have)\s+been\s+{_VERB}\s+(?:for\s+you|just\s+now|successfully)\b
    """
)

# Typographic look-alikes models emit (curly quotes, Unicode hyphens/dashes, no-break spaces).
# Normalised BEFORE matching, so "I\u2019ve refunded" can't slip past a pattern written with "'".
_TYPOGRAPHY = str.maketrans(
    {
        "\u2018": "'", "\u2019": "'", "\u201b": "'", "\u2032": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2212": "-",
        "\u00a0": " ", "\u202f": " ", "\u2007": " ",
    }
)  # fmt: skip


def normalise(text: str) -> str:
    return text.translate(_TYPOGRAPHY)


CORRECTION = "Sorry, I need to correct that: nothing was changed on your account in this message."
CORRECTION_WITH_ACTIONS = (
    "Sorry, I need to correct that: the action details shown in this chat are exactly what was done."
)
SUBMITTED = re.compile(
    r"(?i)\b(?:submit|submitted|initiate|initiated|start|started|schedule|scheduled|arrange|arranged)\b"
)
KINDS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("issue_store_credit", re.compile(r"(?i)\b(?:store\s+)?credit(?:ed)?\b")),
    ("request_refund", re.compile(r"(?i)\brefund(?:ed|s)?\b|\bmoney\s+back\b|\breversed\b|\breturned\b")),
    ("cancel_order", re.compile(r"(?i)\bcancell?(?:ed|ation)?\b")),
    ("update_shipping_address", re.compile(r"(?i)\baddress\b")),
    ("escalate_to_human", re.compile(r"(?i)\b(?:escalat\w*|human|specialist|team\s+member|person)\b")),
    ("create_ticket", re.compile(r"(?i)\bticket\b")),
)
WINDOW = 80  # characters after a claim's verb searched for what the claim is about


@dataclass(frozen=True)
class ClaimCheck:
    passed: bool
    text: str  # the text that may be shown and stored (typography normalised)
    matched: str | None


def _kind(text: str, start: int, end: int) -> str | None:
    """What a claim is about: the first action word in the claim or just after it."""
    span = text[start : min(len(text), end + WINDOW)]
    found = [(m.start(), kind) for kind, rx in KINDS if (m := rx.search(span))]
    return min(found)[1] if found else None


def _backed(claim: str, kind: str | None, actions: Sequence[ActionCard]) -> bool:
    states = {"completed", "waiting_for_approval"} if SUBMITTED.search(claim) else {"completed"}
    return any(a.state in states and (kind is None or a.action == kind) for a in actions)


def check_reply(reply: str, actions: Sequence[ActionCard] = ()) -> ClaimCheck:
    text = normalise(reply)
    for match in ACTION_CLAIM.finditer(text):
        claim = match.group(0)
        if not _backed(claim, _kind(text, match.start(), match.end()), actions):
            return ClaimCheck(
                passed=False, text=CORRECTION_WITH_ACTIONS if actions else CORRECTION, matched=claim
            )
    return ClaimCheck(passed=True, text=text, matched=None)


# -- the reverse case: an action completed, but the reply omits it or says it didn't happen ------------------
# Logged (audit event `claim_check_under_claim`) and counted in eval summaries; never blocks (owner, Phase 3).

NEGATION = re.compile(
    r"(?i)\b(?:couldn't|could\s+not|can't|cannot|wasn't\s+able|was\s+not\s+able|unable|not\s+able|didn't"
    r"|did\s+not|haven't|have\s+not|won't|will\s+not|isn't\s+possible|not\s+possible)\b"
)
NEGATION_WINDOW = 40  # characters before a mention of the action searched for a negation


def under_claims(reply: str, actions: Sequence[ActionCard]) -> list[str]:
    """Completed actions the reply leaves out ("omitted:<action>") or denies ("denied:<action>")."""
    text = normalise(reply)
    kinds = dict(KINDS)
    out: list[str] = []
    for card in actions:
        if card.state != "completed":
            continue
        mentions = list(kinds[card.action].finditer(text))
        if not mentions and not (card.order_id and card.order_id in text):
            out.append(f"omitted:{card.action}")
            continue
        for m in mentions:
            if NEGATION.search(text[max(0, m.start() - NEGATION_WINDOW) : m.start()]):
                out.append(f"denied:{card.action}")
                break
    return out
