"""Typed exceptions. No silent fallbacks (Rule 0.1.7): failures raise one of these and are logged."""


class TollgateError(Exception):
    """Base class for every Tollgate error."""


class ConfigError(TollgateError):
    """Required configuration is missing or invalid."""


class ProviderError(TollgateError):
    """The LLM provider returned an error or an unusable response."""


class RateLimitError(ProviderError):
    """The provider rate-limited the request (HTTP 429)."""

    def __init__(self, message: str, retry_after_s: float | None) -> None:
        super().__init__(message)
        self.retry_after_s = retry_after_s


class ModelNotAvailableError(ProviderError):
    """A configured model ID is not served by the provider's /models endpoint."""
