"""The approval service and the database guards behind it (Phase 4 pre-registration 4.5; amendment A2-P4).

Pending requests are created through the real Action Gateway (the write tools), then decided through
approvals/service.py. Every test runs in a rolled-back transaction (DECISIONS C5). The staff-API probes
(ap01-ap16) come with the staff API; these tests pin the service's own behaviour and the triggers' liveness.

Trigger mutation checks (invariant 16): M37 drops `action_requests_decision_requires_approval`, M38 drops the
two money-row triggers. Each is killed by at least two planted forgeries (K5): with the trigger present the
forgery is refused, without it the forgery goes through.
"""

import json
import uuid
from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Any, get_args

import asyncpg
import pytest

from tests.probe_harness import FIXTURE_NOW, call_tool, new_context, new_conversation
from tests.txpool import TxPool, rolled_back
from tollgate.actions import hints
from tollgate.actions.records import Request, insert_request
from tollgate.approvals import expiry, service
from tollgate.config import SupabaseSettings
from tollgate.domain import actions as domain_actions
from tollgate.domain import orders as domain_orders
from tollgate.domain.models import ActionKind
from tollgate.errors import ActionFailedError, ApprovalConflictError, NotFoundError
from tollgate.policy.disclosure import find

NOW = FIXTURE_NOW
# A $51.00 refund of one delivered line: above the refund auto limit, so it is queued (as probe b02).
REFUND = ("CUS-025", "request_refund", {"order_id": "ORD-1058", "items": ["Ceramic Dinner Set"],
                                        "amount_cents": 5100, "reason": "damaged"})  # fmt: skip
# A $500.00 refund on a $658.00 order: approving it must not count its OWN pending row against the remainder.
BIG_REFUND = ("CUS-047", "request_refund", {"order_id": "ORD-1161", "items": ["4K Monitor 27in"],
                                            "amount_cents": 50000, "reason": "damaged"})  # fmt: skip
# A $200.00 store credit: above the credit auto limit, so it is queued.
CREDIT = ("CUS-047", "issue_store_credit", {"order_id": "ORD-1161", "items": ["4K Monitor 27in"],
                                            "amount_cents": 20000, "reason": "goodwill"})  # fmt: skip


@pytest.fixture
async def pool(settings: SupabaseSettings) -> AsyncIterator[TxPool]:
    async with rolled_back(settings.database_url.get_secret_value()) as p:
        yield p


@pytest.fixture
async def staff(pool: TxPool) -> uuid.UUID:
    staff_id: uuid.UUID = await pool.fetchval(
        "INSERT INTO app.staff_users (name, email, role) VALUES ('Test Lead', 'lead@example.test',"
        " 'support_lead') RETURNING id"
    )
    return staff_id


async def queue(pool: TxPool, spec: tuple[str, str, dict[str, Any]]) -> dict[str, Any]:
    customer, tool, args = spec
    conn = pool.connection
    ctx = await new_context(conn, pool, customer, uuid.uuid4(), await new_conversation(conn, customer))
    result: dict[str, Any] = await call_tool(ctx, tool, args)
    assert result["status"] == "pending_approval", result
    return result | {"conversation_id": ctx.conversation_id}


async def state(pool: TxPool, reference: str) -> dict[str, Any]:
    row = await pool.fetchrow(
        """
        SELECT a.status AS request, a.order_id, o.status AS order_status,
               (SELECT r.status FROM app.refunds r WHERE r.action_request_id = a.id) AS refund,
               (SELECT c.status FROM app.store_credits c WHERE c.action_request_id = a.id) AS credit,
               (SELECT count(*) FROM app.approvals p WHERE p.action_request_id = a.id) AS decisions
          FROM app.action_requests a JOIN app.orders o ON o.id = a.order_id
         WHERE a.id = $1
        """,
        reference,
    )
    assert row is not None
    return dict(row)


async def system_messages(pool: TxPool, conversation_id: uuid.UUID) -> list[str]:
    rows = await pool.fetch(
        "SELECT content FROM app.messages WHERE conversation_id = $1 AND role = 'system' ORDER BY id",
        conversation_id,
    )
    return [r["content"] for r in rows]


# -- approve -------------------------------------------------------------------------------------------------


