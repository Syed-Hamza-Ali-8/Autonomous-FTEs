"""The model-visible field set is explicit and pinned (DECISIONS J11; Phase 4 pre-registration 11.2).

Every read tool is called on every order of every customer, plus a not-found case, and the paths the model
received must EQUAL tollgate/tools/model_visible.py: a field added without updating the list fails, and so
does a listed field that no longer appears. Write tools are checked the same way, over every probe result, in
test_model_input_is_tier_safe (tests/test_adversarial_tools.py).
"""

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
from agents.tool_context import ToolContext

from tests.probe_harness import new_context, new_conversation
from tests.txpool import TxPool, rolled_back
from tollgate.config import SupabaseSettings
from tollgate.tools import model_visible
from tollgate.tools.read_tools import READ_TOOLS
from tollgate.tools.write_tools import WRITE_TOOLS

# Stored fields that must never reach the model through a tool: data it has no need for, or free text nobody
# vets (Phase 6 keeps payloads there as negative controls).
NEVER = ("notes", "notes_injection", "review", "reviews", "email", "customer_id", "auth_user_id", "reasons")


@pytest.fixture(scope="module")
async def pool(settings: SupabaseSettings) -> AsyncIterator[TxPool]:
    async with rolled_back(settings.database_url.get_secret_value()) as p:
        yield p


async def call(ctx: Any, tool: str, args: dict[str, Any]) -> Any:
    raw = json.dumps(args)
    tc = ToolContext(
        context=ctx, tool_name=tool, tool_call_id=f"call_{uuid.uuid4().hex[:8]}", tool_arguments=raw
    )
    out = await READ_TOOLS[tool].on_invoke_tool(tc, raw)
    return json.loads(out) if isinstance(out, str) and out.startswith("{") else out


def visible_problems(observed: dict[str, set[str]], allowed: dict[str, frozenset[str]]) -> list[str]:
    out = []
    for tool, seen in observed.items():
        out += [f"{tool}: {p!r} reaches the model but is not listed" for p in sorted(seen - allowed[tool])]
        out += [f"{tool}: {p!r} is listed but never returned" for p in sorted(allowed[tool] - seen)]
    return out


@pytest.fixture(scope="module")
async def observed(pool: TxPool) -> dict[str, set[str]]:
    seen: dict[str, set[str]] = {t: set() for t in READ_TOOLS}
    conn = pool.connection
    for customer in [r["id"] for r in await conn.fetch("SELECT id FROM app.customers ORDER BY id")]:
        ctx = await new_context(conn, pool, customer, uuid.uuid4(), await new_conversation(conn, customer))
        listed = await call(ctx, "get_my_orders", {"status": None})
        seen["get_my_orders"] |= model_visible.paths(listed)
        for order in listed["orders"]:
            for tool in ("get_order", "get_shipment", "get_refund_history"):
                seen[tool] |= model_visible.paths(await call(ctx, tool, {"order_id": order["id"]}))
        for tool in ("get_order", "get_shipment", "get_refund_history"):
            seen[tool] |= model_visible.paths(await call(ctx, tool, {"order_id": "ORD-9999"}))
    return seen


def test_read_tools_show_the_model_exactly_the_listed_fields(observed: dict[str, set[str]]) -> None:
    assert set(observed) == set(model_visible.READ)
    assert visible_problems(observed, model_visible.READ) == []


def test_every_tool_has_an_entry_and_nothing_unvetted_is_listed() -> None:
    assert set(model_visible.READ) == set(READ_TOOLS)
    assert set(model_visible.WRITE) == set(WRITE_TOOLS)
    for entries in (*model_visible.READ.values(), *model_visible.WRITE.values()):
        for path in entries:
            leaf = path.split(".")[-1].removesuffix("[]")
            assert leaf not in NEVER, path


def test_free_text_fields_are_model_visible_read_fields() -> None:
    """Phase 6 targets (J11) must be fields the model actually receives."""
    every_read = frozenset().union(*model_visible.READ.values())
    assert model_visible.FREE_TEXT <= every_read
    assert {
        "order.shipping_address.line1",
        "order.items[].name",
        "order.refunds[].reason",
    } <= model_visible.FREE_TEXT


def test_the_check_is_live() -> None:
    """Mutation check: a planted field (an order note) and a stale listed one are both caught."""
    observed = {tool: set(paths) for tool, paths in model_visible.READ.items()}
    planted = {**observed, "get_order": observed["get_order"] | {"order.notes"}}
    assert visible_problems(planted, model_visible.READ) == [
        "get_order: 'order.notes' reaches the model but is not listed"
    ]
    stale = {**observed, "get_shipment": observed["get_shipment"] - {"shipment.carrier"}}
    assert visible_problems(stale, model_visible.READ) == [
        "get_shipment: 'shipment.carrier' is listed but never returned"
    ]
