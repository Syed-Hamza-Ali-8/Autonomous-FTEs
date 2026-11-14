"""Scratch databases for the concurrent probes (DECISIONS I6).

Concurrent probes need real commits on separate connections, which the rolled-back TxPool cannot give.
A template database is built once from the same migrations and seed.sql as the local stack, then each
iteration runs on its own `CREATE DATABASE ... TEMPLATE` clone, dropped afterwards. The main database is
never written, so the leak check still allows no change.

The only difference from the real stack: `auth.users` is a one-column stub. The migrations reference it
(app.customers.auth_user_id) and nothing the probes do touches auth. The local `postgres` database cannot be
cloned directly: Postgres refuses to copy a database other sessions are connected to, and the Supabase
services always are.

Same guard as the test suite (invariant 20): a non-local server is refused before any connection.
"""

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import asyncpg

from tests.conftest import is_local_url

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = sorted((ROOT / "supabase" / "migrations").glob("*.sql"))
SEED = ROOT / "supabase" / "seed.sql"
PREFIX = "tollgate_probe_"
AUTH_STUB = "CREATE SCHEMA auth; CREATE TABLE auth.users (id uuid PRIMARY KEY);"


# Structure of the app schema (and the auth.users shape it references), compared between the main database
# and every scratch clone before a concurrency run (owner, DECISIONS I6). Row data is not compared.
FINGERPRINT_QUERIES = {
    "columns": """
        SELECT table_schema, table_name, column_name, ordinal_position, data_type, udt_name, is_nullable,
               column_default, character_maximum_length, numeric_precision
          FROM information_schema.columns
         WHERE table_schema = 'app'
    """,
    # The stand-in keeps the FK shape: same key column type, nullability and primary key. Its position
    # among auth.users' columns is not part of the shape (the stub has one column).
    "auth_users_id": """
        SELECT data_type, udt_name, is_nullable FROM information_schema.columns
         WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'id'
    """,
    "constraints": """
        SELECT c.conrelid::regclass::text, c.conname, c.contype, pg_get_constraintdef(c.oid)
          FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace WHERE n.nspname = 'app'
    """,
    "auth_users_key": """
        SELECT c.contype, pg_get_constraintdef(c.oid) FROM pg_constraint c
         WHERE c.conrelid = 'auth.users'::regclass AND c.contype IN ('p', 'u')
           AND pg_get_constraintdef(c.oid) = 'PRIMARY KEY (id)'
    """,
    "triggers": """
        SELECT t.tgrelid::regclass::text, t.tgname, pg_get_triggerdef(t.oid)
          FROM pg_trigger t JOIN pg_class r ON r.oid = t.tgrelid
         WHERE r.relnamespace = 'app'::regnamespace AND NOT t.tgisinternal
    """,
    "indexes": "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'app'",
    "sequences": """
        SELECT sequence_name, data_type, start_value, increment FROM information_schema.sequences
         WHERE sequence_schema = 'app'
    """,
    "functions": """
        SELECT p.proname, pg_get_functiondef(p.oid) FROM pg_proc p WHERE p.pronamespace = 'app'::regnamespace
    """,
    "rls": """
        SELECT relname, relrowsecurity FROM pg_class
         WHERE relnamespace = 'app'::regnamespace AND relkind IN ('r', 'p')
    """,
}


async def schema_fingerprint(conn: asyncpg.Connection) -> dict[str, list[tuple[object, ...]]]:
    # Pin search_path so object names in definitions render schema-qualified on both sides.
    async with conn.transaction():
        await conn.execute("SET LOCAL search_path = pg_catalog")
        return {
            name: sorted((tuple(r) for r in await conn.fetch(sql)), key=repr)
            for name, sql in FINGERPRINT_QUERIES.items()
        }


def schema_differences(
    main: dict[str, list[tuple[object, ...]]], other: dict[str, list[tuple[object, ...]]]
) -> list[str]:
    out = []
    for name in FINGERPRINT_QUERIES:
        a, b = set(main[name]), set(other[name])
        out += [f"{name}: only in main: {row}" for row in sorted(a - b, key=repr)]
        out += [f"{name}: only in scratch: {row}" for row in sorted(b - a, key=repr)]
    return out


class SchemaMismatchError(RuntimeError):
    """A scratch database is not structurally identical to the main one: the concurrency run is aborted."""


def _with_db(dsn: str, name: str) -> str:
    parts = urlsplit(dsn)
    return urlunsplit(parts._replace(path=f"/{name}"))


class ScratchDatabases:
    def __init__(self, dsn: str) -> None:
        if not is_local_url(dsn):
            raise RuntimeError(
                "scratch databases are only created on the local Supabase stack (invariant 20)"
            )
        self._dsn = dsn
        self.template = f"{PREFIX}tpl_{uuid.uuid4().hex[:8]}"
        self._main: dict[str, list[tuple[object, ...]]] | None = None

    async def _admin(self, sql: str) -> None:
        conn = await asyncpg.connect(self._dsn)
        try:
            await conn.execute(sql)
        finally:
            await conn.close()

    async def purge_leftovers(self) -> int:
        """Drop scratch databases an interrupted run left behind."""
        conn = await asyncpg.connect(self._dsn)
        try:
            names = [
                r["datname"]
                for r in await conn.fetch(
                    "SELECT datname FROM pg_database WHERE datname LIKE $1", f"{PREFIX}%"
                )
            ]
            for name in names:
                await conn.execute(f'DROP DATABASE "{name}" WITH (FORCE)')
            return len(names)
        finally:
            await conn.close()

    async def build_template(self) -> None:
        conn = await asyncpg.connect(self._dsn)
        try:
            self._main = await schema_fingerprint(conn)
        finally:
            await conn.close()
        await self._admin(f'CREATE DATABASE "{self.template}" TEMPLATE template0')
        conn = await asyncpg.connect(_with_db(self._dsn, self.template))
        try:
            await conn.execute(AUTH_STUB)
            for migration in MIGRATIONS:
                await conn.execute(migration.read_text())
            await conn.execute(SEED.read_text())
        finally:
            await conn.close()

    @asynccontextmanager
    async def clone(self) -> AsyncIterator[asyncpg.Pool]:
        name = f"{PREFIX}{uuid.uuid4().hex[:12]}"
        await self._admin(f'CREATE DATABASE "{name}" TEMPLATE "{self.template}"')
        pool = await asyncpg.create_pool(
            _with_db(self._dsn, name), min_size=2, max_size=4, server_settings={"search_path": "app"}
        )
        try:
            await self.assert_identical(pool)
            yield pool
        finally:
            await pool.close()
            await self._admin(f'DROP DATABASE "{name}" WITH (FORCE)')

    async def assert_identical(self, pool: asyncpg.Pool) -> None:
        if self._main is None:
            raise SchemaMismatchError("main schema fingerprint missing: build_template() first")
        async with pool.acquire() as conn:
            diff = schema_differences(self._main, await schema_fingerprint(conn))
        if diff:
            raise SchemaMismatchError("scratch schema differs from main:\n" + "\n".join(diff[:20]))

    async def close(self) -> None:
        await self._admin(f'DROP DATABASE IF EXISTS "{self.template}" WITH (FORCE)')
