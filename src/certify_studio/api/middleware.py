"""
API Middleware Components

Custom middleware for request logging, rate limiting, security headers,
and other cross-cutting concerns.
"""

import time
import uuid
from typing import Callable
import logging

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..config import settings

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with timing information."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration
                }
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "duration": duration,
                    "error": str(e)
                }
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware using in-memory storage."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limit_storage = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
            
        # Get client identifier (IP address)
        client_id = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/status"]:
            return await call_next(request)
        
        # Check rate limit
        current_time = time.time()
        window_start = current_time - settings.RATE_LIMIT_WINDOW
        
        # Clean old entries
        if client_id in self.rate_limit_storage:
            self.rate_limit_storage[client_id] = [
                timestamp for timestamp in self.rate_limit_storage[client_id]
                if timestamp > window_start
            ]
        else:
            self.rate_limit_storage[client_id] = []
        
        # Check if limit exceeded
        request_count = len(self.rate_limit_storage[client_id])
        
        if request_count >= settings.RATE_LIMIT_REQUESTS:
            logger.warning(
                f"Rate limit exceeded",
                extra={
                    "client_id": client_id,
                    "request_count": request_count
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": settings.RATE_LIMIT_WINDOW
                },
                headers={
                    "Retry-After": str(settings.RATE_LIMIT_WINDOW),
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(window_start + settings.RATE_LIMIT_WINDOW))
                }
            )
        
        # Record request
        self.rate_limit_storage[client_id].append(current_time)
        
        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(
            settings.RATE_LIMIT_REQUESTS - request_count - 1
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(window_start + settings.RATE_LIMIT_WINDOW)
        )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy (adjust as needed)
        if not settings.DEBUG:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' wss: https:;"
            )
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Custom compression middleware with configurable settings."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Process request
        response = await call_next(request)
        
        # Check if compression is appropriate
        if (
            response.status_code < 200 or
            response.status_code >= 300 or
            "Content-Encoding" in response.headers or
            int(response.headers.get("Content-Length", 0)) < 1000
        ):
            return response
        
        # Check Accept-Encoding header
        accept_encoding = request.headers.get("Accept-Encoding", "")
        if "gzip" not in accept_encoding:
            return response
        
        # Compression is handled by GZipMiddleware
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Centralized error handling middleware."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
            
        except HTTPException:
            # Let FastAPI handle HTTP exceptions
            raise
            
        except Exception as e:
            logger.error(
                f"Unhandled exception in middleware",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "path": request.url.path,
                    "error": str(e)
                },
                exc_info=True
            )
            
            # Return generic error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error",
                    "request_id": getattr(request.state, "request_id", None)
                }
            )
