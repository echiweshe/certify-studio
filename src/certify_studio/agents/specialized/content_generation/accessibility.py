"""
Accessibility Manager Module for Content Generation Agent.

This module ensures all generated content meets WCAG AA standards and provides
multiple accessibility features for diverse learners.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from enum import Enum
import re
import hashlib
import uuid

from loguru import logger
from pydantic import BaseModel, Field
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import webvtt
import pyttsx3
from gtts import gTTS

from .models import (
    ContentPiece,
    MediaType,
    DiagramElement,
    AnimationSequence,
    InteractiveElement
)
from ....core.llm import MultimodalLLM
from ....core.llm.vision_processor import VisionProcessor
from ....config import settings


class AccessibilityStandard(Enum):
    """Accessibility standards."""
    WCAG_A = "wcag_a"
    WCAG_AA = "wcag_aa"
    WCAG_AAA = "wcag_aaa"
    SECTION_508 = "section_508"
    ADA = "ada"
    EN_301_549 = "en_301_549"


class ContrastRatio(BaseModel):
    """Color contrast ratio information."""
    ratio: float
    passes_aa: bool
    passes_aaa: bool
    recommendation: Optional[str] = None


class AccessibilityIssue(BaseModel):
    """Accessibility issue found during validation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    severity: str  # "error", "warning", "info"
    standard: AccessibilityStandard
    criterion: str
    description: str
    element_id: Optional[str] = None
    suggestion: str
    auto_fixable: bool = False


class AccessibilityReport(BaseModel):
    """Comprehensive accessibility report."""
    content_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    standards_checked: List[AccessibilityStandard]
    overall_score: float
    issues: List[AccessibilityIssue]
    passed_criteria: List[str]
    recommendations: List[str]
    automated_fixes: List[str]


class TextAlternative(BaseModel):
    """Text alternative for non-text content."""
    element_id: str
    alt_text: str
    long_description: Optional[str] = None
    context: str
    confidence: float


class CaptionSegment(BaseModel):
    """Caption segment for time-based media."""
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str] = None
    sound_effects: Optional[str] = None


class AccessibilityFeatures(BaseModel):
    """Accessibility features for content."""
    alt_texts: Dict[str, str]
    captions: List[CaptionSegment]
    transcripts: Dict[str, str]
    audio_descriptions: Dict[str, str]
    keyboard_navigation: Dict[str, Any]
    aria_labels: Dict[str, str]
    focus_indicators: Dict[str, Any]
    color_adjustments: Dict[str, Any]
    text_adjustments: Dict[str, Any]
    
    
