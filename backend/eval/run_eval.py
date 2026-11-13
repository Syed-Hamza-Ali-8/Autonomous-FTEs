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

from eval.isolation import carry_trace, store_fingerprint
from eval.models import RecordingModel, ReplayDiverged, ReplayModel
from eval.score import ScenarioScore, WriteSnapshot, score, summarise
from eval.throttle import ThrottledModel, TokenThrottle
from eval.verify_scenarios import FIXTURE, SCENARIOS, Store, fixture_clock, load
from tests.leakcheck import REAL_MODEL_RUN_MAY_GROW, problems, snapshot
from tests.scratch_db import ScratchDatabases
from tollgate.agents_def.runner import ChatTurn, LLMRuntime, run_turn
from tollgate.agents_def.support import PROMPT_VERSION, tool_schema_version
from tollgate.auth.deps import CustomerContext
from tollgate.clock import Clock
from tollgate.config import LLMSettings, SupabaseSettings
from tollgate.db import create_pool
from tollgate.domain import conversations as conv
from tollgate.llm.budget import tokens_used_24h
from tollgate.llm.provider import make_client
from tollgate.policy.disclosure import find

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
            "SELECT model_calls, total_tokens, latency_ms, system_fingerprints FROM app.run_log"
            " WHERE turn_id = ANY($1::uuid[]) ORDER BY started_at",
            turn_ids,
        )
        under = await conn.fetchval(
            "SELECT count(*) FROM app.audit_log"
            " WHERE turn_id = ANY($1::uuid[]) AND event = 'claim_check_under_claim'",
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
        # Completed actions the reply omitted or denied: logged, not scored as a failure (Phase 3).
        "under_claims": int(under),
        # Monitoring (DECISIONS I15), reported, never blocking: replies containing a group-C term (reason
        # code, rule name, internal window or count), and replies naming an amount equal to an internal
        # limit (to review: it may simply be the customer's own amount).
        "internal_terms_in_replies": sum(bool(find(r, ("term",))) for r in replies),
        "limit_amounts_in_replies": sum(bool(find(r, ("limit_amount",))) for r in replies),
        "unsealed_calls": replay.unsealed if replay else 0,
        "drifted_calls": replay.drifted if replay else 0,
        "turns": len(scenario["turns"]),
        "model_calls": sum(r["model_calls"] for r in runs),
        "tokens": sum(r["total_tokens"] for r in runs),
        "latency_ms": sum(r["latency_ms"] for r in runs),
        # One per model call, in order (pre-registration 12.4): shows a provider backend change between runs.
        "system_fingerprints": [fp for r in runs for fp in r["system_fingerprints"]],
        "replies": replies,
        "conversation_id": str(conv_id),
        "turn_ids": [str(t) for t in turn_ids],
    }
    return result, meta


def recorded_ids(run_dir: Path) -> set[str]:
    """Scenarios with a recording to replay. An empty file is a scenario the run never got to (a budget stop
    can leave one behind), not a recording."""
    return {p.stem for p in (run_dir / "recordings").glob("*.jsonl") if p.stat().st_size > 0}


# DECISIONS J5 / Phase 4 pre-registration 5.1, widened by amendment A7-P4: ALL 39 scenarios that passed in the
# Phase 3 gate set (the 26 original write passes, the 5 added at approval, the 8 read-only). If any fails in a
# live Phase 4 run, the run stops at that point and the failure is reported; it continues only on the owner's
# say-so (`--resume`). The aggregate never absorbs a regression.
PHASE3_PASSES = frozenset(
    "a01 a02 a03 a04 a06 a07 a08 p01 p02 p03 p04 p05 p06 p07 p08 d01 d02 d03 d04 d05 d06 e01"
    " m01 m02 m03 m04"  # the 26 (5.1)
    " a09 a10 a11 p09 p10"  # added at approval (H5)
    " r01 r02 r03 r04 r05 r06 r07 r08".split()  # read-only (A7-P4)
)


def only_unasked_contact(result: ScenarioScore) -> bool:
    """Amendment A10-P4: the ONLY deviation is extra, unasked contact-tier actions (tickets, escalations). An
    order- or money-tier action, a wrong amount, a missing expected outcome or reply fact, a leak, an error or
    any unsafe part (a)-(c) is something else."""
    return (
        bool(result.end_state_diff)
        and all(d.startswith("tickets:") for d in result.end_state_diff)
        and bool(result.unsolicited_actions)
        and all(u.startswith("ticket (") for u in result.unsolicited_actions)
        and not (result.missing_facts or result.forbidden_leaks or result.errors)
        and not (result.unsafe_actions or result.unsafe_limits or result.unsafe_decisions)
    )


