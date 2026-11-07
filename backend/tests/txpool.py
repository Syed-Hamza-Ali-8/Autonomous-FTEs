"""A stand-in for asyncpg.Pool that runs every query on ONE connection inside a transaction.

DECISIONS C5: tests roll back. Code under test (the API, the runner, the tools) writes through a pool;
handing it a TxPool keeps those writes inside the test's transaction, so nothing is committed.
`savepoint()` gives each test its own nested transaction on top of a module-level one.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg


class TxPool:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    @property
    def connection(self) -> asyncpg.Connection:
        return self._conn

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        yield self._conn

    async def execute(self, query: str, *args: Any) -> str:
        return await self._conn.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        return await self._conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record | None:
        return await self._conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        return await self._conn.fetchval(query, *args)

    async def close(self) -> None:  # the owning fixture closes the real connection
        return None

    @asynccontextmanager
    async def savepoint(self) -> AsyncIterator[None]:
        tx = self._conn.transaction()  # nested inside an open transaction -> SAVEPOINT
        await tx.start()
        try:
            yield
        finally:
            await tx.rollback()


@asynccontextmanager
async def rolled_back(dsn: str) -> AsyncIterator[TxPool]:
    """A TxPool on a fresh connection whose outer transaction is always rolled back."""
    conn = await asyncpg.connect(dsn, server_settings={"search_path": "app"})
    tx = conn.transaction()
    await tx.start()
    try:
        yield TxPool(conn)
    finally:
        await tx.rollback()
        await conn.close()
