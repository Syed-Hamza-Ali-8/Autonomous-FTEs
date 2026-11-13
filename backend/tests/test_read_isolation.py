"""Read isolation: a customer sees only their own data, and a foreign order looks nonexistent.

Invariants 2, 3, 8. Tools are invoked exactly as the Agents SDK would invoke them, with
attacker-chosen arguments, so these results hold no matter what the model asks for.
scripts/mutation_reads.py removes the SQL ownership filters and shows these tests fail.
"""

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any, cast

import asyncpg
import pytest
from agents.tool_context import ToolContext

from tests.probe_harness import FIXTURE_NOW
from tests.txpool import TxPool, rolled_back
from tollgate.auth.deps import CustomerContext
from tollgate.config import SupabaseSettings
from tollgate.domain import orders
from tollgate.tools.context import TurnContext
from tollgate.tools.read_tools import NOT_FOUND, READ_TOOLS

ME, OTHER = "CUS-001", "CUS-002"
ORDER_TOOLS = ("get_order", "get_shipment", "get_refund_history")


@pytest.fixture(scope="module")
async def txpool(settings: SupabaseSettings) -> AsyncIterator[TxPool]:
    """Tool calls are logged through the pool; keep those writes in a rolled-back transaction (C5)."""
    async with rolled_back(settings.database_url.get_secret_value()) as p:
        yield p


@pytest.fixture(scope="module")
def pool(txpool: TxPool) -> asyncpg.Pool:
    return cast(asyncpg.Pool, txpool)


@pytest.fixture(scope="module")
def db(txpool: TxPool) -> asyncpg.Connection:
    """Overrides the session `db` so reads see the tool-call rows written in this transaction."""
    return txpool.connection


@pytest.fixture(autouse=True)
async def _rollback_each_test(txpool: TxPool) -> AsyncIterator[None]:
    async with txpool.savepoint():
        yield


@pytest.fixture(scope="module")
async def ids(db: asyncpg.Connection) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for cid in (ME, OTHER):
        out[cid] = [r["id"] for r in await db.fetch("SELECT id FROM app.orders WHERE customer_id = $1", cid)]
        assert out[cid], f"fixture must give {cid} orders"
    # an order of OTHER that has a shipment and a refund, so a leak would carry real data
    out["other_rich"] = [
        await db.fetchval(
            """SELECT o.id FROM app.orders o JOIN app.shipments s ON s.order_id = o.id
                WHERE o.customer_id = $1 AND EXISTS (SELECT 1 FROM app.refunds r WHERE r.order_id = o.id)
                LIMIT 1""",
            OTHER,
        )
    ]
    assert out["other_rich"][0], "fixture must give CUS-002 a shipped, refunded order"
    return out


def turn(pool: asyncpg.Pool, customer_id: str) -> TurnContext:
    me = CustomerContext(customer_id=customer_id, auth_user_id=uuid.uuid4(), name="t", email="t@example.test")
    return TurnContext(customer=me, pool=pool, conversation_id=uuid.uuid4(), turn_id=uuid.uuid4())


async def invoke(ctx: TurnContext, tool: str, args: dict[str, Any]) -> Any:
    t = READ_TOOLS[tool]
    raw = json.dumps(args)
    return await t.on_invoke_tool(
        ToolContext(ctx, tool_name=tool, tool_call_id="call-1", tool_arguments=raw), raw
    )


# --- domain layer ----------


async def test_list_orders_returns_only_own_orders(db: asyncpg.Connection, ids: dict[str, list[str]]) -> None:
    got = [o.id for o in await orders.list_orders(db, ME)]
    assert sorted(got) == sorted(ids[ME])
    assert not set(got) & set(ids[OTHER])


async def test_get_order_of_other_customer_is_none(db: asyncpg.Connection, ids: dict[str, list[str]]) -> None:
    for oid in ids[OTHER]:
        assert await orders.get_order(db, ME, oid, FIXTURE_NOW) is None
        assert await orders.get_shipment(db, ME, oid) is None
        assert await orders.get_refund_history(db, ME, oid, FIXTURE_NOW) is None


