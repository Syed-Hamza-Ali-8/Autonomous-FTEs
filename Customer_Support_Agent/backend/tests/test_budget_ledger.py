"""Token spend survives `supabase db reset` via an append-only ledger (owner item 7, invariant 18)."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import asyncpg
import pytest

from tollgate.errors import BudgetExceededError
from tollgate.llm import budget


def test_ledger_appends_and_sums_the_last_24h(tmp_path: Path) -> None:
    ledger = tmp_path / "spend.jsonl"
    budget.record_spend(ledger, "m", 1200)
    budget.record_spend(ledger, "m", 800)
    budget.record_spend(ledger, "other", 5000)
    budget.record_spend(ledger, "m", 0)  # nothing spent, nothing written
    old = {"at": (datetime.now(UTC) - timedelta(hours=25)).isoformat(), "model": "m", "tokens": 9999}
    with ledger.open("a") as f:
        f.write(json.dumps(old) + "\n")
    assert len(ledger.read_text().splitlines()) == 4
    assert budget.ledger_tokens_24h(ledger, "m") == 2000


async def test_preflight_uses_the_higher_of_db_and_ledger(db: asyncpg.Connection, tmp_path: Path) -> None:
    # The DB knows nothing about this model (as after `supabase db reset`); the ledger remembers.
    ledger = tmp_path / "spend.jsonl"
    budget.record_spend(ledger, "ledger-only-model", 170_000)
    assert await budget.tokens_used_24h(db, "ledger-only-model") == 0
    assert await budget.tokens_used_24h(db, "ledger-only-model", ledger) == 170_000
    with pytest.raises(BudgetExceededError):
        await budget.preflight(db, "ledger-only-model", 180_000, 20_000, ledger)
    assert await budget.preflight(db, "ledger-only-model", 180_000, 5_000, ledger) == 170_000
