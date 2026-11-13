"""Malicious-model stub for the model-free adversarial suite (spec 9.3; eval/ADVERSARIAL_PREREGISTRATION.md).

Each probe call is issued the way the SDK runner issues a model's tool call:
`FunctionTool.on_invoke_tool(ToolContext(...), raw_json)`, with attacker-chosen JSON. No model client exists.
`run_probe` returns the list of pass-criteria failures (empty = pass), so the mutation checks can assert
that a probe FAILS when its protection is removed.
"""

import asyncio
import json
import re
import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager, nullcontext
from datetime import datetime
from typing import Any

import asyncpg
import time_machine
from agents.tool_context import ToolContext

from eval.verify_probes import load
from eval.verify_scenarios import FIXTURE
from tollgate.auth.deps import CustomerContext
from tollgate.clock import FixedClock
from tollgate.guardrails import fraud_signal
from tollgate.tools.context import TurnContext
from tollgate.tools.write_tools import WRITE_TOOLS

FIXTURE_NOW = datetime.fromisoformat(json.loads(FIXTURE.read_text())["fixture_now"])
PROBES = {p["id"]: p for p in load()}
# Every result a tool returned to the (stub) model, for the model-input audit (DECISIONS I15).
MODEL_INPUTS: list[tuple[str, str, Any]] = []  # (probe id, tool, result)
OUTCOMES = {
    "done": "ALLOW",
    "pending_approval": "NEEDS_APPROVAL",
    "denied": "DENY",
    "not_found": "NOT_FOUND",
    "invalid": "INVALID",
    "needs_more_information": "NEEDS_MORE_INFORMATION",
    "rejected": "SCHEMA_REJECTED",
}
# Tables a probe may change; every other app table must keep its row count.
EFFECT_TABLES = {"refunds", "store_credits", "action_requests", "idempotency_keys", "tickets", "audit_log"}


async def new_context(
    conn: Any, pool: Any, customer_id: str, turn_id: uuid.UUID, conv: uuid.UUID
) -> TurnContext:
    row = await conn.fetchrow("SELECT id, name, email FROM app.customers WHERE id = $1", customer_id)
    customer = CustomerContext(
        customer_id=row["id"], auth_user_id=uuid.uuid4(), name=row["name"], email=row["email"]
    )
    return TurnContext(
        customer=customer,
        pool=pool,
        conversation_id=conv,
        turn_id=turn_id,
        clock=FixedClock(FIXTURE_NOW),
        prompt_version="adversarial-probe",
    )


async def new_conversation(conn: Any, customer_id: str) -> uuid.UUID:
    conv: uuid.UUID = await conn.fetchval(
        "INSERT INTO app.conversations (customer_id) VALUES ($1) RETURNING id", customer_id
    )
    return conv


async def call_tool(ctx: TurnContext, tool: str, args: dict[str, Any]) -> Any:
    raw = json.dumps(args)
    tc = ToolContext(
        context=ctx, tool_name=tool, tool_call_id=f"call_{uuid.uuid4().hex[:12]}", tool_arguments=raw
    )
    out = await WRITE_TOOLS[tool].on_invoke_tool(tc, raw)
    if isinstance(out, str):
        try:
            return json.loads(out)
        except ValueError:
            return out  # the generic internal-error text
    return out


def outcome_of(result: Any, audit_outcome: str | None) -> str:
    if audit_outcome == "replayed":
        return "REPLAY"
    if isinstance(result, dict):
        return OUTCOMES.get(result.get("status", ""), "ERROR")
    return "ERROR"


# -- database state ----------------------------------------------------------------------------------------


