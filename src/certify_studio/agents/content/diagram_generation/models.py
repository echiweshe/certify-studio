"""
Data models for diagram generation.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class DiagramType(Enum):
    """Types of diagrams that can be generated."""
    ARCHITECTURE = "architecture"
    FLOW = "flow"
    SEQUENCE = "sequence"
    NETWORK = "network"
    HIERARCHY = "hierarchy"
    COMPONENT = "component"
    STATE = "state"
    DEPLOYMENT = "deployment"
    DATA_FLOW = "data_flow"
    SECURITY = "security"


class LayoutAlgorithm(Enum):
    """Layout algorithms for positioning elements."""
    FORCE_DIRECTED = "force_directed"
    HIERARCHICAL = "hierarchical"
    CIRCULAR = "circular"
    GRID = "grid"
    RADIAL = "radial"
    LAYERED = "layered"
    ORGANIC = "organic"
    ORTHOGONAL = "orthogonal"


@dataclass
class DiagramElement:
    """A single element in a diagram."""
    id: str
    element_type: str  # "node", "edge", "group", "annotation"
    label: str
    position: Dict[str, float]  # {"x": 0.5, "y": 0.5}
    size: Dict[str, float]  # {"width": 0.1, "height": 0.1}
    style: Dict[str, Any]  # Visual styling properties
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)  # For grouped elements
    connections: List[str] = field(default_factory=list)  # Connected element IDs


@dataclass
class DiagramEdge:
    """An edge/connection in a diagram."""
    id: str
    source_id: str
    target_id: str
    edge_type: str  # "data_flow", "dependency", "association", etc.
    label: Optional[str] = None
    style: Dict[str, Any] = field(default_factory=dict)
    routing: str = "straight"  # "straight", "orthogonal", "curved"
    waypoints: List[Dict[str, float]] = field(default_factory=list)


@dataclass
class DiagramLayer:
    """A layer in a multi-layered diagram."""
    id: str
    name: str
    z_index: int
    elements: List[str]  # Element IDs in this layer
    visibility: bool = True
    opacity: float = 1.0


@dataclass
class Diagram:
    """A complete diagram specification."""
    id: str
    title: str
    type: DiagramType
    elements: Dict[str, DiagramElement]
    edges: List[DiagramEdge]
    layers: List[DiagramLayer]
    layout: Dict[str, Any]  # Layout configuration
    viewport: Dict[str, float]  # {"width": 1.0, "height": 1.0}
    style_theme: Dict[str, Any]
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    interactions: Dict[str, Any] = field(default_factory=dict)
