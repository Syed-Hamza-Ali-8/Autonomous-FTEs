"""Phase 1 single agent: answers order and tracking questions with read tools only."""

from pathlib import Path

from agents import Agent, Model, ModelSettings, RunContextWrapper

from tollgate.tools.context import TurnContext
from tollgate.tools.read_tools import READ_TOOLS
from tollgate.tools.registry import allowed_tools

AGENT_NAME = "support"
PROMPT_VERSION = "support-v1"
PROMPT = (Path(__file__).parent / "prompts" / f"{PROMPT_VERSION}.md").read_text()


def instructions(ctx: RunContextWrapper[TurnContext], agent: Agent[TurnContext]) -> str:
    if ctx.context.order_id:
        # The order id was ownership-checked when the conversation was created.
        return f"{PROMPT}\nContext: the customer opened this chat from order {ctx.context.order_id}.\n"
    return PROMPT


def build_support_agent(model: Model) -> Agent[TurnContext]:
    tools = [READ_TOOLS[name] for name in sorted(allowed_tools(AGENT_NAME))]
    return Agent[TurnContext](
        name=AGENT_NAME,
        instructions=instructions,
        tools=list(tools),
        model=model,
        # include_usage: streamed Chat Completions only report tokens when asked (budget accounting).
        model_settings=ModelSettings(temperature=0.2, parallel_tool_calls=False, include_usage=True),
    )
