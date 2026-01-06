"""Pydantic models for hotels API."""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict
from datetime import date
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class HotelSortBy(str, Enum):
    """Sort options for hotels."""
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    RATING = "rating"
    DISTANCE = "distance"
    POPULARITY = "popularity"


class PropertyType(str, Enum):
    """Hotel property types."""
    HOTEL = "hotel"
    APARTMENT = "apartment"
    HOSTEL = "hostel"
    BED_AND_BREAKFAST = "bed_and_breakfast"
    VILLA = "villa"
    RESORT = "resort"
    GUEST_HOUSE = "guest_house"


class HotelAmenity(str, Enum):
    """Normalized amenity codes."""
    WIFI = "wifi"
    PARKING = "parking"
    BREAKFAST = "breakfast"
    POOL = "pool"
    GYM = "gym"
    SPA = "spa"
    RESTAURANT = "restaurant"
    BAR = "bar"
    AC = "ac"
    KITCHEN = "kitchen"


# ============================================================================
# INPUT MODELS (REQUEST)
# ============================================================================

class RoomOccupancy(BaseModel):
    """Room occupancy details."""
    adults: int = Field(default=2, ge=1, le=10, description="Number of adults")
    childrenAges: List[int] = Field(default_factory=list, description="Ages of children")


class HotelFilters(BaseModel):
    """Filters for hotel search."""
    priceMin: Optional[int] = Field(None, ge=0, description="Minimum price per night")
    priceMax: Optional[int] = Field(None, ge=0, description="Maximum price per night")
    types: Optional[List[PropertyType]] = Field(None, description="Property types filter")
    minRating: Optional[float] = Field(None, ge=0, le=10, description="Minimum rating (0-10)")
    minStars: Optional[int] = Field(None, ge=1, le=5, description="Minimum star rating")
    amenities: Optional[List[HotelAmenity]] = Field(None, description="Required amenities")


class HotelSearchRequest(BaseModel):
    """Request model for hotel search."""
    model_config = ConfigDict(populate_by_name=True)

    city: str = Field(..., min_length=2, description="City name")
    countryCode: str = Field(..., min_length=2, max_length=2, description="ISO country code")
    lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude (optional)")
    lng: Optional[float] = Field(None, ge=-180, le=180, description="Longitude (optional)")
    checkIn: date = Field(..., description="Check-in date")
    checkOut: date = Field(..., description="Check-out date")
    rooms: List[RoomOccupancy] = Field(default_factory=lambda: [RoomOccupancy()], description="Room configurations")
    filters: Optional[HotelFilters] = None
    sort: HotelSortBy = Field(default=HotelSortBy.POPULARITY, description="Sort order")
    limit: int = Field(default=30, ge=1, le=100, description="Results limit")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    currency: str = Field(default="EUR", pattern="^[A-Z]{3}$")
    locale: str = Field(default="en", pattern="^[a-z]{2}$")

    @field_validator("countryCode")
    @classmethod
    def uppercase_country_code(cls, v):
        return v.upper() if v else v


class HotelDetailsQuery(BaseModel):
    """Query parameters for hotel details."""
    checkIn: date
    checkOut: date
    rooms: str = Field(..., description="Format: adults-childAge1-childAge2,... per room")
    currency: str = Field(default="EUR", pattern="^[A-Z]{3}$")
    locale: str = Field(default="en", pattern="^[a-z]{2}$")


class CityPrice(BaseModel):
    """City with coordinates for map prices."""
    city: str
    countryCode: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class MapPricesRequest(BaseModel):
    """Request model for map prices."""
    cities: List[CityPrice] = Field(..., max_length=20, description="Cities to get prices for (max 20)")
    checkIn: date
    checkOut: date
    rooms: List[RoomOccupancy] = Field(default_factory=lambda: [RoomOccupancy()])
    currency: str = Field(default="EUR", pattern="^[A-Z]{3}$")


