"""
Certify Studio Main Application

FastAPI-based backend for AI-powered certification content generation.
Provides REST API endpoints, WebSocket connections, and background task processing.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import get_settings
from .api.main import api_router
from .api.middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware
)
from .database.connection import database_manager
from .integrations.observability.logging import setup_logging
from .integrations.observability.metrics import setup_metrics
from .frontend_connector import setup_frontend_connector
# Setup observability
try:
    from .integrations.observability.tracing import setup_tracing
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    setup_tracing = None


# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Certify Studio application...")
    
    try:
        # Initialize database
        await database_manager.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")
        logger.warning("Running without database - some features will be unavailable")
        
        # Setup observability
        if settings.ENABLE_METRICS:
            setup_metrics()
            logger.info("Metrics collection enabled")
            
        if settings.ENABLE_TRACING and TRACING_AVAILABLE:
            setup_tracing()
            logger.info("Distributed tracing enabled")
        elif settings.ENABLE_TRACING:
            logger.warning("Tracing enabled but OpenTelemetry not installed")
        
        # Initialize AI services
        try:
            from .agents.orchestrator import AgentOrchestrator
            app.state.agent_orchestrator = AgentOrchestrator()
            await app.state.agent_orchestrator.initialize()
            logger.info("AI agent orchestrator initialized")
        except ImportError as e:
            logger.warning(f"Agent orchestrator not available: {e}")
            app.state.agent_orchestrator = None
        
        # Initialize background task queues
        try:
            from .core.celery import celery_app
            # Celery will be started separately
            logger.info("Background task system ready")
        except ImportError:
            logger.warning("Celery not available - background tasks disabled")
        
        # Create necessary directories
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path(settings.EXPORT_DIR).mkdir(parents=True, exist_ok=True)
        Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
        logger.info("Directory structure created")
        
        logger.info("Certify Studio started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Certify Studio...")
    
    try:
        # Cleanup database connections
        await database_manager.close()
        logger.info("Database connections closed")
        
        # Cleanup AI services
        if hasattr(app.state, 'agent_orchestrator'):
            await app.state.agent_orchestrator.cleanup()
            logger.info("AI services cleaned up")
        
        logger.info("Certify Studio shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Certify Studio API",
        description="AI-Powered Certification Content Generation Platform",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # Configure CORS
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Add middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Setup frontend connector for real-time updates
    setup_frontend_connector(app)
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "Certify Studio",
            "version": "0.1.0",
            "status": "operational",
            "api": "/api/v1",
            "docs": "/docs",
            "health": "/health"
        }
    
    # Serve static files in development
    if settings.DEBUG:
        app.mount(
            "/static", 
            StaticFiles(directory="assets"), 
            name="static"
        )
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        if settings.DEBUG:
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error": str(exc),
                    "type": type(exc).__name__
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Application health check."""
        try:
            # Check database connectivity
            db_healthy = True
            if database_manager.engine:
                db_healthy = await database_manager.health_check()
            else:
                db_healthy = None  # Database not configured
            
            # Check AI services
            ai_healthy = True
            if hasattr(app.state, 'agent_orchestrator') and app.state.agent_orchestrator:
                ai_healthy = await app.state.agent_orchestrator.health_check()
            
            # Determine overall status
            if db_healthy is None:  # Database not configured
                status = "healthy" if ai_healthy else "degraded"
            else:
                status = "healthy" if (db_healthy and ai_healthy) else "unhealthy"
            
            return {
                "status": status,
                "version": "0.1.0",
                "services": {
                    "database": "healthy" if db_healthy else ("not_configured" if db_healthy is None else "unhealthy"),
                    "ai_agents": "healthy" if ai_healthy else "unhealthy"
                },
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": str(e)
                }
            )
    
    # Metrics endpoint (if enabled)
    if settings.ENABLE_METRICS:
        @app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint."""
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            from fastapi.responses import Response
            
            return Response(
                generate_latest(),
                media_type=CONTENT_TYPE_LATEST
            )
    
    return app


# Create application instance
app = create_application()


def run_server():
    """
    Run the FastAPI server.
    Used by startup scripts.
    """
    uvicorn.run(
        "certify_studio.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        access_log=settings.DEBUG,
        log_config=None  # We handle logging ourselves
    )


def main():
    """
    Main entry point for running the application.
    Used by CLI and development server.
    """
    run_server()


if __name__ == "__main__":
    main()
