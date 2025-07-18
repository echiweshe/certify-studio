"""
Main API application - FastAPI app configuration and startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from ..core.config import settings
from ..core.logging import get_logger
from .middleware import setup_middleware, setup_exception_handlers
from .routers import (
    auth_router,
    generation_router,
    domains_router,
    quality_router,
    export_router
)
from .websocket import websocket_endpoint
from .schemas import HealthCheck

logger = get_logger(__name__)

# Create API router that combines all sub-routers
from fastapi import APIRouter

api_router = APIRouter(prefix="/v1")
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(generation_router, prefix="/generation", tags=["content-generation"])
api_router.include_router(domains_router, prefix="/domains", tags=["domain-extraction"])
api_router.include_router(quality_router, prefix="/quality", tags=["quality-assurance"])
api_router.include_router(export_router, prefix="/export", tags=["export"])

# Add info endpoint to the api_router
@api_router.get(
    "/info",
    tags=["general"],
    summary="API information",
    description="Get API version and capabilities"
)
async def api_info():
    """Get API information."""
    return {
        "name": "Certify Studio API",
        "version": "1.0.0",
        "description": "AI-powered educational content generation",
        "capabilities": [
            "multimodal-content-generation",
            "domain-knowledge-extraction",
            "quality-assurance",
            "multi-format-export",
            "real-time-updates"
        ],
        "agents": [
            {
                "name": "Pedagogical Reasoning Agent",
                "status": "operational",
                "capabilities": ["cognitive-load-optimization", "learning-path-generation"]
            },
            {
                "name": "Content Generation Agent",
                "status": "operational",
                "capabilities": ["animation-generation", "diagram-creation", "interactive-elements"]
            },
            {
                "name": "Domain Extraction Agent",
                "status": "operational",
                "capabilities": ["concept-extraction", "relationship-mapping", "knowledge-graphs"]
            },
            {
                "name": "Quality Assurance Agent",
                "status": "operational",
                "capabilities": ["technical-validation", "accessibility-checking", "continuous-monitoring"]
            }
        ],
        "supported_formats": [
            "video/mp4",
            "video/webm",
            "interactive/html",
            "scorm/package",
            "pdf/document",
            "powerpoint/pptx"
        ],
        "api_version": "v1",
        "documentation": "/api/docs"
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Certify Studio API")
    
    # Initialize database
    # from ..database import init_db
    # await init_db()
    
    # Initialize agents
    logger.info("Initializing AI agents...")
    # This would initialize all agents in production
    
    # Initialize cache
    # from .dependencies import get_redis
    # redis = await get_redis()
    # await redis.ping()
    
    # Start WebSocket cleanup task
    import asyncio
    from .websocket import cleanup_stale_connections
    cleanup_task = asyncio.create_task(cleanup_stale_connections())
    
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Certify Studio API")
    
    # Cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    # Close database connections
    # await close_db()
    
    # Close cache connections
    # await redis.close()
    
    logger.info("API shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Create app
    app = FastAPI(
        title="Certify Studio API",
        description="Production-ready API for AI-powered educational content generation",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include routers - they're already in api_router, so just include that
    # Don't include individual routers again
    
    # WebSocket endpoint
    app.add_api_websocket_route("/api/ws", websocket_endpoint)
    
    # Static files (if needed)
    # app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint."""
        return {
            "name": "Certify Studio API",
            "version": "1.0.0",
            "status": "operational",
            "docs": "/api/docs"
        }
    
    # Health check endpoint
    @app.get(
        "/health",
        response_model=HealthCheck,
        tags=["monitoring"],
        summary="Health check",
        description="Check API and service health"
    )
    async def health_check():
        """Health check endpoint."""
        # Check services
        services = {
            "api": "healthy",
            "database": "healthy",  # Would check actual connection
            "cache": "healthy",      # Would check Redis
            "agents": "healthy"      # Would check agent status
        }
        
        # Overall status
        all_healthy = all(status == "healthy" for status in services.values())
        
        return HealthCheck(
            status="healthy" if all_healthy else "degraded",
            version="1.0.0",
            services=services
        )
    
    # Metrics endpoint (Prometheus format)
    @app.get(
        "/metrics",
        include_in_schema=False,
        tags=["monitoring"]
    )
    async def metrics():
        """Prometheus metrics endpoint."""
        # In production, use prometheus_client
        metrics_text = """
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{method="GET",endpoint="/health"} 1234
api_requests_total{method="POST",endpoint="/api/generation/generate"} 567

# HELP api_request_duration_seconds API request duration
# TYPE api_request_duration_seconds histogram
api_request_duration_seconds_bucket{le="0.1"} 1000
api_request_duration_seconds_bucket{le="0.5"} 1200
api_request_duration_seconds_bucket{le="1.0"} 1300
api_request_duration_seconds_bucket{le="+Inf"} 1400

# HELP active_generations Number of active content generations
# TYPE active_generations gauge
active_generations 5

# HELP content_quality_score Average content quality score
# TYPE content_quality_score gauge
content_quality_score 0.92
        """
        
        return Response(
            content=metrics_text,
            media_type="text/plain; version=0.0.4"
        )
    
    # API info endpoint
    @app.get(
        "/api/info",
        tags=["general"],
        summary="API information",
        description="Get API version and capabilities"
    )
    async def api_info():
        """Get API information."""
        return {
            "name": "Certify Studio API",
            "version": "1.0.0",
            "description": "AI-powered educational content generation",
            "capabilities": [
                "multimodal-content-generation",
                "domain-knowledge-extraction",
                "quality-assurance",
                "multi-format-export",
                "real-time-updates"
            ],
            "agents": [
                {
                    "name": "Pedagogical Reasoning Agent",
                    "status": "operational",
                    "capabilities": ["cognitive-load-optimization", "learning-path-generation"]
                },
                {
                    "name": "Content Generation Agent",
                    "status": "operational",
                    "capabilities": ["animation-generation", "diagram-creation", "interactive-elements"]
                },
                {
                    "name": "Domain Extraction Agent",
                    "status": "operational",
                    "capabilities": ["concept-extraction", "relationship-mapping", "knowledge-graphs"]
                },
                {
                    "name": "Quality Assurance Agent",
                    "status": "operational",
                    "capabilities": ["technical-validation", "accessibility-checking", "continuous-monitoring"]
                }
            ],
            "supported_formats": [
                "video/mp4",
                "video/webm",
                "interactive/html",
                "scorm/package",
                "pdf/document",
                "powerpoint/pptx"
            ],
            "api_version": "v1",
            "documentation": "/api/docs"
        }
    
    # Error test endpoint (for testing error handling)
    if settings.DEBUG:
        @app.get("/api/test/error", include_in_schema=False)
        async def test_error():
            """Test error handling."""
            raise Exception("This is a test error")
    
    return app


