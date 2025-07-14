"""
Common schemas used across the API.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class StatusEnum(str, Enum):
    """Status values for operations."""
    SUCCESS = "success"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutputFormat(str, Enum):
    """Supported output formats."""
    VIDEO_MP4 = "video/mp4"
    VIDEO_WEBM = "video/webm"
    INTERACTIVE_HTML = "interactive/html"
    SCORM_PACKAGE = "scorm/package"
    PDF_DOCUMENT = "pdf/document"
    POWERPOINT = "powerpoint/pptx"
    MARKDOWN = "text/markdown"


class CertificationType(str, Enum):
    """Supported certification types."""
    AWS_SAA = "aws-saa"
    AWS_DVA = "aws-dva"
    AWS_SOA = "aws-soa"
    AWS_SAP = "aws-sap"
    AWS_DOP = "aws-dop"
    AWS_ANS = "aws-ans"
    AWS_SCS = "aws-scs"
    AWS_DAS = "aws-das"
    AWS_MLS = "aws-mls"
    AWS_DBS = "aws-dbs"
    AZURE_AZ104 = "azure-az104"
    AZURE_AZ204 = "azure-az204"
    AZURE_AZ305 = "azure-az305"
    AZURE_AZ400 = "azure-az400"
    AZURE_AZ500 = "azure-az500"
    AZURE_AZ900 = "azure-az900"
    GCP_ACE = "gcp-ace"
    GCP_PCA = "gcp-pca"
    GCP_PCD = "gcp-pcd"
    GCP_PCDE = "gcp-pcde"
    GCP_PCNE = "gcp-pcne"
    GCP_PCSE = "gcp-pcse"
    GCP_PCML = "gcp-pcml"
    KUBERNETES_CKA = "kubernetes-cka"
    KUBERNETES_CKAD = "kubernetes-ckad"
    KUBERNETES_CKS = "kubernetes-cks"
    DOCKER_DCA = "docker-dca"
    TERRAFORM_ASSOCIATE = "terraform-associate"
    LINUX_LPIC1 = "linux-lpic1"
    LINUX_LPIC2 = "linux-lpic2"
    LINUX_RHCSA = "linux-rhcsa"
    LINUX_RHCE = "linux-rhce"
    COMPTIA_APLUS = "comptia-aplus"
    COMPTIA_NETWORKPLUS = "comptia-networkplus"
    COMPTIA_SECURITYPLUS = "comptia-securityplus"
    COMPTIA_CLOUDPLUS = "comptia-cloudplus"
    COMPTIA_LINUXPLUS = "comptia-linuxplus"
    CISCO_CCNA = "cisco-ccna"
    CISCO_CCNP = "cisco-ccnp"
    CISCO_CCIE = "cisco-ccie"
    VMWARE_VCP = "vmware-vcp"
    MICROSOFT_AZ900 = "microsoft-az900"
    CUSTOM = "custom"


class QualityLevel(str, Enum):
    """Content quality levels."""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class UserRole(str, Enum):
    """User roles."""
    USER = "user"
    PREMIUM_USER = "premium_user"
    ENTERPRISE_USER = "enterprise_user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class PlanType(str, Enum):
    """Subscription plan types."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class GenerationPhase(str, Enum):
    """Content generation phases."""
    EXTRACTION = "extraction"
    ANALYSIS = "analysis"
    PEDAGOGICAL_DESIGN = "pedagogical_design"
    CONTENT_CREATION = "content_creation"
    QUALITY_ASSURANCE = "quality_assurance"
    EXPORT = "export"


class ExportOptions(BaseModel):
    """Export configuration options."""
    model_config = ConfigDict(from_attributes=True)
    
    format: OutputFormat = Field(..., description="Output format")
    
    # Video options
    video_resolution: str = Field("1920x1080", description="Video resolution")
    video_fps: int = Field(30, description="Video frames per second")
    video_bitrate: str = Field("5M", description="Video bitrate")
    include_captions: bool = Field(True, description="Include captions")
    caption_language: str = Field("en", description="Caption language")
    
    # Interactive options
    include_navigation: bool = Field(True, description="Include navigation controls")
    include_progress_tracking: bool = Field(True, description="Track user progress")
    include_assessments: bool = Field(True, description="Include assessment questions")
    
    # PDF options
    pdf_layout: str = Field("portrait", pattern="^(portrait|landscape)$")
    include_toc: bool = Field(True, description="Include table of contents")
    include_glossary: bool = Field(True, description="Include glossary")
    
    # SCORM options
    scorm_version: str = Field("2004", pattern="^(1.2|2004)$")
    mastery_score: int = Field(80, ge=0, le=100)
    
    # General options
    include_source_references: bool = Field(True)
    include_branding: bool = Field(True)
    custom_branding: Optional[Dict[str, Any]] = Field(None)


