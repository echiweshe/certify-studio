"""
Certify Studio - AI-Powered Certification Content Generation Platform

This package provides the core functionality for generating enterprise-grade
certification training content using advanced AI agents and Manim animations.
"""

__version__ = "0.1.0"
__author__ = "Certify Studio Team"
__email__ = "team@certifystudio.com"

# Main application imports
from .main import app, create_application
from .config import settings, get_settings

__all__ = [
    "app",
    "create_application", 
    "settings",
    "get_settings"
]
