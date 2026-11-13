"""The K7 zero-token measurement (Phases 5+6 pre-registration section 6; DECISIONS L13). No model call.

    uv run python -m eval.k7_measure > k7_measurement.json

Runs the K7 check (guardrails/facts.py) over every customer-facing reply recorded in the Phase 3 gate set
and the Phase 4 run, counted once each (a resumed run's later row wins). The allowlist per reply is the
customer's own email, order IDs and tracking numbers from store data: a superset of what that turn's tool
results could hold, so the measurement can only under-count firings, never over-count them. Prints every
firing and a random sample of 50 replies it did NOT fire on (seed 20261113, pre-registered), for hand
labelling. The L13 rule is applied only after the owner has reviewed the labels.
"""

import json
import random
import sys
from typing import Any

from eval.run_eval import RUNS
from eval.verify_scenarios import FIXTURE, Store, fixture_clock, load
from tollgate.guardrails import facts

RUNS_MEASURED = {
    "Phase 3 (new)": "20261110T182938Z",
    "Phase 3 (carried)": "20261109T161333Z",
    "Phase 4": "20261111T184142Z",
}
SAMPLE_SEED, SAMPLE_SIZE = 20261113, 50


def _rows(run: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for line in (RUNS / run / "results.jsonl").read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            out[row["id"]] = row
    return out


def main() -> int:
    fixture = json.loads(FIXTURE.read_text())
    store = Store.load(fixture, fixture_clock(fixture))
    customer_of = {s["id"]: s["customer"] for s in load()}
    replies: list[dict[str, Any]] = []
    for label, run in RUNS_MEASURED.items():
        for sid, row in sorted(_rows(run).items()):
            cid = customer_of[sid]
            owned = [o for o, rec in store.orders.items() if rec["customer_id"] == cid]
            allowed = [store.customers[cid]["email"], *owned]
            allowed += [s["tracking_number"] for o, s in store.shipments.items() if o in owned]
            for i, text in enumerate(row.get("replies", [])):
                found = facts.findings(text, allowed)
                replies.append(
                    {"run": label, "scenario": sid, "turn": i + 1, "findings": found, "reply": text}
                )
    fired = [r for r in replies if r["findings"]]
    quiet = [r for r in replies if not r["findings"]]
    sample = random.Random(SAMPLE_SEED).sample(  # noqa: S311 - a reproducible sample, not security
        quiet, min(SAMPLE_SIZE, len(quiet))
    )
    report = {
        "replies": len(replies),
        "fired": len(fired),
        "fired_rate": round(len(fired) / len(replies), 4) if replies else None,
        "firings": fired,
        "not_fired_sample": sample,
    }
    json.dump(report, sys.stdout, indent=1, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
