"""A scripted stand-in for the LLM (zero tokens). Implements the Agents SDK `Model` interface.

Each model call consumes the next step: a tool call, a text reply, or an exception. Phase 3 builds the
malicious-model stub (Section 9.3) on the same idea.
"""

import json
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from agents import Model, ModelResponse, Usage
from openai.types.responses import (
    Response,
    ResponseCompletedEvent,
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)


@dataclass(frozen=True)
class CallTool:
    name: str
    args: dict[str, Any]


@dataclass(frozen=True)
class Say:
    text: str


@dataclass(frozen=True)
class Fail:
    exc: BaseException


Step = CallTool | Say | Fail


class ScriptedModel(Model):
    # A plain class, not a dataclass: the SDK snapshots agents with dataclasses.asdict, which would
    # deep-copy a dataclass model (and its scripted exceptions). Real SDK models aren't dataclasses either.
    def __init__(self, steps: list[Step]) -> None:
        self.steps = steps
        self.calls = 0
        self.inputs: list[Any] = []

    def _next(self, input: Any) -> list[Any]:
        self.calls += 1
        self.inputs.append(input)
        if not self.steps:
            raise AssertionError("ScriptedModel ran out of steps")
        step = self.steps.pop(0)
        if isinstance(step, Fail):
            raise step.exc
        if isinstance(step, CallTool):
            return [
                ResponseFunctionToolCall(
                    type="function_call",
                    call_id=f"call_{self.calls}",
                    name=step.name,
                    arguments=json.dumps(step.args),
                )
            ]
        return [
            ResponseOutputMessage(
                id=f"msg_{self.calls}",
                type="message",
                role="assistant",
                status="completed",
                content=[ResponseOutputText(type="output_text", text=step.text, annotations=[])],
            )
        ]

    async def get_response(self, *args: Any, **kwargs: Any) -> ModelResponse:
        output = self._next(args[1] if len(args) > 1 else kwargs.get("input"))
        return ModelResponse(output=output, usage=Usage(requests=1, total_tokens=100), response_id=None)

    async def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:  # type: ignore[override]
        output = self._next(args[1] if len(args) > 1 else kwargs.get("input"))
        response = Response(
            id=f"resp_{self.calls}",
            created_at=time.time(),
            model="scripted",
            object="response",
            output=output,
            parallel_tool_calls=False,
            tool_choice="auto",
            tools=[],
        )
        yield ResponseCompletedEvent(type="response.completed", response=response, sequence_number=0)
