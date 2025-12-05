from functools import lru_cache
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

    app_name: str = "POI Details API"
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_db: str = Field(..., alias="MONGODB_DB")
    mongodb_collection_poi: str = Field("poi_details", alias="MONGODB_COLLECTION_POI")

    google_maps_api_key: str = Field(..., alias="GOOGLE_MAPS_API_KEY")
    opentripmap_api_key: str = Field(..., alias="OPENTRIPMAP_API_KEY")

    ttl_days: int = Field(365, description="Days before a POI document is considered stale")
    google_places_daily_cap: int = Field(9500, description="Soft cap to avoid exceeding free Google quotas")
    opentripmap_daily_cap: int = Field(9500, description="Soft cap to avoid exceeding free OpenTripMap quotas")
    wikidata_user_agent: str = Field("poi-details-api/1.0", description="User agent used for Wikidata requests")
    default_detail_types: list[str] = Field(default_factory=lambda: ["hours", "pricing", "contact", "facts"])


class SourceMeta(BaseModel):
    name: str
    last_fetched: str
    fields: list[str] | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
