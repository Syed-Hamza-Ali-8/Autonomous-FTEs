"""Token-aware pacing for real-model eval runs (owner, Phase 2 gate; tightened 2026-11-09).

Instead of hitting the provider's per-minute limit and retrying, the runner asks the throttle for headroom
BEFORE each model call:
- Each call's cost is ESTIMATED from the request itself: instructions, input and tool schemas, at about 3
  characters per token (generous), plus an output reserve (the largest output seen, at least 1,024). It is
  never below the largest whole call seen so far.
- The call waits until the rolling 60-second window has room under `target_fraction` of the limit (default
  90%, a margin for estimation error). When the call completes, its reservation is replaced by the actual
  usage, or by the rejected-request charge if it fails.
- The window is persisted (`window_file`, under the git-ignored `.tollgate/`), so a run's first call sees
  the previous run's last minute instead of being sent blind.

Waiting is in-session `await` only (Rule 0.1.12: no detached scheduling). Real (wall) time on purpose:
provider limits run on the wall clock, and the window must carry across processes.
"""

import asyncio
import json
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from math import ceil
from pathlib import Path
from typing import Any

from agents import Model, ModelResponse
from openai.types.responses import ResponseCompletedEvent

WINDOW_S = 60.0


@dataclass
class _Entry:
    at: float
    tokens: int


CHARS_PER_TOKEN = 3.0  # deliberately generous: real tokenisers average closer to 4 characters
MIN_OUTPUT_RESERVE = 1_024


def request_chars(args: tuple[Any, ...], kwargs: dict[str, Any]) -> int:
    """Characters the provider will tokenise in one model call: instructions, input and tool schemas.
    Positions follow `Model.stream_response(system_instructions, input, model_settings, tools, ...)`."""

    def arg(i: int, name: str) -> Any:
        return args[i] if len(args) > i else kwargs.get(name)

    tool_text = [
        json.dumps(
            [getattr(t, "name", ""), getattr(t, "description", ""), getattr(t, "params_json_schema", {})]
        )
        for t in arg(3, "tools") or []
    ]
    system = arg(0, "system_instructions") or ""
    return len(system) + len(json.dumps(arg(1, "input"), default=str)) + sum(map(len, tool_text))


@dataclass
class TokenThrottle:
    tokens_per_minute: int
    requests_per_minute: int
    initial_estimate: int = 2_500
    target_fraction: float = 0.9
    window_file: Path | None = None
    now: Callable[[], float] = time.time
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep
    waited_s: float = 0.0
    _entries: list[_Entry] = field(default_factory=list)
    _largest: int = 0
    _largest_output: int = MIN_OUTPUT_RESERVE

    def __post_init__(self) -> None:
        if self.window_file is not None and self.window_file.exists():
            t = self.now()
            for raw in self.window_file.read_text().splitlines():
                if raw.strip():
                    row = json.loads(raw)
                    if t - row["at"] < WINDOW_S:
                        self._entries.append(_Entry(row["at"], int(row["tokens"])))

    def _prune(self, t: float) -> None:
        self._entries = [e for e in self._entries if t - e.at < WINDOW_S]

    def _save(self) -> None:
        if self.window_file is None:
            return
        self.window_file.parent.mkdir(parents=True, exist_ok=True)
        self._prune(self.now())
        self.window_file.write_text(
            "".join(json.dumps({"at": e.at, "tokens": e.tokens}) + "\n" for e in self._entries)
        )

    @property
    def limit(self) -> int:
        return int(self.tokens_per_minute * self.target_fraction)

    @property
    def estimate(self) -> int:
        return max(self._largest, self.initial_estimate)

    def estimate_for(self, chars: int) -> int:
        return max(self.estimate, ceil(chars / CHARS_PER_TOKEN) + self._largest_output)

    async def acquire(self, need: int | None = None) -> _Entry:
        need = min(need if need is not None else self.estimate, self.limit)
        while True:
            t = self.now()
            self._prune(t)
            used = sum(e.tokens for e in self._entries)
            if used + need <= self.limit and len(self._entries) + 1 <= self.requests_per_minute:
                entry = _Entry(t, need)
                self._entries.append(entry)
                return entry
            # Wait until the oldest entry leaves the window, then re-check.
            wait = max(0.05, WINDOW_S - (t - self._entries[0].at))
            self.waited_s += wait
            await self.sleep(wait)

    def settle(self, entry: _Entry, actual_tokens: int, output_tokens: int | None = None) -> None:
        entry.tokens = actual_tokens
        self._largest = max(self._largest, actual_tokens)
        if output_tokens is not None:
            self._largest_output = max(self._largest_output, output_tokens)
        self._save()


class ThrottledModel(Model):
    def __init__(self, inner: Model, throttle: TokenThrottle, rejected_charge: int) -> None:
        self.inner = inner
        self.throttle = throttle
        self.rejected_charge = rejected_charge

    async def get_response(self, *args: Any, **kwargs: Any) -> ModelResponse:
        raise NotImplementedError("eval runs stream; get_response is not used")

    async def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        entry = await self.throttle.acquire(self.throttle.estimate_for(request_chars(args, kwargs)))
        settled = False
        try:
            async for event in self.inner.stream_response(*args, **kwargs):
                if isinstance(event, ResponseCompletedEvent):
                    usage = event.response.usage
                    self.throttle.settle(
                        entry,
                        usage.total_tokens if usage else entry.tokens,
                        usage.output_tokens if usage else None,
                    )
                    settled = True
                yield event
        finally:
            if not settled:  # rejected or failed: assume it consumed tokens (over-count, item 2)
                self.throttle.settle(entry, max(entry.tokens, self.rejected_charge))