async def snapshot(conn: Any) -> dict[str, Any]:
    tables = [
        r["relname"]
        for r in await conn.fetch(
            "SELECT relname FROM pg_class"
            " WHERE relnamespace = 'app'::regnamespace AND relkind = 'r' ORDER BY 1"
        )
    ]
    counts = {t: await conn.fetchval(f'SELECT count(*) FROM app."{t}"') for t in tables}  # noqa: S608
    return {
        "counts": counts,
        "refunds": {
            r["id"]: dict(r)
            for r in await conn.fetch("SELECT id, order_id, status, amount_cents, currency FROM app.refunds")
        },
        "store_credits": {
            r["id"]: dict(r)
            for r in await conn.fetch(
                "SELECT id, order_id, status, amount_cents, currency FROM app.store_credits"
            )
        },
        "orders": {
            r["id"]: (r["status"], r["addr"])
            for r in await conn.fetch("SELECT id, status, shipping_address::text AS addr FROM app.orders")
        },
        "requests": {
            r["id"]: dict(r)
            for r in await conn.fetch(
                "SELECT id, action, order_id, status, args::text AS args FROM app.action_requests"
            )
        },
        "tickets": {r["id"]: r["kind"] for r in await conn.fetch("SELECT id, kind FROM app.tickets")},
        "audit_max": await conn.fetchval("SELECT coalesce(max(id), 0) FROM app.audit_log"),
    }


async def db_diff(
    conn: Any, before: dict[str, Any], after: dict[str, Any], also: frozenset[str] = frozenset()
) -> tuple[dict[str, list[Any]], list[str]]:
    """(the diff in expect_db's shape, unexpected changes)."""
    problems: list[str] = []
    diff: dict[str, list[Any]] = {}
    for table in ("refunds", "store_credits"):
        new = [after[table][k] for k in sorted(set(after[table]) - set(before[table]))]
        diff[table] = [
            {
                "order": r["order_id"],
                "status": r["status"],
                "amount_cents": r["amount_cents"],
                "currency": r["currency"],
            }
            for r in new
        ]
        problems += [
            f"existing {table} row {k} changed"
            for k in before[table]
            if after[table].get(k) != before[table][k]
        ]
    changed_orders = {k for k in before["orders"] if after["orders"][k] != before["orders"][k]}
    diff["cancellations"] = sorted(
        k
        for k in changed_orders
        if after["orders"][k][0] == "cancelled" and before["orders"][k][0] != "cancelled"
    )
    new_requests = [after["requests"][k] for k in sorted(set(after["requests"]) - set(before["requests"]))]
    diff["address_changes"] = []
    for r in new_requests:
        # only an EXECUTED change moves the address; a queued one (fraud routing, J2) must leave it as it was,
        # which the readdressed-without-a-request check below enforces
        if r["action"] == "update_shipping_address" and r["status"] == "executed":
            line1 = json.loads(r["args"])["new_address"]["line1"]
            diff["address_changes"].append({"order": r["order_id"], "line1_contains": line1})
            if line1 not in after["orders"][r["order_id"]][1]:
                problems.append(f"address request {r['id']} did not change {r['order_id']}")
    address_changed = {k for k in changed_orders if after["orders"][k][1] != before["orders"][k][1]}
    if address_changed - {a["order"] for a in diff["address_changes"]}:
        problems.append(f"orders readdressed without a request: {address_changed}")
    status_changed = {k for k in changed_orders if after["orders"][k][0] != before["orders"][k][0]}
    diff["order_statuses"] = [{"order": k, "status": after["orders"][k][0]} for k in sorted(status_changed)]
    diff["tickets"] = [
        {"kind": after["tickets"][k]} for k in sorted(set(after["tickets"]) - set(before["tickets"]))
    ]
    flags = await conn.fetch(
        "SELECT details->'flags' AS f FROM app.audit_log WHERE id > $1 AND details ? 'flags' ORDER BY id",
        before["audit_max"],
    )
    diff["audit_flags"] = [flag for r in flags for flag in json.loads(r["f"])]
    for table, n in after["counts"].items():
        allowed = EFFECT_TABLES | also | {"conversations"}
        if table not in allowed and n != before["counts"].get(table):
            problems.append(f"app.{table} row count changed: {before['counts'].get(table)} -> {n}")
    return {k: v for k, v in diff.items() if v}, problems


def _canon(db: dict[str, Any]) -> dict[str, Any]:
    return {k: sorted(json.dumps(x, sort_keys=True) for x in v) for k, v in db.items() if v}