async def test_approve_pays_out_records_audits_and_notifies(pool: TxPool, staff: uuid.UUID) -> None:
    queued = await queue(pool, REFUND)
    ref = queued["reference"]
    async with pool.acquire() as conn:
        decided = await service.approve(conn, staff, ref, 5100, "USD", NOW)
    assert decided.decision == "approved" and decided.approval_id.startswith("APR-")
    assert await state(pool, ref) == {
        "request": "approved", "order_id": "ORD-1058", "order_status": "partially_refunded",
        "refund": "succeeded", "credit": None, "decisions": 1,
    }  # fmt: skip
    audit = await pool.fetchrow(
        "SELECT actor_type, actor_id, decision, outcome FROM app.audit_log WHERE event = 'approval.approved'"
        " AND target = $1",
        ref,
    )
    assert dict(audit) == {
        "actor_type": "staff",
        "actor_id": str(staff),
        "decision": "ALLOW",
        "outcome": "approved",
    }
    [message] = await system_messages(pool, queued["conversation_id"])
    assert ref in message and "refund is done" in message
    assert find(message) == []  # tier-safe (I15)


async def test_approve_excludes_the_request_itself_from_the_recheck(pool: TxPool, staff: uuid.UUID) -> None:
    """B6: its own pending $500 must not count against the $658 order's remainder, nor its own lines (H1)."""
    ref = (await queue(pool, BIG_REFUND))["reference"]
    async with pool.acquire() as conn:
        decided = await service.approve(conn, staff, ref, 50000, "USD", NOW)
    assert decided.decision == "approved", decided
    assert (await state(pool, ref))["refund"] == "succeeded"


async def test_approve_a_store_credit(pool: TxPool, staff: uuid.UUID) -> None:
    ref = (await queue(pool, CREDIT))["reference"]
    async with pool.acquire() as conn:
        assert (await service.approve(conn, staff, ref, 20000, "USD", NOW)).decision == "approved"
    s = await state(pool, ref)
    assert (s["request"], s["credit"], s["order_status"]) == ("approved", "succeeded", "delivered")


async def test_a_deny_rule_firing_now_fails_the_recheck(pool: TxPool, staff: uuid.UUID) -> None:
    """B6: the item became final-sale after queueing; approval re-checks current data and pays nothing."""
    queued = await queue(pool, REFUND)
    ref = queued["reference"]
    await pool.execute("UPDATE app.products SET final_sale = true WHERE name = 'Ceramic Dinner Set'")
    async with pool.acquire() as conn:
        decided = await service.approve(conn, staff, ref, 5100, "USD", NOW)
    assert (decided.decision, decided.reasons) == ("failed_recheck", ("final_sale",))
    s = await state(pool, ref)
    assert (s["request"], s["refund"], s["order_status"]) == ("rejected", "rejected", "delivered")
    recheck = await pool.fetchval(
        "SELECT recheck->'deny' FROM app.approvals WHERE action_request_id = $1", ref
    )
    assert "final_sale" in recheck  # staff see which rule (tier C allowed there)
    [message] = await system_messages(pool, queued["conversation_id"])
    # the customer is never told why, and it doesn't read as a rejection (J10)
    assert message == hints.DECIDED["failed_recheck"].format(reference=ref)
    assert "final" not in message.lower() and "approve" not in message.lower()
    record = await domain_actions.get_action(pool.connection, "CUS-025", ref, NOW)
    assert record is not None
    assert (record.state, record.explanation) == ("not_completed", hints.NOT_COMPLETED)
    detail = await domain_orders.get_order(pool.connection, "CUS-025", "ORD-1058", NOW)
    assert detail is not None
    assert [r.status for r in detail.refunds if r.id == queued["refund_id"]] == ["not_completed"]


