"""Each seed_store.py subcommand needs only its own settings (owner, 2026-11-11).

`staff` runs with only the connection and support-lead variables; `apply` with only the connection and demo
customer variables. The real .env is never read here: the settings' env file is switched off and the process
environment holds exactly one subcommand's variables. The Auth and database steps are stubbed (nothing is
written); what is checked is which settings each subcommand loads, and that it gets through with them.
"""

import secrets
from typing import Any

import pytest
from pydantic import ValidationError

from scripts import seed_store

CONNECTION = {
    "DATABASE_URL": "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
    "SUPABASE_URL": "http://127.0.0.1:54321",
    "SUPABASE_SERVICE_ROLE_KEY": "test-service-key",
}
CUSTOMERS = {
    "DEMO_CUSTOMER_EMAIL": "ayesha.khan@northwind.example",
    "DEMO_CUSTOMER_PASSWORD": secrets.token_urlsafe(16),
    "DEMO_TARGET_EMAIL": "bilal.ahmed@northwind.example",
    "DEMO_TARGET_PASSWORD": secrets.token_urlsafe(16),
}
STAFF = {"DEMO_STAFF_EMAIL": "maya.chen@northwind.example", "DEMO_STAFF_PASSWORD": secrets.token_urlsafe(16)}
EVERY_NAME = (
    *CONNECTION, *CUSTOMERS, *STAFF,
    "CLOUD_DATABASE_URL", "CLOUD_SUPABASE_URL", "CLOUD_SUPABASE_SERVICE_ROLE_KEY",
)  # fmt: skip


@pytest.fixture
def only(monkeypatch: pytest.MonkeyPatch) -> Any:
    """only(vars): the process environment holds exactly these seed variables, and no .env file is read."""

    def set_env(variables: dict[str, str]) -> None:
        for cls in (seed_store.CustomerSeedSettings, seed_store.StaffSeedSettings):
            monkeypatch.setitem(cls.model_config, "env_file", None)
        for name in EVERY_NAME:
            monkeypatch.delenv(name, raising=False)
        for name, value in variables.items():
            monkeypatch.setenv(name, value)

    return set_env


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, Any]]:
    """Stub every step that would touch Auth or the database; record what each received."""
    seen: list[tuple[str, Any]] = []

    async def record(name: str, *args: Any) -> None:
        seen.append((name, args[0] if args else None))

    monkeypatch.setattr(seed_store, "apply_sql", lambda *a, **k: record("apply_sql"))
    monkeypatch.setattr(seed_store, "link_demo_users", lambda s, *a: record("link_demo_users", s))
    monkeypatch.setattr(seed_store, "link_demo_staff", lambda s, *a: record("link_demo_staff", s))
    return seen


async def test_staff_runs_with_only_its_own_variables(only: Any, calls: list[tuple[str, Any]]) -> None:
    only(CONNECTION | STAFF)
    await seed_store.cmd_staff()
    assert [name for name, _ in calls] == ["link_demo_staff"]
    assert isinstance(calls[0][1], seed_store.StaffSeedSettings)
    with pytest.raises(ValidationError):  # the customer settings really are absent in this environment
        seed_store.CustomerSeedSettings()


async def test_apply_runs_with_only_its_own_variables(only: Any, calls: list[tuple[str, Any]]) -> None:
    only(CONNECTION | CUSTOMERS)
    await seed_store.cmd_apply("local", reset=False, relative_dates=False)
    # the support lead is skipped (said so, not silently), and nothing asked for its settings to succeed
    assert [name for name, _ in calls] == ["apply_sql", "link_demo_users"]
    with pytest.raises(ValidationError):
        seed_store.StaffSeedSettings()


async def test_apply_also_seeds_the_lead_when_its_variables_are_set(
    only: Any, calls: list[tuple[str, Any]]
) -> None:
    only(CONNECTION | CUSTOMERS | STAFF)
    await seed_store.cmd_apply("local", reset=False, relative_dates=False)
    assert [name for name, _ in calls] == ["apply_sql", "link_demo_users", "link_demo_staff"]


@pytest.mark.parametrize("missing", ["DATABASE_URL", "DEMO_STAFF_PASSWORD"])
async def test_staff_still_requires_what_it_uses(
    only: Any, calls: list[tuple[str, Any]], missing: str
) -> None:
    only({k: v for k, v in (CONNECTION | STAFF).items() if k != missing})
    with pytest.raises(ValidationError):
        await seed_store.cmd_staff()
    assert calls == []


# --- Phase 7 fresh-clone findings D and E (owner, 2026-11-14) ------------------------------------------


async def test_customers_relinks_the_demo_sign_ins_and_touches_no_data(
    only: Any, calls: list[tuple[str, Any]]
) -> None:
    """E: `customers` only links the two demo customers' sign-ins; it never loads seed.sql."""
    only(CONNECTION | CUSTOMERS)
    await seed_store.cmd_customers()
    assert [name for name, _ in calls] == ["link_demo_users"]
    assert isinstance(calls[0][1], seed_store.CustomerSeedSettings)


async def test_customers_refuses_a_non_local_target(only: Any, calls: list[tuple[str, Any]]) -> None:
    only(CONNECTION | CUSTOMERS | {"DATABASE_URL": "postgresql://u:p@db.example.com:5432/postgres"})
    with pytest.raises(SystemExit, match="not local"):
        await seed_store.cmd_customers()
    assert calls == []


async def test_local_apply_is_guarded_and_reset_passes_through(
    only: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D: the local path asks apply_sql to guard existing data, exactly as the cloud path does (C3)."""
    seen: list[dict[str, Any]] = []

    async def record(*_a: Any, **k: Any) -> None:
        seen.append(k)

    async def nothing(*_a: Any) -> None:
        return None

    monkeypatch.setattr(seed_store, "apply_sql", record)
    monkeypatch.setattr(seed_store, "link_demo_users", nothing)
    only(CONNECTION | CUSTOMERS)
    await seed_store.cmd_apply("local", reset=False, relative_dates=False)
    await seed_store.cmd_apply("local", reset=True, relative_dates=False)
    assert seen == [{"reset": False, "guard_existing": True}, {"reset": True, "guard_existing": True}]


async def test_local_apply_refuses_a_store_with_data_unless_reset(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D, on the real local database. seed.sql is swapped for a harmless statement and the Auth steps are
    stubbed, so even a broken guard (the mutation check) cannot empty the real tables."""
    harmless = tmp_path / "seed.sql"
    harmless.write_text("SELECT 1;")
    monkeypatch.setattr(seed_store, "SEED_SQL", harmless)
    linked: list[str] = []

    async def link(*_a: Any) -> None:
        linked.append("link")

    monkeypatch.setattr(seed_store, "link_demo_users", link)
    monkeypatch.setattr(seed_store, "link_demo_staff", link)
    with pytest.raises(SystemExit, match="refusing: target already has"):
        await seed_store.cmd_apply("local", reset=False, relative_dates=False)
    assert linked == []
