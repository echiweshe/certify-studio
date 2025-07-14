"""
Base model configuration for Certify Studio database.

This module provides the base configuration for all SQLAlchemy models,
including timestamp mixins, UUID generation, and common patterns.
"""

from typing import Any, Dict, Type, TypeVar, Generic, Optional, List
from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, String, Boolean, Integer, func, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy.sql import func as sql_func

# Type variable for generic models
T = TypeVar("T")

# Create the declarative base
Base = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=sql_func.now(),
            nullable=False
        )
    
    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=sql_func.now(),
            onupdate=sql_func.now(),
            nullable=False
        )


class UUIDMixin:
    """Mixin to add UUID primary key to models."""
    
    @declared_attr
    def id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False
        )


class SoftDeleteMixin:
    """Mixin to add soft delete functionality to models."""
    
    @declared_attr
    def is_deleted(cls) -> Mapped[bool]:
        return mapped_column(
            Boolean,
            default=False,
            nullable=False,
            index=True
        )
    
    @declared_attr
    def deleted_at(cls) -> Mapped[Optional[datetime]]:
        return mapped_column(
            DateTime(timezone=True),
            nullable=True
        )
    
    def soft_delete(self) -> None:
        """Mark the record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """Mixin to add audit fields to models."""
    
    @declared_attr
    def created_by(cls) -> Mapped[Optional[uuid.UUID]]:
        return mapped_column(
            UUID(as_uuid=True),
            nullable=True
        )
    
    @declared_attr
    def updated_by(cls) -> Mapped[Optional[uuid.UUID]]:
        return mapped_column(
            UUID(as_uuid=True),
            nullable=True
        )
    
    @declared_attr
    def version(cls) -> Mapped[int]:
        return mapped_column(
            Integer,
            default=1,
            nullable=False
        )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """Base model class with common fields."""
    __abstract__ = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            else:
                result[column.name] = value
        return result
    
    def update(self, **kwargs) -> None:
        """Update model attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """Create model instance from dictionary."""
        return cls(**{
            key: value for key, value in data.items()
            if hasattr(cls, key)
        })


class VersionedModel(BaseModel, AuditMixin):
    """Base model with versioning support."""
    __abstract__ = True
    
    def increment_version(self) -> None:
        """Increment the version number."""
        self.version += 1


class SoftDeleteModel(BaseModel, SoftDeleteMixin):
    """Base model with soft delete support."""
    __abstract__ = True


class FullAuditModel(BaseModel, AuditMixin, SoftDeleteMixin):
    """Base model with full audit trail and soft delete."""
    __abstract__ = True


# Event listeners for automatic timestamp updates
@event.listens_for(TimestampMixin, "before_update", propagate=True)
def timestamp_before_update(mapper, connection, target):
    """Update the updated_at timestamp before update."""
    target.updated_at = datetime.utcnow()


# Enum-like classes for database constants
class UserRole:
    """User role constants."""
    ADMIN = "admin"
    MODERATOR = "moderator"
    CREATOR = "creator"
    VIEWER = "viewer"
    API_USER = "api_user"


class PlanType:
    """Subscription plan types."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class TaskStatus:
    """Task status constants."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class ContentStatus:
    """Content status constants."""
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    FAILED = "failed"


class QualityStatus:
    """Quality check status constants."""
    PENDING = "pending"
    CHECKING = "checking"
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class ExportFormat:
    """Export format constants."""
    VIDEO = "video"
    INTERACTIVE = "interactive"
    SCORM = "scorm"
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"
    POWERPOINT = "powerpoint"


class MediaType:
    """Media type constants."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    ANIMATION = "animation"
    DIAGRAM = "diagram"
    INTERACTIVE = "interactive"


class NotificationType:
    """Notification type constants."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    QUALITY_ALERT = "quality_alert"
    SYSTEM_ALERT = "system_alert"


# Utility functions
def generate_uuid() -> uuid.UUID:
    """Generate a new UUID4."""
    return uuid.uuid4()


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.utcnow()


# Export all base classes and utilities
__all__ = [
    "Base",
    "BaseModel",
    "VersionedModel",
    "SoftDeleteModel",
    "FullAuditModel",
    "TimestampMixin",
    "UUIDMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    "UserRole",
    "PlanType",
    "TaskStatus",
    "ContentStatus",
    "QualityStatus",
    "ExportFormat",
    "MediaType",
    "NotificationType",
    "generate_uuid",
    "utcnow"
]
