from functools import lru_cache
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

    app_name: str = "POI Details API"

    # MongoDB
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_db: str = Field(..., alias="MONGODB_DB")
    mongodb_collection_poi: str = Field("poi_details", alias="MONGODB_COLLECTION_POI")

    # PostgreSQL/Supabase (optional - for autocomplete feature)
    pg_host: str | None = Field(None, alias="PG_HOST")
    pg_database: str = Field("postgres", alias="PG_DATABASE")
    pg_user: str | None = Field(None, alias="PG_USER")
    pg_password: str | None = Field(None, alias="PG_PASSWORD")
    pg_port: int = Field(5432, alias="PG_PORT")
    pg_sslmode: str = Field("require", alias="PG_SSLMODE")

    # External APIs
    google_maps_api_key: str = Field(..., alias="GOOGLE_MAPS_API_KEY")
    geoapify_api_key: str = Field(..., alias="GEOAPIFY_API_KEY")
    google_flight_api_key: str = Field(..., alias="GOOGLE_FLIGHT_API")
    translation_service_url: str = Field("https://travliaq-transalte-production.up.railway.app", alias="TRANSLATION_SERVICE_URL")

    # Upstash Redis (for flights cache)
    upstash_redis_rest_url: str = Field(..., alias="UPSTASH_REDIS_REST_URL")
    upstash_redis_rest_token: str = Field(..., alias="UPSTASH_REDIS_REST_TOKEN")

    # Settings
    ttl_days: int = Field(365, description="Days before a POI document is considered stale")
    google_places_daily_cap: int = Field(9500, description="Soft cap to avoid exceeding free Google quotas")
    wikidata_user_agent: str = Field("poi-details-api/1.0", description="User agent used for Wikidata requests")
    default_detail_types: list[str] = Field(default_factory=lambda: ["hours", "pricing", "contact", "facts"])


class SourceMeta(BaseModel):
    name: str
    last_fetched: str
    fields: list[str] | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
