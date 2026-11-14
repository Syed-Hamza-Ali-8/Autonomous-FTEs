"""Rolling 24h token accounting per model (spec Section 2.3; invariant 18).

Spend is read from app.run_log AND from an append-only local ledger file, and the pre-flight uses the
HIGHER of the two: `supabase db reset` wipes run_log, while the provider's real usage does not.
The ledger lives outside the database and is git-ignored. Both use real time on purpose: provider
limits run on the wall clock, not on the eval's pinned clock (tests/test_clock.py allowlist).
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from tollgate.db import Conn
from tollgate.errors import BudgetExceededError


def record_spend(ledger: Path, model: str, tokens: int) -> None:
    """Append one real run's spend. Never rewritten; one JSON object per line."""
    if tokens <= 0:
        return
    ledger.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"at": datetime.now(UTC).isoformat(), "model": model, "tokens": tokens})
    with ledger.open("a") as f:
        f.write(line + "\n")


def ledger_tokens_24h(ledger: Path, model: str) -> int:
    if not ledger.exists():
        return 0
    since = datetime.now(UTC) - timedelta(hours=24)
    total = 0
    for raw in ledger.read_text().splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        if row["model"] == model and datetime.fromisoformat(row["at"]) > since:
            total += int(row["tokens"])
    return total


async def tokens_used_24h(conn: Conn, model: str, ledger: Path | None = None) -> int:
    used = await conn.fetchval(
        "SELECT coalesce(sum(total_tokens), 0) FROM app.run_log"
        " WHERE model = $1 AND started_at > now() - interval '24 hours'",
        model,
    )
    db_total = int(used)
    return max(db_total, ledger_tokens_24h(ledger, model)) if ledger is not None else db_total


async def preflight(conn: Conn, model: str, daily_budget: int, estimate: int, ledger: Path | None) -> int:
    """Raise BudgetExceededError if this request could push the model past its daily budget."""
    used = await tokens_used_24h(conn, model, ledger)
    if used + estimate > daily_budget:
        raise BudgetExceededError(f"{model}: {used} used + {estimate} estimated > {daily_budget} per 24h")
    return used
