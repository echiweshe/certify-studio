"""
Main diagram generation agent.
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import asyncio
from langchain.chat_models.base import BaseChatModel

from ....core.logging import get_logger
from ...certification.domain_extraction_agent import Concept
from .models import DiagramType
from .strategy import IntelligentDiagramStrategy
from .adaptive_engine import AdaptiveDiagramEngine

logger = get_logger(__name__)


class DiagramGenerationAgent:
    """Main agent for generating diagrams from concepts."""
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.strategy = IntelligentDiagramStrategy(llm)
        self.adaptive_engine = AdaptiveDiagramEngine()
        self.export_formats = ["svg", "png", "pdf", "interactive_html", "manim_scene"]
    
    async def generate_diagram(
        self,
        concepts: List[Concept],
        relationships: List[Tuple[str, str, str]],
        requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a complete diagram from concepts and relationships."""
        
        logger.info(f"Generating diagram for {len(concepts)} concepts")
        
        # Extract requirements
        diagram_type = None
        viewer_profile = None
        
        if requirements:
            diagram_type = requirements.get("type")
            viewer_profile = requirements.get("viewer_profile")
        
        # Generate base diagram
        diagram = await self.strategy.generate_diagram(
            concepts,
            relationships,
            diagram_type
        )
        
        # Optimize for viewing
        diagram = await self.adaptive_engine.optimize_diagram(
            diagram,
            viewer_profile
        )
        
        # Generate export specifications
        export_specs = await self._generate_export_specs(diagram)
        
        # Create result
        result = {
            "diagram_id": diagram.id,
            "title": diagram.title,
            "type": diagram.type.value,
            "element_count": len(diagram.elements),
            "edge_count": len(diagram.edges),
            "diagram": self._diagram_to_dict(diagram),
            "export_specs": export_specs,
            "metadata": {
                "created_at": "2024-01-20T10:00:00Z",
                "complexity_score": self._calculate_complexity_score(diagram),
                "interactivity_level": "high" if diagram.interactions else "low"
            }
        }
        
        logger.info(f"Diagram generated: {result['diagram_id']}")
        return result
    
    async def _generate_export_specs(self, diagram) -> Dict[str, Any]:
        """Generate specifications for different export formats."""
        
        return {
            "svg": {
                "scalable": True,
                "include_interactions": True,
                "embed_fonts": True
            },
            "png": {
                "resolution": "300dpi",
                "width": 1920,
                "height": 1080,
                "transparent_background": False
            },
            "interactive_html": {
                "framework": "d3js",
                "features": ["zoom", "pan", "tooltips", "search"],
                "responsive": True
            },
            "manim_scene": {
                "animation_duration": 30,
                "transition_style": "smooth",
                "camera_movement": True
            }
        }
    
    def _calculate_complexity_score(self, diagram) -> float:
        """Calculate diagram complexity score."""
        
        # Factors: number of elements, edges, layers, crossings
        element_score = min(len(diagram.elements) / 20, 1.0)
        edge_score = min(len(diagram.edges) / 30, 1.0)
        layer_score = min(len(diagram.layers) / 5, 1.0)
        
        # Weight the factors
        complexity = (element_score * 0.3 + edge_score * 0.5 + layer_score * 0.2)
        
        return round(complexity, 2)
    
    def _diagram_to_dict(self, diagram) -> Dict[str, Any]:
        """Convert diagram to dictionary for serialization."""
        
        return {
            "id": diagram.id,
            "title": diagram.title,
            "type": diagram.type.value,
            "elements": {
                el_id: {
                    "type": el.element_type,
                    "label": el.label,
                    "position": el.position,
                    "size": el.size,
                    "style": el.style,
                    "metadata": el.metadata,
                    "children": el.children
                }
                for el_id, el in diagram.elements.items()
            },
            "edges": [
                {
                    "id": edge.id,
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "type": edge.edge_type,
                    "label": edge.label,
                    "style": edge.style,
                    "routing": edge.routing
                }
                for edge in diagram.edges
            ],
            "layers": [
                {
                    "id": layer.id,
                    "name": layer.name,
                    "elements": layer.elements,
                    "z_index": layer.z_index
                }
                for layer in diagram.layers
            ],
            "layout": diagram.layout,
            "viewport": diagram.viewport,
            "style_theme": diagram.style_theme,
            "annotations": diagram.annotations,
            "interactions": diagram.interactions
        }
    
    async def generate_diagram_sequence(
        self,
        concepts: List[Concept],
        relationships: List[Tuple[str, str, str]],
        sequence_type: str = "progressive"
    ) -> List[Dict[str, Any]]:
        """Generate a sequence of diagrams for progressive learning."""
        
        sequence = []
        
        if sequence_type == "progressive":
            # Start with simple, add complexity
            concept_groups = self._group_by_complexity(concepts)
            
            for i, (complexity_level, group_concepts) in enumerate(concept_groups.items()):
                # Filter relationships for this group
                concept_ids = {c.id for c in group_concepts}
                group_relationships = [
                    rel for rel in relationships
                    if rel[0] in concept_ids and rel[1] in concept_ids
                ]
                
                # Generate diagram for this complexity level
                diagram_result = await self.generate_diagram(
                    group_concepts,
                    group_relationships,
                    {"type": DiagramType.HIERARCHY if i == 0 else DiagramType.COMPONENT}
                )
                
                diagram_result["sequence_index"] = i
                diagram_result["sequence_title"] = f"Level {complexity_level}: {diagram_result['title']}"
                sequence.append(diagram_result)
        
        elif sequence_type == "focused":
            # Create focused diagrams for each major concept
            major_concepts = [c for c in concepts if c.importance > 0.7]
            
            for concept in major_concepts[:5]:  # Limit to 5 diagrams
                # Find related concepts
                related = self._find_related_concepts(concept, concepts, relationships)
                
                # Generate focused diagram
                diagram_result = await self.generate_diagram(
                    [concept] + related[:5],  # Limit related concepts
                    [(s, t, r) for s, t, r in relationships 
                     if concept.id in [s, t] and s in [c.id for c in [concept] + related] 
                     and t in [c.id for c in [concept] + related]],
                    {"type": DiagramType.NETWORK}
                )
                
                diagram_result["focus_concept"] = concept.name
                sequence.append(diagram_result)
        
        return sequence
    
    def _group_by_complexity(self, concepts: List[Concept]) -> Dict[str, List[Concept]]:
        """Group concepts by complexity level."""
        
        groups = {
            "basic": [],
            "intermediate": [],
            "advanced": []
        }
        
        for concept in concepts:
            if concept.complexity <= 3:
                groups["basic"].append(concept)
            elif concept.complexity <= 6:
                groups["intermediate"].append(concept)
            else:
                groups["advanced"].append(concept)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _find_related_concepts(
        self,
        concept: Concept,
        all_concepts: List[Concept],
        relationships: List[Tuple[str, str, str]]
    ) -> List[Concept]:
        """Find concepts related to a given concept."""
        
        related_ids = set()
        
        # Find directly connected concepts
        for source, target, _ in relationships:
            if source == concept.id:
                related_ids.add(target)
            elif target == concept.id:
                related_ids.add(source)
        
        # Convert IDs to concepts
        related_concepts = [
            c for c in all_concepts
            if c.id in related_ids
        ]
        
        # Sort by importance
        return sorted(related_concepts, key=lambda c: c.importance, reverse=True)


