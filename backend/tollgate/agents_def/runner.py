"""Run one chat turn through the Agents SDK and translate it into chat events (DECISIONS C1).

Live: turn_started, progress (per tool call) and order_ref (from the customer's own tool results).
Buffered: the reply text, released only after the claim check. Only checked text is stored or sent.
Every turn writes one app.run_log row (tokens, model calls, latency, prompt version, outcome),
including failed and cancelled turns. Provider errors become typed error events, never fake answers.
"""

import asyncio
import json
import logging
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import asyncpg
import openai
from agents import (
    AgentsException,
    Model,
    RawResponsesStreamEvent,
    RunConfig,
    RunItemStreamEvent,
    Runner,
    TResponseInputItem,
)
from pydantic import BaseModel

from tollgate.agents_def import events
from tollgate.agents_def.support import AGENT_NAME, PROMPT_VERSION, build_support_agent
from tollgate.auth.deps import CustomerContext
from tollgate.clock import Clock
from tollgate.domain import conversations as conv
from tollgate.errors import BudgetExceededError, ProviderError
from tollgate.guardrails.claims import check_reply
from tollgate.llm import budget
from tollgate.tools.context import TurnContext

log = logging.getLogger(__name__)

MAX_TURNS = 6  # model calls per customer turn (Section 2.3: one turn is 2-6 calls)
LABELS = {
    "get_my_orders": "Looking up your orders...",
    "get_order": "Checking your order...",
    "get_shipment": "Checking tracking...",
    "get_refund_history": "Checking refund history...",
}


@dataclass(frozen=True)
class LLMRuntime:
    model: Model
    model_name: str
    daily_budget: int
    turn_estimate: int
    # Where real spend is mirrored (survives DB resets). None for scripted models, tests and replays,
    # which spend no provider tokens. Required on purpose: a real path can't forget to set it.
    ledger: Path | None


@dataclass(frozen=True)
class ChatTurn:
    customer: CustomerContext
    conversation: conv.OwnedConversation
    client_message_id: uuid.UUID
    message: str


def _tool_name(raw: Any) -> str | None:
    name = raw.get("name") if isinstance(raw, dict) else getattr(raw, "name", None)
    return name if isinstance(name, str) else None


def _retry_after(exc: openai.APIStatusError) -> float | None:
    header = exc.response.headers.get("retry-after")
    try:
        return float(header) if header is not None else None
    except ValueError:
        return None


