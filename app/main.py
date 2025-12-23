from __future__ import annotations
import asyncio
from fastapi import FastAPI
import httpx

from app.api.routes import router
from app.api.search_routes import router as search_router
from app.core.config import get_settings
from app.db.mongo import MongoManager
from app.db.postgres import PostgresManager
from app.services.enrichment import EnrichmentService
from app.services.autocomplete import AutocompleteService
from app.services.airports import AirportsService
from app.services.geoapify import GeoapifyClient
from app.services.google_places import GooglePlacesClient
from app.services.nominatim import NominatimClient
from app.services.poi_repository import POIRepository
from app.services.translation import TranslationClient
from app.services.wikidata import WikidataClient

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.on_event("startup")
async def startup_event() -> None:
    app.state.http_client = httpx.AsyncClient()

    # Initialize MongoDB
    app.state.mongo_manager = MongoManager(settings)
    await app.state.mongo_manager.init_indexes()

    # Initialize PostgreSQL (optional - only if credentials are provided)
    if settings.pg_host and settings.pg_user and settings.pg_password:
        app.state.postgres_manager = PostgresManager(settings)
        app.state.postgres_manager.init_pool(min_conn=2, max_conn=10)

        # Initialize autocomplete service
        app.state.autocomplete_service = AutocompleteService(
            postgres_manager=app.state.postgres_manager
        )

        # Initialize airports service
        app.state.airports_service = AirportsService(
            postgres_manager=app.state.postgres_manager
        )
    else:
        app.state.postgres_manager = None
        app.state.autocomplete_service = None
        app.state.airports_service = None

    # Initialize POI enrichment services
    repository = POIRepository(app.state.mongo_manager.collection(), ttl_days=settings.ttl_days)
    google_client = GooglePlacesClient(settings.google_maps_api_key, app.state.http_client, settings.google_places_daily_cap)
    nominatim_client = NominatimClient(settings.wikidata_user_agent, app.state.http_client)
    geoapify_client = GeoapifyClient(settings.geoapify_api_key, app.state.http_client)
    translation_client = TranslationClient(settings.translation_service_url, app.state.http_client)
    wikidata_client = WikidataClient(settings.wikidata_user_agent, app.state.http_client)

    app.state.enrichment_service = EnrichmentService(
        repo=repository,
        google=google_client,
        nominatim=nominatim_client,
        geoapify=geoapify_client,
        translation=translation_client,
        wikidata=wikidata_client,
        ttl_days=settings.ttl_days,
        default_detail_types=settings.default_detail_types,
    )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    client: httpx.AsyncClient = app.state.http_client
    await client.aclose()
    await app.state.mongo_manager.close()

    # Close PostgreSQL if it was initialized
    if app.state.postgres_manager:
        app.state.postgres_manager.close_all()


app.include_router(router)
app.include_router(search_router)
