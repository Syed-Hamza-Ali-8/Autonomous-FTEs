"""Derived approval expiry: probes ex01-ex12 and mutations M39-M43, M30 (Phase 4 pre-registration section 9;
DECISIONS J8; amendment A3-P4, committed before this code).

A pending request is expired once `now >= created_at + 48h`. Every reader applies that predicate itself,
so an expired request shows as closed, counts toward nothing, blocks nothing and can't be approved, whether
or not the lazy expiry write has happened. Here it never has: every probe queues through the real gateway
with the clock 49 hours (ex02: exactly 48) before `fixture_now`, and acts at `fixture_now` without writing
any expiry.

Each mutation removes the predicate from exactly ONE reader (its seam treats every pending row as live). Every
probe pre-registered for it must then fail; each mutation has at least two (K5).
"""

import dataclasses
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from tests.probe_harness import FIXTURE_NOW, call_tool, new_context, new_conversation
from tests.txpool import TxPool, rolled_back
from tollgate.actions import cards, gateway, hints
from tollgate.approvals import service
from tollgate.clock import FixedClock
from tollgate.config import SupabaseSettings
from tollgate.domain import actions as domain_actions
from tollgate.domain import conversations as domain_conversations
from tollgate.domain import orders as domain_orders
from tollgate.policy.disclosure import find

NOW = FIXTURE_NOW
EXPIRED_AT = NOW - timedelta(hours=49)
NEVER = datetime(1, 1, 1, tzinfo=UTC)  # a cutoff before every row: every pending row counts as live

Spec = tuple[str, str, dict[str, Any]]


def refund(customer: str, order: str, item: str, cents: int | None) -> Spec:
    args = {"order_id": order, "items": [item], "reason": "damaged"}
    return customer, "request_refund", args | ({"amount_cents": cents} if cents is not None else {})


def credit(customer: str, order: str, item: str, cents: int | None) -> Spec:
    args = {"order_id": order, "items": [item], "reason": "goodwill"}
    return customer, "issue_store_credit", args | ({"amount_cents": cents} if cents is not None else {})


CERAMIC_51 = refund("CUS-025", "ORD-1058", "Ceramic Dinner Set", 5100)
CERAMIC_95 = refund("CUS-025", "ORD-1058", "Ceramic Dinner Set", 9500)
BEDSHEET_51 = refund("CUS-025", "ORD-1058", "Cotton Bedsheet Set", 5100)
SPEAKER_40 = refund("CUS-025", "ORD-1058", "Bluetooth Speaker", 4000)
CREDIT_200 = credit("CUS-047", "ORD-1161", "4K Monitor 27in", 20000)
MONITOR_250 = refund("CUS-031", "ORD-1005", "4K Monitor 27in", 25000)  # remainder at the time: $256.20


async def submit(pool: TxPool, spec: Spec, at: datetime) -> dict[str, Any]:
    customer, tool, args = spec
    conn = pool.connection
    ctx = await new_context(conn, pool, customer, uuid.uuid4(), await new_conversation(conn, customer))
    ctx = dataclasses.replace(ctx, clock=FixedClock(at))
    result: dict[str, Any] = await call_tool(ctx, tool, args)
    return result


async def expired(pool: TxPool, spec: Spec, at: datetime = EXPIRED_AT) -> dict[str, Any]:
    """Queue `spec` at `at` (setup): it must be pending, and stays pending in storage."""
    result = await submit(pool, spec, at)
    assert result["status"] == "pending_approval", f"setup: {result}"
    return result


def expect(label: str, got: object, want: object) -> list[str]:
    return [] if got == want else [f"{label}: got {got!r}, expected {want!r}"]


# -- probes: each returns its failures ([] = pass) --------------------------------------------------------


async def ex01(pool: TxPool) -> list[str]:
    ref = (await expired(pool, CERAMIC_51))["reference"]
    record = await domain_actions.get_action(pool.connection, "CUS-025", ref, NOW)
    assert record is not None
    out = expect("state", record.state, "closed") + expect("explanation", record.explanation, hints.CLOSED)
    if "48" in record.explanation or find(record.explanation):
        out.append(f"explanation states an internal control: {record.explanation!r}")
    return out


async def ex02(pool: TxPool) -> list[str]:
    ref = (await expired(pool, CREDIT_200, at=NOW - timedelta(hours=48)))["reference"]  # the boundary
    record = await domain_actions.get_action(pool.connection, "CUS-047", ref, NOW)
    assert record is not None
    return expect("state", record.state, "closed")