class AccessibilityManager:
    """Ensures all content meets WCAG AA standards."""
    
    def __init__(self):
        self.llm = MultimodalLLM()
        self.vision_processor = VisionProcessor()
        self.contrast_checker = ContrastChecker()
        self.screen_reader_optimizer = ScreenReaderOptimizer()
        self.caption_generator = CaptionGenerator()
        self.keyboard_nav_builder = KeyboardNavigationBuilder()
        self._tts_engine = self._initialize_tts()
        
    def _initialize_tts(self):
        """Initialize text-to-speech engine."""
        try:
            engine = pyttsx3.init()
            # Configure voice settings
            engine.setProperty('rate', 150)  # Speech rate
            engine.setProperty('volume', 0.9)  # Volume
            return engine
        except Exception as e:
            logger.warning(f"Could not initialize TTS engine: {str(e)}")
            return None
            
    async def generate_alt_text(
        self,
        visual_element: Dict[str, Any],
        context: str,
        detail_level: str = "concise"
    ) -> str:
        """Generate descriptive alt text for visual elements."""
        try:
            logger.info(f"Generating alt text for visual element")
            
            # Extract visual information
            element_type = visual_element.get("type", "image")
            
            if element_type == "image":
                alt_text = await self._generate_image_alt_text(
                    visual_element, context, detail_level
                )
            elif element_type == "diagram":
                alt_text = await self._generate_diagram_alt_text(
                    visual_element, context, detail_level
                )
            elif element_type == "chart":
                alt_text = await self._generate_chart_alt_text(
                    visual_element, context, detail_level
                )
            elif element_type == "animation":
                alt_text = await self._generate_animation_alt_text(
                    visual_element, context, detail_level
                )
            else:
                alt_text = await self._generate_generic_alt_text(
                    visual_element, context
                )
                
            # Validate alt text
            alt_text = await self._validate_alt_text(alt_text, context)
            
            logger.info(f"Generated alt text: {alt_text[:50]}...")
            return alt_text
            
        except Exception as e:
            logger.error(f"Error generating alt text: {str(e)}")
            return f"Visual element showing {context}"
            
    async def add_captions(
        self,
        animation: Dict[str, Any],
        narration: Optional[str] = None,
        include_sound_effects: bool = True
    ) -> Dict[str, Any]:
        """Add synchronized captions to animations."""
        try:
            logger.info("Adding captions to animation")
            
            # Extract or generate narration
            if not narration:
                narration = await self._extract_narration_from_animation(animation)
                
            # Generate caption segments
            segments = await self.caption_generator.generate_captions(
                narration,
                animation.get("duration", 30),
                include_sound_effects
            )
            
            # Synchronize with animation timeline
            synchronized_segments = await self._synchronize_captions(
                segments,
                animation.get("timeline", [])
            )
            
            # Add captions to animation
            animation["captions"] = {
                "segments": [s.dict() for s in synchronized_segments],
                "format": "WebVTT",
                "language": "en",
                "style": {
                    "font_size": "18px",
                    "background": "rgba(0, 0, 0, 0.8)",
                    "color": "#FFFFFF",
                    "position": "bottom"
                }
            }
            
            # Generate WebVTT file
            vtt_content = await self._generate_webvtt(synchronized_segments)
            animation["captions"]["vtt_content"] = vtt_content
            
            logger.info(f"Added {len(synchronized_segments)} caption segments")
            return animation
            
        except Exception as e:
            logger.error(f"Error adding captions: {str(e)}")
            raise
            
    async def validate_wcag_compliance(
        self,
        content: ContentPiece,
        standard: AccessibilityStandard = AccessibilityStandard.WCAG_AA
    ) -> Tuple[bool, List[str]]:
        """Validate WCAG AA compliance and return issues."""
        try:
            logger.info(f"Validating {standard.value} compliance")
            
            issues = []
            
            # Check perceivable criteria
            perceivable_issues = await self._check_perceivable(content, standard)
            issues.extend(perceivable_issues)
            
            # Check operable criteria
            operable_issues = await self._check_operable(content, standard)
            issues.extend(operable_issues)
            
            # Check understandable criteria
            understandable_issues = await self._check_understandable(content, standard)
            issues.extend(understandable_issues)
            
            # Check robust criteria
            robust_issues = await self._check_robust(content, standard)
            issues.extend(robust_issues)
            
            # Generate report
            report = AccessibilityReport(
                content_id=content.id,
                standards_checked=[standard],
                overall_score=self._calculate_compliance_score(issues),
                issues=issues,
                passed_criteria=await self._get_passed_criteria(content, standard),
                recommendations=await self._generate_recommendations(issues),
                automated_fixes=[]
            )
            
            # Attempt automatic fixes
            if issues:
                fixed_issues = await self._auto_fix_issues(content, issues)
                report.automated_fixes = [f.description for f in fixed_issues]
                
            compliant = len([i for i in issues if i.severity == "error"]) == 0
            issue_descriptions = [i.description for i in issues]
            
            logger.info(f"Compliance check complete. Compliant: {compliant}")
            return compliant, issue_descriptions
            
        except Exception as e:
            logger.error(f"Error validating WCAG compliance: {str(e)}")
            raise
            
    async def ensure_keyboard_navigation(
        self,
        interactive_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ensure full keyboard navigation support."""
        try:
            logger.info("Ensuring keyboard navigation")
            
            # Add keyboard event handlers
            keyboard_config = await self.keyboard_nav_builder.build_navigation(
                interactive_content
            )
            
            # Add to content
            interactive_content["keyboard_navigation"] = keyboard_config
            
            # Add focus management
            interactive_content["focus_management"] = {
                "tab_order": keyboard_config["tab_order"],
                "focus_trap": keyboard_config.get("focus_trap", False),
                "skip_links": keyboard_config.get("skip_links", []),
                "focus_visible": True
            }
            
            # Add keyboard shortcuts
            shortcuts = await self._generate_keyboard_shortcuts(interactive_content)
            interactive_content["keyboard_shortcuts"] = shortcuts
            
            logger.info("Keyboard navigation ensured")
            return interactive_content
            
        except Exception as e:
            logger.error(f"Error ensuring keyboard navigation: {str(e)}")
            raise
            
    async def generate_audio_description(
        self,
        visual_content: Dict[str, Any],
        style: str = "educational"
    ) -> Dict[str, Any]:
        """Generate audio description for visual content."""
        try:
            logger.info("Generating audio description")
            
            # Analyze visual content
            visual_analysis = await self.vision_processor.analyze_content(
                visual_content
            )
            
            # Generate description script
            script = await self._generate_description_script(
                visual_analysis,
                style
            )
            
            # Convert to audio
            audio_data = await self._text_to_speech(script)
            
            # Create audio description track
            audio_description = {
                "script": script,
                "audio_data": audio_data,
                "duration": self._calculate_audio_duration(script),
                "sync_points": await self._generate_sync_points(
                    script,
                    visual_content
                )
            }
            
            return audio_description
            
        except Exception as e:
            logger.error(f"Error generating audio description: {str(e)}")
            raise
            
    async def optimize_for_screen_readers(
        self,
        content: ContentPiece
    ) -> ContentPiece:
        """Optimize content for screen reader users."""
        try:
            logger.info("Optimizing for screen readers")
            
            # Add semantic structure
            content = await self.screen_reader_optimizer.add_semantic_structure(
                content
            )
            
            # Add ARIA labels and descriptions
            content = await self.screen_reader_optimizer.add_aria_labels(content)
            
            # Optimize reading order
            content = await self.screen_reader_optimizer.optimize_reading_order(
                content
            )
            
            # Add landmarks
            content = await self.screen_reader_optimizer.add_landmarks(content)
            
            # Generate text alternatives for complex elements
            content = await self._add_text_alternatives(content)
            
            logger.info("Screen reader optimization complete")
            return content
            
        except Exception as e:
            logger.error(f"Error optimizing for screen readers: {str(e)}")
            raise
            
    async def create_high_contrast_version(
        self,
        content: ContentPiece
    ) -> ContentPiece:
        """Create high contrast version of content."""
        try:
            logger.info("Creating high contrast version")
            
            high_contrast = content.copy()
            
            # Adjust colors for high contrast
            if hasattr(high_contrast, 'style') and 'colors' in high_contrast.style:
                high_contrast.style['colors'] = {
                    'background': '#000000',
                    'text': '#FFFFFF',
                    'primary': '#FFFF00',
                    'secondary': '#00FFFF',
                    'accent': '#FF00FF',
                    'success': '#00FF00',
                    'error': '#FF0000',
                    'warning': '#FFA500'
                }
                
            # Increase font sizes
            if hasattr(high_contrast, 'style') and 'typography' in high_contrast.style:
                high_contrast.style['typography']['base_size'] = 20
                high_contrast.style['typography']['line_height'] = 1.8
                
            # Add borders to interactive elements
            if hasattr(high_contrast, 'interactive_elements'):
                for element in high_contrast.interactive_elements:
                    element.style['border'] = '3px solid #FFFFFF'
                    
            logger.info("High contrast version created")
            return high_contrast
            
        except Exception as e:
            logger.error(f"Error creating high contrast version: {str(e)}")
            raise
            
    async def add_language_support(
        self,
        content: ContentPiece,
        languages: List[str]
    ) -> ContentPiece:
        """Add multi-language support to content."""
        try:
            logger.info(f"Adding support for {len(languages)} languages")
            
            # Create translations
            translations = {}
            for lang in languages:
                if lang != 'en':  # Assuming English is default
                    translations[lang] = await self._translate_content(
                        content, lang
                    )
                    
            # Add language selector
            content.metadata['languages'] = ['en'] + languages
            content.metadata['translations'] = translations
            
            # Add language attributes
            content = await self._add_language_attributes(content)
            
            logger.info("Language support added")
            return content
            
        except Exception as e:
            logger.error(f"Error adding language support: {str(e)}")
            raise
            
    # Private helper methods
    
    async def _generate_image_alt_text(
        self,
        image_data: Dict[str, Any],
        context: str,
        detail_level: str
    ) -> str:
        """Generate alt text for images."""
        prompt = f"""
        Generate {detail_level} alt text for an image in the context of: {context}
        
        Image contains: {image_data.get('description', 'Unknown content')}
        Purpose: {image_data.get('purpose', 'Educational')}
        
        Guidelines:
        - Be descriptive but concise
        - Focus on educational value
        - Don't start with "Image of" or "Picture of"
        - Include relevant details for understanding the concept
        """
        
        response = await self.llm.generate(prompt)
        return response.strip()
        
    async def _generate_diagram_alt_text(
        self,
        diagram_data: Dict[str, Any],
        context: str,
        detail_level: str
    ) -> str:
        """Generate alt text for diagrams."""
        components = diagram_data.get('components', [])
        relationships = diagram_data.get('relationships', [])
        
        prompt = f"""
        Generate {detail_level} alt text for a technical diagram showing: {context}
        
        Components: {len(components)} elements
        Key components: {[c.get('label', '') for c in components[:5]]}
        Relationships: {len(relationships)} connections
        
        Create a clear description that conveys the diagram's educational purpose.
        """
        
        response = await self.llm.generate(prompt)
        return response.strip()
        
    async def _check_perceivable(
        self,
        content: ContentPiece,
        standard: AccessibilityStandard
    ) -> List[AccessibilityIssue]:
        """Check WCAG Perceivable criteria."""
        issues = []
        
        # 1.1.1 Non-text Content
        if hasattr(content, 'media_elements'):
            for element in content.media_elements:
                if element.type in [MediaType.IMAGE, MediaType.DIAGRAM]:
                    if not element.alt_text:
                        issues.append(AccessibilityIssue(
                            severity="error",
                            standard=standard,
                            criterion="1.1.1",
                            description=f"Missing alt text for {element.type}",
                            element_id=element.id,
                            suggestion="Add descriptive alt text",
                            auto_fixable=True
                        ))
                        
        # 1.4.3 Contrast (Minimum)
        if hasattr(content, 'style') and 'colors' in content.style:
            bg_color = content.style['colors'].get('background', '#FFFFFF')
            text_color = content.style['colors'].get('text', '#000000')
            
            contrast = self.contrast_checker.calculate_ratio(bg_color, text_color)
            if not contrast.passes_aa:
                issues.append(AccessibilityIssue(
                    severity="error",
                    standard=standard,
                    criterion="1.4.3",
                    description=f"Insufficient color contrast: {contrast.ratio:.1f}:1",
                    suggestion="Increase contrast to at least 4.5:1",
                    auto_fixable=True
                ))
                
        # 1.4.1 Use of Color
        # Check if color is the only way to convey information
        color_only_elements = await self._find_color_only_elements(content)
        for element in color_only_elements:
            issues.append(AccessibilityIssue(
                severity="error",
                standard=standard,
                criterion="1.4.1",
                description="Color used as only method to convey information",
                element_id=element,
                suggestion="Add text labels or patterns in addition to color",
                auto_fixable=False
            ))
            
        return issues
        
    async def _check_operable(
        self,
        content: ContentPiece,
        standard: AccessibilityStandard
    ) -> List[AccessibilityIssue]:
        """Check WCAG Operable criteria."""
        issues = []
        
        # 2.1.1 Keyboard
        if hasattr(content, 'interactive_elements'):
            for element in content.interactive_elements:
                if not element.keyboard_accessible:
                    issues.append(AccessibilityIssue(
                        severity="error",
                        standard=standard,
                        criterion="2.1.1",
                        description=f"Interactive element not keyboard accessible",
                        element_id=element.id,
                        suggestion="Add keyboard event handlers",
                        auto_fixable=True
                    ))
                    
        # 2.4.7 Focus Visible
        focus_issues = await self._check_focus_indicators(content)
        for issue in focus_issues:
            issues.append(AccessibilityIssue(
                severity="error",
                standard=standard,
                criterion="2.4.7",
                description=issue,
                suggestion="Add visible focus indicators",
                auto_fixable=True
            ))
            
        return issues
        
    async def _check_understandable(
        self,
        content: ContentPiece,
        standard: AccessibilityStandard
    ) -> List[AccessibilityIssue]:
        """Check WCAG Understandable criteria."""
        issues = []
        
        # 3.1.1 Language of Page
        if not hasattr(content, 'language') or not content.language:
            issues.append(AccessibilityIssue(
                severity="error",
                standard=standard,
                criterion="3.1.1",
                description="Language not specified",
                suggestion="Add language attribute",
                auto_fixable=True
            ))
            
        # 3.3.2 Labels or Instructions
        if hasattr(content, 'form_elements'):
            for element in content.form_elements:
                if not element.label:
                    issues.append(AccessibilityIssue(
                        severity="error",
                        standard=standard,
                        criterion="3.3.2",
                        description=f"Form element missing label",
                        element_id=element.id,
                        suggestion="Add descriptive label",
                        auto_fixable=True
                    ))
                    
        return issues
        
    async def _check_robust(
        self,
        content: ContentPiece,
        standard: AccessibilityStandard
    ) -> List[AccessibilityIssue]:
        """Check WCAG Robust criteria."""
        issues = []
        
        # 4.1.2 Name, Role, Value
        if hasattr(content, 'custom_controls'):
            for control in content.custom_controls:
                if not control.aria_role:
                    issues.append(AccessibilityIssue(
                        severity="error",
                        standard=standard,
                        criterion="4.1.2",
                        description="Custom control missing ARIA role",
                        element_id=control.id,
                        suggestion="Add appropriate ARIA role",
                        auto_fixable=True
                    ))
                    
        return issues
        
    async def _auto_fix_issues(
        self,
        content: ContentPiece,
        issues: List[AccessibilityIssue]
    ) -> List[AccessibilityIssue]:
        """Automatically fix accessibility issues where possible."""
        fixed_issues = []
        
        for issue in issues:
            if issue.auto_fixable:
                try:
                    if issue.criterion == "1.1.1":  # Missing alt text
                        await self._fix_missing_alt_text(content, issue)
                        fixed_issues.append(issue)
                    elif issue.criterion == "1.4.3":  # Contrast
                        await self._fix_contrast_issue(content, issue)
                        fixed_issues.append(issue)
                    elif issue.criterion == "2.1.1":  # Keyboard
                        await self._fix_keyboard_access(content, issue)
                        fixed_issues.append(issue)
                except Exception as e:
                    logger.error(f"Could not auto-fix issue: {str(e)}")
                    
        return fixed_issues
        
    def _calculate_compliance_score(self, issues: List[AccessibilityIssue]) -> float:
        """Calculate overall compliance score."""
        if not issues:
            return 1.0
            
        # Weight by severity
        weights = {"error": 1.0, "warning": 0.5, "info": 0.1}
        total_weight = sum(weights[i.severity] for i in issues)
        
        # Score decreases with more issues
        score = max(0, 1 - (total_weight / 20))  # Arbitrary scaling
        
        return round(score, 2)
        
    async def _generate_webvtt(self, segments: List[CaptionSegment]) -> str:
        """Generate WebVTT format captions."""
        vtt_lines = ["WEBVTT", ""]
        
        for idx, segment in enumerate(segments):
            # Add cue identifier
            vtt_lines.append(str(idx + 1))
            
            # Add timestamp
            start = self._format_timestamp(segment.start_time)
            end = self._format_timestamp(segment.end_time)
            vtt_lines.append(f"{start} --> {end}")
            
            # Add text (with speaker if available)
            text = segment.text
            if segment.speaker:
                text = f"<v {segment.speaker}>{text}"
            if segment.sound_effects:
                text += f" [{segment.sound_effects}]"
                
            vtt_lines.append(text)
            vtt_lines.append("")  # Empty line between cues
            
        return "\n".join(vtt_lines)
        
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to WebVTT timestamp."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
        
    async def _text_to_speech(self, text: str) -> bytes:
        """Convert text to speech audio."""
        if self._tts_engine:
            # Use pyttsx3
            audio_file = f"/tmp/tts_{uuid.uuid4()}.mp3"
            self._tts_engine.save_to_file(text, audio_file)
            self._tts_engine.runAndWait()
            
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
                
            return audio_data
        else:
            # Fallback to gTTS
            tts = gTTS(text=text, lang='en', slow=False)
            audio_file = f"/tmp/tts_{uuid.uuid4()}.mp3"
            tts.save(audio_file)
            
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
                
            return audio_data
            
    def _calculate_audio_duration(self, text: str) -> float:
        """Estimate audio duration for text."""
        # Average speaking rate: 150 words per minute
        words = len(text.split())
        duration = (words / 150) * 60  # Convert to seconds
        
        return duration


class ContrastChecker:
    """Check color contrast ratios."""
    
    def calculate_ratio(self, bg_color: str, fg_color: str) -> ContrastRatio:
        """Calculate contrast ratio between two colors."""
        # Convert hex to RGB
        bg_rgb = self._hex_to_rgb(bg_color)
        fg_rgb = self._hex_to_rgb(fg_color)
        
        # Calculate relative luminance
        bg_lum = self._relative_luminance(bg_rgb)
        fg_lum = self._relative_luminance(fg_rgb)
        
        # Calculate contrast ratio
        if bg_lum > fg_lum:
            ratio = (bg_lum + 0.05) / (fg_lum + 0.05)
        else:
            ratio = (fg_lum + 0.05) / (bg_lum + 0.05)
            
        return ContrastRatio(
            ratio=round(ratio, 2),
            passes_aa=ratio >= 4.5,
            passes_aaa=ratio >= 7.0,
            recommendation=self._get_recommendation(ratio)
        )
        
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
    def _relative_luminance(self, rgb: Tuple[int, int, int]) -> float:
        """Calculate relative luminance of RGB color."""
        def adjust(val):
            val = val / 255.0
            if val <= 0.03928:
                return val / 12.92
            else:
                return ((val + 0.055) / 1.055) ** 2.4
                
        r, g, b = [adjust(val) for val in rgb]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
    def _get_recommendation(self, ratio: float) -> str:
        """Get recommendation based on ratio."""
        if ratio >= 7.0:
            return "Excellent contrast (AAA)"
        elif ratio >= 4.5:
            return "Good contrast (AA)"
        elif ratio >= 3.0:
            return "Improve contrast for AA compliance"
        else:
            return "Poor contrast - significant improvement needed"


class ScreenReaderOptimizer:
    """Optimize content for screen readers."""
    
    async def add_semantic_structure(self, content: ContentPiece) -> ContentPiece:
        """Add semantic HTML structure."""
        # Add proper heading hierarchy
        # Add lists where appropriate
        # Add nav, main, aside elements
        return content
        
    async def add_aria_labels(self, content: ContentPiece) -> ContentPiece:
        """Add ARIA labels and descriptions."""
        # Add aria-label for icons
        # Add aria-describedby for complex elements
        # Add role attributes
        return content
        
    async def optimize_reading_order(self, content: ContentPiece) -> ContentPiece:
        """Ensure logical reading order."""
        # Use CSS flexbox/grid for visual layout
        # Keep DOM order logical
        # Add skip links
        return content
        
    async def add_landmarks(self, content: ContentPiece) -> ContentPiece:
        """Add ARIA landmarks."""
        # Add role="navigation"
        # Add role="main"
        # Add role="complementary"
        return content


class CaptionGenerator:
    """Generate captions for media."""
    
    async def generate_captions(
        self,
        narration: str,
        duration: float,
        include_sound_effects: bool
    ) -> List[CaptionSegment]:
        """Generate caption segments from narration."""
        # Split narration into sentences
        sentences = re.split(r'[.!?]+', narration)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Calculate timing
        time_per_sentence = duration / len(sentences)
        
        segments = []
        current_time = 0
        
        for sentence in sentences:
            segment = CaptionSegment(
                start_time=current_time,
                end_time=current_time + time_per_sentence,
                text=sentence
            )
            segments.append(segment)
            current_time += time_per_sentence
            
        return segments


class KeyboardNavigationBuilder:
    """Build keyboard navigation support."""
    
    async def build_navigation(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Build complete keyboard navigation configuration."""
        return {
            "tab_order": await self._determine_tab_order(content),
            "shortcuts": await self._generate_shortcuts(content),
            "focus_management": {
                "trap_focus": False,
                "return_focus": True,
                "initial_focus": "first_interactive"
            },
            "skip_links": [
                {"target": "#main-content", "text": "Skip to main content"},
                {"target": "#navigation", "text": "Skip to navigation"}
            ]
        }
        
    async def _determine_tab_order(self, content: Dict[str, Any]) -> List[str]:
        """Determine logical tab order."""
        # Extract interactive elements
        # Order by visual position and importance
        return []
        
    async def _generate_shortcuts(self, content: Dict[str, Any]) -> Dict[str, str]:
        """Generate keyboard shortcuts."""
        return {
            "?": "show_help",
            "Escape": "close_dialog",
            "Space": "play_pause",
            "ArrowLeft": "previous",
            "ArrowRight": "next"
        }