# Example usage
if __name__ == "__main__":
    from ...certification.domain_extraction_agent import Concept, ConceptType
    
    async def test_diagram_generation():
        # Create test concepts
        concepts = [
            Concept(
                id="s3",
                name="S3 Bucket",
                type=ConceptType.SERVICE,
                description="Object storage service",
                importance=0.9,
                complexity=3
            ),
            Concept(
                id="lambda",
                name="Lambda Function",
                type=ConceptType.SERVICE,
                description="Serverless compute",
                importance=0.8,
                complexity=5
            ),
            Concept(
                id="api_gw",
                name="API Gateway",
                type=ConceptType.SERVICE,
                description="API management",
                importance=0.7,
                complexity=4
            )
        ]
        
        relationships = [
            ("api_gw", "lambda", "triggers"),
            ("lambda", "s3", "reads_from")
        ]
        
        agent = DiagramGenerationAgent()
        
        # Generate single diagram
        result = await agent.generate_diagram(
            concepts,
            relationships,
            {"type": DiagramType.ARCHITECTURE}
        )
        
        print(json.dumps(result, indent=2))
        
        # Generate diagram sequence
        sequence = await agent.generate_diagram_sequence(
            concepts,
            relationships,
            "progressive"
        )
        
        print(f"\nGenerated {len(sequence)} diagrams in sequence")
    
    asyncio.run(test_diagram_generation())
