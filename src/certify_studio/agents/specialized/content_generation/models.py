"""
Data models for content generation system.
"""

from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class MediaType(Enum):
    """Types of media content."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    ANIMATION = "animation"
    INTERACTIVE = "interactive"
    THREE_D = "3d"


class ContentType(Enum):
    """Types of educational content."""
    DIAGRAM = "diagram"
    ANIMATION = "animation"
    INTERACTIVE = "interactive"
    HYBRID = "hybrid"
    INFOGRAPHIC = "infographic"
    SIMULATION = "simulation"
    QUIZ = "quiz"
    LAB = "lab"


class DiagramType(Enum):
    """Types of diagrams."""
    ARCHITECTURE = "architecture"
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    NETWORK = "network"
    HIERARCHY = "hierarchy"
    TIMELINE = "timeline"
    COMPARISON = "comparison"
    MINDMAP = "mindmap"


class AnimationType(Enum):
    """Types of animations."""
    CONCEPT_REVEAL = "concept_reveal"
    PROCESS_FLOW = "process_flow"
    TRANSFORMATION = "transformation"
    COMPARISON = "comparison"
    BUILD_UP = "build_up"
    INTERACTION = "interaction"
    SIMULATION = "simulation"


class InteractionType(Enum):
    """Types of interactive elements."""
    CLICK_REVEAL = "click_reveal"
    DRAG_DROP = "drag_drop"
    HOVER_INFO = "hover_info"
    QUIZ = "quiz"
    SIMULATION_CONTROL = "simulation_control"
    NAVIGATION = "navigation"
    ANNOTATION = "annotation"


class VisualStyle(Enum):
    """Visual style presets."""
    TECHNICAL = "technical"
    FRIENDLY = "friendly"
    MINIMALIST = "minimalist"
    DETAILED = "detailed"
    CORPORATE = "corporate"
    PLAYFUL = "playful"
    DARK_MODE = "dark_mode"
    HIGH_CONTRAST = "high_contrast"


@dataclass
class DiagramElement:
    """Element in a diagram."""
    id: str
    type: str  # node, edge, group, annotation
    label: str
    position: Optional[Tuple[float, float]] = None
    size: Optional[Tuple[float, float]] = None
    style: Dict[str, Any] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    connections: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "position": self.position,
            "size": self.size,
            "style": self.style,
            "properties": self.properties,
            "connections": self.connections
        }


@dataclass
class ContentMetadata:
    """Metadata for generated content."""
    id: str = field(default_factory=lambda: str(datetime.now().timestamp()))
    title: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    author: str = "Certify Studio"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    license: str = "Educational Use"
    language: str = "en"
    duration_seconds: Optional[int] = None
    file_size_bytes: Optional[int] = None
    dimensions: Optional[Tuple[int, int]] = None
    format: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "keywords": self.keywords,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "license": self.license,
            "language": self.language,
            "duration_seconds": self.duration_seconds,
            "file_size_bytes": self.file_size_bytes,
            "dimensions": self.dimensions,
            "format": self.format
        }


@dataclass
class ColorPalette:
    """Color palette for consistent styling."""
    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    success: str = "#4CAF50"
    warning: str = "#FF9800"
    error: str = "#F44336"
    info: str = "#2196F3"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "background": self.background,
            "text": self.text,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "info": self.info
        }


@dataclass
class StyleGuide:
    """Comprehensive style guide for content generation."""
    visual_style: VisualStyle
    color_palette: ColorPalette
    font_family: str = "Inter, sans-serif"
    font_size_base: int = 16
    line_height: float = 1.5
    spacing_unit: int = 8
    border_radius: int = 4
    animation_duration: float = 0.3
    shadow_intensity: str = "medium"
    icon_style: str = "outlined"
    
    def apply_to_element(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Apply style guide to an element."""
        styled = element.copy()
        styled["style"] = {
            "fontFamily": self.font_family,
            "fontSize": f"{self.font_size_base}px",
            "lineHeight": self.line_height,
            "borderRadius": f"{self.border_radius}px",
            "transition": f"all {self.animation_duration}s ease"
        }
        return styled


@dataclass
class DiagramSpecification:
    """Specification for generating a diagram."""
    id: str
    type: DiagramType
    title: str
    concepts: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    style_guide: StyleGuide
    dimensions: Tuple[int, int] = (1920, 1080)
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate diagram specification."""
        if not self.concepts:
            return False
        if self.dimensions[0] < 800 or self.dimensions[1] < 600:
            return False
        return True


@dataclass
class AnimationKeyframe:
    """Single keyframe in an animation sequence."""
    time: float  # seconds
    element_id: str
    properties: Dict[str, Any]
    easing: str = "ease-in-out"
    
    def to_manim_command(self) -> str:
        """Convert to Manim animation command."""
        # Simplified for demonstration
        return f"# Animate {self.element_id} at {self.time}s"


@dataclass
class AnimationSequence:
    """Complete animation sequence specification."""
    id: str
    type: AnimationType
    title: str
    duration: float  # total seconds
    keyframes: List[AnimationKeyframe]
    narration_script: Optional[str] = None
    background_music: Optional[str] = None
    style_guide: StyleGuide = None
    fps: int = 30
    resolution: Tuple[int, int] = (1920, 1080)
    
    def get_timeline(self) -> List[Tuple[float, str]]:
        """Get timeline of events."""
        timeline = []
        for keyframe in self.keyframes:
            timeline.append((keyframe.time, keyframe.element_id))
        return sorted(timeline, key=lambda x: x[0])
    
    def validate_timing(self) -> bool:
        """Validate that keyframes don't exceed duration."""
        max_time = max(kf.time for kf in self.keyframes) if self.keyframes else 0
        return max_time <= self.duration


