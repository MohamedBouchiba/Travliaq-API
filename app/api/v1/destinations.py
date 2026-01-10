"""Destinations API endpoints for personalized destination suggestions."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
import logging

from app.models.destination_suggestions import (
    DestinationSuggestionsResponse,
    SuggestionError,
    SuggestionErrorResponse,
    UserPreferencesPayload,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/destinations", tags=["Destinations"])


def get_suggestions_service(request: Request):
    """Dependency to get destination suggestions service from app state."""
    service = request.app.state.destination_suggestions_service
    if service is None:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Destination suggestions service is not configured. Please ensure country profiles are loaded.",
                    "details": None,
                },
            },
        )
    return service


@router.post(
    "/suggest",
    response_model=DestinationSuggestionsResponse,
    responses={
        400: {"model": SuggestionErrorResponse},
        500: {"model": SuggestionErrorResponse},
        503: {"model": SuggestionErrorResponse},
    },
    summary="Get personalized destination suggestions",
    description="""
    Generate personalized destination suggestions based on user preferences.

    ## Scoring Algorithm (100 points total)

    The algorithm uses 7 dimensions to match destinations to user preferences:

    - **25% Style Matching**: How well the destination matches your travel style
      (chill vs intense, city vs nature, eco vs luxury, tourist vs local)
    - **30% Interest Alignment**: How well the destination matches your interests
      (culture, food, beach, adventure, nature, etc.)
    - **15% Must-Haves**: Whether the destination meets mandatory requirements
      (accessibility, pet-friendly, family-friendly, WiFi quality)
    - **10% Budget Alignment**: Cost of living vs your budget level
    - **10% Seasonal Relevance**: Whether it's a good season to visit
    - **5% Trending Score**: Current popularity of the destination
    - **5% Travel Context**: Bonuses for travel style and occasion

    ## Response Features

    Each suggestion includes:
    - **matchScore**: 0-100 score indicating how well the destination matches
    - **keyFactors**: 3-5 specific reasons explaining the match
    - **headline/description**: LLM-generated personalized content
    - **estimatedBudgetPerPerson**: Budget estimate for 7 days
    - **topActivities**: Top 5 activities in the destination
    - **bestSeasons**: Best times to visit

    ## Caching

    - Results are cached for 1 hour based on preferences hash
    - Use `force_refresh=true` to bypass cache

    ## Example Request

    ```json
    {
        "userLocation": {"city": "Paris", "country": "France"},
        "styleAxes": {
            "chillVsIntense": 30,
            "cityVsNature": 60,
            "ecoVsLuxury": 40,
            "touristVsLocal": 70
        },
        "interests": ["food", "culture", "beach"],
        "mustHaves": {"familyFriendly": true},
        "travelStyle": "family",
        "budgetLevel": "comfort",
        "travelMonth": 4
    }
    ```
    """,
)
async def suggest_destinations(
    preferences: UserPreferencesPayload,
    limit: int = Query(
        3,
        ge=1,
        le=5,
        description="Number of suggestions to return (1-5)",
    ),
    force_refresh: bool = Query(
        False,
        description="Bypass cache and generate fresh suggestions",
    ),
    service=Depends(get_suggestions_service),
):
    """
    Generate personalized destination suggestions.

    Returns a list of country destinations ranked by match score,
    with personalized content and budget estimates.
    """
    try:
        response = await service.get_suggestions(
            preferences=preferences,
            limit=limit,
            force_refresh=force_refresh,
        )
        return response

    except ValueError as e:
        logger.warning(f"Invalid preferences: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_PREFERENCES",
                    "message": str(e),
                    "details": None,
                },
            },
        )

    except Exception as e:
        logger.error(f"Error generating suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Failed to generate destination suggestions",
                    "details": None,
                },
            },
        )


@router.get(
    "/suggest/health",
    summary="Health check for destinations service",
    description="Check if the destination suggestions service is available and configured.",
)
async def health_check(request: Request):
    """
    Health check endpoint for the destination suggestions service.

    Returns service status and configuration info.
    """
    service = request.app.state.destination_suggestions_service

    if service is None:
        return {
            "status": "unavailable",
            "service": "destination_suggestions",
            "message": "Service not initialized",
            "llm_enabled": False,
            "profiles_loaded": 0,
        }

    # Try to get profile count
    try:
        profiles = await service.profiles.get_all_profiles()
        profile_count = len(profiles)
    except Exception:
        profile_count = 0

    return {
        "status": "healthy" if profile_count > 0 else "degraded",
        "service": "destination_suggestions",
        "llm_enabled": service.llm is not None,
        "profiles_loaded": profile_count,
        "cache_ttl_seconds": service.cache_ttl,
    }
