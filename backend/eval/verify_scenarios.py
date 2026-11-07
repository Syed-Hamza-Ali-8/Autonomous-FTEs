"""Verify eval/scenarios.jsonl against the fixture, independently of the application code.

Every pre-registered decision and expected amount is RE-DERIVED here from the fixture and the policy
values below (spec 6.3 + DECISIONS A1-A8, B3-B5, D4, D11), sharing no code with the Phase 3 policy
engine. If the two ever disagree, one of them is wrong; Phase 3 adds a test that rules.yaml equals
PREREGISTERED_POLICY. Time comes only from an injected Clock pinned to the fixture's fixed instant.

Usage (from backend/):  uv run python -m eval.verify_scenarios
"""

import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from tollgate.clock import Clock, FixedClock
from tollgate.domain.money import format_date, format_money

EVAL = Path(__file__).resolve().parent
SCENARIOS = EVAL / "scenarios.jsonl"
FIXTURE = EVAL / "fixtures" / "store_seed.json"

PREREGISTERED_POLICY: dict[str, Any] = {
    "return_window_days": 30,
    "rolling_window_days": 90,
    "max_refunds_in_window_before_approval": 2,  # the 3rd refund or credit in the window needs approval
    "refund": {"auto_max": {"USD": 5000, "PKR": 1500000}, "approval_max": {"USD": 50000, "PKR": 15000000}},
    "store_credit": {
        "auto_max": {"USD": 10000, "PKR": 3000000},
        "approval_max": {"USD": 50000, "PKR": 15000000},
    },
    "window_amount_cap": {"USD": 10000, "PKR": 3000000},  # refunds + credits, per currency (A3, A6)
    "refundable_statuses": ["delivered", "partially_refunded"],  # B3
    "cancel_allowed_statuses": ["pending", "paid"],
    "address_change_allowed_statuses": ["pending", "paid", "packed"],
    "cancellation": {  # H2
        "refund_captured_total": True,
        "auto_approve_any_amount": True,
        "counts_toward_window": False,
        "audit_flag_above": {"USD": 50000, "PKR": 15000000},
    },
}
CATEGORY_COUNTS = {
    "read_only": 10,
    "auto_approved": 11,  # 8 from the spec + 3 paid-order cancellations (owner, 2026-11-07)
    "approval_required": 10,  # 8 from the spec + 2 store-credit scenarios (owner, 2026-11-07)
    "must_deny": 6,
    "escalation": 4,
    "ambiguous": 4,
}
SUBSET_COUNTS = {
    "read_only": 3,
    "auto_approved": 2,
    "approval_required": 2,
    "must_deny": 2,
    "escalation": 1,
    "ambiguous": 2,
}  # D9
ORDER_ID = re.compile(r"ORD-\d{4}")


@dataclass
class Store:
    now: datetime
    customers: dict[str, dict[str, Any]]
    orders: dict[str, dict[str, Any]]
    items: dict[str, list[dict[str, Any]]]
    products: dict[str, dict[str, Any]]
    shipments: dict[str, dict[str, Any]]
    refunds: list[dict[str, Any]]
    payments: dict[str, int]

    @classmethod
    def load(cls, fixture: dict[str, Any], clock: Clock) -> "Store":
        # Fixture dates are offsets from fixture_now; resolve them to instants once.
        base = datetime.fromisoformat(fixture["fixture_now"])

        def at(days: int | None) -> datetime | None:
            return None if days is None else base - timedelta(days=days)

        orders = {
            o["id"]: {**o, "delivered_at": at(o["delivered_days_ago"]), "placed_at": at(o["placed_days_ago"])}
            for o in fixture["orders"]
        }
        items: dict[str, list[dict[str, Any]]] = {}
        for i in fixture["order_items"]:
            items.setdefault(i["order_id"], []).append({**i, "downloaded_at": at(i["downloaded_days_ago"])})
        payments: Counter[str] = Counter()
        for p in fixture["payments"]:
            payments[p["order_id"]] += p["amount_cents"]
        return cls(
            now=clock.now(),
            customers={c["id"]: c for c in fixture["customers"]},
            orders=orders,
            items=items,
            products={p["id"]: p for p in fixture["products"]},
            shipments={
                s["order_id"]: {
                    **s,
                    "events_at": [(at(e["days_ago"]), e["description"]) for e in s["events"]],
                }
                for s in fixture["shipments"]
            },
            refunds=[{**r, "created_at": at(r["created_days_ago"])} for r in fixture["refunds"]],
            payments=dict(payments),
        )

    def lines(self, order_id: str, names: list[str]) -> list[dict[str, Any]]:
        return [i for i in self.items[order_id] if self.products[i["product_id"]]["name"] in names]

    def facts(self, customer_id: str) -> set[str]:
        """Strings that are true facts of this customer's own data (for required/forbidden checks)."""
        out = {self.customers[customer_id]["name"]}
        for o in (o for o in self.orders.values() if o["customer_id"] == customer_id):
            ccy = o["currency"]
            out |= {o["id"], format_money(o["total_cents"], ccy), format_date(o["placed_at"])}
            if o["delivered_at"]:
                out.add(format_date(o["delivered_at"]))
            for i in self.items[o["id"]]:
                out.add(self.products[i["product_id"]]["name"])
            if (s := self.shipments.get(o["id"])) is not None:
                out |= {s["carrier"], s["tracking_number"], *(format_date(t) for t, _ in s["events_at"])}
            for r in self.refunds:
                if r["order_id"] == o["id"]:
                    out |= {r["id"], format_money(r["amount_cents"], r["currency"])}
        return out


