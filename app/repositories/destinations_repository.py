"""MongoDB repository for destinations."""

from __future__ import annotations
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection

logger = logging.getLogger(__name__)


class DestinationsRepository:
    """Repository for destinations collection in MongoDB."""

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def upsert_destination(self, destination_id: str, destination_data: dict):
        """
        Upsert destination.

        Args:
            destination_id: Viator destination ID (unique identifier)
            destination_data: Destination data to store (must include metadata.last_synced)
        """
        result = await self.collection.update_one(
            {"destination_id": destination_id},
            {"$set": destination_data},
            upsert=True
        )

        if result.upserted_id:
            logger.info(f"Inserted new destination: {destination_id}")
        else:
            logger.info(f"Updated existing destination: {destination_id}")

    async def get_destination(self, destination_id: str) -> Optional[dict]:
        """Get destination by ID."""
        return await self.collection.find_one({"destination_id": destination_id})

    async def search_destinations(
        self,
        search_text: Optional[str] = None,
        country_code: Optional[str] = None,
        limit: int = 20
    ) -> list[dict]:
        """Search destinations."""
        query = {}

        if country_code:
            query["country_code"] = country_code.upper()

        if search_text:
            query["$text"] = {"$search": search_text}

        cursor = self.collection.find(query).limit(limit)
        return await cursor.to_list(length=limit)

    async def create_indexes(self):
        """Create MongoDB indexes for destinations collection."""
        logger.info("Creating indexes for destinations collection")

        # Destination ID (unique)
        await self.collection.create_index("destination_id", unique=True)

        # Slug
        await self.collection.create_index("slug")

        # Country code
        await self.collection.create_index("country_code")

        # Geospatial
        await self.collection.create_index([("location", "2dsphere")])

        # Text search on name
        await self.collection.create_index([("name", "text")])

        logger.info("Destinations indexes created successfully")
