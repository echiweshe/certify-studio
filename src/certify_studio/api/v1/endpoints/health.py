"""
Health Check Endpoints

Provides health and readiness checks for the application.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional

from ....database.connection import get_db, database_manager
from ....config import settings

router = APIRouter()


@router.get("/status")
async def health_status():
    """Quick health check endpoint."""
    return {
        "status": "healthy",
        "service": "certify-studio",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check including database connectivity.
    Used by Kubernetes readiness probes.
    """
    # Check database
    db_status = "not_configured"
    if database_manager.engine:
        try:
            async with database_manager.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                db_status = "connected" if result.scalar() == 1 else "error"
        except Exception as e:
            db_status = f"error: {str(e)}"
    
    return {
        "status": "ready" if db_status in ["connected", "not_configured"] else "not_ready",
        "checks": {
            "database": db_status,
            "redis": "not_configured",  # TODO: Add actual Redis check
            "storage": "available"  # TODO: Add storage check
        }
    }


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes liveness probes.
    Simple check that the application is running.
    """
    return {"status": "alive"}
