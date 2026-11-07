"""Read models returned by domain/ and serialised by the API (OpenAPI -> frontend types)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

OrderStatus = Literal[
    "pending", "paid", "packed", "shipped", "delivered", "cancelled", "refunded", "partially_refunded"
]
Currency = Literal["USD", "PKR"]


class Money(BaseModel):
    amount_cents: int  # integer minor units of `currency` (PKR = paisa)
    currency: Currency


class OrderSummary(BaseModel):
    id: str
    status: OrderStatus
    total: Money
    placed_at: datetime
    delivered_at: datetime | None
    item_count: int
    first_item_name: str


class OrderItem(BaseModel):
    product_id: str
    name: str
    category: str
    quantity: int
    unit_price: Money
    line_total: Money
    final_sale: bool
    digital: bool


class Refund(BaseModel):
    id: str
    amount: Money
    status: Literal["pending_approval", "succeeded", "rejected"]
    reason: str | None
    created_at: datetime


class ShipmentEvent(BaseModel):
    at: datetime
    description: str


class Shipment(BaseModel):
    carrier: str
    tracking_number: str
    status: Literal["label_created", "in_transit", "out_for_delivery", "delivered"]
    shipped_at: datetime | None
    delivered_at: datetime | None
    events: list[ShipmentEvent]


class Address(BaseModel):
    name: str
    line1: str
    city: str
    postal_code: str
    country: str


class OrderDetail(BaseModel):
    id: str
    status: OrderStatus
    total: Money
    placed_at: datetime
    paid_at: datetime | None
    packed_at: datetime | None
    delivered_at: datetime | None
    shipping_address: Address
    items: list[OrderItem]
    captured: Money
    refunded: Money
    refunds: list[Refund]
    shipment: Shipment | None


class CustomerProfile(BaseModel):
    id: str
    name: str
    email: str
