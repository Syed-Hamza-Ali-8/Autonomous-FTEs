"""tollgate/policy/rules.yaml must equal the owner-approved pre-registration (eval/PREREGISTRATION.md)."""

from pathlib import Path

import yaml

from eval.verify_scenarios import PREREGISTERED_POLICY

RULES = Path(__file__).resolve().parents[1] / "tollgate" / "policy" / "rules.yaml"


def test_rules_yaml_equals_preregistered_policy() -> None:
    assert yaml.safe_load(RULES.read_text()) == PREREGISTERED_POLICY


def test_store_credit_auto_limit_is_higher_than_refunds_and_explained() -> None:
    rules = yaml.safe_load(RULES.read_text())
    for ccy in ("USD", "PKR"):
        assert rules["store_credit"]["auto_max"][ccy] > rules["refund"]["auto_max"][ccy]
    assert "stays with the business" in RULES.read_text()
