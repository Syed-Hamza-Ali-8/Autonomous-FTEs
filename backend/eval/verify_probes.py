"""Verify eval/adversarial_tools.jsonl against the fixture, independently of the application code.

Each call's outcome, reason and recomputed amount is RE-DERIVED here from the fixture, the pre-registered
tool schemas below and `verify_scenarios.decide` (the approved policy re-derivation). Calls run in order
on a simulated ledger, so later calls see earlier ones. Concurrent probes are checked as every serial
ordering: each must give exactly one execution. Structural probes (no calls) are only shape-checked here;
they are enforced by Phase 3 tests.

Usage (from backend/):  uv run python -m eval.verify_probes
"""

import json
import sys
from dataclasses import fields, replace
from datetime import datetime, timedelta
from itertools import permutations
from pathlib import Path
from typing import Any

from eval.verify_scenarios import FIXTURE, PREREGISTERED_POLICY, Earlier, Store, decide, fixture_clock

PROBES = Path(__file__).resolve().parent / "adversarial_tools.jsonl"

INT_MAX = 2**31 - 1  # amounts are Postgres integer columns
SUMMARY_MAX = 10_000
ADDRESS_KEYS = {"name", "line1", "city", "postal_code", "country"}
# Pre-registered strict tool schemas: argument name -> accepted Python types. Every argument is
# required (strict mode); None stands for an explicit null where the type allows it.
MONEY = {"order_id": (str,), "items": (list, type(None)), "amount_cents": (int, type(None)), "reason": (str,)}
SCHEMAS: dict[str, dict[str, tuple[type, ...]]] = {
    "request_refund": MONEY,
    "issue_store_credit": MONEY,
    "cancel_order": {"order_id": (str,), "reason": (str,)},
    "update_shipping_address": {"order_id": (str,), "new_address": (dict,)},
    "create_ticket": {"summary": (str,), "category": (str,)},
    "escalate_to_human": {"summary": (str,)},
}
CATEGORIES = {
    "boundary": 20, "double_payment": 6, "cross_customer": 13, "amount_tampering": 16,
    "threshold_evasion": 8, "state_violation": 17, "approval_forging": 6, "idempotency": 7,
    "validation": 1, "structural": 4, "time": 2, "order_status": 5, "address": 5,
}  # fmt: skip
PROTECTIONS = {
    "ownership", "indistinguishable", "policy", "window", "line_rule", "lock", "recompute",
    "validation", "strict_schema", "audit_on_reject", "idempotency", "cancel_refund",
    "no_approval_tools", "executor_boundary", "clock", "order_status", "address_merge",
}  # fmt: skip

# Reference mutants: each removes one protection from this model, so the mutation table in
# ADVERSARIAL_PREREGISTRATION.md is derived, not asserted. Structural and audit mutants (M10-M12, M15) act
# on code shape or audit rows, which this model does not simulate; their probes are listed by hand.
MUTANTS = {
    "M1": "ownership clause removed: any existing order is loaded",
    "M2": "policy call removed: every validated, owned request is ALLOW",
    "M3": "idempotency check removed",
    "M3b": "a DENY is recorded under the idempotency key (cached instead of re-evaluated)",
    "M4": "recompute removed: the model's amount is trusted",
    "M5": "rolling window removed (count and cap)",
    "M6": "H1 line rule removed (the captured remainder check stays)",
    "M7": "order row lock removed: concurrent calls both see the pre-call state",
    "M8": "unknown arguments ignored instead of rejected",
    "M8b": "lax types: numeric strings, integral floats and booleans coerced",
    "M8c": "amount_cents typed as a number instead of an integer",
    "M9": "gateway validation bounds removed (amount range, summary length, address given)",
    "M13": "system clock instead of the injected clock",
    "M14": "paid-order cancel no longer refunds atomically",
    "M16": "a foreign order answers differently from a missing one",
    "M17": "item line-match dropped: requested items that match no line are ignored",
    "M18": "repeated items not collapsed: each listed item adds its line again",
    "M19": "order status not updated after a succeeded refund",
    "M23": "address change replaces instead of merging (fields not given are lost)",
    "M24": "recipient-name and country change flags removed",
}


class _PerItemStore(Store):
    """M18: lines are looked up once per requested name, so a repeated name repeats its line."""

    def lines(self, order_id: str, names: list[str]) -> list[dict[str, Any]]:
        return [i for n in names for i in self.items[order_id] if self.products[i["product_id"]]["name"] == n]


