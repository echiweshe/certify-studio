"""
Common schemas used across the API.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class StatusEnum(str, Enum):
    """API response status values."""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OutputFormat(str, Enum):
    """Supported output formats."""
    VIDEO_MP4 = "video/mp4"
    VIDEO_WEBM = "video/webm"
    INTERACTIVE_HTML = "interactive/html"
    SCORM_PACKAGE = "scorm/package"
    PDF_DOCUMENT = "pdf/document"
    POWERPOINT = "powerpoint/pptx"


class CertificationType(str, Enum):
    """Supported certification types."""
    AWS_SAA = "aws-saa"
    AWS_SAP = "aws-sap"
    AWS_DEV = "aws-dev"
    AZURE_AZ900 = "azure-az900"
    AZURE_AZ104 = "azure-az104"
    GCP_ACE = "gcp-ace"
    KUBERNETES_CKA = "kubernetes-cka"
    DOCKER_DCA = "docker-dca"
    CUSTOM = "custom"


class QualityLevel(str, Enum):
    """Quality level presets."""
    DRAFT = "draft"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    PREMIUM = "premium"


class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    status: StatusEnum = Field(..., description="Response status")
    message: Optional[str] = Field(None, description="Human-readable message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[UUID] = Field(None, description="Request tracking ID")


class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ErrorResponse(BaseResponse):
    """Error response model."""
    status: StatusEnum = StatusEnum.ERROR
    errors: List[ErrorDetail] = Field(..., description="List of errors")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseResponse):
    """Base model for paginated responses."""
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(..., description="Status of dependent services")


class FileUpload(BaseModel):
    """File upload information."""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type")
    size: int = Field(..., description="File size in bytes")
    upload_id: UUID = Field(..., description="Upload tracking ID")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class ProgressUpdate(BaseModel):
    """Real-time progress update."""
    task_id: UUID = Field(..., description="Task ID")
    phase: str = Field(..., description="Current phase")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    message: str = Field(..., description="Progress message")
    eta_seconds: Optional[int] = Field(None, description="Estimated time remaining")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class User(BaseModel):
    """User model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: str
    username: str
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class TokenData(BaseModel):
    """JWT token data."""
    sub: str  # Subject (user ID)
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    jti: str  # JWT ID
    scope: str = "access"  # Token scope (access/refresh)


class GenerationMetrics(BaseModel):
    """Metrics for a generation task."""
    total_concepts: int = Field(..., description="Total concepts extracted")
    total_animations: int = Field(..., description="Total animations created")
    total_diagrams: int = Field(..., description="Total diagrams generated")
    processing_time_seconds: float = Field(..., description="Total processing time")
    quality_score: float = Field(..., ge=0, le=1, description="Overall quality score")
    pedagogical_score: float = Field(..., ge=0, le=1, description="Pedagogical effectiveness")
    technical_accuracy: float = Field(..., ge=0, le=1, description="Technical accuracy score")
    accessibility_score: float = Field(..., ge=0, le=1, description="Accessibility compliance")


class ExportOptions(BaseModel):
    """Export configuration options."""
    format: OutputFormat = Field(..., description="Export format")
    quality: QualityLevel = Field(QualityLevel.STANDARD, description="Quality level")
    include_subtitles: bool = Field(True, description="Include subtitles/captions")
    include_interactivity: bool = Field(True, description="Include interactive elements")
    custom_branding: Optional[Dict[str, Any]] = Field(None, description="Custom branding options")
    optimization_profile: Optional[str] = Field(None, description="Optimization profile")


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    
class RateLimitInfo(BaseModel):
    """Rate limit information."""
    limit: int = Field(..., description="Request limit")
    remaining: int = Field(..., description="Remaining requests")
    reset_at: datetime = Field(..., description="Reset timestamp")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")
