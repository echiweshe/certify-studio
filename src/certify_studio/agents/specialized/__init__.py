"""
Specialized agents module.

This module contains all specialized agents for various tasks.
"""

# Import all specialized agents for easy access
from .pedagogical.agent import PedagogicalReasoningAgent
from .content_generation.agent import ContentGenerationAgent
from .domain_extraction.agent import DomainExtractionAgent
from .quality_assurance.agent import QualityAssuranceAgent

__all__ = [
    "PedagogicalReasoningAgent",
    "ContentGenerationAgent",
    "DomainExtractionAgent",
    "QualityAssuranceAgent",
]
