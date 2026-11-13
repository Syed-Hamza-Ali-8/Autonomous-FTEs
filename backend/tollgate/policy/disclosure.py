"""Group C of DECISIONS I15: internal control parameters that must never be customer-facing.

Built from `rules.yaml`, where the `disclosure` section marks each rule published (B) or internal (C). The
patterns cover the internal money limits (formatted, and as raw cents), the internal window length and count
as customers would read them ("90 days", "3rd refund"), every reason code, and every rule name. Published
terms (the 30-day return window, final sale, digital goods) and order-state facts (already shipped, already
refunded) are deliberately NOT here: they may be said.

Used by the customer-facing text test, the model-input audit, and the eval's reply monitor.
"""

import re
from dataclasses import dataclass
from functools import cache
from typing import Any, Literal

import yaml

from tollgate.actions.hints import REASON_CODES, RECHECK_CODES
from tollgate.domain.money import format_money
from tollgate.policy.engine import RULES_PATH

Kind = Literal["term", "limit_amount"]
ORDINAL = {2: "2nd", 3: "3rd", 4: "4th"}
WORDS = {2: "two", 3: "three", 4: "four"}


@dataclass(frozen=True)
class Pattern:
    kind: Kind  # "term": always a disclosure; "limit_amount": a money value equal to an internal limit
    regex: re.Pattern[str]
    source: str


def _rule_names(node: Any) -> set[str]:
    out: set[str] = set()
    if isinstance(node, dict):
        for k, v in node.items():
            if "_" in k:  # identifiers like return_window_days; plain section words are ordinary language
                out.add(k)
            out |= _rule_names(v)
    return out


def _amounts(node: Any) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("USD", "PKR") and isinstance(v, int):
                out.append((v, k))
            else:
                out += _amounts(v)
    return out


@cache
def internal_patterns() -> tuple[Pattern, ...]:
    rules = yaml.safe_load(RULES_PATH.read_text())
    internal = {k: rules[k] for k in rules["disclosure"]["internal"]}
    out: list[Pattern] = []

    def add(kind: Kind, rx: str, source: str) -> None:
        out.append(Pattern(kind, re.compile(rx, re.IGNORECASE), source))

    for key, value in internal.items():
        if key == "rolling_window_days":
            add("term", rf"\b{value}[- ]day|\b{value}\s+days\b", key)
        elif key == "max_refunds_in_window_before_approval":
            n = value + 1  # the one that needs approval
            add(
                "term",
                rf"\b(?:{ORDINAL[n]}|{['', 'first', 'second', 'third', 'fourth'][n]})\s+(?:refund|request)",
                key,
            )
            add("term", rf"\b(?:{value}|{WORDS[value]})\s+refunds?\b", key)
        for cents, ccy in _amounts(value):
            shown = format_money(cents, ccy)
            # not followed by more digits or decimals: Rs 15,000.01 is a different amount from Rs 15,000
            add("limit_amount", re.escape(shown) + r"(?![\d,]|\.\d)", f"{key} {ccy}")
            add("limit_amount", re.escape(shown.removesuffix(".00")) + r"(?![\d,]|\.\d)", f"{key} {ccy}")
            add("term", rf"\b{cents}\b", f"{key} {ccy} (cents)")
    for code in (*REASON_CODES, *RECHECK_CODES):
        add("term", rf"\b{re.escape(code)}\b", "reason code")
    for name in sorted(_rule_names(rules)):
        add("term", rf"\b{re.escape(name)}\b", "rule name")
    return tuple(out)


def find(text: str, kinds: tuple[Kind, ...] = ("term", "limit_amount")) -> list[str]:
    """The group-C values a text contains, as 'source: match'."""
    return [
        f"{p.source}: {m.group(0)}"
        for p in internal_patterns()
        if p.kind in kinds
        for m in p.regex.finditer(text)
    ]
