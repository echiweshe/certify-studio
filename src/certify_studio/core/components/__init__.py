"""
Component Library Module

This module provides the core component library system that enables
rapid content assembly through high-quality, reusable components.
"""

from .component_library import (
    ComponentLibrary,
    AnimationComponent,
    ComponentMetadata,
    ComponentStyle,
    AnimationParameters,
    AnimationPatterns,
    ComponentType,
    Provider,
    AnimationType
)

__all__ = [
    "ComponentLibrary",
    "AnimationComponent",
    "ComponentMetadata",
    "ComponentStyle",
    "AnimationParameters",
    "AnimationPatterns",
    "ComponentType",
    "Provider",
    "AnimationType"
]
