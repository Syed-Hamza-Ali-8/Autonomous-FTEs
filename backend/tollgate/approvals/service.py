"""Approval service. Phase 3: queue a NEEDS_APPROVAL request; Phase 4 adds staff approve / reject.

No agent can reach this module's decisions (invariant 7): it is called by the Action Gateway to queue, and
(from Phase 4) by the staff API. A queued refund or credit holds its lines (H1) and counts against the
order's remainder and the rolling window until staff decide.
"""

from typing import Any

from tollgate.actions.executors import MoneyAction, Request, insert_compensation, insert_request
from tollgate.db import Conn


async def create(conn: Conn, kind: MoneyAction, req: Request, reason: str) -> dict[str, Any]:
    request_id = await insert_request(conn, req)
    row_id = await insert_compensation(conn, kind, request_id, req, "pending_approval", reason)
    id_key = "refund_id" if kind == "request_refund" else "store_credit_id"
    return {"reference": request_id, id_key: row_id}
