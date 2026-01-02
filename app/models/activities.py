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


# ============================================================================
# INPUT MODELS (REQUEST)
# ============================================================================

class GeoInput(BaseModel):
    """Geographic coordinates input."""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(default=50, ge=1, le=200)


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
    from_price: float
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


class SearchResults(BaseModel):
    """Search results container."""
    total: int
    page: int
    limit: int
    activities: List[Activity]


class LocationResolution(BaseModel):
    """Resolved location information."""
    matched_city: Optional[str] = None
    destination_id: str
    coordinates: Optional[dict] = None
    match_score: Optional[float] = None
    distance_km: Optional[float] = None


class CacheInfo(BaseModel):
    """Cache information."""
    cached: bool
    cached_at: Optional[str] = None
    expires_at: Optional[str] = None


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
