# Référence Complète des Modèles Pydantic

## 📦 Modèles pour l'API Publique

### Fichier : `app/models/activities.py`

```python
"""Pydantic models for activities API."""

from __future__ import annotations
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class SortBy(str, Enum):
    """Sort options for activities."""
    DEFAULT = "default"
    RATING = "rating"
    PRICE = "price"
    DURATION = "duration"


class SortOrder(str, Enum):
    """Sort order."""
    ASC = "asc"
    DESC = "desc"


class ConfirmationType(str, Enum):
    """Booking confirmation types."""
    INSTANT = "INSTANT"
    MANUAL = "MANUAL"


class ActivityFlag(str, Enum):
    """Activity flags."""
    FREE_CANCELLATION = "FREE_CANCELLATION"
    SKIP_THE_LINE = "SKIP_THE_LINE"
    PRIVATE_TOUR = "PRIVATE_TOUR"
    SPECIAL_OFFER = "SPECIAL_OFFER"
    LIKELY_TO_SELL_OUT = "LIKELY_TO_SELL_OUT"
    NEW_ON_VIATOR = "NEW_ON_VIATOR"


class AvailabilityStatus(str, Enum):
    """Availability status."""
    AVAILABLE = "available"
    LIMITED = "limited"
    SOLD_OUT = "sold_out"
    UNKNOWN = "unknown"


# ============================================================================
# INPUT MODELS (REQUEST)
# ============================================================================

class GeoInput(BaseModel):
    """Geographic coordinates input."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    radius_km: float = Field(
        default=50,
        ge=1,
        le=200,
        description="Search radius in kilometers"
    )


class LocationInput(BaseModel):
    """
    Location input - accepts one of three options.

    Examples:
        - By city: {"city": "Paris", "country_code": "FR"}
        - By destination ID: {"destination_id": "77"}
        - By geo: {"geo": {"lat": 48.8566, "lon": 2.3522, "radius_km": 50}}
    """
    city: Optional[str] = Field(None, min_length=2, description="City name")
    country_code: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code"
    )
    destination_id: Optional[str] = Field(None, description="Viator destination ID")
    geo: Optional[GeoInput] = Field(None, description="Geographic coordinates")

    @validator("country_code")
    def uppercase_country_code(cls, v):
        """Convert country code to uppercase."""
        return v.upper() if v else v

    @validator("city")
    def validate_location_provided(cls, v, values):
        """Ensure at least one location option is provided."""
        if not v and not values.get("destination_id") and not values.get("geo"):
            raise ValueError(
                "At least one location option must be provided: "
                "city, destination_id, or geo"
            )
        return v


class DateRange(BaseModel):
    """Date range for activity search."""
    start: date = Field(..., description="Start date (YYYY-MM-DD)")
    end: Optional[date] = Field(None, description="End date (YYYY-MM-DD), optional")

    @validator("end")
    def validate_end_after_start(cls, v, values):
        """Ensure end date is after start date."""
        if v and "start" in values and v < values["start"]:
            raise ValueError("end date must be after start date")
        return v


class PriceRange(BaseModel):
    """Price range filter."""
    min: Optional[float] = Field(None, ge=0, description="Minimum price")
    max: Optional[float] = Field(None, ge=0, description="Maximum price")

    @validator("max")
    def validate_max_greater_than_min(cls, v, values):
        """Ensure max price is greater than min price."""
        if v and "min" in values and values["min"] and v < values["min"]:
            raise ValueError("max price must be greater than min price")
        return v


class DurationRange(BaseModel):
    """Duration range filter in minutes."""
    min: Optional[int] = Field(None, ge=0, description="Minimum duration in minutes")
    max: Optional[int] = Field(None, ge=0, description="Maximum duration in minutes")

    @validator("max")
    def validate_max_greater_than_min(cls, v, values):
        """Ensure max duration is greater than min duration."""
        if v and "min" in values and values["min"] and v < values["min"]:
            raise ValueError("max duration must be greater than min duration")
        return v


class ActivityFilters(BaseModel):
    """Filters for activity search."""
    categories: Optional[List[str]] = Field(
        None,
        description="List of category IDs (e.g., ['food', 'museum', 'adventure'])"
    )
    price_range: Optional[PriceRange] = Field(None, description="Price range filter")
    rating_min: Optional[float] = Field(
        None,
        ge=0,
        le=5,
        description="Minimum rating (0-5)"
    )
    duration_minutes: Optional[DurationRange] = Field(
        None,
        description="Duration range in minutes"
    )
    flags: Optional[List[ActivityFlag]] = Field(
        None,
        description="Activity flags (e.g., FREE_CANCELLATION, SKIP_THE_LINE)"
    )


class Sorting(BaseModel):
    """Sorting options."""
    sort_by: SortBy = Field(
        default=SortBy.DEFAULT,
        description="Sort field"
    )
    order: SortOrder = Field(
        default=SortOrder.DESC,
        description="Sort order"
    )


class Pagination(BaseModel):
    """Pagination options."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    limit: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Results per page (max 50)"
    )


class ActivitySearchRequest(BaseModel):
    """
    Request model for activity search.

    Example:
        ```json
        {
          "location": {
            "city": "Paris",
            "country_code": "FR"
          },
          "dates": {
            "start": "2026-03-15",
            "end": "2026-03-20"
          },
          "filters": {
            "categories": ["food", "museum"],
            "price_range": {"min": 10, "max": 200},
            "rating_min": 4.0
          },
          "sorting": {
            "sort_by": "rating",
            "order": "desc"
          },
          "pagination": {
            "page": 1,
            "limit": 20
          },
          "currency": "EUR",
          "language": "fr"
        }
        ```
    """
    location: LocationInput
    dates: DateRange
    filters: Optional[ActivityFilters] = None
    sorting: Optional[Sorting] = Field(default_factory=Sorting)
    pagination: Optional[Pagination] = Field(default_factory=Pagination)
    currency: str = Field(
        default="EUR",
        pattern="^[A-Z]{3}$",
        description="ISO 4217 currency code (e.g., EUR, USD, GBP)"
    )
    language: str = Field(
        default="en",
        pattern="^[a-z]{2}$",
        description="ISO 639-1 language code (e.g., en, fr, es)"
    )


class AvailabilityCheckRequest(BaseModel):
    """Request to check real-time availability for an activity."""
    activity_id: str = Field(..., description="Activity product code")
    date: date = Field(..., description="Travel date (YYYY-MM-DD)")
    travelers: dict = Field(
        ...,
        description="Travelers breakdown (e.g., {'adults': 2, 'children': 1})"
    )
    currency: str = Field(default="EUR", pattern="^[A-Z]{3}$")

    class Config:
        schema_extra = {
            "example": {
                "activity_id": "5010SYDNEY",
                "date": "2026-03-15",
                "travelers": {
                    "adults": 2,
                    "children": 1,
                    "infants": 0
                },
                "currency": "EUR"
            }
        }


# ============================================================================
# OUTPUT MODELS (RESPONSE)
# ============================================================================

class ImageVariants(BaseModel):
    """Image variants in different sizes."""
    small: Optional[str] = Field(None, description="Small image URL (~200px)")
    medium: Optional[str] = Field(None, description="Medium image URL (~600px)")
    large: Optional[str] = Field(None, description="Large image URL (>600px)")


class ActivityImage(BaseModel):
    """Activity image."""
    url: str = Field(..., description="Primary image URL")
    is_cover: bool = Field(default=False, description="Whether this is the cover image")
    variants: ImageVariants = Field(
        default_factory=ImageVariants,
        description="Image size variants"
    )


class ActivityPricing(BaseModel):
    """Activity pricing information."""
    from_price: float = Field(..., description="Starting price per person")
    currency: str = Field(..., description="Currency code")
    original_price: Optional[float] = Field(
        None,
        description="Original price before discount (if applicable)"
    )
    is_discounted: bool = Field(
        default=False,
        description="Whether the activity is currently discounted"
    )


class ActivityRating(BaseModel):
    """Activity rating information."""
    average: float = Field(..., ge=0, le=5, description="Average rating (0-5)")
    count: int = Field(..., ge=0, description="Total number of reviews")


class ActivityDuration(BaseModel):
    """Activity duration."""
    minutes: int = Field(..., ge=0, description="Duration in minutes")
    formatted: str = Field(..., description="Human-readable duration (e.g., '3 hours')")


class ActivityLocation(BaseModel):
    """Activity location information."""
    destination: str = Field(..., description="Destination name (e.g., 'Paris')")
    country: str = Field(..., description="Country name")
    coordinates: Optional[dict] = Field(None, description="Lat/lon coordinates if available")


class Activity(BaseModel):
    """
    Simplified activity model for frontend consumption.

    This is the core activity object returned by the API.
    """
    id: str = Field(..., description="Unique product code")
    title: str = Field(..., description="Activity title")
    description: str = Field(..., description="Activity description")
    images: List[ActivityImage] = Field(default_factory=list, description="Activity images")
    pricing: ActivityPricing = Field(..., description="Pricing information")
    rating: ActivityRating = Field(..., description="Rating and review count")
    duration: ActivityDuration = Field(..., description="Activity duration")
    categories: List[str] = Field(
        default_factory=list,
        description="Category tags (e.g., ['food', 'museum'])"
    )
    flags: List[str] = Field(
        default_factory=list,
        description="Activity flags (e.g., FREE_CANCELLATION)"
    )
    booking_url: str = Field(..., description="URL to book this activity")
    confirmation_type: str = Field(..., description="Booking confirmation type")
    location: ActivityLocation = Field(..., description="Location information")
    availability: AvailabilityStatus = Field(
        default=AvailabilityStatus.UNKNOWN,
        description="Availability status"
    )

    class Config:
        schema_extra = {
            "example": {
                "id": "5010SYDNEY",
                "title": "Louvre Museum Skip-the-Line Ticket",
                "description": "Explore the world's largest art museum...",
                "images": [
                    {
                        "url": "https://cdn.viator.com/...",
                        "is_cover": True,
                        "variants": {
                            "small": "https://...",
                            "medium": "https://...",
                            "large": "https://..."
                        }
                    }
                ],
                "pricing": {
                    "from_price": 45.00,
                    "currency": "EUR",
                    "original_price": 60.00,
                    "is_discounted": True
                },
                "rating": {
                    "average": 4.7,
                    "count": 1523
                },
                "duration": {
                    "minutes": 180,
                    "formatted": "3h"
                },
                "categories": ["museum", "art", "culture"],
                "flags": ["SKIP_THE_LINE", "FREE_CANCELLATION"],
                "booking_url": "https://www.viator.com/tours/...",
                "confirmation_type": "INSTANT",
                "location": {
                    "destination": "Paris",
                    "country": "France"
                },
                "availability": "available"
            }
        }


class SearchResults(BaseModel):
    """Search results container."""
    total: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Results per page")
    activities: List[Activity] = Field(..., description="List of activities")


class LocationResolution(BaseModel):
    """Resolved location information."""
    matched_city: Optional[str] = Field(None, description="Matched city name")
    destination_id: str = Field(..., description="Viator destination ID")
    coordinates: Optional[dict] = Field(None, description="Coordinates if provided")
    match_score: Optional[float] = Field(
        None,
        description="Fuzzy match score (0-100) if city name was provided"
    )
    distance_km: Optional[float] = Field(
        None,
        description="Distance in km if geo search was used"
    )


class CacheInfo(BaseModel):
    """Cache information."""
    cached: bool = Field(..., description="Whether result was served from cache")
    cached_at: Optional[str] = Field(None, description="ISO timestamp when cached")
    expires_at: Optional[str] = Field(None, description="ISO timestamp when cache expires")


class ActivitySearchResponse(BaseModel):
    """
    Response model for activity search.

    Example:
        ```json
        {
          "success": true,
          "location": {
            "matched_city": "Paris",
            "destination_id": "77",
            "coordinates": null,
            "match_score": 100
          },
          "filters_applied": {
            "categories": ["food", "museum"],
            "price_range": {"min": 10, "max": 200}
          },
          "results": {
            "total": 234,
            "page": 1,
            "limit": 20,
            "activities": [...]
          },
          "cache_info": {
            "cached": false,
            "cached_at": null,
            "expires_at": null
          }
        }
        ```
    """
    success: bool = Field(default=True, description="Whether request was successful")
    location: LocationResolution = Field(..., description="Resolved location info")
    filters_applied: dict = Field(..., description="Summary of applied filters")
    results: SearchResults = Field(..., description="Search results")
    cache_info: CacheInfo = Field(..., description="Cache information")


class ActivityDetails(BaseModel):
    """Full activity details (extended version of Activity)."""
    # All fields from Activity
    id: str
    title: str
    description: str
    images: List[ActivityImage]
    pricing: ActivityPricing
    rating: ActivityRating
    duration: ActivityDuration
    categories: List[str]
    flags: List[str]
    booking_url: str
    confirmation_type: str
    location: ActivityLocation
    availability: AvailabilityStatus

    # Extended fields
    itinerary: Optional[dict] = Field(None, description="Detailed itinerary")
    cancellation_policy: Optional[dict] = Field(None, description="Cancellation policy")
    included: Optional[List[str]] = Field(None, description="What's included")
    excluded: Optional[List[str]] = Field(None, description="What's excluded")
    meeting_point: Optional[str] = Field(None, description="Meeting point details")
    important_info: Optional[str] = Field(None, description="Important information")


class ActivityDetailsResponse(BaseModel):
    """Response for activity details endpoint."""
    success: bool = Field(default=True)
    activity: ActivityDetails = Field(..., description="Full activity details")
    cache_info: CacheInfo


class AvailabilityOption(BaseModel):
    """Availability option for a specific time slot."""
    option_id: str = Field(..., description="Option identifier")
    time: str = Field(..., description="Start time (HH:MM)")
    price: dict = Field(..., description="Pricing breakdown")
    availability: str = Field(..., description="Availability status")
    spots_remaining: Optional[int] = Field(None, description="Spots remaining")


class AvailabilityCheckResponse(BaseModel):
    """Response for availability check."""
    success: bool = Field(default=True)
    available: bool = Field(..., description="Whether activity is available")
    options: List[AvailabilityOption] = Field(
        default_factory=list,
        description="Available time slot options"
    )


# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorDetail(BaseModel):
    """Error detail information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(default=False)
    error: ErrorDetail = Field(..., description="Error information")

    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "DESTINATION_NOT_FOUND",
                    "message": "Unable to find destination for city 'Parisx'. Did you mean 'Paris'?",
                    "details": {
                        "city_query": "Parisx",
                        "suggestions": ["Paris", "Parma"]
                    }
                }
            }
        }


# ============================================================================
# DESTINATION MODELS
# ============================================================================

class Destination(BaseModel):
    """Destination model."""
    id: str = Field(..., description="Viator destination ID")
    name: str = Field(..., description="Destination name")
    country: str = Field(..., description="Country name")
    country_code: str = Field(..., description="ISO country code")
    type: str = Field(..., description="Destination type (city, country, region)")
    coordinates: Optional[dict] = Field(None, description="Lat/lon coordinates")
    activity_count: int = Field(default=0, description="Number of activities")


class DestinationsResponse(BaseModel):
    """Response for destinations list."""
    success: bool = Field(default=True)
    destinations: List[Destination] = Field(..., description="List of destinations")
    cache_info: CacheInfo


# ============================================================================
# CATEGORY MODELS
# ============================================================================

class Category(BaseModel):
    """Category/tag model."""
    id: str = Field(..., description="Simplified category ID (e.g., 'food')")
    name: str = Field(..., description="Category name")
    name_translations: Optional[dict] = Field(
        None,
        description="Translations (e.g., {'fr': 'Gastronomie'})"
    )
    viator_tags: List[int] = Field(..., description="Mapped Viator tag IDs")
    icon: Optional[str] = Field(None, description="Emoji icon")


class CategoriesResponse(BaseModel):
    """Response for categories list."""
    success: bool = Field(default=True)
    categories: List[Category] = Field(..., description="List of categories")
    cache_info: CacheInfo


# ============================================================================
# RECOMMENDATIONS
# ============================================================================

class RecommendationsResponse(BaseModel):
    """Response for activity recommendations."""
    success: bool = Field(default=True)
    recommendations: List[Activity] = Field(..., description="Recommended activities")
    cache_info: CacheInfo
```

