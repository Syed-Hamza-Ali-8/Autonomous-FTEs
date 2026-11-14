"""Request identity for FastAPI routes.

The bearer token proves only *who* the Auth user is. Whether that user is a customer, and which one,
is read from app.customers on every request (invariant 22). The token's `role`, `email` or metadata
claims are never used.
"""

import uuid
from dataclasses import dataclass
from typing import Annotated

import asyncpg
from fastapi import Depends, Request

from tollgate.auth.supabase_jwt import TokenVerifier, VerifiedToken
from tollgate.errors import AuthError, ForbiddenError


@dataclass(frozen=True)
class CustomerContext:
    customer_id: str
    auth_user_id: uuid.UUID
    name: str
    email: str


def get_pool(request: Request) -> asyncpg.Pool:
    pool: asyncpg.Pool = request.app.state.pool
    return pool


def get_verifier(request: Request) -> TokenVerifier:
    verifier: TokenVerifier = request.app.state.verifier
    return verifier


async def verified_token(
    request: Request, verifier: Annotated[TokenVerifier, Depends(get_verifier)]
) -> VerifiedToken:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthError("missing bearer token")
    return await verifier.verify(token.strip())


async def customer_context(
    token: Annotated[VerifiedToken, Depends(verified_token)],
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> CustomerContext:
    row = await pool.fetchrow(
        "SELECT id, name, email FROM app.customers WHERE auth_user_id = $1", token.auth_user_id
    )
    if row is None:
        raise ForbiddenError("authenticated user has no customer account")
    return CustomerContext(
        customer_id=row["id"], auth_user_id=token.auth_user_id, name=row["name"], email=row["email"]
    )


@dataclass(frozen=True)
class StaffContext:
    """A support lead (Phase 4; DECISIONS E3). Loaded from app.staff_users on every request, never from token
    claims (invariant 22). Staff have no customer row, so every customer endpoint refuses them (403)."""

    staff_id: uuid.UUID
    auth_user_id: uuid.UUID
    name: str
    email: str
    role: str


async def staff_context(
    token: Annotated[VerifiedToken, Depends(verified_token)],
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> StaffContext:
    row = await pool.fetchrow(
        "SELECT id, name, email, role FROM app.staff_users WHERE auth_user_id = $1 AND role = 'support_lead'",
        token.auth_user_id,
    )
    if row is None:
        raise ForbiddenError("authenticated user is not staff")  # same 403 body as every other refusal
    return StaffContext(
        staff_id=row["id"],
        auth_user_id=token.auth_user_id,
        name=row["name"],
        email=row["email"],
        role=row["role"],
    )


Customer = Annotated[CustomerContext, Depends(customer_context)]
Staff = Annotated[StaffContext, Depends(staff_context)]
Pool = Annotated[asyncpg.Pool, Depends(get_pool)]
