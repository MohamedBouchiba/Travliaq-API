"""Pydantic models for destination suggestions API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# ENUMS
# ============================================================================


class TravelStyle(str, Enum):
    """Travel group composition."""

    SOLO = "solo"
    COUPLE = "couple"
    FAMILY = "family"
    FRIENDS = "friends"
    PET = "pet"


class Occasion(str, Enum):
    """Special occasion for the trip."""

    HONEYMOON = "honeymoon"
    ANNIVERSARY = "anniversary"
    BIRTHDAY = "birthday"
    VACATION = "vacation"
    WORKATION = "workation"
    OTHER = "other"


class Flexibility(str, Enum):
    """Date flexibility level."""

    FIXED = "fixed"
    FLEXIBLE = "flexible"
    VERY_FLEXIBLE = "very_flexible"


class BudgetLevel(str, Enum):
    """Budget tier."""

    BUDGET = "budget"
    COMFORT = "comfort"
    PREMIUM = "premium"
    LUXURY = "luxury"


# ============================================================================
# INPUT MODELS (REQUEST)
# ============================================================================


class UserLocation(BaseModel):
    """User's current location for flight estimates."""

    city: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lng: Optional[float] = Field(None, ge=-180, le=180)


class StyleAxes(BaseModel):
    """Travel style preferences on 0-100 scales."""

    chillVsIntense: int = Field(
        50, ge=0, le=100, description="0=Relaxed/Chill, 100=Intense/Active"
    )
    cityVsNature: int = Field(
        50, ge=0, le=100, description="0=Urban/City, 100=Nature/Outdoor"
    )
    ecoVsLuxury: int = Field(
        50, ge=0, le=100, description="0=Budget/Eco, 100=Luxury/Premium"
    )
    touristVsLocal: int = Field(
        50, ge=0, le=100, description="0=Tourist attractions, 100=Local/Authentic"
    )


class MustHaves(BaseModel):
    """Non-negotiable requirements."""

    accessibilityRequired: bool = False
    petFriendly: bool = False
    familyFriendly: bool = False
    highSpeedWifi: bool = False


class UserPreferencesPayload(BaseModel):
    """Complete user preferences for destination matching."""

    userLocation: UserLocation = Field(default_factory=UserLocation)
    styleAxes: StyleAxes = Field(default_factory=StyleAxes)
    interests: List[str] = Field(
        default_factory=list,
        description="User interests (max 5): culture, food, beach, adventure, nature, nightlife, history, art, shopping, wellness, sports",
    )
    mustHaves: MustHaves = Field(default_factory=MustHaves)
    dietaryRestrictions: List[str] = Field(default_factory=list)
    travelStyle: TravelStyle = TravelStyle.COUPLE
    occasion: Optional[Occasion] = None
    flexibility: Flexibility = Flexibility.FLEXIBLE
    budgetLevel: BudgetLevel = BudgetLevel.COMFORT
    travelMonth: Optional[int] = Field(
        None, ge=1, le=12, description="Target travel month (1-12) for seasonal scoring"
    )

    @field_validator("interests")
    @classmethod
    def validate_interests(cls, v: List[str]) -> List[str]:
        """Normalize and limit interests to 5."""
        allowed = {
            "culture",
            "food",
            "beach",
            "adventure",
            "nature",
            "nightlife",
            "history",
            "art",
            "shopping",
            "wellness",
            "sports",
        }
        normalized = [i.lower().strip() for i in v if i.strip()]
        # Keep only valid interests, max 5
        valid = [i for i in normalized if i in allowed]
        return valid[:5]


# ============================================================================
# OUTPUT MODELS (RESPONSE)
# ============================================================================


class BudgetEstimate(BaseModel):
    """Budget estimate per person per day."""

    min: int = Field(..., ge=0, description="Minimum budget in EUR per day")
    max: int = Field(..., ge=0, description="Maximum budget in EUR per day")
    currency: Literal["EUR"] = "EUR"
    duration: Literal["per_day", "7_days"] = "per_day"


class TopActivity(BaseModel):
    """Top activity in a destination."""

    name: str
    emoji: str
    category: str


class DestinationSuggestion(BaseModel):
    """Single destination suggestion with scoring justification."""

    countryCode: str = Field(..., min_length=2, max_length=2, description="ISO 2-letter code")
    countryName: str
    flagEmoji: str
    headline: str = Field(..., description="LLM-generated catchy headline (max 50 chars)")
    description: str = Field(
        ..., description="LLM-generated personalized description (max 150 chars)"
    )
    matchScore: int = Field(..., ge=0, le=100, description="0-100 match score")
    keyFactors: List[str] = Field(
        ..., description="3-5 reasons explaining why this destination matches"
    )
    estimatedBudgetPerPerson: BudgetEstimate
    topActivities: List[TopActivity] = Field(default_factory=list)
    bestSeasons: List[str] = Field(default_factory=list)
    flightDurationFromOrigin: Optional[str] = None
    flightPriceEstimate: Optional[int] = Field(
        None, description="Average round-trip flight price in EUR"
    )
    flightPriceSource: Optional[Literal["cache", "api", "estimated"]] = Field(
        None, description="Source of flight price: cache, api, or estimated"
    )
    imageUrl: Optional[str] = Field(
        None, description="URL of country cover image"
    )
    imageCredit: Optional[str] = Field(
        None, description="Photo attribution/credit"
    )


class ProfileCompleteness(BaseModel):
    """Metadata about user profile quality."""

    completionScore: int = Field(..., ge=0, le=100)
    keyFactors: List[str] = Field(default_factory=list)


class DestinationSuggestionsResponse(BaseModel):
    """Response model for destination suggestions."""

    success: bool = True
    suggestions: List[DestinationSuggestion] = Field(default_factory=list)
    generatedAt: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )
    basedOnProfile: ProfileCompleteness
    sourceAirportIata: Optional[str] = Field(
        None, description="IATA code of the nearest airport to user's location"
    )


# ============================================================================
# ERROR MODELS
# ============================================================================


class SuggestionError(BaseModel):
    """Error detail for suggestions endpoint."""

    code: str
    message: str
    details: Optional[dict] = None


class SuggestionErrorResponse(BaseModel):
    """Error response for suggestions endpoint."""

    success: bool = False
    error: SuggestionError
