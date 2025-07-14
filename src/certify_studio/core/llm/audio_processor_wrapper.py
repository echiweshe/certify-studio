"""
Audio Processing Component - Python 3.13 Compatible Wrapper
Redirects to the enterprise-grade audio processor
"""

import sys
import logging

logger = logging.getLogger(__name__)

# Check Python version
python_version = sys.version_info

if python_version >= (3, 13):
    logger.info("Python 3.13+ detected, using enterprise audio processor without librosa")
    from certify_studio.media.audio import (
        EnterpriseAudioProcessor as AudioProcessor,
        AudioFormat,
        AudioFeatures,
        create_audio_processor
    )
else:
    logger.info(f"Python {python_version.major}.{python_version.minor} detected, using original audio processor")
    try:
        from .audio_processor_original import AudioProcessor
        from certify_studio.media.audio import AudioFormat, AudioFeatures, create_audio_processor
    except ImportError:
        logger.warning("Original audio processor not available, falling back to enterprise version")
        from certify_studio.media.audio import (
            EnterpriseAudioProcessor as AudioProcessor,
            AudioFormat,
            AudioFeatures,
            create_audio_processor
        )

__all__ = ['AudioProcessor', 'AudioFormat', 'AudioFeatures', 'create_audio_processor']