@dataclass
class InteractiveElement:
    """Specification for interactive elements."""
    id: str
    type: InteractionType
    trigger: str  # click, hover, drag, etc.
    action: Dict[str, Any]
    target_elements: List[str]
    feedback: Optional[Dict[str, Any]] = None
    accessibility_label: Optional[str] = None
    keyboard_shortcut: Optional[str] = None
    
    def to_javascript(self) -> str:
        """Generate JavaScript for interaction."""
        # Simplified for demonstration
        return f"""
        document.getElementById('{self.id}').addEventListener('{self.trigger}', function() {{
            // Execute action
            console.log('Interaction triggered: {self.type.value}');
        }});
        """


@dataclass
class ContentPiece:
    """A complete piece of educational content."""
    id: str
    type: ContentType
    title: str
    learning_objective_id: str
    specification: Any  # DiagramSpecification, AnimationSequence, or InteractiveElement
    style_guide: StyleGuide
    accessibility_features: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Optional['QualityMetrics'] = None
    created_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    
    def export_format(self) -> str:
        """Determine export format based on content type."""
        format_map = {
            ContentType.DIAGRAM: "svg",
            ContentType.ANIMATION: "mp4",
            ContentType.INTERACTIVE: "html",
            ContentType.HYBRID: "html",
            ContentType.INFOGRAPHIC: "pdf",
            ContentType.SIMULATION: "html",
            ContentType.QUIZ: "json",
            ContentType.LAB: "html"
        }
        return format_map.get(self.type, "html")


@dataclass
class QualityMetrics:
    """Metrics for content quality assessment."""
    technical_accuracy: float  # 0-1
    visual_clarity: float  # 0-1
    educational_effectiveness: float  # 0-1
    accessibility_score: float  # 0-1
    engagement_potential: float  # 0-1
    overall_quality: float  # 0-1
    
    feedback: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    validation_timestamp: datetime = field(default_factory=datetime.now)
    
    def meets_threshold(self, threshold: float = 0.85) -> bool:
        """Check if content meets quality threshold."""
        return self.overall_quality >= threshold
    
    def get_weakest_area(self) -> str:
        """Identify area needing most improvement."""
        metrics = {
            "technical_accuracy": self.technical_accuracy,
            "visual_clarity": self.visual_clarity,
            "educational_effectiveness": self.educational_effectiveness,
            "accessibility_score": self.accessibility_score,
            "engagement_potential": self.engagement_potential
        }
        return min(metrics.items(), key=lambda x: x[1])[0]


@dataclass
class AccessibilityMetadata:
    """Accessibility information for content."""
    alt_text: str
    long_description: Optional[str] = None
    captions: Optional[List[Dict[str, Any]]] = None
    transcript: Optional[str] = None
    aria_labels: Dict[str, str] = field(default_factory=dict)
    keyboard_navigation: bool = True
    screen_reader_optimized: bool = True
    color_contrast_ratio: float = 4.5  # WCAG AA standard
    focus_indicators: bool = True
    
    def validate_wcag_aa(self) -> Tuple[bool, List[str]]:
        """Validate WCAG AA compliance."""
        issues = []
        
        if not self.alt_text:
            issues.append("Missing alt text")
        if self.color_contrast_ratio < 4.5:
            issues.append(f"Color contrast ratio {self.color_contrast_ratio} below AA standard (4.5)")
        if not self.keyboard_navigation:
            issues.append("Keyboard navigation not supported")
        
        return len(issues) == 0, issues


@dataclass
class RenderingOptions:
    """Options for rendering content."""
    format: str  # svg, png, mp4, html, etc.
    resolution: Tuple[int, int] = (1920, 1080)
    quality: str = "high"  # low, medium, high
    compression: bool = True
    include_metadata: bool = True
    embed_fonts: bool = True
    optimize_for_web: bool = True
    
    def get_export_settings(self) -> Dict[str, Any]:
        """Get export settings based on format."""
        settings = {
            "resolution": self.resolution,
            "quality": self.quality,
            "compression": self.compression
        }
        
        if self.format == "mp4":
            settings.update({
                "codec": "h264",
                "bitrate": "5000k" if self.quality == "high" else "2000k",
                "fps": 30
            })
        elif self.format == "svg":
            settings.update({
                "embed_fonts": self.embed_fonts,
                "optimize": self.optimize_for_web
            })
        
        return settings


@dataclass
class ContentGenerationRequest:
    """Request to generate educational content."""
    learning_objective_id: str
    content_type: ContentType
    concepts: List[Dict[str, Any]]
    style_preferences: Optional[StyleGuide] = None
    target_audience: str = "general"
    time_constraint: Optional[int] = None  # seconds for animations
    accessibility_requirements: List[str] = field(default_factory=list)
    quality_threshold: float = 0.85
    reference_materials: List[str] = field(default_factory=list)
    
    def estimate_generation_time(self) -> int:
        """Estimate generation time in seconds."""
        base_times = {
            ContentType.DIAGRAM: 30,
            ContentType.ANIMATION: 120,
            ContentType.INTERACTIVE: 60,
            ContentType.HYBRID: 180,
            ContentType.SIMULATION: 300
        }
        
        base_time = base_times.get(self.content_type, 60)
        complexity_factor = len(self.concepts) * 0.1
        
        return int(base_time * (1 + complexity_factor))
