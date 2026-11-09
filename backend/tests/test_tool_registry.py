"""No agent holds a tool it isn't registered for (spec Section 5)."""

from tests.fakes import ScriptedModel
from tollgate.agents_def.support import AGENT_NAME, build_support_agent
from tollgate.tools.registry import REGISTRY, allowed_tools


def test_support_agent_tools_match_its_registry_row() -> None:
    agent = build_support_agent(ScriptedModel(steps=[]))
    held = {t.name for t in agent.tools}
    assert held == allowed_tools(AGENT_NAME)
    assert held <= set(REGISTRY)


def test_phase3_support_agent_holds_read_and_write_tools() -> None:
    tiers = {REGISTRY[name].tier for name in allowed_tools(AGENT_NAME)}
    assert tiers == {"read", "low", "money"}
    assert {"request_refund", "issue_store_credit"} == {
        n for n in allowed_tools(AGENT_NAME) if REGISTRY[n].tier == "money"
    }
