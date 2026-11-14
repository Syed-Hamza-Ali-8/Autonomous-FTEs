"""asyncpg pool. search_path is pinned to `app`; every query is parameterized (invariant 12)."""

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from tollgate.config import SupabaseSettings

# What domain/ functions accept: a plain connection (tests, scripts) or one checked out of the pool.
Conn = asyncpg.Connection | PoolConnectionProxy


async def create_pool(settings: SupabaseSettings) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(
        settings.database_url.get_secret_value(),
        min_size=1,
        max_size=10,
        server_settings={"search_path": "app", "application_name": "tollgate-api"},
    )
    if pool is None:  # asyncpg types the result as optional
        raise RuntimeError("asyncpg returned no pool")
    return pool
