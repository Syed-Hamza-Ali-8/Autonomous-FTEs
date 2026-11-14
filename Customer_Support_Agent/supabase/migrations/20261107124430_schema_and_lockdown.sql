-- Tollgate private schema and Data API lockdown (spec Section 2.4, invariant 19).
--
-- Guarantees, each proven by backend/tests/test_supabase_lockdown.py:
--   1. Tollgate data lives in schema `app`, which is NOT in [api].schemas (supabase/config.toml),
--      so the REST Data API never serves it.
--   2. `anon` and `authenticated` hold no privilege on `app` or anything in it, now or later
--      (default privileges below cover objects created by future migrations).
--   3. Every table in `app` has RLS enabled with no policies. Each later migration enables RLS on
--      its tables in the same file; the test fails if any table in `app` lacks it.
--   4. Every table migration also revokes the table's implicit row type from PUBLIC (owner decision,
--      strict handling): `REVOKE ALL ON TYPE app.<table> FROM PUBLIC;` next to ENABLE ROW LEVEL SECURITY.
--      Postgres grants USAGE on a new table's row type to PUBLIC and default privileges don't cover it.
-- The backend reaches `app` only through asyncpg as a database owner role, never through the Data API.

CREATE SCHEMA IF NOT EXISTS app;

REVOKE ALL ON SCHEMA app FROM PUBLIC;
REVOKE ALL ON SCHEMA app FROM anon, authenticated;

-- Objects created later in `app` by the migration role grant nothing to API roles.
ALTER DEFAULT PRIVILEGES IN SCHEMA app REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA app REVOKE ALL ON SEQUENCES FROM PUBLIC, anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA app REVOKE ALL ON FUNCTIONS FROM PUBLIC, anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA app REVOKE ALL ON TYPES FROM PUBLIC, anon, authenticated;

-- Postgres grants EXECUTE on new functions and USAGE on new types to PUBLIC through its built-in
-- global defaults, and a per-schema REVOKE cannot remove a global default (verified 2026-11-07:
-- without these two lines a new app function is executable by anon). Revoke them globally for
-- objects the migration role creates. Supabase's public-schema defaults still grant anon /
-- authenticated / service_role explicitly, so nothing Supabase relies on changes.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres REVOKE USAGE ON TYPES FROM PUBLIC;

COMMENT ON SCHEMA app IS
  'Tollgate private schema. Not exposed via the Data API; RLS on every table; no grants to anon/authenticated.';
