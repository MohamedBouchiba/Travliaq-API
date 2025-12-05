from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Location(BaseModel):
    lat: float
    lng: float


class HoursInfo(BaseModel):
    weekly: Dict[str, List[str]] | None = None
    raw: Any | None = None


class PricingInfo(BaseModel):
    admission_type: str = Field("unknown", description="Free, Paid, or Unknown")
    currency: str | None = None
    amount: float | None = None


class ContactInfo(BaseModel):
    phone: str | None = None
    website: str | None = None


class FactsInfo(BaseModel):
    year_built: int | None = None
    unesco_site: bool | None = None
    instance_of: str | None = None
    description: str | None = None
    extra: Dict[str, Any] | None = None


class SourcesInfo(BaseModel):
    google_places: Dict[str, Any] | None = None
    opentripmap: Dict[str, Any] | None = None
    wikidata: Dict[str, Any] | None = None


class POIDocument(BaseModel):
    poi_key: str
    name: str
    city: str
    country: str | None = None
    location: Location | None = None
    place_id: str | None = None
    hours: HoursInfo | None = None
    pricing: PricingInfo | None = None
    contact: ContactInfo | None = None
    facts: FactsInfo | None = None
    sources: SourcesInfo | None = None
    ttl_days: int = 365
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class POIRequest(BaseModel):
    poi_name: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    detail_types: list[str] | None = None


class POIResponse(BaseModel):
    name: str
    city: str
    country: str | None
    location: Location | None
    hours: HoursInfo | None
    pricing: PricingInfo | None
    contact: ContactInfo | None
    facts: FactsInfo | None
    sources: SourcesInfo | None
    last_updated: datetime
    poi_key: str
    place_id: str | None = None
