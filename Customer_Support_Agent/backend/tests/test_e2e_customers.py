"""The e2e customers are the Playwright suite's alone (owner, 2026-11-15; DECISIONS L24).

The suite signs in only as `anchors.e2e_customers`. Nothing else may touch them, and they may touch nothing
else: no eval scenario, no adversarial conversation (LLM or tool-layer) and no demo sign-in names an e2e
customer or one of its orders; and the e2e customers are none of the customers those name. Shared mutable
state between the test suite and other use of the database is the problem this prevents (the same class as
per-test rollback, C5, and per-scenario database copies).
"""

import json
import re
from pathlib import Path

import pytest

from scripts import e2e_users

BACKEND = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((BACKEND / "eval" / "fixtures" / "store_seed.json").read_text())
# Every file that scripts a conversation or a tool call against the store.
SCRIPTED = sorted((BACKEND / "eval").glob("*.jsonl"))
ID = re.compile(r"\b(?:CUS|ORD)-\d{3,4}\b")

E2E = set(FIXTURE["anchors"]["e2e_customers"])
E2E_ORDERS = {o["id"] for o in FIXTURE["orders"] if o["customer_id"] in E2E}
DEMO = {c["id"] for c in FIXTURE["customers"] if c.get("demo_login")}


def ids_in(text: str) -> set[str]:
    return set(ID.findall(text))


def named_elsewhere() -> set[str]:
    """Customer and order IDs named by any eval scenario or adversarial conversation."""
    return set().union(*(ids_in(p.read_text()) for p in SCRIPTED))


def test_the_scripted_files_are_the_ones_expected() -> None:
    """The scan is not vacuous: it reads the 47 scenarios and both adversarial sets, which name customers."""
    expected = {"scenarios.jsonl", "adversarial_llm.jsonl", "adversarial_tools.jsonl"}
    assert {p.name for p in SCRIPTED} >= expected
    assert len({i for i in named_elsewhere() if i.startswith("CUS-")}) >= 20


def test_no_e2e_customer_or_order_is_named_by_an_eval_scenario_or_adversarial_conversation() -> None:
    assert (E2E | E2E_ORDERS) & named_elsewhere() == set()


def test_no_customer_used_elsewhere_is_an_e2e_customer() -> None:
    """The other direction: every customer an eval scenario, adversarial conversation or demo sign-in uses is
    outside the e2e set, and so is every customer that owns an order they name."""
    owner = {o["id"]: o["customer_id"] for o in FIXTURE["orders"]}
    named = named_elsewhere()
    used = {i for i in named if i.startswith("CUS-")} | {owner[i] for i in named if i in owner} | DEMO
    assert used & E2E == set()


def test_the_e2e_setup_signs_in_only_as_the_e2e_customers() -> None:
    assert sorted(e2e_users.e2e_customer_ids()) == sorted(E2E) == ["CUS-051", "CUS-052"]
    assert E2E_ORDERS and all(o["customer_id"] in E2E for o in FIXTURE["orders"] if o["id"] in E2E_ORDERS)


@pytest.mark.parametrize("planted", ['{"customer": "CUS-051", "turns": ["hi"]}', '{"order_id": "ORD-1165"}'])
def test_the_scan_catches_a_planted_e2e_id(planted: str) -> None:
    """Liveness: an e2e customer or order planted in a scripted line is found."""
    assert ids_in(planted) & (E2E | E2E_ORDERS)
