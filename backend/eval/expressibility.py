"""Zero-token pre-flight: can each scenario's expected action be expressed through the current tools?

Both p05 (an optional field advertised as required) and a04 (a required field the customer never gave) were
this class of bug, and each cost a real-model run to find. For every expected request of every Phase 3
scenario, this check builds the arguments a model could form from what the scenario makes available, and
validates them against both enforcers:
- the PROVIDER, which checks the advertised `params_json_schema` (JSON Schema validation, as Groq does);
- the GATEWAY, with its strict parse and validation bounds (no database needed).

What a model can know:
- the customer's turns;
- the read tools' answers: exact item names from get_order, and the customer's own order IDs from
  get_my_orders;
- free text it writes itself (reason, summary, category).

Nothing else. Optional fields are tried both omitted and as explicit nulls. Recipient name and country are
never available unless the customer's turns say them.

Usage (from backend/):  uv run python -m eval.expressibility
"""

import json
import re
import sys
from collections.abc import Mapping
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ValidationError

from eval.verify_scenarios import load

# Which tools can express each pre-registered action (either one is enough when several are listed).
TOOLS_FOR = {
    "refund": ["request_refund"],
    "issue_store_credit": ["issue_store_credit"],
    "cancel_order": ["cancel_order"],
    "update_shipping_address": ["update_shipping_address"],
    "escalate_to_human": ["escalate_to_human"],
    "create_ticket_or_escalate": ["create_ticket", "escalate_to_human"],
}
POSTCODE = re.compile(r"\b\d{5}\b")
STREET = re.compile(r"\b\d+\s+\w+(?:\s+\w+)?\s+(?:Road|Street|St|Avenue|Ave|Lane|Way|Drive)\b", re.IGNORECASE)


def _address_from(text: str) -> dict[str, str]:
    """Only the address parts the customer actually wrote. Name and country are never guessed."""
    out: dict[str, str] = {}
    if m := STREET.search(text):
        out["line1"] = m.group(0)
        tail = text[m.end() :]
        if c := re.match(r",\s*([A-Z][a-z]+)", tail):
            out["city"] = c.group(1)
    if m := POSTCODE.search(text):
        out["postal_code"] = m.group(0)
    return out


def candidate_args(tool: str, request: dict[str, Any], text: str) -> dict[str, Any]:
    """The arguments a model could form, with optional fields left out."""
    reason = "as the customer described"
    if tool in ("request_refund", "issue_store_credit"):
        args: dict[str, Any] = {"order_id": request["order"], "reason": reason}
        if request.get("items"):
            args["items"] = request["items"]  # exact names, from get_order
        return args
    if tool == "cancel_order":
        return {"order_id": request["order"], "reason": reason}
    if tool == "update_shipping_address":
        return {"order_id": request["order"], "new_address": _address_from(text)}
    if tool == "create_ticket":
        return {"summary": text[:500], "category": "other"}
    return {"summary": text[:500]}


def _with_nulls(args: dict[str, Any], schema: Mapping[str, Any]) -> dict[str, Any]:
    props = schema.get("properties", {})
    return {k: args.get(k) for k in props}


def _gateway_problem(model: type[BaseModel], args: dict[str, Any], invalid: Any) -> str | None:
    try:
        parsed = model.model_validate_json(json.dumps(args))
    except ValidationError as exc:
        return "gateway schema rejects it: " + "; ".join(
            f"{'.'.join(map(str, e['loc']))}: {e['type']}" for e in exc.errors(include_input=False)
        )
    reason = invalid(parsed)
    return f"gateway validation refuses it: {reason}" if reason else None


def structural_problems(tools: Mapping[str, Any], models: Mapping[str, type[BaseModel]]) -> list[str]:
    """No field the gateway treats as optional may be advertised as required (the p05 class)."""
    out = []
    for name, tool in tools.items():
        if name not in models:  # read tools have no gateway model
            continue
        required = set(tool.params_json_schema.get("required", []))
        optional = {f for f, info in models[name].model_fields.items() if not info.is_required()}
        if bad := required & optional:
            out.append(f"{name}: advertises optional field(s) {sorted(bad)} as required")
    return out


def check(
    scenarios: list[dict[str, Any]],
    tools: Mapping[str, Any],
    models: Mapping[str, type[BaseModel]],
    invalid: Any,
) -> list[str]:
    problems = structural_problems(tools, models)
    for s in scenarios:
        if s["phase"] > 3:
            continue
        text = " ".join(s["turns"])
        for request in s["requests"]:
            names = TOOLS_FOR.get(request["action"])
            if not names:
                problems.append(f"{s['id']}: no tool expresses action {request['action']!r}")
                continue
            held = [n for n in names if n in tools]
            if not held:
                problems.append(f"{s['id']}: the agent holds none of {names}")
                continue
            if "order" in request and request["order"] not in text:
                problems.append(f"{s['id']}: order {request['order']} is not in the customer's turns")
            found: list[str] = []
            for name in held:
                schema = tools[name].params_json_schema
                args = candidate_args(name, request, text)
                issues = []
                for variant, label in ((args, "omitted"), (_with_nulls(args, schema), "null")):
                    provider = sorted(e.message for e in Draft202012Validator(schema).iter_errors(variant))
                    if provider:
                        issues.append(f"provider rejects it (optionals {label}): {provider[0]}")
                    if (g := _gateway_problem(models[name], variant, invalid)) is not None:
                        issues.append(f"{g} (optionals {label})")
                if not issues:
                    found = []
                    break
                found += [f"{name}: {i}" for i in issues]
            problems += [f"{s['id']}: {f}" for f in found]
    return problems


def main() -> int:
    from tollgate.actions import gateway
    from tollgate.agents_def.support import agent_tools

    tools = {t.name: t for t in agent_tools()}
    problems = check(load(), tools, gateway.ARGS, gateway._invalid)
    for p in problems:
        print("PROBLEM", p)
    phase3 = [s for s in load() if s["phase"] <= 3 and s["requests"]]
    requests = sum(len(s["requests"]) for s in phase3)
    print(f"{requests} expected requests in {len(phase3)} scenarios, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
