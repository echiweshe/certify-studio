"""
Quality assurance and metrics models for Certify Studio.

This module contains all models related to quality checks,
metrics tracking, benchmarks, and continuous improvement.
"""

from typing import Optional, List, TYPE_CHECKING, Dict, Any
from datetime import datetime
import enum

from sqlalchemy import (
    Column, String, Boolean, Integer, Float, Text, JSON, Enum, DateTime,
    ForeignKey, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

from .base import (
    BaseModel, FullAuditModel, VersionedModel,
    QualityStatus, generate_uuid, utcnow
)

if TYPE_CHECKING:
    from .content import ContentGeneration, ContentPiece
    from .domain import ExtractedConcept
    from .user import User


class QualityDimension(str, enum.Enum):
    """Dimensions of quality that are evaluated."""
    PEDAGOGICAL = "pedagogical"
    TECHNICAL = "technical"
    ACCESSIBILITY = "accessibility"
    ENGAGEMENT = "engagement"
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    COHERENCE = "coherence"
    CLARITY = "clarity"


class FeedbackType(str, enum.Enum):
    """Types of feedback that can be collected."""
    RATING = "rating"
    COMMENT = "comment"
    CORRECTION = "correction"
    SUGGESTION = "suggestion"
    COMPLAINT = "complaint"
    PRAISE = "praise"


class BenchmarkType(str, enum.Enum):
    """Types of benchmarks for comparison."""
    INDUSTRY_STANDARD = "industry_standard"
    CERTIFICATION_OFFICIAL = "certification_official"
    COMPETITOR = "competitor"
    INTERNAL = "internal"
    ACADEMIC = "academic"


class QualityCheck(FullAuditModel):
    """Quality checks performed on generated content."""
    
    __tablename__ = "quality_checks"
    __table_args__ = (
        Index("ix_quality_checks_generation_id", "generation_id"),
        Index("ix_quality_checks_status", "status"),
        Index("ix_quality_checks_check_type", "check_type"),
        Index("ix_quality_checks_created_at", "created_at"),
    )
    
    generation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_generations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Check configuration
    check_type: Mapped[str] = mapped_column(String(50), nullable=False)  # automated, manual, hybrid
    check_name: Mapped[str] = mapped_column(String(255), nullable=False)
    check_version: Mapped[str] = mapped_column(String(20), default="1.0")
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50),
        default=QualityStatus.PENDING,
        nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float)
    
    # Overall results
    passed: Mapped[Optional[bool]] = mapped_column(Boolean)
    overall_score: Mapped[Optional[float]] = mapped_column(Float)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Detailed findings
    findings: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    recommendations: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    issues_found: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    generation: Mapped["ContentGeneration"] = relationship("ContentGeneration", back_populates="quality_checks")
    metrics: Mapped[List["QualityMetric"]] = relationship(
        "QualityMetric",
        back_populates="quality_check",
        cascade="all, delete-orphan"
    )
    issues: Mapped[List["QualityIssue"]] = relationship(
        "QualityIssue",
        back_populates="quality_check",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<QualityCheck(id={self.id}, check_name={self.check_name}, status={self.status})>"


class QualityMetric(BaseModel):
    """Individual quality metrics from checks."""
    
    __tablename__ = "quality_metrics"
    __table_args__ = (
        Index("ix_quality_metrics_quality_check_id", "quality_check_id"),
        Index("ix_quality_metrics_dimension", "dimension"),
        Index("ix_quality_metrics_metric_name", "metric_name"),
        UniqueConstraint("quality_check_id", "metric_name", name="uq_quality_metrics"),
    )
    
    quality_check_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quality_checks.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Metric identification
    dimension: Mapped[QualityDimension] = mapped_column(Enum(QualityDimension), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Metric values
    value: Mapped[float] = mapped_column(Float, nullable=False)
    min_value: Mapped[float] = mapped_column(Float, default=0.0)
    max_value: Mapped[float] = mapped_column(Float, default=1.0)
    target_value: Mapped[Optional[float]] = mapped_column(Float)
    threshold_value: Mapped[Optional[float]] = mapped_column(Float)
    
    # Status
    passed: Mapped[bool] = mapped_column(Boolean, default=True)
    severity: Mapped[Optional[str]] = mapped_column(String(20))  # info, warning, error
    
    # Additional context
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    description: Mapped[Optional[str]] = mapped_column(Text)
    details: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    quality_check: Mapped["QualityCheck"] = relationship("QualityCheck", back_populates="metrics")
    
    def __repr__(self) -> str:
        return f"<QualityMetric(metric={self.metric_name}, value={self.value})>"


class QualityIssue(BaseModel):
    """Specific issues found during quality checks."""
    
    __tablename__ = "quality_issues"
    __table_args__ = (
        Index("ix_quality_issues_quality_check_id", "quality_check_id"),
        Index("ix_quality_issues_severity", "severity"),
        Index("ix_quality_issues_issue_type", "issue_type"),
    )
    
    quality_check_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quality_checks.id", ondelete="CASCADE"),
        nullable=False
    )
    content_piece_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_pieces.id", ondelete="SET NULL")
    )
    
    # Issue details
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False)
    issue_code: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # critical, high, medium, low
    
    # Description
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Location
    location: Mapped[Optional[str]] = mapped_column(String(500))
    line_number: Mapped[Optional[int]] = mapped_column(Integer)
    context: Mapped[Optional[str]] = mapped_column(Text)
    
    # Resolution
    suggestion: Mapped[Optional[str]] = mapped_column(Text)
    auto_fixable: Mapped[bool] = mapped_column(Boolean, default=False)
    fix_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Impact
    impact_score: Mapped[float] = mapped_column(Float, default=0.5)
    affected_users_estimate: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Relationships
    quality_check: Mapped["QualityCheck"] = relationship("QualityCheck", back_populates="issues")
    content_piece: Mapped[Optional["ContentPiece"]] = relationship("ContentPiece")
    
    def __repr__(self) -> str:
        return f"<QualityIssue(type={self.issue_type}, severity={self.severity})>"


