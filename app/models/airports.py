"""Pydantic models for nearest airports endpoint."""

from pydantic import BaseModel, Field
from typing import Optional


class NearestAirportsRequest(BaseModel):
    """Request model for finding nearest airports to a city."""

    city: str = Field(
        ...,
        description="City name (fuzzy matching supported)",
        min_length=2,
        examples=["Paris", "Londre", "New Yor"]  # Examples with typos
    )
    limit: int = Field(
        3,
        ge=1,
        le=10,
        description="Maximum number of airports to return (default: 3)"
    )


class AirportResult(BaseModel):
    """Single airport result with distance."""

    iata: str = Field(
        ...,
        description="IATA airport code",
        examples=["CDG", "ORY", "LHR"]
    )
    name: str = Field(
        ...,
        description="Airport name",
        examples=["Paris Charles de Gaulle", "London Heathrow"]
    )
    city_name: str = Field(
        ...,
        description="Associated city name",
        examples=["Paris", "London"]
    )
    country_code: str = Field(
        ...,
        description="ISO2 country code",
        examples=["FR", "GB"]
    )
    lat: float = Field(
        ...,
        description="Latitude"
    )
    lon: float = Field(
        ...,
        description="Longitude"
    )
    distance_km: float = Field(
        ...,
        description="Distance from the queried city in kilometers"
    )


class NearestAirportsResponse(BaseModel):
    """Response model for nearest airports."""

    city_query: str = Field(
        ...,
        description="Original city query"
    )
    matched_city: str = Field(
        ...,
        description="Actual city name that was matched"
    )
    matched_city_id: str = Field(
        ...,
        description="UUID of the matched city"
    )
    match_score: float = Field(
        ...,
        description="Fuzzy match score (0-100, 100 = exact match)"
    )
    city_location: dict = Field(
        ...,
        description="Location of the matched city",
        examples=[{"lat": 48.8566, "lon": 2.3522}]
    )
    airports: list[AirportResult] = Field(
        default_factory=list,
        description="List of nearest airports sorted by distance"
    )
