"""
API schemas package.
"""

from .common import (
    StatusEnum,
    OutputFormat,
    CertificationType,
    QualityLevel,
    BaseResponse,
    ErrorResponse,
    ErrorDetail,
    PaginationParams,
    PaginatedResponse,
    HealthCheck,
    FileUpload,
    ProgressUpdate,
    User,
    TokenData,
    GenerationMetrics,
    ExportOptions,
    WebSocketMessage,
    RateLimitInfo
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
    GenerationResponse,
    DomainExtractionResponse,
    QualityCheckResponse,
    ContentResponse,
    ContentListResponse,
    ExportResponse,
    FeedbackResponse,
    BatchGenerationResponse,
    AnalyticsResponse,
    UserResponse,
    AuthResponse,
    RateLimitResponse,
    WebSocketAuthResponse,
    ProgressStreamResponse
)

__all__ = [
    # Common
    "StatusEnum",
    "OutputFormat",
    "CertificationType",
    "QualityLevel",
    "BaseResponse",
    "ErrorResponse",
    "ErrorDetail",
    "PaginationParams",
    "PaginatedResponse",
    "HealthCheck",
    "FileUpload",
    "ProgressUpdate",
    "User",
    "TokenData",
    "GenerationMetrics",
    "ExportOptions",
    "WebSocketMessage",
    "RateLimitInfo",
    
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
    "GenerationResponse",
    "DomainExtractionResponse",
    "QualityCheckResponse",
    "ContentResponse",
    "ContentListResponse",
    "ExportResponse",
    "FeedbackResponse",
    "BatchGenerationResponse",
    "AnalyticsResponse",
    "UserResponse",
    "AuthResponse",
    "RateLimitResponse",
    "WebSocketAuthResponse",
    "ProgressStreamResponse"
]
