"""
Metrics Collection

Sets up Prometheus metrics collection for monitoring application performance.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps

from ...config import settings

# Application info
app_info = Info(
    "certify_studio_info",
    "Application information"
)

# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

# Generation metrics
content_generations_total = Counter(
    "content_generations_total",
    "Total content generation requests",
    ["certification_type", "status"]
)

content_generation_duration_seconds = Histogram(
    "content_generation_duration_seconds",
    "Content generation duration in seconds",
    ["certification_type"]
)

# Active operations
active_generations = Gauge(
    "active_generations",
    "Number of active content generations"
)

# Database metrics
database_connections_active = Gauge(
    "database_connections_active",
    "Active database connections"
)

database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"]
)

# Cache metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"]
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"]
)

# AI service metrics
ai_service_requests_total = Counter(
    "ai_service_requests_total",
    "Total AI service requests",
    ["service", "operation", "status"]
)

ai_service_tokens_used = Counter(
    "ai_service_tokens_used",
    "Total tokens used by AI services",
    ["service", "operation"]
)


def setup_metrics():
    """Initialize metrics collection."""
    # Set application info
    app_info.info({
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "name": settings.APP_NAME
    })


def track_request_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """Track HTTP request metrics."""
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=str(status_code)
    ).inc()
    
    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_generation_metrics(func):
    """Decorator to track content generation metrics."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        certification_type = kwargs.get("certification_type", "unknown")
        
        active_generations.inc()
        
        try:
            result = await func(*args, **kwargs)
            status = "success"
            return result
        except Exception as e:
            status = "error"
            raise e
        finally:
            duration = time.time() - start_time
            
            content_generations_total.labels(
                certification_type=certification_type,
                status=status
            ).inc()
            
            content_generation_duration_seconds.labels(
                certification_type=certification_type
            ).observe(duration)
            
            active_generations.dec()
    
    return wrapper


def track_cache_access(cache_type: str, hit: bool):
    """Track cache access metrics."""
    if hit:
        cache_hits_total.labels(cache_type=cache_type).inc()
    else:
        cache_misses_total.labels(cache_type=cache_type).inc()


def track_ai_service_usage(
    service: str,
    operation: str,
    status: str,
    tokens: int = 0
):
    """Track AI service usage metrics."""
    ai_service_requests_total.labels(
        service=service,
        operation=operation,
        status=status
    ).inc()
    
    if tokens > 0:
        ai_service_tokens_used.labels(
            service=service,
            operation=operation
        ).inc(tokens)