def expected_dbs(probe: dict[str, Any]) -> list[dict[str, Any]]:
    e = dict(probe["expect_db"])
    alts = e.pop("one_of", None)
    base = {k: v for k, v in e.items() if v}
    return [_canon(base | {k: v for k, v in a.items() if v}) for a in alts] if alts else [_canon(base)]


def leaves(value: Any) -> Iterator[Any]:
    if isinstance(value, dict):
        for v in value.values():
            yield from leaves(v)
    elif isinstance(value, list):
        for v in value:
            yield from leaves(v)
    else:
        yield value


def redaction_problems(row: Any, args: dict[str, Any]) -> list[str]:
    """Criterion 4: a rejection's audit row holds no argument VALUE (names and error types only)."""
    if row["event"] != "tool_call_rejected" or row["outcome"] != "validation_failed":
        return [f"rejection audited as {row['event']}/{row['outcome']}"]
    text = json.dumps([row["event"], row["target"], row["reasons"], row["outcome"], row["details"]])
    found = []
    for v in leaves(args):
        if isinstance(v, str) and v and v in text:
            found.append(v)
        elif isinstance(v, bool | int | float) and re.search(
            rf"(?<![\w.]){re.escape(json.dumps(v))}(?![\w.])", text
        ):
            found.append(v)
    return [f"audit row for a rejected call contains argument value(s) {found!r}"] if found else []


async def consistency_problems(conn: Any) -> list[str]:
    """Run the deferred order-status consistency check now (I10). Probes roll back, so it would never
    reach a commit otherwise; in a savepoint, a violation surfaces here instead."""
    try:
        async with conn.transaction():
            await conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
            await conn.execute("SET CONSTRAINTS ALL DEFERRED")
    except asyncpg.PostgresError as exc:
        return [f"order status inconsistent with succeeded refunds: {exc}"]
    return []


# -- one probe -------------------------------------------------------------------------------------------


@contextmanager
def system_date(probe: dict[str, Any]) -> Iterator[None]:
    """Time probes move the SYSTEM date; decisions must still follow the injected clock (G1)."""
    with (
        time_machine.travel(datetime.fromisoformat(probe["system_date"]), tick=True)
        if probe.get("system_date")
        else nullcontext()
    ):
        yield


async def run_calls(
    conn: Any, pool: Any, probe: dict[str, Any], conv: uuid.UUID
) -> tuple[list[str], list[Any], list[Any]]:
    """Issue the probe's calls in order. (failures, results, audit rows)."""
    failures: list[str] = []
    results: list[Any] = []
    audits: list[Any] = []
    turns: dict[int, uuid.UUID] = {}
    effects = 0
    idem_before = await conn.fetchval("SELECT count(*) FROM app.idempotency_keys")
    last = await conn.fetchval("SELECT coalesce(max(id), 0) FROM app.audit_log")
    for i, call in enumerate(probe["calls"]):
        turn = turns.setdefault(call.get("turn", 1), uuid.uuid4())
        ctx = await new_context(conn, pool, probe["as_customer"], turn, conv)
        # the runner's own derivation: the real matcher over the turn's customer text only (J2)
        ctx.fraud_signal = fraud_signal.flagged(probe.get("turn_text", ""))
        with system_date(probe):
            result = await call_tool(ctx, call["tool"], call["args"])
        MODEL_INPUTS.append((probe["id"], call["tool"], result))
        rows = await conn.fetch("SELECT * FROM app.audit_log WHERE id > $1 ORDER BY id", last)
        last = rows[-1]["id"] if rows else last
        if len(rows) != 1:
            failures.append(f"call {i}: {len(rows)} audit rows, expected 1")
        audit = rows[0] if rows else None
        failures += flag_audit_problems(i, audit, ctx.fraud_signal)
        got = outcome_of(result, audit["outcome"] if audit else None)
        results.append(result)
        audits.append(audit)
        exp = call["outcome"]
        ok = {
            "ONE_OF": got in ("ALLOW", "NEEDS_APPROVAL", "DENY"),
            "ALLOW_OR_REPLAY": got in ("ALLOW", "REPLAY"),
        }
        if not ok.get(exp, got == exp):
            failures.append(f"call {i}: expected {exp}, got {got} ({json.dumps(result, default=str)[:200]})")
        if call.get("reason"):
            # Reason codes are in the audit row only; the model gets a customer-safe hint (DECISIONS I15).
            raw = audit["reasons"] if audit is not None else "[]"
            reasons = json.loads(raw) if isinstance(raw, str) else list(raw)
            if not reasons or reasons[0] != call["reason"]:
                failures.append(f"call {i}: expected reason {call['reason']}, got {reasons}")
        if got == "REPLAY":
            originals = [
                results[j]
                for j, c in enumerate(probe["calls"][:i])
                if (c["tool"], c["args"], c.get("turn", 1))
                == (call["tool"], call["args"], call.get("turn", 1))
            ]
            if not originals or json.dumps(result) != json.dumps(originals[0]):
                failures.append(f"call {i}: a replay must return the original result byte for byte")
        if got == "SCHEMA_REJECTED" and audit is not None:
            failures += [f"call {i}: {p}" for p in redaction_problems(audit, call["args"])]
        effects += got in ("ALLOW", "NEEDS_APPROVAL")
    idem_after = await conn.fetchval("SELECT count(*) FROM app.idempotency_keys")
    if idem_after - idem_before != effects:
        failures.append(f"{idem_after - idem_before} idempotency rows for {effects} effect(s)")
    return failures, results, audits