class HealthCheck(BaseModel):
    """Health check response."""
    model_config = ConfigDict(from_attributes=True)
    
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(..., description="Individual service statuses")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    model_config = ConfigDict(from_attributes=True)
    
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Base model for paginated responses."""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    
    @classmethod
    def create(cls, items: List[Any], total: int, page: int, page_size: int):
        """Create paginated response."""
        pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )


class ErrorDetail(BaseModel):
    """Error detail information."""
    model_config = ConfigDict(from_attributes=True)
    
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response."""
    model_config = ConfigDict(from_attributes=True)
    
    status: str = Field("error", description="Status (always 'error')")
    message: str = Field(..., description="Error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed errors")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProgressUpdate(BaseModel):
    """Real-time progress update."""
    model_config = ConfigDict(from_attributes=True)
    
    task_id: UUID = Field(..., description="Task ID")
    phase: str = Field(..., description="Current phase")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    message: str = Field(..., description="Progress message")
    eta_seconds: Optional[float] = Field(None, description="Estimated time remaining")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class User(BaseModel):
    """User model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    
    # Account status
    is_active: bool = Field(True, description="Account is active")
    is_verified: bool = Field(False, description="Email is verified")
    is_admin: bool = Field(False, description="User is admin")
    
    # Subscription
    plan_type: PlanType = Field(PlanType.FREE, description="Subscription plan")
    plan_expires_at: Optional[datetime] = Field(None, description="Plan expiration date")
    
    # Usage
    total_generations: int = Field(0, description="Total content generations")
    total_storage_mb: float = Field(0, description="Total storage used in MB")
    
    # Timestamps
    created_at: datetime = Field(..., description="Account creation date")
    updated_at: datetime = Field(..., description="Last update date")
    last_login_at: Optional[datetime] = Field(None, description="Last login date")


class TokenData(BaseModel):
    """JWT token data."""
    model_config = ConfigDict(from_attributes=True)
    
    sub: str = Field(..., description="Subject (user ID)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    jti: Optional[str] = Field(None, description="JWT ID")
    scope: str = Field(..., description="Token scope (access/refresh)")


class RateLimitInfo(BaseModel):
    """Rate limit information."""
    model_config = ConfigDict(from_attributes=True)
    
    limit: int = Field(..., description="Request limit")
    remaining: int = Field(..., description="Remaining requests")
    reset_at: datetime = Field(..., description="Reset time")


class GenerationMetrics(BaseModel):
    """Metrics for generated content."""
    model_config = ConfigDict(from_attributes=True)
    
    # Content metrics
    total_concepts: int = Field(..., description="Total concepts extracted")
    total_animations: int = Field(..., description="Total animations created")
    total_diagrams: int = Field(..., description="Total diagrams generated")
    total_interactions: int = Field(0, description="Total interactive elements")
    
    # Performance metrics
    processing_time_seconds: float = Field(..., description="Total processing time")
    generation_phases: Dict[str, float] = Field(default_factory=dict, description="Time per phase")
    
    # Quality metrics
    quality_score: float = Field(..., ge=0, le=1, description="Overall quality score")
    pedagogical_score: float = Field(..., ge=0, le=1, description="Pedagogical effectiveness")
    technical_accuracy: float = Field(..., ge=0, le=1, description="Technical accuracy score")
    accessibility_score: float = Field(..., ge=0, le=1, description="Accessibility compliance")
    
    # Resource usage
    cpu_usage_percent: Optional[float] = Field(None, description="Peak CPU usage")
    memory_usage_mb: Optional[float] = Field(None, description="Peak memory usage")
    gpu_usage_percent: Optional[float] = Field(None, description="Peak GPU usage")