async def ex03(pool: TxPool) -> list[str]:
    refund_id = (await expired(pool, CERAMIC_51))["refund_id"]
    detail = await domain_orders.get_order(pool.connection, "CUS-025", "ORD-1058", NOW)
    assert detail is not None
    return expect("refund row", {r.id: r.status for r in detail.refunds}.get(refund_id), "expired")


async def ex04(pool: TxPool) -> list[str]:
    refund_id = (await expired(pool, CERAMIC_51))["refund_id"]
    history = await domain_orders.get_refund_history(pool.connection, "CUS-025", "ORD-1058", NOW)
    assert history is not None
    return expect("refund row", {r.id: r.status for r in history}.get(refund_id), "expired")


async def ex05(pool: TxPool) -> list[str]:
    await expired(pool, CERAMIC_51)
    await expired(pool, BEDSHEET_51)
    return expect("new refund", (await submit(pool, SPEAKER_40, NOW))["status"], "done")


async def ex06(pool: TxPool) -> list[str]:
    await expired(pool, CERAMIC_95)
    return expect("new refund", (await submit(pool, SPEAKER_40, NOW))["status"], "done")


async def ex07(pool: TxPool) -> list[str]:
    await expired(pool, CERAMIC_51)
    return expect("same line again", (await submit(pool, CERAMIC_51, NOW))["status"], "pending_approval")


async def ex08(pool: TxPool) -> list[str]:
    await expired(pool, CERAMIC_51)
    new = credit("CUS-025", "ORD-1058", "Ceramic Dinner Set", 4000)
    return expect("credit on the same line", (await submit(pool, new, NOW))["status"], "done")


async def ex09(pool: TxPool) -> list[str]:
    await expired(pool, MONITOR_250)
    new = refund("CUS-031", "ORD-1005", "Wireless Earbuds", None)
    return expect("new refund", (await submit(pool, new, NOW))["status"], "pending_approval")


async def ex10(pool: TxPool) -> list[str]:
    await expired(pool, MONITOR_250)
    new = credit("CUS-031", "ORD-1005", "Linen Kurta", None)
    return expect("new credit", (await submit(pool, new, NOW))["status"], "pending_approval")


async def _staff(pool: TxPool) -> uuid.UUID:
    staff_id: uuid.UUID = await pool.fetchval(
        "INSERT INTO app.staff_users (name, email, role) VALUES ('Probe Lead', 'probe.lead@example.test',"
        " 'support_lead') RETURNING id"
    )
    return staff_id


async def _paid_out(pool: TxPool, ref: str) -> int:
    n: int = await pool.fetchval(
        "SELECT count(*) FROM app.refunds WHERE action_request_id = $1 AND status = 'succeeded'", ref
    )
    return n


async def ex11(pool: TxPool) -> list[str]:
    ref = (await expired(pool, CERAMIC_51))["reference"]
    async with pool.acquire() as conn:
        decided = await service.approve(conn, await _staff(pool), ref, 5100, "USD", NOW)
    return expect("decision", decided.decision, "expired") + expect("paid out", await _paid_out(pool, ref), 0)


async def ex12(pool: TxPool) -> list[str]:
    ref = (await expired(pool, CERAMIC_51))["reference"]
    async with pool.acquire() as conn:
        decided = await service.reject(conn, await _staff(pool), ref, "not eligible", NOW)
    return expect("decision", decided.decision, "expired")


async def _last_message(pool: TxPool, spec: Spec, at: datetime) -> tuple[str, Any]:
    """Queue `spec` in its own conversation at `at`; return (reference, that conversation's last message)."""
    ref = (await expired(pool, spec, at=at))["reference"]
    customer = spec[0]
    conv = await domain_conversations.latest_conversation(pool.connection, customer, NOW)
    assert conv is not None
    return ref, conv.messages[-1] if conv.messages else None


async def ex13(pool: TxPool) -> list[str]:
    ref, last = await _last_message(pool, CERAMIC_51, EXPIRED_AT)
    want = cards.decided_message("expired", ref, "request_refund")
    return expect("last message", (last.role, last.content) if last else None, ("system", want))