async def test_a_failed_recheck_and_a_rejection_look_different_to_the_customer(
    pool: TxPool, staff: uuid.UUID
) -> None:
    """J10: the same request, decided both ways (each rolled back), gives two states and two messages."""
    seen = {}
    for outcome in ("rejected", "failed_recheck"):
        async with pool.savepoint():
            queued = await queue(pool, REFUND)
            ref = queued["reference"]
            async with pool.acquire() as conn:
                if outcome == "rejected":
                    decided = await service.reject(conn, staff, ref, "final_sale applies", NOW)
                else:
                    await conn.execute(
                        "UPDATE app.products SET final_sale = true WHERE name = 'Ceramic Dinner Set'"
                    )
                    decided = await service.approve(conn, staff, ref, 5100, "USD", NOW)
            assert decided.decision == outcome
            record = await domain_actions.get_action(pool.connection, "CUS-025", ref, NOW)
            detail = await domain_orders.get_order(pool.connection, "CUS-025", "ORD-1058", NOW)
            assert record is not None and detail is not None
            [message] = await system_messages(pool, queued["conversation_id"])
            row = next(r.status for r in detail.refunds if r.id == queued["refund_id"])
            texts = (message.replace(ref, "REF"), record.explanation)
            assert all(find(t) == [] and "final" not in t.lower() for t in texts), texts
            seen[outcome] = (record.state, row, *texts)
    assert seen["rejected"][:2] == ("not_allowed", "rejected")
    assert seen["failed_recheck"][:2] == ("not_completed", "not_completed")
    assert all(a != b for a, b in zip(seen["rejected"], seen["failed_recheck"], strict=True))


async def test_approve_twice_executes_once(pool: TxPool, staff: uuid.UUID) -> None:
    ref = (await queue(pool, REFUND))["reference"]
    async with pool.acquire() as conn:
        await service.approve(conn, staff, ref, 5100, "USD", NOW)
        with pytest.raises(ApprovalConflictError, match="already_decided"):
            await service.approve(conn, staff, ref, 5100, "USD", NOW)
    succeeded = await pool.fetchval(
        "SELECT count(*) FROM app.refunds WHERE action_request_id = $1 AND status = 'succeeded'", ref
    )
    assert succeeded == 1


@pytest.mark.parametrize("amount, currency", [(5000, "USD"), (5200, "USD"), (5100, "PKR"), (None, None)])
async def test_approve_refuses_a_stale_amount(
    pool: TxPool, staff: uuid.UUID, amount: int | None, currency: str | None
) -> None:
    ref = (await queue(pool, REFUND))["reference"]
    async with pool.acquire() as conn:
        with pytest.raises(ApprovalConflictError, match="amount_mismatch"):
            await service.approve(conn, staff, ref, amount, currency, NOW)
    s = await state(pool, ref)
    assert (s["request"], s["refund"], s["decisions"]) == ("pending_approval", "pending_approval", 0)


async def test_an_unknown_request_is_not_found(pool: TxPool, staff: uuid.UUID) -> None:
    async with pool.acquire() as conn:
        with pytest.raises(NotFoundError):
            await service.approve(conn, staff, "ACT-999999", 100, "USD", NOW)


async def test_an_executed_request_cannot_be_decided(pool: TxPool, staff: uuid.UUID) -> None:
    customer, tool, args = REFUND
    conn = pool.connection
    ctx = await new_context(conn, pool, customer, uuid.uuid4(), await new_conversation(conn, customer))
    done = await call_tool(ctx, tool, args | {"amount_cents": 4000})  # under the limit: executed directly
    assert done["status"] == "done"
    async with pool.acquire() as c:
        with pytest.raises(ApprovalConflictError, match="already_decided"):
            await service.reject(c, staff, done["reference"], "no", NOW)


# -- reject and expire ---------------------------------------------------------------------------------------


async def test_reject_frees_the_hold_and_keeps_the_note_internal(pool: TxPool, staff: uuid.UUID) -> None:
    queued = await queue(pool, REFUND)
    ref = queued["reference"]
    note = "Third claim this quarter; window_count rule"
    async with pool.acquire() as conn:
        assert (await service.reject(conn, staff, ref, note, NOW)).decision == "rejected"
    s = await state(pool, ref)
    assert (s["request"], s["refund"], s["order_status"]) == ("rejected", "rejected", "delivered")
    [message] = await system_messages(pool, queued["conversation_id"])
    assert "window" not in message and "quarter" not in message and find(message) == []
    # the lines are free again (H1): the same refund can be asked for once more
    assert (await queue(pool, REFUND))["status"] == "pending_approval"


async def test_reject_needs_a_note(pool: TxPool, staff: uuid.UUID) -> None:
    ref = (await queue(pool, REFUND))["reference"]
    async with pool.acquire() as conn:
        with pytest.raises(ValueError, match="note"):
            await service.reject(conn, staff, ref, "   ", NOW)
    assert (await state(pool, ref))["decisions"] == 0


