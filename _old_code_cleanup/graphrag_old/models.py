"""
Data models for GraphRAG troubleshooting system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple
from uuid import UUID, uuid4

import numpy as np


class IssueType(str, Enum):
    """Types of troubleshooting issues."""
    CONNECTIVITY = "connectivity"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CONFIGURATION = "configuration"
    DATA_INTEGRITY = "data_integrity"
    AUTHENTICATION = "authentication"
    RESOURCE_LIMIT = "resource_limit"
    DEPLOYMENT = "deployment"
    INTEGRATION = "integration"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RelationshipType(str, Enum):
    """Types of relationships in troubleshooting graph."""
    CAUSES = "causes"
    CAUSED_BY = "caused_by"
    AFFECTS = "affects"
    AFFECTED_BY = "affected_by"
    RESOLVES = "resolves"
    RESOLVED_BY = "resolved_by"
    REQUIRES = "requires"
    REQUIRED_BY = "required_by"
    SIMILAR_TO = "similar_to"
    PART_OF = "part_of"
    CONTAINS = "contains"
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    VERIFIES = "verifies"
    VERIFIED_BY = "verified_by"


@dataclass
class TroubleshootingIssue:
    """Represents a troubleshooting issue in the graph."""
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    symptoms: List[str] = field(default_factory=list)
    type: IssueType = IssueType.UNKNOWN
    severity: Severity = Severity.MEDIUM
    affected_components: List[str] = field(default_factory=list)
    
    # Graph properties
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Tracking
    occurrence_count: int = 0
    last_seen: Optional[datetime] = None
    resolution_rate: float = 0.0
    avg_resolution_time: float = 0.0  # in minutes
    
    # Related entities
    related_concepts: List[str] = field(default_factory=list)  # From learning graph
    tags: List[str] = field(default_factory=list)


@dataclass
class RootCause:
    """Represents a root cause of an issue."""
    id: UUID = field(default_factory=uuid4)
    issue_id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    likelihood: float = 0.5  # 0-1 probability
    
    # Diagnostic information
    diagnostic_steps: List[str] = field(default_factory=list)
    verification_commands: List[str] = field(default_factory=list)
    expected_outputs: Dict[str, str] = field(default_factory=dict)
    
    # Evidence
    evidence_patterns: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    
    # Related causes
    prerequisite_causes: List[UUID] = field(default_factory=list)
    alternative_causes: List[UUID] = field(default_factory=list)


@dataclass
class Solution:
    """Represents a solution to an issue or root cause."""
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    
    # Solution details
    steps: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    code_snippets: Dict[str, str] = field(default_factory=dict)
    
    # Applicability
    applies_to_issues: List[UUID] = field(default_factory=list)
    applies_to_causes: List[UUID] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    
    # Effectiveness
    success_rate: float = 0.0
    avg_implementation_time: float = 0.0  # minutes
    risk_level: str = "low"  # low, medium, high
    
    # Verification
    verification_steps: List[str] = field(default_factory=list)
    rollback_procedure: Optional[str] = None
    
    # Metadata
    requires_restart: bool = False
    requires_downtime: bool = False
    automation_available: bool = False
    embedding: Optional[np.ndarray] = None


@dataclass
class DiagnosticPath:
    """Represents a diagnostic path through the troubleshooting graph."""
    id: UUID = field(default_factory=uuid4)
    starting_issue: UUID = field(default_factory=uuid4)
    
    # Path information
    nodes: List[UUID] = field(default_factory=list)  # Ordered list of node IDs
    edges: List[Tuple[UUID, UUID, RelationshipType]] = field(default_factory=list)
    
    # Path quality metrics
    confidence: float = 0.0
    total_distance: float = 0.0
    complexity: int = 0  # Number of steps
    
    # Diagnostic information
    checks_required: List[str] = field(default_factory=list)
    potential_causes: List[RootCause] = field(default_factory=list)
    recommended_solutions: List[Solution] = field(default_factory=list)
    
    # Historical performance
    times_used: int = 0
    success_rate: float = 0.0
    avg_resolution_time: float = 0.0


@dataclass
class IssuePattern:
    """Represents a pattern of related issues."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    
    # Pattern components
    issue_sequence: List[UUID] = field(default_factory=list)
    common_symptoms: List[str] = field(default_factory=list)
    common_causes: List[UUID] = field(default_factory=list)
    
    # Pattern metrics
    frequency: int = 0
    seasonal: bool = False
    trend: str = "stable"  # increasing, decreasing, stable
    
    # Predictive elements
    early_warning_signs: List[str] = field(default_factory=list)
    prevention_steps: List[str] = field(default_factory=list)
    
    # Embedding for pattern matching
    embedding: Optional[np.ndarray] = None


