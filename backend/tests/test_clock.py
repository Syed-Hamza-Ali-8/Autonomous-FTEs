"""Decisions read time only from the injected Clock (owner rule 2026-11-07, DECISIONS G1).

A source scan keeps wall-clock reads out of application code except the sanctioned places below.
The "eval result doesn't move with the system date" proof is in tests/test_eval_scoring.py.
"""

import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tollgate.clock import FixedClock, SystemClock
from tollgate.config import AppSettings

APP = Path(__file__).resolve().parents[1] / "tollgate"
WALL_CLOCK = re.compile(
    r"datetime\.now|datetime\.utcnow|date\.today|time\.time\(|\bnow\(\)|CURRENT_DATE|CURRENT_TIMESTAMP|localtimestamp"
)

# (file, fragment that must appear on the line): each allowed because it is NOT a decision.
ALLOWED = {
    ("clock.py", "datetime.now(UTC)"): "SystemClock itself: the one sanctioned source for decisions",
    ("llm/budget.py", "now() - interval '24 hours'"): "provider token limits run on real time",
    ("llm/budget.py", "datetime.now(UTC)"): "spend ledger: provider limits run on real time",
    ("agents_def/runner.py", "datetime.now(UTC)"): "run_log telemetry: when the real call happened",
    (
        "domain/conversations.py",
        "updated_at = now()",
    ): "record-keeping; orders conversations, decides nothing",
}


def test_wall_clock_reads_only_in_sanctioned_places() -> None:
    found = []
    for path in APP.rglob("*.py"):
        rel = path.relative_to(APP).as_posix()
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if WALL_CLOCK.search(line) and not any(f == rel and frag in line for f, frag in ALLOWED):
                found.append(f"{rel}:{n}: {line.strip()}")
    assert found == [], "decision code must read time from the injected Clock"


def test_allowlist_has_no_stale_entries() -> None:
    for (rel, frag), reason in ALLOWED.items():
        assert frag in (APP / rel).read_text(), f"stale allowance ({reason}): {rel}"


def test_fixed_clock_never_moves() -> None:
    at = datetime(2026, 11, 7, 12, tzinfo=UTC)
    clock = FixedClock(at)
    assert clock.now() == at == clock.now()
    with pytest.raises(ValueError):
        FixedClock(datetime(2026, 11, 7))  # naive datetimes are ambiguous


def test_app_clock_is_pinned_by_setting_and_real_otherwise() -> None:
    pinned = AppSettings(clock_fixed_at=datetime(2026, 11, 7, 12, tzinfo=UTC)).clock()
    assert isinstance(pinned, FixedClock) and pinned.now().year == 2026
    assert isinstance(AppSettings(clock_fixed_at=None).clock(), SystemClock)
