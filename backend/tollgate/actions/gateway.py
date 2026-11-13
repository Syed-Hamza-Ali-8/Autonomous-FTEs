"""The Action Gateway: every write passes here, no exceptions (spec 6.2; invariant 5; DECISIONS I1-I8).

    validate -> ownership -> recompute -> idempotency -> policy -> route -> audit

- VALIDATE: the raw tool arguments, strictly (unknown fields rejected, no type coercion), because the SDK's
  own argument model is lax (docs/sdk_surface.md). Then bounds. Rejections are audited, values redacted.
- OWNERSHIP: the order is loaded `WHERE id = $1 AND customer_id = $2 ... FOR UPDATE`; the row lock makes
  concurrent submissions on one order run one at a time. Not yours and does not exist give one result.
- RECOMPUTE: amounts come from the order's lines; the model's amount is only a ceiling (B4).
- IDEMPOTENCY: after ownership, before policy. Only effects record a key (I5).
- POLICY: policy/engine.py on facts read here with owner-filtered SQL; time from the injected clock (G1).
- FRAUD SIGNAL (J2): in a turn whose customer text was flagged, an order- or money-tier ALLOW becomes
  NEEDS_APPROVAL (`fraud_signal`). Tighten only: a NEEDS_APPROVAL or DENY stands. The contact tier is exempt.
- ROUTE: ALLOW -> executors; NEEDS_APPROVAL -> approvals.queue (insert-only); DENY -> nothing. Deciding a
  queued request is approvals/service.py's alone, and nothing a tool imports reaches it (J7, af06).
- AUDIT: exactly one app.audit_log row per submission, in the same transaction as its effect.

Reason codes and their order are pre-registered in eval/ADVERSARIAL_PREREGISTRATION.md section 3. Each
protection is one named function or constant below, so the mutation checks (pre-registration section 6)
can remove exactly that protection and nothing else.
"""

import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from tollgate.actions import cards, executors, hints, idempotency
from tollgate.actions.records import MoneyAction, Request
from tollgate.approvals import expiry, queue
from tollgate.db import Conn
from tollgate.domain.money import with_display
from tollgate.errors import ActionFailedError
from tollgate.policy import engine
from tollgate.tools.context import TurnContext

log = logging.getLogger(__name__)

MAX_AMOUNT_CENTS = 2**31 - 1  # amounts are Postgres integer columns
MAX_SUMMARY_CHARS = 10_000
MAX_AUDITED_NAMES = 50

# What the model sees of an outcome that didn't complete: a status and ONE customer-safe sentence
# (DECISIONS I15). No reason codes, rule names, limits, caps or counts are ever in a tool result; they go
# to the audit log only. "Not yours" and "does not exist" are one constant result, echoing nothing from
# the request (I7).
NOT_FOUND: dict[str, Any] = {"status": "not_found", "customer_message_hint": hints.NOT_FOUND}
REJECTED: dict[str, Any] = {"status": "rejected", "customer_message_hint": hints.REJECTED}
# Version of the model-visible result format; part of the tool-schema version, so a run never mixes formats.
RESULT_FORMAT = "hints-v2"


def _hinted(status: str, reason: str, order_status: str | None = None) -> dict[str, Any]:
    return {"status": status, "customer_message_hint": hints.hint(reason, order_status)}


