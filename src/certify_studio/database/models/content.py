"""
Content and generation models for Certify Studio.

This module contains all content-related database models including
generated content, media assets, versions, and export tasks.
"""

from typing import Optional, List, TYPE_CHECKING, Dict, Any
from datetime import datetime
import enum

from sqlalchemy import (
    Column, String, Boolean, Integer, Float, Text, JSON, Enum,
    ForeignKey, UniqueConstraint, Index, CheckConstraint, DateTime
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

from .base import (
    BaseModel, FullAuditModel, VersionedModel,
    ContentStatus, TaskStatus, ExportFormat, MediaType,
    generate_uuid, utcnow
)

if TYPE_CHECKING:
    from .user import User
    from .domain import ExtractedConcept, ConceptRelationship
    from .quality import QualityCheck, QualityMetric


class ContentType(str, enum.Enum):
    """Types of content that can be generated."""
    LESSON = "lesson"
    COURSE = "course"
    ASSESSMENT = "assessment"
    PRACTICE = "practice"
    SUMMARY = "summary"
    FULL_CERTIFICATION = "full_certification"


class InteractionType(str, enum.Enum):
    """Types of interactive elements."""
    QUIZ = "quiz"
    DRAG_DROP = "drag_drop"
    SIMULATION = "simulation"
    CODE_EDITOR = "code_editor"
    DISCUSSION = "discussion"
    POLL = "poll"


class ContentGeneration(FullAuditModel):
    """Main content generation task model."""
    
    __tablename__ = "content_generations"
    __table_args__ = (
        Index("ix_content_generations_user_id", "user_id"),
        Index("ix_content_generations_status", "status"),
        Index("ix_content_generations_created_at", "created_at"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="ck_content_generations_progress"),
    )
    
    # User relationship
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Source information
    source_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    source_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_file_size: Mapped[int] = mapped_column(Integer)  # in bytes
    source_content_hash: Mapped[str] = mapped_column(String(64))  # SHA256
    
    # Generation configuration
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType), nullable=False)
    target_audience: Mapped[Optional[str]] = mapped_column(String(255))
    difficulty_level: Mapped[Optional[str]] = mapped_column(String(50))
    language: Mapped[str] = mapped_column(String(10), default="en")
    
    # Generation options
    generation_options: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    output_formats: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    quality_settings: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    current_step: Mapped[Optional[str]] = mapped_column(String(255))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float)
    
    # Results
    total_concepts: Mapped[int] = mapped_column(Integer, default=0)
    total_media_items: Mapped[int] = mapped_column(Integer, default=0)
    total_interactions: Mapped[int] = mapped_column(Integer, default=0)
    estimated_duration_minutes: Mapped[Optional[float]] = mapped_column(Float)
    
    # Agent metrics
    agent_metrics: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="content_generations")
    content_pieces: Mapped[List["ContentPiece"]] = relationship(
        "ContentPiece",
        back_populates="generation",
        cascade="all, delete-orphan"
    )
    media_assets: Mapped[List["MediaAsset"]] = relationship(
        "MediaAsset",
        back_populates="generation",
        cascade="all, delete-orphan"
    )
    export_tasks: Mapped[List["ExportTask"]] = relationship(
        "ExportTask",
        back_populates="generation",
        cascade="all, delete-orphan"
    )
    extracted_concepts: Mapped[List["ExtractedConcept"]] = relationship(
        "ExtractedConcept",
        back_populates="generation",
        cascade="all, delete-orphan"
    )
    quality_checks: Mapped[List["QualityCheck"]] = relationship(
        "QualityCheck",
        back_populates="generation",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ContentGeneration(id={self.id}, title={self.title}, status={self.status})>"


class ContentPiece(VersionedModel):
    """Individual piece of generated content (section, lesson, etc.)."""
    
    __tablename__ = "content_pieces"
    __table_args__ = (
        Index("ix_content_pieces_generation_id", "generation_id"),
        Index("ix_content_pieces_parent_id", "parent_id"),
        Index("ix_content_pieces_order_index", "order_index"),
        Index("ix_content_pieces_content_type", "content_type"),
    )
    
    generation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_generations.id", ondelete="CASCADE"),
        nullable=False
    )
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_pieces.id", ondelete="CASCADE")
    )
    
    # Content information
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)  # section, lesson, topic
    
    # Content data
    content_text: Mapped[Optional[str]] = mapped_column(Text)
    content_markdown: Mapped[Optional[str]] = mapped_column(Text)
    content_html: Mapped[Optional[str]] = mapped_column(Text)
    content_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Organization
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    depth_level: Mapped[int] = mapped_column(Integer, default=0)
    
    # Learning metadata
    learning_objectives: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    prerequisites: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    estimated_duration_minutes: Mapped[Optional[float]] = mapped_column(Float)
    difficulty_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Cognitive load metrics
    cognitive_load_intrinsic: Mapped[Optional[float]] = mapped_column(Float)
    cognitive_load_extraneous: Mapped[Optional[float]] = mapped_column(Float)
    cognitive_load_germane: Mapped[Optional[float]] = mapped_column(Float)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default=ContentStatus.DRAFT,
        nullable=False
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    generation: Mapped["ContentGeneration"] = relationship("ContentGeneration", back_populates="content_pieces")
    parent: Mapped[Optional["ContentPiece"]] = relationship(
        "ContentPiece",
        remote_side="ContentPiece.id",
        backref="children"
    )
    media_references: Mapped[List["MediaReference"]] = relationship(
        "MediaReference",
        back_populates="content_piece",
        cascade="all, delete-orphan"
    )
    interactions: Mapped[List["ContentInteraction"]] = relationship(
        "ContentInteraction",
        back_populates="content_piece",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ContentPiece(id={self.id}, title={self.title}, type={self.content_type})>"


class MediaAsset(BaseModel):
    """Media assets (images, videos, animations) generated or used."""
    
    __tablename__ = "media_assets"
    __table_args__ = (
        Index("ix_media_assets_generation_id", "generation_id"),
        Index("ix_media_assets_media_type", "media_type"),
        Index("ix_media_assets_file_hash", "file_hash"),
        UniqueConstraint("file_hash", name="uq_media_assets_file_hash"),
    )
    
    generation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_generations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # File information
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer)  # in bytes
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Media metadata
    media_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    alt_text: Mapped[Optional[str]] = mapped_column(Text)  # For accessibility
    
    # Technical metadata
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    fps: Mapped[Optional[float]] = mapped_column(Float)
    bitrate: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Processing information
    is_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    generation_params: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float)
    
    # Storage and CDN
    cdn_url: Mapped[Optional[str]] = mapped_column(String(500))
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    variants: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)  # Different resolutions/formats
    
    # Relationships
    generation: Mapped["ContentGeneration"] = relationship("ContentGeneration", back_populates="media_assets")
    references: Mapped[List["MediaReference"]] = relationship(
        "MediaReference",
        back_populates="media_asset",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<MediaAsset(id={self.id}, file_name={self.file_name}, type={self.media_type})>"


class MediaReference(BaseModel):
    """References between content pieces and media assets."""
    
    __tablename__ = "media_references"
    __table_args__ = (
        Index("ix_media_references_content_piece_id", "content_piece_id"),
        Index("ix_media_references_media_asset_id", "media_asset_id"),
        UniqueConstraint("content_piece_id", "media_asset_id", "reference_key", name="uq_media_references"),
    )
    
    content_piece_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_pieces.id", ondelete="CASCADE"),
        nullable=False
    )
    media_asset_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media_assets.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Reference information
    reference_key: Mapped[str] = mapped_column(String(100), nullable=False)  # Unique key within content
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)  # inline, hero, background
    position_index: Mapped[int] = mapped_column(Integer, default=0)
    
    # Display settings
    display_settings: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    caption: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    content_piece: Mapped["ContentPiece"] = relationship("ContentPiece", back_populates="media_references")
    media_asset: Mapped["MediaAsset"] = relationship("MediaAsset", back_populates="references")


