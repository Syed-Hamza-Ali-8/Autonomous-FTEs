"""Staff API (spec 13.4; Phase 4 pre-registration 4.3, 4.4). The ONLY importer of approvals/service.py (st05).

Every route requires a support lead from app.staff_users (invariant 22); a customer, or anyone else, gets 403
with the same body as every other refusal. Decisions run in one transaction each and commit before the reply.
Lazy expiry (B7, J8) runs on inbox load and on every read of or action on an approval: an expired request is
recorded as expired and never offered as actionable.
"""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from tollgate.approvals import service
from tollgate.auth.deps import Pool, Staff
from tollgate.domain import dashboard as dashboard_domain
from tollgate.domain import staff as staff_domain
from tollgate.domain.models import ActionKind, Currency
from tollgate.errors import NotFoundError
from tollgate.llm.budget import tokens_used_24h

router = APIRouter(prefix="/v1/staff", tags=["staff"])


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ApproveBody(_Strict):
    """Exactly what the staff member was shown (stale-screen guard). Both null for an action without one."""

    amount_cents: int | None
    currency: Currency | None


class RejectBody(_Strict):
    note: str = Field(
        min_length=1, max_length=2000
    )  # required (pre-registration 4.5): staff-only, never shown

    @field_validator("note")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("a rejection needs a note")
        return value.strip()


class DecisionOut(BaseModel):
    reference: str
    approval_id: str
    decision: Literal["approved", "rejected", "failed_recheck", "expired"]
    reasons: list[str]  # failed_recheck: the rule that fired (staff only)


def _now(request: Request) -> datetime:
    now: datetime = request.app.state.clock.now()  # the injected clock (G1)
    return now


def _ref(reference: str) -> str:
    return reference.strip().upper()


def _decided(d: service.Decision) -> DecisionOut | JSONResponse:
    out = DecisionOut(
        reference=d.reference, approval_id=d.approval_id, decision=d.decision, reasons=list(d.reasons)
    )
    if d.decision == "expired":  # recorded and committed; the action asked for was not taken
        return JSONResponse({"error": "expired", **out.model_dump()}, status_code=409)
    return out


@router.get("/me")
async def me(staff: Staff) -> staff_domain.StaffProfile:
    return staff_domain.StaffProfile(name=staff.name, email=staff.email, role=staff.role)


@router.get("/approvals")
async def approvals(staff: Staff, pool: Pool, request: Request) -> staff_domain.ApprovalQueue:
    now = _now(request)
    async with pool.acquire() as conn, conn.transaction():
        await service.expire_due(conn, now)
        return await staff_domain.pending_queue(conn, now)


@router.get("/approvals/{reference}")
async def approval(reference: str, staff: Staff, pool: Pool, request: Request) -> staff_domain.ApprovalDetail:
    now, ref = _now(request), _ref(reference)
    async with pool.acquire() as conn, conn.transaction():
        await service.expire_due(conn, now)
        item = await staff_domain.approval_item(conn, ref, now)
        if item is None:
            raise NotFoundError("approval")
        lines = await staff_domain.request_lines(conn, ref)
        order = await staff_domain.order_facts(conn, item.order_id, lines) if item.order_id else None
        recheck = (
            await service.preview(conn, ref, now)
            if item.state == "pending"
            else await staff_domain.stored_recheck(conn, ref)
        )
        return staff_domain.ApprovalDetail(
            approval=item,
            order=order,
            checklist=staff_domain.checklist(item, recheck or {}),
            decision=await staff_domain.decision_record(conn, ref),
            transcript=await staff_domain.transcript(conn, item.conversation_id)
            if item.conversation_id
            else None,
        )


@router.post("/approvals/{reference}/approve", response_model=DecisionOut)
async def approve(
    reference: str, body: ApproveBody, staff: Staff, pool: Pool, request: Request
) -> DecisionOut | JSONResponse:
    async with pool.acquire() as conn, conn.transaction():
        decided = await service.approve(
            conn, staff.staff_id, _ref(reference), body.amount_cents, body.currency, _now(request)
        )
    return _decided(decided)


@router.post("/approvals/{reference}/reject", response_model=DecisionOut)
async def reject(
    reference: str, body: RejectBody, staff: Staff, pool: Pool, request: Request
) -> DecisionOut | JSONResponse:
    async with pool.acquire() as conn, conn.transaction():
        decided = await service.reject(conn, staff.staff_id, _ref(reference), body.note, _now(request))
    return _decided(decided)


@router.get("/audit")
async def audit(
    staff: Staff,
    pool: Pool,
    decision: Literal["ALLOW", "NEEDS_APPROVAL", "DENY"] | None = None,
    action: ActionKind | None = None,
    customer: str | None = None,
    since: Annotated[datetime | None, Query(alias="from")] = None,
    until: Annotated[datetime | None, Query(alias="to")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> staff_domain.AuditPage:
    async with pool.acquire() as conn:
        return await staff_domain.audit_page(
            conn, decision=decision, action=action, customer=customer, since=since, until=until,
            page=page, page_size=page_size,
        )  # fmt: skip


@router.get("/conversations/{conversation_id}")
async def conversation(conversation_id: uuid.UUID, staff: Staff, pool: Pool) -> staff_domain.Transcript:
    async with pool.acquire() as conn:
        found = await staff_domain.transcript(conn, conversation_id)
    if found is None:
        raise NotFoundError("conversation")
    return found


@router.get("/dashboard")
async def dashboard(staff: Staff, pool: Pool, request: Request) -> dashboard_domain.Dashboard:
    """Spec 13.5 (DECISIONS L20): live metrics from the database, eval results from the run files, kept
    apart."""
    llm = request.app.state.llm
    async with pool.acquire() as conn:
        used = await tokens_used_24h(conn, llm.model_name, llm.ledger)  # the pre-flight's own figure
        return await dashboard_domain.build(
            conn, _now(request), dashboard_domain.RUNS_DIR, used, llm.daily_budget, llm.model_name
        )

