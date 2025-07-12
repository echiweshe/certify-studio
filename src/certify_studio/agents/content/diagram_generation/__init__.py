"""
Diagram Generation Agent - Dynamic visual diagram creation.

This module creates intelligent, context-aware diagrams that adapt to the
content being visualized. It doesn't rely on templates but instead reasons
about the best visual representation for each concept.
"""

from .agent import DiagramGenerationAgent
from .models import (
    DiagramType, 
    LayoutAlgorithm, 
    DiagramElement, 
    DiagramEdge, 
    DiagramLayer, 
    Diagram
)
from .layout_engine import DiagramLayoutEngine
from .strategy import IntelligentDiagramStrategy
from .adaptive_engine import AdaptiveDiagramEngine

__all__ = [
    'DiagramGenerationAgent',
    'DiagramType',
    'LayoutAlgorithm',
    'DiagramElement',
    'DiagramEdge',
    'DiagramLayer',
    'Diagram',
    'DiagramLayoutEngine',
    'IntelligentDiagramStrategy',
    'AdaptiveDiagramEngine'
]
