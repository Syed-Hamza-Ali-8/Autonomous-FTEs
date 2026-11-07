"""Rolling 24h token accounting per model, from app.run_log (spec Section 2.3; invariant 18)."""

from tollgate.db import Conn
from tollgate.errors import BudgetExceededError


async def tokens_used_24h(conn: Conn, model: str) -> int:
    used = await conn.fetchval(
        "SELECT coalesce(sum(total_tokens), 0) FROM app.run_log"
        " WHERE model = $1 AND started_at > now() - interval '24 hours'",
        model,
    )
    return int(used)


async def preflight(conn: Conn, model: str, daily_budget: int, estimate: int) -> int:
    """Raise BudgetExceededError if this request could push the model past its daily budget."""
    used = await tokens_used_24h(conn, model)
    if used + estimate > daily_budget:
        raise BudgetExceededError(f"{model}: {used} used + {estimate} estimated > {daily_budget} per 24h")
    return used
