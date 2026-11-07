"""Settings from the repo-root `.env` (git-ignored). Every variable is documented in `.env.example`.

Settings are split by concern so a script only requires the variables it actually uses.
"""

from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
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
    # 90% of Groq's published 200K tokens/day per model (rate-limits page, verified 2026-11-07).
    llm_daily_token_budget: int = 180_000
    llm_turn_token_estimate: int = (
        8_000  # pre-flight reserve for one chat turn (Section 2.3: 2-6 calls x 2-4k)
    )

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


ASYMMETRIC_ALGS = frozenset({"ES256", "RS256"})
SYMMETRIC_ALGS = frozenset({"HS256"})


class AuthSettings(BaseSettings):
    """How Supabase access tokens are verified (spec Section 2.4; DECISIONS C4).

    jwks mode (local stack, observed 2026-11-07: ES256): keys from
    <SUPABASE_URL>/auth/v1/.well-known/jwks.json.
    secret mode (legacy projects): HS256 with AUTH_JWT_SECRET. The two modes never share algorithms,
    which rules out algorithm-confusion forgeries.
    """

    model_config = _COMMON

    supabase_url: str
    auth_jwt_mode: Literal["jwks", "secret"] = "jwks"
    auth_jwt_algorithms: list[str] = ["ES256"]
    auth_jwt_secret: SecretStr | None = None
    auth_audience: str = "authenticated"

    @model_validator(mode="after")
    def _check_mode(self) -> "AuthSettings":
        algs = set(self.auth_jwt_algorithms)
        if not algs:
            raise ValueError("AUTH_JWT_ALGORITHMS must not be empty")
        if self.auth_jwt_mode == "jwks" and not algs <= ASYMMETRIC_ALGS:
            raise ValueError(f"jwks mode allows only {sorted(ASYMMETRIC_ALGS)}")
        if self.auth_jwt_mode == "secret":
            if not algs <= SYMMETRIC_ALGS:
                raise ValueError(f"secret mode allows only {sorted(SYMMETRIC_ALGS)}")
            if self.auth_jwt_secret is None or len(self.auth_jwt_secret.get_secret_value()) < 32:
                raise ValueError("secret mode needs AUTH_JWT_SECRET (>= 32 chars)")
        return self

    @property
    def issuer(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1"

    @property
    def jwks_url(self) -> str:
        return f"{self.issuer}/.well-known/jwks.json"


class AppSettings(BaseSettings):
    """API process settings."""

    model_config = _COMMON

    frontend_origin: str = "http://localhost:3000"
