"""Display formatting for the model's tool results. Integer maths only; never floats.

Money (DECISIONS A2, owner UI review): USD always shows cents ($32.00); PKR drops ".00" when the
paisa part is zero (Rs 26,495) and shows it otherwise (Rs 26,495.50). frontend/src/lib/format.ts
implements the same rule, so what the model says matches what the page shows.
Dates: "21 Aug 2026", in UTC, matching the frontend's formatDate.
"""

from datetime import UTC, datetime
from typing import Any

SYMBOL = {"USD": "$", "PKR": "Rs "}
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def format_money(amount_cents: int, currency: str) -> str:
    sign = "-" if amount_cents < 0 else ""
    major, minor = divmod(abs(amount_cents), 100)
    cents = "" if currency == "PKR" and minor == 0 else f".{minor:02d}"
    return f"{sign}{SYMBOL[currency]}{major:,}{cents}"


def format_date(value: datetime) -> str:
    d = value.astimezone(UTC)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def with_display(value: Any) -> Any:
    """Recursively add `display` to {amount_cents, currency} objects and `<key>_display` to ISO dates."""
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            out[k] = with_display(v)
            if (k == "at" or k.endswith("_at")) and isinstance(v, str):
                try:
                    out[f"{k}_display"] = format_date(datetime.fromisoformat(v))
                except ValueError:
                    pass
        if isinstance(out.get("amount_cents"), int) and out.get("currency") in SYMBOL:
            out["display"] = format_money(out["amount_cents"], out["currency"])
        return out
    if isinstance(value, list):
        return [with_display(v) for v in value]
    return value
