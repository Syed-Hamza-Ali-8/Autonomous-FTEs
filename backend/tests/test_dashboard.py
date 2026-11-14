"""The dashboard (spec 13.5; DECISIONS L20; Phase 7 pre-registration item 3): probes db01-db08 and mutations
M69, M70, committed BEFORE the code. Until `tollgate/domain/dashboard.py` exists this module fails at
import, which is its expected state.

Live metrics come from the database and nothing else; eval results come from the run files, in their own
section. With no data a figure is None (an empty state), never a zero that reads like a measurement.
"Resolution rate" is not computed at all: the spec never defined it (L20).
"""

import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from tests.probe_harness import FIXTURE_NOW, call_tool, new_context, new_conversation
from tests.test_approval_service import REFUND, queue
from tests.txpool import TxPool, rolled_back
from tollgate.actions.records import Request, insert_compensation, insert_request
from tollgate.approvals import service
from tollgate.config import SupabaseSettings
from tollgate.domain import dashboard

KETTLE = (
    "CUS-017",
    "request_refund",
    {"order_id": "ORD-1042", "items": ["Electric Kettle 1.7L"], "reason": "broken"},
)
LAMP = (
    "CUS-022",
    "request_refund",
    {"order_id": "ORD-1020", "items": ["Desk Lamp"], "reason": "flickers"},
)  # DENY


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


async def _submit(pool: TxPool, spec: tuple[str, str, dict[str, Any]]) -> dict[str, Any]:
    customer, tool, args = spec
    conn = pool.connection
    ctx = await new_context(conn, pool, customer, uuid.uuid4(), await new_conversation(conn, customer))
    out: dict[str, Any] = await call_tool(ctx, tool, args)
    return out


def _now() -> datetime:
    return datetime.now(
        UTC
    )  # audit rows are stamped by the database clock; the live app's clock is the system's


async def test_db01_each_decision_moves_its_own_24h_count(pool: TxPool) -> None:
    before = await dashboard.action_counts(pool.connection, _now())
    assert (await _submit(pool, KETTLE))["status"] == "done"
    await queue(pool, REFUND)
    assert (await _submit(pool, LAMP))["status"] == "denied"
    after = await dashboard.action_counts(pool.connection, _now())
    assert (
        after.completed - before.completed,
        after.waiting_for_approval - before.waiting_for_approval,
        after.refused - before.refused,
    ) == (1, 1, 1)


async def test_db02_queuing_a_request_raises_approvals_pending(pool: TxPool) -> None:
    before = await dashboard.approvals_pending(pool.connection, FIXTURE_NOW)
    await queue(pool, REFUND)
    assert await dashboard.approvals_pending(pool.connection, FIXTURE_NOW) == before + 1


async def test_db03_a_staff_decision_appears_with_its_exact_duration(pool: TxPool, staff: uuid.UUID) -> None:
    queued = await queue(pool, REFUND)
    decided_at = FIXTURE_NOW + timedelta(minutes=37)
    async with pool.acquire() as conn:
        await service.approve(conn, staff, queued["reference"], 5100, "USD", decided_at)
    durations = await dashboard.decision_durations(pool.connection)
    assert 37 * 60 in [round(d) for d in durations]


async def test_db04_the_live_unsafe_check_reads_zero_on_the_database_as_it_stands(pool: TxPool) -> None:
    """Historical refunds that came with the seed are not actions of this system and are not counted."""
    assert await dashboard.unsafe_live(pool.connection) == []


async def _plant_executed_refund(pool: TxPool, customer: str, order: str, cents: int) -> None:
    """An EXECUTED refund written straight to the database,
    bypassing the gateway: what the check must catch."""
    conn = pool.connection
    req = Request(
        customer_id=customer,
        conversation_id=None,
        turn_id=uuid.uuid4(),
        action="request_refund",
        order_id=order,
        decision="ALLOW",
        now=FIXTURE_NOW,
        amount_cents=cents,
        currency="USD",
    )
    rid = await insert_request(conn, req)
    await insert_compensation(conn, "request_refund", rid, req, "succeeded", "planted")
    # as the executor would, so the plant breaks only what the probe means it to (not I10 as well)
    await conn.execute("UPDATE app.orders SET status = 'partially_refunded' WHERE id = $1", order)


async def db05(pool: TxPool) -> list[str]:
    """An executed refund above the automatic limit, with no approval, is counted (part b)."""
    await _plant_executed_refund(pool, "CUS-025", "ORD-1058", 9000)
    found = await dashboard.unsafe_live(pool.connection)
    return [] if len(found) == 1 and "ORD-1058" in found[0] else [f"db05: {found}"]


