"""Register entries that were implemented but had no test (DECISIONS audit, 2026-11-09)."""

import dataclasses
from collections.abc import AsyncIterator
from datetime import datetime, timedelta

import asyncpg
import pytest

from tollgate.actions import gateway
from tollgate.policy import engine


@pytest.fixture
async def tx(db: asyncpg.Connection) -> AsyncIterator[asyncpg.Connection]:
    t = db.transaction()
    await t.start()
    try:
        yield db
    finally:
        await t.rollback()


async def test_a3_window_counts_across_currencies_but_caps_per_currency(tx: asyncpg.Connection) -> None:
    """A3: amount caps are per currency; the refund COUNT spans currencies."""
    now = datetime.fromisoformat("2026-11-07T12:00:00+00:00")
    customer = "CUS-017"  # a USD customer; give them a PKR order with two recent refunds
    await tx.execute(
        "INSERT INTO app.orders (id, customer_id, status, currency, total_cents, shipping_address, placed_at,"
        " paid_at, delivered_at) VALUES ('ORD-9901', $1, 'partially_refunded', 'PKR', 900000, '{}'::jsonb,"
        " $2, $2, $2)",
        customer,
        now - timedelta(days=10),
    )
    await tx.execute(
        "INSERT INTO app.payments (id, order_id, currency, amount_cents, captured_at)"
        " VALUES ('PAY-9901', 'ORD-9901', 'PKR', 900000, $1)",
        now - timedelta(days=10),
    )
    for i, amount in enumerate((100000, 200000)):
        await tx.execute(
            "INSERT INTO app.refunds (id, order_id, currency, amount_cents, status, source, created_at)"
            " VALUES ($1, 'ORD-9901', 'PKR', $2, 'succeeded', 'historical', $3)",
            f"REF-990{i}",
            amount,
            now - timedelta(days=5),
        )
    since = now - timedelta(days=90)
    usd_count, usd_total = await gateway._window(tx, customer, since, "USD", False)
    pkr_count, pkr_total = await gateway._window(tx, customer, since, "PKR", False)
    assert usd_count == pkr_count  # one count across both currencies
    assert usd_count >= 2
    assert pkr_total - usd_total != 0 and pkr_total >= 300000  # totals are per currency


def test_b8_customer_tier_is_not_a_policy_input() -> None:
    """B8: `gold` has no policy effect in v1: no decision input mentions the tier."""
    assert "tier" not in {f.name for f in dataclasses.fields(engine.MoneyFacts)}
    assert "tier" not in gateway.OWNED_ORDER_SQL


def test_c3_cloud_seed_requires_the_host_typed_back(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import seed_store

    monkeypatch.setattr("builtins.input", lambda _prompt: "wrong-host.example")
    with pytest.raises(SystemExit, match="not confirmed"):
        seed_store.confirm_cloud("https://abcd.supabase.co")


async def test_c3_seed_refuses_a_target_with_data_unless_reset(settings: object) -> None:
    from scripts import seed_store
    from tollgate.config import SupabaseSettings

    dsn = SupabaseSettings().database_url.get_secret_value()
    with pytest.raises(SystemExit, match="refusing: target already has"):
        # guard first: the harmless SQL never runs, because the local store has customers
        await seed_store.apply_sql(dsn, "SELECT 1", reset=False, guard_existing=True)


async def test_f2_every_stored_timestamp_is_timestamptz(db: asyncpg.Connection) -> None:
    """F2 (amended on 2026-11-09): storage is UTC timestamptz everywhere; only display differs by audience."""
    naive = await db.fetch(
        "SELECT table_name, column_name FROM information_schema.columns"
        " WHERE table_schema = 'app' AND data_type = 'timestamp without time zone'"
    )
    assert [(r["table_name"], r["column_name"]) for r in naive] == []
    aware = await db.fetchval(
        "SELECT count(*) FROM information_schema.columns"
        " WHERE table_schema = 'app' AND data_type = 'timestamp with time zone'"
    )
    assert aware > 10  # not vacuous
