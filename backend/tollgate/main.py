"""FastAPI app: lifespan resources, routers, error mapping, and per-user response headers."""

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import httpx
from agents import OpenAIChatCompletionsModel, set_tracing_disabled
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from tollgate.agents_def.runner import LLMRuntime
from tollgate.api import chat, orders, staff
from tollgate.auth.supabase_jwt import TokenVerifier
from tollgate.config import AppSettings, AuthSettings, LLMSettings, SupabaseSettings
from tollgate.db import create_pool
from tollgate.errors import (
    ApprovalConflictError,
    AuthError,
    AuthUnavailableError,
    ConfigError,
    ForbiddenError,
    NotFoundError,
)
from tollgate.llm.provider import make_client

log = logging.getLogger("tollgate")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_tracing_disabled(True)  # SDK traces would go to OpenAI; we trace locally (Section 2.2)
    llm_settings = LLMSettings()
    if not llm_settings.model_strong:
        raise ConfigError("MODEL_STRONG is not set; run scripts/resolve_models.py")
    http = httpx.AsyncClient(timeout=10)
    app.state.pool = await create_pool(SupabaseSettings())
    app.state.verifier = TokenVerifier(AuthSettings(), http=http)
    app.state.clock = AppSettings().clock()  # decisions read time only from here
    app.state.llm = LLMRuntime(
        model=OpenAIChatCompletionsModel(
            model=llm_settings.model_strong, openai_client=make_client(llm_settings)
        ),
        model_name=llm_settings.model_strong,
        daily_budget=llm_settings.llm_daily_token_budget,
        turn_estimate=llm_settings.llm_turn_token_estimate,
        ledger=llm_settings.llm_budget_ledger,
        rejected_request_tokens=llm_settings.llm_rejected_request_tokens,
    )
    try:
        yield
    finally:
        await app.state.pool.close()
        await http.aclose()


app = FastAPI(title="Tollgate API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[AppSettings().frontend_origin],
    allow_methods=["GET", "POST"],
    allow_headers=["authorization", "content-type"],
)


@app.middleware("http")
async def no_store(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    response = await call_next(request)
    if request.url.path.startswith("/v1/"):
        # Per-user data is never cached by browsers, proxies or CDNs (CLAUDE.md security rules).
        response.headers["Cache-Control"] = "no-store"
        response.headers["Vary"] = "Authorization"
    return response


@app.exception_handler(AuthError)
async def on_auth(_: Request, __: AuthError) -> JSONResponse:
    return JSONResponse({"error": "unauthorized"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})


@app.exception_handler(AuthUnavailableError)
async def on_auth_unavailable(_: Request, exc: AuthUnavailableError) -> JSONResponse:
    log.error("auth unavailable: %s", exc)
    return JSONResponse({"error": "auth_unavailable"}, status_code=503)


@app.exception_handler(ForbiddenError)
async def on_forbidden(_: Request, __: ForbiddenError) -> JSONResponse:
    return JSONResponse({"error": "forbidden"}, status_code=403)


@app.exception_handler(NotFoundError)
async def on_not_found(_: Request, __: NotFoundError) -> JSONResponse:
    return JSONResponse({"error": "not_found"}, status_code=404)


@app.exception_handler(ApprovalConflictError)
async def on_approval_conflict(_: Request, exc: ApprovalConflictError) -> JSONResponse:
    # already_decided | amount_mismatch: nothing was changed (staff only; never a customer surface)
    return JSONResponse({"error": exc.reason}, status_code=409)


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(orders.router)
app.include_router(chat.router)
app.include_router(staff.router)
