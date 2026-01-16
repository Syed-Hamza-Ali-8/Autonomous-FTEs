#!/usr/bin/env python3
"""
Error Recovery Mechanisms

Provides automatic error recovery strategies for Silver tier components:
- Exponential backoff with jitter
- Circuit breaker pattern
- Graceful degradation
- State recovery
- Dead letter queue
"""

import time
import random
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import json
from enum import Enum


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by stopping requests to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
            success_threshold: Successes needed to close circuit from half-open
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def reset(self):
        """Reset circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None


class RetryStrategy:
    """
    Retry strategy with exponential backoff and jitter.
    """

    @staticmethod
    def exponential_backoff(
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        exceptions: tuple = (Exception,)
    ) -> Any:
        """
        Retry function with exponential backoff.

        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            jitter: Add random jitter to delay
            exceptions: Tuple of exceptions to catch

        Returns:
            Function result

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return func()
            except exceptions as e:
                last_exception = e

                if attempt == max_retries:
                    raise last_exception

                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)

                # Add jitter to prevent thundering herd
                if jitter:
                    delay = delay * (0.5 + random.random())

                time.sleep(delay)

        raise last_exception


class DeadLetterQueue:
    """
    Dead letter queue for failed operations.

    Stores failed operations for later retry or manual intervention.
    """

    def __init__(self, queue_dir: Path):
        """
        Initialize dead letter queue.

        Args:
            queue_dir: Directory to store failed operations
        """
        self.queue_dir = queue_dir
        self.queue_dir.mkdir(parents=True, exist_ok=True)

    def add(
        self,
        operation_id: str,
        operation_type: str,
        operation_data: Dict[str, Any],
        error: str,
        retry_count: int = 0
    ) -> Path:
        """
        Add failed operation to queue.

        Args:
            operation_id: Unique operation identifier
            operation_type: Type of operation
            operation_data: Operation data
            error: Error message
            retry_count: Number of retry attempts

        Returns:
            Path to dead letter file
        """
        dead_letter = {
            "id": operation_id,
            "type": operation_type,
            "data": operation_data,
            "error": error,
            "retry_count": retry_count,
            "timestamp": datetime.now().isoformat(),
            "status": "failed"
        }

        file_path = self.queue_dir / f"{operation_id}.json"
        with open(file_path, 'w') as f:
            json.dump(dead_letter, f, indent=2)

        return file_path

    def get_all(self) -> List[Dict[str, Any]]:
        """
        Get all items in dead letter queue.

        Returns:
            List of dead letter items
        """
        items = []
        for file_path in self.queue_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    items.append(json.load(f))
            except Exception:
                continue
        return items

    def remove(self, operation_id: str) -> bool:
        """
        Remove item from dead letter queue.

        Args:
            operation_id: Operation identifier

        Returns:
            True if removed, False if not found
        """
        file_path = self.queue_dir / f"{operation_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def retry_all(self, retry_func: Callable[[Dict[str, Any]], bool]) -> Dict[str, int]:
        """
        Retry all items in dead letter queue.

        Args:
            retry_func: Function to retry operation (returns True on success)

        Returns:
            Dictionary with success/failure counts
        """
        items = self.get_all()
        results = {"success": 0, "failed": 0}

        for item in items:
            try:
                if retry_func(item):
                    self.remove(item["id"])
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception:
                results["failed"] += 1

        return results


