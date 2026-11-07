"""The anon key can read nothing in `app`; RLS is on for every `app` table (invariant 19, Section 2.4).

Liveness (Rule 0.1.11):
- A probe table with a marker row is created in `app` for the session, so the RLS and privilege
  checks never pass vacuously on an empty schema.
- A positive control table in `public` that anon IS granted must be readable over REST. This proves
  the REST path, URL and key work, so a denial on `app` is meaningful.
- scripts/mutation_lockdown.py removes each protection and shows the targeted test fails.
"""

import asyncio
import tomllib
from collections.abc import AsyncIterator

import asyncpg
import httpx
import pytest

from tests.conftest import is_local_url
from tollgate.config import REPO_ROOT, SupabaseSettings

PROBE = "lockdown_probe"
CONTROL = "lockdown_control"
MARKER = "tollgate-lockdown-marker-7f3a"
API_ROLES = ("anon", "authenticated")


async def _reload_rest_schema(db: asyncpg.Connection) -> None:
    await db.execute("NOTIFY pgrst, 'reload schema'")


@pytest.fixture(scope="module")
async def probe_tables(db: asyncpg.Connection) -> AsyncIterator[None]:
    # Literal SQL: identifiers and marker are fixed constants, nothing is interpolated (invariant 12).
    await db.execute(
        """
        CREATE TABLE app.lockdown_probe (id int PRIMARY KEY, marker text NOT NULL);
        ALTER TABLE app.lockdown_probe ENABLE ROW LEVEL SECURITY;
        INSERT INTO app.lockdown_probe VALUES (1, 'tollgate-lockdown-marker-7f3a');
        CREATE SEQUENCE app.lockdown_probe_seq;
        CREATE FUNCTION app.lockdown_probe_fn() RETURNS int LANGUAGE sql AS 'SELECT 1';
        CREATE TYPE app.lockdown_probe_type AS ENUM ('a');

        CREATE TABLE public.lockdown_control (id int PRIMARY KEY, marker text NOT NULL);
        INSERT INTO public.lockdown_control VALUES (1, 'tollgate-lockdown-marker-7f3a');
        GRANT SELECT ON public.lockdown_control TO anon;
        """
    )
    await _reload_rest_schema(db)
    try:
        yield
    finally:
        await db.execute(
            "DROP TABLE IF EXISTS app.lockdown_probe; DROP TABLE IF EXISTS public.lockdown_control;"
            "DROP SEQUENCE IF EXISTS app.lockdown_probe_seq;"
            "DROP FUNCTION IF EXISTS app.lockdown_probe_fn();"
            "DROP TYPE IF EXISTS app.lockdown_probe_type;"
        )
        await _reload_rest_schema(db)


async def _anon_get(settings: SupabaseSettings, table: str, schema: str | None) -> httpx.Response:
    key = settings.supabase_anon_key.get_secret_value()
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    if schema is not None:
        headers["Accept-Profile"] = schema
    async with httpx.AsyncClient(base_url=settings.supabase_url, timeout=10) as client:
        return await client.get(f"/rest/v1/{table}", params={"select": "*"}, headers=headers)


async def _anon_get_settled(settings: SupabaseSettings, table: str, schema: str | None) -> httpx.Response:
    # The REST schema cache reloads asynchronously after NOTIFY; allow it a few seconds to settle.
    resp = await _anon_get(settings, table, schema)
    for _ in range(20):
        if resp.status_code == 200:
            break
        await asyncio.sleep(0.25)
        resp = await _anon_get(settings, table, schema)
    return resp


def test_guard_accepts_only_local_urls() -> None:
    assert is_local_url("postgresql://u:p@127.0.0.1:54322/postgres")
    assert is_local_url("http://localhost:54321")
    assert not is_local_url("postgresql://u:p@aws-0-region.pooler.supabase.com:5432/postgres")
    assert not is_local_url("https://abcd.supabase.co")


def test_app_schema_not_in_exposed_schemas() -> None:
    config = tomllib.loads((REPO_ROOT / "supabase" / "config.toml").read_text())
    assert "app" not in config["api"]["schemas"]


