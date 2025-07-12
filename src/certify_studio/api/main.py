"""
API Router Configuration

Main API router that aggregates all endpoint routers and configures
API-wide settings, middleware, and error handling.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from .v1.router import router as v1_router
from ..config import settings

# Create main API router
api_router = APIRouter()

# Include version-specific routers
api_router.include_router(
    v1_router,
    prefix="/v1",
    tags=["v1"]
)

# Root API endpoint
@api_router.get("/")
async def api_root():
    """API root endpoint with version information."""
    return {
        "message": "Certify Studio API",
        "version": settings.APP_VERSION,
        "documentation": "/docs" if settings.DEBUG else None,
        "available_versions": ["v1"]
    }

# API health check (different from main app health check)
@api_router.get("/status")
async def api_status():
    """Quick API status check."""
    return {
        "status": "operational",
        "api_version": "v1",
        "debug_mode": settings.DEBUG
    }
