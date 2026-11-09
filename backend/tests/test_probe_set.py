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
    "M9": "am02 am03 am05 am06 tk01",
    "M13": "tm01 tm02",
    "M14": "sv15 sv16 os04 id04",
    "M16": "xc01 xc02 xc03 xc04 xc05 xc06 xc07 xc10 xc11 xc12 xc13",
    "M17": "am10 am15",
    "M18": "am11",
    "M19": "b01 b05 b17 b18 b19 b20 dp02 dp03 dp04 dp05 dp06 am01 am11 am14 te01 te02 te07 te08 os01"
    " os02 id01 id02 tm01",
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
