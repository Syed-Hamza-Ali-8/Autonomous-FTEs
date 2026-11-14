"""Fraud-signal matcher (Phase 4 pre-registration 2.1; DECISIONS J2).

Deterministic, over the CUSTOMER'S OWN TURN TEXT ONLY: never tool results, order notes or model output, which
are data (invariant 11). The runner calls it once per turn and stores the result on the turn context; the
gateway then routes any `order`- or `money`-tier action that policy would ALLOW to staff approval.

A heuristic may only tighten a decision, never loosen one (CLAUDE.md, J2): a flag can turn ALLOW into
NEEDS_APPROVAL and nothing else. Limitation, stated plainly: unusual phrasings, misspellings and other
languages are missed. It is a backstop, not a guarantee; a false positive only costs a staff review.
"""

import re

from tollgate.guardrails.claims import normalise

_PHRASES = re.compile(
    r"""
      \bnever\s+(?:placed|ordered|made|bought)\b
    | \b(?:didn't|did\s+not)\s+(?:place|order|make|authori[sz]e)\b
    | \b(?:wasn't|was\s+not|not)\s+me\b
    | \bnot\s+my\s+order\b
    | \bsomeone\s+(?:has\s+)?(?:used|is\s+using)\s+my\s+(?:card|account)\b
    | \bunauthori[sz]ed\b
    | \bfraud(?:ulent)?\b
    | \bstolen\s+card\b | \bcard\s+was\s+stolen\b | \baccount\s+was\s+hacked\b | \bhacked\b
    | \b(?:don't|do\s+not)\s+recogni[sz]e\s+this\s+(?:order|charge|payment)\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


def flagged(customer_text: str) -> bool:
    """True if the customer's turn text reports a possible unauthorised order or payment."""
    return _PHRASES.search(normalise(customer_text)) is not None
