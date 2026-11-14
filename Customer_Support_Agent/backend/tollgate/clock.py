"""The only source of "now" for decisions (owner rule, 2026-11-07; DECISIONS G1).

Policy rules, return windows, rolling 90-day limits, approval expiry and every timestamp written into
a row that later feeds a decision read time from an injected Clock, never from the system clock.
Tests and eval runs pin it to the fixture's fixed instant, so their results never change with the
calendar; the live demo uses SystemClock. tests/test_clock.py enforces this with a source scan.
"""

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)  # the one sanctioned wall-clock read for decisions


class FixedClock:
    def __init__(self, at: datetime) -> None:
        if at.tzinfo is None:
            raise ValueError("FixedClock needs a timezone-aware datetime")
        self._at = at.astimezone(UTC)

    def now(self) -> datetime:
        return self._at
