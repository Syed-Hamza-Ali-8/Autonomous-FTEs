"""Verify that each configured model returns structured tool calls (Section 2.2).

Two probes per model, both must pass for the model to be usable:
  raw  - one Chat Completions request with a tool; expects a function tool call with the right args.
  sdk  - the same task through the Agents SDK (OpenAIChatCompletionsModel), the path Tollgate uses.

Usage (from backend/):  uv run python scripts/probe_tools.py
Writes a result file to eval/runs/probe_tools/<utc-timestamp>.json (no keys, synthetic text only).
Exits 0 if at least one model passes both probes, else 1.
"""

import asyncio
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import openai
from agents import (
    Agent,
    AgentsException,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    function_tool,
    set_tracing_disabled,
)
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageFunctionToolCall, ChatCompletionToolParam

from tollgate.config import LLMSettings
from tollgate.errors import TollgateError
from tollgate.llm.provider import (
    configured_models,
    make_client,
    require_models_available,
    translate_api_error,
)

ORDER_ID = "ORD-1042"
QUESTION = f"What is the status of my order {ORDER_ID}?"
SYSTEM = "You are a store support assistant. Use the tools to look up order data."
RUNS_DIR = Path(__file__).resolve().parents[1] / "eval" / "runs" / "probe_tools"

RAW_TOOL: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "get_order_status",
        "description": "Look up the current status of an order by its ID.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "Order ID, e.g. ORD-1042"}},
            "required": ["order_id"],
            "additionalProperties": False,
        },
    },
}


async def probe_raw(client: AsyncOpenAI, model: str) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": QUESTION}],
            tools=[RAW_TOOL],
            tool_choice="auto",
            temperature=0.1,
        )
    except openai.APIStatusError as exc:
        raise translate_api_error(exc) from exc
    calls = [
        c for c in (resp.choices[0].message.tool_calls or [])
        if isinstance(c, ChatCompletionMessageFunctionToolCall)
    ]
    args: list[Any] = []
    for call in calls:
        try:
            args.append(json.loads(call.function.arguments))
        except json.JSONDecodeError:
            args.append({"_unparseable": call.function.arguments})
    passed = (
        len(calls) == 1
        and calls[0].function.name == "get_order_status"
        and args[0] == {"order_id": ORDER_ID}
    )
    return {
        "passed": passed,
        "tool_calls": [{"name": c.function.name, "args": a} for c, a in zip(calls, args, strict=True)],
        "text": resp.choices[0].message.content,
        "total_tokens": resp.usage.total_tokens if resp.usage else None,
        "latency_ms": round((time.perf_counter() - started) * 1000),
    }


async def probe_sdk(client: AsyncOpenAI, model: str) -> dict[str, Any]:
    seen: list[str] = []

    @function_tool
    def get_order_status(order_id: str) -> str:
        """Look up the current status of an order by its ID.

        Args:
            order_id: Order ID, e.g. ORD-1042.
        """
        seen.append(order_id)
        return "shipped"

    agent = Agent(
        name="probe",
        instructions=SYSTEM,
        tools=[get_order_status],
        model=OpenAIChatCompletionsModel(model=model, openai_client=client),
        model_settings=ModelSettings(temperature=0.1),
    )
    started = time.perf_counter()
    try:
        result = await Runner.run(
            agent, QUESTION, max_turns=3, run_config=RunConfig(tracing_disabled=True)
        )
    except openai.APIStatusError as exc:
        raise translate_api_error(exc) from exc
    final = str(result.final_output or "")
    return {
        "passed": seen == [ORDER_ID] and "shipped" in final.lower(),
        "tool_args_seen": seen,
        "final_output": final,
        "total_tokens": result.context_wrapper.usage.total_tokens,
        "latency_ms": round((time.perf_counter() - started) * 1000),
    }


async def main() -> int:
    set_tracing_disabled(True)
    settings = LLMSettings()
    client = make_client(settings)
    models = configured_models(settings)
    await require_models_available(client, models)

    results: dict[str, Any] = {}
    for model in models:
        entry: dict[str, Any] = {}
        for name, probe in (("raw", probe_raw), ("sdk", probe_sdk)):
            try:
                entry[name] = await probe(client, model)
            except (TollgateError, AgentsException, openai.APIError) as exc:
                # Recorded as a failure for this model, never replaced by a fake pass.
                entry[name] = {"passed": False, "error": f"{type(exc).__name__}: {exc}"}
        entry["usable"] = all(entry[n]["passed"] for n in ("raw", "sdk"))
        results[model] = entry
        print(f"{model}: raw={entry['raw']['passed']} sdk={entry['sdk']['passed']} "
              f"usable={entry['usable']}")

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out = RUNS_DIR / f"{stamp}.json"
    record = {"provider": settings.llm_provider, "base_url": settings.base_url(),
              "agents_sdk": "see docs/sdk_surface.md", "results": results}
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(f"recorded: {out.relative_to(RUNS_DIR.parents[2])}")
    return 0 if any(r["usable"] for r in results.values()) else 1


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except TollgateError as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(2)
