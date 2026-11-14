"""Register entries that were implemented but had no test (DECISIONS audit, 2026-11-09)."""

import dataclasses
import json
from collections.abc import AsyncIterator
from datetime import datetime, timedelta

import asyncpg
import pytest

from tollgate.actions import gateway
from tollgate.policy import engine


@pytest.fixture
async def tx(db: asyncpg.Connection) -> AsyncIterator[asyncpg.Connection]:
    t = db.transaction()
    await t.start()
    try:
        yield db
    finally:
        await t.rollback()


async def test_a3_window_counts_across_currencies_but_caps_per_currency(tx: asyncpg.Connection) -> None:
    """A3: amount caps are per currency; the refund COUNT spans currencies."""
    now = datetime.fromisoformat("2026-11-07T12:00:00+00:00")
    customer = "CUS-017"  # a USD customer; give them a PKR order with two recent refunds
    await tx.execute(
        "INSERT INTO app.orders (id, customer_id, status, currency, total_cents, shipping_address, placed_at,"
        " paid_at, delivered_at) VALUES ('ORD-9901', $1, 'partially_refunded', 'PKR', 900000, '{}'::jsonb,"
        " $2, $2, $2)",
        customer,
        now - timedelta(days=10),
    )
    await tx.execute(
        "INSERT INTO app.payments (id, order_id, currency, amount_cents, captured_at)"
        " VALUES ('PAY-9901', 'ORD-9901', 'PKR', 900000, $1)",
        now - timedelta(days=10),
    )
    for i, amount in enumerate((100000, 200000)):
        await tx.execute(
            "INSERT INTO app.refunds (id, order_id, currency, amount_cents, status, source, created_at)"
            " VALUES ($1, 'ORD-9901', 'PKR', $2, 'succeeded', 'historical', $3)",
            f"REF-990{i}",
            amount,
            now - timedelta(days=5),
        )
    since = now - timedelta(days=90)
    usd_count, usd_total = await gateway._window(tx, customer, since, "USD", False, now)
    pkr_count, pkr_total = await gateway._window(tx, customer, since, "PKR", False, now)
    assert usd_count == pkr_count  # one count across both currencies
    assert usd_count >= 2
    assert pkr_total - usd_total != 0 and pkr_total >= 300000  # totals are per currency


def test_b8_customer_tier_is_not_a_policy_input() -> None:
    """B8: `gold` has no policy effect in v1: no decision input mentions the tier."""
    assert "tier" not in {f.name for f in dataclasses.fields(engine.MoneyFacts)}
    assert "tier" not in gateway.OWNED_ORDER_SQL


