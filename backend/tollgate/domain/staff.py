"""What the staff console reads (spec 13.4; Phase 4 pre-registration 4.4, 4.7).

Staff surfaces SHOW policy reasons, reason codes and the rule values behind them (tier C is allowed here,
I15); customer surfaces never do (tests/test_staff_api.py checks both sides for the same request). Staff see
every customer's requests: that is the role, decided by app.staff_users (invariant 22), never by the token.

Nothing here writes or decides. Pending state is read with the derived expiry predicate (J8), and a pending
request's checklist comes from a read-only dry run of the same re-check the approve path runs (J9), passed in
by the staff API (the only caller of approvals/service.py, st05).
"""

import json
import re
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from tollgate.approvals import expiry
from tollgate.db import Conn
from tollgate.domain.models import ActionKind, Money
from tollgate.domain.money import format_money
from tollgate.policy import engine

# Staff vocabulary for reason codes, with the rule values behind them (tier C: staff only, spec 13.4).
RISK_LABELS = {"fraud_signal": "Customer reported a possible unauthorised order"}


def risk_label(code: str, currency: str | None) -> str:
    rules = engine.load_rules()
    ordinal = {2: "2nd", 3: "3rd"}.get(rules.max_refunds_in_window_before_approval + 1, "another")
    caps = {str(k): v for k, v in rules.window_amount_cap.items()}
    cap = format_money(caps[currency], currency) if currency in caps else None
    labels = {
        "auto_max": "Above auto limit",
        "window_count": f"{ordinal} refund or credit in {rules.rolling_window_days} days",
        "window_cap": f"Over {cap} in {rules.rolling_window_days} days" if cap else "Over the window cap",
    }
    return RISK_LABELS.get(code) or labels.get(code) or code


class RiskTag(BaseModel):
    code: str
    label: str


class ApprovalItem(BaseModel):
    reference: str  # the action request (ACT-...)
    action: ActionKind
    order_id: str | None
    customer_id: str
    customer_name: str
    conversation_id: uuid.UUID | None
    amount: Money | None
    reasons: list[str]  # why it was queued (codes; staff only)
    risk_tags: list[RiskTag]
    queued_at: datetime
    expires_at: datetime
    state: Literal["pending", "expired", "approved", "rejected", "failed_recheck"]


class ApprovalQueue(BaseModel):
    now: datetime  # the injected clock (G1); ages are computed against it
    items: list[ApprovalItem]


class ChecklistItem(BaseModel):
    code: str
    label: str  # the rule, with its value (tier C: staff only)
    kind: Literal["deny", "approval"]
    state: Literal["pass", "fail", "not_reached", "needs_approval"]
    detail: str | None = None  # this request's fact the rule was checked against


class OrderFacts(BaseModel):
    id: str
    status: str
    total: Money
    captured: Money
    refunded: Money  # succeeded refunds only
    items: list[str]  # the lines this request covers


class TranscriptMessage(BaseModel):
    turn_id: uuid.UUID
    role: Literal["customer", "assistant", "system"]
    content: str
    at: datetime


class ToolTrace(BaseModel):
    turn_id: uuid.UUID
    tool: str
    arguments: dict[str, Any]
    outcome: str
    latency_ms: int
    at: datetime


class AuditEntry(BaseModel):
    id: int
    at: datetime
    actor_type: str
    actor_id: str
    event: str
    target: str | None
    decision: str | None
    reasons: list[str]
    outcome: str | None
    details: dict[str, Any]
    turn_id: uuid.UUID | None  # the customer turn that wrote it; None for staff decisions and expiries
    # The amount the record is about, with its currency: a refund or credit's, or a paid cancel's H2 refund.
    # Not sortable across rows: USD cents and PKR paisa are never converted (DECISIONS A1, A2).
    amount: Money | None = None
    conversation_id: uuid.UUID | None = None  # for the link to the read-only conversation view


class ReferenceCheck(BaseModel):
    """An approval reference found in customer- or model-written text, checked against app.approvals (L18)."""

    reference: str
    exists: bool


