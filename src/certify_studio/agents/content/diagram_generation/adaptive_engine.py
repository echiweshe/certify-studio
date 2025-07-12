"""
Adaptive diagram optimization engine.
"""

from typing import Dict, List, Any, Optional, Set

from .models import Diagram, DiagramElement, DiagramEdge


class AdaptiveDiagramEngine:
    """Engine that adapts diagrams based on viewer feedback and understanding."""
    
    def __init__(self):
        self.feedback_history = []
        self.optimization_rules = self._initialize_optimization_rules()
    
    def _initialize_optimization_rules(self) -> Dict[str, Any]:
        """Initialize rules for diagram optimization."""
        
        return {
            "clarity": {
                "max_elements_visible": 15,
                "min_element_spacing": 0.05,
                "label_overlap_threshold": 0.1
            },
            "complexity": {
                "progressive_disclosure": True,
                "initial_detail_level": "medium",
                "max_edge_crossings": 5
            },
            "performance": {
                "max_animation_elements": 20,
                "simplify_threshold": 50  # Number of elements
            }
        }
    
    async def optimize_diagram(
        self,
        diagram: Diagram,
        viewer_profile: Optional[Dict[str, Any]] = None
    ) -> Diagram:
        """Optimize diagram based on viewer profile and best practices."""
        
        # Simplify if too complex
        if len(diagram.elements) > self.optimization_rules["performance"]["simplify_threshold"]:
            diagram = await self._simplify_diagram(diagram)
        
        # Reduce edge crossings
        if len(diagram.edges) > 10:
            diagram = await self._minimize_edge_crossings(diagram)
        
        # Adjust for viewer expertise
        if viewer_profile:
            diagram = await self._adjust_for_viewer(diagram, viewer_profile)
        
        # Ensure labels don't overlap
        diagram = await self._prevent_label_overlap(diagram)
        
        return diagram
    
    async def _simplify_diagram(
        self,
        diagram: Diagram
    ) -> Diagram:
        """Simplify complex diagram through clustering or filtering."""
        
        # Group related elements
        clusters = self._identify_clusters(diagram)
        
        # Create simplified elements for clusters
        simplified_elements = {}
        for cluster_id, element_ids in clusters.items():
            if len(element_ids) > 3:
                # Create group element
                cluster_elements = [diagram.elements[eid] for eid in element_ids if eid in diagram.elements]
                
                # Calculate cluster center
                center_x = sum(el.position["x"] for el in cluster_elements) / len(cluster_elements)
                center_y = sum(el.position["y"] for el in cluster_elements) / len(cluster_elements)
                
                group_element = DiagramElement(
                    id=f"cluster_{cluster_id}",
                    element_type="group",
                    label=f"Group: {cluster_id}",
                    position={"x": center_x, "y": center_y},
                    size={"width": 0.2, "height": 0.15},
                    style={
                        "fill": "rgba(100, 100, 100, 0.1)",
                        "stroke": "#666",
                        "stroke_width": 2,
                        "stroke_dash": "5,5"
                    },
                    children=element_ids
                )
                
                simplified_elements[group_element.id] = group_element
            else:
                # Keep individual elements
                for eid in element_ids:
                    if eid in diagram.elements:
                        simplified_elements[eid] = diagram.elements[eid]
        
        # Update diagram
        diagram.elements = simplified_elements
        
        # Filter edges to only show between clusters
        simplified_edges = []
        for edge in diagram.edges:
            source_cluster = self._find_element_cluster(edge.source_id, clusters)
            target_cluster = self._find_element_cluster(edge.target_id, clusters)
            
            if source_cluster != target_cluster:
                # Create edge between clusters
                new_edge = DiagramEdge(
                    id=edge.id,
                    source_id=f"cluster_{source_cluster}" if source_cluster else edge.source_id,
                    target_id=f"cluster_{target_cluster}" if target_cluster else edge.target_id,
                    edge_type=edge.edge_type,
                    label=edge.label,
                    style=edge.style
                )
                simplified_edges.append(new_edge)
        
        diagram.edges = simplified_edges
        
        return diagram
    
    def _identify_clusters(self, diagram: Diagram) -> Dict[str, List[str]]:
        """Identify clusters of related elements."""
        
        clusters = {}
        
        # Simple clustering based on position proximity
        grid_size = 0.2  # Grid cell size
        
        for element in diagram.elements.values():
            grid_x = int(element.position["x"] / grid_size)
            grid_y = int(element.position["y"] / grid_size)
            cluster_key = f"{grid_x}_{grid_y}"
            
            if cluster_key not in clusters:
                clusters[cluster_key] = []
            clusters[cluster_key].append(element.id)
        
        return clusters
    
    def _find_element_cluster(self, element_id: str, clusters: Dict[str, List[str]]) -> Optional[str]:
        """Find which cluster an element belongs to."""
        
        for cluster_id, element_ids in clusters.items():
            if element_id in element_ids:
                return cluster_id
        return None
    
    async def _minimize_edge_crossings(self, diagram: Diagram) -> Diagram:
        """Minimize edge crossings through layout optimization."""
        
        # This would implement edge crossing minimization algorithms
        # For now, we'll just mark crossing edges with a different style
        
        crossings = self._detect_edge_crossings(diagram.edges, diagram.elements)
        
        for edge in diagram.edges:
            if edge.id in crossings:
                edge.style["stroke_dash"] = "3,3"
                edge.style["opacity"] = 0.7
        
        return diagram
    
    def _detect_edge_crossings(self, edges: List[DiagramEdge], elements: Dict[str, DiagramElement]) -> Set[str]:
        """Detect which edges cross each other."""
        
        crossing_edges = set()
        
        # Simple crossing detection (would be more sophisticated in production)
        for i, edge1 in enumerate(edges):
            for j, edge2 in enumerate(edges[i+1:], i+1):
                if self._edges_intersect(edge1, edge2, elements):
                    crossing_edges.add(edge1.id)
                    crossing_edges.add(edge2.id)
        
        return crossing_edges
    
    def _edges_intersect(self, edge1: DiagramEdge, edge2: DiagramEdge, elements: Dict[str, DiagramElement]) -> bool:
        """Check if two edges intersect."""
        
        # Get positions
        if (edge1.source_id not in elements or edge1.target_id not in elements or
            edge2.source_id not in elements or edge2.target_id not in elements):
            return False
        
        # Simple check - would implement proper line intersection in production
        return False
    
    async def _adjust_for_viewer(self, diagram: Diagram, viewer_profile: Dict[str, Any]) -> Diagram:
        """Adjust diagram based on viewer expertise and preferences."""
        
        expertise_level = viewer_profile.get("expertise", "intermediate")
        
        if expertise_level == "beginner":
            # Simplify for beginners
            for element in diagram.elements.values():
                # Use simpler labels
                element.label = self._simplify_label(element.label)
                
                # Add more descriptive metadata
                if "description" not in element.metadata:
                    element.metadata["description"] = f"This is {element.label}"
            
            # Reduce visual complexity
            for edge in diagram.edges:
                edge.style["stroke_width"] = 2  # Uniform width
                if "animation" in edge.style:
                    del edge.style["animation"]  # Remove animations
        
        elif expertise_level == "expert":
            # Add more detail for experts
            for element in diagram.elements.values():
                # Show technical details
                if "concept_type" in element.metadata:
                    element.label += f" ({element.metadata['concept_type']})"
        
        return diagram
    
    def _simplify_label(self, label: str) -> str:
        """Simplify technical labels for beginners."""
        
        simplifications = {
            "API Gateway": "API Entry",
            "Load Balancer": "Traffic Distributor",
            "Lambda Function": "Code Runner",
            "DynamoDB": "Database",
            "S3 Bucket": "File Storage"
        }
        
        return simplifications.get(label, label)
    
    async def _prevent_label_overlap(self, diagram: Diagram) -> Diagram:
        """Adjust label positions to prevent overlap."""
        
        # Sort elements by position
        sorted_elements = sorted(
            diagram.elements.values(),
            key=lambda e: (e.position["y"], e.position["x"])
        )
        
        # Check for overlaps and adjust
        for i, element1 in enumerate(sorted_elements):
            for element2 in sorted_elements[i+1:]:
                if self._labels_overlap(element1, element2):
                    # Adjust position slightly
                    element2.position["y"] += 0.05
        
        return diagram
    
    def _labels_overlap(self, el1: DiagramElement, el2: DiagramElement) -> bool:
        """Check if two element labels overlap."""
        
        # Simple bounding box check
        distance_x = abs(el1.position["x"] - el2.position["x"])
        distance_y = abs(el1.position["y"] - el2.position["y"])
        
        min_distance_x = (el1.size["width"] + el2.size["width"]) / 2
        min_distance_y = (el1.size["height"] + el2.size["height"]) / 2
        
        return distance_x < min_distance_x and distance_y < min_distance_y