# ============================================================================
# OUTPUT MODELS (RESPONSE)
# ============================================================================

class HotelResult(BaseModel):
    """Hotel search result."""
    id: str
    name: str
    lat: float
    lng: float
    imageUrl: Optional[str] = None
    stars: Optional[int] = Field(None, ge=1, le=5)
    rating: Optional[float] = Field(None, ge=0, le=10)
    reviewCount: int = 0
    pricePerNight: float
    totalPrice: Optional[float] = None
    currency: str
    address: str
    distanceFromCenter: Optional[float] = None  # Distance in km
    amenities: List[str] = Field(default_factory=list)
    bookingUrl: Optional[str] = None


class HotelSearchResults(BaseModel):
    """Hotel search results container."""
    hotels: List[HotelResult] = Field(default_factory=list)
    total: int = 0
    hasMore: bool = False


class HotelSearchResponse(BaseModel):
    """Response model for hotel search."""
    success: bool = True
    results: HotelSearchResults
    filters_applied: dict = Field(default_factory=dict)
    cache_info: Optional[dict] = None


# Hotel Details Models

class AmenityDetail(BaseModel):
    """Amenity with label."""
    code: str
    label: str


class RatingBreakdown(BaseModel):
    """Sous-ratings détaillés (scores 0-10)."""
    cleanliness: Optional[float] = None     # Propreté
    staff: Optional[float] = None           # Personnel
    location: Optional[float] = None        # Emplacement
    facilities: Optional[float] = None      # Équipements
    comfort: Optional[float] = None         # Confort
    valueForMoney: Optional[float] = None   # Rapport qualité/prix


class PropertyBadge(BaseModel):
    """Badge/avantage visible de l'hôtel."""
    code: str       # "free_breakfast", "free_cancellation", "pool", "spa"
    label: str      # "Petit-déjeuner inclus", "Annulation gratuite"
    icon: Optional[str] = None  # Hint icône: "coffee", "shield", "waves"


class HotelPolicies(BaseModel):
    """Hotel policies."""
    checkIn: Optional[str] = None
    checkOut: Optional[str] = None
    cancellation: Optional[str] = None


class RoomOption(BaseModel):
    """Room option with pricing."""
    id: str
    name: str
    description: Optional[str] = None
    maxOccupancy: int = 2
    bedType: Optional[str] = None
    pricePerNight: float
    totalPrice: float
    amenities: List[str] = Field(default_factory=list)
    cancellationFree: bool = False


class HotelDetails(BaseModel):
    """Full hotel details."""
    id: str
    name: str
    lat: float
    lng: float
    stars: Optional[int] = None
    rating: Optional[float] = None
    reviewCount: int = 0
    address: str
    distanceFromCenter: Optional[float] = None  # Distance in km
    description: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    amenities: List[AmenityDetail] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    badges: List[PropertyBadge] = Field(default_factory=list)
    ratingBreakdown: Optional[RatingBreakdown] = None
    policies: Optional[HotelPolicies] = None
    rooms: List[RoomOption] = Field(default_factory=list)
    bookingUrl: Optional[str] = None


class HotelDetailsResponse(BaseModel):
    """Response model for hotel details."""
    success: bool = True
    hotel: Optional[HotelDetails] = None
    cache_info: Optional[dict] = None


# Map Prices Models

class CityPriceResult(BaseModel):
    """Price result for a city."""
    minPrice: Optional[float] = None
    currency: str


class MapPricesResponse(BaseModel):
    """Response model for map prices."""
    success: bool = True
    prices: Dict[str, Optional[CityPriceResult]] = Field(default_factory=dict)
    cache_info: Optional[dict] = None


# ============================================================================
# ERROR MODELS
# ============================================================================

class HotelErrorDetail(BaseModel):
    """Error detail information."""
    code: str
    message: str
    details: Optional[dict] = None


class HotelErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: HotelErrorDetail
