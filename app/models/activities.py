"""Pydantic models for activities API."""

from __future__ import annotations
from pydantic import BaseModel, Field, validator, ConfigDict
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


class SortOrder(str, Enum):
    """Sort order."""
    ASC = "asc"
    DESC = "desc"


class SearchType(str, Enum):
    """Type of search to perform (deprecated - use SearchMode)."""
    ACTIVITIES = "activities"
    ATTRACTIONS = "attractions"


class SearchMode(str, Enum):
    """Search mode for unified search."""
    ACTIVITIES = "activities"
    ATTRACTIONS = "attractions"
    BOTH = "both"  # Return both activities and attractions mixed


# ============================================================================
# INPUT MODELS (REQUEST)
# ============================================================================

class GeoBounds(BaseModel):
    """Bounding box for map viewport search."""
    north: float = Field(..., ge=-90, le=90, description="Northern latitude bound")
    south: float = Field(..., ge=-90, le=90, description="Southern latitude bound")
    east: float = Field(..., ge=-180, le=180, description="Eastern longitude bound")
    west: float = Field(..., ge=-180, le=180, description="Western longitude bound")


class GeoInput(BaseModel):
    """Geographic input - supports point search OR bounds search."""
    # Point search (existing - for backward compatibility)
    lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude for point search")
    lon: Optional[float] = Field(None, ge=-180, le=180, description="Longitude for point search")
    radius_km: Optional[float] = Field(None, ge=1, le=50, description="Search radius in km (max 50km)")

    # Bounds search (NEW - for map viewport search)
    bounds: Optional[GeoBounds] = Field(None, description="Bounding box for viewport search")


class LocationInput(BaseModel):
    """Location input - accepts city, destination_id, or geo."""
    model_config = ConfigDict(populate_by_name=True)

    city: Optional[str] = Field(None, min_length=2)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    destination_id: Optional[str] = None
    geo: Optional[GeoInput] = Field(None, alias="coordinates")

    @validator("country_code")
    def uppercase_country_code(cls, v):
        return v.upper() if v else v


class DateRange(BaseModel):
    """Date range for activity search."""
    start: date
    end: Optional[date] = None


class PriceRange(BaseModel):
    """Price range filter."""
    min: Optional[float] = Field(None, ge=0)
    max: Optional[float] = Field(None, ge=0)


class DurationRange(BaseModel):
    """Duration range filter in minutes."""
    min: Optional[int] = Field(None, ge=0)
    max: Optional[int] = Field(None, ge=0)


class ActivityFilters(BaseModel):
    """Filters for activity search."""
    categories: Optional[List[str]] = None
    price_range: Optional[PriceRange] = None
    rating_min: Optional[float] = Field(None, ge=0, le=5)
    duration_minutes: Optional[DurationRange] = None
    flags: Optional[List[str]] = None


class Sorting(BaseModel):
    """Sorting options."""
    sort_by: SortBy = Field(default=SortBy.DEFAULT)
    order: SortOrder = Field(default=SortOrder.DESC)


class Pagination(BaseModel):
    """Pagination options."""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=50)


class ActivitySearchRequest(BaseModel):
    """Request model for activity search."""
    search_type: SearchType = Field(default=SearchType.ACTIVITIES, description="Type of search: activities or attractions (deprecated)")
    search_mode: SearchMode = Field(default=SearchMode.BOTH, description="Search mode: activities, attractions, or both mixed")
    location: LocationInput
    dates: DateRange
    filters: Optional[ActivityFilters] = None
    sorting: Optional[Sorting] = Field(default_factory=Sorting)
    pagination: Optional[Pagination] = Field(default_factory=Pagination)
    currency: str = Field(default="EUR", pattern="^[A-Z]{3}$")
    language: str = Field(default="en", pattern="^[a-z]{2}$")


# ============================================================================
# OUTPUT MODELS (RESPONSE)
# ============================================================================

class ImageVariants(BaseModel):
    """Image variants in different sizes."""
    small: Optional[str] = None
    medium: Optional[str] = None
    large: Optional[str] = None


class ActivityImage(BaseModel):
    """Activity image."""
    url: str
    is_cover: bool = False
    variants: ImageVariants = Field(default_factory=ImageVariants)


class ActivityPricing(BaseModel):
    """Activity pricing information."""
    from_price: Optional[float] = None
    currency: str
    original_price: Optional[float] = None
    is_discounted: bool = False


class ActivityRating(BaseModel):
    """Activity rating information."""
    average: float = Field(..., ge=0, le=5)
    count: int = Field(..., ge=0)


class ActivityDuration(BaseModel):
    """Activity duration."""
    minutes: int = Field(..., ge=0)
    formatted: str


class ActivityLocation(BaseModel):
    """Activity location information."""
    destination: str
    country: str
    coordinates: Optional[dict] = None
    coordinates_precision: Optional[str] = None  # "precise" | "attraction" | "geocoded" | "dispersed" | null
    coordinates_source: Optional[str] = None  # Source of coordinates (e.g., "viator_logistics", "attraction_12345", "geoapify", "deterministic_hash")
    _dispersion_metadata: Optional[dict] = None  # Internal: {"offset_km": float, "angle_degrees": int, "city_radius_km": float}


class Activity(BaseModel):
    """Simplified activity model for frontend consumption."""
    id: str
    title: str
    description: str
    images: List[ActivityImage] = Field(default_factory=list)
    pricing: ActivityPricing
    rating: ActivityRating
    duration: ActivityDuration
    categories: List[str] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)
    booking_url: str
    confirmation_type: str
    location: ActivityLocation
    availability: str = "available"
    type: Optional[str] = Field(None, description="Type: 'activity' or 'attraction'")
    product_codes: Optional[List[str]] = Field(None, description="Related product codes (for attractions)")
    distance_from_search: Optional[float] = Field(None, description="Distance in km from search coordinates (for geo searches)")


class SearchResults(BaseModel):
    """Search results container with v2 separation support."""
    # V1 fields (backward compatibility - deprecated)
    total: int = Field(..., description="Total results (deprecated - use total_activities + total_attractions)")
    page: int
    limit: int
    activities: List[Activity] = Field(default_factory=list, description="Combined list (deprecated - use activities_list + attractions)")

    # V2 fields (NEW - separate activities and attractions)
    attractions: List[Activity] = Field(default_factory=list, description="Top attractions for map pins only")
    activities_list: List[Activity] = Field(default_factory=list, description="Filtered activities for list display")
    total_attractions: int = Field(default=0, description="Total attractions available")
    total_activities: int = Field(default=0, description="Total activities available")
    has_more: bool = Field(default=False, description="Whether more results are available for pagination")


class LocationResolution(BaseModel):
    """Resolved location information."""
    matched_city: Optional[str] = None
    destination_id: str
    coordinates: Optional[dict] = None
    match_score: Optional[float] = None
    distance_km: Optional[float] = None
    search_type: Optional[str] = Field(None, description="Type of search performed: 'city' or 'geo'")


class CacheInfo(BaseModel):
    """Cache information."""
    cached: bool
    cached_at: Optional[str] = None
    expires_at: Optional[str] = None
    cursor_id: Optional[str] = Field(None, description="Cursor ID for stateful pagination (unified search)")


class ActivitySearchResponse(BaseModel):
    """Response model for activity search."""
    success: bool = True
    location: LocationResolution
    filters_applied: dict
    results: SearchResults
    cache_info: CacheInfo


# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorDetail(BaseModel):
    """Error detail information."""
    code: str
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: ErrorDetail