async def db06(pool: TxPool) -> list[str]:
    """An executed refund on another customer's order is counted (part a): ORD-1058 belongs to CUS-025."""
    await _plant_executed_refund(pool, "CUS-017", "ORD-1058", 1000)
    found = await dashboard.unsafe_live(pool.connection)
    return [] if any("ORD-1058" in f and "another customer" in f for f in found) else [f"db06: {found}"]


async def _failures(probe: Any, pool: TxPool) -> list[str]:
    async with pool.savepoint():
        try:
            out: list[str] = await probe(pool)
            return out
        except Exception as exc:  # a probe that breaks under a mutation has caught it
            return [f"{type(exc).__name__}: {exc}"]


@pytest.mark.parametrize("probe", [db05, db06], ids=["db05", "db06"])
async def test_probe(pool: TxPool, probe: Any) -> None:
    assert await _failures(probe, pool) == []


def _run(root: Path, name: str, meta: dict[str, Any], summary: dict[str, Any]) -> None:
    (root / name).mkdir()
    (root / name / "meta.json").write_text(json.dumps(meta))
    (root / name / "summary.json").write_text(json.dumps(summary))


def db07(root: Path) -> list[str]:
    """The eval reader lists runs, excludes replays, and returns [] for an empty directory."""
    out = [] if dashboard.eval_runs(root) == [] else ["db07: an empty directory gave runs"]
    summary = {"scenarios": 8, "task_success": 8, "unsafe_total": 0, "complete": True}
    _run(root, "20261114T085006Z", {"replay_of": None, "started_at": "2026-11-14T08:50:06+00:00",
                                    "prompt_version": "support-v4"}, summary)  # fmt: skip
    _run(root, "replay-20261111T184142Z-20261114T084843Z", {"replay_of": "20261111T184142Z",
         "started_at": "2026-11-14T08:48:43+00:00", "prompt_version": "support-v4"}, summary)  # fmt: skip
    runs = dashboard.eval_runs(root)
    if [r.run_id for r in runs] != ["20261114T085006Z"]:
        return [*out, f"db07: runs {[r.run_id for r in runs]}"]
    got = (runs[0].date, runs[0].task_success, runs[0].scenarios)
    return out + ([] if got == ("2026-11-14", 8, 8) else [f"db07: fields {got}"])


def test_db07_the_eval_reader_lists_runs_and_excludes_replays(tmp_path: Path) -> None:
    assert db07(tmp_path) == []


def test_db08_no_data_is_none_never_zero() -> None:
    assert dashboard.median([]) is None
    assert dashboard.percentile([], 95) is None
    assert dashboard.median([3.0, 1.0, 2.0]) == 2.0


# -- mutations -----------------------------------------------------------------------------------------------


async def test_m69_a_live_check_that_finds_nothing_is_caught_by_db05_and_db06(
    pool: TxPool, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def nothing(conn: Any) -> list[str]:
        return []

    monkeypatch.setattr(dashboard, "_unsafe_findings", nothing)
    survivors = [p.__name__ for p in (db05, db06) if not await _failures(p, pool)]
    assert survivors == [], f"M69: {survivors} still pass with the live check silenced"


def test_m70_a_reader_that_includes_replays_is_caught_by_db07(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M70's second killer is dashboard.spec.ts, which reads the API's real list (no replay may appear)."""
    monkeypatch.setattr(dashboard, "_is_replay", lambda name, meta: False)
    assert db07(tmp_path) != [], "M70: db07 still passes when replays are listed"


async def test_db09_replay_turns_are_not_counted_as_replies(pool: TxPool) -> None:
    """Added 2026-11-14, before the fix (correction to pre-registration 3.2): a zero-token replay re-scores
    recorded outputs, so its turns are not replies to anyone and must not enter reply latency."""
    now = _now()
    before = await dashboard.reply_latencies(pool.connection, now)
    conn = pool.connection
    conv = await new_conversation(conn, "CUS-017")
    for model, ms in (("replay:openai/gpt-oss-120b", 50), ("openai/gpt-oss-120b", 4321)):
        await conn.execute(
            "INSERT INTO app.run_log (turn_id, conversation_id, customer_id, agent, prompt_version, model,"
            " status, latency_ms, started_at)"
            " VALUES ($1, $2, 'CUS-017', 'support', 'support-v4', $3, 'ok', $4, $5)",
            uuid.uuid4(), conv, model, ms, now - timedelta(minutes=5),
        )  # fmt: skip
    after = await dashboard.reply_latencies(pool.connection, now)
    assert sorted(after) == sorted([*before, 4321.0]), "only the real-model turn is a reply"
