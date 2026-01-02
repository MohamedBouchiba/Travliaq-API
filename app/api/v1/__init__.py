"""API v1 routes package."""

from fastapi import APIRouter
from .activities import router as activities_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(activities_router)

__all__ = ["v1_router"]
