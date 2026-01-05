"""Booking.com API HTTP client via RapidAPI (booking-com15)."""

from __future__ import annotations
import asyncio
import logging
from typing import Optional, Any, List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class BookingAPIError(Exception):
    """Exception raised for Booking API errors."""
    pass


class BookingRateLimitError(BookingAPIError):
    """Exception raised when rate limit is exceeded."""
    pass


class BookingClient:
    """HTTP client for Booking.com API via RapidAPI with automatic retry."""

    BASE_URL = "https://booking-com15.p.rapidapi.com/api/v1"

    def __init__(
        self,
        api_key: str,
        http_client: Optional[httpx.AsyncClient] = None
    ):
        """
        Initialize Booking.com API client.

        Args:
            api_key: RapidAPI key
            http_client: Optional shared httpx.AsyncClient instance
        """
        self.api_key = api_key
        self.http_client = http_client or httpx.AsyncClient(timeout=30.0)
        self._own_client = http_client is None

        logger.info("BookingClient initialized")

    async def close(self):
        """Close HTTP client if owned by this instance."""
        if self._own_client:
            await self.http_client.aclose()

    def _build_headers(self) -> dict:
        """Build request headers for RapidAPI."""
        return {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "booking-com15.p.rapidapi.com",
            "Accept": "application/json"
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, BookingRateLimitError)),
        reraise=True
    )
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None
    ) -> dict:
        """
        Make HTTP request to Booking.com API with automatic retry.

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON request body

        Returns:
            JSON response as dict

        Raises:
            BookingAPIError: If API returns an error
            BookingRateLimitError: If rate limit is exceeded
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._build_headers()

        logger.info(f"Booking API request: {method} {endpoint}")
        logger.debug(f"Params: {params}")

        try:
            response = await self.http_client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limit exceeded, retry after {retry_after}s")
                raise BookingRateLimitError(f"Rate limit exceeded, retry after {retry_after}s")

            # Handle other errors
            response.raise_for_status()

            data = response.json()

            # RapidAPI sometimes wraps response in 'data' or 'result'
            if isinstance(data, dict):
                if "data" in data:
                    return data["data"]
                if "result" in data:
                    return data["result"]

            return data

        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = e.response.text

            logger.error(f"Booking API error {e.response.status_code}: {error_detail}")
            raise BookingAPIError(f"Booking API error {e.response.status_code}: {error_detail}")

        except httpx.RequestError as e:
            logger.error(f"Request error to Booking API: {e}")
            raise

    async def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make GET request to Booking API."""
        return await self.request("GET", endpoint, params=params)

    # =========================================================================
    # DESTINATION ENDPOINTS
    # =========================================================================

    async def search_destination(self, query: str, locale: str = "en-gb") -> List[dict]:
        """
        Search for destinations (cities, regions, hotels).

        Args:
            query: Search query (city name)
            locale: Language locale

        Returns:
            List of destination results with dest_id and dest_type
        """
        params = {
            "query": query,
            "locale": locale
        }

        result = await self.get("/hotels/searchDestination", params)

        # Result is typically a list of destinations
        if isinstance(result, list):
            return result
        return result.get("data", []) if isinstance(result, dict) else []

    # =========================================================================
    # HOTEL SEARCH ENDPOINTS
    # =========================================================================

    async def search_hotels(
        self,
        dest_id: str,
        dest_type: str,
        checkin_date: str,
        checkout_date: str,
        adults_number: int,
        room_number: int = 1,
        children_number: int = 0,
        children_ages: Optional[str] = None,
        filter_by_currency: str = "EUR",
        locale: str = "en-gb",
        order_by: str = "popularity",
        page_number: int = 1,
        units: str = "metric",
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        categories_filter_ids: Optional[str] = None
    ) -> dict:
        """
        Search for available hotels.

        Args:
            dest_id: Destination ID from searchDestination
            dest_type: Destination type (city, region, hotel, etc.)
            checkin_date: Check-in date (YYYY-MM-DD)
            checkout_date: Check-out date (YYYY-MM-DD)
            adults_number: Total number of adults
            room_number: Number of rooms
            children_number: Number of children
            children_ages: Comma-separated children ages
            filter_by_currency: Currency code
            locale: Language locale
            order_by: Sort order (popularity, price, review_score, distance)
            page_number: Page number for pagination (starts at 1)
            units: Units (metric/imperial)
            price_min: Minimum price filter
            price_max: Maximum price filter
            categories_filter_ids: Property type filter IDs

        Returns:
            Search results with hotels list
        """
        # Map dest_type to API's search_type format
        search_type = dest_type.upper() if dest_type else "CITY"

        # Map order_by to API format
        sort_by_map = {
            "popularity": "popularity",
            "price": "lowest_price",
            "review_score": "review_score",
            "distance": "distance"
        }
        sort_by = sort_by_map.get(order_by, "popularity")

        params = {
            "dest_id": dest_id,
            "search_type": search_type,
            "arrival_date": checkin_date,
            "departure_date": checkout_date,
            "adults": str(adults_number),
            "room_qty": str(room_number),
            "currency_code": filter_by_currency,
            "languagecode": locale,
            "sort_by": sort_by,
            "page_number": str(max(1, page_number)),  # API starts at 1
        }

        if children_number > 0:
            params["children_qty"] = str(children_number)
            if children_ages:
                params["children_age"] = children_ages

        if price_min is not None:
            params["price_min"] = str(price_min)
        if price_max is not None:
            params["price_max"] = str(price_max)
        if categories_filter_ids:
            params["categories_filter"] = categories_filter_ids

        return await self.get("/hotels/searchHotels", params)

    # =========================================================================
    # HOTEL DETAILS ENDPOINTS
    # =========================================================================

    async def get_hotel_details(
        self,
        hotel_id: str,
        checkin_date: str,
        checkout_date: str,
        adults_number: int,
        locale: str = "en-gb",
        currency_code: str = "EUR"
    ) -> dict:
        """
        Get detailed information about a hotel.

        Args:
            hotel_id: Hotel ID
            checkin_date: Check-in date
            checkout_date: Check-out date
            adults_number: Number of adults
            locale: Language locale
            currency_code: Currency code

        Returns:
            Hotel details dict
        """
        params = {
            "hotel_id": hotel_id,
            "arrival_date": checkin_date,
            "departure_date": checkout_date,
            "adults": str(adults_number),
            "languagecode": locale,
            "currency_code": currency_code
        }

        return await self.get("/hotels/getHotelDetails", params)

    async def get_hotel_photos(self, hotel_id: str, locale: str = "en-gb") -> List[dict]:
        """
        Get hotel photos.

        Args:
            hotel_id: Hotel ID
            locale: Language locale

        Returns:
            List of photo objects
        """
        params = {
            "hotel_id": hotel_id,
            "locale": locale
        }

        result = await self.get("/hotels/getHotelPhotos", params)
        return result if isinstance(result, list) else result.get("data", [])

    async def get_hotel_reviews(
        self,
        hotel_id: str,
        locale: str = "en-gb",
        sort_type: str = "SORT_MOST_RELEVANT",
        page_number: int = 0
    ) -> dict:
        """
        Get hotel reviews.

        Args:
            hotel_id: Hotel ID
            locale: Language locale
            sort_type: Sort type (SORT_MOST_RELEVANT, SORT_HIGHEST_RATED, etc.)
            page_number: Page number

        Returns:
            Reviews data
        """
        params = {
            "hotel_id": hotel_id,
            "locale": locale,
            "sort_type": sort_type,
            "page_number": str(page_number)
        }

        return await self.get("/hotels/getHotelReviews", params)

    async def get_hotel_facilities(self, hotel_id: str, locale: str = "en-gb") -> List[dict]:
        """
        Get hotel facilities/amenities.

        Args:
            hotel_id: Hotel ID
            locale: Language locale

        Returns:
            List of facility objects
        """
        params = {
            "hotel_id": hotel_id,
            "locale": locale
        }

        result = await self.get("/properties/get-facilities", params)
        return result if isinstance(result, list) else result.get("data", [])

    async def get_hotel_rooms(
        self,
        hotel_id: str,
        checkin_date: str,
        checkout_date: str,
        adults_number: int,
        room_number: int = 1,
        currency_code: str = "EUR",
        locale: str = "en-gb"
    ) -> dict:
        """
        Get available rooms and pricing.

        NOTE: The /hotels/getRooms endpoint is deprecated/removed.
        Room data is now included in getHotelDetails response.
        This method returns rooms from getHotelDetails for backwards compatibility.

        Args:
            hotel_id: Hotel ID
            checkin_date: Check-in date
            checkout_date: Check-out date
            adults_number: Number of adults
            room_number: Number of rooms
            currency_code: Currency code
            locale: Language locale

        Returns:
            Rooms data with pricing (from block field)
        """
        # Get full hotel details which includes rooms in 'block' field
        details = await self.get_hotel_details(
            hotel_id=hotel_id,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            adults_number=adults_number,
            locale=locale,
            currency_code=currency_code
        )

        # Extract rooms and block data
        return {
            "rooms": details.get("rooms", {}),
            "block": details.get("block", [])
        }
