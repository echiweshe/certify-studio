"""
Distributed Tracing

Sets up OpenTelemetry tracing for monitoring request flows across services.
"""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from ...config import settings


def setup_tracing():
    """
    Configure OpenTelemetry distributed tracing.
    
    Sets up:
    - Tracer provider with service information
    - OTLP exporter for Jaeger/other backends
    - Auto-instrumentation for common libraries
    """
    if not settings.ENABLE_TRACING:
        return
    
    # Configure tracer provider
    resource = Resource.create({
        "service.name": "certify-studio",
        "service.version": settings.APP_VERSION,
        "deployment.environment": settings.ENVIRONMENT,
    })
    
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    # Configure exporter
    if settings.JAEGER_ENDPOINT:
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.JAEGER_ENDPOINT,
            insecure=True
        )
        
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)
    
    # Get tracer
    tracer = trace.get_tracer(__name__)
    
    return tracer


def instrument_app(app):
    """
    Instrument FastAPI application with tracing.
    
    Args:
        app: FastAPI application instance
    """
    if not settings.ENABLE_TRACING:
        return
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument SQLAlchemy
    # This would be called with the engine instance
    # SQLAlchemyInstrumentor().instrument(engine=engine)
    
    # Instrument Redis
    RedisInstrumentor().instrument()
    
    # Instrument HTTP client
    HTTPXClientInstrumentor().instrument()


def create_span(name: str, attributes: dict = None):
    """
    Create a new span for tracing.
    
    Args:
        name: Span name
        attributes: Optional span attributes
        
    Returns:
        Span context manager
    """
    tracer = trace.get_tracer(__name__)
    
    span = tracer.start_as_current_span(
        name,
        attributes=attributes or {}
    )
    
    return span


def add_span_attributes(attributes: dict):
    """
    Add attributes to the current span.
    
    Args:
        attributes: Dictionary of attributes to add
    """
    span = trace.get_current_span()
    if span:
        for key, value in attributes.items():
            span.set_attribute(key, value)


def record_exception(exception: Exception):
    """
    Record an exception in the current span.
    
    Args:
        exception: Exception to record
    """
    span = trace.get_current_span()
    if span:
        span.record_exception(exception)
        span.set_status(trace.Status(trace.StatusCode.ERROR))