def schema_ok(tool: str, args: dict[str, Any], m: frozenset[str] = frozenset()) -> bool:
    schema = SCHEMAS[tool]
    if set(args) - set(schema) and "M8" not in m:
        return False
    for k, types in schema.items():
        v = args.get(k)
        if "M8b" in m and k == "amount_cents" and isinstance(v, (str, float, bool)):  # the stock SDK's model
            try:
                v = int(v) if isinstance(v, (str, bool)) or float(v).is_integer() else v
            except ValueError:
                pass
            args[k] = v
        if "M8c" in m and k == "amount_cents" and isinstance(v, float):
            continue
        if isinstance(v, bool) or not isinstance(v, types):  # bool is an int subclass: never an amount
            return False
    if "new_address" in args and (
        not set(args["new_address"]) <= ADDRESS_KEYS
        or any(v is not None and not isinstance(v, str) for v in args["new_address"].values())
    ):  # partial addresses are merged (I12); unknown keys and non-strings are rejected
        return False
    return True


def with_nulls(tool: str, args: dict[str, Any]) -> dict[str, Any]:
    """A probe may omit a nullable argument; the strict schema sends it as null."""
    return {k: args.get(k) for k in SCHEMAS[tool]} | {k: v for k, v in args.items() if k not in SCHEMAS[tool]}


class Ledger:
    """What the gateway would have written so far in one probe."""

    def __init__(self) -> None:
        self.earlier: list[Earlier] = []
        self.rows: dict[str, list[dict[str, Any]]] = {
            "refunds": [], "store_credits": [], "cancellations": [], "address_changes": [], "tickets": [],
        }  # fmt: skip
        self.flags: list[str] = []
        self.status: dict[str, str] = {}
        self.keys: dict[tuple[Any, ...], tuple[str, str | None]] = {}


def reason_for(
    store: Store, customer: str, order: dict[str, Any], req: dict[str, Any], led: Ledger, m: frozenset[str]
) -> str:
    """The machine-readable reason, checked in the pre-registered order."""
    pol = PREREGISTERED_POLICY
    kind = "refund" if req["action"] == "refund" else "store_credit"
    if order["status"] not in pol["refundable_statuses"]:
        return "status_not_refundable"
    lines = store.lines(order["id"], req["items"])
    if order["delivered_at"] < store.now - timedelta(days=pol["return_window_days"]):
        return "outside_return_window"
    if any(store.products[i["product_id"]]["final_sale"] for i in lines):
        return "final_sale"
    if any(store.products[i["product_id"]]["digital"] and i["downloaded_at"] for i in lines):
        return "digital_downloaded"
    if {n for e in led.earlier if e.order == order["id"] for n in e.lines} & set(
        req["items"]
    ) and "M6" not in m:
        return "line_already_compensated"
    amount = min(
        sum(i["unit_price_cents"] * i["quantity"] for i in lines), req.get("amount_cents") or INT_MAX
    )
    refunded = sum(
        r["amount_cents"]
        for r in store.refunds
        if r["order_id"] == order["id"] and r["status"] == "succeeded"
    )
    if amount > store.payments.get(order["id"], 0) - refunded - sum(
        e.amount for e in led.earlier if e.order == order["id"]
    ):
        return "exceeds_refundable_remainder"
    if amount > pol[kind]["approval_max"][order["currency"]]:
        return "above_approval_max"
    if amount > pol[kind]["auto_max"][order["currency"]]:
        return "auto_max"
    since = store.now - timedelta(days=pol["rolling_window_days"])
    prior = [
        r for r in store.refunds
        if store.orders[r["order_id"]]["customer_id"] == customer
        and r["status"] in ("succeeded", "pending_approval") and r["created_at"] >= since
    ]  # fmt: skip
    if (
        len(prior) + sum(e.counts_toward_window for e in led.earlier)
        >= pol["max_refunds_in_window_before_approval"]
    ):
        return "window_count"
    return "window_cap"


