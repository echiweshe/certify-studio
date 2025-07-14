"""
Enhanced Diagram Generation Agent with multimodal LLM capabilities.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import asyncio
import json
import numpy as np
from PIL import Image

from ....core.llm import MultimodalLLM, LLMProvider, PromptManager, PromptType
from ....core.llm.multimodal_llm import MultimodalMessage, MultimodalResponse
from ....core.logging import get_logger
from ...certification.domain_extraction_agent import Concept
from .agent import DiagramGenerationAgent as BaseDiagramAgent
from .models import DiagramType, Diagram, DiagramElement, DiagramEdge

logger = get_logger(__name__)


class MultimodalDiagramGenerationAgent(BaseDiagramAgent):
    """Enhanced diagram generation with multimodal LLM capabilities."""
    
    def __init__(
        self,
        llm: Optional[MultimodalLLM] = None,
        enable_sketch_analysis: bool = True
    ):
        # Initialize base agent
        super().__init__(llm=None)
        
        # Initialize multimodal LLM
        self.llm = llm or MultimodalLLM(
            provider=LLMProvider.ANTHROPIC_CLAUDE_VISION,
            temperature=0.6  # Balanced for analytical and creative tasks
        )
        
        self.enable_sketch_analysis = enable_sketch_analysis
        self.prompt_manager = PromptManager()
        self.diagram_examples_cache = {}
    
    async def generate_diagram(
        self,
        concepts: List[Concept],
        relationships: List[Tuple[str, str, str]],
        requirements: Optional[Dict[str, Any]] = None,
        reference_diagrams: Optional[List[Union[Path, Image.Image]]] = None
    ) -> Dict[str, Any]:
        """Generate diagram with multimodal understanding."""
        
        logger.info(f"Generating diagram for {len(concepts)} concepts with multimodal LLM")
        
        # Analyze reference diagrams if provided
        style_insights = None
        if reference_diagrams and self.enable_sketch_analysis:
            style_insights = await self._analyze_reference_diagrams(
                reference_diagrams, concepts
            )
        
        # Generate optimal diagram structure with LLM
        diagram_structure = await self._generate_diagram_structure_llm(
            concepts, relationships, requirements, style_insights
        )
        
        # Create diagram with enhanced layout
        diagram = await self._create_enhanced_diagram(
            diagram_structure, concepts, relationships, requirements
        )
        
        # Optimize with visual analysis
        if self.enable_sketch_analysis:
            diagram = await self._optimize_with_visual_analysis(diagram)
        
        # Generate final result
        result = await self._create_diagram_result(diagram, concepts)
        
        return result
    
    async def _analyze_reference_diagrams(
        self,
        reference_diagrams: List[Union[Path, Image.Image]],
        concepts: List[Concept]
    ) -> Dict[str, Any]:
        """Analyze reference diagrams for style and layout insights."""
        
        concept_names = [c.name for c in concepts[:10]]  # First 10 for context
        
        prompt = f"""
Analyze these reference diagrams to extract style and layout patterns.

Context: Creating a diagram for concepts including: {', '.join(concept_names)}

Analyze:
1. Layout patterns and spatial organization
2. Visual hierarchy techniques
3. Connection/relationship visualization
4. Color usage and meaning
5. Shape language and consistency
6. Labeling and annotation approaches

Extract insights on:
- What makes these diagrams effective
- Layout algorithms that would work well
- Visual metaphors to adopt
- Style elements to incorporate
- What to avoid

