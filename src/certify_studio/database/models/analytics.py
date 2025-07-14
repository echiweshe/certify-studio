"""
Analytics and tracking models for Certify Studio.

This module contains all models related to usage analytics,
performance tracking, business metrics, and user behavior.
"""

from typing import Optional, List, TYPE_CHECKING, Dict, Any
from datetime import datetime, date
import enum

from sqlalchemy import (
    Column, String, Boolean, Integer, Float, Text, JSON, Enum, Date, DateTime,
    ForeignKey, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

from .base import (
    BaseModel, generate_uuid, utcnow
)

if TYPE_CHECKING:
    from .user import User
    from .content import ContentGeneration, ExportTask


class EventType(str, enum.Enum):
    """Types of events that are tracked."""
    PAGE_VIEW = "page_view"
    GENERATION_START = "generation_start"
    GENERATION_COMPLETE = "generation_complete"
    EXPORT_START = "export_start"
    EXPORT_COMPLETE = "export_complete"
    LOGIN = "login"
    LOGOUT = "logout"
    SIGNUP = "signup"
    SUBSCRIPTION_CHANGE = "subscription_change"
    ERROR = "error"
    FEATURE_USE = "feature_use"


class MetricType(str, enum.Enum):
    """Types of business metrics tracked."""
    REVENUE = "revenue"
    USER_COUNT = "user_count"
    GENERATION_COUNT = "generation_count"
    STORAGE_USAGE = "storage_usage"
    API_CALLS = "api_calls"
    QUALITY_SCORE = "quality_score"
    USER_SATISFACTION = "user_satisfaction"
    PERFORMANCE = "performance"


class UserActivity(BaseModel):
    """User activity tracking for analytics."""
    
    __tablename__ = "user_activities"
    __table_args__ = (
        Index("ix_user_activities_user_id", "user_id"),
        Index("ix_user_activities_event_type", "event_type"),
        Index("ix_user_activities_created_at", "created_at"),
        Index("ix_user_activities_session_id", "session_id"),
    )
    
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Event details
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_category: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Session tracking
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Context
    page_url: Mapped[Optional[str]] = mapped_column(String(500))
    referrer_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Event properties
    properties: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Device and location
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    device_type: Mapped[Optional[str]] = mapped_column(String(50))
    browser: Mapped[Optional[str]] = mapped_column(String(50))
    os: Mapped[Optional[str]] = mapped_column(String(50))
    country: Mapped[Optional[str]] = mapped_column(String(2))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Performance
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="activities")
    
    def __repr__(self) -> str:
        return f"<UserActivity(user={self.user_id}, event={self.event_type})>"


class GenerationAnalytics(BaseModel):
    """Analytics for content generation tasks."""
    
    __tablename__ = "generation_analytics"
    __table_args__ = (
        Index("ix_generation_analytics_generation_id", "generation_id"),
        Index("ix_generation_analytics_created_at", "created_at"),
        UniqueConstraint("generation_id", name="uq_generation_analytics"),
    )
    
    generation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_generations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Performance metrics
    total_processing_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    agent_processing_times: Mapped[Dict[str, float]] = mapped_column(JSONB, default=dict)
    
    # Resource usage
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column(Float)
    memory_usage_mb: Mapped[Optional[float]] = mapped_column(Float)
    gpu_usage_percent: Mapped[Optional[float]] = mapped_column(Float)
    
    # Cost tracking
    llm_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    llm_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    compute_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    storage_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Quality metrics
    quality_scores: Mapped[Dict[str, float]] = mapped_column(JSONB, default=dict)
    user_satisfaction_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Content metrics
    concepts_extracted: Mapped[int] = mapped_column(Integer, default=0)
    media_items_generated: Mapped[int] = mapped_column(Integer, default=0)
    interactions_created: Mapped[int] = mapped_column(Integer, default=0)
    content_pieces_created: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error tracking
    errors_encountered: Mapped[int] = mapped_column(Integer, default=0)
    warnings_encountered: Mapped[int] = mapped_column(Integer, default=0)
    retry_attempts: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    generation: Mapped["ContentGeneration"] = relationship("ContentGeneration")
    
    def __repr__(self) -> str:
        return f"<GenerationAnalytics(generation={self.generation_id}, cost=${self.total_cost_usd})>"


