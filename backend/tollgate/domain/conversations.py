"""Conversations and messages. Ownership is the conversation's customer_id, filtered in SQL."""

import json
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from tollgate.actions import cards as action_cards
from tollgate.approvals import expiry
from tollgate.db import Conn
from tollgate.domain.models import ActionCard, ActionKind, OrderSummary
from tollgate.domain.orders import list_orders


class MessageOut(BaseModel):
    id: int
    role: Literal["customer", "assistant", "system"]
    content: str
    created_at: datetime
    # Inline order cards for assistant messages: the customer's own orders that this turn's tool
    # results returned (never parsed from the reply text). Resolved through owner-filtered SQL.
    orders: list[OrderSummary] = []
    # ActionCards for assistant messages: what this turn's write submissions did, as the gateway reported.
    actions: list[ActionCard] = []


class ConversationOut(BaseModel):
    id: uuid.UUID
    order_id: str | None
    messages: list[MessageOut]


class OwnedConversation(BaseModel):
    id: uuid.UUID
    order_id: str | None


async def owned_conversation(
    conn: Conn, customer_id: str, conversation_id: uuid.UUID
) -> OwnedConversation | None:
    """The conversation if this customer owns it; None if it doesn't exist or isn't theirs (invariant 8)."""
    row = await conn.fetchrow(
        "SELECT id, order_id FROM app.conversations WHERE id = $1 AND customer_id = $2",
        conversation_id,
        customer_id,
    )
    return OwnedConversation(id=row["id"], order_id=row["order_id"]) if row is not None else None


# The steps the K7 correction offers (L19): it never offers one that any turn of the conversation completed.
SUPPORT_ACTIONS: tuple[ActionKind, ...] = ("create_ticket", "escalate_to_human")


async def support_actions_done(
    conn: Conn, customer_id: str, conversation_id: uuid.UUID
) -> frozenset[ActionKind]:
    """The offered steps already EXECUTED in this customer's conversation, in any turn. Filtered by owner in
    SQL (invariant 3). Read only by the correction's offer, never by what a reply may claim (invariant 10)."""
    rows = await conn.fetch(
        "SELECT DISTINCT action FROM app.action_requests"
        " WHERE conversation_id = $1 AND customer_id = $2 AND status = 'executed'"
        " AND action = ANY($3::text[])",
        conversation_id,
        customer_id,
        list(SUPPORT_ACTIONS),
    )
    found = {r["action"] for r in rows}
    return frozenset(k for k in SUPPORT_ACTIONS if k in found)


async def owns_order(conn: Conn, customer_id: str, order_id: str) -> bool:
    found = await conn.fetchval(
        "SELECT 1 FROM app.orders WHERE id = $1 AND customer_id = $2", order_id, customer_id
    )
    return found is not None


async def create_conversation(conn: Conn, customer_id: str, order_id: str | None) -> uuid.UUID:
    cid: uuid.UUID = await conn.fetchval(
        "INSERT INTO app.conversations (customer_id, order_id) VALUES ($1, $2) RETURNING id",
        customer_id,
        order_id,
    )
    return cid


async def add_customer_message(
    conn: Conn, conversation_id: uuid.UUID, turn_id: uuid.UUID, content: str, client_message_id: uuid.UUID
) -> bool:
    """Insert the customer's message. False if this client_message_id was already used (B9)."""
    inserted = await conn.fetchval(
        """
        INSERT INTO app.messages (conversation_id, turn_id, role, content, client_message_id)
        VALUES ($1, $2, 'customer', $3, $4)
        ON CONFLICT (conversation_id, client_message_id) DO NOTHING
        RETURNING id
        """,
        conversation_id,
        turn_id,
        content,
        client_message_id,
    )
    if inserted is not None:
        await conn.execute("UPDATE app.conversations SET updated_at = now() WHERE id = $1", conversation_id)
    return inserted is not None


async def existing_turn(
    conn: Conn, conversation_id: uuid.UUID, client_message_id: uuid.UUID
) -> tuple[uuid.UUID, MessageOut | None]:
    """For a repeated client_message_id: the original turn id and its assistant reply, if finished."""
    turn_id: uuid.UUID = await conn.fetchval(
        "SELECT turn_id FROM app.messages WHERE conversation_id = $1 AND client_message_id = $2",
        conversation_id,
        client_message_id,
    )
    row = await conn.fetchrow(
        "SELECT id, role, content, created_at, actions FROM app.messages"
        " WHERE conversation_id = $1 AND turn_id = $2 AND role = 'assistant'",
        conversation_id,
        turn_id,
    )
    return turn_id, _message(row) if row is not None else None


