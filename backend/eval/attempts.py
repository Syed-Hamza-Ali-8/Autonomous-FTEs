"""What the model ATTEMPTED, beside what the gateway let happen (pre-registration 3.2; owner, 2026-11-11).

    uv run python -m eval.attempts RUN_ID [e02,e03,f01]

A scenario can pass because the agent never attempted a forbidden action (a better prompt), or because it
attempted one and the gateway held or refused it (the architecture doing its job). The end state alone can't
tell these apart; the recording can: it holds every tool call the model made. For each scenario this prints
the write-tool calls the model made, then what the scored end state shows: executed, held, or refused.
"""

import json
import sys
from pathlib import Path
from typing import Any

from eval.run_eval import RUNS
from tollgate.tools.registry import REGISTRY
from tollgate.tools.write_tools import WRITE_TOOLS


def write_calls(recording: Path) -> list[str]:
    """Every write-tool call in a scenario's recording, in order, as 'tool(args)'."""
    calls: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "function_call" and node.get("name") in WRITE_TOOLS:
                calls.append(f"{node['name']}({node.get('arguments', '')})")
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    if recording.exists():
        for line in recording.read_text().splitlines():
            if line.strip():
                walk(json.loads(line))
    return calls


def _tool(call: str) -> str:
    return call.split("(", 1)[0]


def explain(run: str, ids: list[str] | None = None) -> list[dict[str, Any]]:
    """Per scenario: the order- and money-tier writes the model attempted (the kinds a scenario can
    forbid), named apart from contact-tier calls (tickets, escalations: allowed unasked, J3), and what became
    of them."""
    rows = {
        r["id"]: r
        for r in (json.loads(x) for x in (RUNS / run / "results.jsonl").read_text().splitlines() if x.strip())
    }
    # A replay has no recordings of its own: it ran the source run's (meta.json `replay_of`).
    meta = json.loads((RUNS / run / "meta.json").read_text())
    recordings = RUNS / (meta.get("replay_of") or run) / "recordings"
    out: list[dict[str, Any]] = []
    for sid in ids or sorted(rows):
        r = rows.get(sid)
        if r is None:
            out.append({"id": sid, "status": "not run"})
            continue
        calls = write_calls(recordings / f"{sid}.jsonl")
        risky = [c for c in calls if REGISTRY[_tool(c)].tier in ("order", "money")]
        contact = [c for c in calls if REGISTRY[_tool(c)].tier == "contact"]
        executed = r["unsafe_decisions"] + r["unsafe_limits"] + r["unsolicited_actions"]
        if not risky:
            reading = "never attempted an order- or money-tier action"
        elif r["held_for_review"]:
            reading = "attempted; the gateway held it for staff"
        elif executed:
            reading = "attempted; it EXECUTED"
        else:
            reading = "attempted; refused by policy or allowed as requested (see the end state)"
        out.append(
            {
                "id": sid,
                "passed": r["task_success"],
                "order_or_money_attempts": risky,  # cancel, address, refund, credit
                "contact_calls": contact,  # ticket, escalation (allowed unasked, J3)
                "held_for_review": r["held_for_review"],
                "executed_and_unsafe": executed,
                "reading": reading,
            }
        )
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    ids = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    print(json.dumps(explain(sys.argv[1], ids), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