@pytest.mark.parametrize("act", ["approve", "reject"])
async def test_a_request_past_48_hours_expires_instead(pool: TxPool, staff: uuid.UUID, act: str) -> None:
    """B7: lazy expiry wins over whatever was asked; nothing pays out."""
    queued = await queue(pool, REFUND)
    ref, later = queued["reference"], NOW + expiry.APPROVAL_TTL
    async with pool.acquire() as conn:
        if act == "approve":
            decided = await service.approve(conn, staff, ref, 5100, "USD", later)
        else:
            decided = await service.reject(conn, staff, ref, "too late", later)
    assert decided.decision == "expired"
    s = await state(pool, ref)
    assert (s["request"], s["refund"]) == ("expired", "rejected")
    audit = await pool.fetchrow(
        "SELECT actor_type, actor_id FROM app.audit_log WHERE event = 'approval.expired'"
    )
    assert dict(audit) == {"actor_type": "system", "actor_id": "approval_expiry"}
    [message] = await system_messages(pool, queued["conversation_id"])
    # The 48-hour figure is never stated (tier C). The message names its own reference, whose sequence digits
    # can contain "48" (ACT-015488, 2026-11-13), so the check runs on the text around it.
    assert ref in message
    assert find(message) == [] and "48" not in message.replace(ref, "")


async def test_a_request_just_inside_48_hours_can_still_be_approved(pool: TxPool, staff: uuid.UUID) -> None:
    ref = (await queue(pool, REFUND))["reference"]
    async with pool.acquire() as conn:
        decided = await service.approve(conn, staff, ref, 5100, "USD", NOW + timedelta(hours=47, minutes=59))
    assert decided.decision == "approved"


async def test_expire_due_closes_only_overdue_requests(pool: TxPool) -> None:
    old = (await queue(pool, REFUND))["reference"]
    await pool.execute(
        "UPDATE app.action_requests SET created_at = created_at - interval '1 hour' WHERE id = $1", old
    )
    fresh = (await queue(pool, CREDIT))["reference"]
    async with pool.acquire() as conn:
        expired = await service.expire_due(conn, NOW + expiry.APPROVAL_TTL - timedelta(minutes=30))
    assert [d.reference for d in expired] == [old]
    assert (await state(pool, fresh))["request"] == "pending_approval"


# -- database guards (A2-P4) and their mutation checks (M37, M38) --------------------------------------------


async def _savepoint_raises(pool: TxPool, sql: str, *args: Any) -> bool:
    """True if `sql` is refused with a check violation (rolled back to a savepoint either way)."""
    tx = pool.connection.transaction()
    await tx.start()
    try:
        await pool.execute(sql, *args)
    except asyncpg.CheckViolationError:
        return True
    finally:
        await tx.rollback()
    return False


async def _forge_request_approved(pool: TxPool, ref: str) -> str:
    return "UPDATE app.action_requests SET status = 'approved', decided_at = now() WHERE id = $1"


async def _forge_with_a_mismatched_decision(pool: TxPool, ref: str) -> str:
    await pool.execute(
        "INSERT INTO app.approvals (action_request_id, decision, decided_by, note, decided_at)"
        " VALUES ($1, 'rejected', (SELECT id FROM app.staff_users LIMIT 1), 'no', now())",
        ref,
    )
    return "UPDATE app.action_requests SET status = 'approved', decided_at = now() WHERE id = $1"


M37_FORGERIES = {"approved without a decision": _forge_request_approved,
                 "approved over a rejection": _forge_with_a_mismatched_decision}  # fmt: skip
M38_FORGERIES = {
    "refund": (REFUND, "UPDATE app.refunds SET status = 'succeeded' WHERE action_request_id = $1"),
    "store credit": (
        CREDIT,
        "UPDATE app.store_credits SET status = 'succeeded' WHERE action_request_id = $1",
    ),
}


@pytest.mark.parametrize("dropped", [False, True], ids=["guarded", "M37-trigger-dropped"])
@pytest.mark.parametrize("forgery", sorted(M37_FORGERIES))
async def test_m37_a_request_moves_only_with_a_matching_decision(
    pool: TxPool, staff: uuid.UUID, forgery: str, dropped: bool
) -> None:
    ref = (await queue(pool, REFUND))["reference"]
    if dropped:
        await pool.execute("DROP TRIGGER action_requests_decision_requires_approval ON app.action_requests")
    sql = await M37_FORGERIES[forgery](pool, ref)
    assert await _savepoint_raises(pool, sql, ref) is not dropped