class StateRecovery:
    """
    State recovery for interrupted operations.

    Saves operation state periodically to enable recovery after crashes.
    """

    def __init__(self, state_dir: Path):
        """
        Initialize state recovery.

        Args:
            state_dir: Directory to store state files
        """
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save_state(
        self,
        operation_id: str,
        state: Dict[str, Any]
    ) -> Path:
        """
        Save operation state.

        Args:
            operation_id: Unique operation identifier
            state: State data to save

        Returns:
            Path to state file
        """
        state_data = {
            "id": operation_id,
            "state": state,
            "timestamp": datetime.now().isoformat()
        }

        file_path = self.state_dir / f"{operation_id}.state.json"
        with open(file_path, 'w') as f:
            json.dump(state_data, f, indent=2)

        return file_path

    def load_state(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Load operation state.

        Args:
            operation_id: Operation identifier

        Returns:
            State data or None if not found
        """
        file_path = self.state_dir / f"{operation_id}.state.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r') as f:
                state_data = json.load(f)
                return state_data.get("state")
        except Exception:
            return None

    def clear_state(self, operation_id: str) -> bool:
        """
        Clear operation state after successful completion.

        Args:
            operation_id: Operation identifier

        Returns:
            True if cleared, False if not found
        """
        file_path = self.state_dir / f"{operation_id}.state.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_all_states(self) -> List[Dict[str, Any]]:
        """
        Get all saved states (for recovery after crash).

        Returns:
            List of state data
        """
        states = []
        for file_path in self.state_dir.glob("*.state.json"):
            try:
                with open(file_path, 'r') as f:
                    states.append(json.load(f))
            except Exception:
                continue
        return states


class GracefulDegradation:
    """
    Graceful degradation strategies.

    Provides fallback mechanisms when primary services fail.
    """

    @staticmethod
    def with_fallback(
        primary_func: Callable,
        fallback_func: Callable,
        exceptions: tuple = (Exception,)
    ) -> Any:
        """
        Try primary function, fall back to secondary on failure.

        Args:
            primary_func: Primary function to try
            fallback_func: Fallback function if primary fails
            exceptions: Exceptions to catch

        Returns:
            Result from primary or fallback function
        """
        try:
            return primary_func()
        except exceptions:
            return fallback_func()

    @staticmethod
    def with_default(
        func: Callable,
        default_value: Any,
        exceptions: tuple = (Exception,)
    ) -> Any:
        """
        Try function, return default value on failure.

        Args:
            func: Function to try
            default_value: Default value to return on failure
            exceptions: Exceptions to catch

        Returns:
            Function result or default value
        """
        try:
            return func()
        except exceptions:
            return default_value

    @staticmethod
    def with_cache(
        func: Callable,
        cache_key: str,
        cache: Dict[str, Any],
        ttl: int = 300
    ) -> Any:
        """
        Try function, use cached value on failure.

        Args:
            func: Function to try
            cache_key: Cache key
            cache: Cache dictionary
            ttl: Time to live in seconds

        Returns:
            Function result or cached value
        """
        try:
            result = func()
            cache[cache_key] = {
                "value": result,
                "timestamp": datetime.now()
            }
            return result
        except Exception:
            # Try to use cached value
            if cache_key in cache:
                cached = cache[cache_key]
                age = (datetime.now() - cached["timestamp"]).total_seconds()
                if age < ttl:
                    return cached["value"]
            raise


class HealthCheck:
    """
    Health check for services and dependencies.
    """

    def __init__(self):
        """Initialize health check."""
        self.checks = {}

    def register_check(
        self,
        name: str,
        check_func: Callable[[], bool],
        critical: bool = True
    ):
        """
        Register a health check.

        Args:
            name: Check name
            check_func: Function that returns True if healthy
            critical: Whether this check is critical for operation
        """
        self.checks[name] = {
            "func": check_func,
            "critical": critical
        }

    def run_checks(self) -> Dict[str, Any]:
        """
        Run all health checks.

        Returns:
            Dictionary with check results
        """
        results = {
            "healthy": True,
            "checks": {},
            "timestamp": datetime.now().isoformat()
        }

        for name, check in self.checks.items():
            try:
                is_healthy = check["func"]()
                results["checks"][name] = {
                    "healthy": is_healthy,
                    "critical": check["critical"]
                }

                if not is_healthy and check["critical"]:
                    results["healthy"] = False
            except Exception as e:
                results["checks"][name] = {
                    "healthy": False,
                    "critical": check["critical"],
                    "error": str(e)
                }

                if check["critical"]:
                    results["healthy"] = False

        return results
