"""Viator Destinations API service."""

from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional

from app.services.viator.client import ViatorClient

logger = logging.getLogger(__name__)


class ViatorDestinationsService:
    """Service for Viator destinations API endpoints."""

    def __init__(self, client: ViatorClient):
        """
        Initialize destinations service.

        Args:
            client: Viator API client
        """
        self.client = client

    async def get_all_destinations(self, language: str = "en") -> List[Dict[str, Any]]:
        """
        Get all destinations from Viator API.

        This endpoint returns a complete list of all Viator destinations worldwide.
        Should be called to populate the destinations collection.

        Args:
            language: Language code (e.g., 'en', 'fr', 'es')

        Returns:
            List of destination dictionaries with structure:
            {
                "ref": "684",  # Destination ID
                "name": "Paris",
                "destinationType": "CITY",
                "timeZone": "Europe/Paris",
                "parentRef": "79",  # Parent destination (e.g., country)
                "lookupId": "paris"  # Slug/lookup identifier
            }

        Raises:
            Exception: If API call fails
        """
        logger.info(f"Fetching all destinations from Viator API (language: {language})")

        try:
            response = await self.client.get(
                "/destinations",
                params={},
                language=language
            )

            destinations = response.get("destinations", [])
            total_count = response.get("totalCount", 0)
            logger.info(f"Retrieved {len(destinations)} destinations from Viator (totalCount: {total_count})")

            return destinations

        except Exception as e:
            logger.error(f"Failed to fetch destinations from Viator: {e}", exc_info=True)
            raise

    async def search_destinations(
        self,
        search_term: str,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Search for destinations using the /search endpoint.

        This can be used as an alternative to get_all_destinations
        for finding specific destinations.

        Args:
            search_term: Search query (city name, country, etc.)
            language: Language code

        Returns:
            List of matching destinations

        Raises:
            Exception: If API call fails
        """
        logger.info(f"Searching destinations for term: {search_term}")

        try:
            response = await self.client.post(
                "/search",
                {
                    "searchTerm": search_term,
                    "searchTypes": ["DESTINATIONS"]
                },
                language=language
            )

            destinations = response.get("destinations", [])
            logger.info(f"Found {len(destinations)} destinations matching '{search_term}'")

            return destinations

        except Exception as e:
            logger.error(f"Failed to search destinations: {e}", exc_info=True)
            raise
