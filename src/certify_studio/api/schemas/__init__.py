"""
API schemas for request/response models.
"""

from .common import (
    StatusEnum,
    OutputFormat,
    CertificationType,
    QualityLevel,
    UserRole,
    PlanType,
    GenerationPhase,
    ExportOptions,
    HealthCheck,
    PaginationParams,
    PaginatedResponse,
    ErrorDetail,
    ErrorResponse,
    ProgressUpdate,
    User,
    TokenData,
    RateLimitInfo,
    GenerationMetrics
)

from .requests import (
    GenerationRequest,
    DomainExtractionRequest,
    QualityCheckRequest,
    ContentUpdateRequest,
    ExportRequest,
    FeedbackSubmission,
    BatchGenerationRequest,
    AnalyticsRequest,
    UserPreferences,
    ContentSearchRequest
)

from .responses import (
    BaseResponse,
    GenerationResponse,
    DomainExtractionResponse,
    QualityCheckResponse,
    ExportResponse,
    ContentListResponse,
    UserContentStats,
    AnalyticsResponse,
    AuthTokenResponse,
    UploadResponse,
    BatchGenerationResponse,
    FeedbackResponse,
    SystemInfoResponse,
    WebSocketMessage
)

__all__ = [
    # Common
    "StatusEnum",
    "OutputFormat",
    "CertificationType",
    "QualityLevel",
    "UserRole",
    "PlanType",
    "GenerationPhase",
    "ExportOptions",
    "HealthCheck",
    "PaginationParams",
    "PaginatedResponse",
    "ErrorDetail",
    "ErrorResponse",
    "ProgressUpdate",
    "User",
    "TokenData",
    "RateLimitInfo",
    "GenerationMetrics",
    
    # Requests
    "GenerationRequest",
    "DomainExtractionRequest",
    "QualityCheckRequest",
    "ContentUpdateRequest",
    "ExportRequest",
    "FeedbackSubmission",
    "BatchGenerationRequest",
    "AnalyticsRequest",
    "UserPreferences",
    "ContentSearchRequest",
    
    # Responses
    "BaseResponse",
    "GenerationResponse",
    "DomainExtractionResponse",
    "QualityCheckResponse",
    "ExportResponse",
    "ContentListResponse",
    "UserContentStats",
    "AnalyticsResponse",
    "AuthTokenResponse",
    "UploadResponse",
    "BatchGenerationResponse",
    "FeedbackResponse",
    "SystemInfoResponse",
    "WebSocketMessage"
]
