"""
Content Generation Agent Module.

This module provides all components for generating high-quality educational content
including diagrams, animations, interactive elements, with full accessibility and
quality validation.
"""

from .agent import ContentGenerationAgent
from .models import (
    ContentGenerationRequest,
    ContentPiece,
    ContentType,
    MediaType,
    InteractionType,
    QualityMetrics,
    ContentMetadata,
    DiagramElement,
    AnimationSequence,
    InteractiveElement
)
from .diagram_generator import DiagramGenerator
from .animation_engine import AnimationEngine
from .interactive_builder import InteractiveBuilder
from .style_manager import StyleManager, StyleGuide, DomainStyle
from .accessibility import AccessibilityManager, AccessibilityStandard
from .quality_validator import QualityValidator

__all__ = [
    # Main agent
    "ContentGenerationAgent",
    
    # Models
    "ContentGenerationRequest",
    "ContentPiece",
    "ContentType",
    "MediaType",
    "InteractionType",
    "QualityMetrics",
    "ContentMetadata",
    "DiagramElement",
    "AnimationSequence",
    "InteractiveElement",
    
    # Modules
    "DiagramGenerator",
    "AnimationEngine", 
    "InteractiveBuilder",
    "StyleManager",
    "StyleGuide",
    "DomainStyle",
    "AccessibilityManager",
    "AccessibilityStandard",
    "QualityValidator"
]
