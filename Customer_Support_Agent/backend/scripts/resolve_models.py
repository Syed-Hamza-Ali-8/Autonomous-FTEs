"""List the provider's models and check that MODEL_FAST / MODEL_STRONG in .env are served.

Usage (from backend/):  uv run python scripts/resolve_models.py
Prints model IDs only, never keys. Exits 1 if a configured model is not served (Rule 0.1.1).
Set MODEL_FAST / MODEL_STRONG in .env yourself from the printed list; nothing is written.
"""

import asyncio
import sys

from tollgate.config import LLMSettings
from tollgate.errors import TollgateError
from tollgate.llm.provider import list_model_ids, make_client


async def main() -> int:
    settings = LLMSettings()
    client = make_client(settings)
    ids = await list_model_ids(client)
    print(f"provider={settings.llm_provider} base_url={settings.base_url()} models={len(ids)}")
    for model_id in ids:
        print(f"  {model_id}")

    status = 0
    for slot, value in (("MODEL_FAST", settings.model_fast), ("MODEL_STRONG", settings.model_strong)):
        if value is None:
            print(f"{slot}: unset")
            status = 1
        elif value in ids:
            print(f"{slot}: {value}  OK (served)")
        else:
            print(f"{slot}: {value}  NOT SERVED by this provider")
            status = 1
    return status


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except TollgateError as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(2)
