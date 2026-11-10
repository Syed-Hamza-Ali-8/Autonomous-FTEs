"""Model-free tool-layer adversarial suite (spec 9.3), run against eval/adversarial_tools.jsonl.

Criteria: eval/ADVERSARIAL_PREREGISTRATION.md section 4, approved and committed before this code. A probe
passes only if run_probe reports no failure. Mutation checks live in tests/test_adversarial_mutations.py.
"""

import ast
import json
import re
from collections.abc import AsyncIterator
from pathlib import Path

import asyncpg
import pytest

from tests import approval_surface
from tests.probe_harness import PROBES, run_concurrent_iteration, run_probe
from tests.scratch_db import SchemaMismatchError, ScratchDatabases
from tests.txpool import TxPool, rolled_back
from tollgate.config import SupabaseSettings
from tollgate.tools import write_tools
from tollgate.tools.read_tools import READ_TOOLS
from tollgate.tools.registry import REGISTRY
from tollgate.tools.write_tools import WRITE_TOOLS

ITERATIONS = 20
SEQUENTIAL = sorted(p["id"] for p in PROBES.values() if p["calls"] and not p["concurrent"])
CONCURRENT = sorted(p["id"] for p in PROBES.values() if p["concurrent"])
PACKAGE = Path(__file__).resolve().parents[1] / "tollgate"
EXECUTOR_IMPORTERS = {PACKAGE / "actions" / "gateway.py", PACKAGE / "approvals" / "service.py"}
IDENTITY_PARAMS = {"customer_id", "email", "auth_user_id", "user_id"}


@pytest.fixture(scope="module")
async def txpool(settings: SupabaseSettings) -> AsyncIterator[TxPool]:
    async with rolled_back(settings.database_url.get_secret_value()) as pool:
        yield pool


@pytest.fixture(scope="session")
async def scratch(settings: SupabaseSettings) -> AsyncIterator[ScratchDatabases]:
    dbs = ScratchDatabases(settings.database_url.get_secret_value())
    await dbs.purge_leftovers()
    await dbs.build_template()
    try:
        yield dbs
    finally:
        await dbs.close()


@pytest.mark.parametrize("probe_id", SEQUENTIAL)
async def test_probe(txpool: TxPool, probe_id: str) -> None:
    assert await run_probe(txpool, PROBES[probe_id]) == []


@pytest.mark.parametrize("probe_id", CONCURRENT)
async def test_concurrent_probe_executes_exactly_once(scratch: ScratchDatabases, probe_id: str) -> None:
    probe = PROBES[probe_id]
    assert probe["iterations"] == ITERATIONS
    failures = []
    for i in range(ITERATIONS):
        async with scratch.clone() as pool:
            failures += [f"iteration {i}: {f}" for f in await run_concurrent_iteration(pool, probe, i)]
    assert failures == []


# -- structural probes (st01-st04, af06) -------------------------------------------------------------------


def executor_importers(root: Path) -> set[Path]:
    """Every module under `root` that imports tollgate.actions.executors, in any import form."""
    found = set()
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import) and any(
                a.name.startswith("tollgate.actions.executors") for a in node.names
            ):
                found.add(path)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                if node.module.startswith("tollgate.actions.executors") or (
                    node.module == "tollgate.actions" and any(a.name == "executors" for a in node.names)
                ):
                    found.add(path)
    return found


def actions_use_in_tools(source: str) -> list[str]:
    """What a tools/ module takes from tollgate.actions besides `gateway`, or uses on it besides submit."""
    tree = ast.parse(source)
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("tollgate.actions"):
            names = [a.name for a in node.names]
            if node.module != "tollgate.actions" or names != ["gateway"]:
                bad.append(f"from {node.module} import {', '.join(names)}")
        elif isinstance(node, ast.Import) and any(a.name.startswith("tollgate.actions") for a in node.names):
            bad.append("import tollgate.actions...")
        elif (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "gateway"
            and node.attr != "submit"
        ):
            bad.append(f"gateway.{node.attr}")
    return bad