def derive(
    store: Store, customer: str, call: dict[str, Any], led: Ledger, m: frozenset[str] = frozenset()
) -> tuple[str, str | None, dict[str, Any] | None]:
    """(outcome, reason, row written or None) for one call against the ledger so far."""
    tool, raw = call["tool"], call["args"]
    args = with_nulls(tool, raw)
    if not schema_ok(tool, args, m):
        return "SCHEMA_REJECTED", None, None
    args = {k: v for k, v in args.items() if k in SCHEMAS[tool]}
    # The key includes the customer and only effects are recorded, so looking it up here gives the same
    # outcomes as the gateway's position (after ownership and recompute, before policy; P5).
    key = (customer, tool, json.dumps(args, sort_keys=True), call.get("turn", 1))
    if (
        key in led.keys and "M3" not in m
    ):  # idempotency: a repeat in the same turn returns the original result
        return "REPLAY", led.keys[key][1], None
    out = _derive(store, customer, tool, args, led, m)
    if out[0] in ("ALLOW", "NEEDS_APPROVAL") or ("M3b" in m and out[0] == "DENY"):
        led.keys[key] = (out[0], out[1])
    return out


def _derive(
    store: Store, customer: str, tool: str, args: dict[str, Any], led: Ledger, m: frozenset[str]
) -> tuple[str, str | None, dict[str, Any] | None]:
    if tool in ("create_ticket", "escalate_to_human"):
        if len(args["summary"]) > SUMMARY_MAX and "M9" not in m:
            return "INVALID", "summary_too_long", None
        row: dict[str, Any] = {"kind": "escalation" if tool == "escalate_to_human" else "ticket"}
        led.rows["tickets"].append(row)
        return "ALLOW", None, row
    if (
        tool == "update_shipping_address"
        and all(v is None for v in args["new_address"].values())
        and "M9" not in m
    ):
        return "INVALID", "address_required", None
    if tool in ("request_refund", "issue_store_credit"):
        amt = args["amount_cents"]
        if amt is not None and not 1 <= amt <= INT_MAX and "M9" not in m:
            return "INVALID", "invalid_amount", None
        if not args["items"]:
            return "INVALID", "items_required", None
    order = store.orders.get(args["order_id"].strip().upper())  # normalised like the read tools
    if order is None:
        return "NOT_FOUND", "not_found", None
    if order["customer_id"] != customer and "M1" not in m:
        if "M16" in m:
            return "FORBIDDEN", "forbidden", None
        return "NOT_FOUND", "not_found", None
    status = led.status.get(order["id"], order["status"])
    ccy = order["currency"]
    if tool == "cancel_order":
        if status not in PREREGISTERED_POLICY["cancel_allowed_statuses"] and "M2" not in m:
            return "DENY", "status_not_cancellable", None
        refund = store.payments.get(order["id"], 0) if status == "paid" and "M14" not in m else 0
        led.status[order["id"]] = "cancelled"
        led.rows["cancellations"].append(order["id"])
        if refund:
            led.rows["refunds"].append(
                {"order": order["id"], "status": "succeeded", "amount_cents": refund, "currency": ccy}
            )
            if refund > PREREGISTERED_POLICY["cancellation"]["audit_flag_above"][ccy]:
                led.flags.append("high_value_cancellation")
        return "ALLOW", None, None
    if tool == "update_shipping_address":
        current = order["shipping_address"]
        given = args["new_address"]
        # I12: merge, not replace (M23 replaces: a field not given becomes empty)
        merged = {
            k: given[k] if given.get(k) is not None else ("" if "M23" in m else str(current.get(k) or ""))
            for k in sorted(ADDRESS_KEYS)
        }
        if any(not v.strip() for v in merged.values()):
            return "INVALID", "address_incomplete", None
        if status not in PREREGISTERED_POLICY["address_change_allowed_statuses"] and "M2" not in m:
            return "DENY", "status_not_addressable", None
        if "M24" not in m:
            for k, flag in (("name", "recipient_name_changed"), ("country", "country_changed")):
                if merged[k] != (current.get(k) or ""):
                    led.flags.append(flag)
        row = {"order": order["id"], "line1_contains": merged["line1"]}
        led.rows["address_changes"].append(row)
        return "ALLOW", None, row
    # Decisions see the order's status as this probe has left it (refunds move it; DECISIONS I10).
    store = replace(
        store,
        orders={**store.orders, **{o: {**store.orders[o], "status": st} for o, st in led.status.items()}},
    )
    order = store.orders[order["id"]]
    if "M18" in m:
        store = _PerItemStore(**{f.name: getattr(store, f.name) for f in fields(store)})
    items = args["items"] if "M18" in m else list(dict.fromkeys(args["items"]))  # a repeat counts once
    if "M17" in m:
        items = [n for n in items if store.lines(order["id"], [n])]
    elif len(store.lines(order["id"], list(dict.fromkeys(items)))) != len(set(items)):
        return "DENY", "item_not_in_order", None
    req = {"action": "refund" if tool == "request_refund" else "store_credit", "order": order["id"],
           "items": items, "amount_cents": args["amount_cents"]}  # fmt: skip
    decision, amount = _decide(store, customer, req, led, m)
    reason = None if decision == "ALLOW" else reason_for(store, customer, order, req, led, m)
    if decision == "DENY":
        return "DENY", reason, None
    led.earlier.append(Earlier(order["id"], ccy, amount, frozenset(items), True))
    status = "succeeded" if decision == "ALLOW" else "pending_approval"
    row = {"order": order["id"], "status": status, "amount_cents": amount, "currency": ccy}
    led.rows["refunds" if tool == "request_refund" else "store_credits"].append(row)
    if tool == "request_refund" and decision == "ALLOW" and "M19" not in m:
        refunded = sum(
            r["amount_cents"]
            for r in store.refunds
            if r["order_id"] == order["id"] and r["status"] == "succeeded"
        ) + sum(
            r["amount_cents"]
            for r in led.rows["refunds"]
            if r["order"] == order["id"] and r["status"] == "succeeded"
        )
        full = refunded >= store.payments.get(order["id"], 0)
        led.status[order["id"]] = "refunded" if full else "partially_refunded"
    return decision, reason, row


