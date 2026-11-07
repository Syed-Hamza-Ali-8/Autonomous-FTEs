"""POST /v1/chat (SSE) and the latest conversation for the chat panel (DECISIONS B9, C1)."""

import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import EventSourceResponse
from pydantic import BaseModel, Field

from tollgate.agents_def.events import ChatEvent
from tollgate.agents_def.runner import ChatTurn, LLMRuntime, run_turn
from tollgate.auth.deps import Customer, Pool
from tollgate.domain import conversations as conv
from tollgate.errors import NotFoundError

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatRequest(BaseModel):
    model_config = {"extra": "forbid"}

    client_message_id: uuid.UUID  # generated per message by the client; repeats map to one turn
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: uuid.UUID | None = None  # omit to start a new conversation
    order_id: str | None = Field(default=None, pattern=r"^ORD-[0-9]{4}$")  # "Get help with this order"


async def prepared_turn(body: ChatRequest, customer: Customer, pool: Pool) -> ChatTurn:
    """Resolve and ownership-check the conversation BEFORE streaming, so a foreign id is a real 404."""
    async with pool.acquire() as conn:
        if body.conversation_id is not None:
            owned = await conv.owned_conversation(conn, customer.customer_id, body.conversation_id)
            if owned is None:
                raise NotFoundError("conversation")
        else:
            if body.order_id is not None and not await conv.owns_order(
                conn, customer.customer_id, body.order_id
            ):
                raise NotFoundError("order")
            new_id = await conv.create_conversation(conn, customer.customer_id, body.order_id)
            owned = conv.OwnedConversation(id=new_id, order_id=body.order_id)
    return ChatTurn(
        customer=customer,
        conversation=owned,
        client_message_id=body.client_message_id,
        message=body.message.strip(),
    )


@router.post("/chat", response_class=EventSourceResponse)
async def chat(
    request: Request, turn: Annotated[ChatTurn, Depends(prepared_turn)], pool: Pool
) -> AsyncIterator[ChatEvent]:
    llm: LLMRuntime = request.app.state.llm
    async for event in run_turn(pool, llm, turn, request.app.state.clock):
        yield event  # type: ignore[misc]  # runner yields ChatEvent members


@router.get("/conversations/latest")
async def latest_conversation(customer: Customer, pool: Pool) -> conv.ConversationOut | None:
    async with pool.acquire() as conn:
        return await conv.latest_conversation(conn, customer.customer_id)
