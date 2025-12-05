from __future__ import annotations
import asyncio
from fastapi import FastAPI
import httpx

from app.api.routes import router
from app.core.config import get_settings
from app.db.mongo import MongoManager
from app.services.enrichment import EnrichmentService
from app.services.geoapify import GeoapifyClient
from app.services.google_places import GooglePlacesClient
from app.services.nominatim import NominatimClient
from app.services.poi_repository import POIRepository
from app.services.wikidata import WikidataClient

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.on_event("startup")
async def startup_event() -> None:
    app.state.http_client = httpx.AsyncClient()
    app.state.mongo_manager = MongoManager(settings)
    await app.state.mongo_manager.init_indexes()

    repository = POIRepository(app.state.mongo_manager.collection(), ttl_days=settings.ttl_days)
    google_client = GooglePlacesClient(settings.google_maps_api_key, app.state.http_client, settings.google_places_daily_cap)
    nominatim_client = NominatimClient(settings.wikidata_user_agent, app.state.http_client)
    geoapify_client = GeoapifyClient(settings.geoapify_api_key, app.state.http_client)
    wikidata_client = WikidataClient(settings.wikidata_user_agent, app.state.http_client)

    app.state.enrichment_service = EnrichmentService(
        repo=repository,
        google=google_client,
        nominatim=nominatim_client,
        geoapify=geoapify_client,
        wikidata=wikidata_client,
        ttl_days=settings.ttl_days,
        default_detail_types=settings.default_detail_types,
    )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    client: httpx.AsyncClient = app.state.http_client
    await client.aclose()
    await app.state.mongo_manager.close()


app.include_router(router)
