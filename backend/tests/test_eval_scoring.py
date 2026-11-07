"""Eval harness: scenarios verify, scoring is state-based, results don't move with the calendar,
and record/replay reproduces a run with zero tokens. Model-free (scripted model), rolled back (C5).
"""

import json
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

    t = TokenThrottle(tokens_per_minute=8_000, requests_per_minute=30, now=lambda: now[0], sleep=fake_sleep)
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
