"""
Layout algorithms for diagram positioning.
"""

from typing import Dict, List, Any, Optional
import math

from .models import DiagramElement, DiagramEdge, LayoutAlgorithm


class DiagramLayoutEngine:
    """Engine for calculating optimal layouts."""
    
    def __init__(self):
        self.algorithms = {
            LayoutAlgorithm.FORCE_DIRECTED: self._force_directed_layout,
            LayoutAlgorithm.HIERARCHICAL: self._hierarchical_layout,
            LayoutAlgorithm.CIRCULAR: self._circular_layout,
            LayoutAlgorithm.GRID: self._grid_layout,
            LayoutAlgorithm.RADIAL: self._radial_layout,
            LayoutAlgorithm.LAYERED: self._layered_layout
        }
    
    async def calculate_layout(
        self,
        elements: List[DiagramElement],
        edges: List[DiagramEdge],
        algorithm: LayoutAlgorithm,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Calculate positions for all elements."""
        
        if algorithm in self.algorithms:
            return await self.algorithms[algorithm](elements, edges, constraints)
        else:
            # Default to force-directed
            return await self._force_directed_layout(elements, edges, constraints)
    
    async def _force_directed_layout(
        self,
        elements: List[DiagramElement],
        edges: List[DiagramEdge],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Force-directed graph layout algorithm."""
        
        positions = {}
        
        # Initialize positions randomly
        for i, element in enumerate(elements):
            angle = 2 * math.pi * i / len(elements)
            radius = 0.3
            positions[element.id] = {
                "x": 0.5 + radius * math.cos(angle),
                "y": 0.5 + radius * math.sin(angle)
            }
        
        # Simulate forces
        iterations = 50
        for _ in range(iterations):
            forces = {el.id: {"x": 0, "y": 0} for el in elements}
            
            # Repulsive forces between all nodes
            for i, el1 in enumerate(elements):
                for j, el2 in enumerate(elements):
                    if i >= j:
                        continue
                    
                    dx = positions[el2.id]["x"] - positions[el1.id]["x"]
                    dy = positions[el2.id]["y"] - positions[el1.id]["y"]
                    distance = max(math.sqrt(dx*dx + dy*dy), 0.01)
                    
                    # Repulsive force
                    force = 0.01 / (distance * distance)
                    forces[el1.id]["x"] -= force * dx / distance
                    forces[el1.id]["y"] -= force * dy / distance
                    forces[el2.id]["x"] += force * dx / distance
                    forces[el2.id]["y"] += force * dy / distance
            
            # Attractive forces along edges
            for edge in edges:
                if edge.source_id in positions and edge.target_id in positions:
                    dx = positions[edge.target_id]["x"] - positions[edge.source_id]["x"]
                    dy = positions[edge.target_id]["y"] - positions[edge.source_id]["y"]
                    distance = max(math.sqrt(dx*dx + dy*dy), 0.01)
                    
                    # Attractive force
                    force = distance * 0.1
                    forces[edge.source_id]["x"] += force * dx / distance
                    forces[edge.source_id]["y"] += force * dy / distance
                    forces[edge.target_id]["x"] -= force * dx / distance
                    forces[edge.target_id]["y"] -= force * dy / distance
            
            # Apply forces
            for el_id in positions:
                positions[el_id]["x"] += forces[el_id]["x"] * 0.1
                positions[el_id]["y"] += forces[el_id]["y"] * 0.1
                
                # Keep within bounds
                positions[el_id]["x"] = max(0.1, min(0.9, positions[el_id]["x"]))
                positions[el_id]["y"] = max(0.1, min(0.9, positions[el_id]["y"]))
        
        return positions
    
    async def _hierarchical_layout(
        self,
        elements: List[DiagramElement],
        edges: List[DiagramEdge],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Hierarchical/tree layout algorithm."""
        
        positions = {}
        
        # Build adjacency information
        children = {el.id: [] for el in elements}
        parents = {el.id: [] for el in elements}
        
        for edge in edges:
            if edge.source_id in children and edge.target_id in children:
                children[edge.source_id].append(edge.target_id)
                parents[edge.target_id].append(edge.source_id)
        
        # Find root nodes (no parents)
        roots = [el.id for el in elements if not parents[el.id]]
        if not roots and elements:
            roots = [elements[0].id]  # Use first element as root if no clear root
        
        # Calculate levels
        levels = {}
        visited = set()
        
        def assign_level(node_id, level):
            if node_id in visited:
                return
            visited.add(node_id)
            levels[node_id] = level
            for child in children[node_id]:
                assign_level(child, level + 1)
        
        for root in roots:
            assign_level(root, 0)
        
        # Group by level
        level_groups = {}
        for el in elements:
            level = levels.get(el.id, 0)
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(el.id)
        
        # Position nodes
        max_level = max(level_groups.keys()) if level_groups else 0
        
        for level, nodes in level_groups.items():
            y = 0.1 + (level / (max_level + 1)) * 0.8 if max_level > 0 else 0.5
            
            for i, node_id in enumerate(nodes):
                x = 0.1 + (i / (len(nodes) + 1)) * 0.8 if len(nodes) > 1 else 0.5
                positions[node_id] = {"x": x, "y": y}
        
        return positions
    
    async def _circular_layout(
        self,
        elements: List[DiagramElement],
        edges: List[DiagramEdge],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Circular layout algorithm."""
        
        positions = {}
        center = {"x": 0.5, "y": 0.5}
        radius = 0.35
        
        for i, element in enumerate(elements):
            angle = 2 * math.pi * i / len(elements)
            positions[element.id] = {
                "x": center["x"] + radius * math.cos(angle),
                "y": center["y"] + radius * math.sin(angle)
            }
        
        return positions
    
    async def _grid_layout(
        self,
        elements: List[DiagramElement],
        edges: List[DiagramEdge],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Grid layout algorithm."""
        
        positions = {}
        
        # Calculate grid dimensions
        n = len(elements)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        
        # Position elements in grid
        for i, element in enumerate(elements):
            row = i // cols
            col = i % cols
            
            x = 0.1 + (col / (cols + 1)) * 0.8 if cols > 1 else 0.5
            y = 0.1 + (row / (rows + 1)) * 0.8 if rows > 1 else 0.5
            
            positions[element.id] = {"x": x, "y": y}
        
        return positions
    
    async def _radial_layout(
        self,
        elements: List[DiagramElement],
        edges: List[DiagramEdge],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Radial layout with central node."""
        
        positions = {}
        
        if not elements:
            return positions
        
        # Find most connected node as center
        connection_count = {el.id: 0 for el in elements}
        for edge in edges:
            if edge.source_id in connection_count:
                connection_count[edge.source_id] += 1
            if edge.target_id in connection_count:
                connection_count[edge.target_id] += 1
        
        center_id = max(connection_count, key=connection_count.get)
        positions[center_id] = {"x": 0.5, "y": 0.5}
        
        # Position other nodes in rings
        remaining = [el for el in elements if el.id != center_id]
        
        if remaining:
            rings = min(3, math.ceil(len(remaining) / 8))  # Max 3 rings
            
            for i, element in enumerate(remaining):
                ring = i % rings
                angle_in_ring = (i // rings) * 2 * math.pi / math.ceil(len(remaining) / rings)
                radius = 0.15 + ring * 0.15
                
                positions[element.id] = {
                    "x": 0.5 + radius * math.cos(angle_in_ring),
                    "y": 0.5 + radius * math.sin(angle_in_ring)
                }
        
        return positions
    
    async def _layered_layout(
        self,
        elements: List[DiagramElement],
        edges: List[DiagramEdge],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Layered layout for complex diagrams."""
        
        # Group elements by type or metadata
        layers = {}
        
        for element in elements:
            layer_key = element.metadata.get("layer", "default")
            if layer_key not in layers:
                layers[layer_key] = []
            layers[layer_key].append(element)
        
        positions = {}
        layer_height = 0.8 / max(len(layers), 1)
        
        for i, (layer_name, layer_elements) in enumerate(layers.items()):
            y_base = 0.1 + i * layer_height + layer_height / 2
            
            for j, element in enumerate(layer_elements):
                x = 0.1 + (j / (len(layer_elements) + 1)) * 0.8 if len(layer_elements) > 1 else 0.5
                positions[element.id] = {"x": x, "y": y_base}
        
        return positions
