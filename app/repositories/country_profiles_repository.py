"""Repository for country profiles data access."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorCollection

logger = logging.getLogger(__name__)


class CountryProfilesRepository:
    """
    Repository for accessing country profile data from MongoDB.

    Includes in-memory caching for performance since country profiles
    are relatively static data (updated at most daily).
    """

    # Cache TTL: 24 hours in seconds
    CACHE_TTL = 86400

    def __init__(self, collection: "AsyncIOMotorCollection"):
        """
        Initialize repository with MongoDB collection.

        Args:
            collection: Motor async collection for country_profiles
        """
        self.collection = collection
        self._cache: Optional[list[dict]] = None
        self._cache_time: Optional[float] = None

    async def create_indexes(self) -> None:
        """Create indexes for efficient querying."""
        await self.collection.create_index("country_code", unique=True)
        await self.collection.create_index("region")
        await self.collection.create_index("trending_score")
        logger.info("Country profiles indexes created")

    async def preload_profiles(self) -> int:
        """
        Preload all profiles into memory at startup for instant access.

        Call this method in startup_event() to eliminate cold-start latency.

        Returns:
            Number of profiles loaded
        """
        profiles = await self.collection.find({}).to_list(length=200)
        self._cache = profiles
        self._cache_time = time.time()
        count = len(profiles)
        logger.info(f"Preloaded {count} country profiles into memory")
        return count

    async def get_all_profiles(self, use_cache: bool = True) -> list[dict]:
        """
        Get all country profiles with optional in-memory caching.

        Args:
            use_cache: Whether to use in-memory cache (default: True)

        Returns:
            List of country profile documents
        """
        # Check cache validity
        if use_cache and self._cache is not None and self._cache_time is not None:
            if (time.time() - self._cache_time) < self.CACHE_TTL:
                logger.debug(f"Cache HIT: {len(self._cache)} country profiles")
                return self._cache

        # Fetch from MongoDB
        cursor = self.collection.find({})
        profiles = await cursor.to_list(length=200)

        # Update cache
        self._cache = profiles
        self._cache_time = time.time()

        logger.info(f"Loaded {len(profiles)} country profiles from MongoDB")
        return profiles

    async def get_by_country_code(self, code: str) -> Optional[dict]:
        """
        Get a single country profile by ISO 2-letter code.

        Args:
            code: ISO 2-letter country code (e.g., "JP", "FR")

        Returns:
            Country profile document or None if not found
        """
        return await self.collection.find_one({"country_code": code.upper()})

    async def get_by_region(self, region: str) -> list[dict]:
        """
        Get all country profiles in a specific region.

        Args:
            region: Region name (e.g., "Europe", "Asia", "Americas")

        Returns:
            List of country profiles in the region
        """
        cursor = self.collection.find({"region": region})
        return await cursor.to_list(length=100)

    async def update_trending_scores(self, trending_data: dict[str, int]) -> int:
        """
        Bulk update trending scores for countries.

        Args:
            trending_data: Dict mapping country_code to trending score (0-100)

        Returns:
            Number of documents updated
        """
        updated = 0
        for code, score in trending_data.items():
            result = await self.collection.update_one(
                {"country_code": code.upper()},
                {"$set": {"trending_score": score}}
            )
            if result.modified_count > 0:
                updated += 1

        # Invalidate cache after updates
        self._cache = None
        self._cache_time = None

        logger.info(f"Updated trending scores for {updated} countries")
        return updated

    async def upsert_profile(self, profile: dict) -> bool:
        """
        Insert or update a country profile.

        Args:
            profile: Country profile document (must include country_code)

        Returns:
            True if document was inserted/updated
        """
        if "country_code" not in profile:
            raise ValueError("Profile must include country_code")

        result = await self.collection.update_one(
            {"country_code": profile["country_code"].upper()},
            {"$set": profile},
            upsert=True
        )

        # Invalidate cache after upsert
        self._cache = None
        self._cache_time = None

        return result.upserted_id is not None or result.modified_count > 0

    async def bulk_upsert_profiles(self, profiles: list[dict]) -> int:
        """
        Bulk insert or update multiple country profiles.

        Args:
            profiles: List of country profile documents

        Returns:
            Number of documents upserted/updated
        """
        from pymongo import UpdateOne

        operations = [
            UpdateOne(
                {"country_code": p["country_code"].upper()},
                {"$set": p},
                upsert=True
            )
            for p in profiles
            if "country_code" in p
        ]

        if not operations:
            return 0

        result = await self.collection.bulk_write(operations)

        # Invalidate cache after bulk update
        self._cache = None
        self._cache_time = None

        total = result.upserted_count + result.modified_count
        logger.info(f"Bulk upserted {total} country profiles")
        return total

    async def get_count(self) -> int:
        """Get total number of country profiles."""
        return await self.collection.count_documents({})

    def invalidate_cache(self) -> None:
        """Manually invalidate the in-memory cache."""
        self._cache = None
        self._cache_time = None
        logger.debug("Country profiles cache invalidated")
