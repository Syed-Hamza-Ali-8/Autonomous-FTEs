"""Display strings the model reads (owner UI review items 3 and 20). Mirrors frontend/src/lib/format.ts."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from tollgate.domain.money import format_date, format_money, with_display


@pytest.mark.parametrize(
    ("cents", "ccy", "expected"),
    [
        (3200, "USD", "$32.00"),
        (5, "USD", "$0.05"),
        (100, "USD", "$1.00"),
        (2649500, "PKR", "Rs 26,495"),
        (2649550, "PKR", "Rs 26,495.50"),
        (0, "PKR", "Rs 0"),
        (150000000, "PKR", "Rs 1,500,000"),
        (-2649500, "PKR", "-Rs 26,495"),
    ],
)
def test_money(cents: int, ccy: str, expected: str) -> None:
    assert format_money(cents, ccy) == expected


def test_dates_are_utc_day_month_year() -> None:
    assert format_date(datetime(2026, 8, 21, 23, 30, tzinfo=UTC)) == "21 Aug 2026"
    assert format_date(datetime(2026, 8, 22, 2, 0, tzinfo=timezone(timedelta(hours=5)))) == "21 Aug 2026"
    assert format_date(datetime(2026, 9, 1, tzinfo=UTC)) == "1 Sep 2026"


def test_with_display_adds_money_and_date_strings_recursively() -> None:
    out = with_display(
        {
            "placed_at": "2026-08-21T10:00:00+00:00",
            "delivered_at": None,
            "total": {"amount_cents": 2649500, "currency": "PKR"},
            "events": [{"at": "2026-09-01T00:00:00+00:00", "description": "Delivered"}],
        }
    )
    assert out["placed_at_display"] == "21 Aug 2026"
    assert "delivered_at_display" not in out
    assert out["total"]["display"] == "Rs 26,495"
    assert out["events"][0]["at_display"] == "1 Sep 2026"