# OWNERSHIP, with the row lock that serialises every write on one order (invariants 3 and 9).
OWNED_ORDER_SQL = (
    "SELECT id, status, currency, delivered_at, shipping_address FROM app.orders"
    " WHERE id = $1 AND customer_id = $2 FOR UPDATE"
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class MoneyArgs(_Strict):
    order_id: str
    items: list[str] | None = None  # required by validation (I2); null reaches it as items_required
    amount_cents: int | None = None  # a ceiling, never trusted (B4)
    reason: str


class CancelArgs(_Strict):
    order_id: str
    reason: str


class NewAddress(_Strict):
    """Only the parts that change: fields left out keep their current values (owner, DECISIONS I12)."""

    name: str | None = None
    line1: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None


ADDRESS_FIELDS = ("name", "line1", "city", "postal_code", "country")
# Audited with a distinct marker whenever an address change alters them (I12). Deferred candidate: a
# recipient-name change could need staff approval; revisit when rules.yaml is tuned.
ADDRESS_FLAGS = {"name": "recipient_name_changed", "country": "country_changed"}


class AddressArgs(_Strict):
    order_id: str
    new_address: NewAddress


class TicketArgs(_Strict):
    summary: str
    category: str


class EscalateArgs(_Strict):
    summary: str


ARGS: dict[str, type[_Strict]] = {
    "request_refund": MoneyArgs,
    "issue_store_credit": MoneyArgs,
    "cancel_order": CancelArgs,
    "update_shipping_address": AddressArgs,
    "create_ticket": TicketArgs,
    "escalate_to_human": EscalateArgs,
}


@dataclass
class Outcome:
    result: dict[str, Any]
    outcome: (
        str  # executed | queued | denied | not_found | invalid | needs_more_information | replayed | error
    )
    decision: str | None = None
    reasons: list[str] = field(default_factory=list)
    target: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class _ConcurrentDuplicate(Exception):  # control flow only; never escapes this module
    def __init__(self, key: str, target: str | None) -> None:
        self.key = key
        self.target = target


async def submit(
    ctx: TurnContext, action: str, raw_arguments: str, *, sdk_rejected: bool = False
) -> dict[str, Any]:
    """Run one write. `raw_arguments` is the model's JSON exactly as sent; `sdk_rejected` marks a call the
    SDK's validation already refused (it is audited and rejected even if the strict model would pass it)."""
    try:
        args = _parse(action, raw_arguments)
    except ValidationError as exc:
        errors = [(e["loc"], e["type"]) for e in exc.errors(include_input=False, include_url=False)]
        await _audit_rejection(ctx, action, raw_arguments, errors)
        return dict(REJECTED)
    if sdk_rejected:
        await _audit_rejection(ctx, action, raw_arguments, [((), "sdk_rejected")])
        return dict(REJECTED)

    if (invalid := _invalid(args)) is not None:
        out = Outcome(_hinted("invalid", invalid), "invalid", reasons=[invalid], target=_target(args))
        async with ctx.pool.acquire() as conn:
            await _audit(conn, ctx, action, out)
        return out.result

    try:
        async with ctx.pool.acquire() as conn, conn.transaction():
            out = await _run(conn, ctx, action, args)
            audit_id = await _audit(conn, ctx, action, out)
    except _ConcurrentDuplicate as dup:
        # Another submission with the same key committed first; ours was rolled back. Answer as a repeat.
        async with ctx.pool.acquire() as conn:
            original = await idempotency.lookup(conn, dup.key, ctx.customer.customer_id)
            if original is None:
                raise ActionFailedError("idempotency conflict without a recorded result") from None
            out = _replayed(original, dup.target)
            audit_id = await _audit(conn, ctx, action, out)
    except Exception as exc:
        log.exception("action %s failed", action)
        async with ctx.pool.acquire() as conn:
            failed = Outcome(
                {"status": "error"}, "error", target=_target(args), details={"error": type(exc).__name__}
            )
            await _audit(conn, ctx, action, failed)
        raise ActionFailedError(f"{action} failed: {type(exc).__name__}") from exc
    # Every submission is audited, so a refused one has a reference too: its audit row (never in the result).
    audit_ref = f"AUD-{audit_id:06d}" if audit_id is not None else None
    if (
        card := cards.card_for(action, out.outcome, out.result, out.target, _now(ctx), audit_ref)
    ) is not None:
        ctx.actions.append(card)
    return out.result


# -- validation -------------------------------------------------------------------------------------------


def _parse(action: str, raw_arguments: str) -> BaseModel:
    """Strict: unknown fields rejected, no coercion of strings, floats or booleans into integers."""
    return ARGS[action].model_validate_json(raw_arguments)


def _invalid(args: BaseModel) -> str | None:
    if isinstance(args, MoneyArgs):
        if args.amount_cents is not None and not 1 <= args.amount_cents <= MAX_AMOUNT_CENTS:
            return "invalid_amount"
        if not args.items:
            return "items_required"
    if isinstance(args, TicketArgs | EscalateArgs) and len(args.summary) > MAX_SUMMARY_CHARS:
        return "summary_too_long"
    if isinstance(args, AddressArgs) and all(getattr(args.new_address, f) is None for f in ADDRESS_FIELDS):
        return "address_required"
    return None


def _target(args: BaseModel) -> str | None:
    order_id = getattr(args, "order_id", None)
    return order_id.strip().upper() if isinstance(order_id, str) else None


def _now(ctx: TurnContext) -> datetime:
    return ctx.clock.now()  # the injected clock only (G1); never the system clock


# -- pipeline ---------------------------------------------------------------------------------------------


async def _run(conn: Conn, ctx: TurnContext, action: str, args: BaseModel) -> Outcome:
    if isinstance(args, TicketArgs | EscalateArgs):
        return await _ticket(conn, ctx, action, args)
    order_id = _target(args)
    order = await _load_order(conn, order_id, ctx.customer.customer_id)
    if order is None:
        return Outcome(dict(NOT_FOUND), "not_found", reasons=["not_found"], target=order_id)
    if isinstance(args, MoneyArgs):
        return await _money(conn, ctx, action, args, order)
    if isinstance(args, CancelArgs):
        return await _cancel(conn, ctx, args, order)
    if isinstance(args, AddressArgs):
        return await _address(conn, ctx, args, order)
    raise TypeError(f"no pipeline for {type(args).__name__}")


async def _load_order(conn: Conn, order_id: str | None, customer_id: str) -> Any:
    return await conn.fetchrow(OWNED_ORDER_SQL, order_id, customer_id)


def _request(
    ctx: TurnContext, action: str, order_id: str | None, decision: Literal["ALLOW", "NEEDS_APPROVAL"]
) -> Request:
    return Request(
        customer_id=ctx.customer.customer_id,
        conversation_id=ctx.conversation_id,
        turn_id=ctx.turn_id,
        action=action,
        order_id=order_id,
        decision=decision,
        now=_now(ctx),
    )


def _dedupe(names: list[str]) -> list[str]:
    return list(dict.fromkeys(names))  # a repeated item counts once


def _missing_items(lines: Sequence[Any], names: list[str]) -> bool:
    return {r["name"] for r in lines} != set(names)


def _line_value(lines: Sequence[Any], names: list[str]) -> int:
    return sum(r["quantity"] * r["unit_price_cents"] for r in lines)


def _amount(line_value: int, ceiling: int | None) -> int:
    return (
        line_value if ceiling is None else min(line_value, ceiling)
    )  # B4: the model's figure only lowers it


async def _fraud_flag(conn: Conn, ctx: TurnContext) -> bool:
    """Whether this turn's customer text was flagged (set by the runner from that text alone; I11). Its own
    seam for mutations M25 (check removed) and M28 (the flag derived from other text the turn has seen)."""
    return ctx.fraud_signal


def _apply_fraud_signal(verdict: engine.Verdict, flagged: bool) -> engine.Verdict:
    """Tighten only (J2): ALLOW -> NEEDS_APPROVAL. A NEEDS_APPROVAL gains the tag for staff; a DENY stands.
    Its own seam for mutation M26 (the flag applied to every decision)."""
    if not flagged or verdict.decision == "DENY":
        return verdict
    return engine.Verdict("NEEDS_APPROVAL", (*verdict.reasons, "fraud_signal"))


# Derived approval expiry (J8): each reader of pending state takes its cutoff from its own seam, so the
# mutation checks (M41-M43) can remove the predicate from exactly one reader. Rows created after it are live.
def _remainder_live_after(now: datetime) -> datetime:
    return expiry.live_after(now)


def _lines_live_after(now: datetime) -> datetime:
    return expiry.live_after(now)


def _window_live_after(now: datetime) -> datetime:
    return expiry.live_after(now)


async def _order_facts(
    conn: Conn,
    order_id: str,
    customer_id: str,
    line_ids: list[int],
    now: datetime,
    exclude_request: str | None = None,
) -> tuple[int, bool]:
    """(refundable remainder, whether a live pending or a succeeded refund/credit covers one of the lines).

    An expired pending request holds nothing (J8). `exclude_request` leaves one request's own rows out: the
    approval re-check (B6) asks whether a queued request still fits next to everything ELSE on the order."""
    row = await conn.fetchrow(
        """
        SELECT (SELECT coalesce(sum(p.amount_cents), 0) FROM app.payments p WHERE p.order_id = o.id)
             - (SELECT coalesce(sum(r.amount_cents), 0) FROM app.refunds r
                 WHERE r.order_id = o.id
                   AND (r.status = 'succeeded' OR (r.status = 'pending_approval' AND r.created_at > $5))
                   AND ($4::text IS NULL OR r.action_request_id IS DISTINCT FROM $4))
             - (SELECT coalesce(sum(c.amount_cents), 0) FROM app.store_credits c
                 WHERE c.order_id = o.id
                   AND (c.status = 'succeeded' OR (c.status = 'pending_approval' AND c.created_at > $5))
                   AND ($4::text IS NULL OR c.action_request_id IS DISTINCT FROM $4)) AS remainder,
               EXISTS (SELECT 1 FROM app.action_requests a
                        WHERE a.order_id = o.id AND a.customer_id = o.customer_id
                          AND a.action IN ('request_refund', 'issue_store_credit')
                          AND (a.status IN ('executed', 'approved')
                               OR (a.status = 'pending_approval' AND a.created_at > $6))
                          AND a.order_item_ids && $3::bigint[]
                          AND ($4::text IS NULL OR a.id IS DISTINCT FROM $4)) AS compensated
          FROM app.orders o
         WHERE o.id = $1 AND o.customer_id = $2
        """,
        order_id,
        customer_id,
        line_ids,
        exclude_request,
        _remainder_live_after(now),
        _lines_live_after(now),
    )
    if row is None:  # the order is locked and owned, so the row exists
        raise ActionFailedError("policy facts missing for a locked order")
    return int(row["remainder"]), bool(row["compensated"])


async def _window(
    conn: Conn,
    customer_id: str,
    since: datetime,
    currency: str,
    include_cancellations: bool,
    now: datetime,
    exclude_request: str | None = None,
) -> tuple[int, int]:
    """(refunds + credits in the rolling window, their total in `currency`); live pending ones count (A7),
    expired ones don't (J8). `exclude_request` leaves one request's own row out (B6)."""
    row = await conn.fetchrow(
        """
        SELECT count(*) AS n, coalesce(sum(w.amount_cents) FILTER (WHERE w.currency = $3), 0) AS total
          FROM (SELECT r.amount_cents, r.currency
                  FROM app.refunds r
                  JOIN app.orders o ON o.id = r.order_id
                  LEFT JOIN app.action_requests a ON a.id = r.action_request_id
                 WHERE o.customer_id = $1
                   AND (r.status = 'succeeded' OR (r.status = 'pending_approval' AND r.created_at > $6))
                   AND r.created_at >= $2 AND ($4 OR a.action IS DISTINCT FROM 'cancel_order')
                   AND ($5::text IS NULL OR r.action_request_id IS DISTINCT FROM $5)
                UNION ALL
                SELECT c.amount_cents, c.currency
                  FROM app.store_credits c
                 WHERE c.customer_id = $1
                   AND (c.status = 'succeeded' OR (c.status = 'pending_approval' AND c.created_at > $6))
                   AND c.created_at >= $2 AND ($5::text IS NULL OR c.action_request_id IS DISTINCT FROM $5)) w
        """,
        customer_id,
        since,
        currency,
        include_cancellations,
        exclude_request,
        _window_live_after(now),
    )
    if row is None:
        raise ActionFailedError("window query returned no row")
    return int(row["n"]), int(row["total"])


async def _money(conn: Conn, ctx: TurnContext, action: str, args: MoneyArgs, order: Any) -> Outcome:
    kind: MoneyAction = "request_refund" if action == "request_refund" else "issue_store_credit"
    customer, order_id, ccy = ctx.customer.customer_id, order["id"], order["currency"]
    names = _dedupe(args.items or [])
    # RECOMPUTE from the order's own lines (owner-filtered through the order join).
    lines = await conn.fetch(
        """
        SELECT i.id, p.name, i.quantity, i.unit_price_cents, p.final_sale, p.digital, i.downloaded_at
          FROM app.order_items i
          JOIN app.orders o ON o.id = i.order_id
          JOIN app.products p ON p.id = i.product_id
         WHERE i.order_id = $1 AND o.customer_id = $2 AND p.name = ANY($3::text[])
         ORDER BY i.id
        """,
        order_id,
        customer,
        names,
    )
    if _missing_items(lines, names):
        return _denied(["item_not_in_order"], order_id, {"items": names}, order["status"])
    line_ids = [r["id"] for r in lines]
    value = _line_value(lines, names)
    amount = _amount(value, args.amount_cents)
    details = {"items": names, "amount_cents": amount, "currency": ccy, "line_value_cents": value}

    # IDEMPOTENCY
    key = idempotency.key(
        customer, action, order_id, {"items": sorted(names), "amount_cents": amount}, ctx.turn_id
    )
    if (original := await idempotency.lookup(conn, key, customer)) is not None:
        return _replayed(original, order_id)

    # POLICY
    rules, now = engine.load_rules(), _now(ctx)
    remainder, compensated = await _order_facts(conn, order_id, customer, line_ids, now)
    count, total = await _window(
        conn, customer, engine.window_start(rules, now), ccy, rules.cancellation.counts_toward_window, now
    )
    facts = engine.MoneyFacts(
        kind="refund" if kind == "request_refund" else "store_credit",
        currency=ccy,
        amount_cents=amount,
        order_status=order["status"],
        delivered_at=order["delivered_at"],
        any_final_sale=any(r["final_sale"] for r in lines),
        any_digital_downloaded=any(r["digital"] and r["downloaded_at"] is not None for r in lines),
        lines_already_compensated=compensated,
        refundable_remainder_cents=remainder,
        window_count=count,
        window_total_cents=total,
    )
    verdict = _apply_fraud_signal(engine.evaluate_money(rules, facts, now), await _fraud_flag(conn, ctx))
    if verdict.decision == "DENY":
        return await _settle(
            conn, ctx, key, _denied(list(verdict.reasons), order_id, details, order["status"])
        )

    # ROUTE
    req = replace(
        _request(ctx, action, order_id, verdict.decision),
        order_item_ids=tuple(line_ids),
        amount_cents=amount,
        currency=ccy,
        args={"items": names, "amount_ceiling_cents": args.amount_cents},
        reasons=verdict.reasons,
    )
    base = {"action": action, "order_id": order_id}
    if verdict.decision == "ALLOW":
        refs = await executors.run_money(conn, kind, req, args.reason)
        result = {"status": "done", **base, **refs, "amount_cents": amount, "currency": ccy}
        out = Outcome(with_display(result), "executed", "ALLOW", [], order_id, details | refs)
    else:
        refs = await queue.create(conn, kind, req, args.reason)
        reasons = list(verdict.reasons)
        result = {"status": "pending_approval", **base, **refs, "amount_cents": amount, "currency": ccy}
        out = Outcome(
            with_display(result | {"customer_message_hint": hints.PENDING}),
            "queued",
            "NEEDS_APPROVAL",
            reasons,
            order_id,
            details | refs,
        )
    return await _settle(conn, ctx, key, out)


async def _cancel_refund(conn: Conn, order: Any, customer_id: str, rules: engine.Rules) -> int:
    """A paid order's cancel refunds exactly its captured total (H2), recomputed here, never the model's."""
    if order["status"] != "paid" or not rules.cancellation.refund_captured_total:
        return 0
    captured: int = await conn.fetchval(
        "SELECT coalesce(sum(p.amount_cents), 0) FROM app.payments p"
        " JOIN app.orders o ON o.id = p.order_id WHERE p.order_id = $1 AND o.customer_id = $2",
        order["id"],
        customer_id,
    )
    return captured


async def _cancel(conn: Conn, ctx: TurnContext, args: CancelArgs, order: Any) -> Outcome:
    customer, order_id, ccy = ctx.customer.customer_id, order["id"], order["currency"]
    rules = engine.load_rules()
    refund = await _cancel_refund(conn, order, customer, rules)
    key = idempotency.key(customer, "cancel_order", order_id, {}, ctx.turn_id)
    if (original := await idempotency.lookup(conn, key, customer)) is not None:
        return _replayed(original, order_id)
    verdict = _apply_fraud_signal(
        engine.evaluate_cancel(rules, order["status"]), await _fraud_flag(conn, ctx)
    )
    if verdict.decision == "DENY":
        return await _settle(conn, ctx, key, _denied(list(verdict.reasons), order_id, {}, order["status"]))
    flags = (
        ["high_value_cancellation"] if refund and engine.high_value_cancellation(rules, ccy, refund) else []
    )
    req = replace(
        _request(ctx, "cancel_order", order_id, "ALLOW" if verdict.decision == "ALLOW" else "NEEDS_APPROVAL"),
        amount_cents=refund or None,
        currency=ccy if refund else None,
        args={"reason": args.reason},  # the approval path runs the same cancel, with this reason (J9)
        reasons=verdict.reasons,
    )
    details = {"refund_cents": refund, "currency": ccy, "flags": flags}
    if verdict.decision == "ALLOW":
        refs = await executors.run_cancel(conn, req, refund, args.reason)
        result: dict[str, Any] = {"status": "done", "action": "cancel_order", "order_id": order_id, **refs}
        out = Outcome(result, "executed", "ALLOW", [], order_id, details | refs)
    else:
        # Queued: nothing changes and no refund row exists until staff approve (the H2 refund is part of the
        # cancel the approval path runs).
        refs = await queue.create_request(conn, req)
        result = {"status": "pending_approval", "action": "cancel_order", "order_id": order_id, **refs}
        result["customer_message_hint"] = hints.PENDING
        out = Outcome(result, "queued", "NEEDS_APPROVAL", list(verdict.reasons), order_id, details | refs)
    if refund:
        out.result["refund"] = {"amount_cents": refund, "currency": ccy}
    out.result = with_display(out.result)
    return await _settle(conn, ctx, key, out)


def _missing_pair(current: dict[str, Any], merged: dict[str, str], given: NewAddress) -> list[str]:
    """K1 (symmetric): if the city or postcode changes, both must be supplied; so must they for a country
    change. Street-only and recipient-only changes are unaffected. Returns the missing field names. Its own
    seam for mutation M34. Limitation: it doesn't check that the postcode belongs to the city."""
    changed = {f for f in ("city", "postal_code", "country") if merged[f] != str(current.get(f) or "")}
    if not changed:
        return []
    return [f for f in ("city", "postal_code") if getattr(given, f) is None]


def _merge_address(current: dict[str, Any], given: NewAddress) -> dict[str, str]:
    """Merge, not replace (I12): a field the customer didn't give keeps its current value."""
    return {
        f: v if (v := getattr(given, f)) is not None else str(current.get(f) or "") for f in ADDRESS_FIELDS
    }


async def _address(conn: Conn, ctx: TurnContext, args: AddressArgs, order: Any) -> Outcome:
    customer, order_id = ctx.customer.customer_id, order["id"]
    raw = order["shipping_address"]
    current: dict[str, Any] = json.loads(raw) if isinstance(raw, str) else dict(raw)
    # RECOMPUTE: the address that would be stored, from the order's own current address.
    new_address = _merge_address(current, args.new_address)
    if any(not v.strip() for v in new_address.values()):
        reasons = ["address_incomplete"]
        return Outcome(_hinted("invalid", reasons[0]), "invalid", reasons=reasons, target=order_id)
    if missing := _missing_pair(current, new_address, args.new_address):
        # Its own outcome, not INVALID (K1): audited with the field NAMES, no key, nothing changed, no card.
        return Outcome(
            {"status": "needs_more_information", "customer_message_hint": hints.fields_required(missing)},
            "needs_more_information",
            reasons=["address_fields_required"],
            target=order_id,
            details={"missing": missing},
        )
    flags = [flag for f, flag in ADDRESS_FLAGS.items() if new_address[f] != (current.get(f) or "")]
    key = idempotency.key(
        customer, "update_shipping_address", order_id, {"new_address": new_address}, ctx.turn_id
    )
    if (original := await idempotency.lookup(conn, key, customer)) is not None:
        return _replayed(original, order_id)
    verdict = _apply_fraud_signal(
        engine.evaluate_address_change(engine.load_rules(), order["status"]), await _fraud_flag(conn, ctx)
    )
    if verdict.decision == "DENY":
        return await _settle(conn, ctx, key, _denied(list(verdict.reasons), order_id, {}, order["status"]))
    allow = verdict.decision == "ALLOW"
    change_args: dict[str, Any] = {
        "new_address": new_address,
        # which fields the customer gave; the rest were kept by the merge (shown on the card, I12)
        "changed": [f for f in ADDRESS_FIELDS if getattr(args.new_address, f) is not None],
    }
    if not allow:
        # the address this change was merged onto: the approval re-check requires it unchanged (J9)
        change_args["previous_address"] = current
    req = replace(
        _request(ctx, "update_shipping_address", order_id, "ALLOW" if allow else "NEEDS_APPROVAL"),
        args=change_args,
        reasons=verdict.reasons,
    )
    if allow:
        refs = await executors.run_address_change(conn, req, new_address)
        result = {"status": "done", "action": "update_shipping_address", "order_id": order_id, **refs}
        details = {**refs, "flags": flags} if flags else dict(refs)
        return await _settle(conn, ctx, key, Outcome(result, "executed", "ALLOW", [], order_id, details))
    refs = await queue.create_request(conn, req)
    queued = {"status": "pending_approval", "action": "update_shipping_address", "order_id": order_id, **refs}
    out = Outcome(
        queued | {"customer_message_hint": hints.PENDING},
        "queued",
        "NEEDS_APPROVAL",
        list(verdict.reasons),
        order_id,
        {**refs, "flags": flags} if flags else dict(refs),
    )
    return await _settle(conn, ctx, key, out)


async def _ticket(conn: Conn, ctx: TurnContext, action: str, args: TicketArgs | EscalateArgs) -> Outcome:
    customer = ctx.customer.customer_id
    category = args.category if isinstance(args, TicketArgs) else None
    key = idempotency.key(
        customer, action, None, {"summary": args.summary, "category": category}, ctx.turn_id
    )
    if (original := await idempotency.lookup(conn, key, customer)) is not None:
        return _replayed(original, None)
    # No policy rule restricts opening a ticket: always ALLOW.
    req = replace(_request(ctx, action, None, "ALLOW"), args={"category": category})
    kind: Literal["ticket", "escalation"] = "escalation" if action == "escalate_to_human" else "ticket"
    refs = await executors.run_ticket(conn, req, kind, args.summary, category)
    result = {"status": "done", "action": action, **refs}
    return await _settle(conn, ctx, key, Outcome(result, "executed", "ALLOW", [], None, dict(refs)))


def _denied(reasons: list[str], order_id: str, details: dict[str, Any], order_status: str) -> Outcome:
    result = _hinted("denied", reasons[0], order_status)
    return Outcome(result, "denied", "DENY", reasons, order_id, details)


def _replayed(original: dict[str, Any], target: str | None) -> Outcome:
    return Outcome(original, "replayed", None, [], target, {"reference": original.get("reference")})


async def _settle(conn: Conn, ctx: TurnContext, key: str, out: Outcome) -> Outcome:
    """Record the idempotency key for an outcome with an EFFECT only; a denial records nothing (I5)."""
    if out.outcome in ("executed", "queued"):
        recorded = await idempotency.record(
            conn, key, ctx.customer.customer_id, out.result["reference"], out.result, _now(ctx)
        )
        if not recorded:
            raise _ConcurrentDuplicate(key, out.target)
    return out


# -- audit ------------------------------------------------------------------------------------------------


async def _audit(conn: Conn, ctx: TurnContext, action: str, out: Outcome) -> int | None:
    audit_id: int | None = await conn.fetchval(
        "INSERT INTO app.audit_log (actor_type, actor_id, event, target, decision, reasons, outcome,"
        " prompt_version, turn_id, details)"
        " VALUES ('customer', $1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9::jsonb) RETURNING id",
        ctx.customer.customer_id,
        f"action.{action}",
        out.target,
        out.decision,
        json.dumps(out.reasons),
        out.outcome,
        ctx.prompt_version,
        ctx.turn_id,
        json.dumps(_flagged_details(ctx, out.details)),
    )
    return audit_id


def _flagged_details(ctx: TurnContext, details: dict[str, Any]) -> dict[str, Any]:
    """Every submission in a flagged turn carries the flag in its audit row (J2)."""
    return details | {"fraud_signal": True} if ctx.fraud_signal else details


async def _audit_rejection(
    ctx: TurnContext, action: str, raw_arguments: str, errors: list[tuple[tuple[int | str, ...], str]]
) -> None:
    """Record that a call failed validation: argument NAMES and error locations/types, never values (I3)."""
    try:
        parsed = json.loads(raw_arguments)
    except ValueError:
        parsed = None
    names = sorted(str(k)[:64] for k in parsed)[:MAX_AUDITED_NAMES] if isinstance(parsed, dict) else []
    details = {
        "tool": action,
        "argument_names": names,
        "errors": [
            {"loc": [str(p)[:64] for p in loc], "type": kind} for loc, kind in errors[:MAX_AUDITED_NAMES]
        ],
    }
    async with ctx.pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO app.audit_log"
            " (actor_type, actor_id, event, reasons, outcome, prompt_version, turn_id, details)"
            " VALUES ('customer', $1, 'tool_call_rejected', '[\"schema_rejected\"]'::jsonb,"
            " 'validation_failed', $2, $3, $4::jsonb)",
            ctx.customer.customer_id,
            ctx.prompt_version,
            ctx.turn_id,
            json.dumps(_flagged_details(ctx, details)),
        )
