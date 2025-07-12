"""
Enhanced Domain Extraction Agent with multimodal LLM capabilities.
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import asyncio
import json

from ...core.llm import MultimodalLLM, LLMProvider, PromptManager, PromptType
from ...core.llm.multimodal_llm import MultimodalMessage, MultimodalResponse
from ...core.logging import get_logger
from .domain_extraction_agent import (
    DomainExtractionAgent as BaseDomainExtractionAgent,
    Concept, ConceptType, LearningDomain, ConceptRelationship
)

logger = get_logger(__name__)


class MultimodalDomainExtractionAgent(BaseDomainExtractionAgent):
    """Enhanced domain extraction with multimodal LLM capabilities."""
    
    def __init__(
        self,
        llm: Optional[MultimodalLLM] = None,
        use_vision: bool = True
    ):
        # Initialize base agent
        super().__init__(llm=None)  # We'll use our multimodal LLM
        
        # Initialize multimodal LLM
        self.llm = llm or MultimodalLLM(
            provider=LLMProvider.ANTHROPIC_CLAUDE_VISION,
            temperature=0.3  # Lower temperature for more consistent extraction
        )
        
        self.use_vision = use_vision
        self.prompt_manager = PromptManager()
    
    async def extract_domain(
        self,
        file_path: Path,
        certification_name: str,
        exam_code: str
    ) -> LearningDomain:
        """Extract domain with multimodal understanding."""
        
        logger.info(f"Extracting domain from {file_path} with multimodal LLM")
        
        # Extract text and images from PDF
        text_content, images = await self._extract_multimodal_content(file_path)
        
        # Use LLM to extract concepts with visual understanding
        concepts = await self._extract_concepts_multimodal(
            text_content, images, certification_name
        )
        
        # Build knowledge graph with LLM assistance
        graph, relationships = await self._build_knowledge_graph_llm(
            concepts, text_content
        )
        
        # Generate learning paths with LLM optimization
        learning_paths = await self._generate_learning_paths_llm(
            concepts, relationships
        )
        
        # Extract additional insights with LLM
        insights = await self._extract_domain_insights(
            concepts, relationships, text_content, images
        )
        
        # Create enhanced domain
        domain = LearningDomain(
            domain_name=insights.get("domain_name", self._identify_domain_name(text_content, certification_name)),
            certification_name=certification_name,
            exam_code=exam_code,
            concepts={c.id: c for c in concepts},
            relationships=relationships,
            learning_paths=learning_paths,
            key_themes=insights.get("key_themes", []),
            difficulty_distribution=insights.get("difficulty_distribution", {}),
            estimated_learning_hours=insights.get("estimated_hours", 40.0)
        )
        
        return domain
    
    async def _extract_multimodal_content(
        self,
        file_path: Path
    ) -> Tuple[str, List[Path]]:
        """Extract text and images from PDF."""
        
        import fitz  # PyMuPDF for better image extraction
        
        text_content = []
        images = []
        temp_dir = Path("temp_images")
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Open PDF with PyMuPDF
            pdf = fitz.open(file_path)
            
            for page_num, page in enumerate(pdf):
                # Extract text
                text = page.get_text()
                text_content.append(text)
                
                # Extract images if vision is enabled
                if self.use_vision:
                    image_list = page.get_images()
                    
                    for img_index, img in enumerate(image_list):
                        # Get image data
                        xref = img[0]
                        pix = fitz.Pixmap(pdf, xref)
                        
                        # Save image
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_path = temp_dir / f"page_{page_num}_img_{img_index}.png"
                            pix.save(str(img_path))
                            images.append(img_path)
                        
                        pix = None
            
            pdf.close()
            
        except Exception as e:
            logger.error(f"Error extracting multimodal content: {e}")
            # Fallback to text-only extraction
            text_content = [await self.strategy.extract_from_pdf(file_path)]
        
        return "\n\n".join(text_content), images
    
    async def _extract_concepts_multimodal(
        self,
        text: str,
        images: List[Path],
        certification_name: str
    ) -> List[Concept]:
        """Extract concepts using multimodal LLM."""
        
        # Prepare prompt
        prompt = self.prompt_manager.get_prompt(
            PromptType.CONCEPT_EXTRACTION,
            {
                "certification_name": certification_name,
                "page_count": len(text.split("\n\n"))
            }
        )
        
        # Create multimodal message
        message = MultimodalMessage(
            text=f"{prompt}\n\nCertification Content:\n{text[:10000]}...",  # Truncate for context limit
            images=images[:5] if images else [],  # Include up to 5 diagram images
            role="user"
        )
        
        # Get LLM response
        response = await self.llm.generate(
            [message],
            response_format={"type": "json"}
        )
        
        # Parse concepts from response
        concepts = []
        if response.structured_data:
            for concept_data in response.structured_data.get("concepts", []):
                concept = Concept(
                    id=concept_data["id"],
                    name=concept_data["name"],
                    type=ConceptType(concept_data["type"]),
                    description=concept_data["description"],
                    importance=concept_data["importance"],
                    complexity=concept_data["complexity"],
                    prerequisites=concept_data.get("prerequisites", []),
                    visual_metaphor_suggestions=concept_data.get("visual_metaphors", []),
                    examples=concept_data.get("examples", [])
                )
                concepts.append(concept)
        
        # If LLM extraction fails, fall back to pattern-based extraction
        if not concepts:
            logger.warning("LLM concept extraction returned no results, using fallback")
            concepts = await self.strategy.identify_concepts(text, certification_name)
        
        logger.info(f"Extracted {len(concepts)} concepts with multimodal LLM")
        return concepts
    
    async def _build_knowledge_graph_llm(
        self,
        concepts: List[Concept],
        text: str
    ) -> Tuple[Any, List[ConceptRelationship]]:
        """Build knowledge graph with LLM assistance."""
        
        # Prepare concept summary for LLM
        concept_summary = []
        for concept in concepts[:30]:  # Limit to prevent context overflow
            concept_summary.append({
                "id": concept.id,
                "name": concept.name,
                "type": concept.type.value,
                "description": concept.description[:100]
            })
        
        # Create prompt for relationship extraction
        prompt = f"""
