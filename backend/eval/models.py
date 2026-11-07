"""Record / replay for eval runs (spec 2.3): record model outputs once, replay them to re-score logic.

RecordingModel wraps the real model and saves each call's final Responses-API object (output items and
usage). ReplayModel serves those responses back in order with zero tokens; tools still execute against
the database, so changes to tools, policy or scoring are re-measured. If a run needs more model calls
than were recorded, replay stops with ReplayDiverged instead of inventing an answer (Rule 0.1.7).
"""

import hashlib
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from agents import Model, ModelResponse
from openai.types.responses import Response, ResponseCompletedEvent


class ReplayDiverged(RuntimeError):
    """Replay can't faithfully continue: a call wasn't recorded, a recording was altered, or the
    model would now be sent different input than when it was recorded."""


def _canonical(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _canonical(value.model_dump(mode="json"))
    if isinstance(value, dict):
        # Absent and null are the same thing: a recorded item revalidated on replay serialises unset
        # fields as null, a live one omits them. Without this, every replay would report drift.
        return {k: _canonical(v) for k, v in sorted(value.items()) if v is not None}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    return value


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value), sort_keys=True, default=str).encode()).hexdigest()


def input_fingerprint(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """What the model is sent: instructions, conversation so far and tool definitions (not settings)."""
    instructions = args[0] if args else kwargs.get("system_instructions")
    items = args[1] if len(args) > 1 else kwargs.get("input")
    # Model.stream_response(system_instructions, input, model_settings, tools, output_schema, ...)
    tools = args[3] if len(args) > 3 else kwargs.get("tools", [])
    tool_sigs = sorted(
        (getattr(t, "name", str(t)), digest(getattr(t, "params_json_schema", {}))) for t in tools or []
    )
    return digest({"instructions": instructions, "input": items, "tools": tool_sigs})


class RecordingModel(Model):
    """Buffers each turn attempt's calls; the runner commits them only when the attempt completes.

    A rate-limited attempt is discarded and retried, so a recording never contains a failed attempt's
    stale calls (which a replay would otherwise serve first).
    """

    def __init__(self, inner: Model, sink: Path) -> None:
        self.inner = inner
        self.sink = sink
        self.calls = 0
        self._pending: list[str] = []

    def reset(self) -> None:
        """Start the scenario's recording fresh (a resumed scenario is re-recorded from scratch)."""
        self.sink.parent.mkdir(parents=True, exist_ok=True)
        self.sink.write_text("")
        self._pending.clear()

    def commit(self) -> None:
        with self.sink.open("a") as f:
            f.writelines(self._pending)
        self._pending.clear()

    def discard(self) -> None:
        self._pending.clear()

    async def get_response(self, *args: Any, **kwargs: Any) -> ModelResponse:
        raise NotImplementedError("eval runs stream; get_response is not used")

    async def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        async for event in self.inner.stream_response(*args, **kwargs):
            if isinstance(event, ResponseCompletedEvent):
                self.calls += 1
                response = event.response.model_dump(mode="json")
                entry = {
                    "response": response,
                    "sha256": digest(response),  # integrity: an altered recording is detected
                    "input_sha256": input_fingerprint(args, kwargs),  # drift: different input stops replay
                }
                self._pending.append(json.dumps(entry) + "\n")
            yield event


class ReplayModel(Model):
    def __init__(self, source: Path, allow_drift: bool = False) -> None:
        lines = source.read_text().splitlines() if source.exists() else []
        self.entries = [json.loads(line) for line in lines if line.strip()]
        self.allow_drift = allow_drift
        self.calls = 0
        self.unsealed = 0  # legacy entries recorded before integrity/drift hashes existed
        self.drifted = 0
        # The chat runner turns unexpected exceptions into a friendly error event, which would hide a
        # divergence; the harness checks this flag after every turn and stops the run instead.
        self.diverged: str | None = None

    def _fail(self, why: str) -> ReplayDiverged:
        self.diverged = why
        return ReplayDiverged(why)

    async def get_response(self, *args: Any, **kwargs: Any) -> ModelResponse:
        raise NotImplementedError("eval runs stream; get_response is not used")

    async def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        if self.calls >= len(self.entries):
            raise self._fail(f"call {self.calls + 1} was not recorded ({len(self.entries)} recorded)")
        entry = self.entries[self.calls]
        self.calls += 1
        if "sha256" not in entry:
            self.unsealed += 1
        elif digest(entry["response"]) != entry["sha256"]:
            raise self._fail(f"call {self.calls}: recording altered (integrity hash mismatch)")
        if "input_sha256" in entry and input_fingerprint(args, kwargs) != entry["input_sha256"]:
            if not self.allow_drift:
                raise self._fail(f"call {self.calls}: input drift (the model would now see different input)")
            self.drifted += 1
        response = Response.model_validate(entry["response"])
        yield ResponseCompletedEvent(type="response.completed", response=response, sequence_number=0)