@dataclass
class GraphNode:
    """Generic node in the GraphRAG system."""
    id: UUID = field(default_factory=uuid4)
    type: str = ""  # issue, cause, solution, diagnostic_step
    content: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GraphEdge:
    """Edge in the GraphRAG system."""
    id: UUID = field(default_factory=uuid4)
    source_id: UUID = field(default_factory=uuid4)
    target_id: UUID = field(default_factory=uuid4)
    relationship_type: RelationshipType = RelationshipType.SIMILAR_TO
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GraphRAGQuery:
    """Query for the GraphRAG system."""
    query_text: str
    query_embedding: Optional[np.ndarray] = None
    
    # Search parameters
    max_results: int = 10
    max_depth: int = 3
    min_confidence: float = 0.5
    
    # Filtering
    issue_types: Optional[List[IssueType]] = None
    severity_filter: Optional[List[Severity]] = None
    component_filter: Optional[List[str]] = None
    
    # Graph traversal rules
    allowed_relationships: List[RelationshipType] = field(default_factory=lambda: [
        RelationshipType.CAUSES,
        RelationshipType.RESOLVES,
        RelationshipType.SIMILAR_TO
    ])
    
    # Context
    user_context: Dict[str, Any] = field(default_factory=dict)
    historical_issues: List[UUID] = field(default_factory=list)


@dataclass
class GraphRAGResult:
    """Result from GraphRAG query."""
    query_id: UUID = field(default_factory=uuid4)
    
    # Primary results
    diagnostic_paths: List[DiagnosticPath] = field(default_factory=list)
    identified_issues: List[TroubleshootingIssue] = field(default_factory=list)
    root_causes: List[RootCause] = field(default_factory=list)
    solutions: List[Solution] = field(default_factory=list)
    
    # Reasoning trace
    reasoning_steps: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    # Graph context
    traversed_nodes: Set[UUID] = field(default_factory=set)
    traversed_edges: List[GraphEdge] = field(default_factory=list)
    
    # Metrics
    query_time: float = 0.0
    nodes_examined: int = 0
    paths_evaluated: int = 0


@dataclass
class GraphRAGConfig:
    """Configuration for GraphRAG system."""
    # Neo4j connection
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    
    # Embedding configuration
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536
    
    # Graph traversal
    max_traversal_depth: int = 5
    max_paths_per_query: int = 10
    similarity_threshold: float = 0.7
    
    # Caching
    enable_caching: bool = True
    cache_ttl: int = 3600  # seconds
    
    # Performance
    batch_size: int = 100
    max_concurrent_queries: int = 10
    
    # Learning
    enable_learning: bool = True
    feedback_weight: float = 0.1
    pattern_detection_threshold: int = 5


@dataclass
class TroubleshootingSession:
    """Represents a complete troubleshooting session."""
    id: UUID = field(default_factory=uuid4)
    user_id: Optional[str] = None
    
    # Session timeline
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
    # Problem description
    initial_query: str = ""
    symptoms: List[str] = field(default_factory=list)
    affected_systems: List[str] = field(default_factory=list)
    
    # Diagnostic journey
    queries_made: List[GraphRAGQuery] = field(default_factory=list)
    paths_explored: List[DiagnosticPath] = field(default_factory=list)
    issues_identified: List[TroubleshootingIssue] = field(default_factory=list)
    
    # Resolution
    root_cause_found: Optional[RootCause] = None
    solution_applied: Optional[Solution] = None
    resolution_successful: Optional[bool] = None
    
    # Feedback and learning
    user_feedback: Optional[str] = None
    effectiveness_rating: Optional[float] = None
    lessons_learned: List[str] = field(default_factory=list)