def test_c3_cloud_seed_requires_the_host_typed_back(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import seed_store

    monkeypatch.setattr("builtins.input", lambda _prompt: "wrong-host.example")
    with pytest.raises(SystemExit, match="not confirmed"):
        seed_store.confirm_cloud("https://abcd.supabase.co")


async def test_c3_seed_refuses_a_target_with_data_unless_reset(settings: object) -> None:
    from scripts import seed_store
    from tollgate.config import SupabaseSettings

    dsn = SupabaseSettings().database_url.get_secret_value()
    with pytest.raises(SystemExit, match="refusing: target already has"):
        # guard first: the harmless SQL never runs, because the local store has customers
        await seed_store.apply_sql(dsn, "SELECT 1", reset=False, guard_existing=True)


async def test_f2_every_stored_timestamp_is_timestamptz(db: asyncpg.Connection) -> None:
    """F2 (amended on 2026-11-09): storage is UTC timestamptz everywhere; only display differs by audience."""
    naive = await db.fetch(
        "SELECT table_name, column_name FROM information_schema.columns"
        " WHERE table_schema = 'app' AND data_type = 'timestamp without time zone'"
    )
    assert [(r["table_name"], r["column_name"]) for r in naive] == []
    aware = await db.fetchval(
        "SELECT count(*) FROM information_schema.columns"
        " WHERE table_schema = 'app' AND data_type = 'timestamp with time zone'"
    )
    assert aware > 10  # not vacuous


# -- the standing gate item (owner, 2026-11-11): the register is clean -------------------------------------
# Every DECISIONS entry is implemented with a named test that proves it, or explicitly deferred to a target
# phase. C2 and J5 were recorded but not built, and found by accident; this closes that class.

import re  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "backend" / "tests"
PROBE_FILE = ROOT / "backend" / "eval" / "adversarial_tools.jsonl"
CURRENT_PHASE = 7
STATUSES = {"✓", "⏸", "◐", "↪"}  # implemented, deferred, partial (both), superseded


def register(text: str) -> tuple[list[str], dict[str, tuple[str, str]]]:
    """(entry ids in order, status table: id -> (status, evidence))."""
    entries = re.findall(r"^- \*\*([A-Z][0-9]+)\*\*", text, re.M)
    table = text[text.index("## Implementation status") :]
    rows = {
        m.group(1): (m.group(2).strip(), m.group(3).strip())
        for m in re.finditer(r"^\| ([A-Z][0-9]+) \| ([^|]+) \| (.+) \|$", table, re.M)
    }
    return entries, rows


def _test_refs(evidence: str) -> list[tuple[str, str]]:
    return re.findall(r"`(test_[a-z0-9_]+)::(test_[a-z0-9_*]+)", evidence)


def _probe_ids(evidence: str) -> set[str]:
    ids: set[str] = set()
    dash = "[\u2013-]"  # ranges are written with an en dash ("b01\u2013b16") or a hyphen
    for m in re.finditer(
        rf"probes? ((?:[a-z]{{1,3}}\d\d(?:{dash}[a-z]{{0,3}}\d\d)?[ ,]*(?:and )?)+)", evidence
    ):
        for part in re.findall(rf"([a-z]{{1,3}})(\d\d)(?:{dash}[a-z]{{0,3}}(\d\d))?", m.group(1)):
            prefix, lo, hi = part
            ids |= {f"{prefix}{n:02d}" for n in range(int(lo), int(hi or lo) + 1)}
    return ids


def unresolved(evidence: str) -> list[str]:
    """Named evidence that does not exist: test functions, probe ids, frontend test files."""
    missing = []
    for module, func in _test_refs(evidence):
        path = TESTS / f"{module}.py"
        body = path.read_text() if path.exists() else ""
        pattern = re.escape(func).replace(r"\*", r"[a-z0-9_]*")
        if not re.search(rf"^(?:async )?def {pattern}\(", body, re.M):
            missing.append(f"{module}::{func}")
    probes = {json.loads(line)["id"] for line in PROBE_FILE.read_text().splitlines() if line.strip()}
    missing += sorted(f"probe {p}" for p in _probe_ids(evidence) - probes)
    for name in re.findall(r"`?([a-z0-9-]+\.(?:test|spec)\.ts)`?", evidence):
        if not list((ROOT / "frontend").glob(f"src/**/{name}")) + list(
            (ROOT / "frontend").glob(f"tests/**/{name}")
        ):
            missing.append(name)
    return missing


def proven(evidence: str) -> bool:
    return bool(
        _test_refs(evidence) or _probe_ids(evidence) or re.search(r"[a-z0-9-]+\.(test|spec)\.ts", evidence)
    )


def targeted(evidence: str) -> bool:
    return any(int(n) >= CURRENT_PHASE for n in re.findall(r"Phase (\d)", evidence))


def register_problems(text: str) -> list[str]:
    entries, rows = register(text)
    out = [f"{e}: no row in the implementation status table" for e in entries if e not in rows]
    out += [f"{r}: a row with no DECISIONS entry" for r in rows if r not in entries]
    for rid, (status, evidence) in rows.items():
        if status not in STATUSES:
            out.append(
                f"{rid}: status {status!r} is not one of {sorted(STATUSES)}"
                " (recorded-but-not-built is not allowed)"
            )
            continue
        if status in ("✓", "◐") and not proven(evidence):
            out.append(f"{rid}: implemented, but no named test proves it")
        if status in ("⏸", "◐") and not targeted(evidence):
            out.append(f"{rid}: deferred without a target phase (Phase {CURRENT_PHASE} or later)")
        if status == "↪":
            successor = re.search(r"superseded by ([A-Z][0-9]+)", evidence)
            if successor is None or successor.group(1) not in rows:
                out.append(f"{rid}: superseded, but the successor is not named or not in the table")
        out += [f"{rid}: names {m}, which does not exist" for m in unresolved(evidence)]
    return out


def test_every_decision_is_implemented_with_a_test_or_deferred_with_a_phase() -> None:
    """The standing gate item: run at every gate, and the gate fails if this does."""
    assert register_problems((ROOT / "DECISIONS.md").read_text()) == []


SELF = "`test_decisions_register::test_the_register_check_is_live`"


def test_the_register_check_is_live() -> None:
    """Mutation check: an untested ✓, a deferral without a phase, a missing test, a missing row, and the old
    recorded-but-not-built status are each caught."""
    good = "- **Z1** x.\n- **Z2** y.\n## Implementation status\n| ID | S | E |\n|---|---|---|\n"
    rows = {
        "untested": "| Z1 | ✓ | it works |\n| Z2 | ⏸ | Phase 7 |",
        "no phase": f"| Z1 | ✓ | {SELF} |\n| Z2 | ⏸ | later |",
        "no test": "| Z1 | ✓ | `test_decisions_register::test_nothing_like_this` |\n| Z2 | ⏸ | Phase 7 |",
        "no row": "| Z1 | ⏸ | Phase 7 |",
        "not built": "| Z1 | ✗ | Phase 7 |\n| Z2 | ⏸ | Phase 7 |",
    }
    for case, body in rows.items():
        assert register_problems(good + body + "\n") != [], case
    clean = f"| Z1 | ✓ | {SELF}; probes b01\u2013b03 |\n| Z2 | ⏸ | Phase 7 |"
    assert register_problems(good + clean + "\n") == []


# -- entries that were process-only, now each checked by code (the register's standing rule) ---------------


def test_c6_two_model_slots_are_configured_separately() -> None:
    from tollgate.config import LLMSettings

    assert {"model_fast", "model_strong"} <= set(LLMSettings.model_fields)


def test_c7_the_frontend_verification_loop_exists_and_is_in_the_manual() -> None:
    scripts = json.loads((ROOT / "frontend" / "package.json").read_text())["scripts"]
    assert {"lint", "typecheck", "build"} <= set(scripts)
    assert "npm run lint && npm run typecheck && npm run build" in (ROOT / "CLAUDE.md").read_text()


def test_d3_only_free_tier_providers_can_be_configured() -> None:
    """Stay at $0: the provider setting only admits the free-tier endpoints (Groq, Gemini)."""
    from typing import get_args

    from tollgate.config import LLMSettings

    assert set(get_args(LLMSettings.model_fields["llm_provider"].annotation)) == {"groq", "gemini"}


# D6 (amended 2026-11-14, owner): the decision is that the assistant never pushes and never configures git
# credentials. The first test asserted that the repository has no remote, a side effect that fails in every
# clone (and in the owner's own checkout once they add a remote to push). The test now checks the intent: no
# script, CI config or tooling in the repo performs a push or configures a credential helper.
PUSH_OR_CREDENTIALS = re.compile(
    r"(?i)\bgit\b[^\n]{0,40}?\bpush\b"  # `git push`, `git -C x push`, "git", "push" in an argv list
    r"|credential[._-]?helper|\bgit\s+credential\b|\.git-credentials\b|\bGIT_ASKPASS\b"
    r"|\bgh\s+auth\s+(?:login|setup-git)\b"
)
# Tooling and config only: Markdown may state the rule, run files hold data, images are binary.
_TOOLING_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".cjs", ".mjs", ".json", ".toml", ".yml", ".yaml", ".sh",
                     ".bash", ".ps1", ".cfg", ".ini", ".env", ".example"}  # fmt: skip
