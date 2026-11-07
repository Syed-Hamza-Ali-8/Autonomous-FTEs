"""Settings from the repo-root `.env` (git-ignored). Every variable is documented in `.env.example`.

Settings are split by concern so a script only requires the variables it actually uses.
"""

from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"

_COMMON = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")


class LLMSettings(BaseSettings):
    """Provider and model slots. Model IDs come from the provider's /models endpoint (Rule 0.1.1)."""

    model_config = _COMMON

    llm_provider: Literal["groq", "gemini"] = "groq"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_api_key: SecretStr | None = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_api_key: SecretStr | None = None
    model_fast: str | None = None
    model_strong: str | None = None

    @field_validator("groq_api_key", "gemini_api_key", "model_fast", "model_strong", mode="before")
    @classmethod
    def _blank_is_unset(cls, value: object) -> object:
        # `.env.example` ships `KEY=` lines; an empty value means "unset", not a model named "".
        return None if isinstance(value, str) and not value.strip() else value

    def base_url(self) -> str:
        return self.groq_base_url if self.llm_provider == "groq" else self.gemini_base_url

    def api_key(self) -> SecretStr | None:
        return self.groq_api_key if self.llm_provider == "groq" else self.gemini_api_key


class SupabaseSettings(BaseSettings):
    """Database and Supabase API access. Tests require a localhost DATABASE_URL (invariant 20)."""

    model_config = _COMMON

    database_url: SecretStr
    supabase_url: str
    supabase_anon_key: SecretStr
    supabase_service_role_key: SecretStr | None = None
