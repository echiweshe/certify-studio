"""
Request schemas for the API endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator, HttpUrl

from .common import (
    OutputFormat,
    CertificationType,
    QualityLevel,
    ExportOptions
)


class GenerationRequest(BaseModel):
    """Request to generate educational content."""
    model_config = ConfigDict(from_attributes=True)
    
    # Content source
    certification_type: CertificationType = Field(..., description="Type of certification")
    upload_id: Optional[UUID] = Field(None, description="ID of uploaded content file")
    content_url: Optional[HttpUrl] = Field(None, description="URL to content (if not uploaded)")
    
    # Generation options
    title: str = Field(..., min_length=1, max_length=200, description="Content title")
    description: Optional[str] = Field(None, max_length=1000, description="Content description")
    target_audience: str = Field("intermediate", description="Target audience level")
    duration_minutes: int = Field(30, ge=5, le=180, description="Target duration in minutes")
    
    # Output options
    output_formats: List[OutputFormat] = Field(..., min_items=1, description="Desired output formats")
    quality_level: QualityLevel = Field(QualityLevel.STANDARD, description="Quality level")
    
    # Advanced options
    language: str = Field("en", description="Content language (ISO 639-1)")
    enable_interactivity: bool = Field(True, description="Include interactive elements")
    enable_accessibility: bool = Field(True, description="Ensure accessibility compliance")
    custom_style: Optional[Dict[str, Any]] = Field(None, description="Custom styling options")
    
    @field_validator('upload_id', 'content_url')
    def validate_content_source(cls, v, info):
        """Ensure either upload_id or content_url is provided."""
        if info.data.get('upload_id') is None and info.data.get('content_url') is None:
            raise ValueError("Either upload_id or content_url must be provided")
        return v


class DomainExtractionRequest(BaseModel):
    """Request to extract domain knowledge from content."""
    model_config = ConfigDict(from_attributes=True)
    
    upload_id: UUID = Field(..., description="ID of uploaded content")
    certification_type: CertificationType = Field(..., description="Type of certification")
    
    # Extraction options
    extract_prerequisites: bool = Field(True, description="Extract prerequisite relationships")
    extract_learning_paths: bool = Field(True, description="Generate learning paths")
    extract_exam_weights: bool = Field(True, description="Extract exam domain weights")
    
    # Advanced options
    chunk_size: int = Field(500, ge=100, le=2000, description="Text chunk size")
    chunk_overlap: int = Field(50, ge=0, le=200, description="Chunk overlap size")
    confidence_threshold: float = Field(0.7, ge=0, le=1, description="Minimum confidence score")


class QualityCheckRequest(BaseModel):
    """Request to check content quality."""
    model_config = ConfigDict(from_attributes=True)
    
    content_id: UUID = Field(..., description="ID of content to check")
    
    # Check options
    check_technical_accuracy: bool = Field(True, description="Verify technical accuracy")
    check_pedagogical_effectiveness: bool = Field(True, description="Assess teaching effectiveness")
    check_accessibility: bool = Field(True, description="Check accessibility compliance")
    check_certification_alignment: bool = Field(True, description="Verify exam alignment")
    
    # Monitoring options
    enable_continuous_monitoring: bool = Field(False, description="Enable ongoing monitoring")
    monitoring_interval_minutes: int = Field(60, ge=5, description="Monitoring interval")
    
    # Feedback
    previous_feedback: Optional[List[Dict[str, Any]]] = Field(None, description="Previous user feedback")


class ContentUpdateRequest(BaseModel):
    """Request to update existing content."""
    model_config = ConfigDict(from_attributes=True)
    
    content_id: UUID = Field(..., description="ID of content to update")
    
    # Update options
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Content updates
    sections_to_update: Optional[List[str]] = Field(None, description="Specific sections to update")
    new_concepts: Optional[List[Dict[str, Any]]] = Field(None, description="New concepts to add")
    remove_concepts: Optional[List[str]] = Field(None, description="Concept IDs to remove")
    
    # Quality improvements
    apply_feedback: bool = Field(False, description="Apply accumulated feedback")
    regenerate_low_quality: bool = Field(False, description="Regenerate low-quality sections")
    update_to_latest_standards: bool = Field(False, description="Update to latest standards")


class ExportRequest(BaseModel):
    """Request to export content in specific format."""
    model_config = ConfigDict(from_attributes=True)
    
    content_id: UUID = Field(..., description="ID of content to export")
    export_options: ExportOptions = Field(..., description="Export configuration")
    
    # Delivery options
    webhook_url: Optional[HttpUrl] = Field(None, description="Webhook for completion notification")
    email_notification: Optional[str] = Field(None, description="Email for notification")


class FeedbackSubmission(BaseModel):
    """User feedback submission."""
    model_config = ConfigDict(from_attributes=True)
    
    content_id: UUID = Field(..., description="ID of content")
    
    # Ratings
    overall_rating: int = Field(..., ge=1, le=5, description="Overall rating")
    technical_accuracy_rating: Optional[int] = Field(None, ge=1, le=5)
    clarity_rating: Optional[int] = Field(None, ge=1, le=5)
    engagement_rating: Optional[int] = Field(None, ge=1, le=5)
    
    # Detailed feedback
    liked_sections: Optional[List[str]] = Field(None, description="Sections user liked")
    improvement_areas: Optional[List[str]] = Field(None, description="Areas needing improvement")
    comments: Optional[str] = Field(None, max_length=2000, description="Additional comments")
    
    # Context
    user_experience_level: Optional[str] = Field(None, description="User's experience level")
    completion_percentage: Optional[float] = Field(None, ge=0, le=100)


class BatchGenerationRequest(BaseModel):
    """Request to generate multiple contents in batch."""
    model_config = ConfigDict(from_attributes=True)
    
    requests: List[GenerationRequest] = Field(..., min_items=1, max_items=10, description="Batch requests")
    
    # Batch options
    priority: int = Field(5, ge=1, le=10, description="Batch priority (1=lowest, 10=highest)")
    parallel_processing: bool = Field(True, description="Process requests in parallel")
    stop_on_error: bool = Field(False, description="Stop batch on first error")
    
    # Notification
    webhook_url: Optional[HttpUrl] = Field(None, description="Webhook for batch completion")


class AnalyticsRequest(BaseModel):
    """Request for analytics data."""
    model_config = ConfigDict(from_attributes=True)
    
    # Time range
    start_date: datetime = Field(..., description="Start date for analytics")
    end_date: datetime = Field(..., description="End date for analytics")
    
    # Metrics to include
    include_usage_metrics: bool = Field(True, description="Include usage statistics")
    include_quality_metrics: bool = Field(True, description="Include quality metrics")
    include_performance_metrics: bool = Field(True, description="Include performance data")
    include_user_feedback: bool = Field(True, description="Include user feedback summary")
    
    # Grouping
    group_by: Optional[str] = Field(None, description="Group results by (day/week/month)")
    
    # Filters
    content_ids: Optional[List[UUID]] = Field(None, description="Filter by content IDs")
    certification_types: Optional[List[CertificationType]] = Field(None, description="Filter by cert type")


class UserPreferences(BaseModel):
    """User preferences update."""
    model_config = ConfigDict(from_attributes=True)
    
    # Display preferences
    theme: Optional[str] = Field(None, description="UI theme preference")
    language: Optional[str] = Field(None, description="Preferred language")
    timezone: Optional[str] = Field(None, description="User timezone")
    
    # Default generation options
    default_quality_level: Optional[QualityLevel] = Field(None)
    default_output_formats: Optional[List[OutputFormat]] = Field(None)
    default_duration_minutes: Optional[int] = Field(None, ge=5, le=180)
    
    # Notification preferences
    email_notifications: Optional[bool] = Field(None)
    webhook_notifications: Optional[bool] = Field(None)
    notification_types: Optional[List[str]] = Field(None)


class ContentSearchRequest(BaseModel):
    """Request to search generated content."""
    model_config = ConfigDict(from_attributes=True)
    
    # Search parameters
    query: Optional[str] = Field(None, description="Search query")
    certification_types: Optional[List[CertificationType]] = Field(None)
    
    # Filters
    created_after: Optional[datetime] = Field(None)
    created_before: Optional[datetime] = Field(None)
    min_quality_score: Optional[float] = Field(None, ge=0, le=1)
    output_formats: Optional[List[OutputFormat]] = Field(None)
    
    # Sorting
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")
    
    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
