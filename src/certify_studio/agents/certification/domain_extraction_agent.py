"""
Domain Extraction Agent - Intelligent parsing and knowledge extraction.

This agent uses AI to understand certification exam guides and extract
structured knowledge that can be animated. It goes beyond simple parsing
to understand relationships, prerequisites, and conceptual hierarchies.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import re
from pathlib import Path
import json

import PyPDF2
from pydantic import BaseModel, Field
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.chat_models.base import BaseChatModel
from langchain.text_splitter import RecursiveCharacterTextSplitter
import networkx as nx

from ...core.logging import get_logger

logger = get_logger(__name__)


class ConceptType(Enum):
    """Types of concepts in technical domains."""
    SERVICE = "service"
    FEATURE = "feature"
    PATTERN = "pattern"
    PRACTICE = "practice"
    PRINCIPLE = "principle"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"


class RelationshipType(Enum):
    """Types of relationships between concepts."""
    DEPENDS_ON = "depends_on"
    ENABLES = "enables"
    CONTAINS = "contains"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    SECURES = "secures"
    OPTIMIZES = "optimizes"
    INTEGRATES_WITH = "integrates_with"


@dataclass
class Concept:
    """A single concept extracted from the domain."""
    id: str
    name: str
    type: ConceptType
    description: str
    importance: float  # 0.0 to 1.0
    complexity: int  # 1 to 10
    prerequisites: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)
    visual_metaphor_suggestions: List[str] = field(default_factory=list)
    animation_hints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConceptRelationship:
    """Relationship between two concepts."""
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    strength: float  # 0.0 to 1.0
    description: str
    bidirectional: bool = False


@dataclass
class LearningDomain:
    """A complete learning domain with concepts and relationships."""
    domain_name: str
    certification_name: str
    exam_code: str
    concepts: Dict[str, Concept]
    relationships: List[ConceptRelationship]
    learning_paths: List[List[str]]  # Ordered sequences of concept IDs
    key_themes: List[str]
    difficulty_distribution: Dict[str, float]
    estimated_learning_hours: float


class DomainExtractionStrategy:
    """Strategy for extracting domains from certification content."""
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " "]
        )
    
    async def extract_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from PDF."""
        text_content = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    text_content.append(text)
                
                logger.info(f"Extracted {len(pdf_reader.pages)} pages from {pdf_path}")
        
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            raise
        
        return "\n\n".join(text_content)
    
    async def identify_concepts(self, text: str, domain: str) -> List[Concept]:
        """Identify concepts from text using pattern matching and AI."""
        
        concepts = []
        
        # Split text into manageable chunks
        chunks = self.text_splitter.split_text(text)
        
        for chunk in chunks:
            # Extract concepts from chunk
            chunk_concepts = await self._extract_concepts_from_chunk(chunk, domain)
            concepts.extend(chunk_concepts)
        
        # Deduplicate and merge similar concepts
        concepts = self._merge_similar_concepts(concepts)
        
        # Enhance concepts with AI if available
        if self.llm:
            concepts = await self._enhance_concepts_with_ai(concepts, domain)
        
        return concepts
    
    async def _extract_concepts_from_chunk(
        self, 
        chunk: str, 
        domain: str
    ) -> List[Concept]:
        """Extract concepts from a text chunk."""
        
        concepts = []
        
        # Pattern matching for common concept indicators
        patterns = {
            ConceptType.SERVICE: [
                r"(?:AWS|Azure|GCP)\s+(\w+(?:\s+\w+)?)",
                r"(\w+)\s+(?:service|platform|solution)",
                r"(?:managed|serverless)\s+(\w+)"
            ],
            ConceptType.FEATURE: [
                r"(?:feature|capability|functionality):\s*(\w+(?:\s+\w+)?)",
                r"(\w+)\s+(?:enables|allows|provides)",
                r"(?:key|main|primary)\s+(?:feature|capability).*?(\w+(?:\s+\w+)?)"
            ],
            ConceptType.PATTERN: [
                r"(\w+(?:\s+\w+)?)\s+pattern",
                r"(?:design|architectural)\s+pattern.*?(\w+(?:\s+\w+)?)",
                r"(?:best|common)\s+practice.*?(\w+(?:\s+\w+)?)"
            ],
            ConceptType.SECURITY: [
                r"(?:security|encryption|authentication|authorization).*?(\w+(?:\s+\w+)?)",
                r"(\w+)\s+(?:security|protection|defense)",
                r"(?:IAM|identity|access).*?(\w+(?:\s+\w+)?)"
            ]
        }
        
        for concept_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.finditer(pattern, chunk, re.IGNORECASE)
                
                for match in matches:
                    concept_name = match.group(1).strip()
                    
                    # Skip common words
                    if concept_name.lower() in ["the", "this", "that", "which", "what"]:
                        continue
                    
                    # Extract context around the match for description
                    start = max(0, match.start() - 100)
                    end = min(len(chunk), match.end() + 100)
                    context = chunk[start:end].strip()
                    
                    # Calculate importance based on frequency and context
                    importance = self._calculate_concept_importance(
                        concept_name, chunk, context
                    )
                    
                    concept = Concept(
                        id=f"{domain}_{concept_name.lower().replace(' ', '_')}",
                        name=concept_name,
                        type=concept_type,
                        description=context,
                        importance=importance,
                        complexity=self._estimate_complexity(concept_name, context),
                        visual_metaphor_suggestions=self._suggest_visual_metaphors(
                            concept_type, concept_name
                        )
                    )
                    
                    concepts.append(concept)
        
        return concepts
    
    def _calculate_concept_importance(
        self, 
        concept_name: str, 
        full_text: str, 
        context: str
    ) -> float:
        """Calculate importance score for a concept."""
        
        # Frequency in text
        frequency = full_text.lower().count(concept_name.lower())
        freq_score = min(frequency / 10, 1.0)
        
        # Importance indicators in context
        importance_indicators = [
            "critical", "essential", "fundamental", "key", "primary",
            "must know", "important", "core", "main", "crucial"
        ]
        
        context_lower = context.lower()
        importance_score = sum(
            0.2 for indicator in importance_indicators 
            if indicator in context_lower
        )
        
        # Combine scores
        total_score = (freq_score * 0.6 + min(importance_score, 1.0) * 0.4)
        
        return round(total_score, 2)
    
    def _estimate_complexity(self, concept_name: str, context: str) -> int:
        """Estimate complexity level of a concept."""
        
        complexity_indicators = {
            "simple": 2,
            "basic": 3,
            "intermediate": 5,
            "advanced": 7,
            "complex": 8,
            "expert": 9,
            "sophisticated": 8,
            "detailed": 6,
            "comprehensive": 7
        }
        
        context_lower = context.lower()
        
        # Check for complexity indicators
        for indicator, score in complexity_indicators.items():
            if indicator in context_lower:
                return score
        
        # Estimate based on concept name length and structure
        words = concept_name.split()
        if len(words) > 3:
            return 6
        elif len(words) > 1:
            return 4
        else:
            return 3
    
    def _suggest_visual_metaphors(
        self, 
        concept_type: ConceptType, 
        concept_name: str
    ) -> List[str]:
        """Suggest visual metaphors for a concept."""
        
        metaphors = []
        
        type_metaphors = {
            ConceptType.SERVICE: ["container", "building", "cloud", "server"],
            ConceptType.FEATURE: ["tool", "gear", "switch", "module"],
            ConceptType.PATTERN: ["blueprint", "template", "flow", "cycle"],
            ConceptType.SECURITY: ["shield", "lock", "wall", "guard"],
            ConceptType.ARCHITECTURE: ["structure", "blueprint", "layers", "network"],
            ConceptType.INTEGRATION: ["bridge", "connector", "puzzle", "link"]
        }
        
        # Add type-specific metaphors
        if concept_type in type_metaphors:
            metaphors.extend(type_metaphors[concept_type])
        
        # Add concept-specific metaphors
        concept_lower = concept_name.lower()
        
        if "flow" in concept_lower or "stream" in concept_lower:
            metaphors.append("river")
        if "storage" in concept_lower or "database" in concept_lower:
            metaphors.append("warehouse")
        if "queue" in concept_lower:
            metaphors.append("line")
        if "stack" in concept_lower:
            metaphors.append("layers")
        if "network" in concept_lower:
            metaphors.append("web")
        
        return list(set(metaphors))  # Remove duplicates
    
    def _merge_similar_concepts(self, concepts: List[Concept]) -> List[Concept]:
        """Merge similar or duplicate concepts."""
        
        merged = {}
        
        for concept in concepts:
            # Check if similar concept already exists
            similar_found = False
            
            for existing_id, existing_concept in merged.items():
                similarity = self._calculate_similarity(concept, existing_concept)
                
                if similarity > 0.8:  # High similarity threshold
                    # Merge into existing concept
                    existing_concept.description += f" {concept.description}"
                    existing_concept.importance = max(
                        existing_concept.importance, 
                        concept.importance
                    )
                    existing_concept.visual_metaphor_suggestions.extend(
                        concept.visual_metaphor_suggestions
                    )
                    similar_found = True
                    break
            
            if not similar_found:
                merged[concept.id] = concept
        
        return list(merged.values())
    
    def _calculate_similarity(self, concept1: Concept, concept2: Concept) -> float:
        """Calculate similarity between two concepts."""
        
        # Name similarity
        name1_lower = concept1.name.lower()
        name2_lower = concept2.name.lower()
        
        if name1_lower == name2_lower:
            return 1.0
        
        # Check if one name contains the other
        if name1_lower in name2_lower or name2_lower in name1_lower:
            return 0.9
        
        # Check word overlap
        words1 = set(name1_lower.split())
        words2 = set(name2_lower.split())
        
        if words1 and words2:
            overlap = len(words1.intersection(words2))
            total = len(words1.union(words2))
            return overlap / total if total > 0 else 0.0
        
        return 0.0
    
    async def _enhance_concepts_with_ai(
        self, 
        concepts: List[Concept], 
        domain: str
    ) -> List[Concept]:
        """Enhance concepts using AI for better understanding."""
        
        # This would use the LLM to enhance concept descriptions,
        # identify prerequisites, and suggest better visual metaphors
        
        # For now, return concepts as-is
        return concepts
    
    async def build_concept_graph(
        self, 
        concepts: List[Concept], 
        text: str
    ) -> Tuple[nx.DiGraph, List[ConceptRelationship]]:
        """Build a knowledge graph from concepts."""
        
        graph = nx.DiGraph()
        relationships = []
        
        # Add nodes
        for concept in concepts:
            graph.add_node(
                concept.id,
                concept=concept,
                importance=concept.importance
            )
        
        # Identify relationships
        for i, concept1 in enumerate(concepts):
            for j, concept2 in enumerate(concepts):
                if i >= j:  # Avoid duplicates and self-relationships
                    continue
                
                relationship = await self._identify_relationship(
                    concept1, concept2, text
                )
                
                if relationship:
                    relationships.append(relationship)
                    graph.add_edge(
                        relationship.source_id,
                        relationship.target_id,
                        relationship=relationship
                    )
        
        return graph, relationships
    
    async def _identify_relationship(
        self,
        concept1: Concept,
        concept2: Concept,
        text: str
    ) -> Optional[ConceptRelationship]:
        """Identify relationship between two concepts."""
        
        # Look for relationship indicators in text
        relationship_patterns = {
            RelationshipType.DEPENDS_ON: [
                r"{0}.*?(?:depends on|requires|needs|relies on).*?{1}",
                r"{1}.*?(?:is required for|is needed for).*?{0}"
            ],
            RelationshipType.ENABLES: [
                r"{0}.*?(?:enables|allows|facilitates|supports).*?{1}",
                r"{1}.*?(?:is enabled by|is supported by).*?{0}"
            ],
            RelationshipType.CONTAINS: [
                r"{0}.*?(?:contains|includes|comprises|has).*?{1}",
                r"{1}.*?(?:is part of|belongs to|is in).*?{0}"
            ],
            RelationshipType.INTEGRATES_WITH: [
                r"{0}.*?(?:integrates with|connects to|works with).*?{1}",
                r"{0}.*?(?:and|with).*?{1}.*?(?:integration|connection)"
            ]
        }
        
        for rel_type, patterns in relationship_patterns.items():
            for pattern in patterns:
                # Format pattern with concept names
                formatted_pattern = pattern.format(
                    re.escape(concept1.name),
                    re.escape(concept2.name)
                )
                
                if re.search(formatted_pattern, text, re.IGNORECASE):
                    return ConceptRelationship(
                        source_id=concept1.id,
                        target_id=concept2.id,
                        relationship_type=rel_type,
                        strength=0.8,
                        description=f"{concept1.name} {rel_type.value} {concept2.name}"
                    )
        
        # Check for implicit relationships based on concept types
        implicit_relationships = self._check_implicit_relationships(concept1, concept2)
        if implicit_relationships:
            return implicit_relationships
        
        return None
    
    def _check_implicit_relationships(
        self,
        concept1: Concept,
        concept2: Concept
    ) -> Optional[ConceptRelationship]:
        """Check for implicit relationships based on concept types."""
        
        # Service-Feature relationship
        if concept1.type == ConceptType.SERVICE and concept2.type == ConceptType.FEATURE:
            if concept2.name.lower() in concept1.description.lower():
                return ConceptRelationship(
                    source_id=concept1.id,
                    target_id=concept2.id,
                    relationship_type=RelationshipType.CONTAINS,
                    strength=0.6,
                    description=f"{concept1.name} contains feature {concept2.name}"
                )
        
        # Security relationships
        if concept1.type == ConceptType.SECURITY:
            if concept2.type in [ConceptType.SERVICE, ConceptType.FEATURE]:
                return ConceptRelationship(
                    source_id=concept1.id,
                    target_id=concept2.id,
                    relationship_type=RelationshipType.SECURES,
                    strength=0.7,
                    description=f"{concept1.name} secures {concept2.name}"
                )
        
        # Architecture-Service relationship
        if concept1.type == ConceptType.ARCHITECTURE and concept2.type == ConceptType.SERVICE:
            return ConceptRelationship(
                source_id=concept1.id,
                target_id=concept2.id,
                relationship_type=RelationshipType.CONTAINS,
                strength=0.7,
                description=f"{concept1.name} includes {concept2.name}"
            )
        
        return None
    
    async def generate_learning_paths(
        self,
        graph: nx.DiGraph,
        concepts: List[Concept]
    ) -> List[List[str]]:
        """Generate optimal learning paths through the concept graph."""
        
        paths = []
        
        # Find concepts with no prerequisites (starting points)
        start_nodes = [
            node for node, in_degree in graph.in_degree()
            if in_degree == 0
        ]
        
        if not start_nodes:
            # If no clear starting points, start with lowest complexity
            start_nodes = sorted(
                concepts,
                key=lambda c: (c.complexity, -c.importance)
            )[:3]
            start_nodes = [c.id for c in start_nodes]
        
        # Generate paths using topological sort variants
        try:
            # Primary path: topological sort
            topo_sort = list(nx.topological_sort(graph))
            paths.append(topo_sort)
            
            # Alternative paths: depth-first from each start node
            for start in start_nodes[:3]:  # Limit to 3 paths
                path = list(nx.dfs_preorder_nodes(graph, start))
                if len(path) > 3:  # Only include substantial paths
                    paths.append(path)
        
        except nx.NetworkXError:
            # Graph has cycles, use approximation
            logger.warning("Concept graph has cycles, using approximation")
            
            # Sort by complexity and importance
            sorted_concepts = sorted(
                concepts,
                key=lambda c: (c.complexity, -c.importance)
            )
            
            # Create a simple linear path
            paths.append([c.id for c in sorted_concepts])
        
        # Deduplicate paths
        unique_paths = []
        for path in paths:
            if path not in unique_paths:
                unique_paths.append(path)
        
        return unique_paths[:5]  # Return top 5 paths


