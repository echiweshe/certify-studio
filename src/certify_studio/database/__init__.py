"""
Database module for Certify Studio.

Provides database connection management, models, and repositories.
"""

from .connection import (
    DatabaseManager,
    database_manager,
    get_db
)

from .session import (
    DatabaseSession,
    TransactionManager,
    BatchProcessor,
    RetryableTransaction,
    get_db_session,
    atomic_operation
)

# Import all models
from .models import *

# Import all repositories
from .repositories import *

# Create an alias for backward compatibility
get_session = get_db

__all__ = [
    # Connection management
    "DatabaseManager",
    "database_manager",
    "get_db",
    "get_session",  # Alias for get_db
    
    # Session management
    "DatabaseSession",
    "TransactionManager",
    "BatchProcessor",
    "RetryableTransaction",
    "get_db_session",
    "atomic_operation",
    
    # Base model exports
    "Base",
    "BaseModel",
    "VersionedModel",
    "SoftDeleteModel",
    "FullAuditModel",
    
    # All models (imported from models module)
    "User",
    "Role",
    "Permission",
    "APIKey",
    "RefreshToken",
    "ContentGeneration",
    "ContentPiece",
    "MediaAsset",
    "ExportTask",
    "ExtractedConcept",
    "ConceptRelationship",
    "LearningPath",
    "QualityCheck",
    "QualityMetric",
    "UserFeedback",
    "UserActivity",
    "GenerationAnalytics",
    "DailyMetrics",
    
    # All repositories (imported from repositories module)
    "BaseRepository",
    "UserRepository",
    "RoleRepository",
    "PermissionRepository",
    "APIKeyRepository",
    "ContentGenerationRepository",
    "ContentPieceRepository",
    "MediaAssetRepository",
    "ExportTaskRepository"
]
