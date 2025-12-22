"""Pydantic models for search autocomplete."""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class AutocompleteResult(BaseModel):
    """Single autocomplete result."""

    type: Literal["country", "city", "airport"] = Field(
        ...,
        description="Type of location"
    )
    id: str = Field(
        ...,
        description="Unique ID (ISO2 for countries, UUID for cities, IATA for airports)"
    )
    label: str = Field(
        ...,
        description="Display label for the UI",
        examples=["Paris, FR", "Paris Charles de Gaulle (CDG)", "France"]
    )
    country_code: str = Field(
        ...,
        description="ISO2 country code"
    )
    slug: str = Field(
        ...,
        description="URL-friendly slug"
    )
    lat: Optional[float] = Field(
        None,
        description="Latitude (null for countries)"
    )
    lon: Optional[float] = Field(
        None,
        description="Longitude (null for countries)"
    )


class AutocompleteResponse(BaseModel):
    """Response model for autocomplete search."""

    q: str = Field(
        ...,
        description="Original search query"
    )
    results: list[AutocompleteResult] = Field(
        default_factory=list,
        description="List of matching locations ordered by relevance (empty if q < 3 chars)"
    )
