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
    assert tiers == {"read", "contact", "order", "money"}
    assert {"request_refund", "issue_store_credit"} == {
        n for n in allowed_tools(AGENT_NAME) if REGISTRY[n].tier == "money"
    }


def test_contact_tier_is_exactly_ticket_and_escalation() -> None:
    """J3 / P4-4: the tiers as pre-registered. The contact tier is never queued and never fraud-routed."""
    by_tier: dict[str, set[str]] = {}
    for name, spec in REGISTRY.items():
        by_tier.setdefault(spec.tier, set()).add(name)
    assert by_tier["contact"] == {"create_ticket", "escalate_to_human"}
    assert by_tier["order"] == {"cancel_order", "update_shipping_address"}
    assert by_tier["money"] == {"request_refund", "issue_store_credit"}


def test_only_order_and_money_tiers_have_an_approval_path() -> None:
    from tollgate.approvals import service

    queueable = {n for n, s in REGISTRY.items() if s.tier in ("order", "money")}
    assert set(service.PATHS) == queueable
    assert service.NEVER_QUEUED == {n for n, s in REGISTRY.items() if s.tier == "contact"}
