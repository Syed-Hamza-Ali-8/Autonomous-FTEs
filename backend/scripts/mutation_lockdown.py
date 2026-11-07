"""Mutation check for tests/test_supabase_lockdown.py (Rule 0.1.11, invariant 16).

Removes one protection at a time on the LOCAL stack, runs the targeted test, and requires it to FAIL.
Every mutation is reverted in `finally`. The whole suite must pass before and after.

Usage (from backend/, with `supabase start` running):  uv run python scripts/mutation_lockdown.py
Writes eval/runs/mutation/lockdown-<utc-timestamp>.json. Exits 0 only if every mutation is caught.
"""

import asyncio
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import asyncpg

from tollgate.config import SupabaseSettings

BACKEND = Path(__file__).resolve().parents[1]
SUITE = "tests/test_supabase_lockdown.py"
RUNS_DIR = BACKEND / "eval" / "runs" / "mutation"
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
EXPOSED = "public, graphql_public, app"


@dataclass(frozen=True)
class Mutation:
    name: str
    removes: str
    apply_sql: str
    revert_sql: str
    must_fail: str


MUTATIONS = (
    Mutation(
        name="grant_api_roles_on_app",
        removes="no privileges for anon/authenticated in app",
        apply_sql="""
            GRANT USAGE ON SCHEMA app TO anon, authenticated;
            ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT ON TABLES TO anon, authenticated;
        """,
        revert_sql="""
            ALTER DEFAULT PRIVILEGES IN SCHEMA app REVOKE SELECT ON TABLES FROM anon, authenticated;
            REVOKE USAGE ON SCHEMA app FROM anon, authenticated;
        """,
        must_fail="test_api_roles_have_no_privileges_in_app",
    ),
    Mutation(
        name="public_execute_on_new_functions",
        removes="global default REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC",
        apply_sql="ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT EXECUTE ON FUNCTIONS TO PUBLIC;",
        revert_sql="ALTER DEFAULT PRIVILEGES FOR ROLE postgres REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;",
        must_fail="test_api_roles_have_no_privileges_in_app",
    ),
    Mutation(
        name="app_table_without_rls",
        removes="RLS enabled on every app table",
        apply_sql="CREATE TABLE app.mutation_no_rls (id int PRIMARY KEY);",
        revert_sql="DROP TABLE IF EXISTS app.mutation_no_rls;",
        must_fail="test_rls_enabled_on_every_app_table",
    ),
    Mutation(
        name="expose_app_in_data_api",
        removes="app not served by the REST Data API",
        apply_sql=f"""
            GRANT USAGE ON SCHEMA app TO anon, authenticated;
            ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT ON TABLES TO anon, authenticated;
            ALTER ROLE authenticator SET pgrst.db_schemas = '{EXPOSED}';
            NOTIFY pgrst, 'reload config';
            NOTIFY pgrst, 'reload schema';
        """,
        revert_sql="""
            ALTER ROLE authenticator RESET pgrst.db_schemas;
            ALTER DEFAULT PRIVILEGES IN SCHEMA app REVOKE SELECT ON TABLES FROM anon, authenticated;
            REVOKE USAGE ON SCHEMA app FROM anon, authenticated;
            NOTIFY pgrst, 'reload config';
            NOTIFY pgrst, 'reload schema';
        """,
        must_fail="test_anon_cannot_read_app_table_via_rest",
    ),
)


def run_pytest(target: str) -> tuple[int, str]:
    proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, "-m", "pytest", target, "-q", "-p", "no:cacheprovider"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        check=False,
    )
    tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-3:])
    return proc.returncode, tail


async def main() -> int:
    settings = SupabaseSettings()
    dsn = settings.database_url.get_secret_value()
    hosts = {urlsplit(dsn).hostname, urlsplit(settings.supabase_url).hostname}
    if not hosts <= LOCAL_HOSTS:
        print("refusing: DATABASE_URL / SUPABASE_URL must be local", file=sys.stderr)
        return 2

    record: dict[str, object] = {}
    code, tail = run_pytest(SUITE)
    record["baseline_before"] = {"passed": code == 0, "tail": tail}
    print(f"baseline before: {'PASS' if code == 0 else 'FAIL'}  {tail.splitlines()[-1] if tail else ''}")
    if code != 0:
        print("baseline must pass before mutating", file=sys.stderr)
        return 1

    results = []
    conn = await asyncpg.connect(dsn)
    try:
        for m in MUTATIONS:
            entry: dict[str, object] = {"mutation": m.name, "removes": m.removes, "target": m.must_fail}
            try:
                await conn.execute(m.apply_sql)
                await asyncio.sleep(1.0)  # let the REST server apply config/schema reloads
                code, tail = run_pytest(f"{SUITE}::{m.must_fail}")
                entry["target_failed"] = code != 0
                entry["tail"] = tail
            except asyncpg.PostgresError as exc:
                entry["target_failed"] = False
                entry["error"] = f"could not apply mutation: {type(exc).__name__}: {exc}"
            finally:
                await conn.execute(m.revert_sql)
                await asyncio.sleep(1.0)
            caught = bool(entry["target_failed"])
            print(f"{m.name}: {'CAUGHT' if caught else 'NOT CAUGHT'}  ({m.must_fail})"
                  + (f"  error={entry['error']}" if "error" in entry else ""))
            results.append(entry)
    finally:
        await conn.close()

    code, tail = run_pytest(SUITE)
    record["baseline_after"] = {"passed": code == 0, "tail": tail}
    print(f"baseline after: {'PASS' if code == 0 else 'FAIL'}  {tail.splitlines()[-1] if tail else ''}")
    record["mutations"] = results

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out = RUNS_DIR / f"lockdown-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(f"recorded: {out.relative_to(BACKEND)}")

    all_caught = all(r["target_failed"] for r in results)
    return 0 if all_caught and code == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
