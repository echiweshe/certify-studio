"""
GraphRAG Domain Extraction Agent - The Core Innovation.

Unified knowledge extraction using Graph-based Retrieval Augmented Generation.
Combines vector embeddings with knowledge graph for true understanding.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from pathlib import Path
import hashlib
from dataclasses import dataclass, field
from uuid import UUID, uuid4

import networkx as nx
import numpy as np
from loguru import logger

from .models import (
    ExtractionRequest,
    ExtractionResult,
    DomainKnowledge,
    Document,
    DocumentChunk,
    Concept,
    ConceptType,
    Relationship,
    RelationshipType,
    SearchQuery,
    SearchResult,
    ExtractionConfidence
)
from .document_processor import DocumentProcessor
from .concept_extractor import ConceptExtractor
from .relationship_mapper import RelationshipMapper
from .weight_calculator import WeightCalculator
from .knowledge_graph_builder import KnowledgeGraphBuilder

from ....agents.core.autonomous_agent import AutonomousAgent, AgentCapability
from ....shared.models import AgentBelief, AgentGoal, AgentPlan
from ....config import settings


class GraphRAGDomainExtractor(AutonomousAgent):
    """
    The heart of Certify Studio - GraphRAG knowledge extraction.
    
    This is where the magic happens:
    - Extracts concepts and relationships from any content
    - Builds unified knowledge graph with embeddings
    - Enables learning path generation through graph traversal
    - Supports multimodal content (text, video, images)
    """
    
    def __init__(self):
        super().__init__(
            agent_id=str(uuid4()),
            name="GraphRAGDomainExtractor",
            capabilities={
                AgentCapability.DOMAIN_EXTRACTION,
                AgentCapability.KNOWLEDGE_GRAPH_BUILDING,
                AgentCapability.CONCEPT_IDENTIFICATION,
                AgentCapability.RELATIONSHIP_MAPPING,
                AgentCapability.MULTIMODAL_UNDERSTANDING,
                AgentCapability.LEARNING
            }
        )
        
        # Core processors
        self.document_processor = DocumentProcessor()
        self.concept_extractor = ConceptExtractor()
        self.relationship_mapper = RelationshipMapper()
        self.weight_calculator = WeightCalculator()
        self.graph_builder = KnowledgeGraphBuilder()
        
        # GraphRAG state
        self.graph = nx.DiGraph()
        self.embeddings = {}  # node_id -> embedding
        self.chunk_index = {}  # chunk_id -> node_ids
        
        # Multimodal processors (to be initialized)
        self.video_processor = None
        self.image_processor = None
        self.audio_processor = None
        
    async def initialize(self) -> None:
        """Initialize GraphRAG system."""
        await super().initialize()
        
        # Initialize multimodal processors if available
        try:
            from ....core.llm import VisionProcessor, AudioProcessor
            self.video_processor = VisionProcessor()
            self.audio_processor = AudioProcessor()
            logger.info("Multimodal processors initialized")
        except ImportError:
            logger.warning("Multimodal processors not available")
            
        logger.info("GraphRAG Domain Extractor initialized")
    
    async def extract_knowledge(
        self,
        request: ExtractionRequest
    ) -> ExtractionResult:
        """
        Main extraction pipeline - the core innovation.
        
        Process any content type and build unified knowledge graph.
        """
        logger.info(f"Extracting knowledge for domain: {request.domain_name}")
        
        # Process documents based on type
        chunks = []
        if request.video_urls:
            video_chunks = await self._process_videos(request.video_urls)
            chunks.extend(video_chunks)
            
        if request.pdf_paths:
            pdf_chunks = await self._process_pdfs(request.pdf_paths)
            chunks.extend(pdf_chunks)
            
        if request.text_content:
            text_chunks = await self._process_text(request.text_content)
            chunks.extend(text_chunks)
            
        # Extract concepts using multimodal understanding
        concepts = await self._extract_concepts(chunks)
        
        # Map relationships between concepts
        relationships = await self._map_relationships(concepts, chunks)
        
        # Build GraphRAG structure
        await self._build_graph(concepts, relationships, chunks)
        
        # Calculate importance weights
        await self._calculate_weights()
        
        # Generate embeddings for all nodes
        await self._generate_embeddings()
        
        # Find learning paths
        learning_paths = await self._discover_learning_paths()
        
        # Create result
        domain_knowledge = DomainKnowledge(
            domain_name=request.domain_name,
            certification_name=request.certification_name,
            concepts=concepts,
            relationships=relationships,
            total_concepts=len(concepts),
            total_relationships=len(relationships),
            extraction_confidence=self._calculate_confidence(),
            metadata={
                "learning_paths": learning_paths,
                "central_concepts": self._find_central_concepts(),
                "prerequisite_chains": self._find_prerequisite_chains()
            }
        )
        
        return ExtractionResult(
            success=True,
            domain_knowledge=domain_knowledge,
            extraction_time=0,  # Will be calculated
            chunks_processed=len(chunks),
            concepts_extracted=len(concepts),
            relationships_found=len(relationships)
        )
    
    async def _process_videos(self, video_urls: List[str]) -> List[DocumentChunk]:
        """Process videos using multimodal understanding."""
        chunks = []
        
        for url in video_urls:
            # Extract keyframes
            keyframes = await self.video_processor.extract_keyframes(url)
            
            # Extract audio transcript
            transcript = await self.audio_processor.transcribe(url)
            
            # Process each keyframe with context
            for i, frame in enumerate(keyframes):
                # Get surrounding transcript
                context_transcript = self._get_transcript_context(transcript, frame.timestamp)
                
                # Multimodal analysis
                analysis = await self.video_processor.analyze_frame_with_context(
                    frame,
                    context_transcript
                )
                
                chunk = DocumentChunk(
                    content=analysis.description,
                    chunk_type="video_frame",
                    metadata={
                        "video_url": url,
                        "timestamp": frame.timestamp,
                        "visual_concepts": analysis.visual_concepts,
                        "transcript": context_transcript,
                        "frame_embedding": analysis.embedding
                    }
                )
                chunks.append(chunk)
                
        return chunks
    
    async def _extract_concepts(self, chunks: List[DocumentChunk]) -> List[Concept]:
        """Extract concepts using unified multimodal approach."""
        concepts = {}
        
        for chunk in chunks:
            # Extract based on chunk type
            if chunk.chunk_type == "video_frame":
                extracted = await self._extract_video_concepts(chunk)
            elif chunk.chunk_type == "pdf_text":
                extracted = await self._extract_text_concepts(chunk)
            else:
                extracted = await self._extract_text_concepts(chunk)
                
            # Merge concepts
            for concept in extracted:
                if concept.name in concepts:
                    # Merge evidence from different sources
                    concepts[concept.name].evidence.extend(concept.evidence)
                    concepts[concept.name].confidence = max(
                        concepts[concept.name].confidence,
                        concept.confidence
                    )
                else:
                    concepts[concept.name] = concept
                    
        return list(concepts.values())
    
    async def _build_graph(
        self,
        concepts: List[Concept],
        relationships: List[Relationship],
        chunks: List[DocumentChunk]
    ) -> None:
        """Build the GraphRAG structure."""
        # Add concept nodes
        for concept in concepts:
            self.graph.add_node(
                concept.id,
                name=concept.name,
                type=concept.type,
                attributes=concept.attributes,
                confidence=concept.confidence,
                node_type="concept"
            )
            
        # Add chunk nodes
        for chunk in chunks:
            self.graph.add_node(
                chunk.id,
                content=chunk.content[:200],  # Preview
                chunk_type=chunk.chunk_type,
                metadata=chunk.metadata,
                node_type="chunk"
            )
            
            # Link chunks to concepts they contain
            for concept in concepts:
                if self._chunk_contains_concept(chunk, concept):
                    self.graph.add_edge(
                        chunk.id,
                        concept.id,
                        relationship="contains"
                    )
        
        # Add concept relationships
        for rel in relationships:
            self.graph.add_edge(
                rel.source_id,
                rel.target_id,
                relationship=rel.type,
                strength=rel.strength,
                evidence=rel.evidence
            )
    
    async def _generate_embeddings(self) -> None:
        """Generate embeddings for GraphRAG search."""
        from ....core.llm import MultimodalLLM
        llm = MultimodalLLM()
        
        for node_id, data in self.graph.nodes(data=True):
            if data["node_type"] == "concept":
                # Embed concept with context
                context = self._get_concept_context(node_id)
                embedding = await llm.embed_text(f"{data['name']}: {context}")
                self.embeddings[node_id] = embedding
            elif data["node_type"] == "chunk":
                # Use existing embedding if available
                if "frame_embedding" in data.get("metadata", {}):
                    self.embeddings[node_id] = data["metadata"]["frame_embedding"]
                else:
                    embedding = await llm.embed_text(data["content"])
                    self.embeddings[node_id] = embedding
    
    async def graph_enhanced_search(self, query: str) -> List[SearchResult]:
        """
        GraphRAG search - combines vector similarity with graph traversal.
        
        This is the key innovation: search that understands relationships.
        """
        from ....core.llm import MultimodalLLM
        llm = MultimodalLLM()
        
        # Get query embedding
        query_embedding = await llm.embed_text(query)
        
        # Phase 1: Vector similarity search
        similar_nodes = self._vector_search(query_embedding, top_k=5)
        
        # Phase 2: Graph expansion
        expanded_context = set()
        for node_id, score in similar_nodes:
            # Get related nodes through graph traversal
            related = self._traverse_graph(node_id, max_hops=2)
            for related_id, distance in related:
                # Combine vector score with graph distance
                combined_score = score * (1.0 / (1.0 + distance))
                expanded_context.add((related_id, combined_score))
        
        # Phase 3: Rank by combined score
        results = []
        for node_id, score in sorted(expanded_context, key=lambda x: x[1], reverse=True)[:10]:
            node_data = self.graph.nodes[node_id]
            
            # Get full context including relationships
            context = self._get_node_context_with_relationships(node_id)
            
            result = SearchResult(
                content=context,
                score=score,
                metadata={
                    "node_id": node_id,
                    "node_type": node_data["node_type"],
                    "relationships": self._get_node_relationships(node_id)
                }
            )
            results.append(result)
            
        return results
    
    async def generate_learning_path(
        self,
        start_concept: str,
        end_concept: str
    ) -> List[Dict[str, Any]]:
        """
        Generate optimal learning path using graph structure.
        
        This is what makes our system special for education.
        """
        # Find concept nodes
        start_node = self._find_concept_node(start_concept)
        end_node = self._find_concept_node(end_concept)
        
        if not start_node or not end_node:
            return []
            
        # Find all paths considering prerequisites
        all_paths = list(nx.all_simple_paths(
            self.graph,
            start_node,
            end_node,
            cutoff=10
        ))
        
        # Score paths based on:
        # 1. Prerequisite satisfaction
        # 2. Cognitive load progression
        # 3. Total path difficulty
        scored_paths = []
        for path in all_paths:
            score = self._score_learning_path(path)
            scored_paths.append((path, score))
            
        # Return best path with details
        best_path = max(scored_paths, key=lambda x: x[1])[0]
        
        path_details = []
        for i, node_id in enumerate(best_path):
            node_data = self.graph.nodes[node_id]
            
            # Get associated content
            content_chunks = self._get_node_content(node_id)
            
            path_details.append({
                "step": i + 1,
                "concept": node_data["name"],
                "type": node_data["type"],
                "content": content_chunks,
                "prerequisites": self._get_prerequisites(node_id),
                "learning_time": self._estimate_learning_time(node_id)
            })
            
        return path_details
    
    def _vector_search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """Perform vector similarity search."""
        scores = []
        
        for node_id, embedding in self.embeddings.items():
            # Cosine similarity
            score = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            scores.append((node_id, score))
            
        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
    
    def _traverse_graph(self, start_node: str, max_hops: int = 2) -> List[Tuple[str, int]]:
        """Traverse graph from start node."""
        visited = {start_node: 0}
        queue = [(start_node, 0)]
        
        while queue:
            node, distance = queue.pop(0)
            
            if distance >= max_hops:
                continue
                
            # Get neighbors
            for neighbor in self.graph.neighbors(node):
                if neighbor not in visited or visited[neighbor] > distance + 1:
                    visited[neighbor] = distance + 1
                    queue.append((neighbor, distance + 1))
                    
        return [(node, dist) for node, dist in visited.items() if node != start_node]
    
    def _find_central_concepts(self) -> List[str]:
        """Find most important concepts in the graph."""
        # Use PageRank to find central concepts
        pagerank = nx.pagerank(self.graph)
        
        concept_nodes = [
            (node, score) for node, score in pagerank.items()
            if self.graph.nodes[node]["node_type"] == "concept"
        ]
        
        return [node for node, score in sorted(concept_nodes, key=lambda x: x[1], reverse=True)[:10]]
    
    def _find_prerequisite_chains(self) -> List[List[str]]:
        """Find prerequisite learning sequences."""
        chains = []
        
        # Find nodes with no prerequisites (starting points)
        start_nodes = [
            node for node in self.graph.nodes()
            if self.graph.nodes[node]["node_type"] == "concept"
            and not any(
                self.graph.edges[edge].get("relationship") == "prerequisite_for"
                for edge in self.graph.in_edges(node)
            )
        ]
        
        # Build chains from each starting point
        for start in start_nodes:
            chain = self._build_prerequisite_chain(start)
            if len(chain) > 1:
                chains.append(chain)
                
        return chains
    
    # Stub implementations for abstract methods
    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        return {}
    
    async def deliberate(self) -> Optional[AgentGoal]:
        return None
    
    async def reflect(self, result: Dict[str, Any]) -> None:
        pass
    
    async def _analyze_situation(self) -> Dict[str, Any]:
        return {}
    
    async def _evaluate_outcome(self, outcome: Any) -> float:
        return 1.0
    
    async def _execute_step(self, step: Any) -> Any:
        return {}
    
    async def _generate_intentions(self) -> List[Any]:
        return []
    
    async def _update_beliefs(self, perception: Dict[str, Any]) -> None:
        pass
    
    async def _update_plans(self) -> None:
        pass


# Create singleton instance
domain_extractor = GraphRAGDomainExtractor()