async def ex14(pool: TxPool) -> list[str]:
    ref, last = await _last_message(pool, CREDIT_200, NOW - timedelta(hours=48))  # the boundary
    want = cards.decided_message("expired", ref, "issue_store_credit")
    return expect("last message", (last.role, last.content) if last else None, ("system", want))


PROBES: dict[str, Callable[[TxPool], Awaitable[list[str]]]] = {
    f.__name__: f
    for f in (ex01, ex02, ex03, ex04, ex05, ex06, ex07, ex08, ex09, ex10, ex11, ex12, ex13, ex14)
}


# -- mutations: the predicate removed from exactly one reader (pre-registration 9.4) -----------------------

Patch = Callable[[pytest.MonkeyPatch], None]


def m39(mp: pytest.MonkeyPatch) -> None:  # R1 action record
    mp.setattr(domain_actions, "_closed", lambda status, created_at, now: False)


def m40(mp: pytest.MonkeyPatch) -> None:  # R2 order-detail refund rows
    mp.setattr(domain_orders, "_refund_status", lambda status, created_at, now: status)


def m41(mp: pytest.MonkeyPatch) -> None:  # R3 remainder
    mp.setattr(gateway, "_remainder_live_after", lambda now: NEVER)


def m42(mp: pytest.MonkeyPatch) -> None:  # R4 window
    mp.setattr(gateway, "_window_live_after", lambda now: NEVER)


def m43(mp: pytest.MonkeyPatch) -> None:  # R5 same lines
    mp.setattr(gateway, "_lines_live_after", lambda now: NEVER)


def m44(mp: pytest.MonkeyPatch) -> None:  # R7 the customer's conversation (amendment A6-P4)
    mp.setattr(domain_conversations, "_unannounced_expiries", lambda pending, now: [])


def m30(mp: pytest.MonkeyPatch) -> None:  # R6 decisions (pre-registered as "no expiry check")
    mp.setattr(service, "_due", lambda req, now: False)


KILLS: dict[str, tuple[Patch, tuple[str, ...]]] = {
    "M39": (m39, ("ex01", "ex02")),
    "M40": (m40, ("ex03", "ex04")),
    "M41": (m41, ("ex09", "ex10")),
    "M42": (m42, ("ex05", "ex06")),
    "M43": (m43, ("ex07", "ex08")),
    "M44": (m44, ("ex13", "ex14")),
    "M30": (m30, ("ex11", "ex12")),  # plus ap05 and ap15 with the staff API
}


@pytest.fixture
async def pool(settings: SupabaseSettings) -> AsyncIterator[TxPool]:
    async with rolled_back(settings.database_url.get_secret_value()) as p:
        yield p


async def _failures(probe: str, pool: TxPool) -> list[str]:
    async with pool.savepoint():
        try:
            return await PROBES[probe](pool)
        except Exception as exc:  # a probe that breaks under a mutation has caught it
            return [f"{type(exc).__name__}: {exc}"]


@pytest.mark.parametrize("probe", sorted(PROBES))
async def test_probe(pool: TxPool, probe: str) -> None:
    assert await _failures(probe, pool) == []


@pytest.mark.parametrize("mutant", sorted(KILLS))
async def test_mutation_makes_its_probes_fail(
    pool: TxPool, mutant: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch, probes = KILLS[mutant]
    patch(monkeypatch)
    survivors = [p for p in probes if not await _failures(p, pool)]
    assert survivors == [], f"{mutant}: these probes still pass with the predicate removed"


def test_every_mutation_is_killed_by_at_least_two_probes_and_every_probe_is_used() -> None:
    """K5 for this set, and no probe is orphaned."""
    assert all(len(set(probes)) >= 2 for _, probes in KILLS.values())
    assert {p for _, probes in KILLS.values() for p in probes} == set(PROBES)


async def test_after_the_lazy_write_the_conversation_shows_one_expiry_message(pool: TxPool) -> None:
    """J14: the derived message gives way to the stored one; never both."""
    async with pool.savepoint():
        ref = (await expired(pool, CERAMIC_51))["reference"]
        async with pool.acquire() as conn:
            assert [d.reference for d in await service.expire_due(conn, NOW)] == [ref]
        conv = await domain_conversations.latest_conversation(pool.connection, "CUS-025", NOW)
        assert conv is not None
        notices = [m for m in conv.messages if m.role == "system" and ref in m.content]
        assert len(notices) == 1 and notices[0].id > 0  # the stored row, not the derived one
