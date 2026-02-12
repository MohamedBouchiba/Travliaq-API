"""Admin routes for cache management and health checks."""

from fastapi import APIRouter, Response, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from app.core.cache import clear_cache, cleanup_expired_cache
from app.services.viator.taxonomy import ViatorTaxonomyService
from app.services.taxonomy_sync import TaxonomySyncService
from app.repositories.tags_repository import TagsRepository

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


@router.post("/cache/clear-map-prices")
async def clear_map_prices_cache(request: Request) -> dict:
    """
    Clear all map-prices cache entries from Redis.

    This endpoint removes all cached flight prices for the /map-prices endpoint.
    Use this to force refresh all map price data.

    Returns:
        Number of keys deleted
    """
    redis_cache = request.app.state.redis_cache
    deleted = redis_cache.clear_pattern("map_price:*")
    return {
        "message": f"Map prices cache cleared successfully",
        "keys_deleted": deleted
    }


class ClearInvalidRoutesRequest(BaseModel):
    """Request model for clearing invalid flight routes."""
    origin: Optional[str] = Field(
        None,
        description="Optional IATA code to clear only routes from this origin (e.g., 'BRU'). If omitted, clears all.",
        min_length=3,
        max_length=3
    )


@router.get("/invalid-routes/list")
async def list_invalid_routes(request: Request, origin: Optional[str] = None) -> dict:
    """
    List known invalid flight routes from MongoDB.

    Use this to diagnose why certain destinations don't show prices on the map.
    """
    mongo_manager = request.app.state.mongo_manager
    if not mongo_manager:
        raise HTTPException(status_code=503, detail="MongoDB not available")

    try:
        db = mongo_manager.client[mongo_manager._settings.mongodb_db]
        collection = db["invalid_flight_routes"]

        query = {"origin": origin.upper()} if origin else {}
        total_count = await collection.count_documents(query)

        cursor = collection.find(query).sort("last_checked_at", -1).limit(200)
        routes = []
        async for doc in cursor:
            routes.append({
                "origin": doc.get("origin"),
                "destination": doc.get("destination"),
                "route_key": doc.get("route_key"),
                "last_checked_at": doc.get("last_checked_at").isoformat() if doc.get("last_checked_at") else None,
                "first_detected_at": doc.get("first_detected_at").isoformat() if doc.get("first_detected_at") else None,
                "failure_count": doc.get("failure_count", 0),
            })

        return {
            "total_count": total_count,
            "showing": len(routes),
            "routes": routes,
        }

    except Exception as e:
        logger.error(f"Failed to list invalid routes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list invalid routes: {str(e)}")


@router.post("/invalid-routes/clear")
async def clear_invalid_routes(
    request: Request,
    body: ClearInvalidRoutesRequest = ClearInvalidRoutesRequest()
) -> dict:
    """
    Clear invalid flight routes from MongoDB blacklist.

    Also clears Redis map-price cache to flush cached None values.
    Use this to restore destinations that were incorrectly blacklisted.
    """
    mongo_manager = request.app.state.mongo_manager
    if not mongo_manager:
        raise HTTPException(status_code=503, detail="MongoDB not available")

    try:
        db = mongo_manager.client[mongo_manager._settings.mongodb_db]
        collection = db["invalid_flight_routes"]

        query = {"origin": body.origin.upper()} if body.origin else {}
        result = await collection.delete_many(query)

        # Also clear Redis map-price cache (cached None values from blacklisted routes)
        redis_cache = request.app.state.redis_cache
        redis_deleted = redis_cache.clear_pattern("map_price:*")

        origin_msg = f" from {body.origin.upper()}" if body.origin else ""
        logger.info(
            f"Cleared {result.deleted_count} invalid routes{origin_msg} "
            f"and {redis_deleted} Redis map-price keys"
        )

        return {
            "message": f"Invalid routes cleared successfully{origin_msg}",
            "invalid_routes_deleted": result.deleted_count,
            "redis_keys_deleted": redis_deleted,
        }

    except Exception as e:
        logger.error(f"Failed to clear invalid routes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clear invalid routes: {str(e)}")


