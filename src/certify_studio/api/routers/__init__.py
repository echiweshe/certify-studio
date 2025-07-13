"""
API routers package.
"""

from .auth import router as auth_router
from .generation import router as generation_router
from .domains import router as domains_router
from .quality import router as quality_router
from .export import router as export_router

__all__ = [
    "auth_router",
    "generation_router",
    "domains_router",
    "quality_router",
    "export_router"
]
