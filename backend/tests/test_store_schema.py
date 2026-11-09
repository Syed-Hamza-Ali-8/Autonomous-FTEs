"""Store schema invariants enforced in the database, and seed reproducibility.

Every test runs inside a transaction that is rolled back (DECISIONS C5), so the seeded store is untouched.
"""

import json
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import asyncpg
import pytest

BACKEND = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((BACKEND / "eval" / "fixtures" / "store_seed.json").read_text())


@pytest.fixture
async def tx(db: asyncpg.Connection) -> AsyncIterator[asyncpg.Connection]:
    t = db.transaction()
    await t.start()
    try:
        yield db
    finally:
        await t.rollback()


def test_fixture_and_seed_sql_are_reproducible() -> None:
    for cmd in (["scripts/generate_fixture.py", "--check"], ["scripts/seed_store.py", "write", "--check"]):
        proc = subprocess.run(
            [sys.executable, *cmd], cwd=BACKEND, capture_output=True, text=True, check=False
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr


async def test_seeded_counts_match_fixture(db: asyncpg.Connection) -> None:
    for table in (
        "customers",
        "products",
        "orders",
        "order_items",
        "payments",
        "shipments",
        "refunds",
        "product_reviews",
    ):
        count = await db.fetchval(f"SELECT count(*) FROM app.{table}")  # noqa: S608 - fixed table names
        assert count == len(FIXTURE[table]), table


async def test_seed_refunds_never_exceed_payments(db: asyncpg.Connection) -> None:
    over = await db.fetch(
        """
        SELECT o.id FROM app.orders o
         WHERE (SELECT coalesce(sum(amount_cents), 0) FROM app.refunds r
                 WHERE r.order_id = o.id AND r.status = 'succeeded')
             > (SELECT coalesce(sum(amount_cents), 0) FROM app.payments p WHERE p.order_id = o.id)
        """
    )
    assert over == []


async def _refundable_order(tx: asyncpg.Connection) -> tuple[str, str, int]:
    row = await tx.fetchrow(
        """
        SELECT o.id, o.currency,
               (SELECT sum(amount_cents) FROM app.payments p WHERE p.order_id = o.id)
             - (SELECT coalesce(sum(amount_cents), 0) FROM app.refunds r
                 WHERE r.order_id = o.id AND r.status = 'succeeded') AS remaining
          FROM app.orders o WHERE o.id = 'ORD-1042'
        """
    )
    assert row is not None and row["remaining"] > 0
    return row["id"], row["currency"], row["remaining"]


async def test_trigger_allows_refund_up_to_captured(tx: asyncpg.Connection) -> None:
    order_id, ccy, remaining = await _refundable_order(tx)
    await tx.execute(
        "INSERT INTO app.refunds (id, order_id, currency, amount_cents, status, source)"
        " VALUES ('REF-9001', $1, $2, $3, 'succeeded', 'historical')",
        order_id,
        ccy,
        remaining,
    )


async def test_trigger_rejects_refund_over_captured(tx: asyncpg.Connection) -> None:
    order_id, ccy, remaining = await _refundable_order(tx)
    with pytest.raises(asyncpg.CheckViolationError, match="exceed captured payments"):
        await tx.execute(
            "INSERT INTO app.refunds (id, order_id, currency, amount_cents, status, source)"
            " VALUES ('REF-9002', $1, $2, $3, 'succeeded', 'historical')",
            order_id,
            ccy,
            remaining + 1,
        )


async def test_trigger_rejects_split_refunds_over_captured(tx: asyncpg.Connection) -> None:
    order_id, ccy, remaining = await _refundable_order(tx)
    half = remaining // 2
    for n in (1, 2):
        await tx.execute(
            "INSERT INTO app.refunds (id, order_id, currency, amount_cents, status, source)"
            " VALUES ($1, $2, $3, $4, 'succeeded', 'historical')",
            f"REF-910{n}",
            order_id,
            ccy,
            half,
        )
    with pytest.raises(asyncpg.CheckViolationError):
        await tx.execute(
            "INSERT INTO app.refunds (id, order_id, currency, amount_cents, status, source)"
            " VALUES ('REF-9109', $1, $2, $3, 'succeeded', 'historical')",
            order_id,
            ccy,
            remaining - 2 * half + 1,
        )


async def test_trigger_rejects_update_to_succeeded_over_captured(tx: asyncpg.Connection) -> None:
    order_id, ccy, remaining = await _refundable_order(tx)
    # A pending action refund needs its (Phase 3) action request: the FK makes an orphan impossible.
    await tx.execute(
        "INSERT INTO app.action_requests (id, customer_id, turn_id, action, order_id, amount_cents, currency,"
        " decision, status, created_at)"
        " SELECT 'ACT-9201', customer_id, gen_random_uuid(), 'request_refund', id, $2, currency,"
        " 'NEEDS_APPROVAL', 'pending_approval', now() FROM app.orders WHERE id = $1",
        order_id,
        remaining + 1,
    )
    await tx.execute(
        "INSERT INTO app.refunds (id, order_id, currency, amount_cents, status, source, action_request_id)"
        " VALUES ('REF-9201', $1, $2, $3, 'pending_approval', 'action', 'ACT-9201')",
        order_id,
        ccy,
        remaining + 1,
    )
    with pytest.raises(asyncpg.CheckViolationError):
        await tx.execute("UPDATE app.refunds SET status = 'succeeded' WHERE id = 'REF-9201'")


async def test_action_refund_requires_an_existing_action_request(tx: asyncpg.Connection) -> None:
    order_id, ccy, _ = await _refundable_order(tx)
    with pytest.raises(asyncpg.ForeignKeyViolationError):
        await tx.execute(
            "INSERT INTO app.refunds"
            " (id, order_id, currency, amount_cents, status, source, action_request_id)"
            " VALUES ('REF-9202', $1, $2, 1, 'pending_approval', 'action', 'ACT-NONE')",
            order_id,
            ccy,
        )


async def test_refund_currency_must_match_order(tx: asyncpg.Connection) -> None:
    with pytest.raises(asyncpg.ForeignKeyViolationError):
        await tx.execute(
            "INSERT INTO app.refunds (id, order_id, currency, amount_cents, status, source)"
            " VALUES ('REF-9301', 'ORD-1042', 'PKR', 100, 'succeeded', 'historical')"
        )


async def test_order_item_currency_must_match_product_and_order(tx: asyncpg.Connection) -> None:
    # ORD-1042 is USD; PRD-101 is the PKR SKU of the same kettle.
    with pytest.raises(asyncpg.ForeignKeyViolationError):
        await tx.execute(
            "INSERT INTO app.order_items (order_id, product_id, currency, quantity, unit_price_cents)"
            " VALUES ('ORD-1042', 'PRD-101', 'USD', 1, 100)"
        )


async def test_historical_refund_cannot_carry_action_request(tx: asyncpg.Connection) -> None:
    with pytest.raises(asyncpg.CheckViolationError):
        await tx.execute(
            "INSERT INTO app.refunds"
            " (id, order_id, currency, amount_cents, status, source, action_request_id)"
            " VALUES ('REF-9401', 'ORD-1042', 'USD', 100, 'succeeded', 'historical', 'ACT-1')"
        )


@pytest.mark.parametrize(
    "stmt", ["UPDATE app.payments SET amount_cents = amount_cents + 1", "DELETE FROM app.payments"]
)
async def test_payments_are_append_only(tx: asyncpg.Connection, stmt: str) -> None:
    with pytest.raises(asyncpg.RestrictViolationError, match="append-only"):
        await tx.execute(stmt)


async def _immediate(tx: asyncpg.Connection) -> None:
    """Fire the deferred consistency triggers now (tests roll back, so they never reach a commit)."""
    await tx.execute("SET CONSTRAINTS ALL IMMEDIATE")


async def _succeeded_refund(tx: asyncpg.Connection, order_id: str, ccy: str, amount: int) -> None:
    await tx.execute(
        "INSERT INTO app.refunds (id, order_id, currency, amount_cents, status, source)"
        " VALUES ('REF-9301', $1, $2, $3, 'succeeded', 'historical')",
        order_id,
        ccy,
        amount,
    )


async def test_order_status_must_agree_with_succeeded_refunds(tx: asyncpg.Connection) -> None:
    order_id, ccy, remaining = await _refundable_order(tx)  # delivered, nothing refunded yet
    await _succeeded_refund(tx, order_id, ccy, remaining)  # a full refund, but the status left 'delivered'
    with pytest.raises(asyncpg.CheckViolationError):
        await _immediate(tx)


async def test_order_status_consistency_accepts_the_executors_transitions(tx: asyncpg.Connection) -> None:
    order_id, ccy, remaining = await _refundable_order(tx)
    await _succeeded_refund(tx, order_id, ccy, remaining)
    await tx.execute("UPDATE app.orders SET status = 'refunded' WHERE id = $1", order_id)
    await _immediate(tx)
    with pytest.raises(asyncpg.CheckViolationError):  # refunded in full is not "partially" refunded
        await tx.execute("UPDATE app.orders SET status = 'partially_refunded' WHERE id = $1", order_id)


async def test_order_status_check_is_live(tx: asyncpg.Connection) -> None:
    """Mutation check (invariant 16): without the trigger, the inconsistent refund would commit."""
    await tx.execute("DROP TRIGGER refunds_order_status_consistent ON app.refunds")
    order_id, ccy, remaining = await _refundable_order(tx)
    await _succeeded_refund(tx, order_id, ccy, remaining)
    await _immediate(tx)  # nothing left to object


async def test_action_requests_are_created_undecided(tx: asyncpg.Connection) -> None:
    for status in ("approved", "rejected", "expired"):
        sp = tx.transaction()
        await sp.start()
        with pytest.raises(asyncpg.CheckViolationError):
            await tx.execute(
                "INSERT INTO app.action_requests (customer_id, turn_id, action, order_id, decision, status,"
                " created_at) SELECT customer_id, gen_random_uuid(), 'request_refund', id, 'NEEDS_APPROVAL',"
                " $1, now() FROM app.orders WHERE id = 'ORD-1042'",
                status,
            )
        await sp.rollback()