@pytest.mark.usefixtures("probe_tables")
async def test_positive_control_anon_can_read_granted_public_table(settings: SupabaseSettings) -> None:
    resp = await _anon_get_settled(settings, CONTROL, None)
    assert resp.status_code == 200, resp.text
    assert MARKER in resp.text


@pytest.mark.usefixtures("probe_tables")
async def test_anon_cannot_read_app_table_via_rest(settings: SupabaseSettings) -> None:
    # Give the schema cache the same settle time as the control before asserting denial.
    for schema in ("app", None):
        resp = await _anon_get_settled(settings, PROBE, schema)
        assert resp.status_code != 200, f"schema={schema}: {resp.status_code}"
        assert MARKER not in resp.text


@pytest.mark.usefixtures("probe_tables")
async def test_api_roles_have_no_privileges_in_app(db: asyncpg.Connection) -> None:
    rows = await db.fetch(
        """
        SELECT r.role, 'schema' AS kind, 'app' AS name
          FROM unnest($1::text[]) AS r(role)
         WHERE has_schema_privilege(r.role, 'app', 'USAGE') OR has_schema_privilege(r.role, 'app', 'CREATE')
        UNION ALL
        SELECT r.role, 'table', c.relname
          FROM unnest($1::text[]) AS r(role)
          CROSS JOIN pg_class c
         WHERE c.relnamespace = 'app'::regnamespace AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
           AND (has_table_privilege(r.role, c.oid,
                                    'SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER')
                OR has_any_column_privilege(r.role, c.oid, 'SELECT, INSERT, UPDATE, REFERENCES'))
        UNION ALL
        SELECT r.role, 'sequence', c.relname
          FROM unnest($1::text[]) AS r(role)
          CROSS JOIN pg_class c
         WHERE c.relnamespace = 'app'::regnamespace AND c.relkind = 'S'
           AND has_sequence_privilege(r.role, c.oid, 'USAGE, SELECT, UPDATE')
        UNION ALL
        SELECT r.role, 'function', p.proname
          FROM unnest($1::text[]) AS r(role)
          CROSS JOIN pg_proc p
         WHERE p.pronamespace = 'app'::regnamespace AND has_function_privilege(r.role, p.oid, 'EXECUTE')
        UNION ALL
        SELECT r.role, 'type', t.typname
          FROM unnest($1::text[]) AS r(role)
          CROSS JOIN pg_type t
         WHERE t.typnamespace = 'app'::regnamespace AND t.typtype IN ('e', 'd', 'c', 'r', 'm')
           -- A table/view's implicit row type is excluded: USAGE on it grants no data access, and the
           -- table itself is checked above. Standalone composites (relkind 'c') are still checked.
           AND (t.typrelid = 0 OR (SELECT relkind FROM pg_class WHERE oid = t.typrelid) = 'c')
           AND has_type_privilege(r.role, t.oid, 'USAGE')
        """,
        list(API_ROLES),
    )
    assert [tuple(r) for r in rows] == []


@pytest.mark.usefixtures("probe_tables")
async def test_privilege_check_is_not_vacuous(db: asyncpg.Connection) -> None:
    # The privilege test only proves something if each object kind it checks exists in app.
    counts = await db.fetchrow(
        """
        SELECT
          (SELECT count(*) FROM pg_class WHERE relnamespace = 'app'::regnamespace AND relkind = 'r') tables,
          (SELECT count(*) FROM pg_class WHERE relnamespace = 'app'::regnamespace AND relkind = 'S') AS seqs,
          (SELECT count(*) FROM pg_proc WHERE pronamespace = 'app'::regnamespace) AS funcs,
          (SELECT count(*) FROM pg_type WHERE typnamespace = 'app'::regnamespace AND typtype = 'e') AS enums
        """
    )
    assert counts is not None
    assert all(counts[k] > 0 for k in ("tables", "seqs", "funcs", "enums")), dict(counts)


@pytest.mark.usefixtures("probe_tables")
async def test_rls_enabled_on_every_app_table(db: asyncpg.Connection) -> None:
    tables = await db.fetch(
        "SELECT relname, relrowsecurity FROM pg_class "
        "WHERE relnamespace = 'app'::regnamespace AND relkind IN ('r', 'p')"
    )
    assert tables, "no tables in app: the check would pass vacuously"
    assert [t["relname"] for t in tables if not t["relrowsecurity"]] == []
