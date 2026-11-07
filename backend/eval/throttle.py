"""Token-aware pacing for real-model eval runs (owner, Phase 2 gate).

Instead of hitting the provider's per-minute limit and retrying, the runner asks the throttle for
headroom BEFORE each model call. The throttle keeps a rolling 60-second window of tokens and requests;
a call reserves an estimate (the largest call seen so far), which is replaced by the actual usage when
the call completes, or by the rejected-request charge if it fails. Waiting is in-session `await`
only (Rule 0.1.12: no detached scheduling). Real time on purpose: provider limits run on the wall clock.
"""

import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from agents import Model, ModelResponse
from openai.types.responses import ResponseCompletedEvent

WINDOW_S = 60.0


@dataclass
class _Entry:
    at: float
    tokens: int


@dataclass
class TokenThrottle:
    tokens_per_minute: int
    requests_per_minute: int
    initial_estimate: int = 2_500
    now: Callable[[], float] = time.monotonic
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep
    waited_s: float = 0.0
    _entries: list[_Entry] = field(default_factory=list)
    _largest: int = 0

    def _prune(self, t: float) -> None:
        self._entries = [e for e in self._entries if t - e.at < WINDOW_S]

    @property
    def estimate(self) -> int:
        return max(self._largest, self.initial_estimate)

    async def acquire(self) -> _Entry:
        need = min(self.estimate, self.tokens_per_minute)
        while True:
            t = self.now()
            self._prune(t)
            used = sum(e.tokens for e in self._entries)
            if used + need <= self.tokens_per_minute and len(self._entries) + 1 <= self.requests_per_minute:
                entry = _Entry(t, need)
                self._entries.append(entry)
                return entry
            # Wait until the oldest entry leaves the window, then re-check.
            wait = max(0.05, WINDOW_S - (t - self._entries[0].at))
            self.waited_s += wait
            await self.sleep(wait)

    def settle(self, entry: _Entry, actual_tokens: int) -> None:
        entry.tokens = actual_tokens
        self._largest = max(self._largest, actual_tokens)


class ThrottledModel(Model):
    def __init__(self, inner: Model, throttle: TokenThrottle, rejected_charge: int) -> None:
        self.inner = inner
        self.throttle = throttle
        self.rejected_charge = rejected_charge

    async def get_response(self, *args: Any, **kwargs: Any) -> ModelResponse:
        raise NotImplementedError("eval runs stream; get_response is not used")

    async def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        entry = await self.throttle.acquire()
        settled = False
        try:
            async for event in self.inner.stream_response(*args, **kwargs):
                if isinstance(event, ResponseCompletedEvent):
                    usage = event.response.usage
                    self.throttle.settle(entry, usage.total_tokens if usage else entry.tokens)
                    settled = True
                yield event
        finally:
            if not settled:  # rejected or failed: assume it consumed tokens (over-count, item 2)
                self.throttle.settle(entry, max(entry.tokens, self.rejected_charge))
