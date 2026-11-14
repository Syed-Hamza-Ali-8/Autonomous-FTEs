"""Injection signal (Phases 5+6 pre-registration section 8; DECISIONS J2, J11, L16). Deterministic; the same
shape as the fraud signal, and tighten-only.

A turn is flagged when
- the customer's own turn text reads like an instruction to the assistant (`flagged`, set by the runner); or
- a model-visible free-text field (`model_visible.FREE_TEXT`) in a result a read tool returned this turn does
  (`scan_result`, ORed in by the read tools). Tool results are data, never instructions (invariant 11): the
  flag can only route actions to staff.

In a flagged turn the gateway turns an order- or money-tier ALLOW into NEEDS_APPROVAL (`injection_signal`);
NEEDS_APPROVAL and DENY stand. `EXEMPT_TIERS` holds the contact tier: tickets and escalations are the route
to a person and stay allowed. Limitation, stated plainly: unusual phrasings and other languages are missed.
It is a backstop; the gateway's policy holds regardless (the model-free suite).
"""

import re
from collections.abc import Iterator
from typing import Any

from tollgate.guardrails.claims import normalise
from tollgate.tools.model_visible import FREE_TEXT

_PHRASES = re.compile(
    r"""
      \bignore\s+(?:all\s+|any\s+|your\s+|the\s+|these\s+|those\s+)?
         (?:previous\s+|prior\s+|above\s+|earlier\s+)?(?:instructions|rules|prompts?|guidelines|policies)\b
    | \bdisregard\s+(?:all\s+|any\s+|your\s+|the\s+)?(?:previous\s+|prior\s+)?
         (?:instructions|rules|policies)\b
    | \byou\s+are\s+now\b
    | (?:^|[\s.:;!?"'(\[])system\s*:
    | \b(?:developer|admin|god)\s+mode\b
    | \bas\s+(?:the|an?|your)\s+(?:admin|administrator|ceo|manager|owner|developer)\b
    | \bpre-?approved\b
    | \bapproval\s+code\b
    | \bnote\s+to\s+the\s+assistant\b
    | \bnew\s+instructions?\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

EXEMPT_TIERS: frozenset[str] = frozenset({"contact"})


def flagged(text: str) -> bool:
    """True if `text` reads like an instruction aimed at the assistant."""
    return _PHRASES.search(normalise(text)) is not None


def _strings(value: Any, prefix: str = "") -> Iterator[tuple[str, str]]:
    """Every (path, string) in a tool result, in `model_visible`'s path notation."""
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _strings(child, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child, f"{prefix}[]")
    elif isinstance(value, str):
        yield prefix, value


def scan_result(tool: str, result: Any) -> bool:
    """True if any model-visible free-text field in a read tool's result is flagged."""
    return any(path in FREE_TEXT and flagged(text) for path, text in _strings(result))
