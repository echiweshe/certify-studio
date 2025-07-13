"""
Certify Studio API - Production-ready REST API for educational content generation.

This API exposes the capabilities of our 4 specialized agents through a robust,
scalable, and secure interface.
"""

from .main import create_app
from .dependencies import get_current_user, get_db
from .schemas import (
    GenerationRequest,
    GenerationResponse,
    DomainExtractionRequest,
    QualityCheckRequest
)

__all__ = [
    "create_app",
    "get_current_user",
    "get_db",
    "GenerationRequest",
    "GenerationResponse",
    "DomainExtractionRequest",
    "QualityCheckRequest"
]
