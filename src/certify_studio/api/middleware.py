"""
API middleware for authentication, rate limiting, logging, and error handling.
"""

import time
import uuid
from datetime import datetime
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.logging import get_logger
from ..core.config import settings
from .schemas import ErrorResponse, ErrorDetail, RateLimitResponse

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID to all requests for tracking."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration
            }
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(duration)
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # Let FastAPI handle HTTP exceptions
            raise
            
        except Exception as e:
            # Log unexpected errors
            logger.error(
                f"Unhandled error: {str(e)}",
                exc_info=True,
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "path": request.url.path
                }
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    status="error",
                    message="Internal server error",
                    errors=[
                        ErrorDetail(
                            code="INTERNAL_ERROR",
                            message="An unexpected error occurred"
                        )
                    ],
                    request_id=getattr(request.state, "request_id", None)
                ).model_dump()
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app: ASGIApp, calls: int = 100, period: int = 3600):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        # Get client identifier
        client = request.client.host if request.client else "unknown"
        
        # Clean old entries
        now = time.time()
        self.clients = {
            k: v for k, v in self.clients.items()
            if now - v["start"] < self.period
        }
        
        # Check rate limit
        if client in self.clients:
            client_data = self.clients[client]
            if client_data["calls"] >= self.calls:
                # Calculate reset time
                reset_time = client_data["start"] + self.period
                retry_after = int(reset_time - now)
                
                return JSONResponse(
                    status_code=429,
                    content=RateLimitResponse(
                        status="error",
                        message="Rate limit exceeded",
                        rate_limit_info={
                            "limit": self.calls,
                            "remaining": 0,
                            "reset_at": datetime.fromtimestamp(reset_time),
                            "retry_after": retry_after
                        }
                    ).model_dump(),
                    headers={
                        "X-RateLimit-Limit": str(self.calls),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(reset_time)),
                        "Retry-After": str(retry_after)
                    }
                )
            
            client_data["calls"] += 1
        else:
            self.clients[client] = {
                "calls": 1,
                "start": now
            }
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        client_data = self.clients[client]
        remaining = self.calls - client_data["calls"]
        reset_time = client_data["start"] + self.period
        
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Compress responses when beneficial."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if client accepts compression
        accept_encoding = request.headers.get("accept-encoding", "")
        
        # Process request
        response = await call_next(request)
        
        # Skip compression for small responses or already compressed
        if (
            response.headers.get("content-encoding") or
            int(response.headers.get("content-length", 0)) < 1000
        ):
            return response
        
        # Add compression header if supported
        if "gzip" in accept_encoding:
            response.headers["Content-Encoding"] = "gzip"
        elif "br" in accept_encoding:
            response.headers["Content-Encoding"] = "br"
        
        return response


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the application."""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time", "X-RateLimit-*"]
    )
    
    # Custom middleware (order matters - executed in reverse order)
    app.add_middleware(CompressionMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, calls=settings.RATE_LIMIT_CALLS, period=settings.RATE_LIMIT_PERIOD)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    
    logger.info("Middleware configured successfully")


# Exception handlers
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status="error",
            message=exc.detail,
            errors=[
                ErrorDetail(
                    code=f"HTTP_{exc.status_code}",
                    message=exc.detail
                )
            ],
            request_id=getattr(request.state, "request_id", None)
        ).model_dump(),
        headers=exc.headers
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation exceptions."""
    errors = []
    
    # Parse validation errors
    if hasattr(exc, "errors"):
        for error in exc.errors():
            errors.append(
                ErrorDetail(
                    code="VALIDATION_ERROR",
                    message=error.get("msg", "Validation failed"),
                    field=".".join(str(loc) for loc in error.get("loc", [])),
                    details=error
                )
            )
    else:
        errors.append(
            ErrorDetail(
                code="VALIDATION_ERROR",
                message=str(exc)
            )
        )
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            status="error",
            message="Validation failed",
            errors=errors,
            request_id=getattr(request.state, "request_id", None)
        ).model_dump()
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure exception handlers."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(422, validation_exception_handler)
    
    logger.info("Exception handlers configured successfully")
