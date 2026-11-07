"""Storefront reads: profile and orders. Customer identity comes only from the token (invariant 2)."""

from fastapi import APIRouter

from tollgate.auth.deps import Customer, Pool
from tollgate.domain import orders
from tollgate.domain.models import CustomerProfile, OrderDetail, OrderStatus, OrderSummary
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
async def get_order(order_id: str, customer: Customer, pool: Pool) -> OrderDetail:
    async with pool.acquire() as conn:
        detail = await orders.get_order(conn, customer.customer_id, order_id.strip().upper())
    if detail is None:
        raise NotFoundError("order")  # same response for missing and not-yours (invariant 8)
    return detail