class QualityBenchmark(VersionedModel):
    """Benchmarks for quality comparison."""
    
    __tablename__ = "quality_benchmarks"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_quality_benchmarks"),
        Index("ix_quality_benchmarks_benchmark_type", "benchmark_type"),
        Index("ix_quality_benchmarks_is_active", "is_active"),
    )
    
    # Benchmark identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    benchmark_type: Mapped[BenchmarkType] = mapped_column(Enum(BenchmarkType), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(255))
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Benchmark data
    metrics: Mapped[Dict[str, float]] = mapped_column(JSONB, nullable=False)
    criteria: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Metadata
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    applicable_domains: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    def __repr__(self) -> str:
        return f"<QualityBenchmark(name={self.name}, type={self.benchmark_type})>"


class UserFeedback(FullAuditModel):
    """User feedback on generated content."""
    
    __tablename__ = "user_feedback"
    __table_args__ = (
        Index("ix_user_feedback_user_id", "user_id"),
        Index("ix_user_feedback_generation_id", "generation_id"),
        Index("ix_user_feedback_content_piece_id", "content_piece_id"),
        Index("ix_user_feedback_feedback_type", "feedback_type"),
        Index("ix_user_feedback_created_at", "created_at"),
    )
    
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    generation_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_generations.id", ondelete="SET NULL")
    )
    content_piece_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_pieces.id", ondelete="SET NULL")
    )
    
    # Feedback details
    feedback_type: Mapped[FeedbackType] = mapped_column(Enum(FeedbackType), nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 scale
    
    # Content
    title: Mapped[Optional[str]] = mapped_column(String(255))
    comment: Mapped[Optional[str]] = mapped_column(Text)
    
    # Structured feedback
    categories: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Response
    admin_response: Mapped[Optional[str]] = mapped_column(Text)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    responded_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    
    # Actions taken
    actions_taken: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    content_improved: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    generation: Mapped[Optional["ContentGeneration"]] = relationship("ContentGeneration")
    content_piece: Mapped[Optional["ContentPiece"]] = relationship("ContentPiece")
    
    def __repr__(self) -> str:
        return f"<UserFeedback(id={self.id}, type={self.feedback_type}, rating={self.rating})>"


class ConceptQualityScore(BaseModel):
    """Quality scores for extracted concepts."""
    
    __tablename__ = "concept_quality_scores"
    __table_args__ = (
        Index("ix_concept_quality_scores_concept_id", "concept_id"),
        Index("ix_concept_quality_scores_score_type", "score_type"),
        UniqueConstraint("concept_id", "score_type", name="uq_concept_quality_scores"),
    )
    
    concept_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_concepts.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Score details
    score_type: Mapped[str] = mapped_column(String(50), nullable=False)
    score_value: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Scoring metadata
    algorithm_version: Mapped[str] = mapped_column(String(20), default="1.0")
    factors: Mapped[Dict[str, float]] = mapped_column(JSONB, default=dict)
    
    # Confidence
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    sample_size: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Relationships
    concept: Mapped["ExtractedConcept"] = relationship("ExtractedConcept", back_populates="quality_scores")
    
    def __repr__(self) -> str:
        return f"<ConceptQualityScore(concept={self.concept_id}, type={self.score_type}, value={self.score_value})>"


class ContentImprovement(VersionedModel):
    """Improvements made to content based on quality checks."""
    
    __tablename__ = "content_improvements"
    __table_args__ = (
        Index("ix_content_improvements_content_piece_id", "content_piece_id"),
        Index("ix_content_improvements_improvement_type", "improvement_type"),
        Index("ix_content_improvements_created_at", "created_at"),
    )
    
    content_piece_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_pieces.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Improvement details
    improvement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(50), nullable=False)  # quality_check, user_feedback, auto
    
    # Changes made
    changes_summary: Mapped[str] = mapped_column(Text, nullable=False)
    before_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    after_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    # Impact
    quality_score_before: Mapped[Optional[float]] = mapped_column(Float)
    quality_score_after: Mapped[Optional[float]] = mapped_column(Float)
    improvement_percentage: Mapped[Optional[float]] = mapped_column(Float)
    
    # Agent involvement
    agent_id: Mapped[Optional[str]] = mapped_column(String(100))
    agent_reasoning: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    content_piece: Mapped["ContentPiece"] = relationship("ContentPiece")
    
    def __repr__(self) -> str:
        return f"<ContentImprovement(id={self.id}, type={self.improvement_type})>"


