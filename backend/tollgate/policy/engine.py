"""Policy engine (spec 6.2 step 5, 6.3). Pure: facts in, decision out; no database, no clock reads.

The gateway gathers every fact with owner-filtered SQL and passes `now` from the injected clock (G1).
Reasons and their order are pre-registered in eval/ADVERSARIAL_PREREGISTRATION.md section 3: a denial
stops at its first reason; approval reasons are all collected, in order.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict

RULES_PATH = Path(__file__).with_name("rules.yaml")

Currency = Literal["USD", "PKR"]
Decision = Literal["ALLOW", "NEEDS_APPROVAL", "DENY"]
MoneyKind = Literal["refund", "store_credit"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Limits(_Strict):
    auto_max: dict[Currency, int]
    approval_max: dict[Currency, int]


class CancellationRules(_Strict):
    refund_captured_total: bool
    auto_approve_any_amount: bool
    counts_toward_window: bool
    audit_flag_above: dict[Currency, int]


class Rules(_Strict):
    return_window_days: int
    rolling_window_days: int
    max_refunds_in_window_before_approval: int
    refund: Limits
    store_credit: Limits
    window_amount_cap: dict[Currency, int]
    refundable_statuses: list[str]
    cancel_allowed_statuses: list[str]
    address_change_allowed_statuses: list[str]
    cancellation: CancellationRules

    def limits(self, kind: MoneyKind) -> Limits:
        return self.refund if kind == "refund" else self.store_credit


@cache
def load_rules(path: Path = RULES_PATH) -> Rules:
    return Rules.model_validate(yaml.safe_load(path.read_text()))


@dataclass(frozen=True)
class Verdict:
    decision: Decision
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class MoneyFacts:
    """Everything a refund or credit decision depends on, read from the database by the gateway."""

    kind: MoneyKind
    currency: Currency
    amount_cents: int  # recomputed: min(line value, the model's ceiling)
    order_status: str
    delivered_at: datetime | None
    any_final_sale: bool
    any_digital_downloaded: bool
    lines_already_compensated: bool  # H1: a pending or succeeded refund/credit covers one of these lines
    refundable_remainder_cents: int  # captured - refunds and credits pending or succeeded on this order
    window_count: int  # refunds + credits in the rolling window (cancellation refunds excluded, H2)
    window_total_cents: int  # their total in this currency


def evaluate_money(rules: Rules, facts: MoneyFacts, now: datetime) -> Verdict:
    if facts.order_status not in rules.refundable_statuses:
        return Verdict("DENY", ("status_not_refundable",))
    if facts.delivered_at is None or facts.delivered_at < now - timedelta(days=rules.return_window_days):
        return Verdict("DENY", ("outside_return_window",))
    if facts.any_final_sale:
        return Verdict("DENY", ("final_sale",))
    if facts.any_digital_downloaded:
        return Verdict("DENY", ("digital_downloaded",))
    if facts.lines_already_compensated:
        return Verdict("DENY", ("line_already_compensated",))
    if facts.amount_cents > facts.refundable_remainder_cents:
        return Verdict("DENY", ("exceeds_refundable_remainder",))
    limits = rules.limits(facts.kind)
    if facts.amount_cents > limits.approval_max[facts.currency]:
        return Verdict("DENY", ("above_approval_max",))
    reasons: list[str] = []
    if facts.amount_cents > limits.auto_max[facts.currency]:
        reasons.append("auto_max")
    if facts.window_count >= rules.max_refunds_in_window_before_approval:
        reasons.append("window_count")
    if facts.window_total_cents + facts.amount_cents > rules.window_amount_cap[facts.currency]:
        reasons.append("window_cap")
    return Verdict("NEEDS_APPROVAL", tuple(reasons)) if reasons else Verdict("ALLOW")


def evaluate_cancel(rules: Rules, order_status: str) -> Verdict:
    """A paid order's cancel carries its captured-total refund at any amount (H2); no approval step."""
    if order_status not in rules.cancel_allowed_statuses:
        return Verdict("DENY", ("status_not_cancellable",))
    return Verdict("ALLOW")


def evaluate_address_change(rules: Rules, order_status: str) -> Verdict:
    if order_status not in rules.address_change_allowed_statuses:
        return Verdict("DENY", ("status_not_addressable",))
    return Verdict("ALLOW")


def window_start(rules: Rules, now: datetime) -> datetime:
    return now - timedelta(days=rules.rolling_window_days)


def high_value_cancellation(rules: Rules, currency: Currency, refund_cents: int) -> bool:
    return refund_cents > rules.cancellation.audit_flag_above[currency]
