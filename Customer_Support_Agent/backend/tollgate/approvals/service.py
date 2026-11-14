"""Approval decisions: approve, reject, expire, notify (spec 4.5; DECISIONS B6, B7, J7-J9; A2-P4, A3-P4).

The ONLY module that writes `app.approvals` or moves an action request out of `pending_approval` (st05). Only
the staff API imports it, so no tool reaches a decision (invariant 7; af06). The database backs this up: a
request moves only with a matching decision row (`action_requests_decision_requires_approval`), and a pending
refund or credit pays out only once its request is approved (`refunds_follow_their_request`,
`store_credits_follow_their_request`).

ONE approval path for every action type (J9): each queueable action has a re-check and an execution in
`PATHS`, and the executions are the effect functions the gateway runs for an ALLOW, so the two can't drift.
Every decision runs in the caller's transaction:
- LOCK the order (the same row lock every gateway write on that order takes), then the request.
- EXPIRE first: the derived predicate (expiry.py, J8) wins over whatever was asked. Nothing executes.
- APPROVE checks the amount staff were shown (stale-screen guard), then re-checks on CURRENT data (B6):
  ownership, order state and every DENY rule, with the request's own rows left out. NEEDS_APPROVAL rules are
  what this approval satisfies. Any DENY now -> `failed_recheck`, nothing executes. It never asks the model.
- RECORD the decision row, then the request's status, then its money row; EXECUTE; AUDIT; NOTIFY the
  conversation with a tier-safe system message (I15).
"""

import json
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, get_args

from tollgate.actions import cards, executors, gateway
from tollgate.actions.records import MoneyAction
from tollgate.approvals import expiry
from tollgate.db import Conn
from tollgate.errors import ActionFailedError, ApprovalConflictError, NotFoundError
from tollgate.policy import engine
from tollgate.tools.registry import REGISTRY

MONEY: tuple[MoneyAction, ...] = get_args(MoneyAction)
# The request's status after each decision (enforced again by action_requests_decision_requires_approval).
REQUEST_STATUS = {
    "approved": "approved",
    "rejected": "rejected",
    "failed_recheck": "rejected",
    "expired": "expired",
}
POLICY_DECISION = {"approved": "ALLOW", "failed_recheck": "DENY"}  # the audit row's decision column

REQUEST_SQL = (
    "SELECT id, customer_id, conversation_id, action, order_id, order_item_ids, amount_cents, currency,"
    " args, reasons, status, created_at FROM app.action_requests WHERE id = $1"
)


@dataclass(frozen=True)
class Decision:
    reference: str  # the action request (ACT-...), which is what staff and the customer's card refer to
    approval_id: str
    decision: str  # approved | rejected | failed_recheck | expired
    reasons: tuple[str, ...] = ()  # failed_recheck: the DENY rule that fired (staff only, tier C)


async def approve(
    conn: Conn,
    staff_id: uuid.UUID,
    reference: str,
    amount_cents: int | None,
    currency: str | None,
    now: datetime,
) -> Decision:
    """Approve exactly what the staff member was shown: `amount_cents`/`currency` must equal the request's own
    (stale-screen guard; both None for an action without an amount). Returns `expired` instead if the request
    ran out of time first."""
    req, order = await _lock(conn, reference)
    if _due(req, now):
        return await _record(conn, req, "expired", None, None, {}, now)
    if not _shown_amount_matches(req, amount_cents, currency):
        raise ApprovalConflictError("amount_mismatch")
    path = PATHS.get(req["action"])
    if path is None:  # the contact tier is never queued (P4-1); nothing else is missing (tested)
        raise ActionFailedError(f"{reference}: {req['action']} is never queued for approval")
    recheck = (
        await path.recheck(conn, req, order, now)
        if order is not None
        else {"deny": ["not_found"], "facts": {}}
    )
    if recheck["deny"]:
        return await _record(conn, req, "failed_recheck", staff_id, None, recheck, now)
    decided = await _record(conn, req, "approved", staff_id, None, recheck, now)
    await path.execute(conn, req, now)
    return decided


