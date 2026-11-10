"""Single support agent (Phase 3): read tools plus write tools that only propose; the gateway decides."""

import hashlib
import json
from pathlib import Path

from agents import Agent, FunctionTool, Model, ModelSettings, RunContextWrapper

from tollgate.actions import gateway, hints
from tollgate.tools.context import TurnContext
from tollgate.tools.read_tools import READ_TOOLS
from tollgate.tools.registry import allowed_tools
from tollgate.tools.write_tools import WRITE_TOOLS

AGENT_NAME = "support"
PROMPT_VERSION = "support-v3"
PROMPT = (Path(__file__).parent / "prompts" / f"{PROMPT_VERSION}.md").read_text()


def instructions(ctx: RunContextWrapper[TurnContext], agent: Agent[TurnContext]) -> str:
    if ctx.context.order_id:
        # The order id was ownership-checked when the conversation was created.
        return f"{PROMPT}\nContext: the customer opened this chat from order {ctx.context.order_id}.\n"
    return PROMPT


ALL_TOOLS = {**READ_TOOLS, **WRITE_TOOLS}


def agent_tools() -> list[FunctionTool]:
    return [ALL_TOOLS[name] for name in sorted(allowed_tools(AGENT_NAME))]


def tool_schema_version() -> str:
    """Fingerprint of the tool schemas the model sees. Recordings are tied to it (CLAUDE.md token rules):
    when it changes, affected recordings are re-recorded and the old ones kept, labelled."""
    shape = [(t.name, t.description, t.params_json_schema) for t in agent_tools()]
    # The model also sees what the tools RETURN, so the result format is part of the version too.
    statuses = (
        "pending",
        "paid",
        "packed",
        "shipped",
        "delivered",
        "cancelled",
        "refunded",
        "partially_refunded",
    )
    hint_table = [hints.hint(code, st) for code in hints.REASON_CODES for st in statuses]
    hint_table += [hints.PENDING, hints.NOT_FOUND, hints.REJECTED]
    material = {"tools": shape, "result_format": gateway.RESULT_FORMAT, "hints": hint_table}
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()[:12]


def build_support_agent(model: Model) -> Agent[TurnContext]:
    tools = agent_tools()
    return Agent[TurnContext](
        name=AGENT_NAME,
        instructions=instructions,
        tools=list(tools),
        model=model,
        # include_usage: streamed Chat Completions only report tokens when asked (budget accounting).
        model_settings=ModelSettings(temperature=0.2, parallel_tool_calls=False, include_usage=True),
    )
