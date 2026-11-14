"""Queue a NEEDS_APPROVAL request: insert-only (DECISIONS J7, amendment A2-P4).

The Action Gateway calls this; it never decides anything. It inserts the undecided request and its pending
refund or credit row, which hold the order's lines (H1) and count against the remainder and the rolling window
(A7) until staff decide. The database refuses a request created already decided
(`action_requests_born_undecided`). Deciding is approvals/service.py's alone, and no tool reaches it (af06).
"""

from typing import Any

from tollgate.actions.records import MoneyAction, Request, insert_compensation, insert_request
from tollgate.db import Conn


async def create(conn: Conn, kind: MoneyAction, req: Request, reason: str) -> dict[str, Any]:
    request_id = await insert_request(conn, req)
    row_id = await insert_compensation(conn, kind, request_id, req, "pending_approval", reason)
    id_key = "refund_id" if kind == "request_refund" else "store_credit_id"
    return {"reference": request_id, id_key: row_id}


async def create_request(conn: Conn, req: Request) -> dict[str, Any]:
    """Queue an action that holds no money row while it waits: a cancellation (its H2 refund is created only
    when approved, by the same effect the gateway runs) or an address change (fraud routing, J2)."""
    return {"reference": await insert_request(conn, req)}