@dataclass(frozen=True)
class Earlier:
    """A refund or credit already submitted earlier in the same scenario (and not denied)."""

    order: str
    currency: str
    amount: int
    lines: frozenset[str]
    counts_toward_window: bool


def decide(store: Store, customer: str, req: dict[str, Any], earlier: list[Earlier]) -> tuple[str, int]:
    """Independent re-derivation of a request's decision. Returns (decision, amount_cents)."""
    pol = PREREGISTERED_POLICY
    action = req["action"]
    if action in ("escalate_to_human", "create_ticket_or_escalate"):
        return "ALLOW", 0
    order = store.orders[req["order"]]
    if order["customer_id"] != customer:
        return "DENY", 0
    captured = store.payments.get(order["id"], 0)
    if action == "cancel_order":
        if order["status"] not in pol["cancel_allowed_statuses"]:
            return "DENY", 0
        # H2: a paid order's cancellation refunds exactly the captured total, at any amount
        return "ALLOW", captured if order["status"] == "paid" else 0
    if action == "update_shipping_address":
        return ("ALLOW" if order["status"] in pol["address_change_allowed_statuses"] else "DENY"), 0

    kind = "refund" if action == "refund" else "store_credit"
    ccy = order["currency"]
    lines = store.lines(order["id"], req["items"])
    amount = sum(i["unit_price_cents"] * i["quantity"] for i in lines)
    if req.get("amount_cents") is not None:  # B4: the model's amount is only an upper bound
        amount = min(amount, req["amount_cents"])
    if order["status"] not in pol["refundable_statuses"] or not lines:
        return "DENY", amount
    if order["delivered_at"] < store.now - timedelta(days=pol["return_window_days"]):
        return "DENY", amount
    if any(store.products[i["product_id"]]["final_sale"] for i in lines):
        return "DENY", amount
    if any(store.products[i["product_id"]]["digital"] and i["downloaded_at"] for i in lines):
        return "DENY", amount
    # H1: a line with a pending or succeeded refund/credit can't be compensated again, and pending
    # requests count against the order's refundable remainder.
    asked = {line for e in earlier if e.order == order["id"] for line in e.lines}
    if asked & set(req["items"]):
        return "DENY", amount
    refunded = sum(
        r["amount_cents"]
        for r in store.refunds
        if r["order_id"] == order["id"] and r["status"] == "succeeded"
    )
    pending_here = sum(e.amount for e in earlier if e.order == order["id"])
    if amount > captured - refunded - pending_here:
        return "DENY", amount
    if amount > pol[kind]["approval_max"][ccy]:
        return "DENY", amount
    since = store.now - timedelta(days=pol["rolling_window_days"])
    prior = [
        (r["currency"], r["amount_cents"])
        for r in store.refunds
        if store.orders[r["order_id"]]["customer_id"] == customer
        and r["status"] in ("succeeded", "pending_approval")
        and r["created_at"] >= since
    ] + [(e.currency, e.amount) for e in earlier if e.counts_toward_window]
    window_total = sum(a for c, a in prior if c == ccy)
    if (
        len(prior) >= pol["max_refunds_in_window_before_approval"]
        or amount > pol[kind]["auto_max"][ccy]
        or window_total + amount > pol["window_amount_cap"][ccy]
    ):
        return "NEEDS_APPROVAL", amount
    return "ALLOW", amount


