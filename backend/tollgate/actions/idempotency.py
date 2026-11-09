"""Idempotency keys (spec 6.2 step 4; DECISIONS I5).

The key is a hash of (customer, action, target, recomputed normalised arguments, turn). The gateway looks it
up after ownership and recompute and before policy, so an unauthorised request never reaches a lookup. A key
is recorded ONLY for an outcome with an effect (executed or queued), in the same transaction as that effect;
a DENY records nothing and is evaluated again on a repeat.
"""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

from tollgate.db import Conn


def key(
    customer_id: str, action: str, target: str | None, normalised: dict[str, Any], turn_id: uuid.UUID
) -> str:
    material = json.dumps(
        [customer_id, action, target, normalised, str(turn_id)], sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(material.encode()).hexdigest()


async def lookup(conn: Conn, idem_key: str, customer_id: str) -> dict[str, Any] | None:
    """The original result for this key, or None. Filtered by customer in SQL like every other read."""
    raw = await conn.fetchval(
        "SELECT result FROM app.idempotency_keys WHERE key = $1 AND customer_id = $2", idem_key, customer_id
    )
    if raw is None:
        return None
    result: dict[str, Any] = json.loads(
        raw
    )  # stored as text: key order preserved, so replays are byte-identical
    return result


async def record(
    conn: Conn, idem_key: str, customer_id: str, action_request_id: str, result: dict[str, Any], now: datetime
) -> bool:
    """Record an effect's key. False if a concurrent submission recorded the same key first."""
    inserted = await conn.fetchval(
        "INSERT INTO app.idempotency_keys (key, customer_id, action_request_id, result, created_at)"
        " VALUES ($1, $2, $3, $4, $5) ON CONFLICT (key) DO NOTHING RETURNING key",
        idem_key,
        customer_id,
        action_request_id,
        json.dumps(result),
        now,
    )
    return inserted is not None
