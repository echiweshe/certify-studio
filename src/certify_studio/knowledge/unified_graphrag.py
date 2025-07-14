"""
Unified GraphRAG System for Certify Studio

This module replaces the separate RAG and Knowledge Base with a single,
unified GraphRAG system that handles ALL knowledge representation and retrieval.

Following the IMMUTABLE VISION: One AI Agent Operating System, not multiple systems.
"""

import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

import numpy as np
from neo4j import AsyncGraphDatabase
import openai
from loguru import logger

from ..agents.specialized.domain_extraction.models import (
    Concept, 
    Relationship,
    DomainKnowledge,
    SearchQuery,
    SearchResult
)
from ..agents.core import AgentCapability
from ..core.llm import MultimodalLLM as LLMRouter


class UnifiedNodeType(Enum):
    """All node types in our unified graph."""
    # Educational nodes
    CONCEPT = "Concept"
    PROCEDURE = "Procedure"
    LEARNING_OBJECTIVE = "LearningObjective"
    PREREQUISITE = "Prerequisite"
    DOMAIN = "Domain"
    CERTIFICATION = "Certification"
    
    # Content nodes
    CHUNK = "Chunk"
    DOCUMENT = "Document"
    SECTION = "Section"
    
    # Troubleshooting nodes (integrated, not separate!)
    ISSUE = "Issue"
    CAUSE = "Cause"
    SOLUTION = "Solution"
    DIAGNOSTIC_STEP = "DiagnosticStep"
    
    # Meta nodes
    PATTERN = "Pattern"
    BEST_PRACTICE = "BestPractice"
    EXAMPLE = "Example"


class UnifiedRelationType(Enum):
    """All relationship types in our unified graph."""
    # Learning relationships
    PREREQUISITE_OF = "PREREQUISITE_OF"
    RELATES_TO = "RELATES_TO"
    PART_OF = "PART_OF"
    TEACHES = "TEACHES"
    DEMONSTRATES = "DEMONSTRATES"
    
    # Problem-solving relationships
    CAUSES = "CAUSES"
    RESOLVES = "RESOLVES"
    DIAGNOSES = "DIAGNOSES"
    PREVENTS = "PREVENTS"
    
    # Content relationships
    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"
    EXTRACTED_FROM = "EXTRACTED_FROM"
    
    # Meta relationships
    SIMILAR_TO = "SIMILAR_TO"
    ALTERNATIVE_TO = "ALTERNATIVE_TO"
    ENHANCES = "ENHANCES"


