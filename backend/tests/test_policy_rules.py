"""tollgate/policy/rules.yaml must equal the owner-approved pre-registration (eval/PREREGISTRATION.md)."""

from pathlib import Path

import yaml

from eval.verify_scenarios import PREREGISTERED_POLICY

RULES = Path(__file__).resolve().parents[1] / "tollgate" / "policy" / "rules.yaml"


def test_rules_yaml_equals_preregistered_policy() -> None:
    rules = yaml.safe_load(RULES.read_text())
    rules.pop("disclosure")  # classification of the rules, not a policy value (I15)
    assert rules == PREREGISTERED_POLICY


def test_every_rule_is_classified_published_or_internal_exactly_once() -> None:
    rules = yaml.safe_load(RULES.read_text())
    tiers = rules.pop("disclosure")
    published, internal = tiers["published"], tiers["internal"]
    assert sorted(published + internal) == sorted(rules)
    assert not set(published) & set(internal)
    # Control parameters can never be published (I15, tier C).
    for key in ("refund", "store_credit", "window_amount_cap", "rolling_window_days",
                "max_refunds_in_window_before_approval"):  # fmt: skip
        assert key in internal


def test_store_credit_auto_limit_is_higher_than_refunds_and_explained() -> None:
    rules = yaml.safe_load(RULES.read_text())
    for ccy in ("USD", "PKR"):
        assert rules["store_credit"]["auto_max"][ccy] > rules["refund"]["auto_max"][ccy]
    assert "stays with the business" in RULES.read_text()
