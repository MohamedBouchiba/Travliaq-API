"""MongoDB repository for activities."""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection

logger = logging.getLogger(__name__)


class ActivitiesRepository:
    """Repository for activities collection in MongoDB."""

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def upsert_activity(self, product_code: str, activity_data: dict):
        """
        Upsert activity with last_updated tracking.

        Args:
            product_code: Viator product code (unique identifier)
            activity_data: Activity data to store
        """
        result = await self.collection.update_one(
            {"product_code": product_code},
            {
                "$set": {
                    **activity_data,
                    "metadata.last_updated": datetime.utcnow()
                },
                "$setOnInsert": {
                    "metadata.first_seen": datetime.utcnow(),
                    "metadata.fetch_count": 0
                },
                "$inc": {
                    "metadata.fetch_count": 1
                }
            },
            upsert=True
        )

        if result.upserted_id:
            logger.info(f"Inserted new activity: {product_code}")
        else:
            logger.info(f"Updated existing activity: {product_code}")

    async def get_activity(self, product_code: str) -> Optional[dict]:
        """Get activity by product code."""
        return await self.collection.find_one({"product_code": product_code})

    async def search_activities(
        self,
        destination_id: Optional[str] = None,
        categories: Optional[list[str]] = None,
        limit: int = 20
    ) -> list[dict]:
        """Search activities in MongoDB (fallback when Viator API fails)."""
        query = {}

        if destination_id:
            query["destination.id"] = destination_id

        if categories:
            query["categories"] = {"$in": categories}

        cursor = self.collection.find(query).limit(limit)
        return await cursor.to_list(length=limit)

    async def create_indexes(self):
        """Create MongoDB indexes for activities collection."""
        logger.info("Creating indexes for activities collection")

        # Product code (unique)
        await self.collection.create_index("product_code", unique=True)

        # Destination ID
        await self.collection.create_index("destination.id")

        # Categories
        await self.collection.create_index("categories")

        # Pricing
        await self.collection.create_index("pricing.from_price")

        # Rating
        await self.collection.create_index([("rating.average", -1)])

        # Geospatial
        await self.collection.create_index([("location", "2dsphere")])

        # Last updated
        await self.collection.create_index("metadata.last_updated")

        logger.info("Activities indexes created successfully")
