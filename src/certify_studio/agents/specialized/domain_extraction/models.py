"""
Domain Extraction Models.

Data structures for domain knowledge extraction, concept identification,
and relationship mapping from certification guides and technical documentation.
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class DocumentType(Enum):
    """Types of documents we can process."""
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    DOCX = "docx"
    EPUB = "epub"


class ConceptType(Enum):
    """Types of concepts in technical domains."""
    SERVICE = "service"
    FEATURE = "feature"
    CONCEPT = "concept"
    PRINCIPLE = "principle"
    BEST_PRACTICE = "best_practice"
    ARCHITECTURE_PATTERN = "architecture_pattern"
    SECURITY_CONTROL = "security_control"
    METRIC = "metric"
    TOOL = "tool"
    PROCESS = "process"


class RelationshipType(Enum):
    """Types of relationships between concepts."""
    DEPENDS_ON = "depends_on"
    RELATED_TO = "related_to"
    PART_OF = "part_of"
    IMPLEMENTS = "implements"
    EXTENDS = "extends"
    CONTRASTS_WITH = "contrasts_with"
    PREREQUISITE_FOR = "prerequisite_for"
    ALTERNATIVE_TO = "alternative_to"
    INTEGRATES_WITH = "integrates_with"
    SECURED_BY = "secured_by"


class DomainCategory(Enum):
    """High-level domain categories for certification content."""
    FUNDAMENTALS = "fundamentals"
    SERVICES = "services"
    SECURITY = "security"
    ARCHITECTURE = "architecture"
    BEST_PRACTICES = "best_practices"
    TROUBLESHOOTING = "troubleshooting"
    COST_OPTIMIZATION = "cost_optimization"
    PERFORMANCE = "performance"
    GOVERNANCE = "governance"
    MIGRATION = "migration"


class ExtractionConfidence(BaseModel):
    """Confidence metrics for extracted information."""
    overall: float = Field(ge=0.0, le=1.0)
    concept_identification: float = Field(ge=0.0, le=1.0)
    relationship_mapping: float = Field(ge=0.0, le=1.0)
    weight_calculation: float = Field(ge=0.0, le=1.0)
    metadata_extraction: float = Field(ge=0.0, le=1.0)


class Document(BaseModel):
    """Processed document with metadata."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_path: str
    document_type: DocumentType
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    sections: List[Dict[str, str]] = Field(default_factory=list)
    processing_date: datetime = Field(default_factory=datetime.utcnow)
    word_count: int = 0
    page_count: Optional[int] = None
    language: str = "en"
    encoding: str = "utf-8"


class DocumentChunk(BaseModel):
    """A chunk of document content for processing."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    content: str
    chunk_index: int
    total_chunks: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    concepts: List[str] = Field(default_factory=list)


class Concept(BaseModel):
    """A concept extracted from documentation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: ConceptType
    category: DomainCategory
    description: str
    aliases: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)
    source_chunks: List[str] = Field(default_factory=list)  # Chunk IDs
    importance_score: float = Field(ge=0.0, le=1.0)
    exam_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    prerequisites: List[str] = Field(default_factory=list)  # Concept IDs
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extracted_date: datetime = Field(default_factory=datetime.utcnow)


class Relationship(BaseModel):
    """A relationship between concepts."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_concept_id: str
    target_concept_id: str
    type: RelationshipType
    strength: float = Field(ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)  # Chunk IDs
    bidirectional: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DomainKnowledge(BaseModel):
    """Complete domain knowledge extracted from documents."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain_name: str
    certification_name: Optional[str] = None
    version: str = "1.0.0"
    concepts: List[Concept] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    concept_hierarchy: Dict[str, List[str]] = Field(default_factory=dict)
    domain_weights: Dict[DomainCategory, float] = Field(default_factory=dict)
    total_concepts: int = 0
    total_relationships: int = 0
    extraction_confidence: ExtractionConfidence = Field(default_factory=ExtractionConfidence)
    source_documents: List[str] = Field(default_factory=list)
    extraction_date: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractionRequest(BaseModel):
    """Request to extract domain knowledge from documents."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_paths: List[str]
    domain_name: str
    certification_name: Optional[str] = None
    extraction_config: Dict[str, Any] = Field(default_factory=dict)
    include_embeddings: bool = True
    chunk_size: int = 500
    chunk_overlap: int = 50
    min_concept_frequency: int = 2
    min_relationship_strength: float = 0.3
    language: str = "en"


class ExtractionResult(BaseModel):
    """Result of domain knowledge extraction."""
    request_id: str
    success: bool
    domain_knowledge: Optional[DomainKnowledge] = None
    documents_processed: int = 0
    chunks_created: int = 0
    concepts_extracted: int = 0
    relationships_found: int = 0
    processing_time_seconds: float = 0.0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ConceptCluster(BaseModel):
    """A cluster of related concepts."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: DomainCategory
    concepts: List[str]  # Concept IDs
    centroid_concept: str  # Most representative concept
    cohesion_score: float = Field(ge=0.0, le=1.0)
    description: str


class LearningPath(BaseModel):
    """A suggested learning path through concepts."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    concept_sequence: List[str]  # Ordered list of concept IDs
    estimated_duration_hours: float
    difficulty_level: str  # "beginner", "intermediate", "advanced"
    prerequisites: List[str] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)


class SearchQuery(BaseModel):
    """Query to search the knowledge base."""
    query: str
    domain_filter: Optional[str] = None
    concept_type_filter: Optional[List[ConceptType]] = None
    category_filter: Optional[List[DomainCategory]] = None
    max_results: int = 10
    include_relationships: bool = True
    min_relevance_score: float = 0.5


class SearchResult(BaseModel):
    """Result from knowledge base search."""
    concept: Concept
    relevance_score: float
    matching_chunks: List[DocumentChunk] = Field(default_factory=list)
    related_concepts: List[Tuple[str, RelationshipType, float]] = Field(default_factory=list)
    context_summary: Optional[str] = None


class KnowledgeBaseStats(BaseModel):
    """Statistics about the knowledge base."""
    total_documents: int = 0
    total_chunks: int = 0
    total_concepts: int = 0
    total_relationships: int = 0
    concepts_by_type: Dict[ConceptType, int] = Field(default_factory=dict)
    concepts_by_category: Dict[DomainCategory, int] = Field(default_factory=dict)
    average_concept_connections: float = 0.0
    most_connected_concepts: List[Tuple[str, int]] = Field(default_factory=list)
    last_update: datetime = Field(default_factory=datetime.utcnow)


class StudyMaterial(BaseModel):
    """Generated study material from domain knowledge."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    material_type: str  # "guide", "flashcards", "quiz", "mind_map", "summary"
    content: str
    format: str  # "markdown", "html", "pdf"
    concepts_covered: List[str] = Field(default_factory=list)
    estimated_study_time_minutes: int
    difficulty_level: str
    generated_date: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result of validating extracted knowledge."""
    is_valid: bool
    completeness_score: float = Field(ge=0.0, le=1.0)
    accuracy_score: float = Field(ge=0.0, le=1.0)
    consistency_score: float = Field(ge=0.0, le=1.0)
    coverage_gaps: List[str] = Field(default_factory=list)
    inconsistencies: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