class DailyMetrics(BaseModel):
    """Daily aggregated metrics for business intelligence."""
    
    __tablename__ = "daily_metrics"
    __table_args__ = (
        UniqueConstraint("metric_date", name="uq_daily_metrics_date"),
        Index("ix_daily_metrics_metric_date", "metric_date"),
    )
    
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # User metrics
    total_users: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)
    new_users: Mapped[int] = mapped_column(Integer, default=0)
    
    # Generation metrics
    total_generations: Mapped[int] = mapped_column(Integer, default=0)
    successful_generations: Mapped[int] = mapped_column(Integer, default=0)
    failed_generations: Mapped[int] = mapped_column(Integer, default=0)
    
    # Export metrics
    total_exports: Mapped[int] = mapped_column(Integer, default=0)
    export_formats: Mapped[Dict[str, int]] = mapped_column(JSONB, default=dict)
    
    # Usage metrics
    total_storage_gb: Mapped[float] = mapped_column(Float, default=0.0)
    total_bandwidth_gb: Mapped[float] = mapped_column(Float, default=0.0)
    api_calls: Mapped[int] = mapped_column(Integer, default=0)
    
    # Financial metrics
    revenue_usd: Mapped[float] = mapped_column(Float, default=0.0)
    costs_usd: Mapped[float] = mapped_column(Float, default=0.0)
    profit_usd: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Quality metrics
    avg_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_user_satisfaction: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Performance metrics
    avg_generation_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    avg_export_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    uptime_percent: Mapped[float] = mapped_column(Float, default=100.0)
    
    # Plan distribution
    plan_distribution: Mapped[Dict[str, int]] = mapped_column(JSONB, default=dict)
    
    def __repr__(self) -> str:
        return f"<DailyMetrics(date={self.metric_date}, users={self.active_users})>"


class FeatureUsage(BaseModel):
    """Track usage of specific features."""
    
    __tablename__ = "feature_usage"
    __table_args__ = (
        Index("ix_feature_usage_user_id", "user_id"),
        Index("ix_feature_usage_feature_name", "feature_name"),
        Index("ix_feature_usage_used_at", "used_at"),
    )
    
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Feature details
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_category: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Usage context
    context: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Timing
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Outcome
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<FeatureUsage(user={self.user_id}, feature={self.feature_name})>"


class PerformanceMetrics(BaseModel):
    """System performance metrics."""
    
    __tablename__ = "performance_metrics"
    __table_args__ = (
        Index("ix_performance_metrics_endpoint", "endpoint"),
        Index("ix_performance_metrics_measured_at", "measured_at"),
    )
    
    # Identification
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Timing
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Details
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    request_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    response_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Resource usage
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column(Float)
    memory_usage_mb: Mapped[Optional[float]] = mapped_column(Float)
    
    # Context
    user_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    trace_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    def __repr__(self) -> str:
        return f"<PerformanceMetrics(endpoint={self.endpoint}, time={self.response_time_ms}ms)>"


class BusinessMetric(BaseModel):
    """Custom business metrics tracking."""
    
    __tablename__ = "business_metrics"
    __table_args__ = (
        Index("ix_business_metrics_metric_type", "metric_type"),
        Index("ix_business_metrics_metric_name", "metric_name"),
        Index("ix_business_metrics_recorded_at", "recorded_at"),
        UniqueConstraint("metric_type", "metric_name", "recorded_at", name="uq_business_metrics"),
    )
    
    # Metric identification
    metric_type: Mapped[MetricType] = mapped_column(Enum(MetricType), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Value
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Time
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Context
    dimensions: Mapped[Dict[str, str]] = mapped_column(JSONB, default=dict)
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    def __repr__(self) -> str:
        return f"<BusinessMetric(type={self.metric_type}, name={self.metric_name}, value={self.value})>"


class UserSegment(BaseModel):
    """User segments for analytics and marketing."""
    
    __tablename__ = "user_segments"
    __table_args__ = (
        UniqueConstraint("name", name="uq_user_segments_name"),
        Index("ix_user_segments_segment_type", "segment_type"),
    )
    
    # Segment definition
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    segment_type: Mapped[str] = mapped_column(String(50), nullable=False)  # behavioral, demographic, etc.
    
    # Criteria
    criteria: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    sql_query: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_update: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Relationships
    members: Mapped[List["UserSegmentMembership"]] = relationship(
        "UserSegmentMembership",
        back_populates="segment",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<UserSegment(name={self.name})>"


class UserSegmentMembership(BaseModel):
    """User membership in segments."""
    
    __tablename__ = "user_segment_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "segment_id", name="uq_user_segment_memberships"),
        Index("ix_user_segment_memberships_user_id", "user_id"),
        Index("ix_user_segment_memberships_segment_id", "segment_id"),
    )
    
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    segment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_segments.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Membership details
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    segment: Mapped["UserSegment"] = relationship("UserSegment", back_populates="members")


class ABTestExperiment(BaseModel):
    """A/B test experiments."""
    
    __tablename__ = "ab_test_experiments"
    __table_args__ = (
        UniqueConstraint("name", name="uq_ab_test_experiments_name"),
        Index("ix_ab_test_experiments_status", "status"),
    )
    
    # Experiment details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Configuration
    variants: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    traffic_allocation: Mapped[Dict[str, float]] = mapped_column(JSONB, nullable=False)
    
    # Timing
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # draft, running, completed
    
    # Results
    results: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    winner_variant: Mapped[Optional[str]] = mapped_column(String(50))
    confidence_level: Mapped[Optional[float]] = mapped_column(Float)
    
    def __repr__(self) -> str:
        return f"<ABTestExperiment(name={self.name}, status={self.status})>"


# Create additional indexes for analytics queries
Index("ix_user_activities_composite", UserActivity.user_id, UserActivity.event_type, UserActivity.created_at)
Index("ix_generation_analytics_cost", GenerationAnalytics.total_cost_usd)
Index("ix_business_metrics_composite", BusinessMetric.metric_type, BusinessMetric.recorded_at)
