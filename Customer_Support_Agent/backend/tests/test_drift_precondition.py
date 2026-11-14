"""The owner's hard precondition for the merged phase (DECISIONS L16, L17; pre-registration section 4): NO
tokens are spent unless a strict replay of the 47 Phase 4 scenarios reported ZERO drifted calls on the
current build. Committed BEFORE the code it tests: until `eval/drift_gate.py` exists, this module fails at
import, which is the expected state of the pre-registration commit.

Pre-registered interface:
- `record(path, run_id, scenarios, drifted_calls)` writes the strict replay's result, stamped with
  `build_fingerprint()`: a hash of the prompt version, the tool-schema version and every source file under
  `tollgate/` and `eval/` that a replay exercises;
- `refusal(path)` returns why a live run may NOT start, or None when it may. The live runner calls it before
  its budget pre-flight and stops on any refusal.
"""

import json
from pathlib import Path

import pytest

from eval import drift_gate


def test_no_record_refuses(tmp_path: Path) -> None:
    assert drift_gate.refusal(tmp_path / "drift_check.json") is not None


def test_any_drift_refuses(tmp_path: Path) -> None:
    path = tmp_path / "drift_check.json"
    drift_gate.record(path, "replay-x", scenarios=47, drifted_calls=1)
    assert drift_gate.refusal(path) is not None


def test_fewer_than_the_47_refuses(tmp_path: Path) -> None:
    path = tmp_path / "drift_check.json"
    drift_gate.record(path, "replay-x", scenarios=46, drifted_calls=0)
    assert drift_gate.refusal(path) is not None


def test_a_record_from_another_build_refuses(tmp_path: Path) -> None:
    path = tmp_path / "drift_check.json"
    drift_gate.record(path, "replay-x", scenarios=47, drifted_calls=0)
    data = json.loads(path.read_text())
    path.write_text(json.dumps({**data, "build": "0" * 64}))  # the code changed since the check ran
    assert drift_gate.refusal(path) is not None


def test_a_clean_record_for_this_build_allows(tmp_path: Path) -> None:
    path = tmp_path / "drift_check.json"
    drift_gate.record(path, "replay-x", scenarios=47, drifted_calls=0)
    assert drift_gate.refusal(path) is None


def test_the_fingerprint_moves_when_the_code_moves(monkeypatch: pytest.MonkeyPatch) -> None:
    before = drift_gate.build_fingerprint()
    monkeypatch.setattr(drift_gate, "PROMPT_VERSION", "support-v4-edited")
    assert drift_gate.build_fingerprint() != before
