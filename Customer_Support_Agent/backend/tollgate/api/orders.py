"""Storefront reads: profile and orders. Customer identity comes only from the token (invariant 2)."""

from fastapi import APIRouter, Request

from tollgate.auth.deps import Customer, Pool
from tollgate.domain import actions, orders
from tollgate.domain.models import ActionRecord, CustomerProfile, OrderDetail, OrderStatus, OrderSummary
from tollgate.errors import NotFoundError

router = APIRouter(prefix="/v1", tags=["store"])


@router.get("/me")
async def me(customer: Customer) -> CustomerProfile:
    return CustomerProfile(id=customer.customer_id, name=customer.name, email=customer.email)


@router.get("/orders")
async def list_orders(
    customer: Customer, pool: Pool, status: OrderStatus | None = None
) -> list[OrderSummary]:
    async with pool.acquire() as conn:
        return await orders.list_orders(conn, customer.customer_id, status)


@router.get("/orders/{order_id}")
async def get_order(order_id: str, customer: Customer, pool: Pool, request: Request) -> OrderDetail:
    async with pool.acquire() as conn:
        detail = await orders.get_order(
            conn, customer.customer_id, order_id.strip().upper(), request.app.state.clock.now()
        )
    if detail is None:
        raise NotFoundError("order")  # same response for missing and not-yours (invariant 8)
    return detail


@router.get("/actions/{reference}")
async def get_action(reference: str, customer: Customer, pool: Pool, request: Request) -> ActionRecord:
    """One of the customer's own action requests, for its ActionCard (C2)."""
    async with pool.acquire() as conn:
        record = await actions.get_action(
            conn, customer.customer_id, reference.strip().upper(), request.app.state.clock.now()
        )
    if record is None:
        raise NotFoundError("action")  # same response for missing and not-yours (invariant 8)
    return record
