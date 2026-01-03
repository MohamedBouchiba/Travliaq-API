"""Viator products API methods."""

from __future__ import annotations
import logging
from typing import Optional
from .client import ViatorClient

logger = logging.getLogger(__name__)


class ViatorProductsService:
    """Service for Viator /products/* endpoints."""

    def __init__(self, client: ViatorClient):
        self.client = client

    async def search_products(
        self,
        destination_id: str,
        start_date: str,
        end_date: Optional[str] = None,
        tags: Optional[list[int]] = None,
        lowest_price: Optional[float] = None,
        highest_price: Optional[float] = None,
        rating_from: Optional[float] = None,
        flags: Optional[list[str]] = None,
        sort: str = "DEFAULT",
        order: str = "ASCENDING",
        start: int = 1,
        count: int = 20,
        currency: str = "EUR",
        language: str = "en"
    ) -> dict:
        """
        Search products using /products/search endpoint.

        Args:
            destination_id: Viator destination ID (required)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (optional)
            tags: List of tag IDs for filtering
            lowest_price: Minimum price
            highest_price: Maximum price
            rating_from: Minimum rating (0-5)
            flags: List of flags (FREE_CANCELLATION, LIKELY_TO_SELL_OUT, etc.)
            sort: Sort method (DEFAULT, PRICE, TRAVELER_RATING, etc.)
            order: Sort order (ASCENDING, DESCENDING)
            start: Pagination start position (1-based)
            count: Number of results to return (max 50)
            currency: Currency code (EUR, USD, etc.)
            language: Language code for translations

        Returns:
            API response with products list
        """
        # Build filtering object
        filtering = {"destination": destination_id}

        if start_date:
            filtering["startDate"] = start_date
        if end_date:
            filtering["endDate"] = end_date
        if tags:
            filtering["tags"] = tags
        if lowest_price is not None:
            filtering["lowestPrice"] = lowest_price
        if highest_price is not None:
            filtering["highestPrice"] = highest_price
        if rating_from is not None:
            filtering["rating"] = {"from": rating_from}
        if flags:
            filtering["flags"] = flags

        # Build request body
        request_body = {
            "filtering": filtering,
            "currency": currency
        }

        # Add sorting if not default
        if sort != "DEFAULT":
            request_body["sorting"] = {
                "sort": sort,
                "order": order
            }

        # Add pagination
        request_body["pagination"] = {
            "start": start,
            "count": min(count, 50)  # Max 50 per API spec
        }

        logger.info(f"Searching products for destination {destination_id}")

        response = await self.client.post("/partner/products/search", request_body, language=language)

        logger.info(f"Found {response.get('totalCount', 0)} products")

        return response

    async def get_product_details(self, product_code: str, language: str = "en") -> dict:
        """
        Get full product details.

        Args:
            product_code: Viator product code
            language: Language for translations

        Returns:
            Full product details
        """
        logger.info(f"Fetching product details for {product_code}")

        return await self.client.get(f"/partner/products/{product_code}", language=language)

    async def get_bulk_products(self, product_codes: list[str], language: str = "en") -> list[dict]:
        """
        Get bulk product details.

        Args:
            product_codes: List of Viator product codes
            language: Language for translations

        Returns:
            List of product details
        """
        if not product_codes:
            return []

        logger.info(f"Fetching bulk product details for {len(product_codes)} products")

        response = await self.client.post(
            "/partner/products/bulk",
            json_data={"productCodes": product_codes},
            language=language
        )
        
        return response.get("products", [])
