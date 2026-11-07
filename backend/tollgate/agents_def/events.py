"""Server-sent chat events. A discriminated union on `type`, documented in OpenAPI for the frontend.

DECISIONS C1: progress, tool steps and order cards stream live; the assistant's reply text is sent
once, as `reply`, only after the claim check has passed. No token-level text deltas are ever sent.
"""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from tollgate.domain.models import OrderSummary


class TurnStarted(BaseModel):
    type: Literal["turn_started"] = "turn_started"
    conversation_id: uuid.UUID
    turn_id: uuid.UUID


class Progress(BaseModel):
    type: Literal["progress"] = "progress"
    label: str  # customer-safe, e.g. "Checking tracking..."; never tool arguments or internals


class OrderRef(BaseModel):
    type: Literal["order_ref"] = "order_ref"
    order: OrderSummary  # from the customer's own tool results, never parsed from model text


class Reply(BaseModel):
    type: Literal["reply"] = "reply"
    message_id: int
    text: str
    created_at: datetime


ErrorCode = Literal[
    "rate_limited", "budget_exhausted", "provider_error", "server_error", "duplicate_in_progress"
]


class ChatError(BaseModel):
    type: Literal["error"] = "error"
    code: ErrorCode
    message: str  # friendly, no stack traces, rule names or internal IDs
    retry_after_s: float | None = None


class Done(BaseModel):
    type: Literal["done"] = "done"


ChatEvent = Annotated[
    TurnStarted | Progress | OrderRef | Reply | ChatError | Done, Field(discriminator="type")
]

FRIENDLY: dict[ErrorCode, str] = {
    "rate_limited": "I'm getting a lot of requests right now. Please try again in a moment.",
    "budget_exhausted": "Support chat is busy right now. Please try again later.",
    "provider_error": "Something went wrong on our side. Please try again.",
    "server_error": "Something went wrong on our side. Please try again.",
    "duplicate_in_progress": "I'm still working on that message.",
}


def error(code: ErrorCode, retry_after_s: float | None = None) -> ChatError:
    return ChatError(code=code, message=FRIENDLY[code], retry_after_s=retry_after_s)
