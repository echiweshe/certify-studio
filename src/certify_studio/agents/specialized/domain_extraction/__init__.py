"""
Domain extraction agents module.

Contains agents for extracting domain knowledge and concepts.
"""

from .agent import DomainExtractionAgent
from .graphrag_extractor import domain_extractor as GraphRAGExtractor

__all__ = ["DomainExtractionAgent"]
