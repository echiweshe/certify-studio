"""
Response schemas for API endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from .common import (
    StatusEnum,
    OutputFormat,
    GenerationPhase,
    GenerationMetrics,
    PaginatedResponse,
    ProgressUpdate
)


class BaseResponse(BaseModel):
    """Base response model."""
    model_config = ConfigDict(from_attributes=True)
    
    status: StatusEnum = Field(..., description="Operation status")
    message: str = Field(..., description="Response message")
    request_id: UUID = Field(..., description="Request tracking ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GenerationResponse(BaseResponse):
    """Response for content generation requests."""
    model_config = ConfigDict(from_attributes=True)
    
    task_id: UUID = Field(..., description="Generation task ID")
    generation_status: StatusEnum = Field(..., description="Generation status")
    progress: float = Field(0, ge=0, le=100, description="Progress percentage")
    current_phase: Optional[GenerationPhase] = Field(None, description="Current generation phase")
    
    # Timing
    started_at: datetime = Field(..., description="Generation start time")
    completed_at: Optional[datetime] = Field(None, description="Generation completion time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    
    # Results (when completed)
    download_urls: Optional[Dict[str, str]] = Field(None, description="Download URLs by format")
    preview_url: Optional[str] = Field(None, description="Preview URL")
    metrics: Optional[GenerationMetrics] = Field(None, description="Generation metrics")


class DomainExtractionResponse(BaseResponse):
    """Response for domain extraction requests."""
    model_config = ConfigDict(from_attributes=True)
    
    extraction_id: UUID = Field(..., description="Extraction task ID")
    
    # Results
    total_concepts: int = Field(..., description="Total concepts extracted")
    total_relationships: int = Field(..., description="Total relationships found")
    total_prerequisites: int = Field(..., description="Total prerequisites identified")
    
    # Domain structure
    domains: List[Dict[str, Any]] = Field(..., description="Extracted domains with weights")
    concept_graph: Optional[Dict[str, Any]] = Field(None, description="Concept relationship graph")
    learning_paths: Optional[List[Dict[str, Any]]] = Field(None, description="Suggested learning paths")
    
    # Confidence metrics
    overall_confidence: float = Field(..., ge=0, le=1, description="Overall extraction confidence")
    domain_confidences: Dict[str, float] = Field(..., description="Confidence by domain")


class QualityCheckResponse(BaseResponse):
    """Response for quality check requests."""
    model_config = ConfigDict(from_attributes=True)
    
    check_id: UUID = Field(..., description="Quality check ID")
    content_id: UUID = Field(..., description="Content ID that was checked")
    
    # Overall scores
    overall_quality: float = Field(..., ge=0, le=1, description="Overall quality score")
    passed: bool = Field(..., description="Whether content passed quality checks")
    
    # Detailed scores
    technical_accuracy: float = Field(..., ge=0, le=1, description="Technical accuracy score")
    pedagogical_effectiveness: float = Field(..., ge=0, le=1, description="Teaching effectiveness")
    accessibility_compliance: float = Field(..., ge=0, le=1, description="Accessibility score")
    certification_alignment: float = Field(..., ge=0, le=1, description="Exam alignment score")
    
    # Issues found
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="Quality issues found")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    
    # Benchmarks
    benchmark_comparison: Optional[Dict[str, Any]] = Field(None, description="Industry benchmark comparison")


class ExportResponse(BaseResponse):
    """Response for export requests."""
    model_config = ConfigDict(from_attributes=True)
    
    export_id: UUID = Field(..., description="Export task ID")
    content_id: UUID = Field(..., description="Content ID being exported")
    
    # Export details
    format: OutputFormat = Field(..., description="Export format")
    export_status: StatusEnum = Field(..., description="Export status")
    
    # Results (when completed)
    download_url: Optional[str] = Field(None, description="Download URL")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    expires_at: Optional[datetime] = Field(None, description="Download expiration time")
    
    # Export metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Format-specific metadata")


class ContentListResponse(PaginatedResponse):
    """Response for content listing."""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[Dict[str, Any]] = Field(..., description="List of content items")


class UserContentStats(BaseModel):
    """User content statistics."""
    model_config = ConfigDict(from_attributes=True)
    
    total_content_generated: int = Field(..., description="Total content pieces generated")
    total_export_count: int = Field(..., description="Total exports performed")
    average_quality_score: float = Field(..., description="Average quality score")
    total_concepts_covered: int = Field(..., description="Total unique concepts covered")
    most_used_certification: Optional[str] = Field(None, description="Most frequently used cert type")
    
    # Time-based stats
    content_this_month: int = Field(..., description="Content generated this month")
    content_this_week: int = Field(..., description="Content generated this week")
    
    # Storage
    total_storage_used_mb: float = Field(..., description="Total storage used in MB")
    storage_limit_mb: float = Field(..., description="Storage limit in MB")


class AnalyticsResponse(BaseResponse):
    """Response for analytics requests."""
    model_config = ConfigDict(from_attributes=True)
    
    # Time range
    start_date: datetime = Field(..., description="Analytics start date")
    end_date: datetime = Field(..., description="Analytics end date")
    
    # Usage metrics
    total_generations: int = Field(..., description="Total generations in period")
    unique_users: int = Field(..., description="Unique active users")
    average_generation_time: float = Field(..., description="Average generation time in seconds")
    
    # Quality metrics
    average_quality_score: float = Field(..., description="Average quality score")
    quality_score_trend: List[Dict[str, Any]] = Field(..., description="Quality score over time")
    
    # Performance metrics
    success_rate: float = Field(..., description="Generation success rate")
    average_processing_time: float = Field(..., description="Average processing time")
    peak_usage_times: List[Dict[str, Any]] = Field(..., description="Peak usage periods")
    
    # Content metrics
    popular_certifications: List[Dict[str, Any]] = Field(..., description="Most popular certifications")
    output_format_distribution: Dict[str, int] = Field(..., description="Output format usage")
    
    # User feedback
    average_user_rating: Optional[float] = Field(None, description="Average user rating")
    feedback_summary: Optional[Dict[str, Any]] = Field(None, description="Feedback summary")


class AuthTokenResponse(BaseModel):
    """Authentication token response."""
    model_config = ConfigDict(from_attributes=True)
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    
    # User info
    user_id: UUID = Field(..., description="Authenticated user ID")
    email: str = Field(..., description="User email")
    plan_type: str = Field(..., description="User's subscription plan")


class UploadResponse(BaseResponse):
    """Response for file upload."""
    model_config = ConfigDict(from_attributes=True)
    
    upload_id: UUID = Field(..., description="Upload ID for reference")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    
    # Processing info
    processing_status: StatusEnum = Field(StatusEnum.PENDING, description="Processing status")
    extracted_metadata: Optional[Dict[str, Any]] = Field(None, description="Extracted file metadata")


class BatchGenerationResponse(BaseResponse):
    """Response for batch generation requests."""
    model_config = ConfigDict(from_attributes=True)
    
    batch_id: UUID = Field(..., description="Batch operation ID")
    total_requests: int = Field(..., description="Total requests in batch")
    
    # Status tracking
    completed_count: int = Field(0, description="Completed generations")
    failed_count: int = Field(0, description="Failed generations")
    pending_count: int = Field(..., description="Pending generations")
    
    # Individual results
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Individual generation results")
    
    # Timing
    batch_started_at: datetime = Field(..., description="Batch start time")
    batch_completed_at: Optional[datetime] = Field(None, description="Batch completion time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


class FeedbackResponse(BaseResponse):
    """Response for feedback submission."""
    model_config = ConfigDict(from_attributes=True)
    
    feedback_id: UUID = Field(..., description="Feedback submission ID")
    content_id: UUID = Field(..., description="Content ID feedback relates to")
    
    # Acknowledgment
    thank_you_message: str = Field("Thank you for your feedback!", description="Thank you message")
    
    # Impact
    will_impact_future_generations: bool = Field(True, description="Whether feedback will be used")
    similar_feedback_count: int = Field(0, description="Number of similar feedback items")


class SystemInfoResponse(BaseModel):
    """System information response."""
    model_config = ConfigDict(from_attributes=True)
    
    version: str = Field(..., description="System version")
    api_version: str = Field(..., description="API version")
    
    # Capabilities
    supported_certifications: List[str] = Field(..., description="Supported certification types")
    supported_output_formats: List[str] = Field(..., description="Supported output formats")
    supported_languages: List[str] = Field(..., description="Supported languages")
    
    # Agent status
    agent_statuses: Dict[str, str] = Field(..., description="Status of each agent")
    
    # System health
    system_health: str = Field(..., description="Overall system health")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    
    # Limits
    max_file_size_mb: int = Field(..., description="Maximum upload file size in MB")
    max_generation_duration_minutes: int = Field(..., description="Maximum generation duration")
    rate_limits: Dict[str, int] = Field(..., description="Rate limits by plan type")


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    model_config = ConfigDict(from_attributes=True)
    
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # For progress updates
    task_id: Optional[UUID] = Field(None, description="Associated task ID")
    progress: Optional[float] = Field(None, description="Progress percentage")
    phase: Optional[str] = Field(None, description="Current phase")
    
    # For errors
    error: Optional[str] = Field(None, description="Error message if applicable")
    error_code: Optional[str] = Field(None, description="Error code if applicable")
