"""Viator attractions API methods."""

from __future__ import annotations
import logging
from .client import ViatorClient

logger = logging.getLogger(__name__)


class ViatorAttractionsService:
    """Service for Viator /attractions/* endpoints."""

    def __init__(self, client: ViatorClient):
        self.client = client

    async def search_attractions(
        self,
        destination_id: str,
        sort: str = "DEFAULT",
        start: int = 1,
        count: int = 20,
        language: str = "en"
    ) -> dict:
        """
        Search attractions using /attractions/search endpoint.

        Args:
            destination_id: Viator destination ID (required)
            sort: Sort method - one of:
                - "DEFAULT": Featured attractions (influenced by commission)
                - "ALPHABETICAL": Alphabetical ascending
                - "REVIEW_AVG_RATING": Average review rating descending
            start: Pagination start position (1-based)
            count: Number of results to return (max 30)
            language: Language code for translations

        Returns:
            API response with attractions list

        Response includes:
            - attractions[]: List of attractions with:
                - attractionId: Unique numeric ID
                - name: Attraction name (localized)
                - center: {latitude, longitude} - Direct coordinates!
                - address: {street, city, state, postalCode}
                - productCodes[]: Related activities
                - images[]: Photos
                - reviews: {combinedAverageRating, totalReviews}
                - freeAttraction: boolean
                - openingHours: string
        """
        logger.info(f"Searching attractions for destination {destination_id}")

        # Build request body
        request_body = {
            "destinationId": int(destination_id),
            "pagination": {
                "start": start,
                "count": min(count, 30)  # API limit is 30
            }
        }

        # Add sorting if not default
        if sort and sort != "DEFAULT":
            request_body["sorting"] = {"sort": sort}

        response = await self.client.post(
            "/attractions/search",
            json_data=request_body,
            language=language
        )

        attractions_count = len(response.get("attractions", []))
        total_count = response.get("totalCount", 0)
        logger.info(f"Found {attractions_count} attractions (total: {total_count})")

        return response
