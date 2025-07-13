"""
Domain Extraction Agent - Main Orchestrator.

This agent extracts structured domain knowledge from certification guides and technical
documentation, building a comprehensive knowledge graph for educational content generation.
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
from .document_processor import DocumentProcessor
from .concept_extractor import ConceptExtractor
from .relationship_mapper import RelationshipMapper
from .weight_calculator import WeightCalculator
from .vector_store import VectorStore
from .knowledge_graph_builder import KnowledgeGraphBuilder

from ....core.agents.base import AutonomousAgent
from ....core.agents.types import (
    AgentCapability,
    AgentState,
    AgentBelief,
    AgentGoal,
    AgentPlan,
    PlanStep
)
from ....config import settings


class DomainExtractionGoal(AgentGoal):
    """Specific goal for domain extraction."""
    extraction_request: ExtractionRequest
    target_concept_count: int = 50
    min_confidence: float = 0.7
    include_learning_paths: bool = True


class DomainExtractionPlan(AgentPlan):
    """Plan for extracting domain knowledge."""
    document_processing_steps: List[PlanStep]
    concept_extraction_steps: List[PlanStep]
    relationship_mapping_steps: List[PlanStep]
    knowledge_graph_steps: List[PlanStep]


class DomainExtractionAgent(AutonomousAgent):
    """Agent that extracts domain knowledge from documents."""
    
    def __init__(self):
        super().__init__(
            name="DomainExtractionAgent",
            capabilities={
                AgentCapability.PATTERN_RECOGNITION,
                AgentCapability.KNOWLEDGE_SYNTHESIS,
                AgentCapability.LEARNING,
                AgentCapability.COLLABORATION
            }
        )
        
        # Initialize modules
        self.document_processor = DocumentProcessor()
        self.concept_extractor = ConceptExtractor()
        self.relationship_mapper = RelationshipMapper()
        self.weight_calculator = WeightCalculator()
        self.vector_store = VectorStore()
        self.graph_builder = KnowledgeGraphBuilder()
        
        # Agent state
        self._current_request: Optional[ExtractionRequest] = None
        self._extraction_history: List[Dict[str, Any]] = []
        
    async def initialize(self):
        """Initialize the domain extraction agent."""
        try:
            await super().initialize()
            
            # Initialize sub-modules
            await self.concept_extractor.initialize()
            await self.relationship_mapper.initialize()
            await self.vector_store.initialize()
            
            logger.info("Domain Extraction Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Domain Extraction Agent: {str(e)}")
            raise
            
    async def extract_domain_knowledge(
        self,
        request: ExtractionRequest
    ) -> ExtractionResult:
        """Extract domain knowledge from documents."""
        try:
            logger.info(f"Starting domain extraction for: {request.domain_name}")
            start_time = time.time()
            
            # Update agent state
            self._current_request = request
            self.state = AgentState.ACTIVE
            
            # Create goal
            goal = DomainExtractionGoal(
                description=f"Extract knowledge from {len(request.document_paths)} documents",
                priority=0.9,
                deadline=None,
                extraction_request=request
            )
            
            # Plan extraction
            plan = await self.plan(goal)
            
            # Execute plan
            result = await self.execute(plan)
            
            # Reflect on result
            learning_outcome = await self.reflect(result)
            
            # Store in history
            self._extraction_history.append({
                "request": request.dict(),
                "result": result.dict() if hasattr(result, 'dict') else str(result),
                "learning": learning_outcome,
                "timestamp": datetime.utcnow()
            })
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Ensure result is ExtractionResult
            if isinstance(result, ExtractionResult):
                result.processing_time_seconds = processing_time
                logger.info(f"Domain extraction complete in {processing_time:.2f} seconds")
                return result
            else:
                # Convert to ExtractionResult if needed
                return ExtractionResult(
                    request_id=request.id,
                    success=True,
                    domain_knowledge=result if isinstance(result, DomainKnowledge) else None,
                    processing_time_seconds=processing_time
                )
                
        except Exception as e:
            logger.error(f"Error extracting domain knowledge: {str(e)}")
            self.state = AgentState.ERROR
            
            return ExtractionResult(
                request_id=request.id,
                success=False,
                errors=[str(e)],
                processing_time_seconds=time.time() - start_time if 'start_time' in locals() else 0
            )
            
    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive the extraction environment."""
        observations = {
            "request": self._current_request,
            "available_documents": self._check_document_availability(),
            "vector_store_status": await self._check_vector_store_status(),
            "extraction_capabilities": self._get_extraction_capabilities()
        }
        
        return observations
        
    async def update_beliefs(self, observations: Dict[str, Any]) -> None:
        """Update beliefs based on observations."""
        # Update belief about document availability
        if observations["available_documents"]:
            self.beliefs.add(AgentBelief(
                content={
                    "type": "document_availability",
                    "available": observations["available_documents"]["available"],
                    "total_size": observations["available_documents"]["total_size"]
                },
                confidence=1.0,
                source="file_system"
            ))
            
        # Update belief about extraction capabilities
        self.beliefs.add(AgentBelief(
            content={
                "type": "extraction_capabilities",
                "nlp_available": observations["extraction_capabilities"]["nlp_available"],
                "llm_available": observations["extraction_capabilities"]["llm_available"]
            },
            confidence=0.95,
            source="self_assessment"
        ))
        
    async def deliberate(self) -> AgentGoal:
        """Decide what to extract next."""
        if not self._current_request:
            return None
            
        # Create extraction goal
        goal = DomainExtractionGoal(
            description=f"Extract domain knowledge for {self._current_request.domain_name}",
            priority=0.9,
            extraction_request=self._current_request,
            target_concept_count=50,
            min_confidence=0.7
        )
        
        return goal
        
    async def plan(self, goal: DomainExtractionGoal) -> DomainExtractionPlan:
        """Create plan to achieve extraction goal."""
        logger.info("Planning domain extraction")
        
        # Document processing steps
        doc_steps = [
            PlanStep(
                action="process_documents",
                parameters={
                    "paths": goal.extraction_request.document_paths,
                    "chunk_size": goal.extraction_request.chunk_size,
                    "chunk_overlap": goal.extraction_request.chunk_overlap
                },
                expected_duration=30.0
            )
        ]
        
        # Concept extraction steps
        concept_steps = [
            PlanStep(
                action="extract_concepts",
                parameters={
                    "min_frequency": goal.extraction_request.min_concept_frequency,
                    "use_llm": goal.extraction_request.extraction_config.get("use_llm", True)
                },
                expected_duration=60.0
            ),
            PlanStep(
                action="identify_prerequisites",
                parameters={},
                expected_duration=15.0
            )
        ]
        
        # Relationship mapping steps
        relationship_steps = [
            PlanStep(
                action="map_relationships",
                parameters={
                    "min_strength": goal.extraction_request.min_relationship_strength
                },
                expected_duration=45.0
            ),
            PlanStep(
                action="find_clusters",
                parameters={},
                expected_duration=20.0
            )
        ]
        
        # Knowledge graph steps
        graph_steps = [
            PlanStep(
                action="build_knowledge_graph",
                parameters={},
                expected_duration=30.0
            ),
            PlanStep(
                action="calculate_weights",
                parameters={},
                expected_duration=20.0
            ),
            PlanStep(
                action="store_in_vector_db",
                parameters={
                    "include_embeddings": goal.extraction_request.include_embeddings
                },
                expected_duration=40.0
            )
        ]
        
        # Add learning path generation if requested
        if goal.include_learning_paths:
            graph_steps.append(PlanStep(
                action="generate_learning_paths",
                parameters={},
                expected_duration=30.0
            ))
            
        plan = DomainExtractionPlan(
            goal_id=goal.id,
            steps=doc_steps + concept_steps + relationship_steps + graph_steps,
            estimated_duration=sum(s.expected_duration for s in doc_steps + concept_steps + relationship_steps + graph_steps),
            document_processing_steps=doc_steps,
            concept_extraction_steps=concept_steps,
            relationship_mapping_steps=relationship_steps,
            knowledge_graph_steps=graph_steps
        )
        
        logger.info(f"Created extraction plan with {len(plan.steps)} steps")
        return plan
        
    async def execute(self, plan: DomainExtractionPlan) -> ExtractionResult:
        """Execute the extraction plan."""
        logger.info("Executing domain extraction plan")
        
        try:
            # Initialize result tracking
            documents = []
            chunks = []
            concepts = []
            relationships = []
            domain_knowledge = None
            
            # Execute each step
            for step in plan.steps:
                logger.info(f"Executing step: {step.action}")
                
                if step.action == "process_documents":
                    documents, chunks = await self._process_documents(step.parameters)
                    
                elif step.action == "extract_concepts":
                    concepts = await self._extract_concepts(documents, chunks, step.parameters)
                    
                elif step.action == "identify_prerequisites":
                    await self.concept_extractor.identify_prerequisites(concepts, chunks)
                    
                elif step.action == "map_relationships":
                    relationships = await self._map_relationships(concepts, chunks, step.parameters)
                    
                elif step.action == "find_clusters":
                    clusters = await self.relationship_mapper.create_concept_clusters(concepts, relationships)
                    
                elif step.action == "build_knowledge_graph":
                    domain_knowledge = await self._build_knowledge_graph(
                        concepts, relationships, documents
                    )
                    
                elif step.action == "calculate_weights":
                    weights = await self.weight_calculator.calculate_weights(
                        concepts, relationships, documents, chunks
                    )
                    domain_knowledge.domain_weights = weights
                    
                elif step.action == "store_in_vector_db":
                    await self._store_in_vector_db(chunks, concepts, step.parameters)
                    
                elif step.action == "generate_learning_paths":
                    # Generate learning paths using the graph
                    if domain_knowledge:
                        graph = await self.graph_builder.build_graph(domain_knowledge)
                        # Find paths between fundamental and advanced concepts
                        fundamental_concepts = [c.id for c in concepts if c.importance_score < 0.4][:3]
                        advanced_concepts = [c.id for c in concepts if c.importance_score > 0.7][:3]
                        
                        if fundamental_concepts and advanced_concepts:
                            learning_paths = await self.graph_builder.find_learning_paths(
                                fundamental_concepts,
                                advanced_concepts
                            )
                            
            # Create final result
            result = ExtractionResult(
                request_id=self._current_request.id,
                success=True,
                domain_knowledge=domain_knowledge,
                documents_processed=len(documents),
                chunks_created=len(chunks),
                concepts_extracted=len(concepts),
                relationships_found=len(relationships)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing extraction plan: {str(e)}")
            return ExtractionResult(
                request_id=self._current_request.id,
                success=False,
                errors=[str(e)]
            )
            
    async def reflect(self, result: ExtractionResult) -> Dict[str, Any]:
        """Reflect on extraction result and learn."""
        logger.info("Reflecting on extraction result")
        
        learning_outcome = {
            "success": result.success,
            "concepts_extracted": result.concepts_extracted,
            "relationships_found": result.relationships_found,
            "confidence": result.domain_knowledge.extraction_confidence.overall if result.domain_knowledge else 0,
            "lessons_learned": []
        }
        
        # Analyze extraction quality
        if result.success and result.domain_knowledge:
            # Check concept density
            if result.concepts_extracted < 20:
                learning_outcome["lessons_learned"].append({
                    "aspect": "concept_extraction",
                    "insight": "Low concept count - may need to adjust extraction thresholds",
                    "confidence": 0.8
                })
                
            # Check relationship density
            relationship_ratio = result.relationships_found / result.concepts_extracted if result.concepts_extracted > 0 else 0
            if relationship_ratio < 1.5:
                learning_outcome["lessons_learned"].append({
                    "aspect": "relationship_mapping",
                    "insight": "Low relationship density - consider semantic similarity threshold adjustment",
                    "confidence": 0.7
                })
                
        # Store learning for future use
        self._update_extraction_strategies(learning_outcome)
        
        return learning_outcome
        
    async def collaborate(self, other_agents: List[AutonomousAgent]) -> Dict[str, Any]:
        """Collaborate with other agents."""
        collaboration_result = {
            "agents_involved": [agent.name for agent in other_agents],
            "contributions": {}
        }
        
        for agent in other_agents:
            if agent.name == "PedagogicalReasoningAgent":
                # Get learning objectives for extracted concepts
                objectives = await agent.send_message(
                    "generate_learning_objectives",
                    {"concepts": self._current_request}
                )
                collaboration_result["contributions"]["learning_objectives"] = objectives
                
            elif agent.name == "ContentGenerationAgent":
                # Share extracted knowledge for content generation
                knowledge = await self.get_current_knowledge()
                collaboration_result["contributions"]["shared_knowledge"] = True
                
        return collaboration_result
        
    # Knowledge base operations
    
    async def search_knowledge(self, query: SearchQuery) -> List[SearchResult]:
        """Search the knowledge base."""
        return await self.vector_store.search(query)
        
    async def get_concept_details(self, concept_name: str) -> Optional[Concept]:
        """Get detailed information about a concept."""
        # Search for the concept
        query = SearchQuery(
            query=concept_name,
            max_results=1,
            include_relationships=True
        )
        
        results = await self.search_knowledge(query)
        if results:
            return results[0].concept
            
        return None
        
    async def export_knowledge_graph(self, format: str = "json") -> Any:
        """Export the knowledge graph."""
        if not self.graph_builder.graph:
            return None
            
        return await self.graph_builder.export_graph(format)
        
    # Private helper methods
    
    def _check_document_availability(self) -> Dict[str, Any]:
        """Check if requested documents are available."""
        if not self._current_request:
            return {"available": False, "total_size": 0}
            
        available = []
        total_size = 0
        
        for path in self._current_request.document_paths:
            p = Path(path)
            if p.exists():
                available.append(str(p))
                total_size += p.stat().st_size
                
        return {
            "available": len(available) == len(self._current_request.document_paths),
            "found": available,
            "total_size": total_size
        }
        
    async def _check_vector_store_status(self) -> Dict[str, Any]:
        """Check vector store status."""
        try:
            stats = await self.vector_store.get_stats()
            return {
                "operational": True,
                "total_items": stats.total_chunks + stats.total_concepts
            }
        except:
            return {
                "operational": False,
                "total_items": 0
            }
            
    def _get_extraction_capabilities(self) -> Dict[str, Any]:
        """Get current extraction capabilities."""
        return {
            "nlp_available": self.concept_extractor._nlp is not None,
            "llm_available": True,  # Assuming LLM is always available
            "embedding_available": self.relationship_mapper._sentence_transformer is not None
        }
        
    async def _process_documents(self, parameters: Dict[str, Any]) -> Tuple[List[Document], List[DocumentChunk]]:
        """Process documents into chunks."""
        return await self.document_processor.process_documents(
            parameters["paths"],
            parameters.get("chunk_size"),
            parameters.get("chunk_overlap")
        )
        
    async def _extract_concepts(
        self,
        documents: List[Document],
        chunks: List[DocumentChunk],
        parameters: Dict[str, Any]
    ) -> List[Concept]:
        """Extract concepts from documents."""
        return await self.concept_extractor.extract_concepts(
            documents,
            chunks,
            parameters.get("min_frequency", 2)
        )
        
    async def _map_relationships(
        self,
        concepts: List[Concept],
        chunks: List[DocumentChunk],
        parameters: Dict[str, Any]
    ) -> List[Relationship]:
        """Map relationships between concepts."""
        return await self.relationship_mapper.map_relationships(
            concepts,
            chunks,
            parameters.get("min_strength", 0.3)
        )
        
    async def _build_knowledge_graph(
        self,
        concepts: List[Concept],
        relationships: List[Relationship],
        documents: List[Document]
    ) -> DomainKnowledge:
        """Build complete domain knowledge structure."""
        # Calculate extraction confidence
        confidence = ExtractionConfidence(
            overall=0.8,  # Simplified - would calculate based on various factors
            concept_identification=0.85,
            relationship_mapping=0.75,
            weight_calculation=0.8,
            metadata_extraction=0.9
        )
        
        # Create domain knowledge
        domain_knowledge = DomainKnowledge(
            domain_name=self._current_request.domain_name,
            certification_name=self._current_request.certification_name,
            concepts=concepts,
            relationships=relationships,
            total_concepts=len(concepts),
            total_relationships=len(relationships),
            extraction_confidence=confidence,
            source_documents=[doc.source_path for doc in documents]
        )
        
        # Build graph
        await self.graph_builder.build_graph(domain_knowledge)
        
        # Find central concepts
        central_concepts = await self.graph_builder.identify_central_concepts()
        domain_knowledge.metadata["central_concepts"] = central_concepts
        
        # Find clusters
        clusters = await self.graph_builder.find_concept_clusters()
        domain_knowledge.metadata["concept_clusters"] = len(clusters)
        
        return domain_knowledge
        
    async def _store_in_vector_db(
        self,
        chunks: List[DocumentChunk],
        concepts: List[Concept],
        parameters: Dict[str, Any]
    ) -> None:
        """Store extracted knowledge in vector database."""
        # Store chunks
        if parameters.get("include_embeddings", True):
            await self.vector_store.add_chunks(chunks)
            
        # Store concepts
        await self.vector_store.add_concepts(concepts)
        
    def _update_extraction_strategies(self, learning_outcome: Dict[str, Any]) -> None:
        """Update extraction strategies based on learning."""
        # Store successful strategies
        if learning_outcome["success"]:
            self.memory.add_episodic_memory({
                "type": "successful_extraction",
                "concepts_extracted": learning_outcome["concepts_extracted"],
                "relationships_found": learning_outcome["relationships_found"],
                "confidence": learning_outcome["confidence"]
            })
            
        # Update procedural memory with insights
        for lesson in learning_outcome["lessons_learned"]:
            self.memory.add_procedural_memory({
                "aspect": lesson["aspect"],
                "strategy": lesson["insight"],
                "confidence": lesson["confidence"]
            })
            
    async def get_current_knowledge(self) -> Optional[DomainKnowledge]:
        """Get the currently extracted knowledge."""
        # This would retrieve the most recent extraction result
        # For now, return None
        return None
