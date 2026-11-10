"""Mutation checks for the adversarial suite (eval/ADVERSARIAL_PREREGISTRATION.md section 6; invariant 16).

Each mutation removes exactly ONE protection from the real code (monkeypatch, undone after the test) and
every probe pre-registered for it must then FAIL. A mutation whose probes all still pass means the suite is
not live.
Concurrent probes count as caught if any of their 20 iterations fails (M7 is a race).
"""

import json
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from agents import RunContextWrapper, function_tool

from tests import approval_surface
from tests.probe_harness import PROBES, run_concurrent_iteration, run_probe
from tests.scratch_db import ScratchDatabases
from tests.test_adversarial_tools import (
    ITERATIONS,
    actions_use_in_tools,
    executor_importers,
    write_tool_bodies_submit,
)
from tests.test_probe_set import PREREGISTERED_KILLS
from tests.txpool import TxPool, rolled_back
from tollgate.actions import executors, gateway, idempotency
from tollgate.config import SupabaseSettings
from tollgate.policy import engine
from tollgate.tools import write_tools

Patch = Callable[[pytest.MonkeyPatch], None]


def m1(mp: pytest.MonkeyPatch) -> None:
    mp.setattr(
        gateway,
        "OWNED_ORDER_SQL",
        gateway.OWNED_ORDER_SQL.replace("customer_id = $2", "$2::text IS NOT NULL"),
    )


def m2(mp: pytest.MonkeyPatch) -> None:
    for fn in ("evaluate_money", "evaluate_cancel", "evaluate_address_change"):
        mp.setattr(engine, fn, lambda *a, **k: engine.Verdict("ALLOW"))


def m3(mp: pytest.MonkeyPatch) -> None:
    async def lookup(*a: Any) -> None:
        return None

    async def record(*a: Any) -> bool:
        return True

    mp.setattr(idempotency, "lookup", lookup)
    mp.setattr(idempotency, "record", record)


def m3b(mp: pytest.MonkeyPatch) -> None:
    """A gateway that caches a DENY under its key (the schema can't store one, so the cache is in memory)."""
    cache: dict[str, dict[str, Any]] = {}
    settle, lookup = gateway._settle, idempotency.lookup

    async def caching_settle(conn: Any, ctx: Any, key: str, out: gateway.Outcome) -> gateway.Outcome:
        if out.outcome == "denied":
            cache[key] = out.result
        return await settle(conn, ctx, key, out)

    async def caching_lookup(conn: Any, key: str, customer_id: str) -> dict[str, Any] | None:
        return cache.get(key) or await lookup(conn, key, customer_id)

    mp.setattr(gateway, "_settle", caching_settle)
    mp.setattr(idempotency, "lookup", caching_lookup)


def m4(mp: pytest.MonkeyPatch) -> None:
    mp.setattr(gateway, "_amount", lambda value, ceiling: value if ceiling is None else ceiling)


def m5(mp: pytest.MonkeyPatch) -> None:
    async def window(*a: Any) -> tuple[int, int]:
        return 0, 0

    mp.setattr(gateway, "_window", window)


def m6(mp: pytest.MonkeyPatch) -> None:
    facts = gateway._order_facts

    async def no_line_rule(*a: Any) -> tuple[int, bool]:
        remainder, _ = await facts(*a)
        return remainder, False

    mp.setattr(gateway, "_order_facts", no_line_rule)


def m7(mp: pytest.MonkeyPatch) -> None:
    mp.setattr(gateway, "OWNED_ORDER_SQL", gateway.OWNED_ORDER_SQL.replace(" FOR UPDATE", ""))


def m8(mp: pytest.MonkeyPatch) -> None:
    def parse(action: str, raw: str) -> Any:  # unknown fields dropped, like the stock SDK
        model, data = gateway.ARGS[action], json.loads(raw)
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if k in model.model_fields}
        return model.model_validate_json(json.dumps(data))

    mp.setattr(gateway, "_parse", parse)


def m8b(mp: pytest.MonkeyPatch) -> None:
    mp.setattr(
        gateway, "_parse", lambda action, raw: gateway.ARGS[action].model_validate_json(raw, strict=False)
    )


