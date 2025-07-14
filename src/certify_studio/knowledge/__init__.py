"""
Unified Knowledge System for Certify Studio

This module provides the ONE unified GraphRAG system that replaces separate
RAG and knowledge base implementations with a single, cohesive architecture.
"""

from .unified_graphrag import (
    UnifiedGraphRAG,
    UnifiedGraphNode,
    UnifiedGraphEdge,
    UnifiedNodeType,
    UnifiedRelationType,
    GraphRAGQuery,
    GraphRAGResult,
    UnifiedVectorStore
)
from .setup import setup_unified_system

__all__ = [
    "UnifiedGraphRAG",
    "UnifiedGraphNode", 
    "UnifiedGraphEdge",
    "UnifiedNodeType",
    "UnifiedRelationType",
    "GraphRAGQuery",
    "GraphRAGResult",
    "UnifiedVectorStore",
    "setup_unified_system"
]