def transport_failure(row: dict[str, Any], recording: Path) -> bool:
    """DECISIONS J18: the scenario failed with provider_error AND the model produced nothing (zero recorded
    tokens, no model call, no reply, an empty recording). Any scenario where the model produced output never
    qualifies, however badly it scored."""
    return (
        "provider_error" in row["errors"]
        and row["tokens"] == 0
        and row["model_calls"] == 0
        and not row["replies"]
        and (not recording.exists() or recording.read_text().strip() == "")
    )


def take_transport_failures(run_dir: Path, apply: bool = True) -> list[str]:
    """J18: remove each qualifying row from a resumed run's results so it is re-run, once. A scenario already
    re-run is never taken again: its re-run result stands. Each removal (with the removed row) is logged in
    meta.json `queue_changes`; the ids re-run are kept in `transport_reruns`."""
    results_path, meta_path = run_dir / "results.jsonl", run_dir / "meta.json"
    meta = json.loads(meta_path.read_text())
    already = set(meta.get("transport_reruns", []))
    keep, taken = [], []
    for line in results_path.read_text().splitlines():
        row = json.loads(line)
        if row["id"] not in already and transport_failure(row, run_dir / "recordings" / f"{row['id']}.jsonl"):
            taken.append(row["id"])
            meta.setdefault("queue_changes", []).append(
                {
                    "at": datetime.now(UTC).isoformat(),
                    "rerun": row["id"],
                    "why": "transport timeout with 0 tokens (provider_error, no model output); re-run once"
                    " under identical settings, its re-run result stands (DECISIONS J18)",
                    "removed_row": row,
                }
            )
        else:
            keep.append(line)
    if taken and apply:
        meta["transport_reruns"] = sorted(already | set(taken))
        results_path.write_text("".join(f"{line}\n" for line in keep))
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    return taken


def regression(
    scenario_id: str, result: ScenarioScore, args: argparse.Namespace, not_measured: bool = False
) -> str | None:
    """The J5 stop reason, if this live Phase 4 result is a regression against the Phase 3 passes. Since
    A10-P4, a regression whose only cause is an unasked contact-tier action is recorded (the scenario still
    fails) but doesn't stop the run: that cause is identified and reviewed. A J18 re-run that times out again
    is recorded as not measured, not a regression."""
    if args.replay or args.phase < 4 or scenario_id not in PHASE3_PASSES or result.task_success:
        return None
    if only_unasked_contact(result) or not_measured:
        return None
    return (
        f"scenario-level regression: {scenario_id} passed in Phase 3 and fails now ({why(result)}); stopped"
        " under J5. Report it with its cause; continue only on the owner's say-so"
    )


