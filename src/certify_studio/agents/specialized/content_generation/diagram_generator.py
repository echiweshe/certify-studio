"""
AI-powered diagram generation module.
"""

from typing import List, Dict, Any, Optional, Tuple
import asyncio
from datetime import datetime
from loguru import logger

from .models import (
    DiagramType,
    DiagramSpecification,
    StyleGuide,
    QualityMetrics,
    AccessibilityMetadata
)


class DiagramGenerator:
    """Generates educational diagrams using AI vision and reasoning."""
    
    def __init__(self, llm_provider: Any = None):
        """Initialize the diagram generator."""
        self.llm_provider = llm_provider
        self.diagram_templates = self._initialize_templates()
        self.layout_algorithms = self._initialize_layout_algorithms()
        self.generated_diagrams: Dict[str, Dict[str, Any]] = {}
    
    def _initialize_templates(self) -> Dict[DiagramType, Dict[str, Any]]:
        """Initialize diagram templates for different types."""
        return {
            DiagramType.ARCHITECTURE: {
                "components": ["boxes", "connections", "labels", "layers"],
                "layout": "hierarchical",
                "style": "technical",
                "common_patterns": ["client-server", "microservices", "layered", "event-driven"]
            },
            DiagramType.FLOWCHART: {
                "components": ["start_end", "process", "decision", "arrows"],
                "layout": "top_to_bottom",
                "style": "clear_flow",
                "common_patterns": ["linear", "branching", "loop", "parallel"]
            },
            DiagramType.SEQUENCE: {
                "components": ["actors", "lifelines", "messages", "activations"],
                "layout": "temporal",
                "style": "interaction_focused",
                "common_patterns": ["request-response", "async", "error_handling"]
            },
            DiagramType.NETWORK: {
                "components": ["nodes", "edges", "clusters", "labels"],
                "layout": "force_directed",
                "style": "connectivity",
                "common_patterns": ["star", "mesh", "tree", "ring"]
            },
            DiagramType.MINDMAP: {
                "components": ["central_node", "branches", "sub_branches", "keywords"],
                "layout": "radial",
                "style": "organic",
                "common_patterns": ["balanced", "weighted", "color_coded"]
            }
        }
    
    def _initialize_layout_algorithms(self) -> Dict[str, Any]:
        """Initialize layout algorithms for different diagram types."""
        return {
            "hierarchical": {
                "direction": "top_to_bottom",
                "level_separation": 100,
                "node_separation": 50,
                "algorithm": "sugiyama"
            },
            "force_directed": {
                "spring_length": 100,
                "spring_strength": 0.1,
                "charge_strength": -30,
                "iterations": 300
            },
            "radial": {
                "center_attraction": 0.1,
                "angle_spread": 360,
                "level_separation": 150,
                "sort_by": "importance"
            },
            "temporal": {
                "time_axis": "horizontal",
                "actor_spacing": 200,
                "message_spacing": 50,
                "activation_width": 20
            }
        }
    
    async def generate_diagram(
        self,
        specification: DiagramSpecification,
        vision_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a diagram based on specification."""
        try:
            logger.info(f"Generating {specification.type.value} diagram: {specification.title}")
            
            # Validate specification
            if not specification.validate():
                raise ValueError("Invalid diagram specification")
            
            # Plan diagram layout
            layout_plan = await self._plan_layout(specification)
            
            # Generate visual elements
            elements = await self._generate_elements(specification, layout_plan)
            
            # Apply styling
            styled_elements = await self._apply_styling(elements, specification.style_guide)
            
            # Add relationships
            connected_diagram = await self._add_relationships(
                styled_elements,
                specification.relationships
            )
            
            # Generate accessibility features
            accessibility = await self._generate_accessibility(
                connected_diagram,
                specification
            )
            
            # Validate quality
            quality_metrics = await self._validate_quality(
                connected_diagram,
                specification
            )
            
            # Create final diagram
            diagram = {
                "id": specification.id,
                "type": specification.type.value,
                "title": specification.title,
                "elements": connected_diagram,
                "metadata": {
                    "dimensions": specification.dimensions,
                    "created_at": datetime.now().isoformat(),
                    "generator_version": "1.0.0"
                },
                "accessibility": accessibility,
                "quality_metrics": quality_metrics,
                "export_ready": quality_metrics.meets_threshold()
            }
            
            # Store for future reference
            self.generated_diagrams[specification.id] = diagram
            
            return diagram
            
        except Exception as e:
            logger.error(f"Failed to generate diagram: {e}")
            raise
    
    async def _plan_layout(self, specification: DiagramSpecification) -> Dict[str, Any]:
        """Plan the layout of diagram elements."""
        template = self.diagram_templates.get(specification.type, {})
        layout_type = template.get("layout", "hierarchical")
        algorithm = self.layout_algorithms.get(layout_type, {})
        
        # Analyze concepts for layout planning
        concept_hierarchy = self._analyze_concept_hierarchy(specification.concepts)
        
        # Calculate positions
        positions = await self._calculate_positions(
            specification.concepts,
            concept_hierarchy,
            algorithm,
            specification.dimensions
        )
        
        return {
            "layout_type": layout_type,
            "positions": positions,
            "hierarchy": concept_hierarchy,
            "algorithm_params": algorithm
        }
    
    def _analyze_concept_hierarchy(self, concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze concept relationships to determine hierarchy."""
        hierarchy = {
            "levels": {},
            "connections": [],
            "root_nodes": []
        }
        
        # Build dependency graph
        dependencies = {}
        for concept in concepts:
            concept_id = concept.get("id", concept.get("name"))
            deps = concept.get("dependencies", [])
            dependencies[concept_id] = deps
        
        # Find root nodes (no dependencies)
        for concept_id, deps in dependencies.items():
            if not deps:
                hierarchy["root_nodes"].append(concept_id)
        
        # Assign levels using BFS
        visited = set()
        queue = [(root, 0) for root in hierarchy["root_nodes"]]
        
        while queue:
            node, level = queue.pop(0)
            if node in visited:
                continue
            
            visited.add(node)
            if level not in hierarchy["levels"]:
                hierarchy["levels"][level] = []
            hierarchy["levels"][level].append(node)
            
            # Find children
            for concept in concepts:
                concept_id = concept.get("id", concept.get("name"))
                if node in concept.get("dependencies", []):
                    queue.append((concept_id, level + 1))
                    hierarchy["connections"].append((node, concept_id))
        
        return hierarchy
    
    async def _calculate_positions(
        self,
        concepts: List[Dict[str, Any]],
        hierarchy: Dict[str, Any],
        algorithm: Dict[str, Any],
        dimensions: Tuple[int, int]
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate positions for each concept."""
        positions = {}
        width, height = dimensions
        
        if algorithm.get("algorithm") == "sugiyama":
            # Hierarchical layout
            levels = hierarchy["levels"]
            max_level = max(levels.keys()) if levels else 0
            
            for level, nodes in levels.items():
                y = (level + 1) * height / (max_level + 2)
                x_spacing = width / (len(nodes) + 1)
                
                for i, node in enumerate(nodes):
                    x = (i + 1) * x_spacing
                    positions[node] = (x, y)
        
        elif algorithm.get("spring_length"):
            # Force-directed layout (simplified)
            # In production, this would use a proper force-directed algorithm
            import random
            for concept in concepts:
                concept_id = concept.get("id", concept.get("name"))
                positions[concept_id] = (
                    random.uniform(100, width - 100),
                    random.uniform(100, height - 100)
                )
        
        return positions
    
    async def _generate_elements(
        self,
        specification: DiagramSpecification,
        layout_plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate visual elements for the diagram."""
        elements = []
        positions = layout_plan["positions"]
        
        for concept in specification.concepts:
            concept_id = concept.get("id", concept.get("name"))
            position = positions.get(concept_id, (100, 100))
            
            element = {
                "id": f"element_{concept_id}",
                "type": self._determine_element_type(concept, specification.type),
                "position": {"x": position[0], "y": position[1]},
                "size": self._calculate_element_size(concept),
                "content": {
                    "text": concept.get("name", ""),
                    "description": concept.get("description", ""),
                    "icon": concept.get("icon", None)
                },
                "data": concept
            }
            
            elements.append(element)
        
        return elements
    
    def _determine_element_type(
        self,
        concept: Dict[str, Any],
        diagram_type: DiagramType
    ) -> str:
        """Determine the visual element type for a concept."""
        if diagram_type == DiagramType.ARCHITECTURE:
            if "layer" in concept.get("tags", []):
                return "layer_box"
            elif "service" in concept.get("tags", []):
                return "service_box"
            else:
                return "component_box"
        elif diagram_type == DiagramType.FLOWCHART:
            if concept.get("is_decision", False):
                return "diamond"
            elif concept.get("is_terminal", False):
                return "rounded_rectangle"
            else:
                return "rectangle"
        else:
            return "default_shape"
    
    def _calculate_element_size(self, concept: Dict[str, Any]) -> Dict[str, float]:
        """Calculate appropriate size for an element."""
        base_width = 150
        base_height = 80
        
        # Adjust based on content
        text_length = len(concept.get("name", ""))
        width = max(base_width, text_length * 10)
        
        # Adjust based on importance
        importance = concept.get("importance", 1.0)
        width *= importance
        height *= importance
        
        return {"width": width, "height": height}
    
    async def _apply_styling(
        self,
        elements: List[Dict[str, Any]],
        style_guide: StyleGuide
    ) -> List[Dict[str, Any]]:
        """Apply visual styling to elements."""
        styled_elements = []
        colors = style_guide.color_palette
        
        for element in elements:
            styled = element.copy()
            
            # Apply colors based on element type
            if element["type"] == "layer_box":
                styled["style"] = {
                    "fill": colors.primary,
                    "stroke": colors.secondary,
                    "strokeWidth": 2
                }
            elif element["type"] == "service_box":
                styled["style"] = {
                    "fill": colors.secondary,
                    "stroke": colors.primary,
                    "strokeWidth": 1
                }
            else:
                styled["style"] = {
                    "fill": colors.background,
                    "stroke": colors.primary,
                    "strokeWidth": 1
                }
            
            # Apply typography
            styled["style"].update({
                "fontFamily": style_guide.font_family,
                "fontSize": style_guide.font_size_base,
                "borderRadius": style_guide.border_radius
            })
            
            styled_elements.append(styled)
        
        return styled_elements
    
    async def _add_relationships(
        self,
        elements: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Add relationship connections between elements."""
        all_items = elements.copy()
        
        for rel in relationships:
            source_id = f"element_{rel['source']}"
            target_id = f"element_{rel['target']}"
            
            # Find source and target elements
            source = next((e for e in elements if e["id"] == source_id), None)
            target = next((e for e in elements if e["id"] == target_id), None)
            
            if source and target:
                connection = {
                    "id": f"connection_{source_id}_{target_id}",
                    "type": "arrow",
                    "source": source_id,
                    "target": target_id,
                    "style": {
                        "stroke": "#666",
                        "strokeWidth": 2,
                        "markerEnd": "arrow"
                    },
                    "label": rel.get("label", ""),
                    "path": self._calculate_connection_path(source, target)
                }
                
                all_items.append(connection)
        
        return all_items
    
    def _calculate_connection_path(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any]
    ) -> str:
        """Calculate SVG path for connection."""
        sx = source["position"]["x"] + source["size"]["width"] / 2
        sy = source["position"]["y"] + source["size"]["height"]
        tx = target["position"]["x"] + target["size"]["width"] / 2
        ty = target["position"]["y"]
        
        # Simple straight line for now
        # In production, this would calculate curved paths avoiding overlaps
        return f"M {sx} {sy} L {tx} {ty}"
    
    async def _generate_accessibility(
        self,
        elements: List[Dict[str, Any]],
        specification: DiagramSpecification
    ) -> AccessibilityMetadata:
        """Generate accessibility features for the diagram."""
        # Generate alt text
        alt_text = f"{specification.type.value} diagram: {specification.title}. "
        alt_text += f"Shows {len(specification.concepts)} concepts with "
        alt_text += f"{len(specification.relationships)} relationships."
        
        # Generate detailed description
        long_description = self._generate_long_description(
            specification,
            elements
        )
        
        # Generate ARIA labels
        aria_labels = {}
        for element in elements:
            if element["type"] != "arrow":
                aria_labels[element["id"]] = element["content"]["text"]
        
        return AccessibilityMetadata(
            alt_text=alt_text,
            long_description=long_description,
            aria_labels=aria_labels,
            keyboard_navigation=True,
            screen_reader_optimized=True
        )
    
    def _generate_long_description(
        self,
        specification: DiagramSpecification,
        elements: List[Dict[str, Any]]
    ) -> str:
        """Generate detailed text description of diagram."""
        description = f"This {specification.type.value} diagram titled "
        description += f"'{specification.title}' illustrates the following:\n\n"
        
        # Describe main components
        components = [e for e in elements if e["type"] != "arrow"]
        description += f"Main components ({len(components)}):\n"
        for comp in components:
            description += f"- {comp['content']['text']}"
            if comp['content']['description']:
                description += f": {comp['content']['description']}"
            description += "\n"
        
        # Describe relationships
        connections = [e for e in elements if e["type"] == "arrow"]
        if connections:
            description += f"\nRelationships ({len(connections)}):\n"
            for conn in connections:
                description += f"- {conn['source']} connects to {conn['target']}"
                if conn['label']:
                    description += f" ({conn['label']})"
                description += "\n"
        
        return description
    
    async def _validate_quality(
        self,
        diagram: List[Dict[str, Any]],
        specification: DiagramSpecification
    ) -> QualityMetrics:
        """Validate the quality of generated diagram."""
        # In production, this would use vision AI to assess quality
        # For now, use heuristic checks
        
        technical_accuracy = self._check_technical_accuracy(diagram, specification)
        visual_clarity = self._check_visual_clarity(diagram)
        educational_effectiveness = self._assess_educational_value(diagram, specification)
        accessibility_score = self._check_accessibility(diagram)
        engagement_potential = self._assess_engagement(diagram)
        
        overall_quality = (
            technical_accuracy * 0.3 +
            visual_clarity * 0.2 +
            educational_effectiveness * 0.3 +
            accessibility_score * 0.1 +
            engagement_potential * 0.1
        )
        
        metrics = QualityMetrics(
            technical_accuracy=technical_accuracy,
            visual_clarity=visual_clarity,
            educational_effectiveness=educational_effectiveness,
            accessibility_score=accessibility_score,
            engagement_potential=engagement_potential,
            overall_quality=overall_quality
        )
        
        # Add feedback
        if visual_clarity < 0.8:
            metrics.feedback.append("Some elements may be too close together")
            metrics.improvement_suggestions.append("Increase spacing between elements")
        
        if technical_accuracy < 0.9:
            metrics.feedback.append("Some relationships may be missing")
            metrics.improvement_suggestions.append("Verify all dependencies are shown")
        
        return metrics
    
    def _check_technical_accuracy(
        self,
        diagram: List[Dict[str, Any]],
        specification: DiagramSpecification
    ) -> float:
        """Check technical accuracy of the diagram."""
        # Check if all concepts are represented
        concept_ids = {c.get("id", c.get("name")) for c in specification.concepts}
        element_ids = {
            e["data"].get("id", e["data"].get("name"))
            for e in diagram
            if e["type"] != "arrow" and "data" in e
        }
        
        concept_coverage = len(element_ids.intersection(concept_ids)) / len(concept_ids)
        
        # Check if all relationships are represented
        rel_coverage = 1.0  # Simplified
        
        return (concept_coverage + rel_coverage) / 2
    
    def _check_visual_clarity(self, diagram: List[Dict[str, Any]]) -> float:
        """Check visual clarity of the diagram."""
        # Check for overlapping elements (simplified)
        elements = [e for e in diagram if e["type"] != "arrow"]
        
        if len(elements) < 2:
            return 1.0
        
        # Check spacing
        min_distance = float('inf')
        for i, e1 in enumerate(elements):
            for e2 in elements[i+1:]:
                dist = self._calculate_distance(
                    e1["position"],
                    e2["position"]
                )
                min_distance = min(min_distance, dist)
        
        # Score based on minimum distance
        if min_distance < 50:
            return 0.6
        elif min_distance < 100:
            return 0.8
        else:
            return 1.0
    
    def _calculate_distance(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
        """Calculate Euclidean distance between positions."""
        dx = pos1["x"] - pos2["x"]
        dy = pos1["y"] - pos2["y"]
        return (dx*dx + dy*dy) ** 0.5
    
    def _assess_educational_value(
        self,
        diagram: List[Dict[str, Any]],
        specification: DiagramSpecification
    ) -> float:
        """Assess educational effectiveness of the diagram."""
        score = 0.8  # Base score
        
        # Check for proper labeling
        labeled_elements = sum(
            1 for e in diagram
            if e.get("content", {}).get("text")
        )
        total_elements = len([e for e in diagram if e["type"] != "arrow"])
        
        if total_elements > 0:
            label_ratio = labeled_elements / total_elements
            score *= label_ratio
        
        # Check for annotations
        if specification.annotations:
            score += 0.1
        
        return min(score, 1.0)
    
    def _check_accessibility(self, diagram: List[Dict[str, Any]]) -> float:
        """Check accessibility features."""
        # This is simplified - in production would check WCAG compliance
        return 0.9
    
    def _assess_engagement(self, diagram: List[Dict[str, Any]]) -> float:
        """Assess engagement potential."""
        # Check for visual variety
        element_types = set(e["type"] for e in diagram)
        variety_score = min(len(element_types) / 5, 1.0)
        
        # Check for color usage (simplified)
        color_score = 0.8
        
        return (variety_score + color_score) / 2
    
    async def export_diagram(
        self,
        diagram_id: str,
        format: str = "svg",
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export diagram to specified format."""
        if diagram_id not in self.generated_diagrams:
            raise ValueError(f"Diagram {diagram_id} not found")
        
        diagram = self.generated_diagrams[diagram_id]
        
        if format == "svg":
            return self._export_to_svg(diagram, options)
        elif format == "png":
            return await self._export_to_png(diagram, options)
        elif format == "json":
            return self._export_to_json(diagram, options)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_to_svg(self, diagram: Dict[str, Any], options: Optional[Dict[str, Any]]) -> str:
        """Export diagram to SVG format."""
        width, height = diagram["metadata"]["dimensions"]
        
        svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
        
        # Add elements
        for element in diagram["elements"]:
            if element["type"] == "arrow":
                svg += f'  <path d="{element["path"]}" '
                svg += f'stroke="{element["style"]["stroke"]}" '
                svg += f'stroke-width="{element["style"]["strokeWidth"]}" '
                svg += f'fill="none" marker-end="url(#arrow)" />\n'
            else:
                x = element["position"]["x"]
                y = element["position"]["y"]
                w = element["size"]["width"]
                h = element["size"]["height"]
                
                svg += f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" '
                svg += f'fill="{element["style"]["fill"]}" '
                svg += f'stroke="{element["style"]["stroke"]}" '
                svg += f'stroke-width="{element["style"]["strokeWidth"]}" '
                svg += f'rx="{element["style"]["borderRadius"]}" />\n'
                
                # Add text
                text = element["content"]["text"]
                svg += f'  <text x="{x + w/2}" y="{y + h/2}" '
                svg += f'text-anchor="middle" dominant-baseline="middle">{text}</text>\n'
        
        svg += '</svg>'
        return svg
    
    async def _export_to_png(self, diagram: Dict[str, Any], options: Optional[Dict[str, Any]]) -> str:
        """Export diagram to PNG format."""
        # In production, this would use a proper rendering engine
        # For now, return a placeholder
        return "PNG export not implemented"
    
    def _export_to_json(self, diagram: Dict[str, Any], options: Optional[Dict[str, Any]]) -> str:
        """Export diagram to JSON format."""
        import json
        return json.dumps(diagram, indent=2)
