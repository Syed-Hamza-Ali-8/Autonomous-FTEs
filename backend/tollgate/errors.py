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


class AuthError(TollgateError):
    """A credential was missing, malformed, expired, or failed verification (HTTP 401).

    `reason` is for logs only; clients always get the same generic message.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class AuthUnavailableError(TollgateError):
    """The signing keys could not be fetched, so no token can be verified (HTTP 503, never a pass)."""


class ForbiddenError(TollgateError):
    """A verified identity has no role for this resource (HTTP 403)."""


class BudgetExceededError(TollgateError):
    """A model's rolling 24h token budget would be exceeded; the request is refused, never degraded."""


class NotFoundError(TollgateError):
    """The resource does not exist or is not the caller's. Deliberately one error for both (invariant 8)."""


class ActionFailedError(TollgateError):
    """An Action Gateway submission failed after validation. Its effect was rolled back and audited."""


class ApprovalConflictError(TollgateError):
    """A staff decision can't be applied to this request as it now stands (HTTP 409). Nothing was changed.

    `reason`: already_decided (decided before, or concurrently) | amount_mismatch (the screen the staff member
    decided on is stale). An approval that has expired is not an error: the expiry is recorded and returned.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