async def reject(conn: Conn, staff_id: uuid.UUID, reference: str, note: str, now: datetime) -> Decision:
    """Reject with a note (staff only; never shown to the customer). Frees the lines (H1) and window (A7)."""
    if not note.strip():
        raise ValueError("a rejection needs a note")
    req, _ = await _lock(conn, reference)
    if _due(req, now):
        return await _record(conn, req, "expired", None, None, {}, now)
    return await _record(conn, req, "rejected", staff_id, note.strip(), {}, now)


async def expire_due(conn: Conn, now: datetime) -> list[Decision]:
    """Catch stored state up with the derived predicate (J8): record every pending request that is expired.
    Readers never wait for this; it keeps the decisions log and the stored statuses honest."""
    due = await conn.fetch(
        "SELECT id FROM app.action_requests WHERE status = 'pending_approval' AND created_at <= $1"
        " ORDER BY id",
        expiry.live_after(now),
    )
    out = []
    for row in due:
        try:
            req, _ = await _lock(conn, row["id"])
        except ApprovalConflictError:
            continue  # decided by someone else in the meantime
        out.append(await _record(conn, req, "expired", None, None, {}, now))
    return out


async def preview(conn: Conn, reference: str, now: datetime) -> dict[str, Any] | None:
    """What approving NOW would find, without deciding or locking anything: the same per-type re-check (B6)
    the approve path runs, for the staff checklist. None if it isn't pending or has no approval path."""
    req = await conn.fetchrow(REQUEST_SQL, reference)
    if req is None or req["status"] != "pending_approval" or req["action"] not in PATHS:
        return None
    order = await conn.fetchrow(
        "SELECT id, status, currency, delivered_at, shipping_address FROM app.orders"
        " WHERE id = $1 AND customer_id = $2",
        req["order_id"],
        req["customer_id"],
    )
    if order is None:
        return {"deny": ["not_found"], "satisfied_by_approval": [], "facts": {}}
    return await PATHS[req["action"]].recheck(conn, req, order, now)


def _shown_amount_matches(req: Any, amount_cents: int | None, currency: str | None) -> bool:
    """The stale-screen guard: staff approve exactly what they were shown. Its own seam for mutation M33."""
    return (amount_cents, currency) == (req["amount_cents"], req["currency"])


def _due(req: Any, now: datetime) -> bool:
    """R6 of the derived expiry predicate (J8); its own seam for mutation M30."""
    return expiry.is_expired(req["created_at"], now)


async def _lock(conn: Conn, reference: str) -> tuple[Any, Any]:
    """Lock the order (ownership: it must still be the request's customer's), then the request, and require it
    to be pending. Returns (request, order or None). A missing request -> NotFoundError."""
    peek = await conn.fetchrow(
        "SELECT order_id, customer_id FROM app.action_requests WHERE id = $1", reference
    )
    if peek is None:
        raise NotFoundError("approval")
    order = None
    if peek["order_id"] is not None:
        order = await gateway._load_order(conn, peek["order_id"], peek["customer_id"])
    req = await conn.fetchrow(REQUEST_SQL + " FOR UPDATE", reference)
    if req is None:
        raise NotFoundError("approval")
    if req["status"] != "pending_approval":
        raise ApprovalConflictError("already_decided")
    return req, order


def _args(req: Any) -> dict[str, Any]:
    raw = req["args"]
    return dict(json.loads(raw) if isinstance(raw, str) else raw)


# -- re-checks (B6): DENY rules only, on current data, the request's own rows left out ---------------------


