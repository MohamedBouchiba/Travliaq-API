"""Simple in-memory cache with TTL (Time To Live)."""

import time
import hashlib
import json
from typing import Callable, Any, Optional
from functools import wraps


class CacheEntry:
    """Cache entry with expiration time."""

    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expires_at = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() > self.expires_at


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None

        if entry.is_expired():
            del self._cache[key]
            return None

        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int):
        """Set value in cache with TTL."""
        self._cache[key] = CacheEntry(value, ttl_seconds)

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()

    def cleanup_expired(self):
        """Remove all expired entries."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]


# Global cache instance
_global_cache = SimpleCache()


def cache_result(ttl_seconds: int):
    """Decorator to cache function results with TTL.

    Args:
        ttl_seconds: Time to live in seconds

    Example:
        @cache_result(ttl_seconds=300)  # Cache for 5 minutes
        def expensive_function(arg1, arg2):
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = _create_cache_key(func.__name__, args, kwargs)

            # Try to get from cache
            cached_value = _global_cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)
            _global_cache.set(cache_key, result, ttl_seconds)

            return result

        return wrapper
    return decorator


def _create_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Create a unique cache key from function name and arguments.

    Args:
        func_name: Name of the function
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Unique cache key as string
    """
    # Skip 'self' argument for instance methods
    args_to_hash = args[1:] if args and hasattr(args[0], '__dict__') else args

    # Create a serializable representation
    key_data = {
        'func': func_name,
        'args': args_to_hash,
        'kwargs': kwargs
    }

    # Serialize to JSON and hash
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()

    return f"{func_name}:{key_hash}"


def clear_cache():
    """Clear all cached data."""
    _global_cache.clear()


def cleanup_expired_cache():
    """Remove expired cache entries."""
    _global_cache.cleanup_expired()