Analyze the relationships between these concepts from {len(concepts)} total concepts:

{json.dumps(concept_summary, indent=2)}

Based on the certification text, identify how these concepts relate to each other.
Focus on the most important relationships that help understanding.

Output Format:
```json
{{
  "relationships": [
    {{
      "source": "concept_id1",
      "target": "concept_id2", 
      "type": "depends_on|enables|contains|extends|implements|secures|optimizes|integrates_with",
      "strength": 0.0-1.0,
      "rationale": "Brief explanation"
    }}
  ],
  "relationship_insights": {{
    "central_concepts": ["most connected concept IDs"],
    "concept_clusters": [["related_id1", "related_id2"], ["related_id3", "related_id4"]],
    "learning_dependencies": "Description of prerequisite relationships"
  }}
}}
```
"""
        
        message = MultimodalMessage(
            text=prompt,
            role="user"
        )
        
        response = await self.llm.generate(
            [message],
            response_format={"type": "json"}
        )
        
        relationships = []
        if response.structured_data:
            for rel_data in response.structured_data.get("relationships", []):
                relationship = ConceptRelationship(
                    source_id=rel_data["source"],
                    target_id=rel_data["target"],
                    relationship_type=RelationshipType(rel_data["type"]),
                    strength=rel_data["strength"],
                    description=rel_data.get("rationale", "")
                )
                relationships.append(relationship)
        
        # Build NetworkX graph
        import networkx as nx
        graph = nx.DiGraph()
        
        for concept in concepts:
            graph.add_node(concept.id, concept=concept)
        
        for rel in relationships:
            if rel.source_id in graph and rel.target_id in graph:
                graph.add_edge(rel.source_id, rel.target_id, relationship=rel)
        
        return graph, relationships
    
    async def _generate_learning_paths_llm(
        self,
        concepts: List[Concept],
        relationships: List[ConceptRelationship]
    ) -> List[List[str]]:
        """Generate optimized learning paths using LLM."""
        
        # Prepare data for LLM
        concept_summary = {
            c.id: {
                "name": c.name,
                "complexity": c.complexity,
                "importance": c.importance,
                "prerequisites": c.prerequisites
            }
            for c in concepts
        }
        
        relationship_summary = [
            {
                "source": r.source_id,
                "target": r.target_id,
                "type": r.relationship_type.value
            }
            for r in relationships
        ]
        
        prompt = f"""
Generate optimal learning paths for these concepts:

Concepts: {json.dumps(concept_summary, indent=2)}
Relationships: {json.dumps(relationship_summary, indent=2)}

Create 3-5 different learning paths that:
1. Respect prerequisite relationships
2. Progress from simple to complex
3. Group related concepts
4. Minimize cognitive load
5. Maximize retention

