"""
Certify Studio Manim Extensions

Enhanced Manim framework for enterprise-grade certification content generation.
Provides specialized scenes, animations, and tools for creating professional
cloud architecture and technical education content.
"""

from .scenes.certification_scene import CertificationScene
from .scenes.interactive_scene import InteractiveLearningScene
from .scenes.accessible_scene import AccessibleScene
from .scenes.multi_export_scene import MultiExportScene
from .scenes.optimized_scene import OptimizedCertificationScene

from .icons.icon_library import OfficialIconLibrary
from .animations.aws_animations import AWSArchitectureAnimations
from .animations.azure_animations import AzureArchitectureAnimations
from .animations.gcp_animations import GCPArchitectureAnimations

from .themes.aws_theme import AWSCertificationTheme
from .themes.azure_theme import AzureCertificationTheme
from .themes.gcp_theme import GCPCertificationTheme

__version__ = "0.1.0"
__author__ = "Certify Studio Team"

__all__ = [
    # Scenes
    "CertificationScene",
    "InteractiveLearningScene", 
    "AccessibleScene",
    "MultiExportScene",
    "OptimizedCertificationScene",
    
    # Icons and Assets
    "OfficialIconLibrary",
    
    # Animations
    "AWSArchitectureAnimations",
    "AzureArchitectureAnimations", 
    "GCPArchitectureAnimations",
    
    # Themes
    "AWSCertificationTheme",
    "AzureCertificationTheme",
    "GCPCertificationTheme",
]
