"""AsyncOpenAI client for the configured OpenAI-compatible provider. Model IDs come from `.env`."""

import openai
from openai import AsyncOpenAI

from tollgate.config import LLMSettings
from tollgate.errors import ConfigError, ModelNotAvailableError, ProviderError, RateLimitError


def make_client(settings: LLMSettings) -> AsyncOpenAI:
    key = settings.api_key()
    if key is None or not key.get_secret_value():
        raise ConfigError(f"API key for provider '{settings.llm_provider}' is not set in .env")
    # max_retries=0: 429s surface as typed errors; retry policy lives in llm/retry.py (Rule 0.1.7).
    return AsyncOpenAI(api_key=key.get_secret_value(), base_url=settings.base_url(), max_retries=0)


def configured_models(settings: LLMSettings) -> list[str]:
    """The distinct model IDs in the MODEL_FAST / MODEL_STRONG slots, in slot order."""
    models = [m for m in (settings.model_fast, settings.model_strong) if m]
    if not models:
        raise ConfigError("MODEL_FAST and MODEL_STRONG are both unset; run scripts/resolve_models.py")
    return list(dict.fromkeys(models))


async def list_model_ids(client: AsyncOpenAI) -> list[str]:
    try:
        page = await client.models.list()
    except openai.APIStatusError as exc:
        raise translate_api_error(exc) from exc
    except openai.APIConnectionError as exc:
        raise ProviderError(f"cannot reach provider: {exc}") from exc
    return sorted(m.id for m in page.data)


async def require_models_available(client: AsyncOpenAI, models: list[str]) -> None:
    available = set(await list_model_ids(client))
    missing = [m for m in models if m not in available]
    if missing:
        raise ModelNotAvailableError(f"not served by provider /models: {missing}")


def translate_api_error(exc: openai.APIStatusError) -> ProviderError:
    if exc.status_code == 429:
        header = exc.response.headers.get("retry-after")
        retry_after = float(header) if header is not None else None
        return RateLimitError(f"rate limited: {exc.message}", retry_after)
    return ProviderError(f"provider HTTP {exc.status_code}: {exc.message}")
