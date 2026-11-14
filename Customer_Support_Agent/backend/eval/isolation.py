"""Clean state per scenario (PREREGISTRATION section 6, item 3; DECISIONS I11 scratch databases).

Write scenarios change the store, and scenarios share customers, so one scenario's refund would move another's
rolling window or line state. Each scenario therefore runs on its own clone of the seeded template (built from
the same migrations and seed, structurally identical to the main schema, local only), is scored there, and the
clone is dropped. Its WRITES vanish with it.

Its TRACE is copied back to the main database: the conversation, messages, run_log and tool_calls rows of the
real turn (owner decision F6: keep each real turn's trace; run_log also feeds the budget pre-flight, and the
spend ledger is written as the turn runs). Nothing else is copied, so the run's leak check still allows
growth in exactly the F6 tables.
"""

import uuid
from typing import Any

from tollgate.db import Conn

# The ONLY tables the copy-back may write (owner guard a). Everything else in the store, the actions and the
# audit stays in the clone and is dropped with it.
TRACE_TABLES = ("conversations", "messages", "run_log", "tool_calls")
# The seeded store every scenario must start from (owner guard c): row content of these tables, in key order.
STORE_TABLES = (
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
    "shipments",
    "refunds",
    "product_reviews",
)
# Tables a fresh scenario database must have empty.
EMPTY_AT_START = ("action_requests", "store_credits", "idempotency_keys", "tickets", "audit_log", "run_log")


class TraceTableError(ValueError):
    """The copy-back was asked to write a table outside the trace allowlist."""


async def store_fingerprint(conn: Conn) -> str:
    """A digest of the seeded store's content plus the row counts that must be zero at a scenario's start."""
    parts = []
    for table in STORE_TABLES:
        parts.append(
            await conn.fetchval(
                f"SELECT md5(coalesce(string_agg(t::text, '|' ORDER BY t::text), '')) FROM app.\"{table}\" t"  # noqa: S608
            )
        )
    for table in EMPTY_AT_START:
        parts.append(str(await conn.fetchval(f'SELECT count(*) FROM app."{table}"')))  # noqa: S608
    return "/".join(parts)


async def _columns(conn: Conn, table: str) -> list[str]:
    rows = await conn.fetch(
        "SELECT column_name FROM information_schema.columns"
        " WHERE table_schema = 'app' AND table_name = $1 AND is_identity = 'NO' ORDER BY ordinal_position",
        table,
    )
    return [r["column_name"] for r in rows]


async def _copy(src: Conn, dst: Conn, table: str, where: str, *args: Any) -> int:
    if table not in TRACE_TABLES:
        raise TraceTableError(f"copy-back may only write {TRACE_TABLES}, not app.{table}")
    cols = await _columns(dst, table)
    names = ", ".join(f'"{c}"' for c in cols)
    rows = await src.fetch(f'SELECT {names} FROM app."{table}" WHERE {where} ORDER BY 1', *args)  # noqa: S608
    marks = ", ".join(f"${i}" for i in range(1, len(cols) + 1))
    for r in rows:
        await dst.execute(f'INSERT INTO app."{table}" ({names}) VALUES ({marks})', *r.values())  # noqa: S608
    return len(rows)


async def carry_trace(
    src: Conn, dst: Conn, conversation_id: uuid.UUID, turn_ids: list[uuid.UUID]
) -> dict[str, int]:
    """Copy one scenario's trace rows from its clone to the main database. Returns rows copied per table."""
    async with dst.transaction():
        return {
            "conversations": await _copy(src, dst, "conversations", "id = $1", conversation_id),
            "messages": await _copy(src, dst, "messages", "conversation_id = $1", conversation_id),
            "run_log": await _copy(src, dst, "run_log", "conversation_id = $1", conversation_id),
            "tool_calls": await _copy(src, dst, "tool_calls", "turn_id = ANY($1::uuid[])", turn_ids),
        }