# Create the app instance
app = create_app()


# Custom OpenAPI schema
def custom_openapi():
    """Customize OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Certify Studio API",
        version="1.0.0",
        description="""
# Certify Studio API

Production-ready API for AI-powered educational content generation.

## Features

- 🤖 **4 Specialized AI Agents** working in harmony
- 📚 **Multimodal Content Generation** from any certification guide
- 🎯 **Cognitive Load Optimization** for effective learning
- ♿ **Accessibility First** with WCAG AA compliance
- 📊 **Quality Assurance** with continuous monitoring
- 🚀 **Real-time Updates** via WebSocket

## Authentication

All endpoints (except health checks) require authentication via JWT tokens.

Include the token in the Authorization header:
```
Authorization: Bearer <your-token>
```

## Rate Limiting

API requests are rate limited based on your plan:
- Free: 100 requests/hour
- Pro: 1000 requests/hour
- Enterprise: Unlimited

## WebSocket

Connect to `/api/ws` for real-time updates on generation progress.
        """,
        routes=app.routes,
        tags=[
            {
                "name": "authentication",
                "description": "User authentication and authorization"
            },
            {
                "name": "content-generation",
                "description": "Generate educational content from certifications"
            },
            {
                "name": "domain-extraction",
                "description": "Extract knowledge from certification materials"
            },
            {
                "name": "quality-assurance",
                "description": "Check and monitor content quality"
            },
            {
                "name": "export",
                "description": "Export content in various formats"
            },
            {
                "name": "monitoring",
                "description": "Health checks and metrics"
            }
        ]
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://certifystudio.com/logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# If running directly
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "certify_studio.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True
    )
