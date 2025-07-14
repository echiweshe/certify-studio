"""
Knowledge Graph Component - The Brain of Educational Intelligence
Part of the AI Agent Orchestration Platform for Educational Excellence

This is the persistent memory and pattern learning system that makes
the platform smarter with every interaction.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
import numpy as np
from collections import defaultdict

from neo4j import AsyncGraphDatabase
from sklearn.metrics.pairwise import cosine_similarity

from ..core.logging import get_logger
from ..core.config import settings

logger = get_logger(__name__)


class ConceptType(Enum):
    """Types of concepts in our knowledge graph."""
    FUNDAMENTAL = "fundamental"
    DERIVED = "derived"
    APPLIED = "applied"
    ABSTRACT = "abstract"
    CONCRETE = "concrete"
    PROCEDURAL = "procedural"
    METACOGNITIVE = "metacognitive"


class RelationType(Enum):
    """Types of relationships between concepts."""
    PREREQUISITE = "prerequisite_for"
    COMPONENT_OF = "component_of"
    SIMILAR_TO = "similar_to"
    CONTRASTS_WITH = "contrasts_with"
    APPLIED_IN = "applied_in"
    LEADS_TO = "leads_to"
    EXPLAINS = "explains"
    EXEMPLIFIES = "exemplifies"
    GENERALIZES = "generalizes"
    SPECIALIZES = "specializes"


@dataclass
class Concept:
    """A concept in the knowledge graph."""
    id: str
    name: str
    type: ConceptType
    description: str
    cognitive_level: str  # Bloom's taxonomy
    difficulty: float  # 0-1
    prerequisites: List[str] = field(default_factory=list)
    learning_time_minutes: int = 30
    mastery_criteria: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    effectiveness_score: float = 0.8


@dataclass
class Relationship:
    """A relationship between concepts."""
    source: str
    target: str
    type: RelationType
    strength: float = 1.0  # 0-1
    evidence_count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class LearningPattern:
    """A pattern of effective learning discovered by the system."""
    id: str
    pattern_type: str  # "sequence", "cluster", "hierarchy", etc.
    concepts: List[str]
    effectiveness: float
    context: Dict[str, Any]
    discovered_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    refinements: List[Dict[str, Any]] = field(default_factory=list)


class KnowledgeGraph:
    """
    The intelligent knowledge graph that learns and improves.
    
    This isn't just a database - it's an active learning system that:
    - Discovers patterns in how concepts are best taught
    - Tracks effectiveness of different learning paths
    - Adapts based on learner outcomes
    - Suggests optimal concept sequencing
    """
    
    def __init__(self, neo4j_uri: Optional[str] = None):
        """
        Initialize the knowledge graph.
        
        Args:
            neo4j_uri: Neo4j connection URI, defaults to config
        """
        self.neo4j_uri = neo4j_uri or settings.NEO4J_URI
        self.driver = None
        
        # In-memory graph for fast operations
        self.graph = nx.DiGraph()
        
        # Concept and pattern caches
        self.concepts: Dict[str, Concept] = {}
        self.patterns: Dict[str, LearningPattern] = {}
        
        # Learning metrics
        self.concept_effectiveness: Dict[str, List[float]] = defaultdict(list)
        self.path_effectiveness: Dict[Tuple[str, ...], float] = {}
        
        # Pattern discovery thresholds
        self.min_pattern_support = 0.1
        self.min_pattern_confidence = 0.7
        
        logger.info("KnowledgeGraph initialized")
    
    async def connect(self):
        """Connect to Neo4j database."""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            await self.driver.verify_connectivity()
            logger.info("Connected to Neo4j")
            
            # Load graph into memory
            await self._load_graph_from_db()
            
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}. Using in-memory graph only.")
            self.driver = None
    
    async def disconnect(self):
        """Disconnect from Neo4j."""
        if self.driver:
            await self.driver.close()
    
    async def add_concept(self, concept: Concept) -> str:
        """
        Add a concept to the knowledge graph.
        
        Args:
            concept: The concept to add
            
        Returns:
            The concept ID
        """
        # Add to in-memory structures
        self.concepts[concept.id] = concept
        self.graph.add_node(concept.id, **concept.__dict__)
        
        # Add to Neo4j if connected
        if self.driver:
            async with self.driver.session() as session:
                await session.execute_write(
                    self._create_concept_tx,
                    concept
                )
        
        # Update prerequisites relationships
        for prereq in concept.prerequisites:
            await self.add_relationship(
                Relationship(
                    source=prereq,
                    target=concept.id,
                    type=RelationType.PREREQUISITE
                )
            )
        
        logger.info(f"Added concept: {concept.name}")
        return concept.id
    
    async def add_relationship(self, relationship: Relationship):
        """Add a relationship between concepts."""
        # Add to in-memory graph
        self.graph.add_edge(
            relationship.source,
            relationship.target,
            type=relationship.type,
            **relationship.__dict__
        )
        
        # Add to Neo4j if connected
        if self.driver:
            async with self.driver.session() as session:
                await session.execute_write(
                    self._create_relationship_tx,
                    relationship
                )
    
    async def find_learning_path(self,
                               start_concepts: List[str],
                               target_concept: str,
                               learner_profile: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Find the optimal learning path to a target concept.
        
        This uses intelligence about:
        - Prerequisite relationships
        - Cognitive load management
        - Learner preferences
        - Historical effectiveness
        
        Args:
            start_concepts: Concepts the learner already knows
            target_concept: The concept to learn
            learner_profile: Optional learner characteristics
            
        Returns:
            Ordered list of concept IDs to learn
        """
        if target_concept not in self.concepts:
            logger.warning(f"Target concept {target_concept} not found")
            return []
        
        # Find all paths from start concepts to target
        all_paths = []
        for start in start_concepts:
            if start in self.graph:
                try:
                    paths = nx.all_simple_paths(
                        self.graph,
                        start,
                        target_concept,
                        cutoff=10
                    )
                    all_paths.extend(list(paths))
                except nx.NetworkXNoPath:
                    continue
        
        if not all_paths:
            # No direct path, find prerequisites
            return await self._find_prerequisite_path(target_concept, start_concepts)
        
        # Score paths based on effectiveness
        best_path = None
        best_score = -1
        
        for path in all_paths:
            score = await self._score_learning_path(path, learner_profile)
            if score > best_score:
                best_score = score
                best_path = path
        
        return best_path if best_path else []
    
    async def _find_prerequisite_path(self,
                                    target: str,
                                    known: List[str]) -> List[str]:
        """Find prerequisite path when no direct path exists."""
        path = []
        to_learn = {target}
        learned = set(known)
        
        while to_learn:
            # Find concept with all prerequisites met
            for concept_id in to_learn:
                concept = self.concepts.get(concept_id)
                if not concept:
                    continue
                
                if all(p in learned for p in concept.prerequisites):
                    path.append(concept_id)
                    learned.add(concept_id)
                    to_learn.remove(concept_id)
                    break
            else:
                # Add missing prerequisites
                for concept_id in list(to_learn):
                    concept = self.concepts.get(concept_id)
                    if concept:
                        for prereq in concept.prerequisites:
                            if prereq not in learned and prereq not in to_learn:
                                to_learn.add(prereq)
        
        return path
    
    async def _score_learning_path(self,
                                 path: List[str],
                                 learner_profile: Optional[Dict[str, Any]]) -> float:
        """Score a learning path based on multiple factors."""
        if len(path) < 2:
            return 0.0
        
        factors = []
        
        # Historical effectiveness
        path_key = tuple(path)
        if path_key in self.path_effectiveness:
            factors.append(self.path_effectiveness[path_key])
        
        # Cognitive load progression
        difficulties = [self.concepts[c].difficulty for c in path if c in self.concepts]
        if difficulties:
            # Prefer gradual increase in difficulty
            diff_changes = np.diff(difficulties)
            smooth_progression = 1.0 - np.std(diff_changes)
            factors.append(smooth_progression)
        
        # Concept relationships strength
        edge_strengths = []
        for i in range(len(path) - 1):
            if self.graph.has_edge(path[i], path[i+1]):
                edge_data = self.graph[path[i]][path[i+1]]
                edge_strengths.append(edge_data.get('strength', 0.5))
        
        if edge_strengths:
            factors.append(np.mean(edge_strengths))
        
        # Learner profile alignment
        if learner_profile:
            # Match cognitive levels
            learner_level = learner_profile.get('cognitive_level', 'understand')
            level_matches = sum(
                1 for c in path
                if c in self.concepts and 
                self.concepts[c].cognitive_level == learner_level
            )
            factors.append(level_matches / len(path))
        
        return np.mean(factors) if factors else 0.5
    
    async def suggest_next_concepts(self,
                                  learned_concepts: List[str],
                                  n_suggestions: int = 5) -> List[Tuple[str, float]]:
        """
        Suggest next concepts to learn based on what's already learned.
        
        Args:
            learned_concepts: Concepts already mastered
            n_suggestions: Number of suggestions to return
            
        Returns:
            List of (concept_id, relevance_score) tuples
        """
        learned_set = set(learned_concepts)
        suggestions = []
        
        # Find concepts where prerequisites are met
        for concept_id, concept in self.concepts.items():
            if concept_id in learned_set:
                continue
            
            # Check if prerequisites are met
            if all(p in learned_set for p in concept.prerequisites):
                # Calculate relevance score
                score = await self._calculate_concept_relevance(
                    concept_id,
                    learned_concepts
                )
                suggestions.append((concept_id, score))
        
        # Sort by score and return top N
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:n_suggestions]
    
    async def _calculate_concept_relevance(self,
                                         concept_id: str,
                                         learned_concepts: List[str]) -> float:
        """Calculate how relevant a concept is given learned concepts."""
        concept = self.concepts.get(concept_id)
        if not concept:
            return 0.0
        
        factors = []
        
        # Direct connections to learned concepts
        connection_count = sum(
            1 for learned in learned_concepts
            if self.graph.has_edge(learned, concept_id) or
               self.graph.has_edge(concept_id, learned)
        )
        factors.append(connection_count / max(len(learned_concepts), 1))
        
        # Conceptual similarity (if embeddings available)
        if concept.embedding is not None:
            similarities = []
            for learned_id in learned_concepts:
                learned_concept = self.concepts.get(learned_id)
                if learned_concept and learned_concept.embedding is not None:
                    sim = cosine_similarity(
                        concept.embedding.reshape(1, -1),
                        learned_concept.embedding.reshape(1, -1)
                    )[0, 0]
                    similarities.append(sim)
            
            if similarities:
                factors.append(np.mean(similarities))
        
        # Effectiveness score
        factors.append(concept.effectiveness_score)
        
        # Difficulty appropriateness
        learned_difficulties = [
            self.concepts[c].difficulty 
            for c in learned_concepts 
            if c in self.concepts
        ]
        if learned_difficulties:
            avg_learned = np.mean(learned_difficulties)
            difficulty_match = 1.0 - abs(concept.difficulty - (avg_learned + 0.1))
            factors.append(max(0, difficulty_match))
        
        return np.mean(factors) if factors else 0.5
    
    async def record_learning_outcome(self,
                                    concept_id: str,
                                    success: bool,
                                    time_taken_minutes: float,
                                    learner_profile: Optional[Dict[str, Any]] = None):
        """
        Record the outcome of a learning attempt.
        
        This is how the graph learns and improves over time.
        
        Args:
            concept_id: The concept that was learned
            success: Whether learning was successful
            time_taken_minutes: Time taken to learn
            learner_profile: Optional learner characteristics
        """
        if concept_id not in self.concepts:
            return
        
        concept = self.concepts[concept_id]
        
        # Update concept effectiveness
        effectiveness = 1.0 if success else 0.0
        if time_taken_minutes < concept.learning_time_minutes * 0.8:
            effectiveness *= 1.1  # Bonus for fast learning
        elif time_taken_minutes > concept.learning_time_minutes * 1.5:
            effectiveness *= 0.9  # Penalty for slow learning
        
        self.concept_effectiveness[concept_id].append(effectiveness)
        
        # Update rolling effectiveness score
        recent_scores = self.concept_effectiveness[concept_id][-20:]
        concept.effectiveness_score = np.mean(recent_scores)
        
        # Update usage count
        concept.usage_count += 1
        concept.updated_at = datetime.now()
        
        # Learn patterns if enough data
        if len(self.concept_effectiveness[concept_id]) >= 10:
            await self._discover_learning_patterns(concept_id)
    
    async def _discover_learning_patterns(self, concept_id: str):
        """Discover patterns in how concepts are learned effectively."""
        # This is where the magic happens - pattern mining
        # Simplified version, in production would use more sophisticated mining
        
        concept = self.concepts[concept_id]
        
        # Find successful learning sequences ending with this concept
        successful_paths = []
        
        # Look for patterns in prerequisites
        if concept.prerequisites:
            pattern = LearningPattern(
                id=f"prereq_pattern_{concept_id}",
                pattern_type="prerequisite_sequence",
                concepts=concept.prerequisites + [concept_id],
                effectiveness=concept.effectiveness_score,
                context={"target_concept": concept_id}
            )
            
            self.patterns[pattern.id] = pattern
            logger.info(f"Discovered prerequisite pattern for {concept.name}")
    
    async def get_prerequisites(self, concept_id: str) -> List[str]:
        """Get all prerequisites for a concept."""
        if concept_id not in self.concepts:
            return []
        
        # Direct prerequisites
        direct = self.concepts[concept_id].prerequisites
        
        # Transitive prerequisites
        all_prereqs = set(direct)
        to_check = list(direct)
        
        while to_check:
            current = to_check.pop()
            if current in self.concepts:
                for prereq in self.concepts[current].prerequisites:
                    if prereq not in all_prereqs:
                        all_prereqs.add(prereq)
                        to_check.append(prereq)
        
        return list(all_prereqs)
    
    async def find_related_concepts(self,
                                  concept_id: str,
                                  max_distance: int = 2,
                                  limit: int = 10) -> List[str]:
        """Find concepts related to a given concept."""
        if concept_id not in self.graph:
            return []
        
        related = []
        distances = nx.single_source_shortest_path_length(
            self.graph.to_undirected(),
            concept_id,
            cutoff=max_distance
        )
        
        for node, distance in distances.items():
            if node != concept_id and distance <= max_distance:
                related.append((node, distance))
        
        # Sort by distance, then by effectiveness
        related.sort(key=lambda x: (x[1], -self.concepts.get(x[0], Concept("", "", ConceptType.ABSTRACT, "", "", 0)).effectiveness_score))
        
        return [r[0] for r in related[:limit]]
    
    async def validate_concept(self, concept_name: str) -> bool:
        """Validate if a concept exists in the graph."""
        # Check by name (case-insensitive)
        concept_name_lower = concept_name.lower()
        for concept in self.concepts.values():
            if concept.name.lower() == concept_name_lower:
                return True
        return False
    
    async def optimize_graph(self):
        """
        Optimize the knowledge graph based on learned patterns.
        
        This includes:
        - Adjusting relationship strengths
        - Identifying ineffective paths
        - Suggesting new relationships
        """
        logger.info("Optimizing knowledge graph...")
        
        # Update relationship strengths based on usage patterns
        for u, v, data in self.graph.edges(data=True):
            if 'usage_count' in data:
                # Increase strength for frequently used relationships
                data['strength'] = min(1.0, data['strength'] + 0.01 * data['usage_count'])
        
        # Identify weak paths
        weak_paths = []
        for path_key, effectiveness in self.path_effectiveness.items():
            if effectiveness < 0.5:
                weak_paths.append(path_key)
        
        # Suggest alternative relationships
        for path in weak_paths:
            if len(path) > 2:
                # Suggest direct relationship between start and end
                start, end = path[0], path[-1]
                if not self.graph.has_edge(start, end):
                    logger.info(f"Suggesting new relationship: {start} -> {end}")
    
    # Neo4j transaction functions
    async def _create_concept_tx(self, tx, concept: Concept):
        """Transaction to create a concept in Neo4j."""
        query = """
        MERGE (c:Concept {id: $id})
        SET c.name = $name,
            c.type = $type,
            c.description = $description,
            c.cognitive_level = $cognitive_level,
            c.difficulty = $difficulty,
            c.learning_time_minutes = $learning_time_minutes,
            c.effectiveness_score = $effectiveness_score,
            c.usage_count = $usage_count,
            c.created_at = $created_at,
            c.updated_at = $updated_at
        """
        
        await tx.run(query, **{
            'id': concept.id,
            'name': concept.name,
            'type': concept.type.value,
            'description': concept.description,
            'cognitive_level': concept.cognitive_level,
            'difficulty': concept.difficulty,
            'learning_time_minutes': concept.learning_time_minutes,
            'effectiveness_score': concept.effectiveness_score,
            'usage_count': concept.usage_count,
            'created_at': concept.created_at.isoformat(),
            'updated_at': concept.updated_at.isoformat()
        })
    
    async def _create_relationship_tx(self, tx, relationship: Relationship):
        """Transaction to create a relationship in Neo4j."""
        query = f"""
        MATCH (a:Concept {{id: $source}})
        MATCH (b:Concept {{id: $target}})
        MERGE (a)-[r:{relationship.type.value}]->(b)
        SET r.strength = $strength,
            r.evidence_count = $evidence_count,
            r.created_at = $created_at
        """
        
        await tx.run(query, **{
            'source': relationship.source,
            'target': relationship.target,
            'strength': relationship.strength,
            'evidence_count': relationship.evidence_count,
            'created_at': relationship.created_at.isoformat()
        })
    
    async def _load_graph_from_db(self):
        """Load graph from Neo4j into memory."""
        if not self.driver:
            return
        
        async with self.driver.session() as session:
            # Load concepts
            concepts_result = await session.run(
                "MATCH (c:Concept) RETURN c"
            )
            
            async for record in concepts_result:
                node = record['c']
                concept = Concept(
                    id=node['id'],
                    name=node['name'],
                    type=ConceptType(node['type']),
                    description=node['description'],
                    cognitive_level=node['cognitive_level'],
                    difficulty=node['difficulty'],
                    learning_time_minutes=node.get('learning_time_minutes', 30),
                    effectiveness_score=node.get('effectiveness_score', 0.8),
                    usage_count=node.get('usage_count', 0)
                )
                self.concepts[concept.id] = concept
                self.graph.add_node(concept.id, **concept.__dict__)
            
            # Load relationships
            relationships_result = await session.run(
                "MATCH (a)-[r]->(b) RETURN a.id as source, b.id as target, type(r) as type, r"
            )
            
            async for record in relationships_result:
                self.graph.add_edge(
                    record['source'],
                    record['target'],
                    type=record['type'],
                    strength=record['r'].get('strength', 1.0)
                )
        
        logger.info(f"Loaded {len(self.concepts)} concepts and {self.graph.number_of_edges()} relationships")
    
    # Pattern storage methods
    async def add_visual_pattern(self, pattern_type: str, data: Dict[str, Any]):
        """Store a visual learning pattern."""
        pattern_id = f"visual_{pattern_type}_{datetime.now().timestamp()}"
        pattern = LearningPattern(
            id=pattern_id,
            pattern_type=f"visual_{pattern_type}",
            concepts=data.get('concepts', []),
            effectiveness=data.get('educational_value', 0.8),
            context=data
        )
        self.patterns[pattern_id] = pattern
        logger.info(f"Stored visual pattern: {pattern_id}")
    
    async def add_audio_pattern(self, pattern_type: str, data: Dict[str, Any]):
        """Store an audio learning pattern."""
        pattern_id = f"audio_{pattern_type}_{datetime.now().timestamp()}"
        pattern = LearningPattern(
            id=pattern_id,
            pattern_type=f"audio_{pattern_type}",
            concepts=data.get('key_concepts', []),
            effectiveness=data.get('educational_value', 0.8),
            context=data
        )
        self.patterns[pattern_id] = pattern
        logger.info(f"Stored audio pattern: {pattern_id}")
