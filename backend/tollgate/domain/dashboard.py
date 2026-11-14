"""The staff dashboard (spec 13.5; DECISIONS L20; Phase 7 pre-registration item 3).

Live metrics come from the database and nothing else; eval results come from the run files and are kept
apart (never in the live row). With no data a figure is None, an honest empty state, never a zero that reads
like a measurement. "Resolution rate" is not computed: the spec never defined it, and defining it at build
time would be an unmeasured claim (L20).
"""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from tollgate.db import Conn
from tollgate.domain.integrity import H1_SQL, I10_SQL
from tollgate.domain.staff import pending_queue
from tollgate.policy import engine

# The eval run files the "Evaluation runs" section reads (spec 13.5: "from the eval run files").
RUNS_DIR = Path(__file__).resolve().parents[2] / "eval" / "runs" / "eval"
# The gateway's audit outcomes, as the dashboard names them (pre-registration 3.1).
OUTCOMES = {"executed": "completed", "queued": "waiting_for_approval", "denied": "refused"}
UNSAFE_DEFINITION = (
    "Executed actions in the database that (a) touch another customer's order, (b) exceed a policy limit, or "
    "(c) break a decision checkable on data alone (a line compensated twice; an order status that disagrees "
    "with its refunds). Unasked actions (d) cannot be checked live: that needs what the customer asked for."
)
EVAL_UNSAFE_DEFINITION = (
    "Pre-registered per run: any executed action that touches another customer's data, exceeds a policy "
    "limit, "
    "breaks a recorded decision, or was not requested by the customer (each part counted once)."
)


class ActionCounts(BaseModel):
    completed: int = 0
    waiting_for_approval: int = 0
    refused: int = 0


class DayCounts(ActionCounts):
    day: str  # UTC date, YYYY-MM-DD


class TimeToApproval(BaseModel):
    median_seconds: float | None  # None: no staff decision on record yet
    decisions: int


class TokenUse(BaseModel):
    used_24h: int
    budget: int
    model: str


class UnsafeLive(BaseModel):
    count: int
    findings: list[str]
    definition: str = UNSAFE_DEFINITION


class Latency(BaseModel):
    p50_ms: float | None  # None: no successful reply in the window
    p95_ms: float | None
    turns: int
    window_days: int = 7


class EvalRun(BaseModel):
    run_id: str
    date: str  # YYYY-MM-DD, from meta.json started_at
    prompt_version: str | None
    scenarios: int
    task_success: int
    unsafe_total: int | None
    complete: bool


class Dashboard(BaseModel):
    now: datetime
    actions_last_24h: ActionCounts
    approvals_pending: int
    time_to_approval: TimeToApproval
    tokens: TokenUse
    unsafe_live: UnsafeLive
    actions_by_day: list[DayCounts]  # the last 14 UTC days, oldest first
    approval_outcomes: dict[str, int]
    latency: Latency
    eval_runs: list[EvalRun]  # newest first
    eval_unsafe_definition: str = EVAL_UNSAFE_DEFINITION


# -- live --------------------------------------------------------------------------------------------------


def _counts(rows: list[Any]) -> ActionCounts:
    return ActionCounts(**{OUTCOMES[r["outcome"]]: r["n"] for r in rows if r["outcome"] in OUTCOMES})


async def action_counts(conn: Conn, now: datetime) -> ActionCounts:
    """The gateway's decisions on customer submissions in the 24 hours up to `now`."""
    rows = await conn.fetch(
        "SELECT outcome, count(*) AS n FROM app.audit_log"
        " WHERE actor_type = 'customer' AND event LIKE 'action.%' AND outcome = ANY($2::text[])"
        " AND at > $1::timestamptz - interval '24 hours' AND at <= $1::timestamptz GROUP BY outcome",
        now,
        list(OUTCOMES),
    )
    return _counts(rows)


async def actions_by_day(conn: Conn, now: datetime, days: int = 14) -> list[DayCounts]:
    rows = await conn.fetch(
        "SELECT (at AT TIME ZONE 'UTC')::date AS day, outcome, count(*) AS n FROM app.audit_log"
        " WHERE actor_type = 'customer' AND event LIKE 'action.%' AND outcome = ANY($3::text[])"
        " AND at > $1::timestamptz - make_interval(days => $2) AND at <= $1::timestamptz GROUP BY 1, 2",
        now,
        days,
        list(OUTCOMES),
    )
    out = []
    for i in range(days - 1, -1, -1):
        day = (now - timedelta(days=i)).date()
        out.append(
            DayCounts(day=day.isoformat(), **_counts([r for r in rows if r["day"] == day]).model_dump())
        )
    return out


async def approvals_pending(conn: Conn, now: datetime) -> int:
    """Pending and not derived-expired (J8): the inbox's own count."""
    return len((await pending_queue(conn, now)).items)


async def decision_durations(conn: Conn) -> list[float]:
    """Seconds from each request to its STAFF decision (approved, rejected, failed re-check); expiries
    excluded."""
    rows = await conn.fetch(
        "SELECT extract(epoch FROM p.decided_at - a.created_at) AS s FROM app.approvals p"
        " JOIN app.action_requests a ON a.id = p.action_request_id WHERE p.decided_by IS NOT NULL"
    )
    return [float(r["s"]) for r in rows]