def m8c(mp: pytest.MonkeyPatch) -> None:
    """amount_cents typed as a number in BOTH places the integer type lives: the gateway's strict model
    and the tool signature the SDK validates (changing only one leaves the other rejecting 12.5)."""

    class FloatMoneyArgs(gateway.MoneyArgs):
        amount_cents: float | None = None  # type: ignore[assignment]

    for action in ("request_refund", "issue_store_credit"):
        mp.setitem(gateway.ARGS, action, FloatMoneyArgs)

    @function_tool(name_override="request_refund", failure_error_function=write_tools._rejected)
    async def float_refund(
        ctx: RunContextWrapper[Any],
        order_id: str,
        reason: str,
        items: list[str] | None = None,
        amount_cents: float | None = None,
    ) -> dict[str, Any]:
        """Refund."""
        return await gateway.submit(*write_tools._call(ctx))

    mp.setitem(write_tools.WRITE_TOOLS, "request_refund", float_refund)


def m9(mp: pytest.MonkeyPatch) -> None:
    mp.setattr(gateway, "_invalid", lambda args: None)


async def _noop(*a: Any, **k: Any) -> None:
    return None


def m10(mp: pytest.MonkeyPatch) -> None:
    mp.setattr(gateway, "_audit", _noop)
    mp.setattr(gateway, "_audit_rejection", _noop)


def m10b(mp: pytest.MonkeyPatch) -> None:
    mp.setattr(gateway, "_audit_rejection", _noop)


def m13(mp: pytest.MonkeyPatch) -> None:
    mp.setattr(gateway, "_now", lambda ctx: datetime.now(UTC))


def m14(mp: pytest.MonkeyPatch) -> None:
    async def no_refund(*a: Any) -> int:
        return 0

    mp.setattr(gateway, "_cancel_refund", no_refund)


def m16(mp: pytest.MonkeyPatch) -> None:
    load = gateway._load_order

    async def revealing(conn: Any, order_id: str | None, customer_id: str) -> Any:
        row = await load(conn, order_id, customer_id)
        if row is None and await conn.fetchval("SELECT 1 FROM app.orders WHERE id = $1", order_id):
            raise PermissionError("order belongs to another customer")  # answers differently from "missing"
        return row

    mp.setattr(gateway, "_load_order", revealing)


def m17(mp: pytest.MonkeyPatch) -> None:
    mp.setattr(gateway, "_missing_items", lambda lines, names: False)


def m19(mp: pytest.MonkeyPatch) -> None:
    async def no_status(*a: Any) -> None:
        return None

    mp.setattr(executors, "sync_refund_status", no_status)


def m23(mp: pytest.MonkeyPatch) -> None:
    mp.setattr(
        gateway,
        "_merge_address",
        lambda current, given: {f: getattr(given, f) or "" for f in gateway.ADDRESS_FIELDS},  # replace
    )


def m24(mp: pytest.MonkeyPatch) -> None:
    mp.setattr(gateway, "ADDRESS_FLAGS", {})


def m18(mp: pytest.MonkeyPatch) -> None:
    mp.setattr(gateway, "_dedupe", lambda names: list(names))
    mp.setattr(
        gateway,
        "_line_value",
        lambda lines, names: sum(
            r["quantity"] * r["unit_price_cents"] for n in names for r in lines if r["name"] == n
        ),
    )


PATCHES: dict[str, Patch] = {
    "M1": m1, "M2": m2, "M3": m3, "M3b": m3b, "M4": m4, "M5": m5, "M6": m6, "M7": m7, "M8": m8,
    "M8b": m8b, "M8c": m8c, "M9": m9, "M10": m10, "M10b": m10b, "M13": m13, "M14": m14, "M16": m16,
    "M17": m17, "M18": m18, "M19": m19, "M23": m23, "M24": m24,
}  # fmt: skip
WITH_CALLS = " ".join(sorted(p["id"] for p in PROBES.values() if p["calls"]))
KILLS = {
    **PREREGISTERED_KILLS,
    "M10": WITH_CALLS,  # hand-listed rows of section 6
    "M10b": "xc08 xc09 am04 am07 am08 am16 sv17 af02 af03 af04",
}


