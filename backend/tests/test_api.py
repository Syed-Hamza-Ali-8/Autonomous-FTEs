"""HTTP API with two real signed-in customers and a scripted model (zero tokens).

Covers: token rejection at the HTTP layer, 403 for a user with no customer row, two-customer isolation
on every read route, indistinguishable 404s, no-store headers, and the chat flow (C1 buffering,
claim check, B9 de-duplication, ownership of conversations and order context, typed errors).
"""

import json
import secrets
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import asyncpg
import httpx
import jwt
import openai
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from tests.auth_users import test_email
from tests.fakes import CallTool, Fail, Say, ScriptedModel
from tests.txpool import TxPool, rolled_back
from tollgate.agents_def.runner import LLMRuntime
from tollgate.config import SupabaseSettings
from tollgate.guardrails.claims import CORRECTION
from tollgate.main import app


@dataclass(frozen=True)
class SignedIn:
    customer_id: str
    token: str
    order_ids: list[str]

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


async def _make_user(c: httpx.AsyncClient, svc: str, anon: str) -> tuple[str, str]:
    admin = {"apikey": svc, "Authorization": f"Bearer {svc}"}
    email, pw = test_email("api"), secrets.token_urlsafe(24)
    r = await c.post(
        "/admin/users", headers=admin, json={"email": email, "password": pw, "email_confirm": True}
    )
    r.raise_for_status()
    uid = r.json()["id"]
    t = await c.post(
        "/token",
        params={"grant_type": "password"},
        headers={"apikey": anon},
        json={"email": email, "password": pw},
    )
    t.raise_for_status()
    return uid, t.json()["access_token"]


@pytest.fixture(scope="module")
async def auth_users(settings: SupabaseSettings) -> AsyncIterator[list[tuple[str, str]]]:
    """Three throwaway Auth users (uid, access token). Created first and deleted LAST, after the
    rollback below: deleting a user touches app.customers rows our open transaction has locked."""
    assert settings.supabase_service_role_key is not None
    svc = settings.supabase_service_role_key.get_secret_value()
    anon = settings.supabase_anon_key.get_secret_value()
    admin = {"apikey": svc, "Authorization": f"Bearer {svc}"}
    async with httpx.AsyncClient(base_url=f"{settings.supabase_url}/auth/v1", timeout=10) as c:
        users: list[tuple[str, str]] = []
        try:
            for _ in range(3):
                users.append(await _make_user(c, svc, anon))
            yield users
        finally:
            for uid, _ in users:
                await c.delete(f"/admin/users/{uid}", headers=admin)


@pytest.fixture(scope="module")
async def txpool(settings: SupabaseSettings, auth_users: list[tuple[str, str]]) -> AsyncIterator[TxPool]:
    """Every write in this module (API, runner, tools, fixtures) happens in one rolled-back transaction."""
    async with rolled_back(settings.database_url.get_secret_value()) as pool:
        yield pool


@pytest.fixture(scope="module")
def db(txpool: TxPool) -> asyncpg.Connection:
    """Overrides the session `db`: reads here must see this module's uncommitted writes."""
    return txpool.connection


@pytest.fixture(autouse=True)
async def _rollback_each_test(txpool: TxPool) -> AsyncIterator[None]:
    async with txpool.savepoint():
        yield


@pytest.fixture(scope="module")
async def people(db: asyncpg.Connection, auth_users: list[tuple[str, str]]) -> tuple[SignedIn, SignedIn, str]:
    """Two seed-only customers linked to Auth users inside the transaction, plus a customer-less token."""
    picks = await db.fetch(
        """SELECT c.id FROM app.customers c WHERE c.auth_user_id IS NULL
            AND (SELECT count(*) FROM app.orders o WHERE o.customer_id = c.id) >= 3 ORDER BY c.id LIMIT 2"""
    )
    assert len(picks) == 2
    out = []
    for row, (uid, token) in zip(picks, auth_users[:2], strict=True):
        await db.execute(
            "UPDATE app.customers SET auth_user_id = $1 WHERE id = $2", uuid.UUID(uid), row["id"]
        )
        ids = [r["id"] for r in await db.fetch("SELECT id FROM app.orders WHERE customer_id = $1", row["id"])]
        out.append(SignedIn(row["id"], token, ids))
    return out[0], out[1], auth_users[2][1]


@pytest.fixture(scope="module")
async def client(txpool: TxPool) -> AsyncIterator[httpx.AsyncClient]:
    async with app.router.lifespan_context(app):
        real_pool = app.state.pool
        app.state.pool = txpool  # route every API write into the rolled-back transaction
        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://api.test") as c:
                yield c
        finally:
            app.state.pool = real_pool