---

## 📝 Constantes et Mappings

### Fichier : `app/core/constants.py`

```python
"""Constants and mappings for Viator API."""

# Supported currencies
SUPPORTED_CURRENCIES = [
    "AUD", "BRL", "CAD", "CHF", "DKK", "EUR", "GBP",
    "HKD", "INR", "JPY", "NOK", "NZD", "SEK", "SGD",
    "TWD", "USD", "ZAR"
]

# Supported languages
SUPPORTED_LANGUAGES = [
    "en", "fr", "es", "de", "it", "pt", "nl", "sv",
    "da", "no", "fi", "pl", "ru", "ja", "zh", "ko"
]

# Activity flags
ACTIVITY_FLAGS = [
    "NEW_ON_VIATOR",
    "FREE_CANCELLATION",
    "SKIP_THE_LINE",
    "PRIVATE_TOUR",
    "SPECIAL_OFFER",
    "LIKELY_TO_SELL_OUT"
]

# Sort options mapping
SORT_MAPPING = {
    "default": "DEFAULT",
    "rating": "TRAVELER_RATING",
    "price": "PRICE",
    "duration": "ITINERARY_DURATION",
    "date_added": "DATE_ADDED"
}

# Simplified category to Viator tags mapping
# Note: In production, this should be stored in MongoDB and fetched dynamically
CATEGORY_TAG_MAPPING = {
    "food": {
        "name": "Food & Dining",
        "name_translations": {
            "fr": "Gastronomie",
            "es": "Gastronomía",
            "de": "Essen & Trinken"
        },
        "viator_tags": [21972, 21973, 21974],
        "icon": "🍴"
    },
    "museum": {
        "name": "Museums",
        "name_translations": {
            "fr": "Musées",
            "es": "Museos",
            "de": "Museen"
        },
        "viator_tags": [21975],
        "icon": "🏛️"
    },
    "art": {
        "name": "Art & Culture",
        "name_translations": {
            "fr": "Art & Culture",
            "es": "Arte y Cultura",
            "de": "Kunst & Kultur"
        },
        "viator_tags": [21976, 21977],
        "icon": "🎨"
    },
    "adventure": {
        "name": "Adventure & Outdoor",
        "name_translations": {
            "fr": "Aventure & Plein air",
            "es": "Aventura y Aire libre",
            "de": "Abenteuer & Outdoor"
        },
        "viator_tags": [21980, 21981],
        "icon": "⛰️"
    },
    "nature": {
        "name": "Nature & Wildlife",
        "name_translations": {
            "fr": "Nature & Faune",
            "es": "Naturaleza y Vida Silvestre",
            "de": "Natur & Tierwelt"
        },
        "viator_tags": [21985],
        "icon": "🌿"
    },
    "tours": {
        "name": "City Tours",
        "name_translations": {
            "fr": "Visites de la ville",
            "es": "Tours por la ciudad",
            "de": "Stadtführungen"
        },
        "viator_tags": [21990],
        "icon": "🚌"
    },
    "water": {
        "name": "Water Activities",
        "name_translations": {
            "fr": "Activités nautiques",
            "es": "Actividades acuáticas",
            "de": "Wasseraktivitäten"
        },
        "viator_tags": [21995],
        "icon": "🌊"
    },
    "nightlife": {
        "name": "Nightlife",
        "name_translations": {
            "fr": "Vie nocturne",
            "es": "Vida nocturna",
            "de": "Nachtleben"
        },
        "viator_tags": [22000],
        "icon": "🌃"
    },
    "shopping": {
        "name": "Shopping",
        "name_translations": {
            "fr": "Shopping",
            "es": "Compras",
            "de": "Einkaufen"
        },
        "viator_tags": [22005],
        "icon": "🛍️"
    }
}

# Error codes
ERROR_CODES = {
    "DESTINATION_NOT_FOUND": "Unable to find destination",
    "INVALID_DATE_RANGE": "Invalid date range provided",
    "INVALID_LOCATION": "Invalid location input",
    "VIATOR_API_ERROR": "Error communicating with Viator API",
    "CACHE_ERROR": "Cache service error",
    "DATABASE_ERROR": "Database error"
}

# Cache TTLs (seconds)
CACHE_TTL = {
    "activities_search": 604800,  # 7 days
    "activity_details": 604800,   # 7 days
    "availability": 3600,         # 1 hour
    "destinations": 2592000,      # 30 days
    "categories": 2592000         # 30 days
}
```

---

## 🎯 Utilisation des Modèles

### Exemple dans une Route FastAPI

```python
from fastapi import APIRouter, HTTPException, Depends
from app.models.activities import (
    ActivitySearchRequest,
    ActivitySearchResponse,
    ErrorResponse
)
from app.services.activities_service import ActivitiesService

router = APIRouter(prefix="/api/v1/activities", tags=["Activities"])


@router.post(
    "/search",
    response_model=ActivitySearchResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def search_activities(
    request: ActivitySearchRequest,
    activities_service: ActivitiesService = Depends(get_activities_service)
):
    """
    Search for activities based on location, dates, and filters.

    - **location**: City name, destination ID, or geo coordinates
    - **dates**: Start and end dates for the trip
    - **filters**: Optional filters (categories, price range, rating, etc.)
    - **sorting**: Sort by rating, price, or default
    - **pagination**: Page number and limit
    - **currency**: Currency code (EUR, USD, etc.)
    - **language**: Language for translations

    Returns a list of activities matching the criteria.
    """
    try:
        response = await activities_service.search_activities(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching activities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

Cette référence complète des modèles vous permettra d'avoir une API cohérente et bien typée ! 🚀