@router.post("/cache/clear-hotels")
async def clear_hotels_cache(request: Request) -> dict:
    """
    Clear all hotel-related cache entries from Redis.

    This endpoint removes all cached hotel search results, details, and map prices.
    Use this to force refresh all hotel data.

    Returns:
        Number of keys deleted per category
    """
    redis_cache = request.app.state.redis_cache

    # Clear all hotel-related caches
    hotel_search = redis_cache.clear_pattern("hotel_search:*")
    hotel_details = redis_cache.clear_pattern("hotel_details:*")
    hotel_map = redis_cache.clear_pattern("hotel_map_price:*")

    total = hotel_search + hotel_details + hotel_map

    return {
        "message": "Hotel cache cleared successfully",
        "keys_deleted": {
            "hotel_search": hotel_search,
            "hotel_details": hotel_details,
            "hotel_map_price": hotel_map,
            "total": total
        }
    }


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


@router.get(
    "/destinations/search/{city_name}",
    summary="Debug: Search for a city by name",
    description="Debug endpoint to see what's stored in the database for a specific city"
)
async def debug_search_city(request: Request, city_name: str, country_code: Optional[str] = None) -> dict:
    """Debug endpoint to search for a city and see its full data."""
    if not hasattr(request.app.state, 'destinations_repo'):
        raise HTTPException(status_code=503, detail="Destinations repository not available")

    repo = request.app.state.destinations_repo

    # Build query
    query = {"name": {"$regex": city_name, "$options": "i"}, "type": "city"}
    if country_code:
        query["country_code"] = country_code.upper()

    # Find matches
    matches = await repo.collection.find(query).limit(10).to_list(length=10)

    return {
        "query": query,
        "count": len(matches),
        "results": matches
    }


# ============================================================================
# TAGS / TAXONOMY ENDPOINTS
# ============================================================================

class TagsSyncRequest(BaseModel):
    """Request model for tags sync."""
    language: str = Field(default="en", description="Language code for tag names")


class TagsSyncResponse(BaseModel):
    """Response model for tags sync."""
    success: bool
    message: str
    stats: dict


@router.post(
    "/tags/sync",
    response_model=TagsSyncResponse,
    summary="Sync tags from Viator API",
    description="""
    Synchronize tags/taxonomy from Viator API to MongoDB.

    This endpoint fetches ALL tags from Viator and stores them in the local database.
    It should be run:
    - Once during initial deployment (REQUIRED before using category filters)
    - Weekly to refresh tag data (Viator recommends weekly refresh)
    - After deploying updates to tag schema

    **Why this is needed**:
    - Replaces hardcoded CATEGORY_TAG_MAPPING
    - Enables dynamic category filtering for activities search
    - Provides multilingual tag names

    **Note**: This operation usually takes 10-30 seconds.
    """
)
async def sync_tags(
    request: Request,
    sync_request: TagsSyncRequest = TagsSyncRequest()
) -> TagsSyncResponse:
    """
    Sync tags from Viator API to MongoDB.

    This is REQUIRED for the activities search to work with category filters.
    """
    # Check if Viator is enabled
    if not hasattr(request.app.state, 'viator_client') or \
       request.app.state.viator_client is None:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "message": "Viator integration is not configured. Please set VIATOR_API_KEY_DEV or VIATOR_API_KEY_PROD in environment variables."
            }
        )

    if not hasattr(request.app.state, 'tags_repo') or \
       request.app.state.tags_repo is None:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "message": "Tags repository is not initialized. Check MongoDB configuration."
            }
        )

    try:
        # Create taxonomy service
        viator_taxonomy = ViatorTaxonomyService(request.app.state.viator_client)
        sync_service = TaxonomySyncService(viator_taxonomy, request.app.state.tags_repo)

        logger.info("Starting tags sync from Viator API...")
        stats = await sync_service.sync_all_tags(language=sync_request.language)

        return TagsSyncResponse(
            success=True,
            message=f"Successfully synced {stats['updated']} tags from Viator API ({stats['root_tags']} root tags, {stats['child_tags']} child tags)",
            stats=stats
        )

    except Exception as e:
        logger.error(f"Tags sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"Failed to sync tags: {str(e)}"
            }
        )