async def test_own_order_is_returned(db: asyncpg.Connection, ids: dict[str, list[str]]) -> None:
    detail = await orders.get_order(db, OTHER, ids["other_rich"][0], FIXTURE_NOW)
    assert detail is not None and detail.shipment is not None and detail.refunds


# --- tools, invoked as the SDK would ----------


@pytest.mark.parametrize("tool", ORDER_TOOLS)
async def test_foreign_missing_and_malformed_orders_look_identical(
    pool: asyncpg.Pool, ids: dict[str, list[str]], tool: str
) -> None:
    ctx = turn(pool, ME)
    foreign = await invoke(ctx, tool, {"order_id": ids["other_rich"][0]})
    missing = await invoke(ctx, tool, {"order_id": "ORD-9999"})
    malformed = await invoke(ctx, tool, {"order_id": "1042; DROP TABLE app.orders"})
    lower = await invoke(ctx, tool, {"order_id": ids["other_rich"][0].lower()})
    assert foreign == missing == malformed == lower == NOT_FOUND


@pytest.mark.parametrize("tool", ORDER_TOOLS)
async def test_every_foreign_order_is_not_found(
    pool: asyncpg.Pool, ids: dict[str, list[str]], tool: str
) -> None:
    ctx = turn(pool, ME)
    for oid in ids[OTHER]:
        assert await invoke(ctx, tool, {"order_id": oid}) == NOT_FOUND, oid


async def test_get_my_orders_lists_only_own(pool: asyncpg.Pool, ids: dict[str, list[str]]) -> None:
    result = await invoke(turn(pool, ME), "get_my_orders", {})
    assert sorted(o["id"] for o in result["orders"]) == sorted(ids[ME])


@pytest.mark.parametrize("tool", (*ORDER_TOOLS, "get_my_orders"))
async def test_injected_customer_id_argument_does_not_switch_identity(
    pool: asyncpg.Pool, ids: dict[str, list[str]], tool: str
) -> None:
    # A model (or attacker) adds customer_id; the strict schema rejects it, and nothing of OTHER's leaks.
    args: dict[str, Any] = {"customer_id": OTHER}
    if tool != "get_my_orders":
        args["order_id"] = ids["other_rich"][0]
    result = await invoke(turn(pool, ME), tool, args)
    text = json.dumps(result, default=str)
    assert not any(oid in text for oid in ids[OTHER] if oid != args.get("order_id"))
    if isinstance(result, dict) and result.get("found") is True:
        assert all(o["id"] in ids[ME] for o in result.get("orders", []))


def test_no_tool_accepts_an_identity_argument() -> None:
    banned = {"customer_id", "customer", "customer_email", "email", "auth_user_id", "user_id"}
    for name, tool in READ_TOOLS.items():
        params = set(tool.params_json_schema.get("properties", {}))
        assert not params & banned, (name, params & banned)
        assert tool.params_json_schema.get("additionalProperties") is False, name


async def test_each_tool_call_is_logged(pool: asyncpg.Pool, db: asyncpg.Connection) -> None:
    ctx = turn(pool, ME)
    await invoke(ctx, "get_order", {"order_id": "ORD-9999"})
    await invoke(ctx, "get_my_orders", {})
    rows = await db.fetch(
        "SELECT tool_name, outcome FROM app.tool_calls WHERE turn_id = $1 ORDER BY id", ctx.turn_id
    )
    assert [(r["tool_name"], r["outcome"]) for r in rows] == [
        ("get_order", "not_found"),
        ("get_my_orders", "ok"),
    ]


async def test_tool_results_carry_display_dates_and_money(
    pool: asyncpg.Pool, ids: dict[str, list[str]]
) -> None:
    # The model never formats dates or money itself (owner UI review item 20).
    result = await invoke(turn(pool, OTHER), "get_order", {"order_id": ids["other_rich"][0]})
    order = result["order"]
    assert order["placed_at_display"] and order["total"]["display"]
    assert all("at_display" in e for e in order["shipment"]["events"])
