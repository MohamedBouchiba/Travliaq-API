"""Cities API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.models.cities import TopCitiesResponse
from app.services.cities import CitiesService

router = APIRouter(prefix="/cities", tags=["Cities"])


def get_cities_service(request: Request) -> CitiesService:
    """Dependency to get the cities service."""
    return request.app.state.cities_service


@router.get(
    "/top-by-country/{country_identifier}",
    response_model=TopCitiesResponse,
    summary="Get top cities by country",
    description="""
    Retrieve the top cities by population for a given country.

    Returns between 1 and 5 cities depending on the country size.
    Cities are ordered by population (largest first).

    **Parameters:**
    - `country_identifier`: ISO2 country code (e.g., "FR", "US") OR country name (e.g., "France", "United States")
    - `limit`: Maximum number of cities to return (default: 5, min: 1, max: 10)

    **Examples:**
    - `/cities/top-by-country/QA` - Get top cities in Qatar (by code)
    - `/cities/top-by-country/France` - Get top cities in France (by name)
    - `/cities/top-by-country/FR?limit=3` - Get top 3 cities in France (by code)
    - `/cities/top-by-country/United%20States?limit=5` - Get top 5 cities in USA (by name)
    """
)
async def get_top_cities_by_country(
    country_identifier: str,
    limit: int = Query(5, ge=1, le=10, description="Maximum number of cities to return"),
    service: CitiesService = Depends(get_cities_service)
) -> TopCitiesResponse:
    """
    Get the top cities by population for a given country.

    Args:
        country_identifier: ISO2 country code (e.g., "FR", "US") or country name (e.g., "France", "Qatar")
        limit: Maximum number of cities to return (1-10)
        service: Cities service dependency

    Returns:
        TopCitiesResponse with country info and list of top cities

    Raises:
        HTTPException: 404 if country not found or has no cities
    """
    result = service.get_top_cities_by_country(country_identifier=country_identifier, limit=limit)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No cities found for '{country_identifier}'. "
                   f"Please provide a valid ISO2 country code (e.g., 'FR', 'US') "
                   f"or country name (e.g., 'France', 'United States')."
        )

    return result
