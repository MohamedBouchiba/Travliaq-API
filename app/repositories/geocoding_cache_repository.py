"""MongoDB repository for geocoding cache.

This repository caches geocoding results to minimize API costs and improve performance.
Geoapify and Google Places API calls are expensive, so we cache results for 90 days.
"""

from __future__ import annotations
import hashlib
import logging
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument

logger = logging.getLogger(__name__)


class GeocodingCacheRepository:
    """Repository for geocoding cache collection in MongoDB."""

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def get(self, title_en: str, destination: str) -> Optional[dict]:
        """
        Get cached geocoding result.

        Args:
            title_en: Activity title in English
            destination: City/destination name

        Returns:
            Dict with {"coordinates": {...}, "source": "..."} or None if not cached
        """
        cache_key = self._generate_cache_key(title_en, destination)

        # Find and update last_used atomically
        result = await self.collection.find_one_and_update(
            {"cache_key": cache_key},
            {
                "$set": {"last_used": datetime.utcnow()},
                "$inc": {"use_count": 1}
            },
            return_document=ReturnDocument.AFTER
        )

        if result:
            logger.debug(
                f"Geocoding cache HIT: {title_en[:50]} in {destination} "
                f"(used {result.get('use_count', 0)} times)"
            )
            return result.get("result")

        logger.debug(f"Geocoding cache MISS: {title_en[:50]} in {destination}")
        return None

    async def set(
        self,
        title_en: str,
        destination: str,
        coordinates: dict,
        source: str
    ):
        """
        Cache geocoding result.

        Args:
            title_en: Activity title in English
            destination: City/destination name
            coordinates: {"lat": float, "lon": float}
            source: Geocoding provider (e.g., "geoapify", "google_places")
        """
        cache_key = self._generate_cache_key(title_en, destination)

        await self.collection.update_one(
            {"cache_key": cache_key},
            {
                "$set": {
                    "cache_key": cache_key,
                    "input": {
                        "title_en": title_en,
                        "destination": destination
                    },
                    "result": {
                        "coordinates": coordinates,
                        "source": source
                    },
                    "created_at": datetime.utcnow(),
                    "last_used": datetime.utcnow(),
                    "use_count": 1
                }
            },
            upsert=True
        )

        logger.info(
            f"Geocoding cached: {title_en[:50]} in {destination} "
            f"→ ({coordinates['lat']:.4f}, {coordinates['lon']:.4f}) via {source}"
        )

    async def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache size, hit rate, most used entries, etc.
        """
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_entries": {"$sum": 1},
                    "total_uses": {"$sum": "$use_count"},
                    "avg_uses": {"$avg": "$use_count"}
                }
            }
        ]

        result = await self.collection.aggregate(pipeline).to_list(length=1)

        if not result:
            return {
                "total_entries": 0,
                "total_uses": 0,
                "avg_uses": 0
            }

        return result[0]

    async def get_most_used(self, limit: int = 10) -> list[dict]:
        """
        Get most frequently used cache entries.

        Args:
            limit: Number of entries to return

        Returns:
            List of cache entries sorted by use_count
        """
        cursor = self.collection.find().sort("use_count", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def clear_old_entries(self, days: int = 90):
        """
        Clear cache entries older than specified days.

        Args:
            days: Age threshold in days
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.collection.delete_many({
            "last_used": {"$lt": cutoff_date}
        })

        logger.info(f"Cleared {result.deleted_count} old geocoding cache entries (>{days} days)")

        return result.deleted_count

    async def create_indexes(self):
        """Create MongoDB indexes for geocoding cache collection."""
        logger.info("Creating indexes for geocoding_cache collection")

        # Cache key (unique)
        await self.collection.create_index("cache_key", unique=True)

        # TTL index on last_used - auto-delete after 90 days of inactivity
        # This also serves as a regular index for queries
        # Using explicit name to avoid conflict with existing indexes
        await self.collection.create_index(
            "last_used",
            name="last_used_ttl",  # Explicit name to avoid conflicts
            expireAfterSeconds=90 * 24 * 60 * 60  # 90 days
        )

        # Use count (for analytics)
        await self.collection.create_index("use_count")

        logger.info("Geocoding cache indexes created successfully")

    @staticmethod
    def _generate_cache_key(title_en: str, destination: str) -> str:
        """
        Generate deterministic cache key from title and destination.

        Args:
            title_en: Activity title in English (lowercased)
            destination: City/destination name (lowercased)

        Returns:
            MD5 hash as cache key
        """
        normalized = f"{title_en.lower().strip()}:{destination.lower().strip()}"
        return hashlib.md5(normalized.encode()).hexdigest()
