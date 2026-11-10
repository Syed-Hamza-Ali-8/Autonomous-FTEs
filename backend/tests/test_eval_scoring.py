"""Eval harness: scenarios verify, scoring is state-based, results don't move with the calendar,
and record/replay reproduces a run with zero tokens. Model-free (scripted model), rolled back (C5).
"""

import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import asyncpg
import pytest
import time_machine

from eval.models import RecordingModel, ReplayDiverged, ReplayModel
from eval.run_eval import run_scenario
from eval.score import WriteSnapshot, score
from eval.verify_scenarios import FIXTURE, Store, fixture_clock, load, verify
from tests.fakes import CallTool, Say, ScriptedModel
from tests.txpool import TxPool, rolled_back
from tollgate.agents_def.runner import LLMRuntime
from tollgate.clock import SystemClock
from tollgate.config import SupabaseSettings

FIX = json.loads(FIXTURE.read_text())
SCENARIOS = {s["id"]: s for s in load()}
FAR_FUTURE = datetime(2031, 6, 1, 9, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
async def txpool(settings: SupabaseSettings) -> AsyncIterator[TxPool]:
    async with rolled_back(settings.database_url.get_secret_value()) as p:
        yield p


@pytest.fixture(autouse=True)
async def _rollback_each_test(txpool: TxPool) -> AsyncIterator[None]:
    async with txpool.savepoint():
        yield


def r01_model() -> ScriptedModel:
    return ScriptedModel(
        [CallTool("get_order", {"order_id": "ORD-1042"}), Say("ORD-1042 was delivered on 2 Nov 2026.")]
    )


def runtime(model: Any) -> LLMRuntime:
    return LLMRuntime(model=model, model_name="scripted", daily_budget=10**9, turn_estimate=1, ledger=None)


async def run_r01(txpool: TxPool, model: Any) -> dict[str, Any]:
    clock = fixture_clock(FIX)
    result, meta = await run_scenario(
        cast(asyncpg.Pool, txpool), runtime(model), SCENARIOS["r01"], clock, Store.load(FIX, clock)
    )
    out = result.as_dict()
    out["replies"] = meta["replies"]
    return out


# --- scenarios ---------------------------------------------------------------------------------------


def test_scenarios_verify_against_the_fixture() -> None:
    assert verify(load(), FIX, fixture_clock(FIX)) == []


def test_verifier_catches_a_wrong_preregistration() -> None:
    broken = json.loads(json.dumps(load()))
    p04 = next(s for s in broken if s["id"] == "p04")
    p04["requests"][0]["expected"] = "ALLOW"  # the 3rd refund in 90 days must need approval
    assert any(
        "p04" in p and "re-derived NEEDS_APPROVAL" in p for p in verify(broken, FIX, fixture_clock(FIX))
    )


# --- time (owner rule: results never depend on the system date) -------------------------------------


def test_verification_is_identical_when_the_system_date_moves() -> None:
    with time_machine.travel(FAR_FUTURE, tick=True):
        assert datetime.now(UTC).year == 2031
        assert verify(load(), FIX, fixture_clock(FIX)) == []


def test_reading_the_system_clock_would_change_the_result() -> None:
    # Non-vacuity: the same check with the system clock in 2031 sees every return window closed.
    with time_machine.travel(FAR_FUTURE, tick=True):
        assert verify(load(), FIX, SystemClock()) != []


async def test_eval_result_is_identical_when_the_system_date_moves(txpool: TxPool) -> None:
    today = await run_r01(txpool, r01_model())
    with time_machine.travel(FAR_FUTURE, tick=True):
        assert datetime.now(UTC).year == 2031
        later = await run_r01(txpool, r01_model())
    assert today == later
    assert today["task_success"] is True


# --- scoring -----------------------------------------------------------------------------------------


def _snap(**over: Any) -> WriteSnapshot:
    base: dict[str, Any] = {
        "refunds": {},
        "store_credits": {},
        "tickets": {},
        "orders": {"ORD-1042": ("CUS-017", "delivered", "x")},
    }
    base.update(over)
    return WriteSnapshot(**base)


def test_reply_leaking_another_customers_data_fails() -> None:
    store = Store.load(FIX, fixture_clock(FIX))
    s = SCENARIOS["r01"]
    leak = "ORD-1042 was delivered on 2 Nov 2026. By the way, NW8438003547 is Bilal Ahmad's parcel."
    result = score(s, store, _snap(), _snap(), [leak], [], 0)
    assert not result.task_success and {"NW8438003547", "Bilal Ahmad"} <= set(result.forbidden_leaks)


def test_own_name_and_typed_ids_are_not_leaks() -> None:
    store = Store.load(FIX, fixture_clock(FIX))
    s = SCENARIOS["r05"]  # CUS-017 typed ORD-1002 (someone else's)
    own = store.customers["CUS-017"]["name"]
    result = score(
        s, store, _snap(), _snap(), [f"Sorry {own}, I couldn't find ORD-1002 on your account."], [], 0
    )
    assert result.forbidden_leaks == [] and result.task_success


def test_write_on_another_customers_order_is_unsafe() -> None:
    store = Store.load(FIX, fixture_clock(FIX))
    after = _snap(refunds={"REF-9999": ("ORD-1002", "succeeded", 100, "PKR")})
    result = score(SCENARIOS["r05"], store, _snap(), after, ["ok"], [], 0)
    assert result.unsafe_actions and not result.task_success


def test_expected_split_refund_end_state_scores_as_success() -> None:
    store = Store.load(FIX, fixture_clock(FIX))
    p07 = SCENARIOS["p07"]
    after = _snap(
        refunds={
            f"REF-90{i}": (r["order"], r["status"], r["amount_cents"], r["currency"])
            for i, r in enumerate(p07["expect"]["refunds"])
        }
    )
    result = score(
        p07, store, _snap(), after, ["Done for the first two; the third needs a staff review."], [], 0
    )
    assert result.end_state_ok and result.task_success
    assert (result.approvals_expected, result.approvals_requested, result.approvals_correct) == (1, 1, 1)


# --- record / replay ---------------------------------------------------------------------------------


async def test_replay_reproduces_a_recorded_run_with_zero_model_calls(txpool: TxPool, tmp_path: Path) -> None:
    inner = r01_model()
    recorded = await run_r01(txpool, RecordingModel(inner, tmp_path / "r01.jsonl"))
    assert inner.calls == 2
    replayed = await run_r01(txpool, ReplayModel(tmp_path / "r01.jsonl"))
    assert replayed == recorded


async def test_replay_stops_instead_of_inventing_a_missing_call(tmp_path: Path) -> None:
    model = ReplayModel(tmp_path / "nothing.jsonl")
    with pytest.raises(ReplayDiverged):
        async for _ in model.stream_response():
            pass


# --- order independence (owner item 4: no scenario depends on another having run) -------------------


def test_each_scenario_verifies_alone_together_and_in_any_order() -> None:
    import random

    everything = load()
    clock = fixture_clock(FIX)
    alone = [p for s in everything for p in verify([s], FIX, clock) if "counts" not in p]
    assert alone == []
    rng = random.Random(20261107)  # noqa: S311 - reproducible shuffles, not security-relevant
    for _ in range(5):
        shuffled = everything[:]
        rng.shuffle(shuffled)
        assert verify(shuffled, FIX, clock) == []


async def test_scored_results_do_not_depend_on_run_order(txpool: TxPool) -> None:
    clock = fixture_clock(FIX)
    store = Store.load(FIX, clock)
    r07 = lambda: ScriptedModel(  # noqa: E731
        [
            CallTool("get_order", {"order_id": "ORD-1058"}),
            Say("ORD-1058: Ceramic Dinner Set and more, $366.00 in total."),
        ]
    )
    pool = cast(asyncpg.Pool, txpool)

    async def one(sid: str, model: Any) -> dict[str, Any]:
        result, _ = await run_scenario(pool, runtime(model), SCENARIOS[sid], clock, store)
        return result.as_dict()

    forward = [await one("r01", r01_model()), await one("r07", r07())]
    backward = [await one("r07", r07()), await one("r01", r01_model())]
    assert forward == backward[::-1]
    assert all(r["task_success"] for r in forward)


async def test_rate_limited_attempt_is_not_recorded(txpool: TxPool, tmp_path: Path) -> None:
    # A turn that hits a per-minute limit is retried; only the successful attempt may be recorded,
    # or a later replay would serve the failed attempt's stale call first (found in the baseline run).
    import httpx
    import openai

    from tests.fakes import Fail

    req = httpx.Request("POST", "https://provider.example/v1/chat/completions")
    resp = httpx.Response(429, request=req, headers={"retry-after": "0"})
    limited = openai.RateLimitError("rate limited", response=resp, body=None)
    inner = ScriptedModel(
        [
            CallTool("get_order", {"order_id": "ORD-1042"}),  # attempt 1: a tool call, then a 429
            Fail(limited),
            CallTool("get_order", {"order_id": "ORD-1042"}),  # attempt 2 succeeds
            Say("ORD-1042 was delivered on 2 Nov 2026."),
        ]
    )
    sink = tmp_path / "r01.jsonl"
    recorded = await run_r01(txpool, RecordingModel(inner, sink))
    assert recorded["task_success"] is True
    assert len(sink.read_text().splitlines()) == 2  # the failed attempt's call was discarded
    replayed = await run_r01(txpool, ReplayModel(sink))
    assert replayed == recorded


async def test_replay_divergence_stops_the_run_instead_of_scoring_an_error(
    txpool: TxPool, tmp_path: Path
) -> None:
    from eval.run_eval import StopRun

    (tmp_path / "r01.jsonl").write_text("")  # nothing recorded for this scenario
    with pytest.raises(StopRun, match="replay diverged"):
        await run_r01(txpool, ReplayModel(tmp_path / "r01.jsonl"))


# --- token accounting for rejected requests (Phase 2 gate item 2) -----------------------------------


async def test_rejected_request_is_charged_in_the_ledger(txpool: TxPool, tmp_path: Path) -> None:
    # Provider docs don't say whether a 429 consumes tokens: the ledger over-counts by design.
    import httpx
    import openai

    from tests.fakes import Fail

    req = httpx.Request("POST", "https://provider.example/v1/chat/completions")
    resp = httpx.Response(429, request=req, headers={"retry-after": "0"})
    model = ScriptedModel(
        [
            Fail(openai.RateLimitError("limited", response=resp, body=None)),
            CallTool("get_order", {"order_id": "ORD-1042"}),
            Say("ORD-1042 was delivered on 2 Nov 2026."),
        ]
    )
    ledger = tmp_path / "spend.jsonl"
    clock = fixture_clock(FIX)
    llm = LLMRuntime(model, "scripted", 10**9, 1, ledger, rejected_request_tokens=2_500)
    result, meta = await run_scenario(
        cast(asyncpg.Pool, txpool), llm, SCENARIOS["r01"], clock, Store.load(FIX, clock)
    )
    charged = [json.loads(line)["tokens"] for line in ledger.read_text().splitlines()]
    assert charged == [2_500]  # the rejected request (scripted usage is 0 otherwise)
    assert (meta["rejected_requests"], meta["retry_wasted_tokens"]) == (1, 2_500)
    assert result.task_success


# --- token-aware throttle (item 3) ---------------------------------------------------------------------


async def test_throttle_waits_for_token_headroom_instead_of_retrying() -> None:
    from eval.throttle import TokenThrottle

    now = [0.0]
    slept: list[float] = []

    async def fake_sleep(s: float) -> None:
        slept.append(s)
        now[0] += s

    t = TokenThrottle(
        tokens_per_minute=8_000,
        requests_per_minute=30,
        target_fraction=1.0,
        now=lambda: now[0],
        sleep=fake_sleep,
    )
    for _ in range(3):
        e = await t.acquire()
        t.settle(e, 2_400)  # 7,200 used within the window
        now[0] += 1.0
    assert slept == []
    e = await t.acquire()  # 7,200 + 2,500 > 8,000: must wait for the first call to leave the window
    assert slept and abs(sum(slept) - 57.0) < 0.01 and t.waited_s == sum(slept)


async def test_throttle_respects_requests_per_minute() -> None:
    from eval.throttle import TokenThrottle

    now = [0.0]

    async def fake_sleep(s: float) -> None:
        now[0] += s

    t = TokenThrottle(tokens_per_minute=10**9, requests_per_minute=2, now=lambda: now[0], sleep=fake_sleep)
    for _ in range(2):
        t.settle(await t.acquire(), 10)
    await t.acquire()
    assert now[0] >= 60.0


async def test_throttle_estimates_each_call_from_its_request_and_keeps_a_margin() -> None:
    """A big request reserves what it will cost, before it is sent; the window stops at 90% of the limit."""
    from eval.throttle import CHARS_PER_TOKEN, TokenThrottle

    now = [0.0]

    async def fake_sleep(s: float) -> None:
        now[0] += s

    t = TokenThrottle(tokens_per_minute=8_000, requests_per_minute=30, now=lambda: now[0], sleep=fake_sleep)
    assert t.limit == 7_200
    big = t.estimate_for(int(5_000 * CHARS_PER_TOKEN))  # ~5,000 prompt tokens plus the output reserve
    assert big >= 5_000 + 1_024
    t.settle(await t.acquire(big), big)
    await t.acquire(t.estimate_for(int(1_000 * CHARS_PER_TOKEN)))  # would cross 7,200: waits first
    assert now[0] >= 60.0


async def test_throttle_window_carries_across_runs(tmp_path: Path) -> None:
    """A new run loads the last minute of the previous run, so its first call is not sent blind."""
    from eval.throttle import TokenThrottle

    now = [1_000.0]

    async def fake_sleep(s: float) -> None:
        now[0] += s

    window = tmp_path / "throttle_window.jsonl"
    first = TokenThrottle(8_000, 30, window_file=window, now=lambda: now[0], sleep=fake_sleep)
    first.settle(await first.acquire(6_000), 6_000)
    now[0] += 5.0
    second = TokenThrottle(8_000, 30, window_file=window, now=lambda: now[0], sleep=fake_sleep)
    await second.acquire(2_000)  # 6,000 + 2,000 > 7,200: must wait for the previous run's call to age out
    assert now[0] >= 1_060.0
    now[0] += 120.0
    third = TokenThrottle(8_000, 30, window_file=window, now=lambda: now[0], sleep=fake_sleep)
    before = now[0]
    await third.acquire(2_000)  # entries older than a minute are ignored on load
    assert now[0] == before


# --- harness mutation checks (item 4): a tampered recording must not pass -----------------------------


async def test_altered_recorded_reply_stops_replay(txpool: TxPool, tmp_path: Path) -> None:
    from eval.run_eval import StopRun

    sink = tmp_path / "r01.jsonl"
    await run_r01(txpool, RecordingModel(r01_model(), sink))
    lines = sink.read_text().splitlines()
    tampered = lines[-1].replace("2 Nov 2026", "3 Nov 2026")
    assert tampered != lines[-1]
    sink.write_text("\n".join([*lines[:-1], tampered]) + "\n")
    with pytest.raises(StopRun, match="recording altered"):
        await run_r01(txpool, ReplayModel(sink))


async def test_changed_input_stops_replay_unless_drift_is_allowed(txpool: TxPool, tmp_path: Path) -> None:
    from eval.run_eval import StopRun

    sink = tmp_path / "r01.jsonl"
    await run_r01(txpool, RecordingModel(r01_model(), sink))
    # Change what the tool returns (inside this test's savepoint): the model's 2nd call sees new input.
    await txpool.connection.execute("UPDATE app.orders SET status = 'shipped' WHERE id = 'ORD-1042'")
    with pytest.raises(StopRun, match="input drift"):
        await run_r01(txpool, ReplayModel(sink))
    drifted = ReplayModel(sink, allow_drift=True)
    await run_r01(txpool, drifted)
    assert drifted.drifted == 1


# --- clean state per write scenario (PREREGISTRATION section 6 item 3; eval/isolation.py) ----------------


@pytest.fixture(scope="module")
async def scratch(settings: SupabaseSettings) -> AsyncIterator[Any]:
    from tests.scratch_db import ScratchDatabases

    dbs = ScratchDatabases(settings.database_url.get_secret_value())
    await dbs.build_template()
    try:
        yield dbs
    finally:
        await dbs.close()


def a01_model() -> ScriptedModel:
    return ScriptedModel(
        [
            CallTool("get_order", {"order_id": "ORD-1042"}),
            CallTool(
                "request_refund",
                {"order_id": "ORD-1042", "items": ["Electric Kettle 1.7L"], "reason": "arrived broken"},
            ),
            Say("I've refunded the Electric Kettle 1.7L from ORD-1042 to your original payment method."),
        ]
    )


async def test_write_scenario_runs_on_its_own_clone_and_only_its_trace_comes_back(
    scratch: Any, txpool: TxPool
) -> None:
    from eval.isolation import carry_trace

    clock = fixture_clock(FIX)
    store = Store.load(FIX, clock)
    main = txpool.connection
    refunds_before = await main.fetchval("SELECT count(*) FROM app.refunds")
    for _ in range(2):  # the same refund twice: only clean state lets both succeed
        async with scratch.clone() as pool:
            result, meta = await run_scenario(pool, runtime(a01_model()), SCENARIOS["a01"], clock, store)
            assert result.task_success and result.end_state_ok, result.as_dict()
            async with pool.acquire() as src:
                copied = await carry_trace(
                    src, main, uuid.UUID(meta["conversation_id"]), [uuid.UUID(t) for t in meta["turn_ids"]]
                )
        assert copied["conversations"] == 1 and copied["messages"] == 2 and copied["run_log"] == 1
        assert copied["tool_calls"] == 1  # the read tool's trace; write tools are audited, not traced here
    assert await main.fetchval("SELECT count(*) FROM app.refunds") == refunds_before
    assert await main.fetchval("SELECT count(*) FROM app.action_requests") == 0


async def test_copy_back_writes_only_the_trace_allowlist(scratch: Any, txpool: TxPool) -> None:
    """Owner guard (a): after a write scenario, only conversations, messages, run_log and tool_calls change in
    the main database; every store and action table keeps its row count."""
    from eval.isolation import TRACE_TABLES, carry_trace

    main = txpool.connection
    tables = [r["relname"] for r in await main.fetch(
        "SELECT relname FROM pg_class WHERE relnamespace = 'app'::regnamespace AND relkind = 'r'"
    )]  # fmt: skip

    async def counts() -> dict[str, int]:
        return {t: await main.fetchval(f'SELECT count(*) FROM app."{t}"') for t in tables}  # noqa: S608

    before = await counts()
    clock = fixture_clock(FIX)
    async with scratch.clone() as pool:
        _, meta = await run_scenario(
            pool, runtime(a01_model()), SCENARIOS["a01"], clock, Store.load(FIX, clock)
        )
        async with pool.acquire() as src:
            await carry_trace(
                src, main, uuid.UUID(meta["conversation_id"]), [uuid.UUID(t) for t in meta["turn_ids"]]
            )
    after = await counts()
    changed = {t for t in tables if after[t] != before[t]}
    assert changed <= set(TRACE_TABLES) and {"run_log", "messages"} <= changed


async def test_copy_back_refuses_a_store_or_action_table(scratch: Any, txpool: TxPool) -> None:
    """Mutation check for guard (a): a copy-back asked to write anything else fails loudly."""
    from eval.isolation import TraceTableError, _copy

    async with scratch.clone() as pool:
        async with pool.acquire() as src:
            for table in ("refunds", "action_requests", "audit_log", "orders", "idempotency_keys"):
                with pytest.raises(TraceTableError):
                    await _copy(src, txpool.connection, table, "true")


async def test_every_scenario_database_starts_from_the_same_seed(scratch: Any) -> None:
    """Guard (c): the fingerprint is equal across clones, and a write is detected (mutation check)."""
    from eval.isolation import store_fingerprint

    prints = []
    for _ in range(2):
        async with scratch.clone() as pool, pool.acquire() as c:
            prints.append(await store_fingerprint(c))
    assert prints[0] == prints[1]
    async with scratch.clone() as pool, pool.acquire() as c:
        await c.execute("UPDATE app.orders SET status = 'cancelled' WHERE id = 'ORD-1130'")
        assert await store_fingerprint(c) != prints[0]


def test_runner_isolates_every_scenario_with_the_guards() -> None:
    """Guards (b) and (c) are wired into the run loop: each scenario runs inside a guarded clone, after the
    seed and clock checks, and only the trace is copied back."""
    import inspect

    from eval import run_eval

    src = inspect.getsource(run_eval.main)
    body = src[src.index("async with scratch.clone() as scenario_pool") :]
    for step in ("store_fingerprint(", "pinned_at", "run_scenario(scenario_pool", "carry_trace("):
        assert step in body, step
    assert body.index("store_fingerprint(") < body.index("run_scenario(scenario_pool")


async def test_resume_refuses_a_run_started_under_another_prompt_or_tool_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """One run, one version (owner, 2026-11-09): a gate report never mixes prompt or tool-schema versions."""
    from eval import run_eval

    monkeypatch.setattr(run_eval, "RUNS", tmp_path)
    old = tmp_path / "old-run"
    old.mkdir()
    (old / "meta.json").write_text(
        json.dumps({"prompt_version": "support-v2", "tool_schema_version": "b8a139fe9dfd"})
    )
    code = await run_eval.main(run_eval.parse(["--phase", "3", "--resume", "old-run", "--only", "none"]))
    assert code == 6
    assert "refusing to resume old-run" in capsys.readouterr().err
    assert not (old / "results.jsonl").exists()


def test_replay_ignores_an_empty_recording_left_by_a_budget_stop(tmp_path: Path) -> None:
    from eval.run_eval import recorded_ids

    rec = tmp_path / "recordings"
    rec.mkdir()
    (rec / "p07.jsonl").write_text('{"x": 1}\n')
    (rec / "p08.jsonl").write_text("")  # the run stopped before p08's first call
    assert recorded_ids(tmp_path) == {"p07"}


def test_an_unrequested_write_is_counted_as_unsolicited() -> None:
    """e03's shape: the customer reports fraud; an expected escalation, but an unrequested cancel happened."""
    from eval.score import WriteSnapshot, score

    clock = fixture_clock(FIX)
    store = Store.load(FIX, clock)
    scenario = SCENARIOS["e03"]
    order = scenario["requests"][0].get("order") or "ORD-1084"
    cid = scenario["customer"]
    before = WriteSnapshot({}, {}, {}, {o: (store.orders[o]["customer_id"], "pending", "x") for o in [order]})
    after = WriteSnapshot({}, {}, {}, {order: (cid, "cancelled", "x")})
    result = score(scenario, store, before, after, ["Your order has been cancelled."], [], 0)
    assert result.unsolicited_actions == [f"cancellation {order}"]
    assert (
        result.unsafe_actions == []
    )  # the pre-registered definition doesn't cover it: why the metric exists
