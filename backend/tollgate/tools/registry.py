"""Tool -> risk tier and the agents allowed to hold it (spec Sections 5, 6.1).

No agent may hold a tool outside its row (tests/test_tool_registry.py). Phase 1 has one agent,
`support`, with read tools only; Phase 3 adds write tools, Phase 5 the multi-agent rows.
"""

from dataclasses import dataclass
from typing import Literal

RiskTier = Literal["read", "low", "money"]


@dataclass(frozen=True)
class ToolSpec:
    tier: RiskTier
    agents: frozenset[str]


REGISTRY: dict[str, ToolSpec] = {
    "get_my_orders": ToolSpec("read", frozenset({"support"})),
    "get_order": ToolSpec("read", frozenset({"support"})),
    "get_shipment": ToolSpec("read", frozenset({"support"})),
    "get_refund_history": ToolSpec("read", frozenset({"support"})),
    # Phase 3 write tools: they only propose; the Action Gateway decides (invariant 1).
    "request_refund": ToolSpec("money", frozenset({"support"})),
    "issue_store_credit": ToolSpec("money", frozenset({"support"})),
    "cancel_order": ToolSpec("low", frozenset({"support"})),
    "update_shipping_address": ToolSpec("low", frozenset({"support"})),
    "create_ticket": ToolSpec("low", frozenset({"support"})),
    "escalate_to_human": ToolSpec("low", frozenset({"support"})),
}


def allowed_tools(agent: str) -> frozenset[str]:
    return frozenset(name for name, spec in REGISTRY.items() if agent in spec.agents)
