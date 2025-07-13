"""
Response schemas for the API endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, HttpUrl

from .common import (
    BaseResponse,
    StatusEnum,
    OutputFormat,
    PaginatedResponse,
    GenerationMetrics,
    RateLimitInfo
)


class GenerationResponse(BaseResponse):
    """Response for content generation request."""
    model_config = ConfigDict(from_attributes=True)
    
    task_id: UUID = Field(..., description="Task ID for tracking")
    content_id: Optional[UUID] = Field(None, description="Generated content ID")
    
    # Status
    generation_status: StatusEnum = Field(..., description="Generation status")
    progress: float = Field(0, ge=0, le=100, description="Progress percentage")
    current_phase: Optional[str] = Field(None, description="Current processing phase")
    
    # Results (when completed)
    download_urls: Optional[Dict[OutputFormat, HttpUrl]] = Field(None, description="Download URLs by format")
    preview_url: Optional[HttpUrl] = Field(None, description="Preview URL")
    metrics: Optional[GenerationMetrics] = Field(None, description="Generation metrics")
    
    # Timing
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    estimated_completion: Optional[datetime] = Field(None)


class DomainExtractionResponse(BaseResponse):
    """Response for domain extraction request."""
    model_config = ConfigDict(from_attributes=True)
    
    extraction_id: UUID = Field(..., description="Extraction task ID")
    
    # Extracted data
    total_concepts: int = Field(..., description="Total concepts extracted")
    total_relationships: int = Field(..., description="Total relationships found")
    total_domains: int = Field(..., description="Total exam domains identified")
    
    # Domain breakdown
    domains: List[Dict[str, Any]] = Field(..., description="Extracted domains with weights")
    concepts: List[Dict[str, Any]] = Field(..., description="Extracted concepts")
    prerequisites: List[Dict[str, Any]] = Field(..., description="Prerequisite relationships")
    learning_paths: Optional[List[Dict[str, Any]]] = Field(None, description="Generated learning paths")
    
    # Knowledge graph
    knowledge_graph_url: Optional[HttpUrl] = Field(None, description="Interactive knowledge graph URL")
    graph_data: Optional[Dict[str, Any]] = Field(None, description="Raw graph data")
    
    # Quality metrics
    extraction_confidence: float = Field(..., ge=0, le=1, description="Overall extraction confidence")
    coverage_score: float = Field(..., ge=0, le=1, description="Content coverage score")


class QualityCheckResponse(BaseResponse):
    """Response for quality check request."""
    model_config = ConfigDict(from_attributes=True)
    
    check_id: UUID = Field(..., description="Quality check ID")
    content_id: UUID = Field(..., description="Content ID checked")
    
    # Overall scores
    overall_quality_score: float = Field(..., ge=0, le=1, description="Overall quality score")
    passed_quality_threshold: bool = Field(..., description="Whether content passed quality threshold")
    
    # Detailed scores
    technical_accuracy_score: Optional[float] = Field(None, ge=0, le=1)
    pedagogical_effectiveness_score: Optional[float] = Field(None, ge=0, le=1)
    accessibility_score: Optional[float] = Field(None, ge=0, le=1)
    certification_alignment_score: Optional[float] = Field(None, ge=0, le=1)
    
    # Issues and recommendations
    issues_found: List[Dict[str, Any]] = Field(..., description="List of issues found")
    recommendations: List[str] = Field(..., description="Improvement recommendations")
    
    # Detailed reports
    technical_report: Optional[Dict[str, Any]] = Field(None)
    pedagogical_report: Optional[Dict[str, Any]] = Field(None)
    accessibility_report: Optional[Dict[str, Any]] = Field(None)
    alignment_report: Optional[Dict[str, Any]] = Field(None)
    
    # Monitoring
    monitoring_enabled: bool = Field(..., description="Whether monitoring is active")
    monitoring_id: Optional[UUID] = Field(None, description="Monitoring task ID")


class ContentResponse(BaseResponse):
    """Response with content details."""
    model_config = ConfigDict(from_attributes=True)
    
    content_id: UUID = Field(..., description="Content ID")
    title: str = Field(..., description="Content title")
    description: Optional[str] = Field(None, description="Content description")
    
    # Metadata
    certification_type: str = Field(..., description="Certification type")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: UUID = Field(..., description="Creator user ID")
    
    # Status
    status: StatusEnum = Field(..., description="Content status")
    quality_score: float = Field(..., ge=0, le=1, description="Quality score")
    
    # Content details
    duration_minutes: int = Field(..., description="Content duration")
    total_concepts: int = Field(..., description="Number of concepts covered")
    difficulty_level: str = Field(..., description="Difficulty level")
    
    # Available formats
    available_formats: List[OutputFormat] = Field(..., description="Available export formats")
    download_urls: Dict[OutputFormat, HttpUrl] = Field(..., description="Download URLs")
    preview_url: Optional[HttpUrl] = Field(None, description="Preview URL")
    
    # Metrics
    metrics: GenerationMetrics = Field(..., description="Content metrics")
    usage_stats: Optional[Dict[str, Any]] = Field(None, description="Usage statistics")


class ContentListResponse(PaginatedResponse):
    """Response for content listing."""
    model_config = ConfigDict(from_attributes=True)
    
    contents: List[ContentResponse] = Field(..., description="List of contents")


class ExportResponse(BaseResponse):
    """Response for export request."""
    model_config = ConfigDict(from_attributes=True)
    
    export_id: UUID = Field(..., description="Export task ID")
    content_id: UUID = Field(..., description="Content being exported")
    
    # Status
    export_status: StatusEnum = Field(..., description="Export status")
    progress: float = Field(0, ge=0, le=100, description="Export progress")
    
    # Results (when completed)
    download_url: Optional[HttpUrl] = Field(None, description="Download URL")
    file_size_bytes: Optional[int] = Field(None, description="File size")
    expires_at: Optional[datetime] = Field(None, description="Download expiration")
    
    # Timing
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    estimated_completion: Optional[datetime] = Field(None)


class FeedbackResponse(BaseResponse):
    """Response for feedback submission."""
    model_config = ConfigDict(from_attributes=True)
    
    feedback_id: UUID = Field(..., description="Feedback ID")
    content_id: UUID = Field(..., description="Content ID")
    
    # Analysis results
    sentiment_score: float = Field(..., ge=-1, le=1, description="Sentiment score")
    key_themes: List[str] = Field(..., description="Identified themes")
    suggested_improvements: List[str] = Field(..., description="Suggested improvements")
    
    # Impact
    will_trigger_update: bool = Field(..., description="Whether this will trigger content update")
    priority_level: str = Field(..., description="Feedback priority level")


class BatchGenerationResponse(BaseResponse):
    """Response for batch generation request."""
    model_config = ConfigDict(from_attributes=True)
    
    batch_id: UUID = Field(..., description="Batch ID")
    total_requests: int = Field(..., description="Total requests in batch")
    
    # Status
    batch_status: StatusEnum = Field(..., description="Overall batch status")
    completed_count: int = Field(0, description="Completed requests")
    failed_count: int = Field(0, description="Failed requests")
    
    # Individual results
    results: List[GenerationResponse] = Field(..., description="Individual generation results")
    
    # Timing
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    estimated_completion: Optional[datetime] = Field(None)


class AnalyticsResponse(BaseResponse):
    """Response for analytics request."""
    model_config = ConfigDict(from_attributes=True)
    
    # Time range
    start_date: datetime = Field(..., description="Analytics start date")
    end_date: datetime = Field(..., description="Analytics end date")
    
    # Usage metrics
    total_generations: Optional[int] = Field(None)
    total_users: Optional[int] = Field(None)
    total_content_minutes: Optional[float] = Field(None)
    
    # Quality metrics
    average_quality_score: Optional[float] = Field(None, ge=0, le=1)
    quality_trend: Optional[List[Dict[str, Any]]] = Field(None)
    
    # Performance metrics
    average_generation_time: Optional[float] = Field(None)
    success_rate: Optional[float] = Field(None, ge=0, le=1)
    
    # User feedback
    average_rating: Optional[float] = Field(None, ge=1, le=5)
    feedback_summary: Optional[Dict[str, Any]] = Field(None)
    
    # Detailed data
    time_series_data: Optional[List[Dict[str, Any]]] = Field(None)
    breakdown_by_type: Optional[Dict[str, Any]] = Field(None)


class UserResponse(BaseResponse):
    """Response with user information."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    
    # Account status
    is_active: bool = Field(..., description="Account active status")
    is_verified: bool = Field(..., description="Email verification status")
    
    # Timestamps
    created_at: datetime = Field(..., description="Account creation date")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    # Usage stats
    total_generations: int = Field(..., description="Total content generations")
    total_storage_bytes: int = Field(..., description="Total storage used")
    
    # Preferences
    preferences: Dict[str, Any] = Field(..., description="User preferences")
    
    # Subscription/quota
    plan_type: str = Field(..., description="Subscription plan")
    quota_remaining: Dict[str, int] = Field(..., description="Remaining quotas")


class AuthResponse(BaseResponse):
    """Response for authentication requests."""
    model_config = ConfigDict(from_attributes=True)
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    
    # User info
    user: UserResponse = Field(..., description="Authenticated user information")


class RateLimitResponse(BaseResponse):
    """Response when rate limited."""
    status: StatusEnum = StatusEnum.ERROR
    message: str = "Rate limit exceeded"
    rate_limit_info: RateLimitInfo = Field(..., description="Rate limit details")


class WebSocketAuthResponse(BaseModel):
    """WebSocket authentication response."""
    authenticated: bool = Field(..., description="Authentication status")
    connection_id: UUID = Field(..., description="WebSocket connection ID")
    expires_at: datetime = Field(..., description="Connection expiration")


class ProgressStreamResponse(BaseModel):
    """Server-sent event for progress updates."""
    event: str = Field("progress", description="Event type")
    data: Dict[str, Any] = Field(..., description="Progress data")
    id: Optional[str] = Field(None, description="Event ID")
    retry: Optional[int] = Field(None, description="Retry interval in milliseconds")
