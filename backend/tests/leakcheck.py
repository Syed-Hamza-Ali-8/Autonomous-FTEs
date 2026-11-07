"""Leak check: what a run left behind in the local database.

pytest must leave NOTHING: every table's row count, and the number of customers linked to a login,
is identical before and after (DECISIONS C5, F5). Runs that call a real model (live smoke,
Playwright) may grow exactly the tables below, and only grow them; any other change fails the run.
"""

import asyncpg

# Explicit and minimal. Each entry is a table a REAL model turn must keep, with the reason.
REAL_MODEL_RUN_MAY_GROW: dict[str, str] = {
    # Token usage lives here. The rolling 24h budget pre-flight sums it, so deleting these rows
    # would hide real spend from the budget (invariant 18).
    "app.run_log": "token usage and per-turn record of every real model call",
    # The tool trace of that real turn: which lookups the model made and what they returned.
    # Kept with the run it belongs to (owner decision 2026-11-07: keep each real turn's trace).
    "app.tool_calls": "tool trace of the real turn",
    # run_log.conversation_id references the conversation, and the conversation's messages are the
    # turn's input and checked reply. Same owner decision: kept until `supabase db reset`.
    "app.conversations": "conversation the real turn belongs to (run_log FK)",
    "app.messages": "the real turn's customer message and claim-checked reply",
}

LINKED = "app.customers[linked to a login]"


async def snapshot(dsn: str) -> dict[str, int]:
    conn = await asyncpg.connect(dsn)
    try:
        tables = [
            r["relname"]
            for r in await conn.fetch(
                "SELECT relname FROM pg_class"
                " WHERE relnamespace = 'app'::regnamespace AND relkind = 'r' ORDER BY 1"
            )
        ]
        counts = {f"app.{t}": await conn.fetchval(f'SELECT count(*) FROM app."{t}"') for t in tables}  # noqa: S608
        counts["auth.users"] = await conn.fetchval("SELECT count(*) FROM auth.users")
        counts[LINKED] = await conn.fetchval(
            "SELECT count(*) FROM app.customers WHERE auth_user_id IS NOT NULL"
        )
        return counts
    finally:
        await conn.close()


def problems(before: dict[str, int], after: dict[str, int], may_grow: dict[str, str]) -> list[str]:
    out = []
    for key in sorted(set(before) | set(after)):
        b, a = before.get(key), after.get(key)
        if b == a:
            continue
        if key in may_grow and b is not None and a is not None and a > b:
            continue
        out.append(f"{key}: {b} -> {a}")
    return out
