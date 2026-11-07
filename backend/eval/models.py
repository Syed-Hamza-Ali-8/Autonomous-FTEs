"""Record / replay for eval runs (spec 2.3): record model outputs once, replay them to re-score logic.

RecordingModel wraps the real model and saves each call's final Responses-API object (output items and
usage). ReplayModel serves those responses back in order with zero tokens; tools still execute against
the database, so changes to tools, policy or scoring are re-measured. If a run needs more model calls
than were recorded, replay stops with ReplayDiverged instead of inventing an answer (Rule 0.1.7).
"""

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from agents import Model, ModelResponse
from openai.types.responses import Response, ResponseCompletedEvent


class ReplayDiverged(RuntimeError):
    """The replayed run asked for a model call that was never recorded."""


class RecordingModel(Model):
    def __init__(self, inner: Model, sink: Path) -> None:
        self.inner = inner
        self.sink = sink
        self.calls = 0

    async def get_response(self, *args: Any, **kwargs: Any) -> ModelResponse:
        raise NotImplementedError("eval runs stream; get_response is not used")

    async def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        async for event in self.inner.stream_response(*args, **kwargs):
            if isinstance(event, ResponseCompletedEvent):
                self.calls += 1
                with self.sink.open("a") as f:
                    f.write(
                        json.dumps({"call": self.calls, "response": event.response.model_dump(mode="json")})
                        + "\n"
                    )
            yield event


class ReplayModel(Model):
    def __init__(self, source: Path) -> None:
        lines = source.read_text().splitlines() if source.exists() else []
        self.responses = [json.loads(line)["response"] for line in lines if line.strip()]
        self.calls = 0

    async def get_response(self, *args: Any, **kwargs: Any) -> ModelResponse:
        raise NotImplementedError("eval runs stream; get_response is not used")

    async def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        if self.calls >= len(self.responses):
            raise ReplayDiverged(f"call {self.calls + 1} was not recorded ({len(self.responses)} recorded)")
        response = Response.model_validate(self.responses[self.calls])
        self.calls += 1
        yield ResponseCompletedEvent(type="response.completed", response=response, sequence_number=0)
