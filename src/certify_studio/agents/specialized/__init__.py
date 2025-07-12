"""
Specialized agents for Certify Studio.

This module contains domain-specific agents that handle specialized tasks:
- PedagogicalReasoningAgent: Optimizes learning paths and educational content
- ContentGenerationAgent: Creates diagrams, animations, and interactive content
- QualityAssuranceAgent: Validates technical accuracy and educational effectiveness
"""

from .pedagogical import PedagogicalReasoningAgent

__all__ = [
    "PedagogicalReasoningAgent",
]
