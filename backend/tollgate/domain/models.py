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


ActionKind = Literal[
    "request_refund",
    "issue_store_credit",
    "cancel_order",
    "update_shipping_address",
    "create_ticket",
    "escalate_to_human",
]
ActionState = Literal["completed", "waiting_for_approval", "not_allowed"]


class ActionCard(BaseModel):
    """What one Action Gateway submission did, for the chat's ActionCard (spec 13.3).

    Built by the gateway from its own result, never from the model's text. `explanation` is customer-safe:
    no rule names, thresholds or internal IDs beyond the request reference.
    """

    action: ActionKind
    state: ActionState
    order_id: str | None = None  # None when the order was not found: nothing is echoed back
    amount: Money | None = None  # recomputed by the gateway
    reference: str | None = None  # the action request, for completed and waiting cards
    explanation: str
    at: datetime  # when the gateway decided, from the injected clock


class ActionRecord(BaseModel):
    """One of the customer's action requests, read live for its ActionCard (DECISIONS C2): the current state
    (a pending card updates in place when staff decide) and detail too long for the card's live event, such as
    the full resulting delivery address. Never sent to the model."""

    reference: str
    action: ActionKind
    state: ActionState
    order_id: str | None
    amount: Money | None = None
    delivery_address: Address | None = None  # address changes: the address now on the order
    kept_fields: list[str] = []  # address fields the merge kept from the previous address (I12)
    at: datetime
    decided_at: datetime | None = None
