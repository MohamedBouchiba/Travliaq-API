"""Search and autocomplete routes."""

from fastapi import APIRouter, Depends, Request, HTTPException

from app.models.autocomplete import AutocompleteRequest, AutocompleteResponse
from app.services.autocomplete import AutocompleteService

router = APIRouter(prefix="/search", tags=["search"])


def get_autocomplete_service(request: Request) -> AutocompleteService:
    """Dependency to get the autocomplete service from app state."""
    return request.app.state.autocomplete_service


@router.post("/autocomplete", response_model=AutocompleteResponse)
async def search_autocomplete(
    payload: AutocompleteRequest,
    service: AutocompleteService = Depends(get_autocomplete_service)
) -> AutocompleteResponse:
    """
    Autocomplete search for locations (countries, cities, airports).

    ## Usage
    Send a query string (minimum 1 character, recommended 3+) to get location suggestions.

    ## Parameters
    - **query**: Search term (e.g., "Par", "New Yo", "CDG")
    - **limit**: Maximum number of results (default: 5, max: 20)

    ## Returns
    List of matching locations sorted by relevance:
    - Countries (higher rank due to population + 1B boost)
    - Airports (fixed rank of 500k)
    - Cities (ranked by population)

    ## Example Request
    ```json
    {
      "query": "Par",
      "limit": 5
    }
    ```

    ## Example Response
    ```json
    {
      "results": [
        {
          "type": "city",
          "ref": "uuid-here",
          "label": "Paris, FR",
          "country_code": "FR",
          "slug": "paris"
        },
        {
          "type": "airport",
          "ref": "CDG",
          "label": "Paris Charles de Gaulle (CDG)",
          "country_code": "FR",
          "slug": "paris-charles-de-gaulle"
        }
      ],
      "query": "Par",
      "count": 2
    }
    ```
    """
    try:
        results = service.search(payload)

        return AutocompleteResponse(
            results=results,
            query=payload.query,
            count=len(results)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during autocomplete search: {str(e)}"
        )