@pytest.fixture(scope="module")
async def txpool(settings: SupabaseSettings) -> AsyncIterator[TxPool]:
    async with rolled_back(settings.database_url.get_secret_value()) as pool:
        yield pool


@pytest.fixture(scope="module")
async def scratch(settings: SupabaseSettings) -> AsyncIterator[ScratchDatabases]:
    dbs = ScratchDatabases(settings.database_url.get_secret_value())
    await dbs.build_template()
    try:
        yield dbs
    finally:
        await dbs.close()


async def _caught(probe_id: str, txpool: TxPool, scratch: ScratchDatabases) -> bool:
    probe = PROBES[probe_id]
    if not probe["concurrent"]:
        return bool(await run_probe(txpool, probe))
    for i in range(ITERATIONS):
        async with scratch.clone() as pool:
            if await run_concurrent_iteration(pool, probe, i):
                return True
    return False


def test_every_preregistered_mutation_has_a_patch() -> None:
    assert set(PATCHES) == set(KILLS)


@pytest.mark.parametrize("mutant", sorted(PATCHES))
async def test_mutation_makes_its_probes_fail(
    mutant: str, txpool: TxPool, scratch: ScratchDatabases, monkeypatch: pytest.MonkeyPatch
) -> None:
    PATCHES[mutant](monkeypatch)
    survivors = [pid for pid in KILLS[mutant].split() if not await _caught(pid, txpool, scratch)]
    assert survivors == [], f"{mutant}: these probes still pass with the protection removed"


# -- structural mutations (M11, M12): the scanners must flag a planted violation ---------------------------


def test_m11_executor_import_in_a_tool_is_caught(tmp_path: Any) -> None:
    (tmp_path / "tools").mkdir()
    planted = tmp_path / "tools" / "sneaky.py"
    planted.write_text("from tollgate.actions import executors\n")
    assert planted in executor_importers(tmp_path)
    assert actions_use_in_tools("from tollgate.actions.executors import run_money\n") != []
    body = "async def request_refund(ctx):\n    return await executors.run_money(ctx)\n"
    assert write_tool_bodies_submit(body, {"request_refund"}) == {"request_refund"}


def test_m12_a_tool_that_accepts_an_approval_status_is_caught(tmp_path: Any) -> None:
    """Each af06 check must fail on a planted tool that can set an approval's status."""

    # (b): a write tool whose gateway model accepts `status` maps a parameter onto an approval column.
    class StatusArgs(gateway.MoneyArgs):
        status: str

    @function_tool(name_override="request_refund")
    async def refund_with_status(
        ctx: RunContextWrapper[Any],
        order_id: str,
        reason: str,
        status: str,
        items: list[str] | None = None,
        amount_cents: int | None = None,
    ) -> str:
        """Refund."""
        return order_id

    columns = set(approval_surface.DECISION_COLUMNS) | set(approval_surface.REFERENCE_COLUMNS)
    problems = approval_surface.parameter_mapping_problems(
        {"request_refund": refund_with_status}, {"request_refund": StatusArgs}, columns
    )
    assert any("approval column status" in p for p in problems)

    # (a): a tool module that imports, two hops away, code writing an approval decision.
    pkg = tmp_path / "tollgate"
    (pkg / "tools").mkdir(parents=True)
    (pkg / "approvals").mkdir()
    (pkg / "tools" / "sneaky.py").write_text("from tollgate.approvals import helper\n")
    (pkg / "approvals" / "helper.py").write_text("from tollgate.approvals.decide import approve\n")
    (pkg / "approvals" / "decide.py").write_text(
        "SQL = \"UPDATE app.action_requests SET status = 'approved' WHERE id = $1\"\n"
    )
    hits = approval_surface.approval_writers_reachable([pkg / "tools" / "sneaky.py"], pkg)
    assert "tollgate/approvals/decide.py" in hits

    # (c): the name tripwire flags it too, and only allowlisted exceptions pass.
    assert "request_refund(status)" in approval_surface.tripwire({"request_refund": refund_with_status})