def script(steps: list[Any], daily_budget: int = 10_000_000) -> ScriptedModel:
    model = ScriptedModel(steps=steps)
    app.state.llm = LLMRuntime(
        model=model, model_name="scripted", daily_budget=daily_budget, turn_estimate=1, ledger=None
    )
    return model


async def chat(
    client: httpx.AsyncClient, who: SignedIn, body: dict[str, Any]
) -> tuple[int, list[dict[str, Any]]]:
    payload = {"client_message_id": str(uuid.uuid4()), **body}
    resp = await client.post("/v1/chat", headers=who.headers, json=payload)
    if resp.status_code != 200:
        return resp.status_code, [resp.json()]
    events = [json.loads(line[6:]) for line in resp.text.splitlines() if line.startswith("data: ")]
    return 200, events


# --- authentication at the HTTP layer ----------


def _forged_tokens(settings: SupabaseSettings) -> dict[str, str]:
    now = int(time.time())
    claims = {"sub": str(uuid.uuid4()), "aud": "authenticated", "iss": f"{settings.supabase_url}/auth/v1"}
    key = ec.generate_private_key(ec.SECP256R1())
    return {
        "anon_key": settings.supabase_anon_key.get_secret_value(),
        "expired": jwt.encode(
            {**claims, "iat": now - 7200, "exp": now - 3600}, key, algorithm="ES256", headers={"kid": "x"}
        ),
        "alg_none": jwt.encode({**claims, "iat": now, "exp": now + 600}, None, algorithm="none"),
        "hs256_anon_secret": jwt.encode(
            {**claims, "iat": now, "exp": now + 600},
            settings.supabase_anon_key.get_secret_value(),
            algorithm="HS256",
        ),
        "garbage": "not-a-token",
    }


@pytest.mark.parametrize("path", ["/v1/me", "/v1/orders", "/v1/orders/ORD-1042", "/v1/conversations/latest"])
async def test_bad_tokens_get_identical_401(
    client: httpx.AsyncClient, settings: SupabaseSettings, path: str
) -> None:
    responses = [await client.get(path)]
    for token in _forged_tokens(settings).values():
        responses.append(await client.get(path, headers={"Authorization": f"Bearer {token}"}))
    assert {r.status_code for r in responses} == {401}
    assert {r.text for r in responses} == {'{"error":"unauthorized"}'}


async def test_chat_rejects_bad_tokens(client: httpx.AsyncClient, settings: SupabaseSettings) -> None:
    model = script([Say("should never run")])
    for token in _forged_tokens(settings).values():
        r = await client.post(
            "/v1/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"client_message_id": str(uuid.uuid4()), "message": "hi"},
        )
        assert r.status_code == 401
    assert model.calls == 0


async def test_valid_user_without_customer_row_is_forbidden(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str]
) -> None:
    _, _, stray = people
    r = await client.get("/v1/orders", headers={"Authorization": f"Bearer {stray}"})
    assert r.status_code == 403


# --- two-customer isolation (owner gate item) ----------


async def test_each_customer_sees_only_their_orders(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str]
) -> None:
    a, b, _ = people
    for me, other in ((a, b), (b, a)):
        listed = (await client.get("/v1/orders", headers=me.headers)).json()
        assert sorted(o["id"] for o in listed) == sorted(me.order_ids)
        assert (await client.get("/v1/me", headers=me.headers)).json()["id"] == me.customer_id
        for oid in other.order_ids:
            r = await client.get(f"/v1/orders/{oid}", headers=me.headers)
            assert r.status_code == 404, oid


async def test_foreign_order_404_is_identical_to_missing(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str]
) -> None:
    a, b, _ = people
    foreign = await client.get(f"/v1/orders/{b.order_ids[0]}", headers=a.headers)
    missing = await client.get("/v1/orders/ORD-9999", headers=a.headers)
    lowered = await client.get(f"/v1/orders/{b.order_ids[0].lower()}", headers=a.headers)
    strip = {"date", "content-length"}
    for r in (foreign, lowered):
        assert (r.status_code, r.text) == (missing.status_code, missing.text)
        assert {k: v for k, v in r.headers.items() if k not in strip} == {
            k: v for k, v in missing.headers.items() if k not in strip
        }


async def test_per_user_responses_are_not_cacheable(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str]
) -> None:
    a, _, _ = people
    for path in ("/v1/me", "/v1/orders", f"/v1/orders/{a.order_ids[0]}", "/v1/conversations/latest"):
        r = await client.get(path, headers=a.headers)
        assert r.headers["cache-control"] == "no-store", path
        assert "authorization" in r.headers["vary"].lower(), path


