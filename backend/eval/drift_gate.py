"""The owner's hard precondition for the merged phase (DECISIONS L16, L17; pre-registration section 4): NO
tokens are spent unless a strict replay of the 47 Phase 4 scenarios reported ZERO drifted calls on the
current build.

A strict replay (`run_eval --phase 4 --replay 20261111T184142Z`, no `--allow-drift`) of the full 47 records
its result here, stamped with `build_fingerprint()`. Every live run of the merged phase calls `refusal()`
first and stops on any refusal: no record, any drift, fewer than the 47, or a record from another build (the
code changed since the check ran, so the check no longer describes it).
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from tollgate.agents_def.support import PROMPT_VERSION, tool_schema_version

BACKEND = Path(__file__).resolve().parents[1]
RECORD = Path(__file__).resolve().parent / "runs" / "eval" / "drift_check.json"
SCENARIOS = 47  # the Phase 4 run whose results carry over (L16)
SOURCE_RUN = "20261111T184142Z"
# Everything a replay exercises: the application, the prompt and policy files, and the eval harness itself.
_SOURCES = ("tollgate/**/*.py", "tollgate/**/*.md", "tollgate/**/*.yaml", "eval/*.py")


def build_fingerprint() -> str:
    h = hashlib.sha256()
    h.update(f"{PROMPT_VERSION}\n{tool_schema_version()}\n".encode())
    for pattern in _SOURCES:
        for path in sorted(BACKEND.glob(pattern)):
            h.update(str(path.relative_to(BACKEND)).encode())
            h.update(path.read_bytes())
    return h.hexdigest()


def record(path: Path, run_id: str, scenarios: int, drifted_calls: int, detail: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "scenarios": scenarios,
                "drifted_calls": drifted_calls,
                "detail": detail,
                "build": build_fingerprint(),
                "prompt_version": PROMPT_VERSION,
                "tool_schema_version": tool_schema_version(),
                "at": datetime.now(UTC).isoformat(),
            },
            indent=2,
        )
        + "\n"
    )


def refusal(path: Path = RECORD) -> str | None:
    """Why a live run may NOT start, or None when it may."""
    if not path.exists():
        return "no strict drift check of the 47 on record: run the strict replay first"
    data = json.loads(path.read_text())
    if data.get("drifted_calls") != 0:
        return f"the strict replay reported {data.get('drifted_calls')} drifted call(s): {data.get('detail')}"
    if data.get("scenarios") != SCENARIOS:
        return f"the strict replay covered {data.get('scenarios')} scenarios, not the {SCENARIOS}"
    if data.get("build") != build_fingerprint():
        return "the code changed since the strict replay ran: run it again on this build"
    return None
