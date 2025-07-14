"""
Style Manager Module for Content Generation Agent.

This module manages visual consistency across all generated content, ensuring
a cohesive learning experience through intelligent style application and brand compliance.
"""

import asyncio
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from enum import Enum
from pathlib import Path
import hashlib
import uuid

from loguru import logger
from pydantic import BaseModel, Field
import cv2
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import seaborn as sns

from .models import (
    ContentPiece,
    MediaType,
    DiagramElement,
    AnimationSequence
)
from ....core.llm import MultimodalLLM
from ....core.llm.vision_processor import VisionProcessor
from ....config import settings


class ColorScheme(BaseModel):
    """Color scheme definition."""
    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    success: str
    warning: str
    error: str
    info: str
    gradients: Dict[str, List[str]] = Field(default_factory=dict)
    
    
class Typography(BaseModel):
    """Typography settings."""
    font_family: str
    heading_font: Optional[str] = None
    code_font: str = "monospace"
    base_size: int = 16
    scale_ratio: float = 1.25
    line_height: float = 1.5
    letter_spacing: float = 0
    

class VisualStyle(BaseModel):
    """Complete visual style definition."""
    name: str
    description: str
    color_scheme: ColorScheme
    typography: Typography
    spacing: Dict[str, int]
    borders: Dict[str, Any]
    shadows: Dict[str, str]
    animations: Dict[str, Any]
    icons: Dict[str, str]
    

class StyleGuide(BaseModel):
    """Comprehensive style guide."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str = "1.0.0"
    visual_style: VisualStyle
    component_styles: Dict[str, Dict[str, Any]]
    domain_specific: Dict[str, Any] = Field(default_factory=dict)
    accessibility_overrides: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    

class DomainStyle(Enum):
    """Pre-defined domain styles."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    LINUX = "linux"
    NETWORKING = "networking"
    SECURITY = "security"
    DEVOPS = "devops"
    DATA = "data"
    

