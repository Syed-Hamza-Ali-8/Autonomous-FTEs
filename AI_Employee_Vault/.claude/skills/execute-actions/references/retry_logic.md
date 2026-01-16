# Retry Logic Strategy

## Overview

This document describes the retry logic strategy used for executing external actions, particularly email sending via the MCP server.

## Retry Strategy: Exponential Backoff

### Why Exponential Backoff?

Exponential backoff is a standard error handling strategy that:
1. **Reduces server load**: Gives the server time to recover
2. **Avoids thundering herd**: Prevents all clients from retrying simultaneously
3. **Increases success rate**: Transient errors often resolve within seconds
4. **Respects rate limits**: Allows rate limit windows to reset

### Configuration

```python
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]  # seconds

# Total retry time: 2s + 4s + 8s = 14 seconds
# Total attempts: 1 initial + 3 retries = 4 attempts
```

### Implementation

```python
import time
import logging

def execute_with_retry(action_func, max_retries=3, retry_delays=[2, 4, 8]):
    """
    Execute action with exponential backoff retry logic.

    Args:
        action_func: Function to execute
        max_retries: Maximum number of retry attempts
        retry_delays: List of delays (in seconds) between retries

    Returns:
        Result dict with success status and details
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            result = action_func()

            return {
                "success": True,
                "result": result,
                "retry_count": attempt
            }

        except Exception as e:
            last_error = e
            logging.warning(f"Attempt {attempt + 1} failed: {e}")

            # Don't retry on last attempt
            if attempt < max_retries:
                delay = retry_delays[attempt]
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error(f"Max retries ({max_retries}) reached")

    return {
        "success": False,
        "error": str(last_error),
        "retry_count": max_retries + 1
    }
```

## Retryable vs Non-Retryable Errors

### Retryable Errors (Transient)

These errors are likely to resolve on retry:

1. **Network Errors**
   - `ETIMEDOUT`: Connection timeout
   - `ECONNREFUSED`: Connection refused
   - `ECONNRESET`: Connection reset
   - `ENOTFOUND`: DNS lookup failed
   - `EPIPE`: Broken pipe

2. **Server Errors**
   - `500 Internal Server Error`: Temporary server issue
   - `502 Bad Gateway`: Upstream server issue
   - `503 Service Unavailable`: Server overloaded
   - `504 Gateway Timeout`: Upstream timeout

3. **SMTP Errors**
   - `421`: Service not available (temporary)
   - `450`: Mailbox unavailable (temporary)
   - `451`: Local error in processing

### Non-Retryable Errors (Permanent)

These errors will NOT resolve on retry:

1. **Authentication Errors**
   - `401 Unauthorized`: Invalid credentials
   - `403 Forbidden`: Access denied
   - `535 SMTP Auth Failed`: Invalid SMTP credentials

2. **Validation Errors**
   - `400 Bad Request`: Invalid request format
   - `422 Unprocessable Entity`: Validation failed
   - `550 SMTP Recipient Rejected`: Invalid email address

3. **Resource Errors**
   - `404 Not Found`: Resource doesn't exist
   - `410 Gone`: Resource permanently deleted
   - `552 SMTP Message Size Exceeded`: Email too large

4. **Rate Limit Errors**
   - `429 Too Many Requests`: Rate limit exceeded
   - Note: Should wait for rate limit window to reset, not retry immediately

## Error Classification

```python
def is_retryable_error(error):
    """
    Determine if an error is retryable.

    Args:
        error: Exception or error dict

    Returns:
        bool: True if error is retryable
    """
    # Network errors (always retryable)
    network_errors = [
        'ETIMEDOUT', 'ECONNREFUSED', 'ECONNRESET',
        'ENOTFOUND', 'EPIPE', 'EHOSTUNREACH'
    ]

    # HTTP status codes (retryable)
    retryable_status_codes = [500, 502, 503, 504]

    # SMTP codes (retryable)
    retryable_smtp_codes = [421, 450, 451]

    # Check error type
    if hasattr(error, 'code'):
        if error.code in network_errors:
            return True

    if hasattr(error, 'status_code'):
        if error.status_code in retryable_status_codes:
            return True

    if hasattr(error, 'smtp_code'):
        if error.smtp_code in retryable_smtp_codes:
            return True

    # Default: not retryable
    return False
```