class Transcript(BaseModel):
    conversation_id: uuid.UUID
    customer_id: str
    messages: list[TranscriptMessage]
    tool_calls: list[ToolTrace]
    actions: list[AuditEntry]  # the Action Gateway's audit rows for this conversation's turns
    # Every APR reference in the customer's messages, the assistant's replies and the tool arguments, with
    # whether that approval exists. Only the staff API records approvals (invariant 7), so a reference a
    # customer or the model wrote is a claim, and this says whether it is true (L18; adv01's "APR-000123").
    references: list[ReferenceCheck] = []


class DecisionRecord(BaseModel):
    approval_id: str
    decision: Literal["approved", "rejected", "expired", "failed_recheck"]
    decided_by: str | None  # the staff member's name; None for an expiry
    note: str | None
    decided_at: datetime


class ApprovalDetail(BaseModel):
    approval: ApprovalItem
    order: OrderFacts | None
    checklist: list[ChecklistItem]
    decision: DecisionRecord | None
    transcript: Transcript | None


class StaffProfile(BaseModel):
    name: str
    email: str
    role: str


class AuditPage(BaseModel):
    items: list[AuditEntry]
    page: int
    page_size: int
    total: int


def _json(value: Any) -> Any:
    return json.loads(value) if isinstance(value, str) else value


# -- queue -------------------------------------------------------------------------------------------------

ITEM_SQL = """
    SELECT a.id, a.action, a.order_id, a.customer_id, c.name AS customer_name, a.conversation_id,
           a.amount_cents, a.currency, a.reasons, a.status, a.created_at, p.decision
      FROM app.action_requests a
      JOIN app.customers c ON c.id = a.customer_id
      LEFT JOIN app.approvals p ON p.action_request_id = a.id
"""


def _item(row: Any, now: datetime) -> ApprovalItem:
    reasons = list(_json(row["reasons"]))
    state = row["decision"] or "pending"
    if state == "pending" and expiry.is_expired(row["created_at"], now):
        state = "expired"  # derived (J8): never offered as actionable, whether or not the write happened
    amount = (
        Money(amount_cents=row["amount_cents"], currency=row["currency"]) if row["amount_cents"] else None
    )
    return ApprovalItem(
        reference=row["id"],
        action=row["action"],
        order_id=row["order_id"],
        customer_id=row["customer_id"],
        customer_name=row["customer_name"],
        conversation_id=row["conversation_id"],
        amount=amount,
        reasons=reasons,
        risk_tags=[RiskTag(code=r, label=risk_label(r, row["currency"])) for r in reasons],
        queued_at=row["created_at"],
        expires_at=row["created_at"] + expiry.APPROVAL_TTL,
        state=state,
    )


async def pending_queue(conn: Conn, now: datetime) -> ApprovalQueue:
    """Live pending requests, oldest first. Expired ones are left out by the derived predicate (J8)."""
    rows = await conn.fetch(
        ITEM_SQL + " WHERE a.status = 'pending_approval' AND a.created_at > $1 ORDER BY a.created_at, a.id",
        expiry.live_after(now),
    )
    return ApprovalQueue(now=now, items=[_item(r, now) for r in rows])


async def approval_item(conn: Conn, reference: str, now: datetime) -> ApprovalItem | None:
    """Any request that was queued for approval (pending or decided); None otherwise."""
    row = await conn.fetchrow(ITEM_SQL + " WHERE a.id = $1 AND a.decision = 'NEEDS_APPROVAL'", reference)
    return _item(row, now) if row is not None else None


# -- detail ------------------------------------------------------------------------------------------------


async def order_facts(conn: Conn, order_id: str, line_ids: list[int]) -> OrderFacts | None:
    row = await conn.fetchrow(
        """
        SELECT o.id, o.status, o.currency, o.total_cents,
               (SELECT coalesce(sum(p.amount_cents), 0) FROM app.payments p
                 WHERE p.order_id = o.id) AS captured,
               (SELECT coalesce(sum(r.amount_cents), 0) FROM app.refunds r
                 WHERE r.order_id = o.id AND r.status = 'succeeded') AS refunded,
               (SELECT coalesce(array_agg(pr.name ORDER BY i.id), '{}') FROM app.order_items i
                  JOIN app.products pr ON pr.id = i.product_id
                 WHERE i.order_id = o.id AND i.id = ANY($2::bigint[])) AS items
          FROM app.orders o WHERE o.id = $1
        """,
        order_id,
        line_ids,
    )
    if row is None:
        return None
    ccy = row["currency"]
    return OrderFacts(
        id=row["id"],
        status=row["status"],
        total=Money(amount_cents=row["total_cents"], currency=ccy),
        captured=Money(amount_cents=row["captured"], currency=ccy),
        refunded=Money(amount_cents=row["refunded"], currency=ccy),
        items=list(row["items"]),
    )