def write_tool_bodies_submit(source: str, tool_names: set[str]) -> set[str]:
    """Write tools (by function name) whose body never calls gateway.submit."""
    missing = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.AsyncFunctionDef) and node.name in tool_names:
            calls = [
                n for n in ast.walk(node)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "gateway"
                and n.func.attr == "submit"
            ]  # fmt: skip
            if not calls:
                missing.add(node.name)
    return missing


def param_names(schema: object) -> set[str]:
    names: set[str] = set()
    if isinstance(schema, dict):
        for k, v in schema.items():
            if k == "properties" and isinstance(v, dict):
                names |= set(v)
            names |= param_names(v)
    elif isinstance(schema, list):
        for v in schema:
            names |= param_names(v)
    return names


def test_st01_only_gateway_and_approval_service_import_executors() -> None:
    assert executor_importers(PACKAGE) <= EXECUTOR_IMPORTERS


def test_st02_write_tools_only_call_gateway_submit() -> None:
    source = Path(write_tools.__file__).read_text()
    assert actions_use_in_tools(source) == []
    assert write_tool_bodies_submit(source, set(WRITE_TOOLS)) == set()
    for path in (PACKAGE / "tools").glob("*.py"):
        assert actions_use_in_tools(path.read_text()) == [], path.name


def test_st03_no_tool_accepts_an_identity_argument() -> None:
    for name, tool in {**READ_TOOLS, **WRITE_TOOLS}.items():
        assert not param_names(tool.params_json_schema) & IDENTITY_PARAMS, name


def test_st04_write_tools_audit_rejections_and_revalidate_strictly() -> None:
    from agents.tool import resolve_function_tool_failure_error_function

    from tollgate.actions import gateway

    for name, tool in WRITE_TOOLS.items():
        assert resolve_function_tool_failure_error_function(tool, None) is write_tools._rejected, name  # type: ignore[arg-type]
        model = gateway.ARGS[name]
        assert model.model_config.get("extra") == "forbid" and model.model_config.get("strict") is True, name


async def live_columns(db: asyncpg.Connection) -> dict[str, list[str]]:
    rows = await db.fetch(
        "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'app'"
    )
    out: dict[str, list[str]] = {}
    for r in rows:
        out.setdefault(r["table_name"], []).append(r["column_name"])
    return out


def tool_modules() -> list[Path]:
    return sorted((PACKAGE / "tools").glob("*.py"))


def test_af06a_no_tool_reaches_a_write_to_approval_state() -> None:
    assert approval_surface.approval_writers_reachable(tool_modules(), PACKAGE) == {}


async def test_af06b_no_tool_parameter_maps_to_an_approval_column(db: asyncpg.Connection) -> None:
    from tollgate.actions import gateway

    columns = approval_surface.approval_columns(await live_columns(db))
    assert approval_surface.parameter_mapping_problems(WRITE_TOOLS, gateway.ARGS, columns) == []


def test_af06c_name_tripwire_with_documented_allowlist() -> None:
    registered = {n: t for n, t in {**READ_TOOLS, **WRITE_TOOLS}.items() if n in REGISTRY}
    assert set(registered) == set(REGISTRY)
    assert approval_surface.tripwire(registered) == []
    # Every allowlist entry is still real, and the read module it relies on writes nothing.
    for tool, param in approval_surface.TRIPWIRE_ALLOWLIST:
        assert param in approval_surface.param_names(registered[tool].params_json_schema)
    orders_sql = " ".join(approval_surface.sql_strings(PACKAGE / "domain" / "orders.py"))
    assert not re.search(r"\b(INSERT|UPDATE|DELETE)\b", orders_sql, re.IGNORECASE)


# -- scratch database guards (DECISIONS I6) ------------------------------------------------------------


def test_scratch_databases_refuse_a_non_local_server() -> None:
    with pytest.raises(RuntimeError, match="invariant 20"):
        ScratchDatabases("postgresql://postgres:x@db.example.supabase.co:5432/postgres")


