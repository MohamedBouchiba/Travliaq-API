"""Activities API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
import logging

from app.models.activities import (
    ActivitySearchRequest,
    ActivitySearchResponse,
    ErrorResponse,
    ErrorDetail
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/activities", tags=["Activities"])


def get_activities_service(request: Request):
    """Dependency to get activities service from app state."""
    service = request.app.state.activities_service
    if service is None:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Viator integration is not configured. Please set VIATOR_API_KEY_DEV or VIATOR_API_KEY_PROD in environment variables.",
                    "details": None
                }
            }
        )
    return service


@router.post(
    "/search",
    response_model=ActivitySearchResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Search for activities",
    description="""
    Search for activities based on location, dates, and filters.

    **Location options** (provide one):
    - City name + country code
    - Viator destination ID
    - Geographic coordinates (lat/lon + radius)

    **Features**:
    - Intelligent caching (7 days TTL)
    - Fuzzy city name matching
    - Filter by categories, price, rating, duration
    - Sort by rating, price, or default
    - Pagination support

    **Example**:
    ```json
    {
      "location": {"city": "Paris", "country_code": "FR"},
      "dates": {"start": "2026-03-15"},
      "filters": {
        "categories": ["food", "museum"],
        "price_range": {"min": 10, "max": 200},
        "rating_min": 4.0
      },
      "sorting": {"sort_by": "rating", "order": "desc"},
      "pagination": {"page": 1, "limit": 20},
      "currency": "EUR",
      "language": "fr"
    }
    ```
    """
)
async def search_activities(
    request: ActivitySearchRequest,
    service=Depends(get_activities_service)
):
    """
    Search for activities.

    Returns a list of activities matching the search criteria, with simplified
    information suitable for frontend consumption (images, pricing, ratings, etc.).
    """
    try:
        response = await service.search_activities(request)
        return response

    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_LOCATION",
                    "message": str(e),
                    "details": None
                }
            }
        )

    except Exception as e:
        logger.error(f"Error searching activities: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": None
                }
            }
        )


@router.get(
    "/health",
    summary="Health check for activities service",
    description="Check if the activities service is healthy and can communicate with Viator API"
)
async def health_check(service=Depends(get_activities_service)):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "activities",
        "viator_api": "connected"
    }