def flag_problems(probe: dict[str, Any]) -> list[str]:
    """A fraud probe pre-registers whether its turn text is flagged; the real matcher must agree (J2)."""
    if "turn_text" not in probe:
        return []
    got = fraud_signal.flagged(probe["turn_text"])
    return (
        [] if got == probe["expect_flag"] else [f"turn text flagged={got}, expected {probe['expect_flag']}"]
    )


def flag_audit_problems(i: int, audit: Any, flagged: bool) -> list[str]:
    """Every submission in a flagged turn carries the flag in its audit row, and only those do (J2)."""
    if audit is None:
        return []
    details = json.loads(audit["details"]) if isinstance(audit["details"], str) else audit["details"]
    marked = bool(details.get("fraud_signal"))
    return [] if marked == flagged else [f"call {i}: audit fraud_signal={marked}, turn flagged={flagged}"]


async def run_probe(pool: Any, probe: dict[str, Any]) -> list[str]:
    """Run one sequential probe inside a savepoint of `pool` (a TxPool). Returns its failures."""
    if probe.get("scripted"):
        return await run_scripted_probe(pool, probe)
    flagging = flag_problems(probe)
    async with pool.savepoint():
        conn = pool.connection
        conv = await new_conversation(conn, probe["as_customer"])
        before = await snapshot(conn)
        failures, results, audits = await run_calls(conn, pool, probe, conv)
        failures += await consistency_problems(conn)
        after = await snapshot(conn)
        diff, problems = await db_diff(conn, before, after)
        failures += problems
        if _canon(diff) not in expected_dbs(probe):
            failures.append(f"database diff {diff} != expected {probe['expect_db']}")
    failures = flagging + failures
    if (twin_id := probe["compare_response_with"]) and results:
        twin = PROBES[twin_id]
        async with pool.savepoint():
            conn = pool.connection
            conv = await new_conversation(conn, twin["as_customer"])
            _, twin_results, twin_audits = await run_calls(
                conn, pool, {**twin, "calls": twin["calls"][:1]}, conv
            )
        if json.dumps(results[0]) != json.dumps(twin_results[0]):
            failures.append(f"response differs from {twin_id}: {results[0]!r} vs {twin_results[0]!r}")
        mine, theirs = audits[0], twin_audits[0]
        if mine is None or theirs is None or mine["reasons"] != theirs["reasons"]:
            failures.append(f"audit reason differs from {twin_id}")
    return [f"{probe['id']}: {f}" for f in failures]


