"""Search and autocomplete routes."""

from fastapi import APIRouter, Depends, Request, HTTPException, Query

from app.models.autocomplete import AutocompleteResponse
from app.services.autocomplete import AutocompleteService

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
    - Results ordered by relevance (countries > airports > cities by population)
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
