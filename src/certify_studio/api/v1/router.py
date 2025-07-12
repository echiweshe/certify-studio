"""
API v1 Router

Main router for API version 1 that aggregates all endpoint routers.
"""

from fastapi import APIRouter

from .endpoints import health

# Create v1 router
router = APIRouter()

# Include endpoint routers
router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

# TODO: Add other routers as they are implemented
# router.include_router(auth.router, prefix="/auth", tags=["authentication"])
# router.include_router(certifications.router, prefix="/certifications", tags=["certifications"])
# router.include_router(content_generation.router, prefix="/content", tags=["content-generation"])
# router.include_router(exports.router, prefix="/exports", tags=["exports"])
# router.include_router(websockets.router, prefix="/ws", tags=["websockets"])

# Version info endpoint
@router.get("/")
async def v1_info():
    """API v1 information."""
    return {
        "version": "1.0",
        "description": "Certify Studio API v1",
        "endpoints": {
            "auth": "/api/v1/auth",
            "certifications": "/api/v1/certifications",
            "content": "/api/v1/content",
            "exports": "/api/v1/exports",
            "health": "/api/v1/health",
            "websockets": "/api/v1/ws"
        }
    }
