"""Test configuration. Refuses to run against anything but the local Supabase stack (invariant 20)."""

from collections.abc import AsyncIterator
from urllib.parse import urlsplit

import asyncpg
import pytest

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