class QualityReport(BaseModel):
    """Aggregated quality reports."""
    
    __tablename__ = "quality_reports"
    __table_args__ = (
        Index("ix_quality_reports_generation_id", "generation_id"),
        Index("ix_quality_reports_report_type", "report_type"),
        Index("ix_quality_reports_created_at", "created_at"),
    )
    
    generation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_generations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Report details
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Summary scores
    overall_quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    dimension_scores: Mapped[Dict[str, float]] = mapped_column(JSONB, nullable=False)
    
    # Detailed findings
    strengths: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    weaknesses: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    recommendations: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Comparison
    benchmark_comparison: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    percentile_rank: Mapped[Optional[float]] = mapped_column(Float)
    
    # Report data
    full_report: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    # Relationships
    generation: Mapped["ContentGeneration"] = relationship("ContentGeneration")
    
    def __repr__(self) -> str:
        return f"<QualityReport(id={self.id}, type={self.report_type}, score={self.overall_quality_score})>"


# Create additional indexes for performance
Index("ix_quality_metrics_composite", QualityMetric.quality_check_id, QualityMetric.dimension)
Index("ix_user_feedback_composite", UserFeedback.user_id, UserFeedback.generation_id)
Index("ix_quality_checks_generation_status", QualityCheck.generation_id, QualityCheck.status)