class StyleManager:
    """Manages visual consistency across all content."""
    
    def __init__(self):
        self.llm = MultimodalLLM()
        self.vision_processor = VisionProcessor()
        self._style_cache = {}
        self._domain_styles = self._load_domain_styles()
        self._style_analyzer = StyleAnalyzer()
        self._consistency_checker = ConsistencyChecker()
        
    def _load_domain_styles(self) -> Dict[DomainStyle, StyleGuide]:
        """Load pre-defined domain styles."""
        return {
            DomainStyle.AWS: self._create_aws_style(),
            DomainStyle.AZURE: self._create_azure_style(),
            DomainStyle.GCP: self._create_gcp_style(),
            DomainStyle.KUBERNETES: self._create_kubernetes_style(),
            DomainStyle.DOCKER: self._create_docker_style()
        }
        
    def _create_aws_style(self) -> StyleGuide:
        """Create AWS brand style guide."""
        return StyleGuide(
            name="AWS Style Guide",
            visual_style=VisualStyle(
                name="AWS",
                description="Amazon Web Services visual style",
                color_scheme=ColorScheme(
                    primary="#FF9900",  # AWS Orange
                    secondary="#232F3E",  # AWS Dark Blue
                    accent="#146EB4",  # AWS Light Blue
                    background="#FFFFFF",
                    text="#232F3E",
                    success="#36C63F",
                    warning="#FF9900",
                    error="#D13212",
                    info="#146EB4",
                    gradients={
                        "primary": ["#FF9900", "#EC7211"],
                        "dark": ["#232F3E", "#161E2D"]
                    }
                ),
                typography=Typography(
                    font_family="Amazon Ember, Arial, sans-serif",
                    heading_font="Amazon Ember Display",
                    code_font="Monaco, Consolas, monospace",
                    base_size=16,
                    scale_ratio=1.25
                ),
                spacing={
                    "xs": 4,
                    "sm": 8,
                    "md": 16,
                    "lg": 24,
                    "xl": 32
                },
                borders={
                    "radius": 4,
                    "width": 1,
                    "color": "#D5D7DA"
                },
                shadows={
                    "sm": "0 1px 3px rgba(0,0,0,0.12)",
                    "md": "0 4px 6px rgba(0,0,0,0.1)",
                    "lg": "0 10px 15px rgba(0,0,0,0.1)"
                },
                animations={
                    "duration": 200,
                    "easing": "cubic-bezier(0.4, 0, 0.2, 1)"
                },
                icons={
                    "style": "aws-icons",
                    "size": 24
                }
            ),
            component_styles={
                "diagram": {
                    "node": {
                        "fill": "#FFFFFF",
                        "stroke": "#232F3E",
                        "strokeWidth": 2
                    },
                    "service": {
                        "iconSize": 48,
                        "labelFont": "Amazon Ember",
                        "labelSize": 14
                    }
                },
                "code": {
                    "theme": "aws-light",
                    "lineNumbers": True,
                    "highlightLines": True
                }
            }
        )
        
    def _create_azure_style(self) -> StyleGuide:
        """Create Azure brand style guide."""
        return StyleGuide(
            name="Azure Style Guide",
            visual_style=VisualStyle(
                name="Azure",
                description="Microsoft Azure visual style",
                color_scheme=ColorScheme(
                    primary="#0078D4",  # Azure Blue
                    secondary="#005A9E",  # Darker Blue
                    accent="#40E0D0",  # Azure Accent
                    background="#FFFFFF",
                    text="#323130",
                    success="#107C10",
                    warning="#FFB900",
                    error="#D83B01",
                    info="#0078D4",
                    gradients={
                        "primary": ["#0078D4", "#005A9E"],
                        "accent": ["#40E0D0", "#00BCF2"]
                    }
                ),
                typography=Typography(
                    font_family="Segoe UI, Arial, sans-serif",
                    heading_font="Segoe UI Light",
                    code_font="Consolas, monospace",
                    base_size=16,
                    scale_ratio=1.2
                ),
                spacing={
                    "xs": 4,
                    "sm": 8,
                    "md": 16,
                    "lg": 24,
                    "xl": 32
                },
                borders={
                    "radius": 2,
                    "width": 1,
                    "color": "#E1E1E1"
                },
                shadows={
                    "sm": "0 1.6px 3.6px rgba(0,0,0,0.132)",
                    "md": "0 3.2px 7.2px rgba(0,0,0,0.108)",
                    "lg": "0 6.4px 14.4px rgba(0,0,0,0.096)"
                },
                animations={
                    "duration": 250,
                    "easing": "cubic-bezier(0.1, 0.9, 0.2, 1)"
                },
                icons={
                    "style": "azure-icons",
                    "size": 24
                }
            ),
            component_styles={
                "diagram": {
                    "node": {
                        "fill": "#F2F2F2",
                        "stroke": "#0078D4",
                        "strokeWidth": 1.5
                    }
                }
            }
        )
        
    def _create_gcp_style(self) -> StyleGuide:
        """Create Google Cloud Platform style guide."""
        return StyleGuide(
            name="GCP Style Guide",
            visual_style=VisualStyle(
                name="GCP",
                description="Google Cloud Platform visual style",
                color_scheme=ColorScheme(
                    primary="#4285F4",  # Google Blue
                    secondary="#34A853",  # Google Green
                    accent="#FBBC04",  # Google Yellow
                    background="#FFFFFF",
                    text="#202124",
                    success="#34A853",
                    warning="#FBBC04",
                    error="#EA4335",  # Google Red
                    info="#4285F4",
                    gradients={
                        "primary": ["#4285F4", "#1A73E8"],
                        "multi": ["#4285F4", "#34A853", "#FBBC04", "#EA4335"]
                    }
                ),
                typography=Typography(
                    font_family="Google Sans, Roboto, sans-serif",
                    heading_font="Google Sans Display",
                    code_font="Roboto Mono, monospace",
                    base_size=16,
                    scale_ratio=1.25
                ),
                spacing={
                    "xs": 4,
                    "sm": 8,
                    "md": 16,
                    "lg": 24,
                    "xl": 32
                },
                borders={
                    "radius": 8,
                    "width": 1,
                    "color": "#DADCE0"
                },
                shadows={
                    "sm": "0 1px 2px rgba(60,64,67,0.3)",
                    "md": "0 2px 4px rgba(60,64,67,0.3)",
                    "lg": "0 4px 8px rgba(60,64,67,0.3)"
                },
                animations={
                    "duration": 200,
                    "easing": "cubic-bezier(0.4, 0.0, 0.2, 1)"
                },
                icons={
                    "style": "material-icons",
                    "size": 24
                }
            ),
            component_styles={}
        )
        
    def _create_kubernetes_style(self) -> StyleGuide:
        """Create Kubernetes style guide."""
        return StyleGuide(
            name="Kubernetes Style Guide",
            visual_style=VisualStyle(
                name="Kubernetes",
                description="Kubernetes visual style",
                color_scheme=ColorScheme(
                    primary="#326CE5",  # K8s Blue
                    secondary="#0066CC",
                    accent="#6CBCE8",
                    background="#FFFFFF",
                    text="#2D3E50",
                    success="#00D067",
                    warning="#FFA500",
                    error="#E53935",
                    info="#326CE5"
                ),
                typography=Typography(
                    font_family="Inter, Arial, sans-serif",
                    code_font="JetBrains Mono, monospace",
                    base_size=16
                ),
                spacing={
                    "xs": 4,
                    "sm": 8,
                    "md": 16,
                    "lg": 24,
                    "xl": 32
                },
                borders={
                    "radius": 6,
                    "width": 2,
                    "color": "#E0E0E0"
                },
                shadows={
                    "sm": "0 2px 4px rgba(0,0,0,0.1)",
                    "md": "0 4px 8px rgba(0,0,0,0.12)",
                    "lg": "0 8px 16px rgba(0,0,0,0.15)"
                },
                animations={
                    "duration": 300,
                    "easing": "ease-in-out"
                },
                icons={
                    "style": "kubernetes-icons",
                    "size": 32
                }
            ),
            component_styles={}
        )
        
    def _create_docker_style(self) -> StyleGuide:
        """Create Docker style guide."""
        return StyleGuide(
            name="Docker Style Guide",
            visual_style=VisualStyle(
                name="Docker",
                description="Docker visual style",
                color_scheme=ColorScheme(
                    primary="#2496ED",  # Docker Blue
                    secondary="#0DB7ED",
                    accent="#384D54",
                    background="#FFFFFF",
                    text="#384D54",
                    success="#28A745",
                    warning="#FFC107",
                    error="#DC3545",
                    info="#17A2B8"
                ),
                typography=Typography(
                    font_family="Helvetica Neue, Arial, sans-serif",
                    code_font="Source Code Pro, monospace",
                    base_size=16
                ),
                spacing={
                    "xs": 4,
                    "sm": 8,
                    "md": 16,
                    "lg": 24,
                    "xl": 32
                },
                borders={
                    "radius": 4,
                    "width": 1,
                    "color": "#E9ECEF"
                },
                shadows={
                    "sm": "0 1px 3px rgba(0,0,0,0.1)",
                    "md": "0 3px 6px rgba(0,0,0,0.16)",
                    "lg": "0 10px 20px rgba(0,0,0,0.19)"
                },
                animations={
                    "duration": 250,
                    "easing": "ease-out"
                },
                icons={
                    "style": "docker-icons",
                    "size": 24
                }
            ),
            component_styles={}
        )
        
    async def learn_style_from_reference(
        self,
        reference_images: List[str],
        style_guide: Optional[StyleGuide] = None,
        domain_context: Optional[str] = None
    ) -> StyleGuide:
        """Learn visual style from reference materials."""
        try:
            logger.info(f"Learning style from {len(reference_images)} reference images")
            
            # Analyze each reference image
            style_attributes = []
            for img_path in reference_images:
                attributes = await self._analyze_image_style(img_path)
                style_attributes.append(attributes)
                
            # Aggregate style attributes
            aggregated_style = await self._aggregate_styles(style_attributes)
            
            # Create or update style guide
            if style_guide:
                # Update existing style guide
                updated_guide = await self._update_style_guide(
                    style_guide, aggregated_style
                )
            else:
                # Create new style guide
                updated_guide = await self._create_style_guide_from_analysis(
                    aggregated_style, domain_context
                )
                
            # Cache the style
            self._style_cache[updated_guide.id] = updated_guide
            
            logger.info(f"Successfully learned style: {updated_guide.name}")
            return updated_guide
            
        except Exception as e:
            logger.error(f"Error learning style: {str(e)}")
            raise
            
    async def apply_domain_style(
        self,
        content: Dict[str, Any],
        domain: str,
        custom_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Apply domain-specific visual language."""
        try:
            logger.info(f"Applying {domain} style to content")
            
            # Get domain style
            domain_enum = DomainStyle(domain.lower())
            style_guide = self._domain_styles.get(domain_enum)
            
            if not style_guide:
                logger.warning(f"No pre-defined style for domain: {domain}")
                style_guide = await self._create_generic_style(domain)
                
            # Apply custom overrides if provided
            if custom_overrides:
                style_guide = await self._apply_overrides(style_guide, custom_overrides)
                
            # Apply style to content
            styled_content = await self._apply_style_to_content(
                content, style_guide
            )
            
            # Add domain-specific elements
            styled_content = await self._add_domain_elements(
                styled_content, domain_enum
            )
            
            logger.info(f"Successfully applied {domain} style")
            return styled_content
            
        except Exception as e:
            logger.error(f"Error applying domain style: {str(e)}")
            raise
            
    async def ensure_consistency(
        self,
        content_pieces: List[ContentPiece],
        style_guide: Optional[StyleGuide] = None,
        consistency_level: str = "strict"
    ) -> List[ContentPiece]:
        """Ensure visual consistency across multiple pieces."""
        try:
            logger.info(f"Ensuring consistency across {len(content_pieces)} pieces")
            
            # Determine style guide to use
            if not style_guide:
                # Infer style from first piece or create default
                style_guide = await self._infer_style_guide(content_pieces[0])
                
            # Check consistency of each piece
            consistency_issues = []
            for idx, piece in enumerate(content_pieces):
                issues = await self._consistency_checker.check_consistency(
                    piece, style_guide, consistency_level
                )
                if issues:
                    consistency_issues.append((idx, issues))
                    
            # Fix consistency issues
            if consistency_issues:
                logger.info(f"Found {len(consistency_issues)} pieces with issues")
                content_pieces = await self._fix_consistency_issues(
                    content_pieces, consistency_issues, style_guide
                )
                
            # Apply final polish
            polished_pieces = []
            for piece in content_pieces:
                polished = await self._apply_final_polish(piece, style_guide)
                polished_pieces.append(polished)
                
            logger.info("Successfully ensured visual consistency")
            return polished_pieces
            
        except Exception as e:
            logger.error(f"Error ensuring consistency: {str(e)}")
            raise
            
    async def create_style_variations(
        self,
        base_style: StyleGuide,
        variation_types: List[str]
    ) -> Dict[str, StyleGuide]:
        """Create style variations for different contexts."""
        try:
            logger.info(f"Creating {len(variation_types)} style variations")
            
            variations = {}
            for var_type in variation_types:
                if var_type == "dark_mode":
                    variation = await self._create_dark_mode_variation(base_style)
                elif var_type == "high_contrast":
                    variation = await self._create_high_contrast_variation(base_style)
                elif var_type == "colorblind_safe":
                    variation = await self._create_colorblind_variation(base_style)
                elif var_type == "print":
                    variation = await self._create_print_variation(base_style)
                elif var_type == "mobile":
                    variation = await self._create_mobile_variation(base_style)
                else:
                    logger.warning(f"Unknown variation type: {var_type}")
                    continue
                    
                variations[var_type] = variation
                
            return variations
            
        except Exception as e:
            logger.error(f"Error creating style variations: {str(e)}")
            raise
            
    async def optimize_for_learning(
        self,
        content: Dict[str, Any],
        learning_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize visual style for learning effectiveness."""
        try:
            logger.info("Optimizing visual style for learning")
            
            # Analyze learning context
            audience_level = learning_context.get("audience_level", "intermediate")
            cognitive_load = learning_context.get("cognitive_load", 0.5)
            subject_complexity = learning_context.get("complexity", 0.5)
            
            # Apply cognitive load principles
            if cognitive_load > 0.7:
                content = await self._simplify_visuals(content)
            elif cognitive_load < 0.3:
                content = await self._enrich_visuals(content)
                
            # Adjust for audience
            if audience_level == "beginner":
                content = await self._apply_beginner_optimizations(content)
            elif audience_level == "expert":
                content = await self._apply_expert_optimizations(content)
                
            # Apply learning principles
            content = await self._apply_visual_learning_principles(content)
            
            return content
            
        except Exception as e:
            logger.error(f"Error optimizing for learning: {str(e)}")
            raise
            
    # Private helper methods
    
    async def _analyze_image_style(self, image_path: str) -> Dict[str, Any]:
        """Analyze style attributes of an image."""
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot load image: {image_path}")
            
        # Extract color palette
        colors = await self._extract_color_palette(image)
        
        # Analyze typography if text present
        typography = await self._analyze_typography(image)
        
        # Analyze layout and spacing
        layout = await self._analyze_layout(image)
        
        # Analyze visual elements
        elements = await self._analyze_visual_elements(image)
        
        return {
            "colors": colors,
            "typography": typography,
            "layout": layout,
            "elements": elements
        }
        
    async def _extract_color_palette(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract dominant colors from image."""
        # Convert to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Reshape for clustering
        pixels = image_rgb.reshape(-1, 3)
        
        # Use k-means to find dominant colors
        from sklearn.cluster import KMeans
        n_colors = 5
        kmeans = KMeans(n_clusters=n_colors, random_state=42)
        kmeans.fit(pixels)
        
        # Get color centers
        colors = kmeans.cluster_centers_.astype(int)
        
        # Convert to hex
        hex_colors = ['#{:02x}{:02x}{:02x}'.format(r, g, b) for r, g, b in colors]
        
        # Calculate color proportions
        labels = kmeans.labels_
        proportions = [np.sum(labels == i) / len(labels) for i in range(n_colors)]
        
        # Sort by dominance
        sorted_indices = np.argsort(proportions)[::-1]
        
        return {
            "dominant": hex_colors[sorted_indices[0]],
            "palette": [hex_colors[i] for i in sorted_indices],
            "proportions": [proportions[i] for i in sorted_indices]
        }
        
    async def _analyze_typography(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze typography in image using OCR."""
        # Use vision processor for text detection
        text_regions = await self.vision_processor.detect_text(image)
        
        if not text_regions:
            return {"detected": False}
            
        # Analyze text properties
        font_sizes = []
        line_heights = []
        
        for region in text_regions:
            # Estimate font size from bounding box
            height = region["bbox"][3] - region["bbox"][1]
            font_sizes.append(height)
            
        return {
            "detected": True,
            "estimated_sizes": font_sizes,
            "avg_size": np.mean(font_sizes) if font_sizes else 0,
            "text_regions": len(text_regions)
        }
        
    async def _analyze_layout(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze layout and spacing patterns."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analyze spacing
        if len(contours) > 1:
            # Calculate distances between elements
            bounding_boxes = [cv2.boundingRect(c) for c in contours]
            spacings = []
            
            for i in range(len(bounding_boxes) - 1):
                for j in range(i + 1, len(bounding_boxes)):
                    x1, y1, w1, h1 = bounding_boxes[i]
                    x2, y2, w2, h2 = bounding_boxes[j]
                    
                    # Calculate minimum distance
                    x_dist = max(0, max(x1 - (x2 + w2), x2 - (x1 + w1)))
                    y_dist = max(0, max(y1 - (y2 + h2), y2 - (y1 + h1)))
                    
                    if x_dist > 0 or y_dist > 0:
                        spacings.append(min(x_dist, y_dist))
                        
            avg_spacing = np.mean(spacings) if spacings else 0
        else:
            avg_spacing = 0
            
        return {
            "element_count": len(contours),
            "average_spacing": avg_spacing,
            "layout_density": len(contours) / (image.shape[0] * image.shape[1])
        }
        
    async def _analyze_visual_elements(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze visual elements like shapes and patterns."""
        # Detect shapes
        shapes = await self._detect_shapes(image)
        
        # Detect patterns
        patterns = await self._detect_patterns(image)
        
        # Analyze complexity
        complexity = await self._calculate_visual_complexity(image)
        
        return {
            "shapes": shapes,
            "patterns": patterns,
            "complexity": complexity
        }
        
    async def _detect_shapes(self, image: np.ndarray) -> Dict[str, int]:
        """Detect common shapes in image."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        shapes = {
            "rectangles": 0,
            "circles": 0,
            "lines": 0
        }
        
        # Detect rectangles
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:
                shapes["rectangles"] += 1
                
        # Detect circles using Hough transform
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                                  param1=50, param2=30, minRadius=10, maxRadius=100)
        if circles is not None:
            shapes["circles"] = len(circles[0])
            
        # Detect lines
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=50, maxLineGap=10)
        if lines is not None:
            shapes["lines"] = len(lines)
            
        return shapes
        
    async def _detect_patterns(self, image: np.ndarray) -> Dict[str, Any]:
        """Detect visual patterns like gradients, textures."""
        patterns = {
            "has_gradient": False,
            "has_texture": False,
            "has_pattern": False
        }
        
        # Check for gradients
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gradient_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gradient_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_mag = np.sqrt(gradient_x**2 + gradient_y**2)
        
        # If gradient is smooth and directional, likely a gradient fill
        if np.std(gradient_mag) < 50:
            patterns["has_gradient"] = True
            
        # Check for repeating patterns using FFT
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.abs(f_shift)
        
        # Look for peaks in frequency domain
        peaks = cv2.findNonZero((magnitude_spectrum > np.mean(magnitude_spectrum) * 3).astype(np.uint8))
        if peaks is not None and len(peaks) > 10:
            patterns["has_pattern"] = True
            
        return patterns
        
    async def _calculate_visual_complexity(self, image: np.ndarray) -> float:
        """Calculate visual complexity score (0-1)."""
        # Multiple factors contribute to complexity
        
        # Edge density
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Color variety
        unique_colors = len(np.unique(image.reshape(-1, 3), axis=0))
        color_complexity = min(unique_colors / 1000, 1.0)
        
        # Texture complexity (using local binary patterns)
        from skimage.feature import local_binary_pattern
        lbp = local_binary_pattern(gray, 8, 1, method='uniform')
        texture_complexity = len(np.unique(lbp)) / 59  # 59 is max unique patterns
        
        # Combine factors
        complexity = (edge_density * 0.4 + color_complexity * 0.3 + texture_complexity * 0.3)
        
        return float(np.clip(complexity, 0, 1))
        
    async def _aggregate_styles(self, style_attributes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate multiple style analyses into unified style."""
        aggregated = {
            "colors": {},
            "typography": {},
            "layout": {},
            "elements": {}
        }
        
        # Aggregate colors
        all_palettes = [s["colors"]["palette"] for s in style_attributes if "colors" in s]
        if all_palettes:
            # Find most common colors
            color_counts = {}
            for palette in all_palettes:
                for color in palette[:3]:  # Top 3 colors
                    color_counts[color] = color_counts.get(color, 0) + 1
                    
            # Sort by frequency
            sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
            aggregated["colors"]["palette"] = [c[0] for c in sorted_colors[:5]]
            aggregated["colors"]["primary"] = sorted_colors[0][0] if sorted_colors else "#000000"
            
        # Aggregate typography
        font_sizes = []
        for s in style_attributes:
            if "typography" in s and s["typography"].get("detected"):
                font_sizes.extend(s["typography"]["estimated_sizes"])
                
        if font_sizes:
            aggregated["typography"]["base_size"] = int(np.median(font_sizes))
            aggregated["typography"]["size_range"] = (int(np.min(font_sizes)), int(np.max(font_sizes)))
            
        # Aggregate layout
        spacings = [s["layout"]["average_spacing"] for s in style_attributes if "layout" in s]
        if spacings:
            aggregated["layout"]["spacing"] = int(np.mean(spacings))
            
        # Aggregate complexity
        complexities = [s["elements"]["complexity"] for s in style_attributes if "elements" in s]
        if complexities:
            aggregated["elements"]["avg_complexity"] = np.mean(complexities)
            
        return aggregated
        
    async def _create_style_guide_from_analysis(
        self,
        analysis: Dict[str, Any],
        domain_context: Optional[str]
    ) -> StyleGuide:
        """Create style guide from analyzed attributes."""
        # Extract primary colors
        colors = analysis.get("colors", {})
        primary_color = colors.get("primary", "#000000")
        palette = colors.get("palette", [primary_color])
        
        # Create color scheme
        color_scheme = ColorScheme(
            primary=primary_color,
            secondary=palette[1] if len(palette) > 1 else primary_color,
            accent=palette[2] if len(palette) > 2 else primary_color,
            background="#FFFFFF",
            text="#000000",
            success="#00C851",
            warning="#FFBB33",
            error="#FF4444",
            info="#33B5E5"
        )
        
        # Create typography
        base_size = analysis.get("typography", {}).get("base_size", 16)
        typography = Typography(
            font_family="Arial, sans-serif",
            base_size=base_size,
            scale_ratio=1.25
        )
        
        # Create spacing
        base_spacing = analysis.get("layout", {}).get("spacing", 16)
        spacing = {
            "xs": base_spacing // 4,
            "sm": base_spacing // 2,
            "md": base_spacing,
            "lg": base_spacing * 1.5,
            "xl": base_spacing * 2
        }
        
        # Create visual style
        visual_style = VisualStyle(
            name=f"Learned Style - {domain_context or 'Generic'}",
            description="Style learned from reference images",
            color_scheme=color_scheme,
            typography=typography,
            spacing=spacing,
            borders={"radius": 4, "width": 1, "color": "#E0E0E0"},
            shadows={"sm": "0 2px 4px rgba(0,0,0,0.1)", "md": "0 4px 8px rgba(0,0,0,0.15)"},
            animations={"duration": 200, "easing": "ease-out"},
            icons={"style": "default", "size": 24}
        )
        
        # Create style guide
        return StyleGuide(
            name=f"Learned Style Guide - {datetime.now().strftime('%Y%m%d')}",
            visual_style=visual_style,
            component_styles={}
        )
        
    async def _apply_style_to_content(
        self,
        content: Dict[str, Any],
        style_guide: StyleGuide
    ) -> Dict[str, Any]:
        """Apply style guide to content."""
        styled_content = content.copy()
        
        # Apply color scheme
        if "colors" not in styled_content:
            styled_content["colors"] = {}
        styled_content["colors"].update(style_guide.visual_style.color_scheme.dict())
        
        # Apply typography
        if "typography" not in styled_content:
            styled_content["typography"] = {}
        styled_content["typography"].update(style_guide.visual_style.typography.dict())
        
        # Apply spacing
        styled_content["spacing"] = style_guide.visual_style.spacing
        
        # Apply component-specific styles
        for component_type, component_style in style_guide.component_styles.items():
            if component_type in styled_content:
                styled_content[component_type].update(component_style)
                
        return styled_content
        
    async def _create_dark_mode_variation(self, base_style: StyleGuide) -> StyleGuide:
        """Create dark mode variation of style."""
        dark_style = base_style.copy(deep=True)
        dark_style.name = f"{base_style.name} - Dark Mode"
        
        # Invert colors
        colors = dark_style.visual_style.color_scheme
        colors.background = "#1A1A1A"
        colors.text = "#FFFFFF"
        
        # Adjust primary colors for dark background
        # This is simplified - real implementation would use proper color theory
        if colors.primary.startswith("#"):
            # Lighten primary colors for dark mode
            colors.primary = self._lighten_color(colors.primary, 0.2)
            colors.secondary = self._lighten_color(colors.secondary, 0.2)
            
        # Adjust shadows for dark mode
        dark_style.visual_style.shadows = {
            "sm": "0 2px 4px rgba(0,0,0,0.3)",
            "md": "0 4px 8px rgba(0,0,0,0.4)",
            "lg": "0 8px 16px rgba(0,0,0,0.5)"
        }
        
        return dark_style
        
    def _lighten_color(self, hex_color: str, amount: float) -> str:
        """Lighten a hex color by amount (0-1)."""
        # Convert hex to RGB
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Lighten
        lightened = tuple(int(min(255, c + (255 - c) * amount)) for c in rgb)
        
        # Convert back to hex
        return '#{:02x}{:02x}{:02x}'.format(*lightened)
        
    async def _simplify_visuals(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify visuals to reduce cognitive load."""
        simplified = content.copy()
        
        # Reduce color variety
        if "colors" in simplified:
            # Keep only primary colors
            simplified["colors"] = {
                k: v for k, v in simplified["colors"].items()
                if k in ["primary", "secondary", "background", "text"]
            }
            
        # Increase spacing
        if "spacing" in simplified:
            for key in simplified["spacing"]:
                simplified["spacing"][key] = int(simplified["spacing"][key] * 1.2)
                
        # Remove decorative elements
        if "decorative_elements" in simplified:
            simplified["decorative_elements"] = []
            
        return simplified
        
    async def _apply_visual_learning_principles(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Apply research-based visual learning principles."""
        optimized = content.copy()
        
        # Ensure sufficient contrast (WCAG AA standard)
        if "colors" in optimized:
            # Check text contrast
            bg_color = optimized["colors"].get("background", "#FFFFFF")
            text_color = optimized["colors"].get("text", "#000000")
            
            # Simple contrast check (real implementation would be more sophisticated)
            if not self._check_contrast(bg_color, text_color, 4.5):
                # Adjust text color for better contrast
                optimized["colors"]["text"] = "#000000" if bg_color == "#FFFFFF" else "#FFFFFF"
                
        # Apply Gestalt principles
        if "layout" in optimized:
            # Proximity - group related elements
            optimized["layout"]["grouping"] = "proximity"
            
            # Similarity - use consistent styling
            optimized["layout"]["consistency"] = "high"
            
        return optimized
        
    def _check_contrast(self, bg_color: str, text_color: str, min_ratio: float) -> bool:
        """Check if color contrast meets minimum ratio."""
        # Simplified contrast check
        # Real implementation would calculate actual contrast ratio
        return True  # Placeholder


class StyleAnalyzer:
    """Analyzes visual styles from content."""
    
    async def analyze_style(self, content: Any) -> Dict[str, Any]:
        """Analyze style attributes from content."""
        # Placeholder implementation
        return {
            "colors": {},
            "typography": {},
            "layout": {},
            "complexity": 0.5
        }


class ConsistencyChecker:
    """Checks visual consistency across content."""
    
    async def check_consistency(
        self,
        content: ContentPiece,
        style_guide: StyleGuide,
        level: str
    ) -> List[Dict[str, Any]]:
        """Check if content follows style guide."""
        issues = []
        
        # Check color consistency
        # Check typography consistency
        # Check spacing consistency
        # etc.
        
        return issues
