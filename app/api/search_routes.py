"""Search and autocomplete routes."""

from fastapi import APIRouter, Depends, Request, HTTPException, Query, Body

from app.models.autocomplete import AutocompleteResponse
from app.models.airports import NearestAirportsRequest, NearestAirportsResponse
from app.models.cities import TopCitiesResponse
from app.services.autocomplete import AutocompleteService
from app.services.airports import AirportsService
from app.services.cities import CitiesService

router = APIRouter(tags=["search"])


def get_autocomplete_service(request: Request) -> AutocompleteService:
    """Dependency to get the autocomplete service from app state."""
    service = request.app.state.autocomplete_service
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Autocomplete service unavailable - PostgreSQL not configured"
        )
    return service


def get_airports_service(request: Request) -> AirportsService:
    """Dependency to get the airports service from app state."""
    service = request.app.state.airports_service
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Airports service unavailable - PostgreSQL not configured"
        )
    return service


def get_cities_service(request: Request) -> CitiesService:
    """Dependency to get the cities service from app state."""
    service = request.app.state.cities_service
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Cities service unavailable - PostgreSQL not configured"
        )
    return service


@router.get("/autocomplete", response_model=AutocompleteResponse)
async def search_autocomplete(
    q: str = Query(..., description="Search query (results empty if < 3 chars)", min_length=1),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of results"),
    types: str = Query(
        "city,airport,country",
        description="Comma-separated list of types to filter (e.g., 'city,airport')",
        regex="^(city|airport|country)(,(city|airport|country))*$"
    ),
    service: AutocompleteService = Depends(get_autocomplete_service)
) -> AutocompleteResponse:
    """
    Autocomplete search for locations (countries, cities, airports).

    ## Usage
    Returns location suggestions based on the search query.

    ## Parameters
    - **q** (required): Search term - Returns empty results if < 3 characters
    - **limit** (optional): Maximum results (default: 10, max: 20)
    - **types** (optional): Filter by type - default: "city,airport,country"

    ## Example Request
    ```
    GET /autocomplete?q=par&limit=10&types=city,airport,country
    ```

    ## Example Response
    ```json
    {
      "q": "par",
      "results": [
        {
          "type": "city",
          "id": "3978405a-2f88-40fd-a9d1-1b7c896626ff",
          "label": "Paris, FR",
          "country_code": "FR",
          "slug": "paris",
          "lat": 48.8566,
          "lon": 2.3522
        },
        {
          "type": "airport",
          "id": "CDG",
          "label": "Paris Charles de Gaulle (CDG)",
          "country_code": "FR",
          "slug": "paris-charles-de-gaulle-cdg",
          "lat": 49.0097,
          "lon": 2.5479
        },
        {
          "type": "country",
          "id": "PY",
          "label": "Paraguay",
          "country_code": "PY",
          "slug": "paraguay",
          "lat": null,
          "lon": null
        }
      ]
    }
    ```

    ## Behavior
    - Returns `results: []` if query < 3 characters
    - Results ordered by: match relevance, then type (cities > airports > countries), then by population/importance (rank_signal DESC)
    - Case-insensitive search
    - Prioritizes results starting with query over those containing it
    """
    try:
        # Parse types from comma-separated string
        type_list = [t.strip() for t in types.split(",") if t.strip()]

        # Search
        results = service.search(q=q, limit=limit, types=type_list)

        return AutocompleteResponse(
            q=q,
            results=results
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during autocomplete search: {str(e)}"
        )


