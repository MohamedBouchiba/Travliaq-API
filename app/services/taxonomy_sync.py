"""Service for synchronizing Viator tags to MongoDB."""

from __future__ import annotations
import logging
from typing import Dict, Any, List
from datetime import datetime

from app.services.viator.taxonomy import ViatorTaxonomyService
from app.repositories.tags_repository import TagsRepository

logger = logging.getLogger(__name__)


class TaxonomySyncService:
    """Service for syncing Viator tags to MongoDB."""

    def __init__(
        self,
        viator_taxonomy: ViatorTaxonomyService,
        tags_repo: TagsRepository
    ):
        """
        Initialize sync service.

        Args:
            viator_taxonomy: Viator taxonomy API service
            tags_repo: MongoDB tags repository
        """
        self.viator = viator_taxonomy
        self.repo = tags_repo

    async def sync_all_tags(self, language: str = "en") -> Dict[str, Any]:
        """
        Sync all tags from Viator API to MongoDB.

        Viator recommends caching tags and refreshing weekly.

        Args:
            language: Primary language for tag names

        Returns:
            Dictionary with sync statistics:
            {
                "total_fetched": int,
                "updated": int,
                "errors": int,
                "root_tags": int,
                "child_tags": int
            }
        """
        logger.info("Starting Viator tags sync")

        stats = {
            "total_fetched": 0,
            "updated": 0,
            "errors": 0,
            "root_tags": 0,
            "child_tags": 0,
            "started_at": datetime.utcnow().isoformat()
        }

        try:
            # 1. Fetch all tags from Viator
            viator_tags = await self.viator.get_all_tags(language=language)
            stats["total_fetched"] = len(viator_tags)

            logger.info(f"Fetched {len(viator_tags)} tags from Viator")

            # 2. Process and upsert each tag
            for viator_tag in viator_tags:
                try:
                    # Transform Viator tag to our schema
                    tag_doc = self._transform_tag(viator_tag)

                    # Count root vs child tags
                    if tag_doc["parent_tag_id"] is None:
                        stats["root_tags"] += 1
                    else:
                        stats["child_tags"] += 1

                    # Upsert to MongoDB
                    await self.repo.upsert_tag(
                        tag_id=tag_doc["tag_id"],
                        tag_data=tag_doc
                    )

                    stats["updated"] += 1

                except Exception as e:
                    logger.error(
                        f"Error processing tag {viator_tag.get('tagId')}: {e}",
                        exc_info=True
                    )
                    stats["errors"] += 1

            stats["completed_at"] = datetime.utcnow().isoformat()

            logger.info(
                f"Tags sync completed: {stats['updated']} updated, "
                f"{stats['errors']} errors, "
                f"{stats['root_tags']} root tags, "
                f"{stats['child_tags']} child tags"
            )

            return stats

        except Exception as e:
            logger.error(f"Tags sync failed: {e}", exc_info=True)
            raise

    def _transform_tag(self, viator_tag: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Viator tag to our MongoDB schema.

        Args:
            viator_tag: Tag from Viator API

        Returns:
            Tag document for MongoDB
        """
        tag_id = viator_tag["tagId"]
        tag_name = viator_tag.get("tagName", "")
        parent_tag_id = viator_tag.get("parentTagId")  # None for root tags

        # Get all translations
        all_names = viator_tag.get("allNamesByLocale", {})

        # Build document
        now = datetime.utcnow()
        doc = {
            "tag_id": tag_id,
            "tag_name": tag_name,
            "parent_tag_id": parent_tag_id,
            "all_names": all_names,
            "metadata": {
                "synced_at": now,
                "last_synced": now,
                "source": "viator_api"
            }
        }

        return doc

    async def build_category_mapping(
        self,
        category_keywords: List[str],
        language: str = "en"
    ) -> Dict[str, List[int]]:
        """
        Build dynamic category to tag ID mapping.

        This replaces the hardcoded CATEGORY_TAG_MAPPING by searching
        MongoDB for tags matching each category keyword.

        Args:
            category_keywords: List of category keywords (e.g., ['food', 'museum'])
            language: Language code for searching

        Returns:
            Dictionary mapping category -> list of tag IDs
            {
                "food": [19927, 19928],
                "museum": [19929]
            }
        """
        mapping = {}

        for keyword in category_keywords:
            # Search for tags matching this keyword
            matching_tags = await self.repo.find_tags_by_category_keyword(
                keyword=keyword,
                language=language
            )

            # Extract tag IDs
            tag_ids = [tag["tag_id"] for tag in matching_tags]

            if tag_ids:
                mapping[keyword] = tag_ids
                logger.info(f"Mapped category '{keyword}' to {len(tag_ids)} tags: {tag_ids}")
            else:
                logger.warning(f"No tags found for category keyword: '{keyword}'")

        return mapping
