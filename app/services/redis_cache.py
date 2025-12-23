"""Redis cache service using Upstash Redis."""

from __future__ import annotations
import json
import hashlib
import logging
from typing import Optional, Any
from upstash_redis import Redis

logger = logging.getLogger(__name__)


class RedisCache:
    """Service for caching data in Upstash Redis."""

    def __init__(self, url: str, token: str):
        """
        Initialize Redis cache.

        Args:
            url: Upstash Redis REST URL
            token: Upstash Redis REST token
        """
        self._redis = Redis(url=url, token=token)
        logger.info("Redis cache initialized")

    def _generate_key(self, prefix: str, params: dict) -> str:
        """
        Generate a unique cache key based on prefix and parameters.

        Args:
            prefix: Cache key prefix (e.g., "flight_search", "calendar_prices")
            params: Dictionary of parameters to hash

        Returns:
            Unique cache key string
        """
        # Sort params to ensure consistent key generation
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{prefix}:{param_hash}"

    def get(self, prefix: str, params: dict) -> Optional[Any]:
        """
        Get cached data from Redis.

        Args:
            prefix: Cache key prefix
            params: Parameters used to generate cache key

        Returns:
            Cached data if found, None otherwise
        """
        try:
            key = self._generate_key(prefix, params)
            cached = self._redis.get(key)

            if cached:
                logger.info(f"Cache HIT for key: {key}")
                # Upstash returns string, parse JSON
                return json.loads(cached) if isinstance(cached, str) else cached
            else:
                logger.info(f"Cache MISS for key: {key}")
                return None

        except Exception as e:
            logger.error(f"Error getting cache: {e}", exc_info=True)
            return None

    def set(
        self,
        prefix: str,
        params: dict,
        data: Any,
        ttl_seconds: int = 86400  # 24 hours default
    ) -> bool:
        """
        Set data in Redis cache with TTL.

        Args:
            prefix: Cache key prefix
            params: Parameters used to generate cache key
            data: Data to cache (will be JSON serialized)
            ttl_seconds: Time to live in seconds (default: 86400 = 24 hours)

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._generate_key(prefix, params)

            # Serialize data to JSON
            serialized = json.dumps(data)

            # Set with expiration
            self._redis.setex(key, ttl_seconds, serialized)

            logger.info(f"Cache SET for key: {key} (TTL: {ttl_seconds}s)")
            return True

        except Exception as e:
            logger.error(f"Error setting cache: {e}", exc_info=True)
            return False

    def delete(self, prefix: str, params: dict) -> bool:
        """
        Delete cached data from Redis.

        Args:
            prefix: Cache key prefix
            params: Parameters used to generate cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._generate_key(prefix, params)
            self._redis.delete(key)
            logger.info(f"Cache DELETE for key: {key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting cache: {e}", exc_info=True)
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "flight_search:*")

        Returns:
            Number of keys deleted
        """
        try:
            # Get all keys matching pattern
            keys = self._redis.keys(pattern)

            if not keys:
                logger.info(f"No keys found for pattern: {pattern}")
                return 0

            # Delete all matching keys
            deleted = 0
            for key in keys:
                self._redis.delete(key)
                deleted += 1

            logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
            return deleted

        except Exception as e:
            logger.error(f"Error clearing pattern {pattern}: {e}", exc_info=True)
            return 0