async def _recheck_money(conn: Conn, req: Any, order: Any, now: datetime) -> dict[str, Any]:
    reference, customer, order_id = req["id"], req["customer_id"], req["order_id"]
    line_ids = list(req["order_item_ids"])
    lines = await conn.fetch(
        """
        SELECT i.id, p.final_sale, p.digital, i.downloaded_at
          FROM app.order_items i
          JOIN app.orders o ON o.id = i.order_id
          JOIN app.products p ON p.id = i.product_id
         WHERE i.order_id = $1 AND o.customer_id = $2 AND i.id = ANY($3::bigint[])
        """,
        order_id,
        customer,
        line_ids,
    )
    if len(lines) != len(set(line_ids)):
        return {"deny": ["item_not_in_order"], "facts": {}}
    rules = engine.load_rules()
    remainder, compensated = await gateway._order_facts(
        conn, order_id, customer, line_ids, now, exclude_request=reference
    )
    count, total = await gateway._window(
        conn,
        customer,
        engine.window_start(rules, now),
        req["currency"],
        rules.cancellation.counts_toward_window,
        now,
        exclude_request=reference,
    )
    facts = engine.MoneyFacts(
        kind="refund" if req["action"] == "request_refund" else "store_credit",
        currency=req["currency"],
        amount_cents=req["amount_cents"],
        order_status=order["status"],
        delivered_at=order["delivered_at"],
        any_final_sale=any(r["final_sale"] for r in lines),
        any_digital_downloaded=any(r["digital"] and r["downloaded_at"] is not None for r in lines),
        lines_already_compensated=compensated,
        refundable_remainder_cents=remainder,
        window_count=count,
        window_total_cents=total,
    )
    return _verdict(
        engine.evaluate_money(rules, facts, now), json.loads(json.dumps(asdict(facts), default=str))
    )


async def _recheck_cancel(conn: Conn, req: Any, order: Any, now: datetime) -> dict[str, Any]:
    """The current status must still allow a cancel, and the H2 refund, recomputed now, must be what staff
    were shown (the request's amount)."""
    rules = engine.load_rules()
    refund = await gateway._cancel_refund(conn, order, req["customer_id"], rules)
    facts = {"order_status": order["status"], "refund_cents": refund}
    verdict = engine.evaluate_cancel(rules, order["status"])
    if verdict.decision != "DENY" and refund != (req["amount_cents"] or 0):
        return {"deny": ["amount_changed"], "facts": facts}
    return _verdict(verdict, facts)


async def _recheck_address(conn: Conn, req: Any, order: Any, now: datetime) -> dict[str, Any]:
    """The current status must still allow a change, and the address must still be the one the change was
    merged onto (stored at queueing; missing -> fail closed)."""
    raw = order["shipping_address"]
    current = json.loads(raw) if isinstance(raw, str) else dict(raw)
    facts = {"order_status": order["status"]}
    verdict = engine.evaluate_address_change(engine.load_rules(), order["status"])
    if verdict.decision != "DENY" and _args(req).get("previous_address") != current:
        return {"deny": ["address_changed"], "facts": facts}
    return _verdict(verdict, facts)


def _verdict(verdict: engine.Verdict, facts: dict[str, Any]) -> dict[str, Any]:
    return {
        "deny": list(verdict.reasons) if verdict.decision == "DENY" else [],
        # the NEEDS_APPROVAL rules this approval satisfies (B6), as they stand now
        "satisfied_by_approval": list(verdict.reasons) if verdict.decision == "NEEDS_APPROVAL" else [],
        "facts": facts,
    }


# -- executions: the gateway's own effect functions (J9) --------------------------------------------------


async def _execute_money(conn: Conn, req: Any, now: datetime) -> None:
    kind: MoneyAction = req["action"]
    await executors.complete_money(conn, kind, req["id"], req["order_id"], req["customer_id"])


async def _execute_cancel(conn: Conn, req: Any, now: datetime) -> None:
    await executors.cancel(
        conn,
        req["id"],
        req["order_id"],
        req["customer_id"],
        req["currency"],
        req["amount_cents"] or 0,
        str(_args(req).get("reason") or ""),
        now,
    )


async def _execute_address(conn: Conn, req: Any, now: datetime) -> None:
    await executors.change_address(conn, req["order_id"], req["customer_id"], _args(req)["new_address"])


