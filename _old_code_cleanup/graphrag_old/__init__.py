"""
GraphRAG Implementation for Customer Support Troubleshooting.

This module implements a full GraphRAG system that combines vector embeddings
with graph traversal for intelligent troubleshooting and root cause analysis.
"""

from .models import (
    TroubleshootingIssue,
    DiagnosticPath,
    RootCause,
    Solution,
    IssuePattern,
    GraphRAGConfig
)

from .graph_store import (
    Neo4jGraphStore,
    GraphRAGIndex
)

from .troubleshooting_engine import (
    GraphRAGTroubleshooter,
    DiagnosticReasoner,
    SolutionRanker
)

from .knowledge_integration import (
    KnowledgeGraphIntegrator,
    ConceptToIssueMapper
)

__all__ = [
    # Models
    "TroubleshootingIssue",
    "DiagnosticPath",
    "RootCause",
    "Solution",
    "IssuePattern",
    "GraphRAGConfig",
    
    # Core Components
    "Neo4jGraphStore",
    "GraphRAGIndex",
    "GraphRAGTroubleshooter",
    "DiagnosticReasoner",
    "SolutionRanker",
    
    # Integration
    "KnowledgeGraphIntegrator",
    "ConceptToIssueMapper"
]