Output Format:
```json
{{
  "learning_paths": [
    {{
      "path_name": "Descriptive name",
      "description": "What this path focuses on",
      "target_audience": "Who this is best for",
      "concept_sequence": ["concept_id1", "concept_id2", ...],
      "rationale": "Why this order works"
    }}
  ],
  "path_selection_guide": "How to choose between paths"
}}
```
"""
        
        message = MultimodalMessage(text=prompt, role="user")
        response = await self.llm.generate([message], response_format={"type": "json"})
        
        learning_paths = []
        if response.structured_data:
            for path_data in response.structured_data.get("learning_paths", []):
                learning_paths.append(path_data["concept_sequence"])
        
        # Fallback to algorithmic generation if needed
        if not learning_paths:
            learning_paths = await self.strategy.generate_learning_paths(
                nx.DiGraph(), concepts  # Create a simple graph
            )
        
        return learning_paths
    
    async def _extract_domain_insights(
        self,
        concepts: List[Concept],
        relationships: List[ConceptRelationship],
        text: str,
        images: List[Path]
    ) -> Dict[str, Any]:
        """Extract additional insights about the domain."""
        
        prompt = f"""
Analyze this certification domain and provide insights:

Total Concepts: {len(concepts)}
Total Relationships: {len(relationships)}
Key Concepts: {', '.join([c.name for c in concepts[:10]])}

Provide insights on:
1. The main domain/field this certification covers
2. Key themes that run throughout
3. Difficulty distribution and progression
4. Estimated learning time for average professional
5. Visual learning opportunities

Output Format:
```json
{{
  "domain_name": "Specific domain name",
  "domain_category": "cloud|security|data|networking|devops|ai_ml",
  "key_themes": ["theme1", "theme2", "theme3"],
  "difficulty_distribution": {{
    "beginner": percentage,
    "intermediate": percentage,
    "advanced": percentage,
    "expert": percentage
  }},
  "estimated_hours": number,
  "visual_learning_opportunities": [
    {{
      "concept": "concept that benefits from visualization",
      "visual_approach": "How to visualize it",
      "rationale": "Why this helps understanding"
    }}
  ],
  "learning_challenges": ["challenge1", "challenge2"],
  "success_factors": ["factor1", "factor2"]
}}
```
"""
        
        # Include sample diagram images if available
        message = MultimodalMessage(
            text=prompt,
            images=images[:3] if images else [],
            role="user"
        )
        
        response = await self.llm.generate([message], response_format={"type": "json"})
        
        if response.structured_data:
            return response.structured_data
        
        # Fallback insights
        return {
            "domain_name": "Technical Certification",
            "key_themes": ["Technology", "Best Practices", "Implementation"],
            "difficulty_distribution": {"beginner": 20, "intermediate": 50, "advanced": 25, "expert": 5},
            "estimated_hours": 40.0
        }
    
    async def analyze_concept_visual_potential(
        self,
        concept: Concept,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze how well a concept can be visualized."""
        
        prompt = f"""
Analyze the visual learning potential for this concept:

Concept: {concept.name}
Type: {concept.type.value}
Description: {concept.description}
Complexity: {concept.complexity}/10

{f"Additional Context: {context}" if context else ""}

Assess:
1. How well can this be visualized?
2. What visual metaphors work best?
3. Should this be animated or static?
4. What interactions would help understanding?

Output Format:
```json
{{
  "visual_potential_score": 0-100,
  "recommended_format": "animation|diagram|interactive|hybrid",
  "visual_metaphors": [
    {{
      "metaphor": "Description",
      "effectiveness": 0-100,
      "implementation": "How to implement"
    }}
  ],
  "animation_value": {{
    "score": 0-100,
    "key_moments": ["What to animate"],
    "duration_estimate": seconds
  }},
  "interaction_design": {{
    "primary_interaction": "click|hover|drag|explore",
    "learning_benefit": "What interaction adds"
  }}
}}
```
"""
        
        message = MultimodalMessage(text=prompt, role="user")
        response = await self.llm.generate([message], response_format={"type": "json"})
        
        if response.structured_data:
            return response.structured_data
        
        # Fallback assessment
        return {
            "visual_potential_score": 75,
            "recommended_format": "animation",
            "visual_metaphors": concept.visual_metaphor_suggestions,
            "animation_value": {"score": 80, "duration_estimate": 30}
        }
