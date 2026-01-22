"""
Error Recovery Module

Implements exponential backoff with jitter for transient errors.
Provides error classification and retry logic.

Gold Tier Requirement #8: Error Recovery & Graceful Degradation
"""

import time
import random
import logging
from enum import Enum
from functools import wraps
from typing import Callable, Any, Optional, Type
from dataclasses import dataclass


class ErrorType(Enum):
    """Error classification for recovery strategy"""
    TRANSIENT = "transient"      # Network timeout, API rate limit
    AUTH = "auth"                 # Expired token, revoked access
    LOGIC = "logic"               # Claude misinterprets message
    DATA = "data"                 # Corrupted file, missing field
    SYSTEM = "system"             # Orchestrator crash, disk full


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True


class ErrorRecovery:
    """
    Error recovery with exponential backoff and jitter.

    Usage:
        recovery = ErrorRecovery()
        result = recovery.execute_with_retry(
            func=my_function,
            args=(arg1, arg2),
            error_type=ErrorType.TRANSIENT
        )
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.logger = logging.getLogger(__name__)

    def classify_error(self, error: Exception) -> ErrorType:
        """
        Classify error to determine recovery strategy.

        Args:
            error: The exception to classify

        Returns:
            ErrorType enum value
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()

        # Network/timeout errors
        if any(keyword in error_str for keyword in ['timeout', 'connection', 'network']):
            return ErrorType.TRANSIENT

        # Rate limiting
        if any(keyword in error_str for keyword in ['rate limit', 'too many requests', '429']):
            return ErrorType.TRANSIENT

        # Authentication errors
        if any(keyword in error_str for keyword in ['auth', 'token', 'unauthorized', '401', '403']):
            return ErrorType.AUTH

        # Data errors
        if any(keyword in error_type_name for keyword in ['valueerror', 'typeerror', 'keyerror']):
            return ErrorType.DATA

        # File/IO errors
        if any(keyword in error_type_name for keyword in ['ioerror', 'oserror', 'filenotfound']):
            return ErrorType.SYSTEM

        # Default to logic error
        return ErrorType.LOGIC

    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """
        Determine if error should be retried.

        Args:
            error_type: Classification of the error
            attempt: Current attempt number (0-indexed)

        Returns:
            True if should retry, False otherwise
        """
        # Never retry beyond max attempts
        if attempt >= self.config.max_attempts:
            return False

        # Retry transient errors
        if error_type == ErrorType.TRANSIENT:
            return True

        # Don't retry auth, logic, or data errors
        if error_type in [ErrorType.AUTH, ErrorType.LOGIC, ErrorType.DATA]:
            return False

        # Retry system errors once
        if error_type == ErrorType.SYSTEM:
            return attempt < 1

        return False

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry using exponential backoff with jitter.

        Formula: delay = min(base_delay * (exponential_base ** attempt), max_delay)
        With jitter: delay = delay * random(0.5, 1.5)

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)

        # Cap at max delay
        delay = min(delay, self.config.max_delay)

        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter_factor = random.uniform(0.5, 1.5)
            delay = delay * jitter_factor

        return delay

    def execute_with_retry(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        error_type: Optional[ErrorType] = None
    ) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            args: Positional arguments for function
            kwargs: Keyword arguments for function
            error_type: Optional pre-classified error type

        Returns:
            Function result

        Raises:
            Last exception if all retries exhausted
        """
        kwargs = kwargs or {}
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)

                # Success - log if this was a retry
                if attempt > 0:
                    self.logger.info(
                        f"✅ Retry successful after {attempt} attempts: {func.__name__}"
                    )

                return result

            except Exception as e:
                last_exception = e

                # Classify error if not pre-classified
                classified_type = error_type or self.classify_error(e)

                # Check if should retry
                if not self.should_retry(classified_type, attempt):
                    self.logger.error(
                        f"❌ Error not recoverable ({classified_type.value}): {func.__name__} - {e}"
                    )
                    raise

                # Calculate delay
                delay = self.calculate_delay(attempt)

                # Log retry attempt
                self.logger.warning(
                    f"⚠️  Attempt {attempt + 1}/{self.config.max_attempts} failed: "
                    f"{func.__name__} - {e}. Retrying in {delay:.2f}s..."
                )

                # Wait before retry
                time.sleep(delay)

        # All retries exhausted
        self.logger.error(
            f"❌ All {self.config.max_attempts} retry attempts exhausted: {func.__name__}"
        )
        raise last_exception


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    error_type: Optional[ErrorType] = None
):
    """
    Decorator for automatic retry with exponential backoff.

    Usage:
        @with_retry(max_attempts=3, base_delay=1.0)
        def my_function():
            # Function that might fail
            pass

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        error_type: Optional pre-classified error type

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay
            )
            recovery = ErrorRecovery(config)
            return recovery.execute_with_retry(
                func=func,
                args=args,
                kwargs=kwargs,
                error_type=error_type
            )
        return wrapper
    return decorator


# Critical rule: NEVER auto-retry payments
class PaymentError(Exception):
    """Exception for payment-related errors - never auto-retry"""
    pass


def is_payment_operation(func_name: str) -> bool:
    """Check if operation is payment-related"""
    payment_keywords = ['payment', 'pay', 'transfer', 'invoice', 'transaction']
    return any(keyword in func_name.lower() for keyword in payment_keywords)
