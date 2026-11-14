"""Write the API's OpenAPI schema to frontend/openapi.json for `npm run gen:types` (spec Section 2.1).

Usage (from backend/):  uv run python scripts/export_openapi.py [--check]
"""

import argparse
import json
import sys

from tollgate.config import REPO_ROOT
from tollgate.main import app

OUT = REPO_ROOT / "frontend" / "openapi.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if frontend/openapi.json is out of date")
    text = json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"
    if parser.parse_args().check:
        same = OUT.exists() and OUT.read_text() == text
        print("openapi.json up to date" if same else "openapi.json is stale: run scripts/export_openapi.py")
        return 0 if same else 1
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