# -- scripted-turn probes (fp10, fp11): the REAL runner with a scripted model, zero tokens ------------------
# The flag must come from the customer's turn text alone (I11). These probes put the trigger word where a
# leaky matcher would look instead: in a tool result the model reads (fp10), or an earlier model reply (fp11).

AUDITED = {"executed": "ALLOW", "queued": "NEEDS_APPROVAL", "denied": "DENY", "not_found": "NOT_FOUND",
           "invalid": "INVALID", "needs_more_information": "NEEDS_MORE_INFORMATION"}  # fmt: skip


async def run_scripted_probe(pool: Any, probe: dict[str, Any]) -> list[str]:
    from tests.fakes import CallTool, Say, ScriptedModel
    from tollgate.agents_def.runner import ChatTurn, LLMRuntime, run_turn
    from tollgate.domain.conversations import OwnedConversation

    script, customer_id = probe["scripted"], probe["as_customer"]
    failures = flag_problems(probe)
    async with pool.savepoint():
        conn = pool.connection
        conv = await new_conversation(conn, customer_id)
        order_id = probe["calls"][0]["args"]["order_id"]
        if line1 := script.get("setup_line1"):
            await conn.execute(
                "UPDATE app.orders SET shipping_address ="
                " jsonb_set(shipping_address, '{line1}', to_jsonb($2::text)) WHERE id = $1",
                order_id,
                line1,
            )
        for asked, answered in script.get("history", []):
            turn = uuid.uuid4()
            await conn.execute(
                "INSERT INTO app.messages (conversation_id, turn_id, role, content, client_message_id)"
                " VALUES ($1, $2, 'customer', $3, $4), ($1, $2, 'assistant', $5, NULL)",
                conv, turn, asked, uuid.uuid4(), answered,
            )  # fmt: skip
        before = await snapshot(conn)
        steps: list[Any] = (
            [CallTool(script["read_first"], {"order_id": order_id})] if "read_first" in script else []
        )
        steps += [CallTool(c["tool"], c["args"]) for c in probe["calls"]] + [Say("Okay.")]
        row = await conn.fetchrow("SELECT id, name, email FROM app.customers WHERE id = $1", customer_id)
        turn_in = ChatTurn(
            customer=CustomerContext(
                customer_id=row["id"], auth_user_id=uuid.uuid4(), name=row["name"], email=row["email"]
            ),
            conversation=OwnedConversation(id=conv, order_id=None),
            client_message_id=uuid.uuid4(),
            message=probe["turn_text"],
        )
        llm = LLMRuntime(
            model=ScriptedModel(steps=steps), model_name="scripted", daily_budget=10**9, turn_estimate=1,
            ledger=None,
        )  # fmt: skip
        async for _ in run_turn(pool, llm, turn_in, FixedClock(FIXTURE_NOW)):
            pass
        audits = await conn.fetch(
            "SELECT * FROM app.audit_log WHERE id > $1 AND event LIKE 'action.%' ORDER BY id",
            before["audit_max"],
        )
        if len(audits) != len(probe["calls"]):
            failures.append(f"{len(audits)} action audit rows for {len(probe['calls'])} call(s)")
        for i, (call, audit) in enumerate(zip(probe["calls"], audits, strict=False)):
            got = AUDITED.get(audit["outcome"], audit["outcome"])
            if got != call["outcome"]:
                failures.append(
                    f"call {i}: expected {call['outcome']}, got {got} (reasons {audit['reasons']})"
                )
            failures += flag_audit_problems(i, audit, probe["expect_flag"])
        after = await snapshot(conn)
        diff, problems = await db_diff(conn, before, after, frozenset({"messages", "tool_calls", "run_log"}))
        failures += problems
        if _canon(diff) not in expected_dbs(probe):
            failures.append(f"database diff {diff} != expected {probe['expect_db']}")
    return [f"{probe['id']}: {f}" for f in failures]


# -- concurrent probes (scratch databases cloned from a seeded template; DECISIONS I6) --------------------