def _decide(
    store: Store, customer: str, req: dict[str, Any], led: Ledger, m: frozenset[str]
) -> tuple[str, int]:
    """`decide`, with the protections a mutant removes taken out of its inputs."""
    if "M5" in m:
        store = replace(store, refunds=[r for r in store.refunds if r["order_id"] == req["order"]])
    earlier = [
        Earlier(
            e.order,
            e.currency,
            e.amount,
            frozenset() if "M6" in m else e.lines,
            "M5" not in m and e.counts_toward_window,
        )
        for e in led.earlier
    ]
    if "M2" in m:
        return "ALLOW", decide(store, customer, req, earlier)[1]
    line_value = sum(i["unit_price_cents"] * i["quantity"] for i in store.lines(req["order"], req["items"]))
    if "M4" in m and req["amount_cents"] is not None and req["amount_cents"] > line_value:
        # trusted: no recompute and no remainder, so the thresholds see the model's figure
        pol, kind = PREREGISTERED_POLICY, "refund" if req["action"] == "refund" else "store_credit"
        ccy, amt = store.orders[req["order"]]["currency"], req["amount_cents"]
        decision, _ = decide(store, customer, {**req, "amount_cents": None}, earlier)
        if decision == "DENY" or amt > pol[kind]["approval_max"][ccy]:
            return "DENY", amt
        return (
            "NEEDS_APPROVAL" if decision == "NEEDS_APPROVAL" or amt > pol[kind]["auto_max"][ccy] else "ALLOW"
        ), amt
    return decide(store, customer, req, earlier)


def db_of(led: Ledger, store: Store) -> dict[str, Any]:
    out: dict[str, Any] = {k: v for k, v in led.rows.items()}
    out["order_statuses"] = [
        {"order": o, "status": st} for o, st in sorted(led.status.items()) if st != store.orders[o]["status"]
    ]
    if led.flags:
        out["audit_flags"] = led.flags
    return out


def expected_db(probe: dict[str, Any]) -> list[dict[str, Any]]:
    e = dict(probe["expect_db"])
    alts = e.pop("one_of", None)
    base = {k: v for k, v in e.items() if v}
    return [base | {k: v for k, v in a.items() if v} for a in alts] if alts else [base]


