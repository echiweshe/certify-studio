"""
Relationship Mapper Module for Domain Extraction Agent.

Maps relationships between concepts using co-occurrence analysis, semantic similarity,
and explicit relationship patterns in the documentation.
"""

import asyncio
import re
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict, Counter
import numpy as np
from datetime import datetime
import networkx as nx

from loguru import logger
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from .models import (
    Concept,
    Relationship,
    RelationshipType,
    DocumentChunk,
    ConceptCluster,
    DomainCategory
)
from ....core.llm import MultiModalLLM
from ....config import settings


class RelationshipMapper:
    """Map relationships between extracted concepts."""
    
    def __init__(self):
        self.llm = MultiModalLLM()
        self._sentence_transformer = None
        self._concept_embeddings = {}
        
        # Relationship patterns
        self.relationship_patterns = {
            RelationshipType.DEPENDS_ON: [
                r'{concept1}.*?(?:depends on|requires|needs|relies on).*?{concept2}',
                r'{concept2}.*?(?:is required by|is needed by).*?{concept1}'
            ],
            RelationshipType.PART_OF: [
                r'{concept1}.*?(?:is part of|belongs to|is in|within).*?{concept2}',
                r'{concept2}.*?(?:contains|includes|comprises|has).*?{concept1}'
            ],
            RelationshipType.IMPLEMENTS: [
                r'{concept1}.*?(?:implements|realizes|executes).*?{concept2}',
                r'{concept2}.*?(?:is implemented by|is realized by).*?{concept1}'
            ],
            RelationshipType.EXTENDS: [
                r'{concept1}.*?(?:extends|enhances|builds upon).*?{concept2}',
                r'{concept2}.*?(?:is extended by|is enhanced by).*?{concept1}'
            ],
            RelationshipType.INTEGRATES_WITH: [
                r'{concept1}.*?(?:integrates with|works with|connects to).*?{concept2}',
                r'{concept1}.*?(?:and|with|plus).*?{concept2}.*?(?:together|integration)'
            ],
            RelationshipType.ALTERNATIVE_TO: [
                r'{concept1}.*?(?:instead of|rather than|as alternative to).*?{concept2}',
                r'{concept1}.*?(?:or|versus|vs).*?{concept2}'
            ],
            RelationshipType.SECURED_BY: [
                r'{concept1}.*?(?:secured by|protected by|encrypted by).*?{concept2}',
                r'{concept2}.*?(?:secures|protects|encrypts).*?{concept1}'
            ]
        }
        
        # Relationship keywords for co-occurrence
        self.relationship_keywords = {
            'integration': RelationshipType.INTEGRATES_WITH,
            'dependency': RelationshipType.DEPENDS_ON,
            'component': RelationshipType.PART_OF,
            'implementation': RelationshipType.IMPLEMENTS,
            'extension': RelationshipType.EXTENDS,
            'alternative': RelationshipType.ALTERNATIVE_TO,
            'security': RelationshipType.SECURED_BY,
            'related': RelationshipType.RELATED_TO
        }
        
    async def initialize(self):
        """Initialize sentence transformer for semantic similarity."""
        try:
            self._sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Relationship mapper initialized")
        except Exception as e:
            logger.warning(f"Could not initialize sentence transformer: {str(e)}")
            self._sentence_transformer = None
            
    async def map_relationships(
        self,
        concepts: List[Concept],
        chunks: List[DocumentChunk],
        min_strength: float = 0.3
    ) -> List[Relationship]:
        """Map all relationships between concepts."""
        try:
            logger.info(f"Mapping relationships between {len(concepts)} concepts")
            
            # Generate embeddings for semantic similarity
            await self._generate_concept_embeddings(concepts)
            
            # Extract relationships using multiple methods
            pattern_relationships = await self._extract_pattern_relationships(concepts, chunks)
            cooccurrence_relationships = await self._extract_cooccurrence_relationships(concepts, chunks)
            semantic_relationships = await self._extract_semantic_relationships(concepts)
            llm_relationships = await self._extract_llm_relationships(concepts, chunks)
            
            # Merge and deduplicate relationships
            all_relationships = self._merge_relationships(
                pattern_relationships +
                cooccurrence_relationships +
                semantic_relationships +
                llm_relationships
            )
            
            # Filter by strength
            filtered_relationships = [r for r in all_relationships if r.strength >= min_strength]
            
            # Validate and clean relationships
            final_relationships = self._validate_relationships(filtered_relationships, concepts)
            
            logger.info(f"Mapped {len(final_relationships)} relationships")
            return final_relationships
            
        except Exception as e:
            logger.error(f"Error mapping relationships: {str(e)}")
            raise
            
    async def _generate_concept_embeddings(self, concepts: List[Concept]):
        """Generate embeddings for concepts."""
        if not self._sentence_transformer:
            return
            
        try:
            # Create text representations for concepts
            concept_texts = []
            for concept in concepts:
                # Combine name, description, and examples
                text = f"{concept.name}. {concept.description}"
                if concept.examples:
                    text += " " + " ".join(concept.examples[:2])
                concept_texts.append(text)
                
            # Generate embeddings
            embeddings = self._sentence_transformer.encode(concept_texts)
            
            # Store embeddings
            for concept, embedding in zip(concepts, embeddings):
                self._concept_embeddings[concept.id] = embedding
                
        except Exception as e:
            logger.warning(f"Error generating embeddings: {str(e)}")
            
    async def _extract_pattern_relationships(
        self,
        concepts: List[Concept],
        chunks: List[DocumentChunk]
    ) -> List[Relationship]:
        """Extract relationships using pattern matching."""
        relationships = []
        concept_lookup = {c.name.lower(): c for c in concepts}
        
        for chunk in chunks:
            content_lower = chunk.content.lower()
            
            # Check each pair of concepts in the chunk
            chunk_concepts = [c for c in concepts if c.name.lower() in content_lower]
            
            for i, concept1 in enumerate(chunk_concepts):
                for concept2 in chunk_concepts[i+1:]:
                    # Try each relationship pattern
                    for rel_type, patterns in self.relationship_patterns.items():
                        for pattern_template in patterns:
                            # Create pattern with actual concept names
                            pattern = pattern_template.format(
                                concept1=re.escape(concept1.name.lower()),
                                concept2=re.escape(concept2.name.lower())
                            )
                            
                            if re.search(pattern, content_lower, re.IGNORECASE):
                                relationship = Relationship(
                                    source_concept_id=concept1.id,
                                    target_concept_id=concept2.id,
                                    type=rel_type,
                                    strength=0.8,  # High confidence for pattern match
                                    evidence=[chunk.id]
                                )
                                relationships.append(relationship)
                                break
                                
        return relationships
        
    async def _extract_cooccurrence_relationships(
        self,
        concepts: List[Concept],
        chunks: List[DocumentChunk]
    ) -> List[Relationship]:
        """Extract relationships based on co-occurrence."""
        relationships = []
        cooccurrence_matrix = defaultdict(lambda: defaultdict(int))
        
        # Build co-occurrence matrix
        for chunk in chunks:
            content_lower = chunk.content.lower()
            
            # Find concepts in this chunk
            chunk_concepts = []
            for concept in concepts:
                if concept.name.lower() in content_lower:
                    chunk_concepts.append(concept)
                    
            # Count co-occurrences
            for i, concept1 in enumerate(chunk_concepts):
                for concept2 in chunk_concepts[i+1:]:
                    cooccurrence_matrix[concept1.id][concept2.id] += 1
                    cooccurrence_matrix[concept2.id][concept1.id] += 1
                    
        # Convert co-occurrences to relationships
        total_chunks = len(chunks)
        for concept1_id, related in cooccurrence_matrix.items():
            for concept2_id, count in related.items():
                if count >= 2:  # Minimum co-occurrence threshold
                    # Calculate strength based on frequency
                    strength = min(count / (total_chunks * 0.1), 1.0)
                    
                    if strength >= 0.3:
                        relationship = Relationship(
                            source_concept_id=concept1_id,
                            target_concept_id=concept2_id,
                            type=RelationshipType.RELATED_TO,
                            strength=strength,
                            evidence=[],  # No specific chunks, based on overall co-occurrence
                            metadata={'co_occurrence_count': count}
                        )
                        relationships.append(relationship)
                        
        return relationships
        
    async def _extract_semantic_relationships(
        self,
        concepts: List[Concept],
        similarity_threshold: float = 0.7
    ) -> List[Relationship]:
        """Extract relationships based on semantic similarity."""
        relationships = []
        
        if not self._concept_embeddings:
            return relationships
            
        # Calculate pairwise similarities
        concept_ids = list(self._concept_embeddings.keys())
        embeddings = np.array([self._concept_embeddings[cid] for cid in concept_ids])
        
        if len(embeddings) > 1:
            similarities = cosine_similarity(embeddings)
            
            # Extract relationships from high similarities
            for i, concept1_id in enumerate(concept_ids):
                for j, concept2_id in enumerate(concept_ids[i+1:], i+1):
                    similarity = similarities[i, j]
                    
                    if similarity >= similarity_threshold:
                        relationship = Relationship(
                            source_concept_id=concept1_id,
                            target_concept_id=concept2_id,
                            type=RelationshipType.RELATED_TO,
                            strength=float(similarity),
                            evidence=[],
                            metadata={'similarity_score': float(similarity)}
                        )
                        relationships.append(relationship)
                        
        return relationships
        
    async def _extract_llm_relationships(
        self,
        concepts: List[Concept],
        chunks: List[DocumentChunk],
        sample_size: int = 5
    ) -> List[Relationship]:
        """Extract relationships using LLM analysis."""
        relationships = []
        
        # Sample concept pairs to analyze
        concept_pairs = []
        for i, concept1 in enumerate(concepts[:sample_size]):
            for concept2 in concepts[i+1:i+1+sample_size]:
                concept_pairs.append((concept1, concept2))
                
        for concept1, concept2 in concept_pairs[:10]:  # Limit to 10 pairs
            # Find chunks mentioning both concepts
            relevant_chunks = []
            for chunk in chunks:
                content_lower = chunk.content.lower()
                if concept1.name.lower() in content_lower and concept2.name.lower() in content_lower:
                    relevant_chunks.append(chunk.content[:500])
                    
            if not relevant_chunks:
                continue
                
            context = "\n".join(relevant_chunks[:3])
            
            prompt = f"""
            Analyze the relationship between "{concept1.name}" and "{concept2.name}" based on this context:
            
            {context}
            
            What type of relationship exists? Choose from:
            - depends_on: one requires the other
            - part_of: one is a component of the other
            - implements: one implements the other
            - integrates_with: they work together
            - alternative_to: they are alternatives
            - related_to: they are related but relationship is unclear
            - none: no clear relationship
            
            Response format:
            Type: <relationship_type>
            Strength: <0.0-1.0>
            Explanation: <brief explanation>
            """
            
            try:
                response = await self.llm.generate(prompt)
                parsed = self._parse_llm_relationship(response)
                
                if parsed and parsed['type'] != 'none':
                    relationship = Relationship(
                        source_concept_id=concept1.id,
                        target_concept_id=concept2.id,
                        type=RelationshipType(parsed['type']),
                        strength=parsed['strength'],
                        evidence=[],
                        metadata={'explanation': parsed.get('explanation', '')}
                    )
                    relationships.append(relationship)
                    
            except Exception as e:
                logger.warning(f"Error in LLM relationship extraction: {str(e)}")
                continue
                
        return relationships
        
    def _parse_llm_relationship(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response for relationship information."""
        try:
            lines = response.strip().split('\n')
            result = {}
            
            for line in lines:
                if line.startswith('Type:'):
                    rel_type = line.replace('Type:', '').strip().lower()
                    result['type'] = rel_type
                elif line.startswith('Strength:'):
                    strength_str = line.replace('Strength:', '').strip()
                    try:
                        result['strength'] = float(strength_str)
                    except:
                        result['strength'] = 0.5
                elif line.startswith('Explanation:'):
                    result['explanation'] = line.replace('Explanation:', '').strip()
                    
            return result if 'type' in result else None
            
        except:
            return None
            
    def _merge_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """Merge duplicate relationships."""
        merged = {}
        
        for rel in relationships:
            # Create key for relationship
            key = (rel.source_concept_id, rel.target_concept_id, rel.type)
            
            if key in merged:
                # Merge with existing
                existing = merged[key]
                
                # Update strength (take maximum)
                existing.strength = max(existing.strength, rel.strength)
                
                # Merge evidence
                existing.evidence.extend(rel.evidence)
                existing.evidence = list(set(existing.evidence))
                
                # Merge metadata
                if rel.metadata:
                    existing.metadata.update(rel.metadata)
                    
            else:
                merged[key] = rel
                
        return list(merged.values())
        
    def _validate_relationships(
        self,
        relationships: List[Relationship],
        concepts: List[Concept]
    ) -> List[Relationship]:
        """Validate and clean relationships."""
        valid_relationships = []
        concept_ids = {c.id for c in concepts}
        
        for rel in relationships:
            # Check that both concepts exist
            if rel.source_concept_id in concept_ids and rel.target_concept_id in concept_ids:
                # Check for self-relationships
                if rel.source_concept_id != rel.target_concept_id:
                    valid_relationships.append(rel)
                    
        return valid_relationships
        
    async def create_concept_clusters(
        self,
        concepts: List[Concept],
        relationships: List[Relationship]
    ) -> List[ConceptCluster]:
        """Create clusters of related concepts."""
        try:
            # Build graph
            G = nx.Graph()
            
            # Add nodes
            for concept in concepts:
                G.add_node(concept.id, concept=concept)
                
            # Add edges
            for rel in relationships:
                G.add_edge(
                    rel.source_concept_id,
                    rel.target_concept_id,
                    weight=rel.strength
                )
                
            # Find communities
            communities = nx.community.louvain_communities(G)
            
            # Create clusters
            clusters = []
            for community in communities:
                if len(community) < 2:
                    continue
                    
                # Get concepts in this cluster
                cluster_concepts = [c for c in concepts if c.id in community]
                
                # Find most central concept
                subgraph = G.subgraph(community)
                centrality = nx.degree_centrality(subgraph)
                centroid_id = max(centrality.items(), key=lambda x: x[1])[0]
                
                # Determine cluster category
                categories = Counter(c.category for c in cluster_concepts)
                main_category = categories.most_common(1)[0][0]
                
                # Calculate cohesion
                if len(community) > 1:
                    density = nx.density(subgraph)
                else:
                    density = 1.0
                    
                # Create cluster
                cluster = ConceptCluster(
                    name=f"{main_category.value} Cluster",
                    category=main_category,
                    concepts=list(community),
                    centroid_concept=centroid_id,
                    cohesion_score=density,
                    description=f"Cluster of {len(community)} related concepts"
                )
                clusters.append(cluster)
                
            return clusters
            
        except Exception as e:
            logger.error(f"Error creating concept clusters: {str(e)}")
            return []
