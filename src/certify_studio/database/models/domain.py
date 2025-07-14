"""
Domain extraction and knowledge graph models for Certify Studio.

This module contains all models related to concept extraction,
knowledge graphs, learning paths, and domain relationships.
"""

from typing import Optional, List, TYPE_CHECKING, Dict, Any
from datetime import datetime
import enum

from sqlalchemy import (
    Column, String, Boolean, Integer, Float, Text, JSON, Enum, DateTime,
    ForeignKey, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB, TSVECTOR

from .base import (
    BaseModel, VersionedModel,
    generate_uuid, utcnow
)

if TYPE_CHECKING:
    from .content import ContentGeneration, ContentPiece
    from .quality import ConceptQualityScore


class ConceptType(str, enum.Enum):
    """Types of concepts that can be extracted."""
    TOPIC = "topic"
    SKILL = "skill"
    TOOL = "tool"
    THEORY = "theory"
    PRACTICE = "practice"
    PRINCIPLE = "principle"
    PROCESS = "process"
    CERTIFICATION = "certification"


class RelationshipType(str, enum.Enum):
    """Types of relationships between concepts."""
    PREREQUISITE = "prerequisite"
    RELATED_TO = "related_to"
    PART_OF = "part_of"
    ALTERNATIVE_TO = "alternative_to"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    REQUIRES = "requires"
    ENABLES = "enables"


class DifficultyLevel(str, enum.Enum):
    """Difficulty levels for concepts."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ExtractedConcept(VersionedModel):
    """Concepts extracted from source content."""
    
    __tablename__ = "extracted_concepts"
    __table_args__ = (
        Index("ix_extracted_concepts_generation_id", "generation_id"),
        Index("ix_extracted_concepts_concept_type", "concept_type"),
        Index("ix_extracted_concepts_name", "name"),
        Index("ix_extracted_concepts_canonical_id", "canonical_id"),
        Index("ix_extracted_concepts_search_vector", "search_vector", postgresql_using="gin"),
        UniqueConstraint("generation_id", "name", name="uq_extracted_concepts_generation_name"),
    )
    
    generation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_generations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Concept identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    concept_type: Mapped[ConceptType] = mapped_column(Enum(ConceptType), nullable=False)
    
    # Canonical concept reference (for deduplication)
    canonical_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canonical_concepts.id")
    )
    
    # Description and content
    description: Mapped[Optional[str]] = mapped_column(Text)
    definition: Mapped[Optional[str]] = mapped_column(Text)
    examples: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Metadata
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    aliases: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    acronyms: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Learning characteristics
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(Enum(DifficultyLevel))
    importance_score: Mapped[float] = mapped_column(Float, default=0.5)
    cognitive_load_score: Mapped[float] = mapped_column(Float, default=0.5)
    
    # Domain information
    domain_weight: Mapped[float] = mapped_column(Float, default=0.0)  # Weight in certification
    exam_coverage: Mapped[float] = mapped_column(Float, default=0.0)  # Percentage in exam
    
    # Time estimates
    estimated_learning_minutes: Mapped[Optional[float]] = mapped_column(Float)
    estimated_practice_minutes: Mapped[Optional[float]] = mapped_column(Float)
    
    # Source tracking
    source_sections: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    source_page_numbers: Mapped[List[int]] = mapped_column(ARRAY(Integer), default=list)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Embeddings and search
    embedding_vector: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float))
    search_vector: Mapped[Optional[str]] = mapped_column(TSVECTOR)
    
    # Additional data
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    generation: Mapped["ContentGeneration"] = relationship("ContentGeneration", back_populates="extracted_concepts")
    canonical_concept: Mapped[Optional["CanonicalConcept"]] = relationship("CanonicalConcept")
    
    # Relationship mappings
    source_relationships: Mapped[List["ConceptRelationship"]] = relationship(
        "ConceptRelationship",
        foreign_keys="ConceptRelationship.source_concept_id",
        back_populates="source_concept"
    )
    target_relationships: Mapped[List["ConceptRelationship"]] = relationship(
        "ConceptRelationship",
        foreign_keys="ConceptRelationship.target_concept_id",
        back_populates="target_concept"
    )
    
    learning_objectives: Mapped[List["LearningObjective"]] = relationship(
        "LearningObjective",
        back_populates="concept",
        cascade="all, delete-orphan"
    )
    
    prerequisites: Mapped[List["PrerequisiteMapping"]] = relationship(
        "PrerequisiteMapping",
        foreign_keys="PrerequisiteMapping.concept_id",
        back_populates="concept"
    )
    
    quality_scores: Mapped[List["ConceptQualityScore"]] = relationship(
        "ConceptQualityScore",
        back_populates="concept",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ExtractedConcept(id={self.id}, name={self.name}, type={self.concept_type})>"


class CanonicalConcept(VersionedModel):
    """Master list of canonical concepts across all content."""
    
    __tablename__ = "canonical_concepts"
    __table_args__ = (
        UniqueConstraint("name", "concept_type", name="uq_canonical_concepts_name_type"),
        Index("ix_canonical_concepts_name", "name"),
        Index("ix_canonical_concepts_concept_type", "concept_type"),
        Index("ix_canonical_concepts_search_vector", "search_vector", postgresql_using="gin"),
    )
    
    # Concept identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    concept_type: Mapped[ConceptType] = mapped_column(Enum(ConceptType), nullable=False)
    
    # Master description
    description: Mapped[Optional[str]] = mapped_column(Text)
    definition: Mapped[Optional[str]] = mapped_column(Text)
    
    # Aggregated metadata
    all_aliases: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    all_tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Usage statistics
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Quality metrics (aggregated)
    avg_importance_score: Mapped[float] = mapped_column(Float, default=0.5)
    avg_difficulty_score: Mapped[float] = mapped_column(Float, default=0.5)
    
    # Search and embeddings
    master_embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float))
    search_vector: Mapped[Optional[str]] = mapped_column(TSVECTOR)
    
    # External references
    wikipedia_url: Mapped[Optional[str]] = mapped_column(String(500))
    documentation_urls: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    def __repr__(self) -> str:
        return f"<CanonicalConcept(id={self.id}, name={self.name})>"


class ConceptRelationship(BaseModel):
    """Relationships between concepts in the knowledge graph."""
    
    __tablename__ = "concept_relationships"
    __table_args__ = (
        Index("ix_concept_relationships_source", "source_concept_id"),
        Index("ix_concept_relationships_target", "target_concept_id"),
        Index("ix_concept_relationships_type", "relationship_type"),
        UniqueConstraint(
            "source_concept_id", "target_concept_id", "relationship_type",
            name="uq_concept_relationships"
        ),
        CheckConstraint(
            "source_concept_id != target_concept_id",
            name="ck_concept_relationships_no_self_reference"
        ),
    )
    
    source_concept_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_concepts.id", ondelete="CASCADE"),
        nullable=False
    )
    target_concept_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_concepts.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Relationship details
    relationship_type: Mapped[RelationshipType] = mapped_column(Enum(RelationshipType), nullable=False)
    strength: Mapped[float] = mapped_column(Float, default=1.0)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Additional context
    context: Mapped[Optional[str]] = mapped_column(Text)
    evidence: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Relationships
    source_concept: Mapped["ExtractedConcept"] = relationship(
        "ExtractedConcept",
        foreign_keys=[source_concept_id],
        back_populates="source_relationships"
    )
    target_concept: Mapped["ExtractedConcept"] = relationship(
        "ExtractedConcept",
        foreign_keys=[target_concept_id],
        back_populates="target_relationships"
    )
    
    def __repr__(self) -> str:
        return f"<ConceptRelationship({self.source_concept_id} -{self.relationship_type}-> {self.target_concept_id})>"


class LearningObjective(BaseModel):
    """Learning objectives for concepts."""
    
    __tablename__ = "learning_objectives"
    __table_args__ = (
        Index("ix_learning_objectives_concept_id", "concept_id"),
        Index("ix_learning_objectives_bloom_level", "bloom_level"),
    )
    
    concept_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_concepts.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Objective details
    objective_text: Mapped[str] = mapped_column(Text, nullable=False)
    bloom_level: Mapped[str] = mapped_column(String(50), nullable=False)  # remember, understand, apply, etc.
    
    # Measurement
    measurable_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    success_criteria: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Order and grouping
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    objective_group: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Relationships
    concept: Mapped["ExtractedConcept"] = relationship("ExtractedConcept", back_populates="learning_objectives")
    
    def __repr__(self) -> str:
        return f"<LearningObjective(id={self.id}, bloom_level={self.bloom_level})>"


class PrerequisiteMapping(BaseModel):
    """Prerequisite relationships with learning context."""
    
    __tablename__ = "prerequisite_mappings"
    __table_args__ = (
        Index("ix_prerequisite_mappings_concept_id", "concept_id"),
        Index("ix_prerequisite_mappings_prerequisite_id", "prerequisite_id"),
        UniqueConstraint("concept_id", "prerequisite_id", name="uq_prerequisite_mappings"),
        CheckConstraint(
            "concept_id != prerequisite_id",
            name="ck_prerequisite_mappings_no_self_reference"
        ),
    )
    
    concept_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_concepts.id", ondelete="CASCADE"),
        nullable=False
    )
    prerequisite_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_concepts.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Prerequisite details
    is_hard_requirement: Mapped[bool] = mapped_column(Boolean, default=True)
    minimum_mastery_level: Mapped[float] = mapped_column(Float, default=0.7)
    
    # Learning context
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    alternative_prerequisites: Mapped[List[UUID]] = mapped_column(ARRAY(UUID), default=list)
    
    # Relationships
    concept: Mapped["ExtractedConcept"] = relationship(
        "ExtractedConcept",
        foreign_keys=[concept_id],
        back_populates="prerequisites"
    )
    prerequisite: Mapped["ExtractedConcept"] = relationship(
        "ExtractedConcept",
        foreign_keys=[prerequisite_id]
    )
    
    def __repr__(self) -> str:
        return f"<PrerequisiteMapping({self.prerequisite_id} -> {self.concept_id})>"


class LearningPath(VersionedModel):
    """Generated learning paths through concepts."""
    
    __tablename__ = "learning_paths"
    __table_args__ = (
        Index("ix_learning_paths_generation_id", "generation_id"),
        Index("ix_learning_paths_target_concept_id", "target_concept_id"),
    )
    
    generation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_generations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Path details
    path_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Target and constraints
    target_concept_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_concepts.id")
    )
    target_certification: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Path characteristics
    total_concepts: Mapped[int] = mapped_column(Integer, default=0)
    estimated_hours: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty_progression: Mapped[List[float]] = mapped_column(ARRAY(Float), default=list)
    
    # Optimization metrics
    cognitive_load_score: Mapped[float] = mapped_column(Float, default=0.5)
    prerequisite_satisfaction_score: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Path data
    concept_sequence: Mapped[List[UUID]] = mapped_column(ARRAY(UUID), nullable=False)
    path_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    generation: Mapped["ContentGeneration"] = relationship("ContentGeneration")
    target_concept: Mapped[Optional["ExtractedConcept"]] = relationship("ExtractedConcept")
    path_nodes: Mapped[List["LearningPathNode"]] = relationship(
        "LearningPathNode",
        back_populates="learning_path",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<LearningPath(id={self.id}, name={self.path_name})>"


class LearningPathNode(BaseModel):
    """Individual nodes in a learning path."""
    
    __tablename__ = "learning_path_nodes"
    __table_args__ = (
        Index("ix_learning_path_nodes_path_id", "learning_path_id"),
        Index("ix_learning_path_nodes_concept_id", "concept_id"),
        Index("ix_learning_path_nodes_sequence_order", "sequence_order"),
        UniqueConstraint("learning_path_id", "sequence_order", name="uq_learning_path_nodes_order"),
    )
    
    learning_path_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=False
    )
    concept_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_concepts.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Node position and timing
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    recommended_duration_minutes: Mapped[float] = mapped_column(Float, default=30.0)
    
    # Learning activities
    learning_activities: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    practice_exercises: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Progress tracking
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)
    mastery_threshold: Mapped[float] = mapped_column(Float, default=0.8)
    
    # Context
    learning_context: Mapped[Optional[str]] = mapped_column(Text)
    transition_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    learning_path: Mapped["LearningPath"] = relationship("LearningPath", back_populates="path_nodes")
    concept: Mapped["ExtractedConcept"] = relationship("ExtractedConcept")
    
    def __repr__(self) -> str:
        return f"<LearningPathNode(path={self.learning_path_id}, order={self.sequence_order})>"


class DomainTaxonomy(BaseModel):
    """Domain taxonomy for organizing concepts."""
    
    __tablename__ = "domain_taxonomies"
    __table_args__ = (
        UniqueConstraint("domain", "category", "subcategory", name="uq_domain_taxonomies"),
        Index("ix_domain_taxonomies_domain", "domain"),
    )
    
    # Taxonomy structure
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon_name: Mapped[Optional[str]] = mapped_column(String(50))
    color_hex: Mapped[Optional[str]] = mapped_column(String(7))
    
    # Hierarchy
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("domain_taxonomies.id")
    )
    level: Mapped[int] = mapped_column(Integer, default=0)
    
    # Usage
    concept_count: Mapped[int] = mapped_column(Integer, default=0)
    
    def __repr__(self) -> str:
        return f"<DomainTaxonomy(domain={self.domain}, category={self.category})>"


# Create additional indexes for performance
Index("ix_concept_relationships_composite", ConceptRelationship.source_concept_id, ConceptRelationship.target_concept_id)
Index("ix_learning_paths_composite", LearningPath.generation_id, LearningPath.target_concept_id)
