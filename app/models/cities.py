"""Pydantic models for cities endpoints."""

from typing import List, Optional
from pydantic import BaseModel, Field


class CityInfo(BaseModel):
    """Single city information."""

    id: str = Field(..., description="City UUID")
    name: str = Field(..., description="City name")
    country_code: str = Field(..., description="ISO2 country code")
    slug: str = Field(..., description="City slug")
    population: Optional[int] = Field(None, description="City population")
    lat: Optional[float] = Field(None, description="Latitude")
    lon: Optional[float] = Field(None, description="Longitude")


class TopCitiesResponse(BaseModel):
    """Response model for top cities by country."""

    country_code: str = Field(..., description="ISO2 country code queried")
    total_cities: int = Field(..., description="Total cities found in country")
    cities: List[CityInfo] = Field(..., description="Top cities by population")

    class Config:
        json_schema_extra = {
            "example": {
                "country_code": "FR",
                "total_cities": 2847,
                "cities": [
                    {
                        "id": "3978405a-2f88-40fd-a9d1-1b7c896626ff",
                        "name": "Paris",
                        "country_code": "FR",
                        "slug": "paris",
                        "population": 2138551,
                        "lat": 48.8566,
                        "lon": 2.3522
                    },
                    {
                        "id": "uuid-marseille",
                        "name": "Marseille",
                        "country_code": "FR",
                        "slug": "marseille",
                        "population": 869815,
                        "lat": 43.2965,
                        "lon": 5.3698
                    }
                ]
            }
        }