async def request_lines(conn: Conn, reference: str) -> list[int]:
    ids = await conn.fetchval("SELECT order_item_ids FROM app.action_requests WHERE id = $1", reference)
    return list(ids or [])


async def decision_record(conn: Conn, reference: str) -> DecisionRecord | None:
    row = await conn.fetchrow(
        """
        SELECT p.id, p.decision, s.name, p.note, p.decided_at
          FROM app.approvals p LEFT JOIN app.staff_users s ON s.id = p.decided_by
         WHERE p.action_request_id = $1
        """,
        reference,
    )
    if row is None:
        return None
    return DecisionRecord(
        approval_id=row["id"], decision=row["decision"], decided_by=row["name"], note=row["note"],
        decided_at=row["decided_at"],
    )  # fmt: skip


async def stored_recheck(conn: Conn, reference: str) -> dict[str, Any] | None:
    raw = await conn.fetchval("SELECT recheck FROM app.approvals WHERE action_request_id = $1", reference)
    value: dict[str, Any] | None = _json(raw) if raw is not None else None
    return value


def checklist(item: ApprovalItem, recheck: dict[str, Any]) -> list[ChecklistItem]:
    """Every rule that applies to this action, with its value, and how this request fares on it now.

    DENY rules run in the engine's order and stop at the first that fires (the rest are `not_reached`).
    NEEDS_APPROVAL rules are what an approval satisfies: `needs_approval` when they hold now, or when the
    request was queued for them (the fraud signal is about the turn, so only the queued reasons show it)."""
    rules = engine.load_rules()
    facts: dict[str, Any] = recheck.get("facts") or {}
    ccy = item.amount.currency if item.amount else None
    deny_rules, approval_rules = _rules_for(item.action, rules, ccy, facts)
    fired = list(recheck.get("deny") or [])
    out: list[ChecklistItem] = []
    reached = True
    for code, label, detail in deny_rules:
        if not reached:
            state: Literal["pass", "fail", "not_reached", "needs_approval"] = "not_reached"
        elif code in fired:
            state, reached = "fail", False
        else:
            state = "pass"
        out.append(ChecklistItem(code=code, label=label, kind="deny", state=state, detail=detail))
    if fired and fired[0] not in {c for c, _, _ in deny_rules}:  # e.g. not_found, item_not_in_order
        out.insert(
            0, ChecklistItem(code=fired[0], label=fired[0].replace("_", " "), kind="deny", state="fail")
        )
    needs = set(recheck.get("satisfied_by_approval") or []) | set(item.reasons)
    for code, label, detail in approval_rules:
        state = "needs_approval" if code in needs else "pass"
        if code == "fraud_signal" and state == "needs_approval":
            label = RISK_LABELS["fraud_signal"]  # the label states what holds: here, that it WAS reported
        out.append(ChecklistItem(code=code, label=label, kind="approval", state=state, detail=detail))
    return out


def _others(n: Any) -> str | None:
    return None if n is None else f"{n} other" if n == 1 else f"{n} others"


def _words(status: str) -> str:
    return status.replace("_", " ")


def _either(statuses: list[str]) -> str:
    """["pending", "paid", "packed"] -> "pending, paid or packed"."""
    words = [_words(s) for s in statuses]
    return words[0] if len(words) == 1 else f"{', '.join(words[:-1])} or {words[-1]}"


def _money(cents: Any, ccy: str | None) -> str | None:
    return format_money(int(cents), ccy) if ccy and isinstance(cents, int) else None


