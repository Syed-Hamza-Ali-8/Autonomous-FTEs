"""Source-level mutation checks (Rule 0.1.11): remove one protection, require its targeted test to FAIL.

A mutation replaces an exact snippet in one file, runs the target tests, and restores the original
bytes in `finally` (verified by hash). The whole suite must pass before and after.
"""

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
RUNS_DIR = BACKEND / "eval" / "runs" / "mutation"


@dataclass(frozen=True)
class CodeMutation:
    name: str
    removes: str
    file: str  # relative to backend/
    old: str
    new: str
    must_fail: tuple[str, ...]  # pytest node ids relative to backend/


def run_pytest(*targets: str) -> tuple[int, str]:
    proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, "-m", "pytest", *targets, "-q", "-p", "no:cacheprovider"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        check=False,
    )
    lines = (proc.stdout + proc.stderr).strip().splitlines()
    return proc.returncode, "\n".join(lines[-3:])


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_suite(label: str, suite: str, mutations: tuple[CodeMutation, ...]) -> int:
    code, tail = run_pytest(suite)
    record: dict[str, object] = {"suite": suite, "baseline_before": {"passed": code == 0, "tail": tail}}
    print(f"baseline before: {'PASS' if code == 0 else 'FAIL'}  {tail.splitlines()[-1] if tail else ''}")
    if code != 0:
        print("baseline must pass before mutating", file=sys.stderr)
        return 1

    results = []
    for m in mutations:
        path = BACKEND / m.file
        original = path.read_bytes()
        text = original.decode()
        entry: dict[str, object] = {"mutation": m.name, "removes": m.removes, "targets": list(m.must_fail)}
        if text.count(m.old) != 1:
            entry["target_failed"] = False
            entry["error"] = f"snippet found {text.count(m.old)} times in {m.file}; mutation not applied"
        else:
            try:
                path.write_text(text.replace(m.old, m.new))
                code, tail = run_pytest(*m.must_fail)
                entry["target_failed"] = code != 0
                entry["tail"] = tail
            finally:
                path.write_bytes(original)
            if _sha(path.read_bytes()) != _sha(original):
                raise SystemExit(f"FATAL: {m.file} was not restored")
        caught = bool(entry["target_failed"])
        extra = f"  error={entry['error']}" if "error" in entry else ""
        print(f"{m.name}: {'CAUGHT' if caught else 'NOT CAUGHT'}{extra}")
        results.append(entry)

    code, tail = run_pytest(suite)
    record["baseline_after"] = {"passed": code == 0, "tail": tail}
    record["mutations"] = results
    print(f"baseline after: {'PASS' if code == 0 else 'FAIL'}  {tail.splitlines()[-1] if tail else ''}")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out = RUNS_DIR / f"{label}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(f"recorded: {out.relative_to(BACKEND)}")
    return 0 if code == 0 and all(r["target_failed"] for r in results) else 1
