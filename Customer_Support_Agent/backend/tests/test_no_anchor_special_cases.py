"""Evaluation anchors (fixture rows ORD-1151+, CUS-041+) must get no special treatment (owner rule).

They exist only so scenarios and the adversarial suite can exercise rolling-window rules. If any
application code mentioned them, the eval would be measuring a special case, not the product.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = json.loads((ROOT / "backend" / "eval" / "fixtures" / "store_seed.json").read_text())
APP_DIRS = [ROOT / "backend" / "tollgate", ROOT / "frontend" / "src"]
SUFFIXES = {".py", ".ts", ".tsx", ".sql", ".md", ".yaml", ".json"}


def _app_files() -> list[Path]:
    return [p for d in APP_DIRS for p in d.rglob("*") if p.is_file() and p.suffix in SUFFIXES]


def test_anchor_list_is_present() -> None:
    anchors = FIXTURE["anchors"]
    assert anchors["orders"] and anchors["customers"]


def test_no_application_code_mentions_an_anchor() -> None:
    ids = FIXTURE["anchors"]["orders"] + FIXTURE["anchors"]["customers"]
    pattern = re.compile("|".join(map(re.escape, ids)) + r"|\banchor", re.IGNORECASE)
    hits = [
        f"{p.relative_to(ROOT)}:{n}"
        for p in _app_files()
        for n, line in enumerate(p.read_text(errors="ignore").splitlines(), 1)
        if pattern.search(line)
    ]
    assert hits == []


def test_scan_is_not_vacuous() -> None:
    files = _app_files()
    assert len(files) > 40
    assert any("read_tools.py" in str(p) for p in files) and any(p.suffix == ".tsx" for p in files)
