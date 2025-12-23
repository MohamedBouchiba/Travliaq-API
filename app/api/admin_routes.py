"""Admin routes for cache management and health checks."""

from fastapi import APIRouter, Response
from app.core.cache import clear_cache, cleanup_expired_cache

router = APIRouter(tags=["admin"], prefix="/admin")


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
