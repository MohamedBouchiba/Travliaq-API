"""Cities API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.cities import TopCitiesResponse
from app.services.cities import CitiesService

router = APIRouter(prefix="/cities", tags=["Cities"])


def get_cities_service(request) -> CitiesService:
    """Dependency to get the cities service."""
    return request.app.state.cities_service


@router.get(
    "/top-by-country/{country_code}",
    response_model=TopCitiesResponse,
    summary="Get top cities by country",
    description="""
    Retrieve the top cities by population for a given country.

    Returns between 1 and 5 cities depending on the country size.
    Cities are ordered by population (largest first).

    **Parameters:**
    - `country_code`: ISO2 country code (e.g., "FR" for France, "QA" for Qatar, "US" for United States)
    - `limit`: Maximum number of cities to return (default: 5, min: 1, max: 10)

    **Example:**
    - `/cities/top-by-country/QA` - Get top cities in Qatar
    - `/cities/top-by-country/FR?limit=3` - Get top 3 cities in France
    """
)
async def get_top_cities_by_country(
    country_code: str,
    limit: int = Query(5, ge=1, le=10, description="Maximum number of cities to return"),
    service: CitiesService = Depends(get_cities_service)
) -> TopCitiesResponse:
    """
    Get the top cities by population for a given country.

    Args:
        country_code: ISO2 country code (e.g., "FR", "QA", "US")
        limit: Maximum number of cities to return (1-10)
        service: Cities service dependency

    Returns:
        TopCitiesResponse with country info and list of top cities

    Raises:
        HTTPException: 404 if country not found or has no cities
    """
    result = service.get_top_cities_by_country(country_code=country_code, limit=limit)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No cities found for country code '{country_code}'. "
                   f"Please check that the country code is valid (ISO2 format, e.g., 'FR', 'QA', 'US')."
        )

    return result