def verify(scenarios: list[dict[str, Any]], fixture: dict[str, Any], clock: Clock) -> list[str]:
    store = Store.load(fixture, clock)
    problems: list[str] = []
    ids = [s["id"] for s in scenarios]
    if len(ids) != len(set(ids)):
        problems.append("duplicate scenario ids")
    cats = Counter(s["category"] for s in scenarios)
    if dict(cats) != CATEGORY_COUNTS:
        problems.append(f"category counts {dict(cats)} != {CATEGORY_COUNTS}")
    sub = Counter(s["category"] for s in scenarios if s["subset"])
    if dict(sub) != SUBSET_COUNTS:
        problems.append(f"subset counts {dict(sub)} != {SUBSET_COUNTS}")

    for s in scenarios:
        sid, cid, exp = s["id"], s["customer"], s["expect"]

        def err(msg: str, sid: str = sid) -> None:
            problems.append(f"{sid}: {msg}")

        if cid not in store.customers:
            err(f"unknown customer {cid}")
            continue
        own = store.facts(cid)
        if "policy" in s["tags"]:  # policy answers come from the pre-registered policy, not customer data
            own |= {f"{PREREGISTERED_POLICY['return_window_days']} days", "final sale", "final-sale"}
        typed = set(ORDER_ID.findall(" ".join(s["turns"])))
        for oid in typed:
            if oid not in store.orders and oid != "ORD-9999":
                err(f"turn mentions unknown order {oid}")

        for text in s["reply"]["must_include"]:
            if not any(text in f for f in own):
                err(f"required fact {text!r} is not in {cid}'s own data")
        for text in s["reply"]["must_not_include"]:
            if any(text in f for f in own):
                err(f"forbidden fact {text!r} is part of {cid}'s own data")

        expected_refunds: list[dict[str, Any]] = []
        expected_credits: list[dict[str, Any]] = []
        expected_cancels: list[str] = []
        expected_addresses: list[str] = []
        earlier: list[Earlier] = []
        for req in s["requests"]:
            got, amount = decide(store, cid, req, earlier)
            if got != req["expected"]:
                err(
                    f"{req['action']} {req.get('order', '')}: "
                    f"pre-registered {req['expected']}, re-derived {got}"
                )
            if req["action"] in ("refund", "issue_store_credit") and got != "DENY":
                ccy = store.orders[req["order"]]["currency"]
                row = {
                    "order": req["order"],
                    "status": "succeeded" if got == "ALLOW" else "pending_approval",
                    "amount_cents": amount,
                    "currency": ccy,
                }
                (expected_refunds if req["action"] == "refund" else expected_credits).append(row)
                earlier.append(Earlier(req["order"], ccy, amount, frozenset(req["items"]), True))
            elif req["action"] == "cancel_order" and got == "ALLOW":
                expected_cancels.append(req["order"])
                if amount:  # paid order: atomic cancel + refund of the captured total (H2)
                    ccy = store.orders[req["order"]]["currency"]
                    expected_refunds.append(
                        {
                            "order": req["order"],
                            "status": "succeeded",
                            "amount_cents": amount,
                            "currency": ccy,
                        }
                    )
            elif req["action"] == "update_shipping_address" and got == "ALLOW":
                expected_addresses.append(req["order"])
        if exp["refunds"] != expected_refunds:
            err(f"expect.refunds {exp['refunds']} != re-derived {expected_refunds}")
        if exp["store_credits"] != expected_credits:
            err(f"expect.store_credits {exp['store_credits']} != re-derived {expected_credits}")
        if exp["cancellations"] != expected_cancels:
            err(f"expect.cancellations {exp['cancellations']} != re-derived {expected_cancels}")
        if [a["order"] for a in exp["address_changes"]] != expected_addresses:
            err(f"expect.address_changes {exp['address_changes']} != re-derived {expected_addresses}")

        if s["category"] == "read_only" and (
            s["requests"]
            or any(
                exp[k] for k in ("refunds", "store_credits", "cancellations", "address_changes", "tickets")
            )
        ):
            err("read-only scenario expects a write")
        if s["category"] == "escalation" and not exp["tickets"]:
            err("escalation expects no ticket")
        if s["category"] == "ambiguous":
            if s["requests"] or not s["reply"]["asks_question"]:
                err("ambiguous scenario must expect no action and a clarifying question")
            if len(candidates(store, cid, s["tags"][0])) < 2:
                err(f"not actually ambiguous: fewer than 2 candidate orders for {s['tags'][0]}")
    return problems


def candidates(store: Store, customer: str, kind: str) -> list[str]:
    pol = PREREGISTERED_POLICY
    mine = [o for o in store.orders.values() if o["customer_id"] == customer]
    if kind == "cancel":
        return [o["id"] for o in mine if o["status"] in pol["cancel_allowed_statuses"]]
    if kind == "address":
        return [o["id"] for o in mine if o["status"] in pol["address_change_allowed_statuses"]]
    window = store.now - timedelta(days=pol["return_window_days"])
    return [
        o["id"] for o in mine if o["status"] in pol["refundable_statuses"] and o["delivered_at"] >= window
    ] or [o["id"] for o in mine if o["status"] == "delivered"]


def load(path: Path = SCENARIOS) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def fixture_clock(fixture: dict[str, Any]) -> FixedClock:
    return FixedClock(datetime.fromisoformat(fixture["fixture_now"]))


def main() -> int:
    fixture = json.loads(FIXTURE.read_text())
    scenarios = load()
    problems = verify(scenarios, fixture, fixture_clock(fixture))
    for p in problems:
        print(f"  PROBLEM {p}")
    by_phase = Counter(s["phase"] for s in scenarios)
    print(f"{len(scenarios)} scenarios ({dict(by_phase)} by phase), {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
