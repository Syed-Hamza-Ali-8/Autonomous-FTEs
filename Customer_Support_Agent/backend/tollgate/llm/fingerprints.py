"""The provider's `system_fingerprint`, recorded for every model call (pre-registration 12.4; DECISIONS J4).

At temperature 0 with a fixed seed, outputs can still change when the provider changes its serving backend;
the fingerprint is how that shows. openai-agents 0.24.0 does not surface it from streamed Chat Completions, so
the client's `chat.completions.create` is wrapped: the stream passes through unchanged (its `.response`, which
the SDK reads for the request id, is kept), and the first fingerprint each call reports is appended to the
turn's list. The runner stores that list on the turn's run_log row.
"""

from collections.abc import AsyncIterator
from contextvars import ContextVar
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

# The current turn's fingerprints, one per model call. None outside a turn (nothing is recorded).
CURRENT: ContextVar[list[str] | None] = ContextVar("system_fingerprints", default=None)


def _record(fingerprint: str | None) -> None:
    sink = CURRENT.get()
    if sink is not None:
        sink.append(fingerprint or "unreported")  # one entry per call, so a missing one is visible too


class _RecordedStream:
    """A pass-through view of a streamed response that records the call's fingerprint once."""

    def __init__(self, stream: Any) -> None:
        self._stream = stream
        self.response = getattr(stream, "response", None)  # read by the SDK for the request id

    def __aiter__(self) -> AsyncIterator[Any]:
        return self._chunks()

    async def _chunks(self) -> AsyncIterator[Any]:
        seen = False
        async for chunk in self._stream:
            if not seen and getattr(chunk, "system_fingerprint", None):
                _record(chunk.system_fingerprint)
                seen = True
            yield chunk
        if not seen:
            _record(None)


def instrument(client: AsyncOpenAI) -> AsyncOpenAI:
    create = client.chat.completions.create

    async def recorded(*args: Any, **kwargs: Any) -> Any:
        out = await create(*args, **kwargs)
        if isinstance(out, ChatCompletion):
            _record(out.system_fingerprint)
            return out
        return _RecordedStream(out)

    setattr(client.chat.completions, "create", recorded)  # noqa: B010 - wrapping a bound method on purpose
    return client