async def run_turn(
    pool: asyncpg.Pool, llm: LLMRuntime, turn: ChatTurn, clock: Clock
) -> AsyncIterator[BaseModel]:
    conv_id = turn.conversation.id
    turn_id = uuid.uuid4()

    async with pool.acquire() as conn:
        if not await conv.add_customer_message(conn, conv_id, turn_id, turn.message, turn.client_message_id):
            # Repeated submit (double click, retry): answer from the original turn, never run twice (B9).
            prev_turn, reply = await conv.existing_turn(conn, conv_id, turn.client_message_id)
            yield events.TurnStarted(conversation_id=conv_id, turn_id=prev_turn)
            if reply is not None:
                yield events.Reply(message_id=reply.id, text=reply.content, created_at=reply.created_at)
            else:
                yield events.error("duplicate_in_progress")
            yield events.Done()
            return
        past = await conv.history(conn, conv_id, before_turn=turn_id)
        try:
            await budget.preflight(conn, llm.model_name, llm.daily_budget, llm.turn_estimate, llm.ledger)
        except BudgetExceededError as exc:
            log.warning("chat refused by budget pre-flight: %s", exc)
            yield events.TurnStarted(conversation_id=conv_id, turn_id=turn_id)
            yield events.error("budget_exhausted")
            yield events.Done()
            return

    yield events.TurnStarted(conversation_id=conv_id, turn_id=turn_id)

    ctx = TurnContext(
        customer=turn.customer,
        pool=pool,
        conversation_id=conv_id,
        turn_id=turn_id,
        order_id=turn.conversation.order_id,
        clock=clock,
    )
    inputs: list[TResponseInputItem] = [
        {"role": "user" if m.role == "customer" else "assistant", "content": m.content} for m in past
    ]
    inputs.append({"role": "user", "content": turn.message})

    started_at, t0 = datetime.now(UTC), time.perf_counter()
    status, error_text = "error", "not finished"
    result = Runner.run_streamed(
        build_support_agent(llm.model),
        inputs,
        context=ctx,
        max_turns=MAX_TURNS,
        run_config=RunConfig(tracing_disabled=True, workflow_name="tollgate-chat"),
    )
    sent_orders: set[str] = set()
    model_calls = 0
    try:
        async for ev in result.stream_events():
            if isinstance(ev, RawResponsesStreamEvent):
                if getattr(ev.data, "type", None) == "response.completed":
                    model_calls += 1  # counted here, not from provider usage, which may be absent
                continue  # raw token deltas are never forwarded (C1)
            if not isinstance(ev, RunItemStreamEvent):
                continue
            if ev.name == "tool_called":
                yield events.Progress(
                    label=LABELS.get(_tool_name(ev.item.raw_item) or "", "Looking that up...")
                )
            elif ev.name == "tool_output":
                for oid, summary in ctx.referenced_orders.items():
                    if oid not in sent_orders:
                        sent_orders.add(oid)
                        yield events.OrderRef(order=summary)

        text = result.final_output if isinstance(result.final_output, str) else ""
        if not text.strip():
            raise ProviderError("model returned no reply text")
        checked = check_reply(text, succeeded_actions_this_turn=0)
        async with pool.acquire() as conn:
            if not checked.passed:
                await conn.execute(
                    "INSERT INTO app.audit_log"
                    " (actor_type, actor_id, event, target, outcome, prompt_version, turn_id, details)"
                    " VALUES ('system', 'claim_check', 'claim_check_replaced', $1, 'replaced',"
                    " $2, $3, $4::jsonb)",
                    str(conv_id),
                    PROMPT_VERSION,
                    turn_id,
                    json.dumps({"matched": (checked.matched or "")[:200]}),
                )
            msg = await conv.add_assistant_message(
                conn, conv_id, turn_id, checked.text, list(ctx.referenced_orders)
            )
        status, error_text = "ok", ""
        yield events.Reply(message_id=msg.id, text=msg.content, created_at=msg.created_at)
    except openai.RateLimitError as exc:
        error_text = "rate_limited"
        yield events.error("rate_limited", _retry_after(exc))
    except (openai.APIError, ProviderError) as exc:
        error_text = f"provider: {type(exc).__name__}"
        log.warning("chat provider error: %s", exc)
        yield events.error("provider_error")
    except AgentsException as exc:
        error_text = f"agents: {type(exc).__name__}"
        log.warning("chat agent error: %s", exc)
        yield events.error("server_error")
    except (asyncio.CancelledError, GeneratorExit):
        error_text = "cancelled"  # customer pressed stop or disconnected; no reply is stored
        result.cancel()
        raise
    except Exception:
        error_text = "unexpected"
        log.exception("chat turn failed")
        yield events.error("server_error")
    finally:
        usage = result.context_wrapper.usage
        if llm.ledger is not None:
            budget.record_spend(llm.ledger, llm.model_name, usage.total_tokens)
        await asyncio.shield(
            _record_run(
                pool,
                turn,
                turn_id,
                llm.model_name,
                status,
                error_text or None,
                model_calls,
                usage.input_tokens,
                usage.output_tokens,
                usage.total_tokens,
                round((time.perf_counter() - t0) * 1000),
                started_at,
            )
        )
    yield events.Done()


async def _record_run(
    pool: asyncpg.Pool,
    turn: ChatTurn,
    turn_id: uuid.UUID,
    model: str,
    status: str,
    error_text: str | None,
    calls: int,
    tokens_in: int,
    tokens_out: int,
    tokens_total: int,
    latency_ms: int,
    started_at: datetime,
) -> None:
    await pool.execute(
        """
        INSERT INTO app.run_log
          (turn_id, conversation_id, customer_id, agent, prompt_version, model, status, error,
           model_calls, input_tokens, output_tokens, total_tokens, latency_ms, started_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        """,
        turn_id,
        turn.conversation.id,
        turn.customer.customer_id,
        AGENT_NAME,
        PROMPT_VERSION,
        model,
        status,
        error_text,
        calls,
        tokens_in,
        tokens_out,
        tokens_total,
        latency_ms,
        started_at,
    )