def _rules_for(
    action: str, rules: engine.Rules, ccy: str | None, facts: dict[str, Any]
) -> tuple[list[tuple[str, str, str | None]], list[tuple[str, str, str | None]]]:
    fraud = ("fraud_signal", "No report of an unauthorised order in the customer's message", None)
    status = facts.get("order_status")
    on_status = f"order is {_words(status)}" if status else None
    if action == "cancel_order":
        return [
            ("status_not_cancellable", f"Order is {_either(rules.cancel_allowed_statuses)}", on_status),
            (
                "amount_changed",
                "Refund still equals the captured payment (H2)",
                _money(facts.get("refund_cents"), ccy),
            ),
        ], [fraud]
    if action == "update_shipping_address":
        return [
            (
                "status_not_addressable",
                f"Order is {_either(rules.address_change_allowed_statuses)}",
                on_status,
            ),
            ("address_changed", "Delivery address unchanged since the request", None),
        ], [fraud]
    kind = rules.refund if action == "request_refund" else rules.store_credit

    def limit(per_currency: dict[Any, int]) -> str | None:
        return format_money(per_currency[ccy], ccy) if ccy else None

    remainder = _money(facts.get("refundable_remainder_cents"), ccy)
    window_n, window_total = facts.get("window_count"), _money(facts.get("window_total_cents"), ccy)
    return [
        ("status_not_refundable", f"Order is {_either(rules.refundable_statuses)}", on_status),
        ("outside_return_window", f"Within the {rules.return_window_days}-day return window",
         f"delivered {facts['delivered_at'][:10]}" if facts.get("delivered_at") else None),
        ("final_sale", "No final-sale items", None),
        ("digital_downloaded", "No downloaded digital items", None),
        ("line_already_compensated", "No other refund or credit on these lines (H1)", None),
        ("exceeds_refundable_remainder", "Within what's left to refund on the order",
         f"{remainder} left" if remainder else None),
        ("above_approval_max", f"At or under the approval maximum ({limit(kind.approval_max)})", None),
    ], [
        ("auto_max", f"At or under the automatic limit ({limit(kind.auto_max)})", None),
        ("window_count",
         f"Fewer than {rules.max_refunds_in_window_before_approval} other refunds or credits in"
         f" {rules.rolling_window_days} days", _others(window_n)),
        ("window_cap", f"Window total at or under {limit(rules.window_amount_cap)}",
         f"{window_total} others" if window_total else None),
        fraud,
    ]  # fmt: skip


# -- transcripts and audit -----------------------------------------------------------------------------------


def _amount(details: dict[str, Any]) -> Money | None:
    cents = details.get("amount_cents") or details.get("refund_cents")
    currency = details.get("currency")
    if isinstance(cents, int) and cents > 0 and currency in ("USD", "PKR"):
        return Money(amount_cents=cents, currency=currency)
    return None


def _audit_entry(r: Any) -> AuditEntry:
    return AuditEntry(
        id=r["id"], at=r["at"], actor_type=r["actor_type"], actor_id=r["actor_id"], event=r["event"],
        target=r["target"], decision=r["decision"], reasons=list(_json(r["reasons"])), outcome=r["outcome"],
        details=dict(_json(r["details"])), turn_id=r["turn_id"], conversation_id=r.get("conversation_id"),
        amount=_amount(dict(_json(r["details"]))),
    )  # fmt: skip


APPROVAL_REF = re.compile(r"\bAPR-\d+\b")


async def _existing_approvals(conn: Conn, refs: list[str]) -> set[str]:
    """Which of `refs` are approvals on record. Its own seam for mutation M68."""
    rows = await conn.fetch("SELECT id FROM app.approvals WHERE id = ANY($1::text[])", refs)
    return {r["id"] for r in rows}


async def _check_references(conn: Conn, texts: list[str]) -> list[ReferenceCheck]:
    refs = sorted({m.group(0) for text in texts for m in APPROVAL_REF.finditer(text)})
    existing = await _existing_approvals(conn, refs) if refs else set()
    return [ReferenceCheck(reference=r, exists=r in existing) for r in refs]