class DomainExtractionAgent:
    """Main agent for extracting learning domains from certification content."""
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.strategy = DomainExtractionStrategy(llm)
        self.supported_formats = [".pdf", ".txt", ".md", ".docx"]
    
    async def extract_domain(
        self,
        file_path: Path,
        certification_name: str,
        exam_code: str
    ) -> LearningDomain:
        """Extract a complete learning domain from certification content."""
        
        logger.info(f"Extracting domain from {file_path}")
        
        # Extract text based on file type
        if file_path.suffix == ".pdf":
            text = await self.strategy.extract_from_pdf(file_path)
        else:
            # For other formats, simple text reading
            text = file_path.read_text(encoding='utf-8')
        
        # Identify domain from content
        domain_name = self._identify_domain_name(text, certification_name)
        
        # Extract concepts
        concepts = await self.strategy.identify_concepts(text, domain_name)
        logger.info(f"Extracted {len(concepts)} concepts")
        
        # Build concept graph
        graph, relationships = await self.strategy.build_concept_graph(concepts, text)
        logger.info(f"Identified {len(relationships)} relationships")
        
        # Generate learning paths
        learning_paths = await self.strategy.generate_learning_paths(graph, concepts)
        logger.info(f"Generated {len(learning_paths)} learning paths")
        
        # Analyze domain characteristics
        key_themes = self._extract_key_themes(concepts, relationships)
        difficulty_distribution = self._analyze_difficulty_distribution(concepts)
        estimated_hours = self._estimate_learning_hours(concepts)
        
        # Create domain object
        domain = LearningDomain(
            domain_name=domain_name,
            certification_name=certification_name,
            exam_code=exam_code,
            concepts={c.id: c for c in concepts},
            relationships=relationships,
            learning_paths=learning_paths,
            key_themes=key_themes,
            difficulty_distribution=difficulty_distribution,
            estimated_learning_hours=estimated_hours
        )
        
        # Enhance with animation hints
        domain = await self._add_animation_hints(domain)
        
        return domain
    
    def _identify_domain_name(self, text: str, certification_name: str) -> str:
        """Identify the primary domain from the text."""
        
        # Look for domain indicators
        domain_keywords = {
            "cloud": ["aws", "azure", "gcp", "cloud", "iaas", "paas", "saas"],
            "security": ["security", "encryption", "authentication", "iam", "firewall"],
            "data": ["data", "database", "analytics", "warehouse", "lake"],
            "networking": ["network", "vpc", "subnet", "routing", "dns"],
            "devops": ["devops", "ci/cd", "pipeline", "deployment", "kubernetes"],
            "ai_ml": ["machine learning", "ai", "neural", "model", "training"]
        }
        
        domain_scores = {}
        text_lower = text.lower()
        
        for domain, keywords in domain_keywords.items():
            score = sum(text_lower.count(keyword) for keyword in keywords)
            domain_scores[domain] = score
        
        # Get highest scoring domain
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 10:  # Threshold for confidence
                return best_domain
        
        # Default based on certification name
        if "aws" in certification_name.lower():
            return "cloud_aws"
        elif "azure" in certification_name.lower():
            return "cloud_azure"
        elif "security" in certification_name.lower():
            return "security"
        else:
            return "technical"
    
    def _extract_key_themes(
        self,
        concepts: List[Concept],
        relationships: List[ConceptRelationship]
    ) -> List[str]:
        """Extract key themes from the domain."""
        
        themes = set()
        
        # Theme extraction from concept types
        type_counts = {}
        for concept in concepts:
            type_counts[concept.type] = type_counts.get(concept.type, 0) + 1
        
        # Add dominant concept types as themes
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        for concept_type, count in sorted_types[:3]:
            if count > 2:  # Minimum threshold
                themes.add(f"{concept_type.value.title()} Focus")
        
        # Extract themes from high-importance concepts
        important_concepts = [c for c in concepts if c.importance > 0.7]
        for concept in important_concepts[:5]:
            # Extract theme from concept name
            words = concept.name.split()
            if len(words) > 1:
                themes.add(words[0])
        
        # Relationship-based themes
        relationship_counts = {}
        for rel in relationships:
            rel_type = rel.relationship_type.value
            relationship_counts[rel_type] = relationship_counts.get(rel_type, 0) + 1
        
        if relationship_counts:
            dominant_rel = max(relationship_counts, key=relationship_counts.get)
            themes.add(f"{dominant_rel.replace('_', ' ').title()} Patterns")
        
        return list(themes)[:5]  # Top 5 themes
    
    def _analyze_difficulty_distribution(self, concepts: List[Concept]) -> Dict[str, float]:
        """Analyze the distribution of concept difficulties."""
        
        distribution = {
            "beginner": 0,
            "intermediate": 0,
            "advanced": 0,
            "expert": 0
        }
        
        for concept in concepts:
            if concept.complexity <= 3:
                distribution["beginner"] += 1
            elif concept.complexity <= 5:
                distribution["intermediate"] += 1
            elif concept.complexity <= 7:
                distribution["advanced"] += 1
            else:
                distribution["expert"] += 1
        
        # Convert to percentages
        total = len(concepts)
        if total > 0:
            for level in distribution:
                distribution[level] = round(distribution[level] / total * 100, 1)
        
        return distribution
    
    def _estimate_learning_hours(self, concepts: List[Concept]) -> float:
        """Estimate total learning hours based on concepts."""
        
        # Base hours per concept by complexity
        hours_per_complexity = {
            1: 0.5, 2: 1.0, 3: 1.5, 4: 2.0, 5: 2.5,
            6: 3.0, 7: 3.5, 8: 4.0, 9: 4.5, 10: 5.0
        }
        
        total_hours = 0
        for concept in concepts:
            complexity = min(concept.complexity, 10)
            base_hours = hours_per_complexity.get(complexity, 3.0)
            
            # Adjust based on importance
            adjusted_hours = base_hours * (0.5 + concept.importance)
            total_hours += adjusted_hours
        
        # Add overhead for integration and practice (20%)
        total_hours *= 1.2
        
        return round(total_hours, 1)
    
    async def _add_animation_hints(self, domain: LearningDomain) -> LearningDomain:
        """Add animation hints to concepts based on their characteristics."""
        
        for concept_id, concept in domain.concepts.items():
            hints = {
                "duration": 3.0 + concept.complexity * 0.5,  # Longer for complex concepts
                "emphasis_level": "high" if concept.importance > 0.7 else "medium",
                "visual_style": self._determine_visual_style(concept),
                "interaction_type": self._determine_interaction_type(concept),
                "narrative_approach": self._determine_narrative_approach(concept)
            }
            
            concept.animation_hints = hints
        
        return domain
    
    def _determine_visual_style(self, concept: Concept) -> str:
        """Determine the visual style for a concept."""
        
        if concept.type == ConceptType.ARCHITECTURE:
            return "blueprint"
        elif concept.type == ConceptType.SECURITY:
            return "protective"
        elif concept.type == ConceptType.PATTERN:
            return "flowing"
        elif concept.complexity > 7:
            return "detailed"
        else:
            return "clean"
    
    def _determine_interaction_type(self, concept: Concept) -> str:
        """Determine the interaction type for a concept."""
        
        if concept.complexity > 6:
            return "exploratory"  # Allow user to explore details
        elif concept.type == ConceptType.PATTERN:
            return "sequential"  # Step through the pattern
        elif len(concept.examples) > 2:
            return "example_driven"  # Show multiple examples
        else:
            return "observational"  # Simple observation
    
    def _determine_narrative_approach(self, concept: Concept) -> str:
        """Determine the narrative approach for a concept."""
        
        if concept.common_mistakes:
            return "problem_solving"  # Address common mistakes
        elif concept.type == ConceptType.PATTERN:
            return "storytelling"  # Tell a story about the pattern
        elif concept.complexity > 7:
            return "progressive_disclosure"  # Reveal complexity gradually
        else:
            return "direct_explanation"  # Simple, direct explanation
    
    async def export_domain(self, domain: LearningDomain, output_path: Path) -> None:
        """Export domain to JSON format."""
        
        domain_dict = {
            "domain_name": domain.domain_name,
            "certification_name": domain.certification_name,
            "exam_code": domain.exam_code,
            "concepts": {
                id: {
                    "name": c.name,
                    "type": c.type.value,
                    "description": c.description,
                    "importance": c.importance,
                    "complexity": c.complexity,
                    "prerequisites": c.prerequisites,
                    "visual_metaphors": c.visual_metaphor_suggestions,
                    "animation_hints": c.animation_hints
                }
                for id, c in domain.concepts.items()
            },
            "relationships": [
                {
                    "source": r.source_id,
                    "target": r.target_id,
                    "type": r.relationship_type.value,
                    "strength": r.strength
                }
                for r in domain.relationships
            ],
            "learning_paths": domain.learning_paths,
            "key_themes": domain.key_themes,
            "difficulty_distribution": domain.difficulty_distribution,
            "estimated_hours": domain.estimated_learning_hours
        }
        
        with open(output_path, 'w') as f:
            json.dump(domain_dict, f, indent=2)
        
        logger.info(f"Domain exported to {output_path}")


# Example usage
if __name__ == "__main__":
    async def test_extraction():
        agent = DomainExtractionAgent()
        
        # Test with a sample file
        test_file = Path("sample_certification.pdf")
        if test_file.exists():
            domain = await agent.extract_domain(
                file_path=test_file,
                certification_name="AWS Solutions Architect",
                exam_code="SAA-C03"
            )
            
            print(f"Extracted domain: {domain.domain_name}")
            print(f"Total concepts: {len(domain.concepts)}")
            print(f"Key themes: {domain.key_themes}")
            print(f"Estimated hours: {domain.estimated_learning_hours}")
            
            # Export to JSON
            await agent.export_domain(domain, Path("extracted_domain.json"))
    
    asyncio.run(test_extraction())
