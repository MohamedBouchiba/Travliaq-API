"""Admin routes for cache management and health checks."""

from fastapi import APIRouter, Response, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from app.core.cache import clear_cache, cleanup_expired_cache

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"], prefix="/admin")


class DestinationsSyncRequest(BaseModel):
    """Request model for destinations sync."""
    language: str = Field(default="en", description="Language code for destination names")
    filter_types: Optional[List[str]] = Field(
        default=None,
        description="Optional list of destination types to sync (e.g., ['CITY']). If null, syncs all types."
    )
    cities_only: bool = Field(
        default=False,
        description="Shortcut to sync only cities (equivalent to filter_types=['CITY'])"
    )


class DestinationsSyncResponse(BaseModel):
    """Response model for destinations sync."""
    success: bool
    message: str
    stats: dict


@router.post("/cache/clear")
async def clear_all_cache() -> dict:
    """
    Clear all cached data.

    This endpoint clears the entire in-memory cache.
    Use this if you need to force refresh all cached data.

    Returns:
        Success message
    """
    clear_cache()
    return {"message": "Cache cleared successfully"}


@router.post("/cache/cleanup")
async def cleanup_cache() -> dict:
    """
    Remove expired cache entries.

    This endpoint removes only the expired entries from the cache,
    keeping valid entries intact.

    Returns:
        Success message
    """
    cleanup_expired_cache()
    return {"message": "Expired cache entries removed successfully"}


@router.get("/health")
async def health_check() -> dict:
    """
    Simple health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy"}


@router.post(
    "/destinations/sync",
    response_model=DestinationsSyncResponse,
    summary="Sync destinations from Viator API",
    description="""
    Synchronize destinations from Viator API to MongoDB.

    This endpoint fetches all destinations from Viator and stores them in the local database.
    It should be run:
    - Once during initial deployment
    - Weekly to refresh destination data
    - After deploying updates to destination schema

    **Options**:
    - Sync all destination types (cities, countries, regions, etc.)
    - Sync only cities using `cities_only: true`
    - Filter by specific types using `filter_types`

    **Note**: This operation may take 30-60 seconds depending on the number of destinations.
    """
)
async def sync_destinations(
    request: Request,
    sync_request: DestinationsSyncRequest = DestinationsSyncRequest()
) -> DestinationsSyncResponse:
    """
    Sync destinations from Viator API to MongoDB.

    This is a production-ready endpoint that fetches ALL destinations from Viator
    instead of using hardcoded fallbacks.
    """
    # Check if Viator is enabled
    if not hasattr(request.app.state, 'viator_destinations_service') or \
       request.app.state.viator_destinations_service is None:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "message": "Viator integration is not configured. Please set VIATOR_API_KEY_DEV or VIATOR_API_KEY_PROD in environment variables."
            }
        )

    try:
        sync_service = request.app.state.destinations_sync_service

        # Determine which sync method to use
        if sync_request.cities_only:
            logger.info("Starting cities-only sync from Viator API...")
            stats = await sync_service.sync_cities_only(language=sync_request.language)
        else:
            logger.info("Starting full destinations sync from Viator API...")
            stats = await sync_service.sync_all_destinations(
                language=sync_request.language,
                filter_types=sync_request.filter_types
            )

        return DestinationsSyncResponse(
            success=True,
            message=f"Successfully synced {stats['updated']} destinations from Viator API",
            stats=stats
        )

    except Exception as e:
        logger.error(f"Destinations sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"Failed to sync destinations: {str(e)}"
            }
        )


@router.get(
    "/destinations/stats",
    summary="Get destinations statistics",
    description="Get statistics about synced destinations in the database"
)
async def get_destinations_stats(request: Request) -> dict:
    """Get statistics about destinations in MongoDB."""
    if not hasattr(request.app.state, 'destinations_repo') or \
       request.app.state.destinations_repo is None:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "message": "Viator integration is not configured"
            }
        )

    try:
        repo = request.app.state.destinations_repo

        # Count by type
        total = await repo.collection.count_documents({})
        cities = await repo.collection.count_documents({"type": "city"})
        countries = await repo.collection.count_documents({"type": "country"})
        regions = await repo.collection.count_documents({"type": "region"})

        # Get recent syncs
        recent = await repo.collection.find(
            {"metadata.synced_at": {"$exists": True}}
        ).sort("metadata.synced_at", -1).limit(1).to_list(length=1)

        last_sync = None
        if recent:
            last_sync = recent[0].get("metadata", {}).get("synced_at")

        return {
            "total_destinations": total,
            "by_type": {
                "cities": cities,
                "countries": countries,
                "regions": regions,
                "other": total - cities - countries - regions
            },
            "last_sync": last_sync.isoformat() if last_sync else None,
            "database_populated": total > 0
        }

    except Exception as e:
        logger.error(f"Failed to get destinations stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"Failed to get stats: {str(e)}"
            }
        )