@dataclass
class UnifiedGraphNode:
    """Unified node structure for all knowledge."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: UnifiedNodeType = UnifiedNodeType.CONCEPT
    name: str = ""
    description: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Unified properties for all node types
    difficulty_level: float = 0.5
    importance_score: float = 0.5
    confidence_score: float = 1.0
    usage_count: int = 0
    success_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "content": json.dumps(self.content),
            "embedding": self.embedding.tolist() if self.embedding is not None else None,
            "metadata": json.dumps(self.metadata),
            "difficulty_level": self.difficulty_level,
            "importance_score": self.importance_score,
            "confidence_score": self.confidence_score,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass 
class UnifiedGraphEdge:
    """Unified edge structure for all relationships."""
    source_id: str
    target_id: str
    type: UnifiedRelationType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GraphRAGQuery:
    """Unified query structure."""
    query_text: str
    query_type: str = "general"  # general, educational, troubleshooting, exploratory
    query_embedding: Optional[np.ndarray] = None
    context: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    max_depth: int = 3
    max_results: int = 10
    include_paths: bool = True
    include_explanations: bool = True


@dataclass
class GraphRAGResult:
    """Unified result structure."""
    query: GraphRAGQuery
    nodes: List[UnifiedGraphNode] = field(default_factory=list)
    edges: List[UnifiedGraphEdge] = field(default_factory=list)
    paths: List[List[str]] = field(default_factory=list)
    explanations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    processing_time: float = 0.0
    
    def to_search_results(self) -> List[SearchResult]:
        """Convert to legacy SearchResult format for compatibility."""
        results = []
        for node in self.nodes:
            results.append(SearchResult(
                content=node.description,
                metadata={
                    "id": node.id,
                    "type": node.type.value,
                    "name": node.name,
                    **node.metadata
                },
                score=node.importance_score * self.confidence,
                source=node.metadata.get("source", "knowledge_graph")
            ))
        return results


class UnifiedGraphRAG:
    """
    The ONE unified GraphRAG system for Certify Studio.
    
    This replaces:
    - ChromaDB vector store
    - Separate knowledge base
    - Separate troubleshooting graph
    
    Into ONE cohesive system that understands:
    - Educational concepts and their relationships
    - How concepts are taught and learned
    - Common problems and their solutions
    - Everything is connected in one graph!
    """
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = AsyncGraphDatabase.driver(
            neo4j_uri, 
            auth=(neo4j_user, neo4j_password)
        )
        self.llm_router = LLMRouter()
        self._embedding_cache = {}
        
    async def initialize(self):
        """Initialize the unified graph database."""
        try:
            await self.driver.verify_connectivity()
            logger.info("Connected to Neo4j successfully")
            
            # Create unified indexes
            await self._create_unified_indexes()
            
        except Exception as e:
            logger.error(f"Failed to initialize GraphRAG: {e}")
            raise
            
    async def _create_unified_indexes(self):
        """Create indexes for all node types."""
        async with self.driver.session() as session:
            # Constraints for uniqueness
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Concept) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Procedure) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Chunk) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Issue) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Solution) REQUIRE n.id IS UNIQUE",
            ]
            
            # Regular indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (n:Concept) ON (n.name)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Concept) ON (n.importance_score)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Procedure) ON (n.name)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Chunk) ON (n.document_id)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Issue) ON (n.severity)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Solution) ON (n.success_rate)",
            ]
            
            # Vector indexes for similarity search
            vector_indexes = [
                """
                CREATE VECTOR INDEX concept_embeddings IF NOT EXISTS
                FOR (n:Concept) ON (n.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                }}
                """,
                """
                CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
                FOR (n:Chunk) ON (n.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                }}
                """,
                """
                CREATE VECTOR INDEX unified_embeddings IF NOT EXISTS
                FOR (n) ON (n.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                }}
                """
            ]
            
            # Execute all index creations
            for query in constraints + indexes + vector_indexes:
                try:
                    await session.run(query)
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")
                    
    async def close(self):
        """Close the database connection."""
        await self.driver.close()
        
    async def add_node(self, node: UnifiedGraphNode) -> str:
        """Add any type of node to the unified graph."""
        # Generate embedding if not provided
        if node.embedding is None:
            node.embedding = await self._generate_embedding(
                f"{node.name} {node.description} {json.dumps(node.content)}"
            )
            
        async with self.driver.session() as session:
            query = f"""
            CREATE (n:{node.type.value} $properties)
            RETURN n.id as id
            """
            
            result = await session.run(query, properties=node.to_dict())
            record = await result.single()
            
            return record["id"]
            
    async def add_edge(self, edge: UnifiedGraphEdge) -> bool:
        """Add relationship between any nodes."""
        async with self.driver.session() as session:
            query = f"""
            MATCH (a {{id: $source_id}})
            MATCH (b {{id: $target_id}})
            CREATE (a)-[r:{edge.type.value} {{
                weight: $weight,
                properties: $properties,
                created_at: $created_at
            }}]->(b)
            RETURN r
            """
            
            result = await session.run(
                query,
                source_id=edge.source_id,
                target_id=edge.target_id,
                weight=edge.weight,
                properties=json.dumps(edge.properties),
                created_at=edge.created_at.isoformat()
            )
            
            return await result.single() is not None
            
    async def search(self, query: GraphRAGQuery) -> GraphRAGResult:
        """
        Unified search across all knowledge types.
        
        This is the MAIN interface for all retrieval operations.
        It handles educational queries, troubleshooting, and everything in between.
        """
        start_time = datetime.utcnow()
        
        # Generate embedding for query
        if query.query_embedding is None:
            query.query_embedding = await self._generate_embedding(query.query_text)
            
        # Determine search strategy based on query type
        if query.query_type == "educational":
            result = await self._search_educational(query)
        elif query.query_type == "troubleshooting":
            result = await self._search_troubleshooting(query)
        elif query.query_type == "exploratory":
            result = await self._search_exploratory(query)
        else:
            # General search - combines all approaches
            result = await self._search_general(query)
            
        # Add explanations if requested
        if query.include_explanations:
            result.explanations = await self._generate_explanations(result, query)
            
        # Calculate processing time
        result.processing_time = (datetime.utcnow() - start_time).total_seconds()
        result.query = query
        
        return result
        
    async def _search_general(self, query: GraphRAGQuery) -> GraphRAGResult:
        """General search combining vector similarity and graph traversal."""
        async with self.driver.session() as session:
            # Step 1: Vector similarity search across ALL node types
            vector_query = """
            CALL db.index.vector.queryNodes(
                'unified_embeddings',
                $k,
                $embedding
            ) YIELD node, score
            WHERE score > 0.7
            RETURN node, score
            ORDER BY score DESC
            LIMIT $limit
            """
            
            result = await session.run(
                vector_query,
                k=query.max_results * 2,  # Get more for filtering
                embedding=query.query_embedding.tolist(),
                limit=query.max_results
            )
            
            # Collect initial nodes
            initial_nodes = []
            async for record in result:
                node_data = dict(record["node"])
                node = self._dict_to_node(node_data)
                node.confidence_score = record["score"]
                initial_nodes.append(node)
                
            # Step 2: Graph expansion from initial nodes
            if query.max_depth > 0 and initial_nodes:
                expanded = await self._expand_graph(
                    session, 
                    [n.id for n in initial_nodes],
                    query.max_depth
                )
                
                # Merge results
                all_nodes = initial_nodes + expanded["nodes"]
                all_edges = expanded["edges"]
                
                # Step 3: Rank by combined score
                ranked_nodes = await self._rank_by_relevance(
                    all_nodes,
                    all_edges,
                    query
                )
                
                # Step 4: Extract paths if requested
                paths = []
                if query.include_paths:
                    paths = await self._extract_paths(
                        session,
                        ranked_nodes[:query.max_results],
                        query
                    )
                    
                return GraphRAGResult(
                    nodes=ranked_nodes[:query.max_results],
                    edges=all_edges,
                    paths=paths,
                    confidence=np.mean([n.confidence_score for n in ranked_nodes[:query.max_results]]),
                    query=query
                )
            else:
                return GraphRAGResult(
                    nodes=initial_nodes,
                    edges=[],
                    paths=[],
                    confidence=np.mean([n.confidence_score for n in initial_nodes]) if initial_nodes else 0.0,
                    query=query
                )
                
    async def _search_educational(self, query: GraphRAGQuery) -> GraphRAGResult:
        """Specialized search for educational content."""
        async with self.driver.session() as session:
            # Focus on concepts, procedures, and learning objectives
            query_text = """
            CALL db.index.vector.queryNodes(
                'concept_embeddings',
                $k,
                $embedding
            ) YIELD node, score
            WHERE score > 0.6
            WITH node, score
            MATCH (node)-[:PREREQUISITE_OF|RELATES_TO|TEACHES*0..2]-(related)
            WHERE related:Concept OR related:Procedure OR related:LearningObjective
            RETURN DISTINCT node, related, score
            ORDER BY score DESC
            LIMIT $limit
            """
            
            result = await session.run(
                query_text,
                k=50,
                embedding=query.query_embedding.tolist(),
                limit=query.max_results * 3
            )
            
            nodes = []
            edges = []
            seen_nodes = set()
            
            async for record in result:
                # Add primary node
                node_data = dict(record["node"])
                if node_data["id"] not in seen_nodes:
                    node = self._dict_to_node(node_data)
                    node.confidence_score = record["score"]
                    nodes.append(node)
                    seen_nodes.add(node_data["id"])
                    
                # Add related node
                if record["related"]:
                    related_data = dict(record["related"])
                    if related_data["id"] not in seen_nodes:
                        related_node = self._dict_to_node(related_data)
                        nodes.append(related_node)
                        seen_nodes.add(related_data["id"])
                        
            # Get learning paths
            if nodes and query.include_paths:
                paths = await self._find_learning_paths(session, nodes, query)
            else:
                paths = []
                
            return GraphRAGResult(
                nodes=nodes[:query.max_results],
                edges=edges,
                paths=paths,
                confidence=np.mean([n.confidence_score for n in nodes[:5]]) if nodes else 0.0,
                query=query
            )
            
    async def _search_troubleshooting(self, query: GraphRAGQuery) -> GraphRAGResult:
        """Specialized search for troubleshooting."""
        async with self.driver.session() as session:
            # Look for issues and trace to causes and solutions
            query_text = """
            // Find similar issues
            CALL db.index.vector.queryNodes(
                'unified_embeddings',
                20,
                $embedding
            ) YIELD node, score
            WHERE node:Issue AND score > 0.7
            WITH node as issue, score
            
            // Find causes and solutions
            MATCH (issue)-[:CAUSES]-(cause)
            OPTIONAL MATCH (cause)-[:RESOLVES]-(solution:Solution)
            OPTIONAL MATCH (solution)-[:REQUIRES]-(prereq)
            
            RETURN issue, cause, solution, prereq, score
            ORDER BY score DESC, solution.success_rate DESC
            LIMIT $limit
            """
            
            result = await session.run(
                query_text,
                embedding=query.query_embedding.tolist(),
                limit=query.max_results
            )
            
            # Build diagnostic paths
            diagnostic_paths = []
            nodes = []
            edges = []
            seen = set()
            
            async for record in result:
                path_nodes = []
                
                # Add issue
                if record["issue"]:
                    issue = self._dict_to_node(dict(record["issue"]))
                    if issue.id not in seen:
                        nodes.append(issue)
                        seen.add(issue.id)
                    path_nodes.append(issue.id)
                    
                # Add cause
                if record["cause"]:
                    cause = self._dict_to_node(dict(record["cause"]))
                    if cause.id not in seen:
                        nodes.append(cause)
                        seen.add(cause.id)
                    path_nodes.append(cause.id)
                    
                    # Add edge
                    edges.append(UnifiedGraphEdge(
                        source_id=issue.id,
                        target_id=cause.id,
                        type=UnifiedRelationType.CAUSES
                    ))
                    
                # Add solution
                if record["solution"]:
                    solution = self._dict_to_node(dict(record["solution"]))
                    if solution.id not in seen:
                        nodes.append(solution)
                        seen.add(solution.id)
                    path_nodes.append(solution.id)
                    
                    # Add edge
                    edges.append(UnifiedGraphEdge(
                        source_id=cause.id,
                        target_id=solution.id,
                        type=UnifiedRelationType.RESOLVES
                    ))
                    
                if path_nodes:
                    diagnostic_paths.append(path_nodes)
                    
            return GraphRAGResult(
                nodes=nodes,
                edges=edges,
                paths=diagnostic_paths,
                confidence=0.85 if nodes else 0.0,
                query=query
            )
            
    async def _search_exploratory(self, query: GraphRAGQuery) -> GraphRAGResult:
        """Exploratory search for discovering connections."""
        # This would implement more advanced graph algorithms
        # For now, delegate to general search
        return await self._search_general(query)
        
    async def _expand_graph(
        self, 
        session, 
        node_ids: List[str], 
        max_depth: int
    ) -> Dict[str, Any]:
        """Expand graph from initial nodes."""
        # Fallback implementation without APOC:
        all_nodes = []
        all_edges = []
        visited = set(node_ids)
        current_level = node_ids
        
        for depth in range(max_depth):
            if not current_level:
                break
                
            # Get all neighbors
            neighbor_query = """
            UNWIND $node_ids as node_id
            MATCH (n {id: node_id})-[r]-(neighbor)
            WHERE NOT neighbor.id IN $visited
            RETURN DISTINCT neighbor, r, n.id as source_id
            """
            
            result = await session.run(
                neighbor_query,
                node_ids=current_level,
                visited=list(visited)
            )
            
            next_level = []
            async for record in result:
                neighbor = self._dict_to_node(dict(record["neighbor"]))
                if neighbor.id not in visited:
                    all_nodes.append(neighbor)
                    visited.add(neighbor.id)
                    next_level.append(neighbor.id)
                    
                # Add edge
                rel = record["r"]
                edge = UnifiedGraphEdge(
                    source_id=record["source_id"],
                    target_id=neighbor.id,
                    type=UnifiedRelationType(rel.type),
                    weight=rel.get("weight", 1.0)
                )
                all_edges.append(edge)
                
            current_level = next_level
            
        return {"nodes": all_nodes, "edges": all_edges}
        
    async def _rank_by_relevance(
        self,
        nodes: List[UnifiedGraphNode],
        edges: List[UnifiedGraphEdge],
        query: GraphRAGQuery
    ) -> List[UnifiedGraphNode]:
        """Rank nodes by combined relevance score."""
        # Build adjacency for PageRank-style scoring
        adjacency = {}
        for edge in edges:
            if edge.source_id not in adjacency:
                adjacency[edge.source_id] = []
            adjacency[edge.source_id].append((edge.target_id, edge.weight))
            
        # Calculate scores
        scored_nodes = []
        for node in nodes:
            # Base score from vector similarity
            base_score = node.confidence_score
            
            # Graph centrality bonus
            centrality_score = len(adjacency.get(node.id, [])) / (len(edges) + 1)
            
            # Type relevance
            type_score = self._get_type_relevance(node.type, query.query_type)
            
            # Recency bonus
            age_days = (datetime.utcnow() - node.updated_at).days
            recency_score = 1.0 / (1.0 + age_days / 30.0)
            
            # Usage/success bonus
            usage_score = min(1.0, node.usage_count / 100.0)
            success_score = node.success_rate
            
            # Combined score
            final_score = (
                0.4 * base_score +
                0.2 * centrality_score +
                0.15 * type_score +
                0.1 * recency_score +
                0.1 * usage_score +
                0.05 * success_score
            )
            
            node.confidence_score = final_score
            scored_nodes.append(node)
            
        # Sort by final score
        scored_nodes.sort(key=lambda n: n.confidence_score, reverse=True)
        
        return scored_nodes
        
    async def _extract_paths(
        self,
        session,
        nodes: List[UnifiedGraphNode],
        query: GraphRAGQuery
    ) -> List[List[str]]:
        """Extract meaningful paths between nodes."""
        paths = []
        
        # For each pair of top nodes, find shortest paths
        for i in range(min(3, len(nodes))):
            for j in range(i + 1, min(5, len(nodes))):
                path_query = """
                MATCH path = shortestPath(
                    (start {id: $start_id})-[*..6]-(end {id: $end_id})
                )
                RETURN [n in nodes(path) | n.id] as path_ids
                """
                
                result = await session.run(
                    path_query,
                    start_id=nodes[i].id,
                    end_id=nodes[j].id
                )
                
                record = await result.single()
                if record and record["path_ids"]:
                    paths.append(record["path_ids"])
                    
        return paths
        
    async def _generate_explanations(
        self,
        result: GraphRAGResult,
        query: GraphRAGQuery
    ) -> List[str]:
        """Generate explanations for why results are relevant."""
        explanations = []
        
        for i, node in enumerate(result.nodes[:5]):  # Top 5 only
            # Build context
            context = {
                "query": query.query_text,
                "node_type": node.type.value,
                "node_name": node.name,
                "node_description": node.description,
                "confidence": node.confidence_score,
                "relationships": []
            }
            
            # Find relationships for this node
            for edge in result.edges:
                if edge.source_id == node.id:
                    context["relationships"].append(f"{edge.type.value} -> {edge.target_id}")
                elif edge.target_id == node.id:
                    context["relationships"].append(f"{edge.source_id} -> {edge.type.value}")
                    
            # Generate explanation
            prompt = f"""
            Explain why this result is relevant to the query.
            Query: {query.query_text}
            Result: {node.name} ({node.type.value})
            Description: {node.description}
            Confidence: {node.confidence_score:.2f}
            Relationships: {', '.join(context['relationships'][:3])}
            
            Provide a brief, clear explanation in 1-2 sentences.
            """
            
            explanation = await self.llm_router.generate(
                prompt,
                temperature=0.3,
                max_tokens=100
            )
            
            explanations.append(f"{i+1}. {node.name}: {explanation.content}")
            
        return explanations
        
    def _dict_to_node(self, data: Dict[str, Any]) -> UnifiedGraphNode:
        """Convert dictionary to UnifiedGraphNode."""
        node = UnifiedGraphNode()
        
        # Set basic fields
        node.id = data.get("id", str(uuid.uuid4()))
        node.name = data.get("name", "")
        node.description = data.get("description", "")
        
        # Determine type
        if "labels" in data and data["labels"]:
            node.type = UnifiedNodeType(data["labels"][0])
        elif "type" in data:
            node.type = UnifiedNodeType(data["type"])
            
        # Parse JSON fields
        if "content" in data and isinstance(data["content"], str):
            try:
                node.content = json.loads(data["content"])
            except:
                node.content = {"raw": data["content"]}
        elif "content" in data:
            node.content = data["content"]
            
        if "metadata" in data and isinstance(data["metadata"], str):
            try:
                node.metadata = json.loads(data["metadata"])
            except:
                node.metadata = {"raw": data["metadata"]}
        elif "metadata" in data:
            node.metadata = data["metadata"]
            
        # Set numeric fields
        node.difficulty_level = float(data.get("difficulty_level", 0.5))
        node.importance_score = float(data.get("importance_score", 0.5))
        node.confidence_score = float(data.get("confidence_score", 1.0))
        node.usage_count = int(data.get("usage_count", 0))
        node.success_rate = float(data.get("success_rate", 0.0))
        
        # Parse datetime fields
        if "created_at" in data:
            if isinstance(data["created_at"], str):
                node.created_at = datetime.fromisoformat(data["created_at"])
            else:
                node.created_at = data["created_at"]
                
        if "updated_at" in data:
            if isinstance(data["updated_at"], str):
                node.updated_at = datetime.fromisoformat(data["updated_at"])
            else:
                node.updated_at = data["updated_at"]
            
        # Parse embedding
        if "embedding" in data and data["embedding"]:
            node.embedding = np.array(data["embedding"])
            
        return node
        
    def _get_type_relevance(self, node_type: UnifiedNodeType, query_type: str) -> float:
        """Get relevance score based on node type and query type."""
        relevance_map = {
            "educational": {
                UnifiedNodeType.CONCEPT: 1.0,
                UnifiedNodeType.PROCEDURE: 0.9,
                UnifiedNodeType.LEARNING_OBJECTIVE: 0.8,
                UnifiedNodeType.EXAMPLE: 0.7,
                UnifiedNodeType.PREREQUISITE: 0.6,
                UnifiedNodeType.CHUNK: 0.5,
            },
            "troubleshooting": {
                UnifiedNodeType.ISSUE: 1.0,
                UnifiedNodeType.SOLUTION: 0.9,
                UnifiedNodeType.CAUSE: 0.8,
                UnifiedNodeType.DIAGNOSTIC_STEP: 0.7,
                UnifiedNodeType.BEST_PRACTICE: 0.6,
            },
            "general": {
                # All types have moderate relevance
                node_type: 0.7 for node_type in UnifiedNodeType
            }
        }
        
        if query_type in relevance_map:
            return relevance_map[query_type].get(node_type, 0.5)
        return 0.5
        
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        # Check cache
        if text in self._embedding_cache:
            return self._embedding_cache[text]
            
        # Generate embedding using OpenAI
        response = await openai.Embedding.acreate(
            input=[text],
            model="text-embedding-3-small"
        )
        
        embedding = np.array(response['data'][0]['embedding'])
        
        # Cache it (limit cache size)
        if len(self._embedding_cache) < 1000:
            self._embedding_cache[text] = embedding
            
        return embedding
        
    async def _find_learning_paths(
        self,
        session,
        nodes: List[UnifiedGraphNode],
        query: GraphRAGQuery
    ) -> List[List[str]]:
        """Find optimal learning paths through concepts."""
        paths = []
        
        # Simple implementation - find prerequisite chains
        for node in nodes[:3]:  # Top 3 nodes
            path_query = """
            MATCH path = (start {id: $node_id})-[:PREREQUISITE_OF*0..5]->(end)
            WHERE end:Concept OR end:LearningObjective
            RETURN [n in nodes(path) | n.id] as path_ids
            ORDER BY length(path) DESC
            LIMIT 3
            """
            
            result = await session.run(path_query, node_id=node.id)
            
            async for record in result:
                path_ids = record["path_ids"]
                if len(path_ids) > 1:
                    paths.append(path_ids)
                    
        return paths
        
    async def import_from_domain_extraction(self, domain_knowledge: DomainKnowledge) -> Dict[str, int]:
        """Import domain knowledge into unified graph."""
        stats = {
            "concepts": 0,
            "procedures": 0,
            "relationships": 0,
            "chunks": 0
        }
        
        # Import concepts
        concept_map = {}
        for concept in domain_knowledge.concepts:
            node = UnifiedGraphNode(
                type=UnifiedNodeType.CONCEPT,
                name=concept.name,
                description=concept.description,
                content={
                    "type": concept.type,
                    "domain": concept.domain,
                    "original_id": concept.id
                },
                difficulty_level=concept.difficulty_level,
                importance_score=concept.importance_score,
                metadata=concept.metadata
            )
            
            node_id = await self.add_node(node)
            concept_map[concept.id] = node_id
            stats["concepts"] += 1
            
        # Import procedures
        procedure_map = {}
        for procedure in domain_knowledge.procedures:
            node = UnifiedGraphNode(
                type=UnifiedNodeType.PROCEDURE,
                name=procedure.name,
                description=procedure.description,
                content={
                    "steps": procedure.steps,
                    "prerequisites": procedure.prerequisites,
                    "outcomes": procedure.outcomes
                },
                difficulty_level=procedure.complexity_score,
                metadata=procedure.metadata
            )
            
            node_id = await self.add_node(node)
            procedure_map[procedure.id] = node_id
            stats["procedures"] += 1
            
        # Import relationships
        for rel in domain_knowledge.relationships:
            # Map relationship types
            rel_type = self._map_relationship_type(rel.type)
            
            # Get node IDs
            source_id = concept_map.get(rel.source_id) or procedure_map.get(rel.source_id)
            target_id = concept_map.get(rel.target_id) or procedure_map.get(rel.target_id)
            
            if source_id and target_id:
                edge = UnifiedGraphEdge(
                    source_id=source_id,
                    target_id=target_id,
                    type=rel_type,
                    weight=rel.strength,
                    properties={"evidence": rel.evidence}
                )
                
                await self.add_edge(edge)
                stats["relationships"] += 1
                
        # Import text chunks (for RAG compatibility)
        if hasattr(domain_knowledge, 'chunks'):
            for chunk in domain_knowledge.chunks:
                node = UnifiedGraphNode(
                    type=UnifiedNodeType.CHUNK,
                    name=f"Chunk from {chunk.metadata.get('source', 'unknown')}",
                    description=chunk.text[:200] + "...",
                    content={
                        "text": chunk.text,
                        "chunk_index": chunk.metadata.get("chunk_index", 0)
                    },
                    metadata=chunk.metadata,
                    embedding=chunk.embedding if hasattr(chunk, 'embedding') else None
                )
                
                node_id = await self.add_node(node)
                stats["chunks"] += 1
                
                # Link chunk to concepts it mentions
                for concept_id, original_id in concept_map.items():
                    if concept_id in chunk.text:  # Simple mention detection
                        edge = UnifiedGraphEdge(
                            source_id=node_id,
                            target_id=original_id,
                            type=UnifiedRelationType.REFERENCES,
                            weight=0.5
                        )
                        await self.add_edge(edge)
                        
        logger.info(f"Imported into unified graph: {stats}")
        return stats
        
    def _map_relationship_type(self, old_type: str) -> UnifiedRelationType:
        """Map old relationship types to unified types."""
        mapping = {
            "prerequisite": UnifiedRelationType.PREREQUISITE_OF,
            "related": UnifiedRelationType.RELATES_TO,
            "part_of": UnifiedRelationType.PART_OF,
            "teaches": UnifiedRelationType.TEACHES,
            "example_of": UnifiedRelationType.DEMONSTRATES,
            "similar": UnifiedRelationType.SIMILAR_TO,
        }
        
        return mapping.get(old_type.lower(), UnifiedRelationType.RELATES_TO)


# Compatibility layer for existing code
class UnifiedVectorStore:
    """
    Compatibility wrapper to make UnifiedGraphRAG work with existing vector store interface.
    This allows gradual migration of existing code.
    """
    
    def __init__(self, graphrag: UnifiedGraphRAG):
        self.graphrag = graphrag
        
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search using the old interface."""
        # Convert to GraphRAG query
        graphrag_query = GraphRAGQuery(
            query_text=query.query,
            query_type="general",
            max_results=query.max_results,
            context={"filters": query.filters}
        )
        
        # Perform search
        result = await self.graphrag.search(graphrag_query)
        
        # Convert to old format
        return result.to_search_results()
        
    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents using the old interface."""
        for doc in documents:
            node = UnifiedGraphNode(
                type=UnifiedNodeType.CHUNK,
                name=doc.get("title", "Document"),
                description=doc.get("text", "")[:200],
                content=doc,
                metadata=doc.get("metadata", {})
            )
            
            await self.graphrag.add_node(node)
            
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        async with self.graphrag.driver.session() as session:
            result = await session.run("""
                MATCH (n)
                RETURN 
                    count(n) as total_nodes,
                    count(DISTINCT labels(n)) as node_types
            """)
            
            record = await result.single()
            return {
                "total_nodes": record["total_nodes"],
                "node_types": record["node_types"]
            }