# --- chat ----------


async def test_chat_answers_own_order_with_buffered_reply(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str], db: asyncpg.Connection
) -> None:
    a, _, _ = people
    oid = a.order_ids[0]
    model = script([CallTool("get_order", {"order_id": oid}), Say(f"Your order {oid} is on its way.")])
    status, events = await chat(client, a, {"message": f"Where is {oid}?"})
    assert status == 200
    types = [e["type"] for e in events]
    assert types[0] == "turn_started" and types[-1] == "done"
    assert types.count("reply") == 1 and "progress" in types
    assert [e["order"]["id"] for e in events if e["type"] == "order_ref"] == [oid]
    reply = next(e for e in events if e["type"] == "reply")
    assert reply["text"] == f"Your order {oid} is on its way."
    assert model.calls == 2
    turn_id = uuid.UUID(events[0]["turn_id"])
    stored = await db.fetch("SELECT role, content FROM app.messages WHERE turn_id = $1 ORDER BY id", turn_id)
    assert [(r["role"], r["content"]) for r in stored] == [
        ("customer", f"Where is {oid}?"),
        ("assistant", reply["text"]),
    ]
    run = await db.fetchrow(
        "SELECT status, model_calls, prompt_version FROM app.run_log WHERE turn_id = $1", turn_id
    )
    assert run is not None and (run["status"], run["model_calls"], run["prompt_version"]) == (
        "ok",
        2,
        "support-v1",
    )


async def test_chat_model_asking_for_foreign_order_gets_not_found(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str], db: asyncpg.Connection
) -> None:
    a, b, _ = people
    model = script([CallTool("get_order", {"order_id": b.order_ids[0]}), Say("I couldn't find that order.")])
    status, events = await chat(client, a, {"message": f"Show me {b.order_ids[0]}"})
    assert status == 200 and model.calls == 2
    assert not [e for e in events if e["type"] == "order_ref"]
    stream = json.dumps(events)
    assert not any(oid in stream for oid in b.order_ids[1:])
    turn_id = uuid.UUID(events[0]["turn_id"])
    outcome = await db.fetchval("SELECT outcome FROM app.tool_calls WHERE turn_id = $1", turn_id)
    assert outcome == "not_found"
    # what the model saw for the foreign order is the generic not-found result
    assert "No order with that ID was found" in json.dumps(model.inputs[-1], default=str)


async def test_false_action_claim_never_reaches_screen_or_db(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str], db: asyncpg.Connection
) -> None:
    a, _, _ = people
    script([Say("Done! I've refunded your order in full.")])
    _, events = await chat(client, a, {"message": "refund me"})
    stream = json.dumps(events)
    assert "refunded your order" not in stream
    assert next(e for e in events if e["type"] == "reply")["text"] == CORRECTION
    turn_id = uuid.UUID(events[0]["turn_id"])
    stored = await db.fetchval(
        "SELECT content FROM app.messages WHERE turn_id = $1 AND role = 'assistant'", turn_id
    )
    assert stored == CORRECTION
    assert (
        await db.fetchval(
            "SELECT count(*) FROM app.audit_log WHERE turn_id = $1 AND event = 'claim_check_replaced'",
            turn_id,
        )
        == 1
    )


async def test_repeated_client_message_id_runs_once(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str]
) -> None:
    a, _, _ = people
    model = script([Say("Hello! How can I help?")])
    _, first = await chat(client, a, {"message": "hi"})
    conv_id = first[0]["conversation_id"]
    body = {"client_message_id": str(uuid.uuid4()), "message": "hello again", "conversation_id": conv_id}
    model.steps.append(Say("Hi again."))
    r1 = await client.post("/v1/chat", headers=a.headers, json=body)
    r2 = await client.post("/v1/chat", headers=a.headers, json=body)
    replies = [[json.loads(x[6:]) for x in r.text.splitlines() if x.startswith("data: ")] for r in (r1, r2)]
    texts = [next(e["text"] for e in evs if e["type"] == "reply") for evs in replies]
    assert texts == ["Hi again.", "Hi again."]
    assert model.calls == 2  # one for "hi", one for the deduplicated pair