_TOOLING_NAMES = {"Dockerfile", "Makefile", "Justfile", ".gitignore", ".dockerignore", ".npmrc"}


def _tooling_files() -> list[Path]:
    import shutil
    import subprocess

    git = shutil.which("git")
    assert git is not None
    listed = subprocess.run([git, "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    out = []
    for name in listed.splitlines():
        path = ROOT / name
        if (
            name.startswith(("backend/eval/runs/", "frontend/tests/e2e/__screenshots__/"))
            or not path.is_file()
        ):
            continue
        if path.resolve() == Path(__file__).resolve():
            continue  # this test names the patterns it looks for
        if path.suffix in _TOOLING_SUFFIXES or path.name in _TOOLING_NAMES:
            out.append(path)
    return out


def _push_or_credential_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if PUSH_OR_CREDENTIALS.search(line)]


def test_d6_no_tooling_in_the_repo_pushes_or_configures_git_credentials() -> None:
    """D6: nothing in the repo pushes or sets up credentials; the repo's git config holds no credential."""
    import shutil
    import subprocess

    found = {
        str(p.relative_to(ROOT)): hits
        for p in _tooling_files()
        if (hits := _push_or_credential_lines(p.read_text(errors="replace")))
    }
    assert found == {}
    git = shutil.which("git")
    assert git is not None
    local = subprocess.run(
        [git, "config", "--local", "--get-regexp", "credential"], cwd=ROOT, capture_output=True, text=True
    ).stdout
    assert local.strip() == ""


@pytest.mark.parametrize(
    "planted",
    [
        "git push origin main",
        "subprocess.run(['git', 'push', '--force'])",
        "git -C repo push",
        "git config --global credential.helper store",
        "printf 'https://x:y@github.com' > ~/.git-credentials",
        "export GIT_ASKPASS=/tmp/askpass.sh",
        "gh auth login --with-token",
        "gh auth setup-git",
    ],
)
def test_d6_the_scan_is_live(planted: str) -> None:
    """Every kind of push or credential setup the D6 scan looks for is caught when planted."""
    assert _push_or_credential_lines(f"echo start\n{planted}\necho done") == [planted]


def test_d6_the_scan_reads_real_tooling() -> None:
    """The scan is not vacuous: it reads the repo's scripts, Dockerfiles, compose file and manifests."""
    names = {str(p.relative_to(ROOT)) for p in _tooling_files()}
    for expected in ("backend/scripts/seed_store.py", "backend/Dockerfile", "docker-compose.yml",
                     "frontend/package.json", ".env.example"):  # fmt: skip
        assert expected in names


def test_d7_package_name() -> None:
    """D7 (amended 2026-11-14, owner): the Python package is `tollgate`. The folder name was the owner's local
    working directory; a clone lands wherever the cloner puts it, so it is no longer asserted."""
    import tollgate

    assert Path(tollgate.__file__).parent.name == "tollgate"


def test_t1_the_sdk_record_names_the_installed_agents_version() -> None:
    """Verified facts are recorded against the version actually installed (docs/sdk_surface.md)."""
    from importlib.metadata import version

    assert version("openai-agents") in (ROOT / "docs" / "sdk_surface.md").read_text()


def test_f6_the_leak_check_flags_a_table_that_grew() -> None:
    from tests.leakcheck import problems

    assert problems({"app.refunds": 1}, {"app.refunds": 2}, {}) != []
    assert problems({"app.refunds": 1}, {"app.refunds": 1}, {}) == []


async def test_f5_writes_through_the_test_pool_are_rolled_back(settings: object) -> None:
    from tests.txpool import rolled_back
    from tollgate.config import SupabaseSettings

    dsn = SupabaseSettings().database_url.get_secret_value()
    async with rolled_back(dsn) as pool:
        await pool.execute("UPDATE app.customers SET name = 'F5 probe' WHERE id = 'CUS-001'")
    conn = await asyncpg.connect(dsn)
    try:
        assert await conn.fetchval("SELECT name FROM app.customers WHERE id = 'CUS-001'") != "F5 probe"
    finally:
        await conn.close()


def test_j4_support_v4_samples_at_temperature_0_with_the_fixed_seed() -> None:
    from tests.fakes import ScriptedModel
    from tollgate.agents_def.support import PROMPT_VERSION, SAMPLING_SEED, build_support_agent

    settings = build_support_agent(ScriptedModel([])).model_settings
    assert PROMPT_VERSION == "support-v4"
    assert (settings.temperature, settings.extra_args) == (0, {"seed": SAMPLING_SEED})
