"""Viator API HTTP client with retry logic and rate limiting."""

from __future__ import annotations
import asyncio
import logging
from typing import Optional, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class ViatorAPIError(Exception):
    """Exception raised for Viator API errors."""
    pass


class ViatorRateLimitError(ViatorAPIError):
    """Exception raised when rate limit is exceeded."""
    pass


class ViatorClient:
    """HTTP client for Viator API with automatic retry and error handling."""

    def __init__(self, api_key: str, base_url: str = "https://api.viator.com", http_client: Optional[httpx.AsyncClient] = None):
        """
        Initialize Viator API client.

        Args:
            api_key: Viator API key (exp-api-key)
            base_url: Base URL for Viator API
            http_client: Optional shared httpx.AsyncClient instance
        """
        self.api_key = api_key
        self.base_url = base_url
        self.http_client = http_client or httpx.AsyncClient(timeout=30.0)
        self._own_client = http_client is None

        logger.info(f"ViatorClient initialized with base_url={base_url}")

    async def close(self):
        """Close HTTP client if owned by this instance."""
        if self._own_client:
            await self.http_client.aclose()

    def _build_headers(self, language: str = "en") -> dict:
        """Build request headers for Viator API."""
        return {
            "Accept": "application/json;version=2.0",
            "Accept-Language": language,
            "exp-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, ViatorRateLimitError)),
        reraise=True
    )
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        language: str = "en"
    ) -> dict:
        """
        Make HTTP request to Viator API with automatic retry.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/products/search")
            params: Query parameters
            json_data: JSON request body
            language: Accept-Language header value

        Returns:
            JSON response as dict

        Raises:
            ViatorAPIError: If API returns an error
            ViatorRateLimitError: If rate limit is exceeded
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._build_headers(language)

        logger.info(f"Viator API request: {method} {endpoint}")

        try:
            response = await self.http_client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )

            # Log rate limit headers
            if "RateLimit-Remaining" in response.headers:
                logger.info(
                    f"Rate limit: {response.headers['RateLimit-Remaining']}/{response.headers.get('RateLimit-Limit', 'unknown')} remaining"
                )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limit exceeded, retry after {retry_after}s")
                raise ViatorRateLimitError(f"Rate limit exceeded, retry after {retry_after}s")

            # Handle other errors
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = e.response.text

            logger.error(f"Viator API error {e.response.status_code}: {error_detail}")
            raise ViatorAPIError(f"Viator API error {e.response.status_code}: {error_detail}")

        except httpx.RequestError as e:
            logger.error(f"Request error to Viator API: {e}")
            raise

    async def get(self, endpoint: str, params: Optional[dict] = None, language: str = "en") -> dict:
        """Make GET request to Viator API."""
        return await self.request("GET", endpoint, params=params, language=language)

    async def post(self, endpoint: str, json_data: dict, language: str = "en") -> dict:
        """Make POST request to Viator API."""
        return await self.request("POST", endpoint, json_data=json_data, language=language)

    async def get_location_details(self, location_ref: str) -> dict:
        """
        Get details for a single location reference.
        
        Args:
            location_ref: Location reference code
            
        Returns:
            Location details dict
        """
        return await self.get(f"/locations/{location_ref}")

    async def get_bulk_locations(self, location_refs: list[str]) -> list[dict]:
        """
        Get bulk location details.

        Args:
            location_refs: List of location reference codes

        Returns:
            List of location objects
        """
        if not location_refs:
            return []

        logger.info(f"Fetching bulk locations for {len(location_refs)} refs")
        
        response = await self.post(
            "/locations/bulk",
            json_data={"locations": location_refs}
        )
        
        return response.get("locations", [])