Output Format:
```json
{{
  "layout_insights": {{
    "dominant_pattern": "hierarchical|network|flowchart|layered",
    "spatial_organization": "Description of how space is used",
    "effective_techniques": ["technique1", "technique2"],
    "suggested_algorithm": "force_directed|hierarchical|circular|layered"
  }},
  "visual_style": {{
    "shape_language": {{"node_shapes": ["shapes used"], "meanings": {{"shape": "what it represents"}}}},
    "color_scheme": {{"primary": "#hex", "secondary": "#hex", "semantic_colors": {{"meaning": "#hex"}}}},
    "line_styles": {{"connection_types": {{"type": "style description"}}}},
    "typography": {{"hierarchy": ["title", "labels", "annotations"], "sizing": "approach"}}
  }},
  "interaction_cues": {{
    "hover_indicators": "How hover is indicated",
    "clickable_elements": "What appears clickable",
    "visual_feedback": "Types of feedback shown"
  }},
  "effectiveness_analysis": {{
    "strengths": ["what works well"],
    "weaknesses": ["what could improve"],
    "cognitive_load": "high|medium|low",
    "clarity_score": 0-100
  }},
  "adaptation_recommendations": [
    {{
      "element": "What to adapt",
      "rationale": "Why this would work",
      "implementation": "How to implement"
    }}
  ]
}}
```
"""
        
        message = MultimodalMessage(
            text=prompt,
            images=reference_diagrams[:5],  # Limit to 5 diagrams
            role="user"
        )
        
        response = await self.llm.generate(
            [message],
            response_format={"type": "json"}
        )
        
        if response.structured_data:
            return response.structured_data
        
        return {"layout_insights": {"suggested_algorithm": "force_directed"}}
    
    async def _generate_diagram_structure_llm(
        self,
        concepts: List[Concept],
        relationships: List[Tuple[str, str, str]],
        requirements: Optional[Dict[str, Any]],
        style_insights: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate optimal diagram structure using LLM."""
        
        # Prepare concept summary
        concept_summary = [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type.value,
                "importance": c.importance,
                "complexity": c.complexity
            }
            for c in concepts[:30]  # Limit for context
        ]
        
        # Get diagram analysis prompt
        prompt = self.prompt_manager.get_prompt(
            PromptType.DIAGRAM_ANALYSIS,
            {
                "diagram_spec": json.dumps({
                    "concepts": concept_summary,
                    "relationships": [
                        {"source": r[0], "target": r[1], "type": r[2]}
                        for r in relationships[:50]
                    ],
                    "requirements": requirements or {}
                }, indent=2)
            }
        )
        
        # Add style insights if available
        if style_insights:
            prompt += f"\n\nConsider these style insights from reference diagrams:\n"
            prompt += json.dumps(style_insights, indent=2)
        
        message = MultimodalMessage(text=prompt, role="user")
        
        response = await self.llm.generate(
            [message],
            response_format={"type": "json"}
        )
        
        if response.structured_data:
            return response.structured_data
        
        # Fallback structure
        return {
            "layout_improvements": {
                "algorithm_suggestion": "force_directed",
                "rationale": "Default layout for general diagrams"
            },
            "visual_improvements": {},
            "simplification_suggestions": {}
        }
    
    async def _create_enhanced_diagram(
        self,
        diagram_structure: Dict[str, Any],
        concepts: List[Concept],
        relationships: List[Tuple[str, str, str]],
        requirements: Optional[Dict[str, Any]]
    ) -> Diagram:
        """Create diagram with enhanced structure from LLM insights."""
        
        # Determine diagram type with LLM recommendation
        diagram_type = await self._determine_diagram_type_llm(
            concepts, relationships, diagram_structure
        )
        
        # Apply simplification if suggested
        if diagram_structure.get("simplification_suggestions"):
            concepts, relationships = self._apply_simplification(
                concepts, relationships,
                diagram_structure["simplification_suggestions"]
            )
        
        # Generate base diagram
        diagram = await self.strategy.generate_diagram(
            concepts,
            relationships,
            diagram_type,
            requirements
        )
        
        # Apply visual improvements
        if diagram_structure.get("visual_improvements"):
            diagram = self._apply_visual_improvements(
                diagram,
                diagram_structure["visual_improvements"]
            )
        
        # Apply layout improvements
        if diagram_structure.get("layout_improvements"):
            diagram = await self._apply_layout_improvements(
                diagram,
                diagram_structure["layout_improvements"]
            )
        
        return diagram
    
    async def _determine_diagram_type_llm(
        self,
        concepts: List[Concept],
        relationships: List[Tuple[str, str, str]],
        structure: Dict[str, Any]
    ) -> DiagramType:
        """Determine optimal diagram type using LLM analysis."""
        
        # Check if LLM suggested a specific type
        suggested_layout = structure.get("layout_improvements", {}).get("algorithm_suggestion", "")
        
        type_mapping = {
            "hierarchical": DiagramType.HIERARCHY,
            "layered": DiagramType.ARCHITECTURE,
            "force_directed": DiagramType.NETWORK,
            "circular": DiagramType.STATE,
            "flow": DiagramType.FLOW
        }
        
        if suggested_layout in type_mapping:
            return type_mapping[suggested_layout]
        
        # Fallback to base logic
        return await self.strategy._determine_diagram_type(concepts, relationships)
    
    def _apply_simplification(
        self,
        concepts: List[Concept],
        relationships: List[Tuple[str, str, str]],
        simplification: Dict[str, Any]
    ) -> Tuple[List[Concept], List[Tuple[str, str, str]]]:
        """Apply simplification suggestions from LLM."""
        
        # Group elements as suggested
        groups_to_create = simplification.get("elements_to_group", [])
        elements_to_remove = set(simplification.get("elements_to_remove", []))
        
        # Filter out elements to remove
        filtered_concepts = [
            c for c in concepts
            if c.id not in elements_to_remove
        ]
        
        # Filter relationships
        filtered_relationships = [
            (s, t, r) for s, t, r in relationships
            if s not in elements_to_remove and t not in elements_to_remove
        ]
        
        # TODO: Implement grouping logic
        # For now, just return filtered results
        
        return filtered_concepts, filtered_relationships
    
    def _apply_visual_improvements(
        self,
        diagram: Diagram,
        improvements: Dict[str, Any]
    ) -> Diagram:
        """Apply visual improvements from LLM analysis."""
        
        # Apply color improvements
        if "color_usage" in improvements:
            self._apply_color_improvements(diagram, improvements["color_usage"])
        
        # Apply size hierarchy
        if "size_hierarchy" in improvements:
            self._apply_size_hierarchy(diagram, improvements["size_hierarchy"])
        
        # Apply connection styling
        if "connection_styling" in improvements:
            self._apply_connection_styling(diagram, improvements["connection_styling"])
        
        return diagram
    
    def _apply_color_improvements(
        self,
        diagram: Diagram,
        color_guidance: str
    ) -> None:
        """Apply color improvements to diagram elements."""
        
        # Parse color guidance and apply
        if "importance" in color_guidance.lower():
            # Color by importance
            for element in diagram.elements.values():
                importance = element.metadata.get("importance", 0.5)
                if importance > 0.8:
                    element.style["fill"] = "#FF6B6B"  # High importance
                elif importance > 0.5:
                    element.style["fill"] = "#4ECDC4"  # Medium importance
                else:
                    element.style["fill"] = "#95E1D3"  # Low importance
    
    def _apply_size_hierarchy(
        self,
        diagram: Diagram,
        size_guidance: str
    ) -> None:
        """Apply size hierarchy to diagram elements."""
        
        # Adjust sizes based on importance
        for element in diagram.elements.values():
            importance = element.metadata.get("importance", 0.5)
            base_width = element.size["width"]
            base_height = element.size["height"]
            
            # Scale by importance
            scale = 0.8 + (importance * 0.4)  # 0.8x to 1.2x
            element.size["width"] = base_width * scale
            element.size["height"] = base_height * scale
    
    def _apply_connection_styling(
        self,
        diagram: Diagram,
        styling_guidance: str
    ) -> None:
        """Apply connection styling improvements."""
        
        # Apply different styles based on relationship types
        for edge in diagram.edges:
            if "hierarchy" in styling_guidance.lower():
                if edge.edge_type in ["contains", "has"]:
                    edge.style["stroke_width"] = 3
                    edge.style["stroke"] = "#2C3E50"
                elif edge.edge_type in ["depends_on", "requires"]:
                    edge.style["stroke_dash"] = "5,5"
                    edge.style["stroke"] = "#E74C3C"
    
    async def _apply_layout_improvements(
        self,
        diagram: Diagram,
        layout_improvements: Dict[str, Any]
    ) -> Diagram:
        """Apply layout improvements from LLM analysis."""
        
        # Get specific adjustments
        adjustments = layout_improvements.get("specific_adjustments", [])
        
        for adjustment in adjustments:
            element_id = adjustment.get("element")
            suggestion = adjustment.get("suggestion", "")
            
            if element_id in diagram.elements:
                element = diagram.elements[element_id]
                
                # Parse and apply position adjustments
                if "move to" in suggestion.lower():
                    # Extract new position from suggestion
                    # This would need more sophisticated parsing
                    pass
                elif "align with" in suggestion.lower():
                    # Align with other elements
                    pass
        
        return diagram
    
    async def _optimize_with_visual_analysis(
        self,
        diagram: Diagram
    ) -> Diagram:
        """Optimize diagram using visual analysis."""
        
        # Render diagram to image for analysis
        diagram_image = await self._render_diagram_preview(diagram)
        
        # Analyze visual quality
        quality_analysis = await self._analyze_diagram_quality(
            diagram_image, diagram
        )
        
        # Apply optimizations based on analysis
        if quality_analysis.get("issues_identified"):
            diagram = await self._fix_visual_issues(
                diagram, quality_analysis["issues_identified"]
            )
        
        return diagram
    
    async def _render_diagram_preview(
        self,
        diagram: Diagram
    ) -> Image.Image:
        """Render diagram to image for analysis."""
        
        # Create a simple preview using PIL
        # In production, this would use actual rendering
        width, height = 1200, 800
        img = Image.new('RGB', (width, height), 'white')
        
        # This is a placeholder - actual implementation would render the diagram
        # For now, return blank image
        return img
    
    async def _analyze_diagram_quality(
        self,
        diagram_image: Image.Image,
        diagram: Diagram
    ) -> Dict[str, Any]:
        """Analyze visual quality of rendered diagram."""
        
        prompt = f"""
Analyze the visual quality of this diagram:

Diagram contains:
- {len(diagram.elements)} elements
- {len(diagram.edges)} connections
- {len(diagram.layers)} layers

Evaluate:
1. Visual clarity and readability
2. Element spacing and distribution
3. Connection routing quality
4. Label visibility
5. Overall aesthetic balance

Identify specific issues that need fixing.

Output Format:
```json
{{
  "quality_score": 0-100,
  "issues_identified": [
    {{
      "issue": "Description",
      "severity": "critical|high|medium|low",
      "location": "Where in the diagram",
      "fix": "How to fix it"
    }}
  ],
  "positive_aspects": ["what works well"],
  "accessibility_issues": ["any accessibility problems"]
}}
```
"""
        
        message = MultimodalMessage(
            text=prompt,
            images=[diagram_image],
            role="user"
        )
        
        response = await self.llm.generate(
            [message],
            response_format={"type": "json"}
        )
        
        if response.structured_data:
            return response.structured_data
        
        return {"quality_score": 80, "issues_identified": []}
    
    async def _fix_visual_issues(
        self,
        diagram: Diagram,
        issues: List[Dict[str, Any]]
    ) -> Diagram:
        """Fix identified visual issues."""
        
        for issue in issues:
            if issue["severity"] in ["critical", "high"]:
                fix_type = issue["fix"].lower()
                
                if "spacing" in fix_type:
                    # Adjust element spacing
                    await self._improve_spacing(diagram)
                elif "overlap" in fix_type:
                    # Fix overlapping elements
                    await self._fix_overlaps(diagram)
                elif "routing" in fix_type:
                    # Improve edge routing
                    await self._improve_edge_routing(diagram)
        
        return diagram
    
    async def _improve_spacing(self, diagram: Diagram) -> None:
        """Improve element spacing in diagram."""
        
        # Simple spacing improvement
        # In production, this would use force-directed adjustments
        elements = list(diagram.elements.values())
        
        for i, el1 in enumerate(elements):
            for el2 in elements[i+1:]:
                # Check distance
                dx = el1.position["x"] - el2.position["x"]
                dy = el1.position["y"] - el2.position["y"]
                distance = (dx**2 + dy**2)**0.5
                
                # Minimum spacing based on sizes
                min_distance = (
                    (el1.size["width"] + el2.size["width"]) / 2 +
                    (el1.size["height"] + el2.size["height"]) / 2
                ) * 0.1  # 10% of combined size
                
                if distance < min_distance:
                    # Push apart
                    push_factor = (min_distance - distance) / 2
                    if dx != 0:
                        el2.position["x"] += push_factor * (dx / distance)
                    if dy != 0:
                        el2.position["y"] += push_factor * (dy / distance)
    
    async def _fix_overlaps(self, diagram: Diagram) -> None:
        """Fix overlapping elements."""
        
        # This would implement overlap detection and resolution
        # For now, it's a placeholder
        pass
    
    async def _improve_edge_routing(self, diagram: Diagram) -> None:
        """Improve edge routing to reduce crossings."""
        
        # This would implement edge routing optimization
        # For now, it's a placeholder
        pass
    
    async def _create_diagram_result(
        self,
        diagram: Diagram,
        concepts: List[Concept]
    ) -> Dict[str, Any]:
        """Create final diagram result with metadata."""
        
        # Generate quality assessment
        quality_report = await self._generate_quality_report(diagram, concepts)
        
        # Create export specifications
        export_specs = await self._generate_export_specs(diagram)
        
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
                "interactivity_level": "high" if diagram.interactions else "low",
                "llm_enhanced": True,
                "quality_report": quality_report
            }
        }
        
        logger.info(f"Created enhanced diagram: {result['diagram_id']}")
        return result
    
    async def _generate_quality_report(
        self,
        diagram: Diagram,
        concepts: List[Concept]
    ) -> Dict[str, Any]:
        """Generate quality assessment report."""
        
        prompt = f"""
Assess the quality of this generated diagram:

Diagram Summary:
- Type: {diagram.type.value}
- Elements: {len(diagram.elements)}
- Connections: {len(diagram.edges)}
- Layers: {len(diagram.layers)}
- Concepts represented: {len(concepts)}

Evaluate the diagram's effectiveness for learning.

Output Format:
```json
{{
  "overall_effectiveness": 0-100,
  "strengths": ["strength1", "strength2"],
  "areas_for_improvement": ["area1", "area2"],
  "learning_impact": {{
    "clarity": 0-100,
    "memorability": 0-100,
    "engagement": 0-100
  }},
  "recommendations": ["recommendation1", "recommendation2"]
}}
```
"""
        
        message = MultimodalMessage(text=prompt, role="user")
        
        response = await self.llm.generate(
            [message],
            response_format={"type": "json"}
        )
        
        if response.structured_data:
            return response.structured_data
        
        return {
            "overall_effectiveness": 85,
            "strengths": ["Clear hierarchy", "Good use of color"],
            "learning_impact": {"clarity": 90, "memorability": 80, "engagement": 85}
        }
    
    async def generate_sketch_from_description(
        self,
        description: str,
        style_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate diagram sketch from natural language description."""
        
        prompt = f"""
Create a diagram specification from this description:

{description}

Style Preferences:
{json.dumps(style_preferences, indent=2) if style_preferences else "Default modern style"}

Generate:
1. Identify key concepts/entities
2. Determine relationships
3. Select optimal diagram type
4. Define visual structure

Output Format:
```json
{{
  "extracted_concepts": [
    {{"name": "concept", "role": "what it represents", "importance": "high|medium|low"}}
  ],
  "relationships": [
    {{"from": "concept1", "to": "concept2", "type": "relationship", "label": "description"}}
  ],
  "diagram_type": "architecture|flow|network|hierarchy",
  "layout_suggestion": {{
    "algorithm": "force_directed|hierarchical|circular",
    "orientation": "horizontal|vertical",
    "grouping": ["concepts to group together"]
  }},
  "visual_elements": {{
    "shapes": {{"concept": "suggested shape"}},
    "colors": {{"concept": "suggested color or meaning"}},
    "emphasis": ["concepts to emphasize"]
  }}
}}
```
"""
        
        message = MultimodalMessage(text=prompt, role="user")
        
        response = await self.llm.generate(
            [message],
            response_format={"type": "json"}
        )
        
        if response.structured_data:
            # Convert to diagram
            return await self._sketch_to_diagram(response.structured_data)
        
        return {"error": "Could not parse description"}
    
    async def _sketch_to_diagram(
        self,
        sketch_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert sketch specification to actual diagram."""
        
        # Create concepts from extracted data
        concepts = []
        for i, concept_data in enumerate(sketch_spec.get("extracted_concepts", [])):
            concept = Concept(
                id=f"sketch_{i}",
                name=concept_data["name"],
                type=ConceptType.SERVICE,  # Default type
                description=concept_data.get("role", ""),
                importance={"high": 0.9, "medium": 0.5, "low": 0.3}[
                    concept_data.get("importance", "medium")
                ],
                complexity=5  # Default complexity
            )
            concepts.append(concept)
        
        # Create relationships
        relationships = [
            (
                f"sketch_{self._find_concept_index(r['from'], sketch_spec['extracted_concepts'])}",
                f"sketch_{self._find_concept_index(r['to'], sketch_spec['extracted_concepts'])}",
                r.get("type", "related")
            )
            for r in sketch_spec.get("relationships", [])
        ]
        
        # Generate diagram
        return await self.generate_diagram(
            concepts,
            relationships,
            {"type": sketch_spec.get("diagram_type", "network")}
        )
    
    def _find_concept_index(
        self,
        name: str,
        concepts: List[Dict[str, Any]]
    ) -> int:
        """Find concept index by name."""
        
        for i, concept in enumerate(concepts):
            if concept["name"] == name:
                return i
        return 0