async def history(
    conn: Conn, conversation_id: uuid.UUID, before_turn: uuid.UUID, limit: int = 20
) -> list[MessageOut]:
    rows = await conn.fetch(
        """
        SELECT id, role, content, created_at FROM (
          SELECT m.id, m.role, m.content, m.created_at FROM app.messages m
           WHERE m.conversation_id = $1 AND m.turn_id <> $2 AND m.role IN ('customer', 'assistant')
             -- Skip customer messages whose turn never got a reply (failed, rate-limited or stopped):
             -- when the customer re-sends, the model must see that request once, not twice.
             AND (m.role = 'assistant' OR EXISTS (
                   SELECT 1 FROM app.messages a
                    WHERE a.conversation_id = m.conversation_id AND a.turn_id = m.turn_id
                      AND a.role = 'assistant'))
           ORDER BY m.id DESC LIMIT $3
        ) recent ORDER BY id
        """,
        conversation_id,
        before_turn,
        limit,
    )
    return [MessageOut(**dict(r)) for r in rows]


async def add_assistant_message(
    conn: Conn,
    conversation_id: uuid.UUID,
    turn_id: uuid.UUID,
    content: str,
    order_refs: list[str],
    actions: list[ActionCard] | None = None,
) -> MessageOut:
    row = await conn.fetchrow(
        "INSERT INTO app.messages (conversation_id, turn_id, role, content, order_refs, actions)"
        " VALUES ($1, $2, 'assistant', $3, $4, $5::jsonb) RETURNING id, role, content, created_at, actions",
        conversation_id,
        turn_id,
        content,
        order_refs,
        json.dumps([a.model_dump(mode="json") for a in actions or []]),
    )
    if row is None:  # INSERT ... RETURNING always returns the row; asyncpg types it as optional
        raise RuntimeError("assistant message insert returned no row")
    return _message(row)


def _message(row: Any, orders: list[OrderSummary] | None = None) -> MessageOut:
    raw = row["actions"]
    cards = json.loads(raw) if isinstance(raw, str) else raw
    return MessageOut(
        id=row["id"],
        role=row["role"],
        content=row["content"],
        created_at=row["created_at"],
        orders=orders or [],
        actions=[ActionCard.model_validate(c) for c in cards],
    )


def _unannounced_expiries(pending: list[Any], now: datetime) -> list[MessageOut]:
    """R7 of the derived expiry predicate (J8, J14): a request still pending past expiry, its decision not yet
    recorded, shows the expiry system message the lazy write will post: the same text, timed at the expiry.
    Its own seam for mutation M44."""
    return [
        MessageOut(
            id=-int(r["id"].removeprefix("ACT-")),  # never a stored id (those are positive)
            role="system",
            content=action_cards.decided_message("expired", r["id"], r["action"]),
            created_at=r["created_at"] + expiry.APPROVAL_TTL,
        )
        for r in pending
        if expiry.is_expired(r["created_at"], now)
    ]


async def latest_conversation(conn: Conn, customer_id: str, now: datetime) -> ConversationOut | None:
    conv = await conn.fetchrow(
        "SELECT id, order_id FROM app.conversations WHERE customer_id = $1 ORDER BY updated_at DESC LIMIT 1",
        customer_id,
    )
    if conv is None:
        return None
    rows = await conn.fetch(
        """
        SELECT m.id, m.role, m.content, m.created_at, m.order_refs, m.actions
          FROM app.messages m JOIN app.conversations c ON c.id = m.conversation_id
         WHERE m.conversation_id = $1 AND c.customer_id = $2
         ORDER BY m.id
        """,
        conv["id"],
        customer_id,
    )
    referenced = {oid for r in rows for oid in r["order_refs"]}
    owned = {o.id: o for o in await list_orders(conn, customer_id)} if referenced else {}
    messages = [_message(r, [owned[oid] for oid in r["order_refs"] if oid in owned]) for r in rows]
    # Requests of this conversation still waiting in storage. Once a decision is recorded the request is no
    # longer pending, so the stored message shows and the derived one doesn't: never both.
    pending = await conn.fetch(
        "SELECT id, action, created_at FROM app.action_requests"
        " WHERE conversation_id = $1 AND customer_id = $2 AND status = 'pending_approval' ORDER BY id",
        conv["id"],
        customer_id,
    )
    derived = _unannounced_expiries(list(pending), now)
    if derived:
        messages = sorted(messages + derived, key=lambda m: m.created_at)  # stable: stored order kept on ties
    return ConversationOut(id=conv["id"], order_id=conv["order_id"], messages=messages)
