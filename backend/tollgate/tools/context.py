"""Per-turn run context handed to the Agents SDK. Tools read identity from here, never from arguments."""

import uuid
from dataclasses import dataclass, field

import asyncpg

from tollgate.auth.deps import CustomerContext
from tollgate.clock import Clock, SystemClock
from tollgate.domain.models import ActionCard, OrderSummary


@dataclass
class TurnContext:
    customer: CustomerContext
    pool: asyncpg.Pool
    conversation_id: uuid.UUID
    turn_id: uuid.UUID
    order_id: str | None = None  # set when the chat was opened from an order page
    # Orders the customer's own tool results referred to this turn, for inline order cards (13.3).
    referenced_orders: dict[str, OrderSummary] = field(default_factory=dict)
    tool_calls: int = 0
    clock: Clock = field(default_factory=SystemClock)  # injected; the policy reads time only here (G1)
    prompt_version: str | None = None  # recorded on every Action Gateway audit row (spec 6.2 step 7)
    # What this turn's write submissions did, appended by the gateway: the source for ActionCards and for
    # the claim check (invariant 10), never the model's text.
    actions: list[ActionCard] = field(default_factory=list)
