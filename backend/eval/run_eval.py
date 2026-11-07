"""Run eval scenarios through the real agent loop and score them by database end state (spec 9.1, 2.3).

  uv run python -m eval.run_eval --dry-run                 # plan + budget pre-flight only
  uv run python -m eval.run_eval --record                  # run phase<=2 scenarios, record model output
  uv run python -m eval.run_eval --subset --record         # the 12-scenario subset (D9)
  uv run python -m eval.run_eval --resume <run_id>         # continue an interrupted run
  uv run python -m eval.run_eval --replay <run_id>         # re-score with recorded outputs, 0 tokens

Time is pinned to the fixture's instant (Clock), so results never depend on the calendar. Every real
run passes a budget pre-flight first; on a per-day rate limit the run stops and can be resumed
(invariant 18). Results: eval/runs/eval/<run_id>/{meta.json,results.jsonl,recordings/}.
"""

import argparse
import asyncio
import hashlib
import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import asyncpg
from agents import Model, OpenAIChatCompletionsModel, set_tracing_disabled

from eval.models import RecordingModel, ReplayDiverged, ReplayModel
from eval.score import ScenarioScore, WriteSnapshot, score, summarise
from eval.throttle import ThrottledModel, TokenThrottle
from eval.verify_scenarios import FIXTURE, SCENARIOS, Store, fixture_clock, load
from tests.leakcheck import REAL_MODEL_RUN_MAY_GROW, problems, snapshot
from tollgate.agents_def.runner import ChatTurn, LLMRuntime, run_turn
from tollgate.agents_def.support import PROMPT_VERSION
from tollgate.auth.deps import CustomerContext
from tollgate.clock import Clock
from tollgate.config import LLMSettings, SupabaseSettings
from tollgate.db import create_pool
from tollgate.domain import conversations as conv
from tollgate.llm.budget import tokens_used_24h
from tollgate.llm.provider import make_client

RUNS = Path(__file__).resolve().parent / "runs" / "eval"
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
MAX_RETRY_AFTER_S = 60.0  # longer waits mean a per-day limit: stop and resume later
MAX_RETRIES = 5  # per-minute limits: keep honouring retry-after this many times per turn