async def transcript(conn: Conn, conversation_id: uuid.UUID) -> Transcript | None:
    """The whole conversation, every role, with the tool trace and the gateway's audit rows (read-only)."""
    owner = await conn.fetchval("SELECT customer_id FROM app.conversations WHERE id = $1", conversation_id)
    if owner is None:
        return None
    messages = await conn.fetch(
        "SELECT turn_id, role, content, created_at FROM app.messages WHERE conversation_id = $1 ORDER BY id",
        conversation_id,
    )
    # the conversation's turns: those with messages, and those that submitted an action
    turns = (
        "SELECT turn_id FROM app.messages WHERE conversation_id = $1"
        " UNION SELECT turn_id FROM app.action_requests WHERE conversation_id = $1"
    )
    calls = await conn.fetch(
        f"SELECT turn_id, tool_name, arguments, outcome, latency_ms, created_at FROM app.tool_calls"  # noqa: S608
        f" WHERE turn_id IN ({turns}) ORDER BY id",
        conversation_id,
    )
    audits = await conn.fetch(
        # the gateway's rows for those turns, and the staff decisions about this conversation's requests
        f"SELECT * FROM app.audit_log WHERE turn_id IN ({turns})"  # noqa: S608
        " OR target IN (SELECT id FROM app.action_requests WHERE conversation_id = $1) ORDER BY id",
        conversation_id,
    )
    # Customer- and model-written text only: system notices and audit rows are the store's own records.
    claimed = [m["content"] for m in messages if m["role"] in ("customer", "assistant")]
    claimed += [json.dumps(_json(c["arguments"])) for c in calls]
    return Transcript(
        conversation_id=conversation_id,
        customer_id=owner,
        references=await _check_references(conn, claimed),
        messages=[
            TranscriptMessage(turn_id=m["turn_id"], role=m["role"], content=m["content"], at=m["created_at"])
            for m in messages
        ],
        tool_calls=[
            ToolTrace(
                turn_id=c["turn_id"],
                tool=c["tool_name"],
                arguments=dict(_json(c["arguments"])),
                outcome=c["outcome"],
                latency_ms=c["latency_ms"],
                at=c["created_at"],
            )
            for c in calls
        ],
        actions=[_audit_entry(a) for a in audits],
    )


# Which conversation an audit row belongs to: the request it targets, else the turn that wrote it.
CONVERSATION = """coalesce(
    (SELECT r.conversation_id FROM app.action_requests r WHERE r.id = a.target),
    (SELECT r.conversation_id FROM app.action_requests r WHERE r.turn_id = a.turn_id LIMIT 1),
    (SELECT m.conversation_id FROM app.messages m WHERE m.turn_id = a.turn_id LIMIT 1))"""


async def audit_page(
    conn: Conn,
    *,
    decision: str | None,
    action: str | None,
    customer: str | None,
    since: datetime | None,
    until: datetime | None,
    page: int,
    page_size: int,
) -> AuditPage:
    """The audit log, newest first. `action` matches gateway events and the decisions about that action;
    `customer` matches the customer's own submissions and decisions about their requests."""
    where = """
        ($1::text IS NULL OR a.decision = $1)
        AND ($2::text IS NULL OR a.event = 'action.' || $2
             OR (a.event LIKE 'approval.%' AND a.details->>'action' = $2))
        AND ($3::text IS NULL OR (a.actor_type = 'customer' AND a.actor_id = $3)
             OR a.target IN (SELECT r.id FROM app.action_requests r WHERE r.customer_id = $3))
        AND ($4::timestamptz IS NULL OR a.at >= $4)
        AND ($5::timestamptz IS NULL OR a.at < $5)
    """
    args = (decision, action, customer, since, until)
    total = await conn.fetchval(f"SELECT count(*) FROM app.audit_log a WHERE {where}", *args)  # noqa: S608
    rows = await conn.fetch(
        f"SELECT a.*, {CONVERSATION} AS conversation_id FROM app.audit_log a"  # noqa: S608
        f" WHERE {where} ORDER BY a.id DESC LIMIT $6 OFFSET $7",
        *args,
        page_size,
        (page - 1) * page_size,
    )
    return AuditPage(items=[_audit_entry(r) for r in rows], page=page, page_size=page_size, total=int(total))
