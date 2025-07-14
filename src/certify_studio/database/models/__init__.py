"""
Database models for Certify Studio.

This module exports all database models for easy importing throughout the application.
"""

# Base models and utilities
from .base import (
    Base,
    BaseModel,
    VersionedModel,
    SoftDeleteModel,
    FullAuditModel,
    TimestampMixin,
    UUIDMixin,
    SoftDeleteMixin,
    AuditMixin,
    # Constants
    UserRole,
    PlanType,
    TaskStatus,
    ContentStatus,
    QualityStatus,
    ExportFormat,
    MediaType,
    NotificationType,
    # Utilities
    generate_uuid,
    utcnow
)

# User and authentication models
from .user import (
    User,
    Role,
    Permission,
    UserRoleAssignment,
    RolePermissionAssignment,
    APIKey,
    RefreshToken,
    PasswordResetToken,
    OAuthConnection
)

# Content and generation models
from .content import (
    ContentType,
    InteractionType,
    ContentGeneration,
    ContentPiece,
    MediaAsset,
    MediaReference,
    ContentInteraction,
    ExportTask,
    ContentVersion
)

# Domain extraction and knowledge models
from .domain import (
    ConceptType,
    RelationshipType,
    DifficultyLevel,
    ExtractedConcept,
    CanonicalConcept,
    ConceptRelationship,
    LearningObjective,
    PrerequisiteMapping,
    LearningPath,
    LearningPathNode,
    DomainTaxonomy
)

# Quality assurance models
from .quality import (
    QualityDimension,
    FeedbackType,
    BenchmarkType,
    QualityCheck,
    QualityMetric,
    QualityIssue,
    QualityBenchmark,
    UserFeedback,
    ConceptQualityScore,
    ContentImprovement,
    QualityReport
)

# Analytics and tracking models
from .analytics import (
    EventType,
    MetricType,
    UserActivity,
    GenerationAnalytics,
    DailyMetrics,
    FeatureUsage,
    PerformanceMetrics,
    BusinessMetric,
    UserSegment,
    UserSegmentMembership,
    ABTestExperiment
)

# Export all models
__all__ = [
    # Base
    "Base",
    "BaseModel",
    "VersionedModel",
    "SoftDeleteModel",
    "FullAuditModel",
    "TimestampMixin",
    "UUIDMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    # Constants
    "UserRole",
    "PlanType",
    "TaskStatus",
    "ContentStatus",
    "QualityStatus",
    "ExportFormat",
    "MediaType",
    "NotificationType",
    # Utilities
    "generate_uuid",
    "utcnow",
    # User models
    "User",
    "Role",
    "Permission",
    "UserRoleAssignment",
    "RolePermissionAssignment",
    "APIKey",
    "RefreshToken",
    "PasswordResetToken",
    "OAuthConnection",
    # Content models
    "ContentType",
    "InteractionType",
    "ContentGeneration",
    "ContentPiece",
    "MediaAsset",
    "MediaReference",
    "ContentInteraction",
    "ExportTask",
    "ContentVersion",
    # Domain models
    "ConceptType",
    "RelationshipType",
    "DifficultyLevel",
    "ExtractedConcept",
    "CanonicalConcept",
    "ConceptRelationship",
    "LearningObjective",
    "PrerequisiteMapping",
    "LearningPath",
    "LearningPathNode",
    "DomainTaxonomy",
    # Quality models
    "QualityDimension",
    "FeedbackType",
    "BenchmarkType",
    "QualityCheck",
    "QualityMetric",
    "QualityIssue",
    "QualityBenchmark",
    "UserFeedback",
    "ConceptQualityScore",
    "ContentImprovement",
    "QualityReport",
    # Analytics models
    "EventType",
    "MetricType",
    "UserActivity",
    "GenerationAnalytics",
    "DailyMetrics",
    "FeatureUsage",
    "PerformanceMetrics",
    "BusinessMetric",
    "UserSegment",
    "UserSegmentMembership",
    "ABTestExperiment"
]

# Model registry for easy access
MODEL_REGISTRY = {
    # User models
    "User": User,
    "Role": Role,
    "Permission": Permission,
    "UserRoleAssignment": UserRoleAssignment,
    "RolePermissionAssignment": RolePermissionAssignment,
    "APIKey": APIKey,
    "RefreshToken": RefreshToken,
    "PasswordResetToken": PasswordResetToken,
    "OAuthConnection": OAuthConnection,
    # Content models
    "ContentGeneration": ContentGeneration,
    "ContentPiece": ContentPiece,
    "MediaAsset": MediaAsset,
    "MediaReference": MediaReference,
    "ContentInteraction": ContentInteraction,
    "ExportTask": ExportTask,
    "ContentVersion": ContentVersion,
    # Domain models
    "ExtractedConcept": ExtractedConcept,
    "CanonicalConcept": CanonicalConcept,
    "ConceptRelationship": ConceptRelationship,
    "LearningObjective": LearningObjective,
    "PrerequisiteMapping": PrerequisiteMapping,
    "LearningPath": LearningPath,
    "LearningPathNode": LearningPathNode,
    "DomainTaxonomy": DomainTaxonomy,
    # Quality models
    "QualityCheck": QualityCheck,
    "QualityMetric": QualityMetric,
    "QualityIssue": QualityIssue,
    "QualityBenchmark": QualityBenchmark,
    "UserFeedback": UserFeedback,
    "ConceptQualityScore": ConceptQualityScore,
    "ContentImprovement": ContentImprovement,
    "QualityReport": QualityReport,
    # Analytics models
    "UserActivity": UserActivity,
    "GenerationAnalytics": GenerationAnalytics,
    "DailyMetrics": DailyMetrics,
    "FeatureUsage": FeatureUsage,
    "PerformanceMetrics": PerformanceMetrics,
    "BusinessMetric": BusinessMetric,
    "UserSegment": UserSegment,
    "UserSegmentMembership": UserSegmentMembership,
    "ABTestExperiment": ABTestExperiment
}


def get_model_by_name(model_name: str):
    """Get a model class by its name."""
    return MODEL_REGISTRY.get(model_name)


def get_all_models():
    """Get all model classes."""
    return list(MODEL_REGISTRY.values())


def get_model_tablenames():
    """Get all table names used by models."""
    return {
        model.__tablename__: model 
        for model in MODEL_REGISTRY.values()
        if hasattr(model, '__tablename__')
    }