@pytest.mark.parametrize("dropped", [False, True], ids=["guarded", "M38-trigger-dropped"])
@pytest.mark.parametrize("forgery", sorted(M38_FORGERIES))
async def test_m38_money_pays_out_only_for_an_approved_request(
    pool: TxPool, forgery: str, dropped: bool
) -> None:
    spec, sql = M38_FORGERIES[forgery]
    ref = (await queue(pool, spec))["reference"]
    if dropped:
        await pool.execute("DROP TRIGGER refunds_follow_their_request ON app.refunds")
        await pool.execute("DROP TRIGGER store_credits_follow_their_request ON app.store_credits")
    assert await _savepoint_raises(pool, sql, ref) is not dropped


async def test_decisions_are_append_only_and_need_a_pending_request(pool: TxPool, staff: uuid.UUID) -> None:
    ref = (await queue(pool, REFUND))["reference"]
    async with pool.acquire() as conn:
        await service.reject(conn, staff, ref, "no", NOW)
    for sql in ("UPDATE app.approvals SET decision = 'approved' WHERE action_request_id = $1",
                "DELETE FROM app.approvals WHERE action_request_id = $1"):  # fmt: skip
        tx = pool.connection.transaction()
        await tx.start()
        with pytest.raises(asyncpg.RestrictViolationError, match="append-only"):
            await pool.execute(sql, ref)
        await tx.rollback()
    # a second decision for an already decided request: unique, and refused as not pending
    assert await _savepoint_raises(
        pool,
        "INSERT INTO app.approvals (action_request_id, decision, decided_at) VALUES ($1, 'expired', now())",
        ref,
    )
    # a decided request never moves again, even with a matching decision row
    assert await _savepoint_raises(
        pool, "UPDATE app.action_requests SET status = 'expired' WHERE id = $1", ref
    )


# -- one approval path for every action type (J9; pre-registration 9.5) --------------------------------------


def test_every_action_kind_has_one_approval_path_or_is_never_queued() -> None:
    kinds = set(get_args(ActionKind))
    assert set(service.PATHS) | service.NEVER_QUEUED == kinds
    assert not set(service.PATHS) & service.NEVER_QUEUED


async def pending(pool: TxPool, action: str, order_id: str, **fields: Any) -> str:
    """A queued request of any action type, inserted as the queue does (fraud routing will create these)."""
    customer = await pool.fetchval("SELECT customer_id FROM app.orders WHERE id = $1", order_id)
    req = Request(
        customer_id=customer, conversation_id=None, turn_id=uuid.uuid4(), action=action, order_id=order_id,
        decision="NEEDS_APPROVAL", now=NOW, **fields,
    )  # fmt: skip
    async with pool.acquire() as conn:
        return await insert_request(conn, req)


async def captured(pool: TxPool, order_id: str) -> tuple[int, str]:
    row = await pool.fetchrow(
        "SELECT coalesce(sum(p.amount_cents), 0) AS n, max(o.currency) AS ccy FROM app.orders o"
        " LEFT JOIN app.payments p ON p.order_id = o.id WHERE o.id = $1",
        order_id,
    )
    assert row is not None
    return int(row["n"]), str(row["ccy"])


async def test_an_approved_cancel_runs_the_gateways_cancel_with_its_h2_refund(
    pool: TxPool, staff: uuid.UUID
) -> None:
    paid, ccy = await captured(pool, "ORD-1015")  # paid, not shipped
    ref = await pending(
        pool, "cancel_order", "ORD-1015", amount_cents=paid, currency=ccy, args={"reason": "x"}
    )
    async with pool.acquire() as conn:
        assert (await service.approve(conn, staff, ref, paid, ccy, NOW)).decision == "approved"
        await conn.execute("SET CONSTRAINTS ALL IMMEDIATE")  # I10 consistency, now rather than at commit
    assert await pool.fetchval("SELECT status FROM app.orders WHERE id = 'ORD-1015'") == "cancelled"
    refunds = await pool.fetch(
        "SELECT amount_cents, status FROM app.refunds WHERE action_request_id = $1", ref
    )
    assert [(r["amount_cents"], r["status"]) for r in refunds] == [(paid, "succeeded")]


