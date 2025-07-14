"""
Core LLM integration module with full multimodal capabilities.
"""

from .multimodal_llm import MultimodalLLM, LLMProvider
# Delay import to avoid circular dependency
# from .vision_processor import VisionProcessor
# Use Python 3.13 compatible audio processor
try:
    from .audio_processor_py313 import AudioProcessor
except ImportError:
    # Fallback to original if needed
    from .audio_processor import AudioProcessor
from .prompt_manager import PromptManager, PromptType
from .response_parser import ResponseParser

__all__ = [
    'MultimodalLLM',
    'LLMProvider',
    # 'VisionProcessor',  # Temporarily disabled due to circular import
    'AudioProcessor',
    'PromptManager',
    'PromptType',
    'ResponseParser'
]
