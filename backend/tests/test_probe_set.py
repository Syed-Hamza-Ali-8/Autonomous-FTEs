"""The approved Phase 3 probe set is consistent with the fixture, and its mutation table is live.

`eval/verify_probes.py` re-derives every probe's outcome from the fixture; the derived mutation table is
pinned here exactly as pre-registered in eval/ADVERSARIAL_PREREGISTRATION.md section 6, so neither the
probes nor the reference model can drift after approval (invariant 15).
"""

import json

import pytest

from eval.verify_probes import MUTANTS, killed_by, load, verify
from eval.verify_scenarios import FIXTURE

# Space-separated probe ids, exactly as in the pre-registration's section 6.
PREREGISTERED_KILLS: dict[str, str] = {
    "M1": "xc01 xc02 xc03 xc04 xc05 xc06 xc07 xc10 xc11 xc12 xc13",
    "M2": "b02 b03 b04 b06 b07 b08 b10 b11 b12 b14 b15 b16 b18 b20 dp01 dp02 dp03 dp04 dp05 dp06"
    " am12 te01 te02 te03 te04 te05 te06 te07 te08 sv01 sv02 sv03 sv04 sv05 sv06 sv07 sv08"
    " sv09 sv10 sv11 sv12 sv13 sv14 sv15 os01 os03 af01 af05 id05 id07 tm02",
    "M3": "id01 id02 id03 id04 id05 id06",
    "M3b": "id07",
    "M4": "am01 am13",
    "M5": "b18 b20 te01 te02 te03 te04 te05 te06",
    "M6": "dp01 dp04 dp06 te07 af05",
    "M7": "dp04 dp05",
    "M8": "xc08 xc09 am08 sv17 af02 af03 af04",
    "M8b": "am07 am16",
    "M8c": "am04",
    "M9": "am02 am03 am05 am06 ad04 tk01",
    "M13": "tm01 tm02",
    "M14": "sv15 sv16 os04 id04",
    "M16": "xc01 xc02 xc03 xc04 xc05 xc06 xc07 xc10 xc11 xc12 xc13",
    "M17": "am10 am15",
    "M18": "am11",
    "M19": "b01 b05 b17 b18 b19 b20 dp02 dp03 dp04 dp05 dp06 am01 am11 am14 te01 te02 te07 te08 os01"
    " os02 id01 id02 tm01",
    "M23": "ad01 ad02 ad03",
    "M24": "ad02 ad03",
}


@pytest.fixture(scope="module")
def fixture() -> dict[str, object]:
    return json.loads(FIXTURE.read_text())


def test_probe_set_matches_the_fixture(fixture: dict[str, object]) -> None:
    assert verify(load(), fixture) == []


def test_every_reference_mutant_is_preregistered() -> None:
    assert set(MUTANTS) == set(PREREGISTERED_KILLS)


@pytest.mark.parametrize("mutant", sorted(PREREGISTERED_KILLS))
def test_mutation_table_is_as_preregistered(fixture: dict[str, object], mutant: str) -> None:
    assert sorted(killed_by(load(), fixture, mutant)) == sorted(PREREGISTERED_KILLS[mutant].split())


# -- K5: no probe-based mutation may rest on a single probe (owner, 2026-11-09) ---------------------------

# DECISIONS K4: known single-probe mutations, each due a second killing probe in Phase 4. May only shrink.
K4_SINGLE_PROBE = {"M3b", "M8c", "M18"}


def coverage_problems(kills: dict[str, list[str]], allowed: set[str]) -> list[str]:
    """Mutations killed by fewer than two probes and not on the recorded list, plus listed ones now fixed."""
    out = [f"{m} is killed by only {len(ids)} probe(s): {ids}" for m, ids in sorted(kills.items())
           if len(ids) < 2 and m not in allowed]  # fmt: skip
    out += [f"{m} now has {len(kills[m])} probes: remove it from K4_SINGLE_PROBE" for m in sorted(allowed)
            if m in kills and len(kills[m]) >= 2]  # fmt: skip
    out += [f"{m} is on K4_SINGLE_PROBE but no longer in the table" for m in sorted(allowed - set(kills))]
    return out


def probe_kills() -> dict[str, list[str]]:
    """Every probe-based mutation: the derived table plus the hand-listed rows (M10, M10b)."""
    from tests.test_adversarial_mutations import KILLS

    return {m: ids.split() for m, ids in KILLS.items()}


def test_k5_every_mutation_is_killed_by_at_least_two_probes() -> None:
    assert coverage_problems(probe_kills(), K4_SINGLE_PROBE) == []


def test_k5_check_is_live() -> None:
    """Mutation check: a planted single-probe mutation, and a fixed-but-still-listed one, are both caught."""
    planted = {**probe_kills(), "MX": ["am01"]}
    assert any("MX is killed by only 1" in p for p in coverage_problems(planted, K4_SINGLE_PROBE))
    fixed = {**probe_kills(), "M18": ["am11", "am12"]}
    assert any("M18 now has 2 probes" in p for p in coverage_problems(fixed, K4_SINGLE_PROBE))