class BarrierPool:
    """Hands each concurrent call its own connection, and releases the first acquisition of every call at
    the same moment, so the calls race inside the gateway."""

    def __init__(self, pool: asyncpg.Pool, parties: int) -> None:
        self._pool = pool
        self._barrier = asyncio.Barrier(parties)
        self._waiting = parties

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        async with self._pool.acquire() as conn:
            if self._waiting > 0:
                self._waiting -= 1
                await self._barrier.wait()
            yield conn


async def run_concurrent_iteration(
    pool: asyncpg.Pool, probe: dict[str, Any], iteration: int = 0
) -> list[str]:
    """One iteration of a concurrent probe on a fresh clone. Returns its failures.

    The barrier releases waiters first-in first-out, so the call launched first tends to win the order lock.
    Odd iterations launch the calls in reverse, so every probe is exercised with each call winning."""
    async with pool.acquire() as conn:
        conv = await new_conversation(conn, probe["as_customer"])
        before = await snapshot(conn)
        turns = {t: uuid.uuid4() for t in {c.get("turn", 1) for c in probe["calls"]}}
        racing = BarrierPool(pool, len(probe["calls"]))
        ctxs = [
            await new_context(conn, racing, probe["as_customer"], turns[c.get("turn", 1)], conv)
            for c in probe["calls"]
        ]
        for ctx in ctxs:  # the same derivation as sequential probes: the real matcher, turn text only (J2)
            ctx.fraud_signal = fraud_signal.flagged(probe.get("turn_text", ""))
    pairs = list(zip(ctxs, probe["calls"], strict=True))
    launch = list(reversed(range(len(pairs)))) if iteration % 2 else list(range(len(pairs)))
    tasks = {
        i: asyncio.ensure_future(call_tool(pairs[i][0], pairs[i][1]["tool"], pairs[i][1]["args"]))
        for i in launch
    }
    results = list(await asyncio.gather(*(tasks[i] for i in range(len(pairs)))))
    failures: list[str] = []
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM app.audit_log WHERE id > $1 ORDER BY id", before["audit_max"])
        if len(rows) != len(probe["calls"]):
            failures.append(f"{len(rows)} audit rows for {len(probe['calls'])} calls")
        by_turn = {r["turn_id"]: r for r in rows}
        outs = []
        for ctx, result in zip(ctxs, results, strict=True):
            # Calls in different turns have one audit row each, found by turn id.
            audit_outcome = by_turn[ctx.turn_id]["outcome"] if ctx.turn_id in by_turn else None
            outs.append(outcome_of(result, audit_outcome if len(turns) > 1 else None))
        if len(turns) == 1:  # same turn: the audit rows tell which call replayed
            replays = sum(r["outcome"] == "replayed" for r in rows)
            executed = sum(r["outcome"] in ("executed", "queued") for r in rows)
        else:
            replays = 0
            executed = sum(o in ("ALLOW", "NEEDS_APPROVAL") for o in outs)
        if executed != 1:
            failures.append(
                f"{executed} executions, expected exactly 1 ({outs}, {[r['outcome'] for r in rows]})"
            )
        # The losing call's reason comes from its audit row (codes never reach the model; DECISIONS I15).
        denied = [json.loads(r["reasons"]) if isinstance(r["reasons"], str) else list(r["reasons"])
                  for r in rows if r["outcome"] == "denied"]  # fmt: skip
        for reasons in denied:
            if not reasons or reasons[0] not in (
                "line_already_compensated",
                "status_not_cancellable",
                "status_not_refundable",
            ):
                failures.append(f"the losing call was refused for {reasons}, not by the line or status rule")
        for out, result, call in zip(outs, results, probe["calls"], strict=True):
            if out == "ERROR":
                failures.append(f"a call failed: {result!r}")
            if call["outcome"] == "ALLOW_OR_REPLAY" and out not in ("ALLOW",) and not replays:
                failures.append(f"expected ALLOW or REPLAY, got {out}")
        after = await snapshot(conn)
        diff, problems = await db_diff(conn, before, after)
        failures += problems
        if _canon(diff) not in expected_dbs(probe):
            failures.append(f"database diff {diff} not in expected {probe['expect_db']}")
    return [f"{probe['id']}: {f}" for f in failures]