class ContentInteraction(BaseModel):
    """Interactive elements within content."""
    
    __tablename__ = "content_interactions"
    __table_args__ = (
        Index("ix_content_interactions_content_piece_id", "content_piece_id"),
        Index("ix_content_interactions_interaction_type", "interaction_type"),
    )
    
    content_piece_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_pieces.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Interaction information
    interaction_type: Mapped[InteractionType] = mapped_column(Enum(InteractionType), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    
    # Interaction data
    interaction_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    correct_responses: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    feedback_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Configuration
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    max_attempts: Mapped[Optional[int]] = mapped_column(Integer)
    time_limit_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    points_possible: Mapped[Optional[float]] = mapped_column(Float)
    
    # Position
    position_index: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    content_piece: Mapped["ContentPiece"] = relationship("ContentPiece", back_populates="interactions")
    
    def __repr__(self) -> str:
        return f"<ContentInteraction(id={self.id}, type={self.interaction_type}, title={self.title})>"


class ExportTask(FullAuditModel):
    """Export tasks for generating different output formats."""
    
    __tablename__ = "export_tasks"
    __table_args__ = (
        Index("ix_export_tasks_generation_id", "generation_id"),
        Index("ix_export_tasks_status", "status"),
        Index("ix_export_tasks_format", "format"),
    )
    
    generation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_generations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Export configuration
    format: Mapped[str] = mapped_column(String(50), nullable=False)
    export_options: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50),
        default=TaskStatus.PENDING,
        nullable=False
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float)
    
    # Output information
    output_file_path: Mapped[Optional[str]] = mapped_column(String(500))
    output_file_size: Mapped[Optional[int]] = mapped_column(Integer)
    output_file_hash: Mapped[Optional[str]] = mapped_column(String(64))
    download_url: Mapped[Optional[str]] = mapped_column(String(500))
    download_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Metadata
    export_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    generation: Mapped["ContentGeneration"] = relationship("ContentGeneration", back_populates="export_tasks")
    
    def __repr__(self) -> str:
        return f"<ExportTask(id={self.id}, format={self.format}, status={self.status})>"


class ContentVersion(BaseModel):
    """Version tracking for content pieces."""
    
    __tablename__ = "content_versions"
    __table_args__ = (
        Index("ix_content_versions_content_piece_id", "content_piece_id"),
        Index("ix_content_versions_version_number", "version_number"),
    )
    
    content_piece_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_pieces.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Version information
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_tag: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Content snapshot
    content_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    # Change information
    change_summary: Mapped[Optional[str]] = mapped_column(Text)
    changed_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    change_type: Mapped[str] = mapped_column(String(50))  # manual, auto_improve, user_feedback
    
    # Relationships
    content_piece: Mapped["ContentPiece"] = relationship("ContentPiece")
    
    def __repr__(self) -> str:
        return f"<ContentVersion(id={self.id}, content_piece_id={self.content_piece_id}, version={self.version_number})>"


# Create composite indexes for common query patterns
Index("ix_content_generations_user_status", ContentGeneration.user_id, ContentGeneration.status)
Index("ix_content_pieces_generation_status", ContentPiece.generation_id, ContentPiece.status)
Index("ix_export_tasks_generation_status", ExportTask.generation_id, ExportTask.status)
