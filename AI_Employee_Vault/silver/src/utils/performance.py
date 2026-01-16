#!/usr/bin/env python3
"""
Performance Optimization Utilities

Provides performance optimization tools for Silver tier:
- Caching mechanisms
- Batch processing
- Connection pooling
- Memory optimization
- I/O optimization
"""

import time
import hashlib
from typing import Any, Callable, Dict, Optional, List
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
import pickle
import threading


class LRUCache:
    """
    Least Recently Used (LRU) cache implementation.

    Thread-safe cache with TTL support.
    """

    def __init__(self, max_size: int = 100, ttl: int = 300):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items in cache
            ttl: Time to live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_order: List[str] = []
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self.lock:
            if key not in self.cache:
                return None

            entry = self.cache[key]

            # Check if expired
            age = (datetime.now() - entry["timestamp"]).total_seconds()
            if age > self.ttl:
                del self.cache[key]
                self.access_order.remove(key)
                return None

            # Update access order
            self.access_order.remove(key)
            self.access_order.append(key)

            return entry["value"]

    def set(self, key: str, value: Any):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            # Remove oldest if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]

            # Add/update entry
            self.cache[key] = {
                "value": value,
                "timestamp": datetime.now()
            }

            # Update access order
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()

    def size(self) -> int:
        """Get current cache size."""
        with self.lock:
            return len(self.cache)


class DiskCache:
    """
    Disk-based cache for larger data.

    Uses pickle for serialization.
    """

    def __init__(self, cache_dir: Path, ttl: int = 3600):
        """
        Initialize disk cache.

        Args:
            cache_dir: Directory for cache files
            ttl: Time to live in seconds
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from disk cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            # Check if expired
            age = time.time() - cache_path.stat().st_mtime
            if age > self.ttl:
                cache_path.unlink()
                return None

            # Load from disk
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return None

    def set(self, key: str, value: Any):
        """
        Set value in disk cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
        except Exception:
            pass

    def clear(self):
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                cache_file.unlink()
            except Exception:
                pass


