"""
Database repositories for Certify Studio.

This module exports all repository classes for easy importing
throughout the application.
"""

from .base_repo import (
    BaseRepository,
    RepositoryError,
    NotFoundError,
    DuplicateError
)

from .user_repo import (
    UserRepository,
    RoleRepository,
    PermissionRepository,
    UserRoleRepository,
    APIKeyRepository,
    RefreshTokenRepository,
    PasswordResetTokenRepository
)

from .content_repo import (
    ContentGenerationRepository,
    ContentPieceRepository,
    MediaAssetRepository,
    ContentInteractionRepository,
    ExportTaskRepository
)

from .domain_repo import DomainRepository
from .quality_repo import QualityRepository
from .analytics_repo import AnalyticsRepository

# Export all items
__all__ = [
    # Base repository
    "BaseRepository",
    "RepositoryError",
    "NotFoundError",
    "DuplicateError",
    # User repositories
    "UserRepository",
    "RoleRepository",
    "PermissionRepository",
    "UserRoleRepository",
    "APIKeyRepository",
    "RefreshTokenRepository",
    "PasswordResetTokenRepository",
    # Content repositories
    "ContentGenerationRepository",
    "ContentPieceRepository",
    "MediaAssetRepository",
    "ContentInteractionRepository",
    "ExportTaskRepository",
    # Domain repository
    "DomainRepository",
    # Quality repository
    "QualityRepository",
    # Analytics repository
    "AnalyticsRepository"
]
