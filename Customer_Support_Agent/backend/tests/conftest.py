"""Test configuration.

- Refuses to run against anything but the local Supabase stack (invariant 20).
- Deletes leftover test logins at the start of every run (interrupted runs skip their teardown).
- Proves tests leave no trace (DECISIONS C5, F5): see tests/leakcheck.py; pytest allows no change at all.
"""

import asyncio
from collections.abc import AsyncIterator
from urllib.parse import urlsplit

import asyncpg
import pytest

from tests.auth_users import purge_test_logins
from tests.leakcheck import problems, snapshot
from tollgate.config import SupabaseSettings

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def is_local_url(url: str) -> bool:
    return urlsplit(url).hostname in LOCAL_HOSTS


def pytest_configure(config: pytest.Config) -> None:
    settings = SupabaseSettings()
    for name, url in (
        ("DATABASE_URL", settings.database_url.get_secret_value()),
        ("SUPABASE_URL", settings.supabase_url),
    ):
        if not is_local_url(url):
            # Never print the URL itself: it may contain a password.
            pytest.exit(f"{name} is not a local address; tests only run against `supabase start`", 2)
    removed = asyncio.run(purge_test_logins(settings))  # interrupted runs skip their teardown
    if removed:
        print(f"removed {removed} leftover test login(s) before the run")
    config.stash[BEFORE] = asyncio.run(snapshot(settings.database_url.get_secret_value()))


BEFORE = pytest.StashKey[dict[str, int]]()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    before = session.config.stash.get(BEFORE, None)
    if before is None:
        return
    after = asyncio.run(snapshot(SupabaseSettings().database_url.get_secret_value()))
    # pytest never calls a real model, so NOTHING may change (no allowlist here).
    found = problems(before, after, may_grow={})
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if found:
        if reporter:
            reporter.write_line(f"LEAK CHECK FAILED, the run left changes behind: {found}", red=True)
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
    elif reporter:
        reporter.write_line(f"leak check: nothing left behind ({len(after)} counts compared)")


@pytest.fixture(scope="session")
def settings() -> SupabaseSettings:
    return SupabaseSettings()


@pytest.fixture(scope="session")
async def db(settings: SupabaseSettings) -> AsyncIterator[asyncpg.Connection]:
    conn = await asyncpg.connect(settings.database_url.get_secret_value())
    try:
        yield conn
    finally:
        await conn.close()