@router.post("/nearest-airports", response_model=NearestAirportsResponse)
async def find_nearest_airports(
    request: NearestAirportsRequest = Body(...),
    service: AirportsService = Depends(get_airports_service)
) -> NearestAirportsResponse:
    """
    Find the nearest airports to a city.

    ## Features
    - **Fuzzy matching**: Handles typos and spelling variations (min 80% similarity)
    - **Country filtering**: Optional country code to improve match accuracy
    - **Geographic distance**: Uses PostGIS to calculate actual distances
    - **Sorted results**: Returns airports sorted by distance (closest first)

    ## Parameters
    - **city** (required): City name (fuzzy matching supported - typos OK!)
    - **country_code** (optional): ISO2 country code (e.g., 'FR', 'US') to filter cities by country
    - **limit** (optional): Number of airports to return (default: 3, max: 10)

    ## Example Request
    ```json
    {
      "city": "Londre",
      "country_code": "GB",
      "limit": 3
    }
    ```

    ## Example Response
    ```json
    {
      "city_query": "Londre",
      "matched_city": "London",
      "matched_city_id": "uuid-here",
      "match_score": 95,
      "city_location": {
        "lat": 51.5074,
        "lon": -0.1278
      },
      "airports": [
        {
          "iata": "LCY",
          "name": "London City Airport (LCY)",
          "city_name": "London City Airport",
          "country_code": "GB",
          "lat": 51.5053,
          "lon": 0.0553,
          "distance_km": 9.87
        },
        {
          "iata": "LHR",
          "name": "London Heathrow (LHR)",
          "city_name": "London Heathrow",
          "country_code": "GB",
          "lat": 51.4700,
          "lon": -0.4543,
          "distance_km": 24.32
        },
        {
          "iata": "LGW",
          "name": "London Gatwick (LGW)",
          "city_name": "London Gatwick",
          "country_code": "GB",
          "lat": 51.1537,
          "lon": -0.1821,
          "distance_km": 39.54
        }
      ]
    }
    ```

    ## Behavior
    - Returns 404 if no matching city found (match score < 80)
    - Match score: 100.0 = exact match, 80.0-99.9 = fuzzy match
    - Distances calculated using PostGIS (great circle distance)
    - Results sorted by distance (ascending)

    ## Error Cases
    - **404 Not Found**: No city match found for the query
    - **503 Service Unavailable**: PostgreSQL not configured
    - **500 Internal Server Error**: Unexpected error during search
    """
    try:
        result = service.find_nearest_airports(
            city_query=request.city,
            limit=request.limit,
            country_code=request.country_code
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No city match found for '{request.city}'. "
                       f"Please check spelling or try a different city name."
            )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error finding nearest airports: {str(e)}"
        )


@router.get("/top-cities/{country_code}", response_model=TopCitiesResponse)
async def get_top_cities(
    country_code: str,
    limit: int = Query(5, ge=1, le=20, description="Number of cities to return"),
    service: CitiesService = Depends(get_cities_service)
) -> TopCitiesResponse:
    """
    Get the top cities by population for a given country.

    ## Features
    - **Population-based ranking**: Cities sorted by population (largest first)
    - **Flexible limit**: Request 1-20 cities (default: 5)
    - **Geographic data**: Includes coordinates for each city

    ## Parameters
    - **country_code** (required): ISO2 country code (e.g., "FR", "US", "GB")
    - **limit** (optional): Number of cities to return (default: 5, max: 20)

    ## Example Request
    ```
    GET /top-cities/FR?limit=5
    ```

    ## Example Response
    ```json
    {
      "country_code": "FR",
      "total_cities": 2847,
      "cities": [
        {
          "id": "3978405a-2f88-40fd-a9d1-1b7c896626ff",
          "name": "Paris",
          "country_code": "FR",
          "slug": "paris",
          "population": 2138551,
          "lat": 48.8566,
          "lon": 2.3522
        },
        {
          "id": "uuid-marseille",
          "name": "Marseille",
          "country_code": "FR",
          "slug": "marseille",
          "population": 869815,
          "lat": 43.2965,
          "lon": 5.3698
        },
        {
          "id": "uuid-lyon",
          "name": "Lyon",
          "country_code": "FR",
          "slug": "lyon",
          "population": 513275,
          "lat": 45.7640,
          "lon": 4.8357
        }
      ]
    }
    ```

    ## Behavior
    - Returns 404 if country code not found or has no cities
    - Case-insensitive country code matching (fr = FR)
    - Cities ordered by: population DESC, then rank_signal DESC
    - Includes total_cities count for the country

    ## Error Cases
    - **404 Not Found**: Country code not found or has no cities
    - **503 Service Unavailable**: PostgreSQL not configured
    - **500 Internal Server Error**: Unexpected error during search
    """
    try:
        result = service.get_top_cities_by_country(
            country_code=country_code,
            limit=limit
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No cities found for country code '{country_code}'. "
                       f"Please check the country code (use ISO2 format like 'FR', 'US')."
            )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving top cities: {str(e)}"
        )