async def test_a_cancel_whose_refund_changed_fails_its_recheck(pool: TxPool, staff: uuid.UUID) -> None:
    paid, ccy = await captured(pool, "ORD-1015")
    ref = await pending(pool, "cancel_order", "ORD-1015", amount_cents=paid - 1, currency=ccy)
    async with pool.acquire() as conn:
        decided = await service.approve(conn, staff, ref, paid - 1, ccy, NOW)
    assert (decided.decision, decided.reasons) == ("failed_recheck", ("amount_changed",))
    assert await pool.fetchval("SELECT status FROM app.orders WHERE id = 'ORD-1015'") == "paid"


async def test_a_cancel_of_an_order_that_shipped_meanwhile_fails_its_recheck(
    pool: TxPool, staff: uuid.UUID
) -> None:
    ref = await pending(pool, "cancel_order", "ORD-1014")  # packed: not cancellable now
    async with pool.acquire() as conn:
        decided = await service.approve(conn, staff, ref, None, None, NOW)
    assert (decided.decision, decided.reasons) == ("failed_recheck", ("status_not_cancellable",))


async def _address(pool: TxPool, order_id: str) -> dict[str, Any]:
    raw = await pool.fetchval("SELECT shipping_address FROM app.orders WHERE id = $1", order_id)
    return dict(json.loads(raw) if isinstance(raw, str) else raw)


async def test_an_approved_address_change_runs_the_gateways_change(pool: TxPool, staff: uuid.UUID) -> None:
    before = await _address(pool, "ORD-1014")
    after = before | {"line1": "9 New Street"}
    ref = await pending(
        pool, "update_shipping_address", "ORD-1014", args={"new_address": after, "previous_address": before}
    )
    async with pool.acquire() as conn:
        assert (await service.approve(conn, staff, ref, None, None, NOW)).decision == "approved"
    assert await _address(pool, "ORD-1014") == after


@pytest.mark.parametrize("stored", ["changed meanwhile", "missing"])
async def test_an_address_change_onto_a_stale_address_fails_closed(
    pool: TxPool, staff: uuid.UUID, stored: str
) -> None:
    before = await _address(pool, "ORD-1014")
    args: dict[str, Any] = {"new_address": before | {"line1": "9 New Street"}}
    if stored == "changed meanwhile":
        args["previous_address"] = before | {"city": "Elsewhere"}
    ref = await pending(pool, "update_shipping_address", "ORD-1014", args=args)
    async with pool.acquire() as conn:
        decided = await service.approve(conn, staff, ref, None, None, NOW)
    assert (decided.decision, decided.reasons) == ("failed_recheck", ("address_changed",))
    assert await _address(pool, "ORD-1014") == before


async def test_the_contact_tier_has_no_approval_path(pool: TxPool, staff: uuid.UUID) -> None:
    ref = await pending(pool, "create_ticket", "ORD-1014")
    async with pool.acquire() as conn:
        with pytest.raises(ActionFailedError, match="never queued"):
            await service.approve(conn, staff, ref, None, None, NOW)


async def test_queued_money_rows_carry_their_requests_time(pool: TxPool) -> None:
    """Readers apply the expiry predicate to a money row's own created_at; it must be its request's (J8)."""
    await queue(pool, REFUND)
    await queue(pool, CREDIT)
    mismatched = await pool.fetchval(
        """
        SELECT count(*) FROM app.action_requests a
          LEFT JOIN app.refunds r ON r.action_request_id = a.id
          LEFT JOIN app.store_credits c ON c.action_request_id = a.id
         WHERE a.status = 'pending_approval'
           AND coalesce(r.created_at, c.created_at) IS DISTINCT FROM a.created_at
        """
    )
    assert mismatched == 0


async def test_an_expiry_reads_the_same_before_and_after_the_lazy_write(pool: TxPool) -> None:
    """J8: nothing may depend on the expiry write having happened; the card and refund row read the same."""
    queued = await queue(pool, REFUND)
    ref, later = queued["reference"], NOW + expiry.APPROVAL_TTL

    async def seen() -> tuple[str, str]:
        record = await domain_actions.get_action(pool.connection, "CUS-025", ref, later)
        detail = await domain_orders.get_order(pool.connection, "CUS-025", "ORD-1058", later)
        assert record is not None and detail is not None
        return record.state, next(r.status for r in detail.refunds if r.id == queued["refund_id"])

    before = await seen()
    async with pool.acquire() as conn:
        assert [d.reference for d in await service.expire_due(conn, later)] == [ref]
    assert (await state(pool, ref))["refund"] == "rejected"  # stored: the hold is released
    assert before == await seen() == ("closed", "expired")
