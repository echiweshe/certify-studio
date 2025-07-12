"""
Intelligent diagram generation strategy.
"""

from typing import Dict, List, Any, Optional, Tuple
from langchain.chat_models.base import BaseChatModel

from ....core.logging import get_logger
from ...certification.domain_extraction_agent import Concept, ConceptType
from .models import (
    DiagramType, LayoutAlgorithm, DiagramElement, 
    DiagramEdge, DiagramLayer, Diagram
)
from .layout_engine import DiagramLayoutEngine

logger = get_logger(__name__)


class IntelligentDiagramStrategy:
    """AI-driven strategy for creating diagrams."""
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm
        self.layout_engine = DiagramLayoutEngine()
        self.style_themes = self._initialize_style_themes()
    
    def _initialize_style_themes(self) -> Dict[str, Dict[str, Any]]:
        """Initialize visual style themes."""
        
        return {
            "aws": {
                "colors": {
                    "primary": "#232F3E",
                    "secondary": "#FF9900",
                    "accent": "#146EB4",
                    "background": "#FFFFFF",
                    "text": "#232F3E"
                },
                "node_styles": {
                    "service": {"fill": "#FF9900", "stroke": "#232F3E", "stroke_width": 2},
                    "resource": {"fill": "#146EB4", "stroke": "#232F3E", "stroke_width": 1},
                    "security": {"fill": "#DD344C", "stroke": "#232F3E", "stroke_width": 2},
                    "default": {"fill": "#E0E0E0", "stroke": "#232F3E", "stroke_width": 1}
                },
                "edge_styles": {
                    "data_flow": {"stroke": "#146EB4", "stroke_width": 2, "arrow": True},
                    "dependency": {"stroke": "#232F3E", "stroke_width": 1, "dash": "5,5"},
                    "security": {"stroke": "#DD344C", "stroke_width": 2},
                    "default": {"stroke": "#666666", "stroke_width": 1}
                }
            },
            "modern": {
                "colors": {
                    "primary": "#6366F1",
                    "secondary": "#EC4899",
                    "accent": "#10B981",
                    "background": "#F9FAFB",
                    "text": "#1F2937"
                },
                "node_styles": {
                    "default": {"fill": "#6366F1", "stroke": "#4F46E5", "stroke_width": 2},
                    "highlight": {"fill": "#EC4899", "stroke": "#DB2777", "stroke_width": 3},
                    "subtle": {"fill": "#E5E7EB", "stroke": "#D1D5DB", "stroke_width": 1}
                },
                "edge_styles": {
                    "default": {"stroke": "#9CA3AF", "stroke_width": 2},
                    "important": {"stroke": "#6366F1", "stroke_width": 3}
                }
            }
        }
    
    async def generate_diagram(
        self,
        concepts: List[Concept],
        relationships: List[Tuple[str, str, str]],  # (source_id, target_id, relationship_type)
        diagram_type: Optional[DiagramType] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Diagram:
        """Generate a diagram from concepts and relationships."""
        
        # Determine optimal diagram type if not specified
        if not diagram_type:
            diagram_type = await self._determine_diagram_type(concepts, relationships)
        
        # Select appropriate layout algorithm
        layout_algorithm = self._select_layout_algorithm(diagram_type, len(concepts))
        
        # Create diagram elements
        elements = await self._create_elements(concepts, diagram_type)
        
        # Create edges
        edges = await self._create_edges(relationships, elements)
        
        # Calculate layout
        positions = await self.layout_engine.calculate_layout(
            list(elements.values()),
            edges,
            layout_algorithm
        )
        
        # Apply positions to elements
        for el_id, pos in positions.items():
            if el_id in elements:
                elements[el_id].position = pos
        
        # Organize into layers
        layers = await self._organize_layers(elements, diagram_type)
        
        # Select style theme
        style_theme = self._select_style_theme(context)
        
        # Apply styling
        elements, edges = await self._apply_styling(
            elements, edges, style_theme, diagram_type
        )
        
        # Add annotations
        annotations = await self._generate_annotations(
            elements, edges, concepts, diagram_type
        )
        
        # Create diagram
        diagram = Diagram(
            id=f"diagram_{diagram_type.value}_{hash(str(concepts)) % 10000}",
            title=self._generate_title(concepts, diagram_type),
            type=diagram_type,
            elements=elements,
            edges=edges,
            layers=layers,
            layout={
                "algorithm": layout_algorithm.value,
                "spacing": 0.05,
                "margin": 0.1
            },
            viewport={"width": 1.0, "height": 1.0},
            style_theme=style_theme,
            annotations=annotations,
            interactions=self._define_interactions(diagram_type)
        )
        
        return diagram
    
    async def _determine_diagram_type(
        self,
        concepts: List[Concept],
        relationships: List[Tuple[str, str, str]]
    ) -> DiagramType:
        """Determine the most appropriate diagram type."""
        
        # Analyze concept types
        type_counts = {}
        for concept in concepts:
            type_counts[concept.type] = type_counts.get(concept.type, 0) + 1
        
        # Analyze relationship types
        rel_types = [rel[2] for rel in relationships]
        
        # Decision logic
        if ConceptType.ARCHITECTURE in type_counts and type_counts[ConceptType.ARCHITECTURE] > 2:
            return DiagramType.ARCHITECTURE
        
        if "data_flow" in rel_types or "flow" in str(rel_types):
            return DiagramType.DATA_FLOW
        
        if ConceptType.SECURITY in type_counts and type_counts[ConceptType.SECURITY] > len(concepts) * 0.3:
            return DiagramType.SECURITY
        
        if "sequence" in str(concepts).lower():
            return DiagramType.SEQUENCE
        
        if len(relationships) > len(concepts) * 1.5:
            return DiagramType.NETWORK
        
        # Check for hierarchical structure
        if self._has_hierarchical_structure(concepts, relationships):
            return DiagramType.HIERARCHY
        
        # Default to component diagram
        return DiagramType.COMPONENT
    
    def _has_hierarchical_structure(
        self,
        concepts: List[Concept],
        relationships: List[Tuple[str, str, str]]
    ) -> bool:
        """Check if the concepts form a hierarchical structure."""
        
        # Count parent-child relationships
        parent_child_count = sum(
            1 for _, _, rel_type in relationships
            if rel_type in ["contains", "has", "owns", "parent_of"]
        )
        
        return parent_child_count > len(relationships) * 0.5
    
    def _select_layout_algorithm(
        self,
        diagram_type: DiagramType,
        element_count: int
    ) -> LayoutAlgorithm:
        """Select the best layout algorithm for the diagram type."""
        
        algorithm_map = {
            DiagramType.ARCHITECTURE: LayoutAlgorithm.LAYERED,
            DiagramType.FLOW: LayoutAlgorithm.HIERARCHICAL,
            DiagramType.SEQUENCE: LayoutAlgorithm.HIERARCHICAL,
            DiagramType.NETWORK: LayoutAlgorithm.FORCE_DIRECTED,
            DiagramType.HIERARCHY: LayoutAlgorithm.HIERARCHICAL,
            DiagramType.COMPONENT: LayoutAlgorithm.FORCE_DIRECTED,
            DiagramType.STATE: LayoutAlgorithm.CIRCULAR,
            DiagramType.DEPLOYMENT: LayoutAlgorithm.LAYERED,
            DiagramType.DATA_FLOW: LayoutAlgorithm.HIERARCHICAL,
            DiagramType.SECURITY: LayoutAlgorithm.RADIAL
        }
        
        # Override for large diagrams
        if element_count > 20 and diagram_type != DiagramType.HIERARCHY:
            return LayoutAlgorithm.FORCE_DIRECTED
        
        return algorithm_map.get(diagram_type, LayoutAlgorithm.FORCE_DIRECTED)
    
    async def _create_elements(
        self,
        concepts: List[Concept],
        diagram_type: DiagramType
    ) -> Dict[str, DiagramElement]:
        """Create diagram elements from concepts."""
        
        elements = {}
        
        for concept in concepts:
            # Determine element type based on concept
            element_type = self._determine_element_type(concept, diagram_type)
            
            # Calculate size based on importance and complexity
            size = self._calculate_element_size(concept)
            
            # Create element
            element = DiagramElement(
                id=concept.id,
                element_type=element_type,
                label=concept.name,
                position={"x": 0.5, "y": 0.5},  # Will be updated by layout
                size=size,
                style={},  # Will be styled later
                metadata={
                    "concept_type": concept.type.value,
                    "importance": concept.importance,
                    "complexity": concept.complexity,
                    "description": concept.description[:100] + "..." if len(concept.description) > 100 else concept.description
                }
            )
            
            elements[concept.id] = element
        
        return elements
    
    def _determine_element_type(self, concept: Concept, diagram_type: DiagramType) -> str:
        """Determine the visual element type for a concept."""
        
        # Map concept types to element types
        if concept.type == ConceptType.SERVICE:
            return "service_node"
        elif concept.type == ConceptType.SECURITY:
            return "security_node"
        elif concept.type == ConceptType.PATTERN:
            return "pattern_node"
        elif concept.type == ConceptType.ARCHITECTURE:
            return "architecture_node"
        else:
            return "default_node"
    
    def _calculate_element_size(self, concept: Concept) -> Dict[str, float]:
        """Calculate element size based on concept properties."""
        
        # Base size
        base_width = 0.12
        base_height = 0.08
        
        # Scale by importance
        importance_scale = 0.8 + concept.importance * 0.4
        
        # Adjust for label length
        label_scale = min(1.5, 1.0 + len(concept.name) / 50)
        
        return {
            "width": base_width * importance_scale * label_scale,
            "height": base_height * importance_scale
        }
    
    async def _create_edges(
        self,
        relationships: List[Tuple[str, str, str]],
        elements: Dict[str, DiagramElement]
    ) -> List[DiagramEdge]:
        """Create edges from relationships."""
        
        edges = []
        
        for i, (source_id, target_id, rel_type) in enumerate(relationships):
            if source_id in elements and target_id in elements:
                edge = DiagramEdge(
                    id=f"edge_{i}",
                    source_id=source_id,
                    target_id=target_id,
                    edge_type=rel_type,
                    label=self._format_relationship_label(rel_type),
                    routing=self._determine_edge_routing(rel_type)
                )
                edges.append(edge)
        
        return edges
    
    def _format_relationship_label(self, rel_type: str) -> str:
        """Format relationship type for display."""
        
        # Convert snake_case to readable format
        return rel_type.replace("_", " ").title()
    
    def _determine_edge_routing(self, rel_type: str) -> str:
        """Determine edge routing style based on relationship type."""
        
        if rel_type in ["data_flow", "flow"]:
            return "curved"
        elif rel_type in ["contains", "has"]:
            return "orthogonal"
        else:
            return "straight"
    
    async def _organize_layers(
        self,
        elements: Dict[str, DiagramElement],
        diagram_type: DiagramType
    ) -> List[DiagramLayer]:
        """Organize elements into visual layers."""
        
        layers = []
        
        if diagram_type == DiagramType.ARCHITECTURE:
            # Create layers for different architectural levels
            layer_map = {
                "presentation": [],
                "application": [],
                "data": [],
                "infrastructure": []
            }
            
            # Assign elements to layers based on concept type
            for el_id, element in elements.items():
                concept_type = element.metadata.get("concept_type", "")
                
                if "ui" in element.label.lower() or "frontend" in element.label.lower():
                    layer_map["presentation"].append(el_id)
                elif "api" in element.label.lower() or "service" in concept_type:
                    layer_map["application"].append(el_id)
                elif "database" in element.label.lower() or "storage" in element.label.lower():
                    layer_map["data"].append(el_id)
                else:
                    layer_map["infrastructure"].append(el_id)
            
            # Create layer objects
            for i, (layer_name, element_ids) in enumerate(layer_map.items()):
                if element_ids:
                    layers.append(DiagramLayer(
                        id=f"layer_{layer_name}",
                        name=layer_name.title(),
                        z_index=i,
                        elements=element_ids
                    ))
        
        else:
            # Single layer for other diagram types
            layers.append(DiagramLayer(
                id="main_layer",
                name="Main",
                z_index=0,
                elements=list(elements.keys())
            ))
        
        return layers
    
    def _select_style_theme(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Select appropriate style theme."""
        
        if context and "theme" in context:
            theme_name = context["theme"]
        elif context and "aws" in str(context).lower():
            theme_name = "aws"
        else:
            theme_name = "modern"
        
        return self.style_themes.get(theme_name, self.style_themes["modern"])
    
    async def _apply_styling(
        self,
        elements: Dict[str, DiagramElement],
        edges: List[DiagramEdge],
        style_theme: Dict[str, Any],
        diagram_type: DiagramType
    ) -> Tuple[Dict[str, DiagramElement], List[DiagramEdge]]:
        """Apply visual styling to elements and edges."""
        
        # Style elements
        for element in elements.values():
            element_type = element.element_type
            
            # Get style based on element type
            if element_type in style_theme.get("node_styles", {}):
                base_style = style_theme["node_styles"][element_type].copy()
            else:
                base_style = style_theme["node_styles"].get("default", {}).copy()
            
            # Enhance style based on importance
            if element.metadata.get("importance", 0) > 0.7:
                base_style["stroke_width"] = base_style.get("stroke_width", 2) + 1
                base_style["glow"] = True
            
            # Add icon based on concept type
            concept_type = element.metadata.get("concept_type", "")
            if concept_type:
                base_style["icon"] = self._get_icon_for_concept_type(concept_type)
            
            element.style = base_style
        
        # Style edges
        for edge in edges:
            edge_type = edge.edge_type
            
            # Get style based on edge type
            if edge_type in style_theme.get("edge_styles", {}):
                edge.style = style_theme["edge_styles"][edge_type].copy()
            else:
                edge.style = style_theme["edge_styles"].get("default", {}).copy()
            
            # Add animation for data flow edges
            if "flow" in edge_type:
                edge.style["animation"] = "flow"
                edge.style["animation_speed"] = 2.0
        
        return elements, edges
    
    def _get_icon_for_concept_type(self, concept_type: str) -> str:
        """Get icon name for concept type."""
        
        icon_map = {
            "service": "server",
            "security": "shield",
            "storage": "database",
            "network": "network",
            "compute": "cpu",
            "api": "api",
            "function": "function",
            "queue": "queue",
            "notification": "bell",
            "monitoring": "activity"
        }
        
        # Check for matches in concept type
        for key, icon in icon_map.items():
            if key in concept_type.lower():
                return icon
        
        return "box"  # Default icon
    
    async def _generate_annotations(
        self,
        elements: Dict[str, DiagramElement],
        edges: List[DiagramEdge],
        concepts: List[Concept],
        diagram_type: DiagramType
    ) -> List[Dict[str, Any]]:
        """Generate helpful annotations for the diagram."""
        
        annotations = []
        
        # Title annotation
        annotations.append({
            "type": "title",
            "content": self._generate_title(concepts, diagram_type),
            "position": {"x": 0.5, "y": 0.05},
            "style": {
                "font_size": 24,
                "font_weight": "bold",
                "text_align": "center"
            }
        })
        
        # Legend for important elements
        important_concepts = [c for c in concepts if c.importance > 0.7]
        if important_concepts:
            legend_items = [
                {"icon": self._get_icon_for_concept_type(c.type.value), 
                 "label": c.name,
                 "description": c.description[:50] + "..."}
                for c in important_concepts[:3]
            ]
            
            annotations.append({
                "type": "legend",
                "items": legend_items,
                "position": {"x": 0.85, "y": 0.2},
                "style": {
                    "background": "rgba(255, 255, 255, 0.9)",
                    "border": "1px solid #e0e0e0",
                    "padding": 10
                }
            })
        
        # Callout for complex areas
        if len(edges) > 10:
            # Find the most connected node
            connection_count = {}
            for edge in edges:
                connection_count[edge.source_id] = connection_count.get(edge.source_id, 0) + 1
                connection_count[edge.target_id] = connection_count.get(edge.target_id, 0) + 1
            
            if connection_count:
                most_connected_id = max(connection_count, key=connection_count.get)
                if most_connected_id in elements:
                    element = elements[most_connected_id]
                    annotations.append({
                        "type": "callout",
                        "target_id": most_connected_id,
                        "content": f"Central component with {connection_count[most_connected_id]} connections",
                        "position": {
                            "x": element.position["x"] + 0.1,
                            "y": element.position["y"] - 0.05
                        },
                        "style": {
                            "background": "#fff3cd",
                            "border": "1px solid #ffeaa7",
                            "arrow": True
                        }
                    })
        
        return annotations
    
    def _generate_title(self, concepts: List[Concept], diagram_type: DiagramType) -> str:
        """Generate a descriptive title for the diagram."""
        
        # Extract key terms from high-importance concepts
        key_terms = []
        for concept in sorted(concepts, key=lambda c: c.importance, reverse=True)[:3]:
            words = concept.name.split()
            if words:
                key_terms.append(words[0])
        
        if key_terms:
            key_phrase = " & ".join(key_terms)
            return f"{key_phrase} {diagram_type.value.replace('_', ' ').title()}"
        else:
            return f"{diagram_type.value.replace('_', ' ').title()} Diagram"
    
    def _define_interactions(self, diagram_type: DiagramType) -> Dict[str, Any]:
        """Define interactive behaviors for the diagram."""
        
        return {
            "node_hover": {
                "show_tooltip": True,
                "highlight_connections": True,
                "dim_others": True
            },
            "node_click": {
                "action": "show_details",
                "expand_children": diagram_type == DiagramType.HIERARCHY
            },
            "edge_hover": {
                "show_label": True,
                "highlight": True
            },
            "canvas": {
                "pan": True,
                "zoom": True,
                "zoom_range": [0.5, 2.0]
            },
            "selection": {
                "multi_select": True,
                "lasso_select": True
            }
        }
