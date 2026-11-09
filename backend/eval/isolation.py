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

TRACE_TABLES = ("conversations", "messages", "run_log", "tool_calls")


async def _columns(conn: Conn, table: str) -> list[str]:
    rows = await conn.fetch(
        "SELECT column_name FROM information_schema.columns"
        " WHERE table_schema = 'app' AND table_name = $1 AND is_identity = 'NO' ORDER BY ordinal_position",
        table,
    )
    return [r["column_name"] for r in rows]


async def _copy(src: Conn, dst: Conn, table: str, where: str, *args: Any) -> int:
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
