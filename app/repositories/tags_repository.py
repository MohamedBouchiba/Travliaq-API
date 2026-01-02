"""MongoDB repository for tags."""

from __future__ import annotations
import logging
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection

logger = logging.getLogger(__name__)


class TagsRepository:
    """Repository for tags collection in MongoDB."""

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def upsert_tag(self, tag_id: int, tag_data: dict):
        """
        Upsert tag.

        Args:
            tag_id: Viator tag ID (unique identifier)
            tag_data: Tag data to store (must include metadata.last_synced)
        """
        result = await self.collection.update_one(
            {"tag_id": tag_id},
            {"$set": tag_data},
            upsert=True
        )

        if result.upserted_id:
            logger.debug(f"Inserted new tag: {tag_id}")
        else:
            logger.debug(f"Updated existing tag: {tag_id}")

    async def get_tag(self, tag_id: int) -> Optional[dict]:
        """Get tag by ID."""
        return await self.collection.find_one({"tag_id": tag_id})

    async def get_tag_by_name(self, tag_name: str, language: str = "en") -> Optional[dict]:
        """
        Get tag by name (case insensitive).

        Args:
            tag_name: Name of the tag
            language: Language code

        Returns:
            Tag document or None
        """
        return await self.collection.find_one({
            f"all_names.{language}": {"$regex": f"^{tag_name}$", "$options": "i"}
        })

    async def search_tags(
        self,
        search_text: Optional[str] = None,
        parent_tag_id: Optional[int] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        Search tags.

        Args:
            search_text: Text to search in tag names
            parent_tag_id: Filter by parent tag ID (None for root tags)
            limit: Maximum number of results

        Returns:
            List of tag documents
        """
        query = {}

        if parent_tag_id is not None:
            query["parent_tag_id"] = parent_tag_id
        elif parent_tag_id is None and search_text is None:
            # Get root tags only
            query["parent_tag_id"] = None

        if search_text:
            query["$text"] = {"$search": search_text}

        cursor = self.collection.find(query).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_tags_by_category_keyword(
        self,
        keyword: str,
        language: str = "en"
    ) -> List[dict]:
        """
        Find tags matching a category keyword (e.g., 'food', 'museum').

        Args:
            keyword: Keyword to search for
            language: Language code

        Returns:
            List of matching tags
        """
        # Case-insensitive partial match
        regex_pattern = f".*{keyword}.*"
        cursor = self.collection.find({
            f"all_names.{language}": {"$regex": regex_pattern, "$options": "i"}
        })
        return await cursor.to_list(length=50)

    async def get_all_root_tags(self) -> List[dict]:
        """Get all root-level tags (tags with no parent)."""
        cursor = self.collection.find({"parent_tag_id": None})
        return await cursor.to_list(length=None)

    async def create_indexes(self):
        """Create MongoDB indexes for tags collection."""
        logger.info("Creating indexes for tags collection")

        # Tag ID (unique)
        await self.collection.create_index("tag_id", unique=True)

        # Parent tag ID
        await self.collection.create_index("parent_tag_id")

        # Text search on all language names
        await self.collection.create_index([("tag_name", "text")])

        # Last synced
        await self.collection.create_index("metadata.last_synced")

        logger.info("Tags indexes created successfully")
