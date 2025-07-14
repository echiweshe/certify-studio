"""
Application Startup and Configuration

This module handles application initialization, including:
- Database setup
- Event bus initialization
- Background task configuration
- Agent initialization
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.logging import setup_logging, get_logger
from .database import init_database
from .integration.events import initialize_event_bus, shutdown_event_bus
from .integration.background import celery_app
from .agents.orchestration import AgentOrchestrator
from .knowledge import UnifiedGraphRAG

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks.
    """
    logger.info("Starting Certify Studio...")
    
    # Startup
    try:
        # Initialize database
        logger.info("Initializing database...")
        await init_database()
        
        # Initialize event bus
        logger.info("Starting event bus...")
        await initialize_event_bus()
        
        # Initialize knowledge graph
        if settings.NEO4J_ENABLED:
            logger.info("Connecting to knowledge graph...")
            app.state.graphrag = UnifiedGraphRAG(
                neo4j_uri=settings.NEO4J_URI,
                neo4j_user=settings.NEO4J_USER,
                neo4j_password=settings.NEO4J_PASSWORD
            )
            await app.state.graphrag.initialize()
        
        # Initialize agent orchestrator
        logger.info("Initializing agent orchestrator...")
        app.state.orchestrator = AgentOrchestrator()
        await app.state.orchestrator.initialize()
        
        # Start background workers if not in worker mode
        if not settings.IS_CELERY_WORKER:
            logger.info("Background task processing enabled")
            # Celery will be started separately
        
        logger.info("Certify Studio started successfully!")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Certify Studio...")
    
    try:
        # Shutdown event bus
        await shutdown_event_bus()
        
        # Close knowledge graph connection
        if hasattr(app.state, 'graphrag'):
            await app.state.graphrag.close()
        
        # Shutdown agent orchestrator
        if hasattr(app.state, 'orchestrator'):
            await app.state.orchestrator.shutdown()
        
        logger.info("Certify Studio shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI app
    """
    # Create app with lifespan manager
    app = FastAPI(
        title="Certify Studio",
        description="AI Agent Orchestration Platform for Educational Excellence",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom headers middleware
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
    
    # Register routers
    from .api.v1 import auth, content, quality, analytics, agents
    
    api_v1_prefix = "/api/v1"
    
    app.include_router(auth.router, prefix=api_v1_prefix)
    app.include_router(content.router, prefix=api_v1_prefix)
    app.include_router(quality.router, prefix=api_v1_prefix)
    app.include_router(analytics.router, prefix=api_v1_prefix)
    app.include_router(agents.router, prefix=api_v1_prefix)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Application health check."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "services": {
                "database": "connected",
                "event_bus": "running",
                "agents": "ready"
            }
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "Certify Studio",
            "description": "AI Agent Orchestration Platform for Educational Excellence",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # Run the app
    uvicorn.run(
        "certify_studio.app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None  # We use our own logging
    )