def fits(scenario: dict[str, Any], used: int, budget: int, per_turn: int) -> bool:
    """Whether every turn of `scenario` fits in what is left of the rolling 24h budget (--until-budget)."""
    return used + len(scenario["turns"]) * per_turn <= budget


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
        # Recordings are tied to the tool schemas the model saw (CLAUDE.md). A stale recording is never
        # reused silently: it must be re-recorded, or replayed knowingly with --allow-drift.
        source = json.loads((RUNS / args.replay / "meta.json").read_text())
        recorded_under = source.get("tool_schema_version", "unversioned (before Phase 3)")
        if recorded_under != tool_schema_version() and not args.allow_drift:
            print(
                f"refusing: {args.replay} was recorded under tool schema {recorded_under}, current is"
                f" {tool_schema_version()}; re-record it (keep the old run, labelled) or pass --allow-drift",
                file=sys.stderr,
            )
            return 5
        recorded = recorded_ids(RUNS / args.replay)
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
    reruns: list[str] = []
    if args.rerun_transport_failures:
        if not args.resume or not results_path.exists():
            print("--rerun-transport-failures needs --resume of a run with results", file=sys.stderr)
            return 2
        reruns = take_transport_failures(run_dir, apply=not args.dry_run)
        print(
            f"J18 transport re-runs{' (dry run, nothing removed)' if args.dry_run else ''}:"
            f" {reruns or 'none'}"
        )
    done = (
        {json.loads(line)["id"] for line in results_path.read_text().splitlines()}
        if results_path.exists()
        else set()
    )
    todo = [s for s in chosen if s["id"] not in done]
    if args.first:
        # Owner-requested queue order (e.g. the headline scenarios before the budget runs out). Scenarios
        # are independent (own clone, same seed, pinned clock; I13), so order doesn't affect validity; the
        # change is recorded in the run's meta.json `queue_changes`.
        first = [i for i in args.first.split(",") if i]
        unknown = [i for i in first if i not in {s["id"] for s in todo}]
        if unknown:
            print(f"--first: {unknown} are not left to run in this selection", file=sys.stderr)
            return 2
        todo = sorted(todo, key=lambda s: first.index(s["id"]) if s["id"] in first else len(first))
    # J18 re-runs go first (owner, 2026-11-13: cheap, and the gate target is measured on them); the rest keep
    # their order.
    todo = sorted(todo, key=lambda s: s["id"] not in reruns)

    pool = await create_pool(sb)
    scratch: ScratchDatabases | None = None
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
            if args.until_budget and todo:
                # Multi-day mode: only the next scenario must fit. Every turn still pre-flights against
                # the rolling 24h ledger (runner.run_turn) and the run stops cleanly before a turn that
                # would not fit; resume it after the window rolls.
                need = len(todo[0]["turns"]) * llm_s.llm_turn_token_estimate
                print(
                    f"pre-flight (--until-budget): next scenario needs ~{need};"
                    " the run stops before the budget"
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
        if meta_path.exists():
            # One run, one version (owner, 2026-11-09): a resumed run must use the prompt and tool schemas
            # it started with, or its scenarios would mix versions in one report.
            started = json.loads(meta_path.read_text())
            now_versions = {"prompt_version": PROMPT_VERSION, "tool_schema_version": tool_schema_version()}
            then_versions = {k: started.get(k) for k in now_versions}
            if then_versions != now_versions:
                print(
                    f"refusing to resume {run_id}: it started under {then_versions},"
                    f" current is {now_versions}; start a new run (and re-run its scenarios)"
                    " instead of mixing versions",
                    file=sys.stderr,
                )
                return 6
            if args.first:
                started.setdefault("queue_changes", []).append(
                    {
                        "at": datetime.now(UTC).isoformat(),
                        "first": args.first.split(","),
                        "why": "owner: run the headline scenarios before the budget stops the run; order"
                        " does not affect validity (each scenario has its own clone, seed and pinned clock)",
                    }
                )
                meta_path.write_text(json.dumps(started, indent=2) + "\n")
        else:
            meta_path.write_text(
                json.dumps(
                    {
                        "run_id": run_id,
                        "model": model_name,
                        "prompt_version": PROMPT_VERSION,
                        "tool_schema_version": tool_schema_version(),
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
        scratch = ScratchDatabases(sb.database_url.get_secret_value())
        await scratch.purge_leftovers()  # an interrupted run leaves its clones behind
        await scratch.build_template()
        throttle = TokenThrottle(
            llm_s.llm_tokens_per_minute,
            llm_s.llm_requests_per_minute,
            # carried across runs, so a run's first call sees the previous run's last minute
            window_file=llm_s.llm_budget_ledger.parent / "throttle_window.jsonl",
        )
        base: Model = ThrottledModel(
            OpenAIChatCompletionsModel(model=model_name, openai_client=make_client(llm_s)),
            throttle,
            llm_s.llm_rejected_request_tokens,
        )
        stopped: str | None = None
        seed_fingerprint: str | None = None
        pinned_at = datetime.fromisoformat(fixture["fixture_now"])  # G1: the fixture's instant
        for s in todo:
            if not args.replay and args.until_budget:
                # The WHOLE scenario must fit before it starts: a multi-turn scenario stopped by the per-turn
                # pre-flight halfway through spends tokens on a result that doesn't exist (window two, p06).
                async with pool.acquire() as conn:
                    used = await tokens_used_24h(conn, model_name, llm_s.llm_budget_ledger)
                if not fits(s, used, llm_s.llm_daily_token_budget, llm_s.llm_turn_token_estimate):
                    stopped = (
                        f"budget: {s['id']} needs ~{len(s['turns']) * llm_s.llm_turn_token_estimate} for its"
                        f" {len(s['turns'])} turn(s), {llm_s.llm_daily_token_budget - used} left;"
                        " stopped before starting it"
                    )
                    break
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
                # Clean state per scenario: its own clone of the seeded store; only the trace comes back.
                async with scratch.clone() as scenario_pool:  # schema-identical, local only (guard b)
                    # Guard c: every scenario starts from the same seed, at the same pinned instant.
                    async with scenario_pool.acquire() as c:
                        start = await store_fingerprint(c)
                    seed_fingerprint = seed_fingerprint or start
                    if start != seed_fingerprint:
                        raise StopRun(f"{s['id']}: scenario database does not match the seed; run aborted")
                    if clock.now() != pinned_at:
                        raise StopRun(f"{s['id']}: clock moved from the pinned fixture instant; run aborted")
                    result, meta = await run_scenario(scenario_pool, llm, s, clock, store)
                    async with scenario_pool.acquire() as src, pool.acquire() as dst:
                        await carry_trace(
                            src,
                            dst,
                            uuid.UUID(meta["conversation_id"]),
                            [uuid.UUID(t) for t in meta["turn_ids"]],
                        )
            except (StopRun, ReplayDiverged) as exc:
                stopped = str(exc)
                break
            row = {**result.as_dict(), **meta}
            with results_path.open("a") as f:
                f.write(json.dumps(row) + "\n")
            mark = "PASS" if result.task_success else "FAIL"
            print(
                f"  {s['id']} [{s['category']}] {mark}  tokens={meta['tokens']} calls={meta['model_calls']}"
                + ("" if result.task_success else f"  {why(result)}")
            )
            unmeasured = s["id"] in reruns and transport_failure(
                row, run_dir / "recordings" / f"{s['id']}.jsonl"
            )
            if unmeasured:
                # J18: a second transport failure is NOT MEASURED; the report adjusts the denominator and
                # names the exclusion. Recorded, never silently dropped.
                run_meta = json.loads((run_dir / "meta.json").read_text())
                run_meta.setdefault("not_measured", []).append(
                    {
                        "id": s["id"],
                        "at": datetime.now(UTC).isoformat(),
                        "why": "second transport failure, J18",
                    }
                )
                (run_dir / "meta.json").write_text(json.dumps(run_meta, indent=2) + "\n")
                print(f"  {s['id']} NOT MEASURED: second transport failure (J18)")
            if (stop := regression(s["id"], result, args, not_measured=unmeasured)) is not None:
                stopped = stop
                break

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
            "under_claims",
            "internal_terms_in_replies",
            "limit_amounts_in_replies",
        )
        cost: dict[str, Any] = {k: sum(r.get(k, 0) for r in rows) for k in keys}
        cost["throttle_waited_s"] = round(throttle.waited_s, 1)
        summary = {
            **summarise(all_scores),
            **cost,
            "complete": stopped is None and len(all_scores) == len(chosen),
            # J18: excluded from the task-success denominator in the report, and named there
            "not_measured": [
                n["id"] for n in json.loads((run_dir / "meta.json").read_text()).get("not_measured", [])
            ],
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
        if scratch is not None:
            await scratch.close()
        await pool.close()


def parse(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--phase", type=int, default=2, help="run scenarios whose phase is <= this (default 2)")
    p.add_argument("--subset", action="store_true", help="only the 12-scenario stratified subset")
    p.add_argument("--only", help="comma-separated scenario ids")
    p.add_argument("--record", action="store_true", help="save model outputs for later --replay")
    p.add_argument("--replay", metavar="RUN_ID", help="re-score using a recorded run's outputs (0 tokens)")
    p.add_argument("--resume", metavar="RUN_ID", help="continue an interrupted run")
    p.add_argument(
        "--first", metavar="IDS", help="comma-separated scenarios to run before the rest (recorded)"
    )
    p.add_argument(
        "--rerun-transport-failures",
        action="store_true",
        help="with --resume: re-run, once, scenarios that failed with provider_error and 0 tokens (J18)",
    )
    p.add_argument("--dry-run", action="store_true", help="plan and pre-flight only")
    p.add_argument(
        "--until-budget",
        action="store_true",
        help="run what fits today: per-turn pre-flight stops the run cleanly; resume later",
    )
    p.add_argument(
        "--allow-drift", action="store_true", help="replay even if inputs changed (marked drifted)"
    )
    return p.parse_args(argv)


if __name__ == "__main__":
    sys.exit(asyncio.run(main(parse())))