## Retry with Jitter

For distributed systems, add random jitter to prevent synchronized retries:

```python
import random

def execute_with_retry_and_jitter(action_func, max_retries=3, base_delay=2):
    """
    Execute action with exponential backoff + jitter.

    Jitter prevents thundering herd problem in distributed systems.
    """
    for attempt in range(max_retries + 1):
        try:
            return action_func()
        except Exception as e:
            if attempt < max_retries and is_retryable_error(e):
                # Exponential backoff: 2^attempt * base_delay
                delay = (2 ** attempt) * base_delay

                # Add jitter: ±25% of delay
                jitter = delay * 0.25 * (random.random() * 2 - 1)
                actual_delay = delay + jitter

                time.sleep(actual_delay)
            else:
                raise
```

## Circuit Breaker Pattern

For repeated failures, implement circuit breaker to prevent cascading failures:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, action_func):
        if self.state == "OPEN":
            # Check if timeout has passed
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = action_func()

            # Success: reset failure count
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
            self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            # Open circuit if threshold reached
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"

            raise
```

## Retry Budget

Limit total retry attempts across all actions to prevent resource exhaustion:

```python
class RetryBudget:
    def __init__(self, max_retries_per_minute=30):
        self.max_retries_per_minute = max_retries_per_minute
        self.retry_count = 0
        self.window_start = time.time()

    def can_retry(self):
        # Reset window if 1 minute has passed
        if time.time() - self.window_start > 60:
            self.retry_count = 0
            self.window_start = time.time()

        return self.retry_count < self.max_retries_per_minute

    def record_retry(self):
        self.retry_count += 1
```

## Monitoring and Alerting

### Metrics to Track

1. **Retry Rate**: Percentage of actions requiring retry
2. **Success Rate**: Percentage of actions succeeding (including retries)
3. **Average Retry Count**: Average number of retries per action
4. **Max Retry Time**: Maximum time spent retrying

### Alert Thresholds

- **High Retry Rate**: > 20% of actions require retry
- **Low Success Rate**: < 80% of actions succeed after retries
- **Circuit Breaker Open**: Circuit breaker has opened (repeated failures)

## Best Practices

1. **Log all retry attempts**: Include attempt number, delay, error
2. **Use exponential backoff**: Don't retry immediately
3. **Add jitter for distributed systems**: Prevent synchronized retries
4. **Classify errors correctly**: Don't retry permanent failures
5. **Implement circuit breaker**: Prevent cascading failures
6. **Set retry budget**: Limit total retries to prevent resource exhaustion
7. **Monitor retry metrics**: Track retry rate and success rate
8. **Fail fast for non-retryable errors**: Don't waste time on permanent failures

## Example: Email Sending with Retry

```python
def send_email_with_retry(to, subject, body):
    """Send email with retry logic."""

    def send():
        return email_sender.send_email(to, subject, body)

    result = execute_with_retry(
        action_func=send,
        max_retries=3,
        retry_delays=[2, 4, 8]
    )

    if result["success"]:
        logging.info(f"Email sent after {result['retry_count']} retries")
        return result["result"]
    else:
        logging.error(f"Email failed after {result['retry_count']} attempts: {result['error']}")
        raise Exception(result["error"])
```

## References

- [Exponential Backoff](https://en.wikipedia.org/wiki/Exponential_backoff)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Google Cloud Retry Strategy](https://cloud.google.com/iot/docs/how-tos/exponential-backoff)
- [AWS Retry Strategy](https://docs.aws.amazon.com/general/latest/gr/api-retries.html)