@router.get(
    "/tags/stats",
    summary="Get tags statistics",
    description="Get statistics about synced tags in the database"
)
async def get_tags_stats(request: Request) -> dict:
    """Get statistics about tags in MongoDB."""
    if not hasattr(request.app.state, 'tags_repo') or \
       request.app.state.tags_repo is None:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "message": "Tags repository is not initialized"
            }
        )

    try:
        repo = request.app.state.tags_repo

        # Count total and by hierarchy level
        total = await repo.collection.count_documents({})
        root_tags = await repo.collection.count_documents({"parent_tag_id": None})
        child_tags = total - root_tags

        # Get recent syncs
        recent = await repo.collection.find(
            {"metadata.synced_at": {"$exists": True}}
        ).sort("metadata.synced_at", -1).limit(1).to_list(length=1)

        last_sync = None
        if recent:
            last_sync = recent[0].get("metadata", {}).get("synced_at")

        # Sample root tags
        sample_root_tags = await repo.get_all_root_tags()
        sample_names = [tag["tag_name"] for tag in sample_root_tags[:10]]

        return {
            "total_tags": total,
            "root_tags": root_tags,
            "child_tags": child_tags,
            "last_sync": last_sync.isoformat() if last_sync else None,
            "database_populated": total > 0,
            "sample_root_tags": sample_names,
            "ready_for_use": total > 0
        }

    except Exception as e:
        logger.error(f"Failed to get tags stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"Failed to get stats: {str(e)}"
            }
        )


@router.get(
    "/tags/search",
    summary="Search tags by keyword",
    description="Search for tags matching a keyword (useful for debugging category filters)"
)
async def search_tags(
    request: Request,
    keyword: str,
    language: str = "en",
    limit: int = 20
) -> dict:
    """Search for tags matching a keyword."""
    if not hasattr(request.app.state, 'tags_repo'):
        raise HTTPException(status_code=503, detail="Tags repository not available")

    repo = request.app.state.tags_repo

    try:
        # Find tags matching the keyword
        matches = await repo.find_tags_by_category_keyword(
            keyword=keyword,
            language=language
        )

        # Limit results
        matches = matches[:limit]

        # Extract useful info
        results = []
        for tag in matches:
            results.append({
                "tag_id": tag["tag_id"],
                "tag_name": tag["tag_name"],
                "parent_tag_id": tag.get("parent_tag_id"),
                "all_names": tag.get("all_names", {})
            })

        return {
            "keyword": keyword,
            "language": language,
            "count": len(results),
            "results": results,
            "tag_ids": [r["tag_id"] for r in results]
        }

    except Exception as e:
        logger.error(f"Failed to search tags: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"Failed to search tags: {str(e)}"
            }
        )


@router.get(
    "/tags/root",
    summary="List root tags",
    description="Get all root-level tags (tags with no parent)"
)
async def get_root_tags(request: Request) -> dict:
    """Get all root-level tags."""
    if not hasattr(request.app.state, 'tags_repo'):
        raise HTTPException(status_code=503, detail="Tags repository not available")

    repo = request.app.state.tags_repo

    try:
        root_tags = await repo.get_all_root_tags()

        # Format results
        results = []
        for tag in root_tags:
            results.append({
                "tag_id": tag["tag_id"],
                "tag_name": tag["tag_name"],
                "all_names": tag.get("all_names", {})
            })

        return {
            "count": len(results),
            "root_tags": results
        }

    except Exception as e:
        logger.error(f"Failed to get root tags: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"Failed to get root tags: {str(e)}"
            }
        )