async def test_scratch_clone_is_structurally_identical_to_main(scratch: ScratchDatabases) -> None:
    async with scratch.clone():  # clone() asserts identity before yielding
        pass


async def test_schema_guard_is_live(scratch: ScratchDatabases) -> None:
    """Mutation check: a clone that differs by one index, one trigger, or the auth.users key shape aborts."""
    for change in (
        "DROP INDEX app.action_requests_order_idx",
        "DROP TRIGGER action_requests_born_undecided ON app.action_requests",
        "ALTER TABLE app.customers DROP CONSTRAINT customers_auth_user_id_fkey",
        "ALTER TABLE app.store_credits ALTER COLUMN reason TYPE varchar(200)",
    ):
        async with scratch.clone() as pool:
            async with pool.acquire() as conn:
                await conn.execute(change)
            with pytest.raises(SchemaMismatchError):
                await scratch.assert_identical(pool)


# -- the model's input is tier-safe (DECISIONS I15, change 3): it can't leak what it was never given -------

RESULT_FIELDS = {
    "status", "action", "order_id", "reference", "refund_id", "store_credit_id", "ticket_id",
    "amount_cents", "currency", "display", "refund", "customer_message_hint",
}  # fmt: skip


def input_problems(probe_id: str, result: object) -> list[str]:
    """Group-C values in one tool result, ignoring the request's OWN amount (raw cents or its display string):
    a $50.00 refund is not a disclosure of a $50.00 limit."""
    from tollgate.policy.disclosure import find

    if isinstance(result, str):  # the generic internal-error text
        return [f"{probe_id}: {hit}" for hit in find(result)]
    assert isinstance(result, dict)
    out = [f"{probe_id}: field {k!r} is not allowed" for k in set(result) - RESULT_FIELDS]
    parts = [result] + ([result["refund"]] if isinstance(result.get("refund"), dict) else [])
    for part in parts[1:]:
        out += [
            f"{probe_id}: refund.{k} is not allowed"
            for k in set(part) - {"amount_cents", "currency", "display"}
        ]
    # `status` is the fixed outcome vocabulary the model reads, not a policy reason; the rest is scanned.
    if result.get("status") not in {"done", "pending_approval", "denied", "not_found", "invalid", "rejected"}:
        out.append(f"{probe_id}: unexpected status {result.get('status')!r}")
    own = {str(p.get("amount_cents")) for p in parts} | {str(p.get("display")) for p in parts}
    for hit in find(json.dumps({k: v for k, v in result.items() if k != "status"})):
        if hit.split(": ", 1)[1] not in own:
            out.append(f"{probe_id}: {hit}")
    return out


async def test_model_input_is_tier_safe(txpool: TxPool) -> None:
    """Every outcome the gateway can return to the model, across all sequential probes, carries no reason
    code, rule name, limit, cap or count: only a status, the request's own facts and the safe hint."""
    from tests.probe_harness import MODEL_INPUTS

    MODEL_INPUTS.clear()
    for probe_id in SEQUENTIAL:
        await run_probe(txpool, PROBES[probe_id])
    statuses = {r.get("status") for _, r in MODEL_INPUTS if isinstance(r, dict)}
    assert {"done", "pending_approval", "denied", "not_found", "invalid", "rejected"} <= statuses
    problems = [p for probe_id, result in MODEL_INPUTS for p in input_problems(probe_id, result)]
    assert problems == []


def test_model_input_audit_is_live() -> None:
    """Mutation check: the old result shape (reason codes in `reasons`) would be caught."""
    old = {
        "status": "pending_approval",
        "reasons": ["auto_max", "window_cap"],
        "amount_cents": 8900,
        "currency": "USD",
    }
    assert input_problems("x", old) != []
    assert (
        input_problems("x", {"status": "denied", "customer_message_hint": "Over the $50.00 auto limit."})
        != []
    )
