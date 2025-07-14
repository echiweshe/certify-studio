"""
Audio Processing Component - Main Entry Point
Automatically selects the appropriate implementation based on Python version
"""

from .audio_processor_wrapper import (
    AudioProcessor,
    AudioFormat,
    AudioFeatures,
    create_audio_processor
)

__all__ = ['AudioProcessor', 'AudioFormat', 'AudioFeatures', 'create_audio_processor']
