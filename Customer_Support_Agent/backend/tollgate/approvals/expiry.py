"""When a pending approval stops counting: the ONE derived expiry predicate (DECISIONS B7, J8; A3-P4).

A request waiting for staff is expired once `now >= created_at + APPROVAL_TTL`, with `now` from the injected
clock (G1). Every reader of pending state applies this, so nothing depends on the lazy expiry write having
happened: the action status and card, order-detail refund rows, the refundable remainder, the rolling window,
the same-lines check, and decisions. A pending row is LIVE (still holds its lines, remainder and window share)
only while `created_at > live_after(now)`, which is the same condition.

The TTL is an internal control parameter (tier C, I15): it is never stated to customers or the model.
No SQL here, nothing that writes: tools may import this (af06).
"""

from datetime import datetime, timedelta

APPROVAL_TTL = timedelta(hours=48)


def live_after(now: datetime) -> datetime:
    """A pending request created strictly after this instant is still live."""
    return now - APPROVAL_TTL


def is_expired(created_at: datetime, now: datetime) -> bool:
    return created_at <= live_after(now)
