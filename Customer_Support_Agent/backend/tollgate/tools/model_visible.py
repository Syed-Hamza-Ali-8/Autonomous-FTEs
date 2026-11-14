"""Exactly what each tool's result shows the model (DECISIONS J11; Phase 4 pre-registration 11.2).

Every path a tool result can contain, per tool: `a.b` is a key inside an object, `a[]` an element of a list.
Tests pin this in both directions (tests/test_model_visible.py; test_model_input_is_tier_safe): a field added
to a result without updating this list fails, and so does a listed field that no longer appears.

Not here, and so never model-visible: order notes, product reviews, customer email and ids, reason codes, rule
names and limits (I15), audit rows and approval decisions.

FREE_TEXT marks the paths whose content comes from stored text, not a fixed vocabulary or a number. That is
where text written by someone else reaches the model, so Phase 6 indirect-injection probes target them (J11);
everything in them is data, never instructions (invariant 11).
"""


def _money(prefix: str) -> set[str]:
    return {prefix, f"{prefix}.amount_cents", f"{prefix}.currency", f"{prefix}.display"}


def _when(prefix: str) -> set[str]:
    return {prefix, f"{prefix}_display"}


def _refunds(prefix: str) -> set[str]:
    p = f"{prefix}[]"
    return (
        {prefix, p, f"{p}.id", f"{p}.status", f"{p}.reason"}
        | _money(f"{p}.amount")
        | _when(f"{p}.created_at")
    )


def _shipment(prefix: str) -> set[str]:
    e = f"{prefix}.events[]"
    return (
        {prefix, f"{prefix}.carrier", f"{prefix}.tracking_number", f"{prefix}.status", f"{prefix}.events", e}
        | _when(f"{prefix}.shipped_at")
        | _when(f"{prefix}.delivered_at")
        | _when(f"{e}.at")
        | {f"{e}.description"}
    )


NOT_FOUND = {"found", "message"}  # read tools' single not-found result (invariant 8)

_ITEM = "order.items[]"
_ADDRESS = "order.shipping_address"

READ: dict[str, frozenset[str]] = {
    "get_my_orders": frozenset(
        {
            "found",
            "orders",
            "orders[]",
            "orders[].id",
            "orders[].status",
            "orders[].item_count",
            "orders[].first_item_name",
        }
        | _money("orders[].total")
        | _when("orders[].placed_at")
        | _when("orders[].delivered_at")
    ),
    "get_order": frozenset(
        NOT_FOUND
        | {
            "order",
            "order.id",
            "order.status",
            "order.items",
            _ITEM,
            f"{_ITEM}.product_id",
            f"{_ITEM}.name",
            f"{_ITEM}.category",
            f"{_ITEM}.quantity",
            f"{_ITEM}.final_sale",
            f"{_ITEM}.digital",
        }
        | _money(f"{_ITEM}.unit_price")
        | _money(f"{_ITEM}.line_total")
        | {_ADDRESS}
        | {f"{_ADDRESS}.{f}" for f in ("name", "line1", "city", "postal_code", "country")}
        | _money("order.total")
        | _money("order.captured")
        | _money("order.refunded")
        | _when("order.placed_at")
        | _when("order.paid_at")
        | _when("order.packed_at")
        | _when("order.delivered_at")
        | _refunds("order.refunds")
        | _shipment("order.shipment")
    ),
    "get_shipment": frozenset(NOT_FOUND | {"order_id", "order_status"} | _shipment("shipment")),
    "get_refund_history": frozenset(
        NOT_FOUND | {"order_id"} | _money("captured") | _money("refunded") | _refunds("refunds")
    ),
}

# Write tools return the Action Gateway's outcome: a status, the request's own facts, and ONE tier-safe
# sentence (customer_message_hint, I15). Never a reason code, rule name, limit, cap or count.
_OUTCOME = {"status", "customer_message_hint"}
_MONEY_RESULT = {"action", "order_id", "reference", "amount_cents", "currency", "display"}
WRITE: dict[str, frozenset[str]] = {
    "request_refund": frozenset(_OUTCOME | _MONEY_RESULT | {"refund_id"}),
    "issue_store_credit": frozenset(_OUTCOME | _MONEY_RESULT | {"store_credit_id"}),
    "cancel_order": frozenset(_OUTCOME | {"action", "order_id", "reference", "refund_id"} | _money("refund")),
    "update_shipping_address": frozenset(_OUTCOME | {"action", "order_id", "reference"}),
    "create_ticket": frozenset(_OUTCOME | {"action", "reference", "ticket_id"}),
    "escalate_to_human": frozenset(_OUTCOME | {"action", "reference", "ticket_id"}),
}

FREE_TEXT: frozenset[str] = frozenset(
    {"orders[].first_item_name", f"{_ITEM}.name", f"{_ITEM}.category"}
    | {"order.refunds[].reason", "refunds[].reason"}
    | {f"{_ADDRESS}.{f}" for f in ("name", "line1", "city", "postal_code", "country")}
    | {f"{s}.{f}" for s in ("order.shipment", "shipment") for f in ("carrier", "tracking_number")}
    | {"order.shipment.events[].description", "shipment.events[].description"}
)


def paths(value: object, prefix: str = "") -> set[str]:
    """Every path in a tool result, in the notation above."""
    out: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out |= {path} | paths(child, path)
    elif isinstance(value, list):
        for child in value:
            out |= {f"{prefix}[]"} | paths(child, f"{prefix}[]")
    return out
