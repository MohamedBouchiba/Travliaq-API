"""Pydantic models for search autocomplete."""

from pydantic import BaseModel, Field
from typing import Literal


class AutocompleteRequest(BaseModel):
    """Request model for autocomplete search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Search query (min 1 character, recommended 3+)",
        examples=["Par", "New Yo", "CDG"]
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of results to return (default: 5, max: 20)"
    )


class AutocompleteResult(BaseModel):
    """Single autocomplete result."""

    type: Literal["country", "city", "airport"] = Field(
        ...,
        description="Type of location"
    )
    ref: str = Field(
        ...,
        description="Unique reference (ISO2 for countries, UUID for cities, IATA for airports)"
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


class AutocompleteResponse(BaseModel):
    """Response model for autocomplete search."""

    results: list[AutocompleteResult] = Field(
        ...,
        description="List of matching locations ordered by relevance"
    )
    query: str = Field(
        ...,
        description="Original search query"
    )
    count: int = Field(
        ...,
        description="Number of results returned"
    )
