"""
Integration Layer for Certify Studio

This module connects all components:
- API endpoints to database repositories
- Agents to database for persistence
- Background task processing
- Event-driven architecture
"""

from .dependencies import (
    get_db,
    get_current_user,
    get_user_repository,
    get_content_generation_repository,
    get_content_piece_repository,
    get_media_asset_repository,
    get_export_task_repository,
)

from .services import (
    ContentGenerationService,
    DomainExtractionService,
    QualityAssuranceService,
    UserService,
    AnalyticsService,
)

from .background import (
    celery_app,
    process_content_generation,
    process_domain_extraction,
    process_quality_check,
    process_export_task,
)

from .events import (
    EventBus,
    ContentGenerationStartedEvent,
    ContentGenerationCompletedEvent,
    QualityCheckCompletedEvent,
    DomainExtractionCompletedEvent,
)

__all__ = [
    # Dependencies
    "get_db",
    "get_current_user",
    "get_user_repository",
    "get_content_generation_repository",
    "get_content_piece_repository",
    "get_media_asset_repository",
    "get_export_task_repository",
    
    # Services
    "ContentGenerationService",
    "DomainExtractionService",
    "QualityAssuranceService",
    "UserService",
    "AnalyticsService",
    
    # Background tasks
    "celery_app",
    "process_content_generation",
    "process_domain_extraction",
    "process_quality_check",
    "process_export_task",
    
    # Events
    "EventBus",
    "ContentGenerationStartedEvent",
    "ContentGenerationCompletedEvent",
    "QualityCheckCompletedEvent",
    "DomainExtractionCompletedEvent",
]