async def test_cannot_post_into_another_customers_conversation(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str]
) -> None:
    a, b, _ = people
    script([Say("hi")])
    _, events = await chat(client, b, {"message": "hello"})
    b_conv = events[0]["conversation_id"]
    model = script([Say("should never run")])
    status, body = await chat(client, a, {"message": "hijack", "conversation_id": b_conv})
    missing_status, missing_body = await chat(
        client, a, {"message": "x", "conversation_id": str(uuid.uuid4())}
    )
    assert (status, body) == (missing_status, missing_body) == (404, [{"error": "not_found"}])
    assert model.calls == 0


async def test_chat_order_context_must_be_own_order(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str]
) -> None:
    a, b, _ = people
    model = script([Say("should never run")])
    status, body = await chat(client, a, {"message": "help", "order_id": b.order_ids[0]})
    assert (status, body) == (404, [{"error": "not_found"}])
    assert model.calls == 0


async def test_latest_conversation_is_per_customer(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str]
) -> None:
    a, b, _ = people
    script([Say("A's private reply 7d1c")])
    await chat(client, a, {"message": "A's private question 7d1c"})
    seen_by_b = (await client.get("/v1/conversations/latest", headers=b.headers)).text
    assert "7d1c" not in seen_by_b
    assert "7d1c" in (await client.get("/v1/conversations/latest", headers=a.headers)).text


async def test_rate_limit_becomes_typed_error_and_no_reply(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str], db: asyncpg.Connection
) -> None:
    a, _, _ = people
    req = httpx.Request("POST", "https://provider.example/v1/chat/completions")
    resp = httpx.Response(429, request=req, headers={"retry-after": "7"})
    script([Fail(openai.RateLimitError("rate limited", response=resp, body=None))])
    _, events = await chat(client, a, {"message": "status?"})
    err = next(e for e in events if e["type"] == "error")
    assert (err["code"], err["retry_after_s"]) == ("rate_limited", 7.0)
    assert not [e for e in events if e["type"] == "reply"]
    turn_id = uuid.UUID(events[0]["turn_id"])
    assert await db.fetchval("SELECT status FROM app.run_log WHERE turn_id = $1", turn_id) == "error"
    assert (
        await db.fetchval(
            "SELECT count(*) FROM app.messages WHERE turn_id = $1 AND role = 'assistant'", turn_id
        )
        == 0
    )


async def test_budget_preflight_refuses_without_calling_model(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str]
) -> None:
    a, _, _ = people
    model = script([Say("should never run")], daily_budget=0)
    _, events = await chat(client, a, {"message": "status?"})
    assert [e["code"] for e in events if e["type"] == "error"] == ["budget_exhausted"]
    assert model.calls == 0


def test_openapi_documents_chat_events() -> None:
    schema = app.openapi()
    sse = schema["paths"]["/v1/chat"]["post"]["responses"]["200"]["content"]["text/event-stream"]
    assert "contentSchema" in sse["itemSchema"]["properties"]["data"]
    names = set(schema["components"]["schemas"])
    assert {"TurnStarted", "Progress", "OrderRef", "Reply", "ChatError", "Done"} <= names


async def test_order_cards_survive_reload_and_come_from_tool_data(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str]
) -> None:
    a, b, _ = people
    own = a.order_ids[0]
    # The reply text names a foreign order; only the tool-returned (own) order may become a card.
    script([CallTool("get_order", {"order_id": own}), Say(f"{own} is fine. Also see {b.order_ids[0]}.")])
    await chat(client, a, {"message": f"status of {own}?"})
    latest = (await client.get("/v1/conversations/latest", headers=a.headers)).json()
    reply = [m for m in latest["messages"] if m["role"] == "assistant"][-1]
    assert [o["id"] for o in reply["orders"]] == [own]
    assert all(m["orders"] == [] for m in latest["messages"] if m["role"] != "assistant")


async def test_failed_turn_is_not_repeated_in_the_models_history(
    client: httpx.AsyncClient, people: tuple[SignedIn, SignedIn, str]
) -> None:
    # A rate-limited turn stores the customer's message but no reply. When the customer re-sends,
    # the model must see that request once, not twice.
    a, _, _ = people
    req = httpx.Request("POST", "https://provider.example/v1/chat/completions")
    resp = httpx.Response(429, request=req, headers={"retry-after": "1"})
    model = script([Fail(openai.RateLimitError("limited", response=resp, body=None)), Say("Here you go.")])
    _, first = await chat(client, a, {"message": "status of my orders?"})
    conv = first[0]["conversation_id"]
    await chat(client, a, {"message": "status of my orders?", "conversation_id": conv})
    sent = model.inputs[-1]
    customer_msgs = [m for m in sent if isinstance(m, dict) and m.get("role") == "user"]
    assert [m["content"] for m in customer_msgs] == ["status of my orders?"]
