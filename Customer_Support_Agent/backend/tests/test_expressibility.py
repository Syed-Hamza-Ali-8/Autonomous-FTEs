"""The zero-token expressibility pre-flight finds the bug class that cost real runs (p05, a04), and finds none
in the current tools (owner, 2026-11-09)."""

from typing import Any

from agents import RunContextWrapper, function_tool
from pydantic import BaseModel

from eval.expressibility import check
from eval.verify_scenarios import load
from tollgate.actions import gateway
from tollgate.agents_def.support import agent_tools


def current() -> tuple[dict[str, Any], dict[str, type[BaseModel]]]:
    return {t.name: t for t in agent_tools()}, dict(gateway.ARGS)


def test_every_expected_request_is_expressible_with_the_current_tools() -> None:
    tools, models = current()
    assert check(load(), tools, models, gateway._invalid) == []


def test_p05_class_an_optional_field_advertised_as_required_is_found() -> None:
    """Strict mode advertises amount_cents as required; the provider rejects a call that omits it."""

    @function_tool(name_override="request_refund")  # strict_mode=True: the p05 bug
    async def strict_refund(
        ctx: RunContextWrapper[Any],
        order_id: str,
        reason: str,
        items: list[str] | None = None,
        amount_cents: int | None = None,
    ) -> str:
        """Refund."""
        return order_id

    tools, models = current()
    problems = check(load(), {**tools, "request_refund": strict_refund}, models, gateway._invalid)
    assert any("advertises optional field(s)" in p and "amount_cents" in p for p in problems)
    assert any(p.startswith("p05: request_refund: provider rejects it (optionals omitted)") for p in problems)


def test_a04_class_a_required_field_the_customer_never_gave_is_found() -> None:
    """The old address schema required a recipient name and country the customer didn't give."""

    class FullAddress(BaseModel):
        name: str
        line1: str
        city: str
        postal_code: str
        country: str

    @function_tool(name_override="update_shipping_address", strict_mode=False)
    async def full_address(ctx: RunContextWrapper[Any], order_id: str, new_address: FullAddress) -> str:
        """Readdress."""
        return order_id

    class FullAddressArgs(gateway.AddressArgs):
        new_address: FullAddress  # type: ignore[assignment]

    tools, models = current()
    problems = check(
        load(),
        {**tools, "update_shipping_address": full_address},
        {**models, "update_shipping_address": FullAddressArgs},
        gateway._invalid,
    )
    assert any(p.startswith("a04: update_shipping_address: provider rejects it") for p in problems)
    assert any(p.startswith("a04:") and "gateway schema rejects it" in p for p in problems)
