"""Viator Taxonomy API service."""

from __future__ import annotations
import logging
from typing import List, Dict, Any

from app.services.viator.client import ViatorClient

logger = logging.getLogger(__name__)


class ViatorTaxonomyService:
    """Service for Viator taxonomy API endpoints."""

    def __init__(self, client: ViatorClient):
        """
        Initialize taxonomy service.

        Args:
            client: Viator API client
        """
        self.client = client

    async def get_all_tags(self, language: str = "en") -> List[Dict[str, Any]]:
        """
        Get all tags from Viator API.

        This endpoint returns the complete tag taxonomy from Viator.
        Tags should be cached and refreshed weekly as per Viator docs.

        Args:
            language: Language code (e.g., 'en', 'fr', 'es')

        Returns:
            List of tag dictionaries with structure:
            {
                "tagId": 19927,
                "tagName": "Food & Drink",
                "parentTagId": null,
                "allNamesByLocale": {
                    "en": "Food & Drink",
                    "fr": "Gastronomie",
                    "es": "Gastronomía"
                }
            }

        Raises:
            Exception: If API call fails
        """
        logger.info(f"Fetching all tags from Viator API (language: {language})")

        try:
            response = await self.client.get(
                "/products/tags",
                params={},
                language=language
            )

            tags = response.get("tags", [])
            logger.info(f"Retrieved {len(tags)} tags from Viator")

            return tags

        except Exception as e:
            logger.error(f"Failed to fetch tags from Viator: {e}", exc_info=True)
            raise
