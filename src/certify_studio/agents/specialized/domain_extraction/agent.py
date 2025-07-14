"""
Domain Extraction Agent - GraphRAG Implementation Wrapper.

This agent wraps the GraphRAG extractor and provides the autonomous agent interface.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import time

from loguru import logger

from .models import (
    ExtractionRequest,
    ExtractionResult,
    DomainKnowledge,
    Document,
    DocumentChunk,
    Concept,
    Relationship,
    SearchQuery,
    SearchResult,
    ExtractionConfidence
)
from .graphrag_extractor import domain_extractor as graphrag_extractor

from ....agents.core.autonomous_agent import (
    AutonomousAgent,
    AgentCapability,
    AgentState,
    AgentBelief,
    AgentGoal,
    AgentPlan
)
from ....config import settings


class DomainExtractionAgent(AutonomousAgent):
    """
    Autonomous agent wrapper for GraphRAG domain extraction.
    
    This agent orchestrates the GraphRAG extractor within the autonomous agent framework.
    """
    
    def __init__(self):
        super().__init__(
            name="DomainExtractionAgent",
            capabilities={
                AgentCapability.DOMAIN_EXTRACTION,
                AgentCapability.KNOWLEDGE_GRAPH_BUILDING,
                AgentCapability.CONCEPT_IDENTIFICATION,
                AgentCapability.RELATIONSHIP_MAPPING,
                AgentCapability.MULTIMODAL_UNDERSTANDING,
                AgentCapability.LEARNING
            }
        )
        
        # Use the GraphRAG extractor
        self.graphrag = graphrag_extractor
        
        # Agent state
        self.current_request: Optional[ExtractionRequest] = None
        self.extraction_history: List[ExtractionResult] = []
        
    async def initialize(self) -> None:
        """Initialize the domain extraction agent."""
        await super().initialize()
        
        # Initialize GraphRAG
        await self.graphrag.initialize()
        
        logger.info("Domain extraction agent initialized with GraphRAG")
    
    async def extract_domain_knowledge(
        self,
        request: ExtractionRequest
    ) -> ExtractionResult:
        """
        Extract domain knowledge using GraphRAG.
        
        This is the main public interface.
        """
        logger.info(f"Starting GraphRAG extraction for {request.domain_name}")
        
        # Store current request
        self.current_request = request
        
        # Update beliefs
        self.beliefs.add(AgentBelief(
            content={
                "task": "domain_extraction",
                "domain": request.domain_name,
                "certification": request.certification_name,
                "start_time": datetime.now()
            },
            confidence=1.0,
            source="extraction_request",
            timestamp=datetime.now()
        ))
        
        # Set goal
        goal = AgentGoal(
            description=f"Extract knowledge from {request.domain_name}",
            priority=1.0,
            deadline=datetime.now(),
            success_criteria={
                "concepts_extracted": lambda x: x > 0,
                "relationships_found": lambda x: x > 0,
                "confidence": lambda x: x > 0.7
            }
        )
        
        # Create plan
        plan = await self.plan(goal)
        
        # Execute extraction
        start_time = time.time()
        try:
            # Use GraphRAG extractor
            result = await self.graphrag.extract_knowledge(request)
            
            # Update extraction time
            result.extraction_time = time.time() - start_time
            
            # Store in history
            self.extraction_history.append(result)
            
            # Reflect on results
            await self.reflect(result.__dict__)
            
            logger.info(
                f"GraphRAG extraction completed: "
                f"{result.concepts_extracted} concepts, "
                f"{result.relationships_found} relationships"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"GraphRAG extraction failed: {e}")
            return ExtractionResult(
                success=False,
                error_message=str(e),
                extraction_time=time.time() - start_time
            )
    
    async def search_knowledge(
        self,
        query: SearchQuery
    ) -> List[SearchResult]:
        """
        Search using GraphRAG enhanced search.
        
        Combines vector similarity with graph traversal.
        """
        logger.info(f"GraphRAG search: {query.query}")
        
        # Use GraphRAG search
        results = await self.graphrag.graph_enhanced_search(query.query)
        
        logger.info(f"Found {len(results)} results")
        return results
    
    async def generate_learning_path(
        self,
        start_concept: str,
        target_concept: str
    ) -> List[Dict[str, Any]]:
        """
        Generate learning path using graph structure.
        
        This leverages the knowledge graph for educational sequencing.
        """
        logger.info(f"Generating learning path: {start_concept} -> {target_concept}")
        
        path = await self.graphrag.generate_learning_path(
            start_concept,
            target_concept
        )
        
        logger.info(f"Generated path with {len(path)} steps")
        return path
    
    async def get_concept_prerequisites(
        self,
        concept_name: str
    ) -> List[str]:
        """Get prerequisites for a concept from the graph."""
        # Find concept node
        concept_node = None
        for node_id, data in self.graphrag.graph.nodes(data=True):
            if data.get("node_type") == "concept" and data.get("name") == concept_name:
                concept_node = node_id
                break
                
        if not concept_node:
            return []
            
        # Find prerequisites
        prerequisites = []
        for edge in self.graphrag.graph.in_edges(concept_node):
            edge_data = self.graphrag.graph.edges[edge]
            if edge_data.get("relationship") == "prerequisite_for":
                source_data = self.graphrag.graph.nodes[edge[0]]
                if source_data.get("node_type") == "concept":
                    prerequisites.append(source_data["name"])
                    
        return prerequisites
    
    async def get_concept_graph(self) -> Dict[str, Any]:
        """Get the concept graph structure for visualization."""
        nodes = []
        edges = []
        
        for node_id, data in self.graphrag.graph.nodes(data=True):
            if data.get("node_type") == "concept":
                nodes.append({
                    "id": node_id,
                    "name": data["name"],
                    "type": data.get("type", "concept"),
                    "confidence": data.get("confidence", 1.0)
                })
                
        for source, target, data in self.graphrag.graph.edges(data=True):
            source_data = self.graphrag.graph.nodes[source]
            target_data = self.graphrag.graph.nodes[target]
            
            if (source_data.get("node_type") == "concept" and 
                target_data.get("node_type") == "concept"):
                edges.append({
                    "source": source,
                    "target": target,
                    "relationship": data.get("relationship", "related"),
                    "strength": data.get("strength", 1.0)
                })
                
        return {
            "nodes": nodes,
            "edges": edges,
            "central_concepts": self.graphrag._find_central_concepts(),
            "prerequisite_chains": self.graphrag._find_prerequisite_chains()
        }
    
    # Required abstract method implementations
    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive environment for domain extraction opportunities."""
        observations = {}
        
        if "new_documents" in environment:
            observations["documents_to_process"] = environment["new_documents"]
            
        if "user_query" in environment:
            observations["search_needed"] = True
            observations["query"] = environment["user_query"]
            
        return observations
    
    async def deliberate(self) -> Optional[AgentGoal]:
        """Decide next extraction goal."""
        # Check if we have pending extraction requests
        for belief in self.beliefs:
            if belief.content.get("task") == "pending_extraction":
                return AgentGoal(
                    description="Process pending extraction",
                    priority=0.9,
                    success_criteria={
                        "extraction_complete": lambda x: x is True
                    }
                )
                
        return None
    
    async def plan(self, goal: AgentGoal) -> AgentPlan:
        """Create extraction plan."""
        steps = []
        
        if "Extract knowledge" in goal.description:
            steps = [
                {"action": "process_documents", "duration": 2.0},
                {"action": "extract_concepts", "duration": 3.0},
                {"action": "map_relationships", "duration": 2.0},
                {"action": "build_graph", "duration": 1.0},
                {"action": "generate_embeddings", "duration": 2.0}
            ]
            
        return AgentPlan(
            goal_id=goal.id,
            steps=steps,
            estimated_duration=sum(s["duration"] for s in steps)
        )
    
    async def reflect(self, result: Dict[str, Any]) -> None:
        """Reflect on extraction results to improve."""
        if result.get("success"):
            # Update beliefs about successful extraction patterns
            self.beliefs.add(AgentBelief(
                content={
                    "successful_extraction": {
                        "domain": self.current_request.domain_name if self.current_request else "unknown",
                        "concepts": result.get("concepts_extracted", 0),
                        "relationships": result.get("relationships_found", 0),
                        "techniques_used": ["graphrag", "multimodal"]
                    }
                },
                confidence=0.9,
                source="extraction_reflection",
                timestamp=datetime.now()
            ))
    
    # Stub implementations for remaining abstract methods
    async def _analyze_situation(self) -> Dict[str, Any]:
        return {"status": "ready", "graph_size": len(self.graphrag.graph.nodes())}
    
    async def _evaluate_outcome(self, outcome: Any) -> float:
        if isinstance(outcome, dict):
            concepts = outcome.get("concepts_extracted", 0)
            relationships = outcome.get("relationships_found", 0)
            if concepts > 50 and relationships > 100:
                return 1.0
            elif concepts > 20 and relationships > 40:
                return 0.8
            else:
                return 0.6
        return 0.5
    
    async def _execute_step(self, step: Any) -> Any:
        action = step.get("action")
        if action == "extract_concepts":
            return {"status": "completed", "concepts": len(self.graphrag.graph.nodes())}
        return {"status": "completed"}
    
    async def _generate_intentions(self) -> List[Any]:
        return []
    
    async def _update_beliefs(self, perception: Dict[str, Any]) -> None:
        if "documents_to_process" in perception:
            self.beliefs.add(AgentBelief(
                content={"pending_documents": perception["documents_to_process"]},
                confidence=1.0,
                source="perception",
                timestamp=datetime.now()
            ))
    
    async def _update_plans(self) -> None:
        pass
    
    async def get_current_knowledge(self) -> Optional[DomainKnowledge]:
        """Get the current knowledge graph state."""
        if not self.extraction_history:
            return None
            
        latest = self.extraction_history[-1]
        if latest.success and latest.domain_knowledge:
            return latest.domain_knowledge
            
        return None
