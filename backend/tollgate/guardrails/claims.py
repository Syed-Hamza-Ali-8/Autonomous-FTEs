"""Claim check (spec Section 9.5; invariant 10; DECISIONS C1, C8). Deterministic, no LLM.

v0 (Phase 1): flags replies that claim a completed write action ("I've refunded...", "your refund has
been processed"). Phase 1 has no write tools, so the action log is always empty and any such claim
is false: the reply is replaced by a fixed correction before anything reaches the screen or the DB.
Phase 6 replaces this with the full pre-registered check (claims vs. this turn's action log) and
its mutation test.
"""

import re
from dataclasses import dataclass

_VERB = (
    r"(?:refunded|cancell?ed|issued|processed|credited|updated|changed|approved|initiated|submitted"
    r"|started|scheduled|arranged|reversed|returned)"
)
ACTION_CLAIM = re.compile(
    rf"""(?ix)
    \b(?:i|we)(?:'ve|\s+have|\s+just|\s+now|'ll|\s+will)?\s+(?:just\s+|now\s+|already\s+|successfully\s+|gone\s+ahead\s+and\s+)?
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


CORRECTION = (
    "Sorry, I haven't made any changes to your account in this chat. I can look up your orders, "
    "shipping and refund history, but I can't refund, cancel or change an order here yet."
)


@dataclass(frozen=True)
class ClaimCheck:
    passed: bool
    text: str  # the text that may be shown and stored (typography normalised)
    matched: str | None


def check_reply(reply: str, succeeded_actions_this_turn: int) -> ClaimCheck:
    if succeeded_actions_this_turn > 0:
        # Phase 3+ compares each claim with the action log; until then no action can succeed.
        raise NotImplementedError("claim check for turns with actions arrives with write tools")
    text = normalise(reply)
    match = ACTION_CLAIM.search(text)
    if match is None:
        return ClaimCheck(passed=True, text=text, matched=None)
    return ClaimCheck(passed=False, text=CORRECTION, matched=match.group(0))