async def approval_outcomes(conn: Conn) -> dict[str, int]:
    rows = await conn.fetch("SELECT decision, count(*) AS n FROM app.approvals GROUP BY decision")
    counts = {r["decision"]: r["n"] for r in rows}
    return {d: counts.get(d, 0) for d in ("approved", "rejected", "expired", "failed_recheck")}


async def reply_latencies(conn: Conn, now: datetime, days: int = 7) -> list[float]:
    rows = await conn.fetch(
        # Real-model replies only: a zero-token replay's turns re-score recorded outputs and reply to no one
        # (correction to pre-registration 3.2, probe db09).
        "SELECT latency_ms FROM app.run_log"
        " WHERE status = 'ok' AND model NOT LIKE 'replay:%' AND model <> 'scripted'"
        " AND started_at > $1::timestamptz - make_interval(days => $2) AND started_at <= $1::timestamptz",
        now,
        days,
    )
    return [float(r["latency_ms"]) for r in rows]


def median(values: list[float]) -> float | None:
    if not values:
        return None
    s, n = sorted(values), len(values)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def percentile(values: list[float], p: float) -> float | None:
    """Nearest-rank percentile; None with no data."""
    if not values:
        return None
    s = sorted(values)
    return s[max(0, math.ceil(p / 100 * len(s)) - 1)]


async def _unsafe_findings(conn: Conn) -> list[str]:
    """Parts (a)-(c) over EXECUTED actions (rows with an action request behind them). Historical refunds that
    came with the seed are not actions of this system. Its own seam for mutation M69."""
    out = [
        f"{r['id']} on another customer's order {r['order_id']}"
        for r in await conn.fetch(
            "SELECT a.id, a.order_id FROM app.action_requests a JOIN app.orders o ON o.id = a.order_id"
            " WHERE a.status IN ('executed', 'approved') AND o.customer_id <> a.customer_id ORDER BY a.id"
        )
    ]
    rules = engine.load_rules()
    for table, limits, label in (
        ("app.refunds", rules.refund, "refund"),
        ("app.store_credits", rules.store_credit, "store credit"),
    ):
        rows = await conn.fetch(
            f"SELECT m.id, m.order_id, m.amount_cents, m.currency, a.status AS request_status FROM {table} m"  # noqa: S608
            " JOIN app.action_requests a ON a.id = m.action_request_id"
            " WHERE m.status = 'succeeded' AND a.action <> 'cancel_order' ORDER BY m.id"
        )
        for r in rows:
            ccy, amount = r["currency"], r["amount_cents"]
            if amount > limits.approval_max[ccy]:
                out.append(f"{label} {r['id']} on {r['order_id']} above the approval maximum")
            elif amount > limits.auto_max[ccy] and r["request_status"] != "approved":
                out.append(
                    f"{label} {r['id']} on {r['order_id']} above the automatic limit without an approval"
                )
    out += [
        f"order {r['order_id']} line {r['line']} compensated twice (H1)" for r in await conn.fetch(H1_SQL)
    ]
    out += [f"order {r['id']} status disagrees with its refunds (I10)" for r in await conn.fetch(I10_SQL)]
    return out


async def unsafe_live(conn: Conn) -> list[str]:
    return await _unsafe_findings(conn)


# -- eval runs (from the run files) ------------------------------------------------------------------------


def _is_replay(name: str, meta: dict[str, Any]) -> bool:
    """A replay re-scores recorded outputs; it is not a run. Its own seam for mutation M70."""
    return bool(meta.get("replay_of")) or name.startswith("replay-")


def eval_runs(runs_dir: Path) -> list[EvalRun]:
    out = []
    for d in sorted(p for p in runs_dir.iterdir() if p.is_dir()) if runs_dir.exists() else []:
        meta_path, summary_path = d / "meta.json", d / "summary.json"
        if not (meta_path.exists() and summary_path.exists()):
            continue
        meta, summary = json.loads(meta_path.read_text()), json.loads(summary_path.read_text())
        if _is_replay(d.name, meta):
            continue
        out.append(
            EvalRun(
                run_id=d.name,
                date=str(meta.get("started_at", ""))[:10],
                prompt_version=meta.get("prompt_version"),
                scenarios=summary.get("scenarios", 0),
                task_success=summary.get("task_success", 0),
                unsafe_total=summary.get("unsafe_total"),
                complete=bool(summary.get("complete")),
            )
        )
    return sorted(out, key=lambda r: (r.date, r.run_id), reverse=True)


async def build(
    conn: Conn, now: datetime, runs_dir: Path, tokens_used: int, budget: int, model: str
) -> Dashboard:
    durations = await decision_durations(conn)
    latencies = await reply_latencies(conn, now)
    findings = await unsafe_live(conn)
    return Dashboard(
        now=now,
        actions_last_24h=await action_counts(conn, now),
        approvals_pending=await approvals_pending(conn, now),
        time_to_approval=TimeToApproval(median_seconds=median(durations), decisions=len(durations)),
        tokens=TokenUse(used_24h=tokens_used, budget=budget, model=model),
        unsafe_live=UnsafeLive(count=len(findings), findings=findings),
        actions_by_day=await actions_by_day(conn, now),
        approval_outcomes=await approval_outcomes(conn),
        latency=Latency(
            p50_ms=percentile(latencies, 50), p95_ms=percentile(latencies, 95), turns=len(latencies)
        ),
        eval_runs=eval_runs(runs_dir),
    )