class StopRun(Exception):
    """Stop the whole run (per-day rate limit, replay divergence); finished scenarios are kept."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


async def run_scenario(
    pool: asyncpg.Pool, llm: LLMRuntime, scenario: dict[str, Any], clock: Clock, store: Store
) -> tuple[ScenarioScore, dict[str, Any]]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, email FROM app.customers WHERE id = $1", scenario["customer"]
        )
        if row is None:
            raise StopRun(f"{scenario['id']}: customer {scenario['customer']} not in the database (reseed?)")
        before = await WriteSnapshot.take(conn)
        conv_id = await conv.create_conversation(conn, row["id"], None)
    customer = CustomerContext(
        customer_id=row["id"], auth_user_id=uuid.uuid4(), name=row["name"], email=row["email"]
    )
    owned = conv.OwnedConversation(id=conv_id, order_id=None)

    replies: list[str] = []
    errors: list[str] = []
    turn_ids: list[uuid.UUID] = []
    failed_turn_ids: list[uuid.UUID] = []  # rate-limited attempts that were retried
    recorder = llm.model if isinstance(llm.model, RecordingModel) else None
    if recorder is not None:
        recorder.reset()
    for text in scenario["turns"]:
        for attempt in range(1, MAX_RETRIES + 2):
            retry_after: float | None = None
            attempt_replies: list[str] = []
            attempt_errors: list[str] = []
            turn = ChatTurn(
                customer=customer, conversation=owned, client_message_id=uuid.uuid4(), message=text
            )
            attempt_turn: uuid.UUID | None = None
            async for ev in run_turn(pool, llm, turn, clock):
                data = ev.model_dump()
                if data["type"] == "turn_started":
                    attempt_turn = data["turn_id"]
                    turn_ids.append(data["turn_id"])
                elif data["type"] == "reply":
                    attempt_replies.append(data["text"])
                elif data["type"] == "error":
                    if data["code"] == "rate_limited":
                        ra = data.get("retry_after_s")
                        retry_after = float(ra) if ra is not None else MAX_RETRY_AFTER_S + 1
                    elif data["code"] == "budget_exhausted":
                        raise StopRun("token budget exhausted mid-run; resume after the 24h window rolls")
                    else:
                        attempt_errors.append(data["code"])
            if isinstance(llm.model, ReplayModel) and llm.model.diverged:
                raise StopRun(f"{scenario['id']}: replay diverged: {llm.model.diverged}")
            if retry_after is None:
                if recorder is not None:
                    recorder.commit()
                replies += attempt_replies
                errors += attempt_errors
                break
            if recorder is not None:
                recorder.discard()  # never record a failed attempt
            if attempt_turn is not None:
                failed_turn_ids.append(attempt_turn)
            if retry_after > MAX_RETRY_AFTER_S or attempt > MAX_RETRIES:
                raise StopRun(f"rate limited (retry-after {retry_after}s): resume this run later")
            await asyncio.sleep(retry_after)  # per-minute limit: honour retry-after, then retry

    async with pool.acquire() as conn:
        after = await WriteSnapshot.take(conn)
        runs = await conn.fetch(
            "SELECT model_calls, total_tokens, latency_ms FROM app.run_log WHERE turn_id = ANY($1::uuid[])",
            turn_ids,
        )
        replaced = await conn.fetchval(
            "SELECT count(*) FROM app.audit_log"
            " WHERE turn_id = ANY($1::uuid[]) AND event = 'claim_check_replaced'",
            turn_ids,
        )
        wasted = await conn.fetchval(
            "SELECT coalesce(sum(total_tokens), 0) FROM app.run_log WHERE turn_id = ANY($1::uuid[])",
            failed_turn_ids,
        )
    result = score(scenario, store, before, after, replies, errors, int(replaced))
    replay = llm.model if isinstance(llm.model, ReplayModel) else None
    meta = {
        # Provider-reported tokens of attempts that were rate-limited and retried, plus the over-counted
        # charge per rejected request (owner item 2): visible in every summary.
        "retry_wasted_tokens": int(wasted) + len(failed_turn_ids) * llm.rejected_request_tokens,
        "rejected_requests": len(failed_turn_ids),
        "unsealed_calls": replay.unsealed if replay else 0,
        "drifted_calls": replay.drifted if replay else 0,
        "turns": len(scenario["turns"]),
        "model_calls": sum(r["model_calls"] for r in runs),
        "tokens": sum(r["total_tokens"] for r in runs),
        "latency_ms": sum(r["latency_ms"] for r in runs),
        "replies": replies,
    }
    return result, meta


def why(r: ScenarioScore) -> list[str]:
    return r.end_state_diff + r.missing_facts + r.forbidden_leaks + r.unsafe_actions + r.errors


def select(scenarios: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    chosen = [s for s in scenarios if s["phase"] <= args.phase]
    if args.subset:
        chosen = [s for s in chosen if s["subset"]]
    if args.only:
        chosen = [s for s in chosen if s["id"] in set(args.only.split(","))]
    return chosen


async def main(args: argparse.Namespace) -> int:
    set_tracing_disabled(True)
    sb, llm_s = SupabaseSettings(), LLMSettings()
    if {
        urlsplit(sb.database_url.get_secret_value()).hostname,
        urlsplit(sb.supabase_url).hostname,
    } - LOCAL_HOSTS:
        print("refusing: eval runs only against the local stack", file=sys.stderr)
        return 2
    fixture = json.loads(FIXTURE.read_text())
    clock = fixture_clock(fixture)
    store = Store.load(fixture, clock)
    chosen = select(load(), args)
    if args.replay:  # replay exactly the scenarios the source run recorded, nothing else
        recorded = {p.stem for p in (RUNS / args.replay / "recordings").glob("*.jsonl")}
        chosen = [s for s in chosen if s["id"] in recorded]
    model_name = llm_s.model_strong
    if not model_name:
        print("MODEL_STRONG is not set", file=sys.stderr)
        return 2

    run_id = args.resume or (
        f"replay-{args.replay}-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
        if args.replay
        else f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
    )
    run_dir = RUNS / run_id
    results_path = run_dir / "results.jsonl"
    done = (
        {json.loads(line)["id"] for line in results_path.read_text().splitlines()}
        if results_path.exists()
        else set()
    )
    todo = [s for s in chosen if s["id"] not in done]

    pool = await create_pool(sb)
    try:
        async with pool.acquire() as conn:
            used = await tokens_used_24h(conn, model_name, llm_s.llm_budget_ledger)
        need = sum(len(s["turns"]) for s in todo) * llm_s.llm_turn_token_estimate
        remaining = llm_s.llm_daily_token_budget - used
        print(
            f"run {run_id}: {len(todo)} to run ({len(done)} already done), "
            f"model {model_name}, prompt {PROMPT_VERSION}"
        )
        if args.replay:
            print("pre-flight: replay uses recorded outputs, 0 tokens")
        else:
            print(
                f"pre-flight: ~{need} tokens needed, {remaining} left "
                f"of {llm_s.llm_daily_token_budget} in the last 24h"
            )
            if need > remaining:
                print(
                    "pre-flight FAILED: not enough budget; run --subset, fewer scenarios, or resume later",
                    file=sys.stderr,
                )
                return 4
        if args.dry_run:
            for s in todo:
                print(f"  {s['id']} [{s['category']}] {len(s['turns'])} turn(s)")
            return 0

        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "recordings").mkdir(exist_ok=True)
        meta_path = run_dir / "meta.json"
        if not meta_path.exists():
            meta_path.write_text(
                json.dumps(
                    {
                        "run_id": run_id,
                        "model": model_name,
                        "prompt_version": PROMPT_VERSION,
                        "replay_of": args.replay,
                        "recorded": bool(args.record),
                        "clock": clock.now().isoformat(),
                        "scenarios_sha": sha(SCENARIOS),
                        "fixture_sha": sha(FIXTURE),
                        "selection": {"phase": args.phase, "subset": args.subset, "only": args.only},
                        "started_at": datetime.now(UTC).isoformat(),
                    },
                    indent=2,
                )
                + "\n"
            )

        db_before = await snapshot(sb.database_url.get_secret_value())
        throttle = TokenThrottle(llm_s.llm_tokens_per_minute, llm_s.llm_requests_per_minute)
        base: Model = ThrottledModel(
            OpenAIChatCompletionsModel(model=model_name, openai_client=make_client(llm_s)),
            throttle,
            llm_s.llm_rejected_request_tokens,
        )
        stopped: str | None = None
        for s in todo:
            if args.replay:
                model: Model = ReplayModel(
                    RUNS / args.replay / "recordings" / f"{s['id']}.jsonl", allow_drift=args.allow_drift
                )
                name = f"replay:{model_name}"  # replays never count against the real budget
            else:
                model = (
                    RecordingModel(base, run_dir / "recordings" / f"{s['id']}.jsonl") if args.record else base
                )
                name = model_name
            ledger = None if args.replay else llm_s.llm_budget_ledger  # replays spend nothing
            llm = LLMRuntime(
                model,
                name,
                llm_s.llm_daily_token_budget,
                llm_s.llm_turn_token_estimate,
                ledger,
                llm_s.llm_rejected_request_tokens,
            )
            try:
                result, meta = await run_scenario(pool, llm, s, clock, store)
            except (StopRun, ReplayDiverged) as exc:
                stopped = str(exc)
                break
            with results_path.open("a") as f:
                f.write(json.dumps({**result.as_dict(), **meta}) + "\n")
            mark = "PASS" if result.task_success else "FAIL"
            print(
                f"  {s['id']} [{s['category']}] {mark}  tokens={meta['tokens']} calls={meta['model_calls']}"
                + ("" if result.task_success else f"  {why(result)}")
            )

        leaks = problems(
            db_before, await snapshot(sb.database_url.get_secret_value()), REAL_MODEL_RUN_MAY_GROW
        )
        all_scores = (
            [
                ScenarioScore(
                    **{k: v for k, v in json.loads(line).items() if k in ScenarioScore.__dataclass_fields__}
                )
                for line in results_path.read_text().splitlines()
            ]
            if results_path.exists()
            else []
        )
        rows = (
            [json.loads(line) for line in results_path.read_text().splitlines()]
            if results_path.exists()
            else []
        )
        keys = (
            "tokens",
            "model_calls",
            "retry_wasted_tokens",
            "rejected_requests",
            "unsealed_calls",
            "drifted_calls",
        )
        cost: dict[str, Any] = {k: sum(r.get(k, 0) for r in rows) for k in keys}
        cost["throttle_waited_s"] = round(throttle.waited_s, 1)
        summary = {
            **summarise(all_scores),
            **cost,
            "complete": stopped is None and len(all_scores) == len(chosen),
            "stopped": stopped,
            "leak_check": leaks or "ok",
        }
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2))
        if stopped:
            print(f"STOPPED: {stopped}. Resume with --resume {run_id}", file=sys.stderr)
            return 3
        return 1 if leaks else 0
    finally:
        await pool.close()


def parse(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--phase", type=int, default=2, help="run scenarios whose phase is <= this (default 2)")
    p.add_argument("--subset", action="store_true", help="only the 12-scenario stratified subset")
    p.add_argument("--only", help="comma-separated scenario ids")
    p.add_argument("--record", action="store_true", help="save model outputs for later --replay")
    p.add_argument("--replay", metavar="RUN_ID", help="re-score using a recorded run's outputs (0 tokens)")
    p.add_argument("--resume", metavar="RUN_ID", help="continue an interrupted run")
    p.add_argument("--dry-run", action="store_true", help="plan and pre-flight only")
    p.add_argument(
        "--allow-drift", action="store_true", help="replay even if inputs changed (marked drifted)"
    )
    return p.parse_args(argv)


if __name__ == "__main__":
    sys.exit(asyncio.run(main(parse())))
