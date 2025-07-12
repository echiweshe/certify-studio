"""
Certification-specific constants and configurations for Manim extensions.
"""

from enum import Enum
from typing import Dict, Any
import numpy as np


class CertificationProvider(Enum):
    """Supported certification providers"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    KUBERNETES = "k8s"
    GENERAL = "general"


class CertificationLevel(Enum):
    """Certification difficulty levels"""
    FOUNDATIONAL = "foundational"
    ASSOCIATE = "associate"
    PROFESSIONAL = "professional"
    EXPERT = "expert"
    SPECIALTY = "specialty"


# Color schemes for different providers
AWS_COLORS = {
    "primary": "#FF9900",  # AWS Orange
    "secondary": "#232F3E",  # AWS Dark Blue
    "compute": "#FF9900",  # Orange for compute services
    "storage": "#3F48CC",  # Blue for storage services
    "database": "#C925D1",  # Purple for database services
    "networking": "#4B612C",  # Green for networking
    "security": "#DD344C",  # Red for security services
    "analytics": "#8C4FFF",  # Purple for analytics
    "ai_ml": "#01A88D",  # Teal for AI/ML services
    "vpc_blue": "#4B9CD3",
    "public_subnet": "#90EE90",
    "private_subnet": "#FFB6C1",
    "secure_flow": "#00FF00",
    "database_flow": "#0000FF",
    "generic_flow": "#808080",
    "background": "#FFFFFF",
    "text": "#232F3E",
    "border": "#CCCCCC"
}

AZURE_COLORS = {
    "primary": "#0078D4",  # Azure Blue
    "secondary": "#0F1419",  # Azure Dark
    "compute": "#0078D4",  # Blue for compute
    "storage": "#00BCF2",  # Light Blue for storage
    "database": "#FF6C00",  # Orange for database
    "networking": "#7FBA00",  # Green for networking
    "security": "#E74856",  # Red for security
    "analytics": "#A4262C",  # Dark Red for analytics
    "ai_ml": "#00D4FF",  # Cyan for AI/ML
    "background": "#FFFFFF",
    "text": "#0F1419",
    "border": "#E1E1E1"
}

GCP_COLORS = {
    "primary": "#4285F4",  # Google Blue
    "secondary": "#34A853",  # Google Green
    "red": "#EA4335",  # Google Red
    "yellow": "#FBBC04",  # Google Yellow
    "compute": "#4285F4",  # Blue for compute
    "storage": "#34A853",  # Green for storage
    "database": "#EA4335",  # Red for database
    "networking": "#FBBC04",  # Yellow for networking
    "security": "#9AA0A6",  # Gray for security
    "analytics": "#FF6D01",  # Orange for analytics
    "ai_ml": "#0F9D58",  # Green for AI/ML
    "background": "#FFFFFF",
    "text": "#202124",
    "border": "#DADCE0"
}

KUBERNETES_COLORS = {
    "primary": "#326CE5",  # Kubernetes Blue
    "secondary": "#FFFFFF",
    "workloads": "#326CE5",
    "services": "#00D4AA",
    "config": "#FF6B35",
    "storage": "#FFE66D",
    "security": "#FF3366",
    "background": "#FFFFFF",
    "text": "#1A1A1A",
    "border": "#E0E0E0"
}

# Animation timing constants
ANIMATION_TIMING = {
    "fast": 0.5,
    "normal": 1.0,
    "slow": 2.0,
    "diagram_build": 3.0,
    "explanation": 5.0,
    "transition": 1.5
}

# Standard dimensions for certification content
DIMENSIONS = {
    "video_width": 1920,
    "video_height": 1080,
    "presentation_width": 1920,
    "presentation_height": 1080,
    "web_width": 1200,
    "web_height": 800,
    "icon_size": 64,
    "large_icon_size": 128,
    "small_icon_size": 32
}

# Text styles for different content types
TEXT_STYLES = {
    "title": {
        "font_size": 48,
        "font": "Helvetica",
        "weight": "bold"
    },
    "subtitle": {
        "font_size": 36,
        "font": "Helvetica",
        "weight": "normal"
    },
    "body": {
        "font_size": 24,
        "font": "Helvetica",
        "weight": "normal"
    },
    "caption": {
        "font_size": 18,
        "font": "Helvetica",
        "weight": "normal"
    },
    "code": {
        "font_size": 20,
        "font": "Monaco",
        "weight": "normal"
    }
}

# Layout configurations
LAYOUT_CONFIG = {
    "margin": 0.5,
    "spacing": 1.0,
    "icon_spacing": 1.5,
    "group_padding": 0.3,
    "title_offset": 2.0,
    "legend_position": "bottom_right"
}

# Export format configurations
EXPORT_FORMATS = {
    "mp4": {
        "codec": "libx264",
        "fps": 30,
        "quality": "high",
        "audio": True
    },
    "webm": {
        "codec": "libvpx-vp9",
        "fps": 30,
        "quality": "high",
        "audio": True
    },
    "gif": {
        "fps": 15,
        "optimize": True,
        "loop": True
    },
    "svg": {
        "optimize": True,
        "pretty": True
    },
    "png": {
        "dpi": 300,
        "transparent": True
    }
}

# Accessibility configurations
ACCESSIBILITY_CONFIG = {
    "min_contrast_ratio": 4.5,  # WCAG AA standard
    "focus_indicator_width": 3,
    "keyboard_navigation": True,
    "screen_reader_compatible": True,
    "caption_timing": {
        "min_duration": 2.0,
        "max_chars_per_second": 20,
        "pause_duration": 0.5
    }
}

# Quality control thresholds
QUALITY_THRESHOLDS = {
    "animation_fps_min": 24,
    "video_bitrate_min": 2000,  # kbps
    "audio_quality_min": 128,   # kbps
    "compression_ratio_max": 0.8,
    "file_size_mb_max": 100,
    "render_time_max": 300      # seconds
}

# Certification-specific configurations
CERTIFICATION_CONFIG = {
    "aws": {
        "exam_codes": [
            "CLF-C02",  # Cloud Practitioner
            "SAA-C03",  # Solutions Architect Associate
            "SOA-C02",  # SysOps Administrator
            "DVA-C02",  # Developer Associate
            "SAP-C02",  # Solutions Architect Professional
            "DOP-C02",  # DevOps Engineer Professional
        ],
        "domains_per_exam": {
            "CLF-C02": 4,
            "SAA-C03": 4,
            "SOA-C02": 6,
            "DVA-C02": 4,
            "SAP-C02": 4,
            "DOP-C02": 5
        }
    },
    "azure": {
        "exam_codes": [
            "AZ-900",   # Azure Fundamentals
            "AZ-104",   # Azure Administrator
            "AZ-204",   # Azure Developer
            "AZ-303",   # Azure Architect Technologies
            "AZ-304",   # Azure Architect Design
        ]
    },
    "gcp": {
        "exam_codes": [
            "ACE",      # Associate Cloud Engineer
            "PCA",      # Professional Cloud Architect
            "PDE",      # Professional Data Engineer
            "PME",      # Professional Machine Learning Engineer
        ]
    }
}

# Error handling configurations
ERROR_CONFIG = {
    "max_retries": 3,
    "retry_delay": 1.0,
    "timeout": 30.0,
    "fallback_enabled": True,
    "error_logging": True
}