def memoize(ttl: int = 300):
    """
    Decorator to memoize function results.

    Args:
        ttl: Time to live in seconds

    Returns:
        Decorated function
    """
    cache = LRUCache(max_size=100, ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = "|".join(key_parts)

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Compute and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        return wrapper
    return decorator


class BatchProcessor:
    """
    Batch processor for efficient bulk operations.
    """

    def __init__(self, batch_size: int = 10, flush_interval: int = 5):
        """
        Initialize batch processor.

        Args:
            batch_size: Number of items to batch before processing
            flush_interval: Seconds to wait before auto-flushing
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batch: List[Any] = []
        self.last_flush = time.time()
        self.lock = threading.Lock()

    def add(self, item: Any, process_func: Callable[[List[Any]], None]):
        """
        Add item to batch.

        Args:
            item: Item to add
            process_func: Function to process batch
        """
        with self.lock:
            self.batch.append(item)

            # Check if should flush
            should_flush = (
                len(self.batch) >= self.batch_size or
                time.time() - self.last_flush >= self.flush_interval
            )

            if should_flush:
                self._flush(process_func)

    def _flush(self, process_func: Callable[[List[Any]], None]):
        """Flush batch and process items."""
        if not self.batch:
            return

        try:
            process_func(self.batch)
        finally:
            self.batch.clear()
            self.last_flush = time.time()

    def flush(self, process_func: Callable[[List[Any]], None]):
        """Manually flush batch."""
        with self.lock:
            self._flush(process_func)


class ConnectionPool:
    """
    Connection pool for reusing expensive connections.
    """

    def __init__(
        self,
        create_func: Callable[[], Any],
        max_size: int = 5,
        timeout: int = 30
    ):
        """
        Initialize connection pool.

        Args:
            create_func: Function to create new connection
            max_size: Maximum pool size
            timeout: Connection timeout in seconds
        """
        self.create_func = create_func
        self.max_size = max_size
        self.timeout = timeout
        self.pool: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    def acquire(self) -> Any:
        """
        Acquire connection from pool.

        Returns:
            Connection object
        """
        with self.lock:
            # Try to reuse existing connection
            for i, conn_info in enumerate(self.pool):
                age = time.time() - conn_info["timestamp"]
                if age < self.timeout:
                    # Remove from pool and return
                    self.pool.pop(i)
                    return conn_info["connection"]

            # Create new connection if pool not at max
            if len(self.pool) < self.max_size:
                return self.create_func()

            # Wait for connection to become available
            # (simplified - in production, use proper waiting mechanism)
            return self.create_func()

    def release(self, connection: Any):
        """
        Release connection back to pool.

        Args:
            connection: Connection to release
        """
        with self.lock:
            if len(self.pool) < self.max_size:
                self.pool.append({
                    "connection": connection,
                    "timestamp": time.time()
                })

    def close_all(self):
        """Close all connections in pool."""
        with self.lock:
            for conn_info in self.pool:
                try:
                    conn = conn_info["connection"]
                    if hasattr(conn, 'close'):
                        conn.close()
                except Exception:
                    pass
            self.pool.clear()


class RateLimiter:
    """
    Rate limiter to prevent API throttling.
    """

    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: List[float] = []
        self.lock = threading.Lock()

    def acquire(self):
        """
        Acquire permission to make a call.

        Blocks if rate limit exceeded.
        """
        with self.lock:
            now = time.time()

            # Remove old calls outside time window
            self.calls = [t for t in self.calls if now - t < self.time_window]

            # Check if at limit
            if len(self.calls) >= self.max_calls:
                # Calculate wait time
                oldest_call = self.calls[0]
                wait_time = self.time_window - (now - oldest_call)
                if wait_time > 0:
                    time.sleep(wait_time)
                    # Retry after waiting
                    return self.acquire()

            # Record this call
            self.calls.append(now)


class LazyLoader:
    """
    Lazy loader for expensive resources.
    """

    def __init__(self, load_func: Callable[[], Any]):
        """
        Initialize lazy loader.

        Args:
            load_func: Function to load resource
        """
        self.load_func = load_func
        self._resource = None
        self._loaded = False
        self.lock = threading.Lock()

    def get(self) -> Any:
        """
        Get resource (load if not already loaded).

        Returns:
            Loaded resource
        """
        if not self._loaded:
            with self.lock:
                if not self._loaded:
                    self._resource = self.load_func()
                    self._loaded = True
        return self._resource

    def reset(self):
        """Reset loader (force reload on next get)."""
        with self.lock:
            self._resource = None
            self._loaded = False


class PerformanceMonitor:
    """
    Monitor for tracking performance metrics.
    """

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: Dict[str, List[float]] = {}
        self.lock = threading.Lock()

    def record(self, metric_name: str, value: float):
        """
        Record a metric value.

        Args:
            metric_name: Name of metric
            value: Metric value
        """
        with self.lock:
            if metric_name not in self.metrics:
                self.metrics[metric_name] = []
            self.metrics[metric_name].append(value)

            # Keep only last 1000 values
            if len(self.metrics[metric_name]) > 1000:
                self.metrics[metric_name] = self.metrics[metric_name][-1000:]

    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """
        Get statistics for a metric.

        Args:
            metric_name: Name of metric

        Returns:
            Dictionary with min, max, avg, p95, p99
        """
        with self.lock:
            if metric_name not in self.metrics or not self.metrics[metric_name]:
                return {}

            values = sorted(self.metrics[metric_name])
            count = len(values)

            return {
                "min": values[0],
                "max": values[-1],
                "avg": sum(values) / count,
                "p50": values[int(count * 0.5)],
                "p95": values[int(count * 0.95)],
                "p99": values[int(count * 0.99)],
                "count": count
            }

    def time_function(self, func_name: str):
        """
        Decorator to time function execution.

        Args:
            func_name: Name for metric

        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration = time.time() - start
                    self.record(func_name, duration)
            return wrapper
        return decorator