def check(store: Store, probe: dict[str, Any], m: frozenset[str] = frozenset()) -> list[str]:
    pid, calls = probe["id"], probe["calls"]
    errs: list[str] = []
    if not set(probe["protections"]) <= PROTECTIONS:
        errs.append(f"{pid}: unknown protection {set(probe['protections']) - PROTECTIONS}")
    if probe["category"] == "structural" or not calls:
        if calls or probe["audit_rows"] != 0:
            errs.append(f"{pid}: a structural probe has no calls and no audit rows")
        return errs
    if probe["audit_rows"] != len(calls):
        errs.append(f"{pid}: one audit row per call expected")
    if "M13" in m and probe.get("system_date"):  # the mutant reads the moved system date
        store = replace(store, now=datetime.fromisoformat(probe["system_date"]))
    wanted = expected_db(probe)
    orders = list(permutations(range(len(calls)))) if probe["concurrent"] else [tuple(range(len(calls)))]
    for order in orders:
        led = Ledger()
        if probe["concurrent"] and "M7" in m:  # no lock: each call reads the pre-call state; keys stay unique
            got = []
            for i in order:
                solo = Ledger()
                solo.keys = led.keys
                got.append(derive(store, probe["as_customer"], calls[i], solo, m))
                for k, v in solo.rows.items():
                    led.rows[k] += v
                led.flags += solo.flags
                led.status.update(solo.status)
        else:
            got = [derive(store, probe["as_customer"], calls[i], led, m) for i in order]
        for i, (outcome, reason, _) in zip(order, got, strict=True):
            exp = calls[i]
            ok = {
                "ONE_OF": outcome in ("ALLOW", "NEEDS_APPROVAL", "DENY"),
                "ALLOW_OR_REPLAY": outcome in ("ALLOW", "REPLAY"),
            }.get(exp["outcome"], outcome == exp["outcome"])
            if not ok or (exp.get("reason") and reason != exp["reason"]):
                errs.append(
                    f"{pid} call {i} (order {order}): expected {exp['outcome']}/{exp.get('reason')},"
                    f" derived {outcome}/{reason}"
                )
        if probe["concurrent"]:
            executed = sum(o in ("ALLOW", "NEEDS_APPROVAL") for o, _, _ in got)
            if executed != 1:
                errs.append(f"{pid} (order {order}): {executed} executions, expected exactly 1")
            if any(
                o == "DENY"
                and r not in ("line_already_compensated", "status_not_cancellable", "status_not_refundable")
                for o, r, _ in got
            ):
                errs.append(
                    f"{pid} (order {order}): the losing call must be refused by the line or status rule"
                )
        db = {k: v for k, v in db_of(led, store).items() if v}
        if db not in wanted:
            errs.append(f"{pid} (order {order}): expected DB {wanted}, derived {db}")
    if probe["compare_response_with"] and probe["calls"][0]["outcome"] != "NOT_FOUND":
        errs.append(f"{pid}: byte-identical comparison only applies to NOT_FOUND")
    return errs


def verify(
    probes: list[dict[str, Any]], fixture: dict[str, Any], m: frozenset[str] = frozenset()
) -> list[str]:
    store = Store.load(fixture, fixture_clock(fixture))
    problems: list[str] = []
    ids = [p["id"] for p in probes]
    if len(ids) != len(set(ids)):
        problems.append("duplicate probe ids")
    counts: dict[str, int] = {}
    for p in probes:
        counts[p["category"]] = counts.get(p["category"], 0) + 1
    if counts != CATEGORIES:
        problems.append(f"category counts {counts} != pre-registered {CATEGORIES}")
    by_id = {p["id"]: p for p in probes}
    for p in probes:
        if (other := p["compare_response_with"]) and by_id.get(other, {}).get("calls", [{}])[0].get(
            "outcome"
        ) != "NOT_FOUND":
            problems.append(f"{p['id']}: compares with {other}, which is not a NOT_FOUND probe")
        if other and m:  # byte-identical: both probes must derive the same outcome under this build
            mine, theirs = (
                derive(store, by_id[x]["as_customer"], by_id[x]["calls"][0], Ledger(), m)[0]
                for x in (p["id"], other)
            )
            if mine != theirs:
                problems.append(f"{p['id']}: answers {mine}, {other} answers {theirs}")
        problems += check(store, p, m)
    return problems


def load(path: Path = PROBES) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def killed_by(probes: list[dict[str, Any]], fixture: dict[str, Any], mutant: str) -> list[str]:
    """Probe ids that fail when `mutant` removes its protection from the reference model."""
    failed = {msg.split(":")[0].split(" ")[0] for msg in verify(probes, fixture, frozenset({mutant}))}
    return [p["id"] for p in probes if p["id"] in failed]


def main() -> int:
    fixture = json.loads(FIXTURE.read_text())
    probes = load()
    problems = verify(probes, fixture)
    for msg in problems:
        print("PROBLEM", msg)
    print(f"{len(probes)} probes, {len(problems)} problems")
    if "--mutants" in sys.argv:
        for mid, desc in MUTANTS.items():
            ids = killed_by(probes, fixture, mid)
            print(f"{mid:4} {len(ids):3} {desc}: {' '.join(ids) or 'NONE'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
