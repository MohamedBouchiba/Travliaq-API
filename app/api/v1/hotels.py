"""Hotels API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from datetime import date
import logging

from app.models.hotels import (
    HotelSearchRequest,
    HotelSearchResponse,
    HotelDetailsQuery,
    HotelDetailsResponse,
    MapPricesRequest,
    MapPricesResponse,
    HotelErrorResponse,
    HotelErrorDetail
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hotels", tags=["Hotels"])


def get_hotels_service(request: Request):
    """Dependency to get hotels service from app state."""
    service = request.app.state.hotels_service
    if service is None:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Hotels integration is not configured. Please set RAPIDAPI_KEY in environment variables.",
                    "details": None
                }
            }
        )
    return service


# =============================================================================
# HEALTH CHECK (must be before /{hotel_id} to avoid route conflict)
# =============================================================================

@router.get(
    "/health",
    summary="Health check for hotels service",
    description="Check if the hotels service is healthy and configured"
)
async def health_check(service=Depends(get_hotels_service)):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "hotels",
        "booking_api": "connected"
    }


# =============================================================================
# POST /hotels/search
# =============================================================================

@router.post(
    "/search",
    response_model=HotelSearchResponse,
    responses={
        400: {"model": HotelErrorResponse},
        404: {"model": HotelErrorResponse},
        500: {"model": HotelErrorResponse},
        503: {"model": HotelErrorResponse}
    },
    summary="Search for hotels",
    description="""
    Search for available hotels in a city.

    **Required parameters**:
    - `city`: City name (e.g., "Paris")
    - `countryCode`: ISO country code (e.g., "FR")
    - `lat`, `lng`: Coordinates for map display
    - `checkIn`, `checkOut`: Dates in YYYY-MM-DD format
    - `rooms`: Array of room configurations with adults and children ages

    **Optional filters**:
    - `priceMin`, `priceMax`: Price range per night
    - `types`: Property types (hotel, apartment, hostel, etc.)
    - `minRating`: Minimum rating (0-10)
    - `minStars`: Minimum star rating (1-5)
    - `amenities`: Required amenities (wifi, parking, breakfast, pool, gym, spa, restaurant, bar, ac, kitchen)

    **Sorting options**:
    - `price_asc`, `price_desc`: Sort by price
    - `rating`: Sort by rating
    - `distance`: Sort by distance from center
    - `popularity`: Sort by popularity (default)

    **Example**:
    ```json
    {
      "city": "Paris",
      "countryCode": "FR",
      "lat": 48.8566,
      "lng": 2.3522,
      "checkIn": "2025-03-15",
      "checkOut": "2025-03-18",
      "rooms": [{"adults": 2, "childrenAges": []}],
      "filters": {
        "priceMin": 50,
        "priceMax": 300,
        "types": ["hotel"],
        "minRating": 7
      },
      "sort": "price_asc",
      "limit": 30,
      "currency": "EUR"
    }
    ```
    """
)
async def search_hotels(
    request: HotelSearchRequest,
    force_refresh: bool = Query(False, description="Bypass cache and fetch fresh data"),
    service=Depends(get_hotels_service)
):
    """
    Search for hotels.

    Returns a list of hotels matching the search criteria, with coordinates
    for map display and pricing information.
    """
    # Validate dates
    today = date.today()
    if request.checkIn < today:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "PAST_DATE",
                    "message": f"Check-in date {request.checkIn} cannot be in the past. Today is {today}.",
                    "details": None
                }
            }
        )
    if request.checkOut <= request.checkIn:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_DATE_RANGE",
                    "message": f"Check-out date must be after check-in date.",
                    "details": None
                }
            }
        )
    if (request.checkOut - request.checkIn).days > 30:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "STAY_TOO_LONG",
                    "message": "Maximum stay is 30 nights.",
                    "details": None
                }
            }
        )

    try:
        response = await service.search_hotels(request, force_refresh=force_refresh)
        return response

    except ValueError as e:
        logger.warning(f"Invalid hotel search request: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": str(e),
                    "details": None
                }
            }
        )

    except Exception as e:
        error_msg = str(e)
        if "No destination found" in error_msg:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": {
                        "code": "DESTINATION_NOT_FOUND",
                        "message": f"Could not find destination: {request.city}",
                        "details": None
                    }
                }
            )

        logger.error(f"Error searching hotels: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred while searching hotels",
                    "details": None
                }
            }
        )


# =============================================================================
# GET /hotels/{hotel_id}
# =============================================================================

@router.get(
    "/{hotel_id}",
    response_model=HotelDetailsResponse,
    responses={
        400: {"model": HotelErrorResponse},
        404: {"model": HotelErrorResponse},
        500: {"model": HotelErrorResponse},
        503: {"model": HotelErrorResponse}
    },
    summary="Get hotel details",
    description="""
    Get detailed information about a specific hotel.

    **Required query parameters**:
    - `checkIn`: Check-in date (YYYY-MM-DD)
    - `checkOut`: Check-out date (YYYY-MM-DD)
    - `rooms`: Room configuration string

    **Room format**: `adults-childAge1-childAge2,...`
    - Example: `2-0` = 1 room with 2 adults, no children
    - Example: `2-0,2-8-5` = 2 rooms: first with 2 adults, second with 2 adults and children aged 8 and 5

    **Response includes**:
    - Full hotel description
    - All photos
    - Amenities with labels
    - Available rooms with pricing
    - Booking policies
    - Booking URL

    **Example**:
    ```
    GET /hotels/htl_12345?checkIn=2025-03-15&checkOut=2025-03-18&rooms=2-0&currency=EUR
    ```
    """
)
async def get_hotel_details(
    hotel_id: str,
    checkIn: date = Query(..., description="Check-in date"),
    checkOut: date = Query(..., description="Check-out date"),
    rooms: str = Query(..., description="Room configuration: adults-childAge1-childAge2,... per room"),
    currency: str = Query("EUR", description="Currency code", pattern="^[A-Z]{3}$"),
    locale: str = Query("en", description="Language code", pattern="^[a-z]{2}$"),
    force_refresh: bool = Query(False, description="Bypass cache and fetch fresh data"),
    service=Depends(get_hotels_service)
):
    """
    Get detailed hotel information.

    Returns complete hotel details including photos, amenities, rooms, and policies.
    """
    # Validate dates
    today = date.today()
    if checkIn < today:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "PAST_DATE",
                    "message": f"Check-in date {checkIn} cannot be in the past. Today is {today}.",
                    "details": None
                }
            }
        )
    if checkOut <= checkIn:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_DATE_RANGE",
                    "message": f"Check-out date must be after check-in date.",
                    "details": None
                }
            }
        )

    try:
        query = HotelDetailsQuery(
            checkIn=checkIn,
            checkOut=checkOut,
            rooms=rooms,
            currency=currency,
            locale=locale
        )

        response = await service.get_hotel_details(hotel_id, query, force_refresh=force_refresh)

        if not response.hotel:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": {
                        "code": "HOTEL_NOT_FOUND",
                        "message": f"Hotel not found: {hotel_id}",
                        "details": None
                    }
                }
            )

        return response

    except HTTPException:
        raise

    except ValueError as e:
        logger.warning(f"Invalid hotel details request: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": str(e),
                    "details": None
                }
            }
        )

    except Exception as e:
        logger.error(f"Error getting hotel details: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred while fetching hotel details",
                    "details": None
                }
            }
        )


# =============================================================================
# POST /hotels/map-prices
# =============================================================================

@router.post(
    "/map-prices",
    response_model=MapPricesResponse,
    responses={
        400: {"model": HotelErrorResponse},
        500: {"model": HotelErrorResponse},
        503: {"model": HotelErrorResponse}
    },
    summary="Get minimum prices for map markers",
    description="""
    Get minimum hotel prices for multiple cities to display as map markers.

    **Important notes**:
    - Maximum 10 cities per request (limited to avoid rate limits)
    - Results are aggressively cached (2 hours)
    - Prices may be null if no hotels available

    **Example**:
    ```json
    {
      "cities": [
        {"city": "Paris", "countryCode": "FR", "lat": 48.8566, "lng": 2.3522},
        {"city": "Lyon", "countryCode": "FR", "lat": 45.7640, "lng": 4.8357}
      ],
      "checkIn": "2025-03-15",
      "checkOut": "2025-03-18",
      "rooms": [{"adults": 2, "childrenAges": []}],
      "currency": "EUR"
    }
    ```

    **Response**:
    ```json
    {
      "success": true,
      "prices": {
        "Paris_FR": {"minPrice": 85, "currency": "EUR"},
        "Lyon_FR": {"minPrice": 62, "currency": "EUR"}
      }
    }
    ```

    **Cache behavior**:
    - Results cached for 2 hours
    - Use `force_refresh=true` to bypass cache
    """
)
async def get_map_prices(
    request: MapPricesRequest,
    force_refresh: bool = Query(False, description="Bypass cache and fetch fresh data"),
    service=Depends(get_hotels_service)
):
    """
    Get minimum prices per city for map display.

    Returns the cheapest hotel price for each requested city.
    """
    # Validate dates
    today = date.today()
    if request.checkIn < today:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "PAST_DATE",
                    "message": f"Check-in date {request.checkIn} cannot be in the past. Today is {today}.",
                    "details": None
                }
            }
        )
    if request.checkOut <= request.checkIn:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_DATE_RANGE",
                    "message": f"Check-out date must be after check-in date.",
                    "details": None
                }
            }
        )

    try:
        # Validate number of cities
        if len(request.cities) > 20:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "TOO_MANY_CITIES",
                        "message": "Maximum 20 cities allowed per request",
                        "details": {"max_cities": 20, "requested": len(request.cities)}
                    }
                }
            )

        response = await service.get_map_prices(request, force_refresh=force_refresh)
        return response

    except HTTPException:
        raise

    except ValueError as e:
        logger.warning(f"Invalid map prices request: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": str(e),
                    "details": None
                }
            }
        )

    except Exception as e:
        logger.error(f"Error getting map prices: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred while fetching map prices",
                    "details": None
                }
            }
        )