@dataclass(frozen=True)
class Path:
    recheck: Callable[[Conn, Any, Any, datetime], Awaitable[dict[str, Any]]]
    execute: Callable[[Conn, Any, datetime], Awaitable[None]]


PATHS: dict[str, Path] = {
    "request_refund": Path(_recheck_money, _execute_money),
    "issue_store_credit": Path(_recheck_money, _execute_money),
    "cancel_order": Path(_recheck_cancel, _execute_cancel),
    "update_shipping_address": Path(_recheck_address, _execute_address),
}
NEVER_QUEUED = frozenset(n for n, s in REGISTRY.items() if s.tier == "contact")  # P4-1


# -- record, audit, notify --------------------------------------------------------------------------------


async def _record(
    conn: Conn,
    req: Any,
    decision: str,
    staff_id: uuid.UUID | None,
    note: str | None,
    recheck: dict[str, Any],
    now: datetime,
) -> Decision:
    """Decision row first (the request's trigger requires it), then the request, then its money row."""
    reference = req["id"]
    approval_id: str = await conn.fetchval(
        "INSERT INTO app.approvals (action_request_id, decision, decided_by, note, recheck, decided_at)"
        " VALUES ($1, $2, $3, $4, $5::jsonb, $6) RETURNING id",
        reference,
        decision,
        staff_id,
        note,
        json.dumps(recheck),
        now,
    )
    await conn.execute(
        "UPDATE app.action_requests SET status = $2, decided_at = $3"
        " WHERE id = $1 AND status = 'pending_approval'",
        reference,
        REQUEST_STATUS[decision],
        now,
    )
    if decision != "approved" and req["action"] in MONEY:
        # The hold ends: the lines (H1), the remainder and the window (A7) are free again. No money moves.
        for sql in RELEASE_SQL:
            await conn.execute(sql, reference)
    reasons = tuple(recheck.get("deny", ()))
    await _audit(conn, req, decision, staff_id, approval_id, reasons, note, recheck)
    await _notify(conn, req, decision, now)
    return Decision(reference, approval_id, decision, reasons)


RELEASE_SQL = (
    "UPDATE app.refunds SET status = 'rejected' WHERE action_request_id = $1 AND status = 'pending_approval'",
    "UPDATE app.store_credits SET status = 'rejected'"
    " WHERE action_request_id = $1 AND status = 'pending_approval'",
)


async def _audit(
    conn: Conn,
    req: Any,
    decision: str,
    staff_id: uuid.UUID | None,
    approval_id: str,
    reasons: tuple[str, ...],
    note: str | None,
    recheck: dict[str, Any],
) -> None:
    """One audit row per decision. Staff-facing, so reason codes and re-check facts are kept (tier C)."""
    details = {
        "approval_id": approval_id,
        "action": req["action"],
        "order_id": req["order_id"],
        "amount_cents": req["amount_cents"],
        "currency": req["currency"],
        "queued_for": json.loads(req["reasons"]) if isinstance(req["reasons"], str) else req["reasons"],
        "recheck": recheck,
    } | ({"note": note} if note else {})
    await conn.execute(
        "INSERT INTO app.audit_log (actor_type, actor_id, event, target, decision, reasons, outcome, details)"
        " VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8::jsonb)",
        "system" if staff_id is None else "staff",
        "approval_expiry" if staff_id is None else str(staff_id),
        f"approval.{decision}",
        req["id"],
        POLICY_DECISION.get(decision),
        json.dumps(list(reasons)),
        decision,
        json.dumps(details),
    )


async def _notify(conn: Conn, req: Any, decision: str, now: datetime) -> None:
    """A system message in the customer's conversation: the outcome only, never why (I15)."""
    if req["conversation_id"] is None:
        return
    await conn.execute(
        "INSERT INTO app.messages (conversation_id, turn_id, role, content, created_at)"
        " VALUES ($1, $2, 'system', $3, $4)",
        req["conversation_id"],
        uuid.uuid4(),
        cards.decided_message(decision, req["id"], req["action"]),
        now,
    )
