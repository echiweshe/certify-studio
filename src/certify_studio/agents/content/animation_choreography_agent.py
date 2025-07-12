"""
Animation Choreography Agent - Core of the agentic animation system.

This agent doesn't use hardcoded animations. Instead, it:
1. Understands the conceptual structure of what needs to be animated
2. Reasons about the best visual metaphors and storytelling approaches
3. Dynamically generates animation sequences based on context
4. Adapts animations based on viewer understanding and feedback
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from abc import ABC, abstractmethod
import json

from pydantic import BaseModel, Field
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.chat_models.base import BaseChatModel

from ...core.logging import get_logger

logger = get_logger(__name__)


class AnimationPrinciple(Enum):
    """Core animation principles that guide our visual storytelling."""
    PROGRESSIVE_DISCLOSURE = "progressive_disclosure"
    VISUAL_HIERARCHY = "visual_hierarchy"
    MOTION_CONSISTENCY = "motion_consistency"
    COGNITIVE_LOAD_MANAGEMENT = "cognitive_load_management"
    NARRATIVE_FLOW = "narrative_flow"
    CONTEXT_PRESERVATION = "context_preservation"


class VisualMetaphor(Enum):
    """Types of visual metaphors for representing abstract concepts."""
    CONTAINER = "container"  # For grouping, isolation, security
    FLOW = "flow"  # For data movement, processes
    TRANSFORMATION = "transformation"  # For state changes, processing
    CONNECTION = "connection"  # For relationships, networking
    HIERARCHY = "hierarchy"  # For structure, organization
    CYCLE = "cycle"  # For loops, recurring processes
    GROWTH = "growth"  # For scaling, expansion
    BARRIER = "barrier"  # For security, access control


@dataclass
class AnimationContext:
    """Context for animation decisions."""
    concept: str
    domain: str
    complexity_level: int  # 1-10
    target_audience: str
    prior_animations: List[Dict[str, Any]] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    time_constraints: Optional[float] = None  # Max duration in seconds


@dataclass
class AnimationElement:
    """A single element in an animation sequence."""
    element_type: str  # "shape", "text", "icon", "particle", etc.
    properties: Dict[str, Any]
    enter_animation: Dict[str, Any]
    exit_animation: Dict[str, Any]
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    duration: float = 1.0
    start_time: float = 0.0


@dataclass
class AnimationScene:
    """A complete scene with multiple elements."""
    scene_id: str
    title: str
    narration: str
    elements: List[AnimationElement]
    camera_movements: List[Dict[str, Any]]
    transitions: Dict[str, Any]
    total_duration: float
    learning_checkpoints: List[Dict[str, Any]] = field(default_factory=list)


class AnimationStrategy(ABC):
    """Abstract base for animation strategies."""
    
    @abstractmethod
    async def generate_animation_plan(
        self, 
        context: AnimationContext
    ) -> List[AnimationScene]:
        """Generate an animation plan based on context."""
        pass


class IntelligentAnimationStrategy(AnimationStrategy):
    """AI-driven animation strategy that reasons about visual storytelling."""
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm
        self.visual_grammar = self._initialize_visual_grammar()
        
    def _initialize_visual_grammar(self) -> Dict[str, Any]:
        """Initialize the visual grammar rules."""
        return {
            "transitions": {
                "smooth": {"duration": 0.5, "easing": "ease-in-out"},
                "quick": {"duration": 0.2, "easing": "ease-out"},
                "dramatic": {"duration": 1.0, "easing": "ease-in"}
            },
            "movements": {
                "enter_stage": ["fade_in", "slide_in", "grow_in", "spiral_in"],
                "exit_stage": ["fade_out", "slide_out", "shrink_out", "spiral_out"],
                "emphasis": ["pulse", "glow", "shake", "bounce"]
            },
            "compositions": {
                "centered": {"alignment": "center", "padding": 0.1},
                "grid": {"alignment": "grid", "spacing": 0.05},
                "flow": {"alignment": "sequential", "spacing": 0.1},
                "hierarchical": {"alignment": "tree", "spacing": 0.15}
            }
        }
    
    async def generate_animation_plan(
        self, 
        context: AnimationContext
    ) -> List[AnimationScene]:
        """Generate animation plan using AI reasoning."""
        
        # Step 1: Analyze the concept and determine visual metaphors
        metaphors = await self._select_visual_metaphors(context)
        
        # Step 2: Create narrative structure
        narrative = await self._create_narrative_structure(context, metaphors)
        
        # Step 3: Generate scene breakdowns
        scenes = await self._generate_scenes(context, narrative, metaphors)
        
        # Step 4: Add interactive elements and learning checkpoints
        scenes = await self._enhance_with_interactivity(scenes, context)
        
        return scenes
    
    async def _select_visual_metaphors(
        self, 
        context: AnimationContext
    ) -> List[VisualMetaphor]:
        """Select appropriate visual metaphors for the concept."""
        
        if self.llm:
            prompt = f"""
            Given the following learning context:
            - Concept: {context.concept}
            - Domain: {context.domain}
            - Complexity: {context.complexity_level}/10
            - Audience: {context.target_audience}
            
            Select the most appropriate visual metaphors from:
            {[m.value for m in VisualMetaphor]}
            
            Consider:
            1. How to make abstract concepts concrete
            2. Cultural universality of the metaphor
            3. Cognitive load on the audience
            
            Return a JSON list of selected metaphors with reasoning.
            """
            
            # In production, this would call the LLM
            # For now, we'll use intelligent defaults
        
        # Intelligent default selection based on concept analysis
        metaphors = []
        
        concept_lower = context.concept.lower()
        
        if any(word in concept_lower for word in ["flow", "stream", "pipeline", "process"]):
            metaphors.append(VisualMetaphor.FLOW)
        
        if any(word in concept_lower for word in ["container", "bucket", "storage", "database"]):
            metaphors.append(VisualMetaphor.CONTAINER)
        
        if any(word in concept_lower for word in ["network", "connection", "api", "integration"]):
            metaphors.append(VisualMetaphor.CONNECTION)
        
        if any(word in concept_lower for word in ["transform", "convert", "process", "compute"]):
            metaphors.append(VisualMetaphor.TRANSFORMATION)
        
        if any(word in concept_lower for word in ["scale", "grow", "expand", "increase"]):
            metaphors.append(VisualMetaphor.GROWTH)
        
        if any(word in concept_lower for word in ["secure", "protect", "firewall", "auth"]):
            metaphors.append(VisualMetaphor.BARRIER)
        
        # Default to hierarchy if nothing specific found
        if not metaphors:
            metaphors.append(VisualMetaphor.HIERARCHY)
        
        logger.info(f"Selected metaphors for '{context.concept}': {[m.value for m in metaphors]}")
        return metaphors
    
    async def _create_narrative_structure(
        self, 
        context: AnimationContext,
        metaphors: List[VisualMetaphor]
    ) -> Dict[str, Any]:
        """Create a narrative structure for the animation."""
        
        narrative = {
            "introduction": {
                "purpose": "Set context and grab attention",
                "duration": 3.0,
                "elements": ["title", "problem_statement", "overview"]
            },
            "development": {
                "purpose": "Build understanding progressively",
                "segments": []
            },
            "climax": {
                "purpose": "Show the complete picture",
                "duration": 5.0,
                "elements": ["full_system", "interactions"]
            },
            "resolution": {
                "purpose": "Reinforce learning and provide summary",
                "duration": 3.0,
                "elements": ["key_points", "applications"]
            }
        }
        
        # Break down complex concepts into digestible segments
        if context.complexity_level > 7:
            # High complexity: more segments, slower pace
            num_segments = 5
            segment_duration = 4.0
        elif context.complexity_level > 4:
            # Medium complexity
            num_segments = 3
            segment_duration = 3.0
        else:
            # Low complexity
            num_segments = 2
            segment_duration = 2.5
        
        for i in range(num_segments):
            narrative["development"]["segments"].append({
                "index": i,
                "focus": f"Component {i+1}",
                "duration": segment_duration,
                "metaphor": metaphors[i % len(metaphors)].value
            })
        
        return narrative
    
    async def _generate_scenes(
        self,
        context: AnimationContext,
        narrative: Dict[str, Any],
        metaphors: List[VisualMetaphor]
    ) -> List[AnimationScene]:
        """Generate actual animation scenes."""
        
        scenes = []
        current_time = 0.0
        
        # Introduction scene
        intro_scene = await self._create_introduction_scene(
            context, narrative["introduction"], current_time
        )
        scenes.append(intro_scene)
        current_time += intro_scene.total_duration
        
        # Development scenes
        for segment in narrative["development"]["segments"]:
            dev_scene = await self._create_development_scene(
                context, segment, metaphors, current_time
            )
            scenes.append(dev_scene)
            current_time += dev_scene.total_duration
        
        # Climax scene
        climax_scene = await self._create_climax_scene(
            context, narrative["climax"], metaphors, current_time
        )
        scenes.append(climax_scene)
        current_time += climax_scene.total_duration
        
        # Resolution scene
        resolution_scene = await self._create_resolution_scene(
            context, narrative["resolution"], current_time
        )
        scenes.append(resolution_scene)
        
        return scenes
    
    async def _create_introduction_scene(
        self,
        context: AnimationContext,
        intro_config: Dict[str, Any],
        start_time: float
    ) -> AnimationScene:
        """Create the introduction scene."""
        
        elements = []
        
        # Title element
        title_element = AnimationElement(
            element_type="text",
            properties={
                "content": context.concept,
                "font_size": 48,
                "font_weight": "bold",
                "color": "#1a73e8",
                "position": {"x": 0.5, "y": 0.5}  # Relative positioning
            },
            enter_animation={
                "type": "fade_scale",
                "duration": 1.0,
                "from": {"opacity": 0, "scale": 0.8},
                "to": {"opacity": 1, "scale": 1.0}
            },
            exit_animation={
                "type": "fade",
                "duration": 0.5,
                "to": {"opacity": 0}
            },
            duration=2.5,
            start_time=0
        )
        elements.append(title_element)
        
        # Problem visualization
        if context.learning_objectives:
            problem_element = AnimationElement(
                element_type="composite",
                properties={
                    "components": [
                        {
                            "type": "icon",
                            "name": "question_mark",
                            "position": {"x": 0.3, "y": 0.7}
                        },
                        {
                            "type": "text",
                            "content": context.learning_objectives[0],
                            "position": {"x": 0.5, "y": 0.7}
                        }
                    ]
                },
                enter_animation={
                    "type": "slide_fade",
                    "duration": 0.8,
                    "from": {"x": -0.2, "opacity": 0},
                    "to": {"x": 0, "opacity": 1}
                },
                exit_animation={
                    "type": "fade",
                    "duration": 0.3
                },
                duration=2.0,
                start_time=1.0
            )
            elements.append(problem_element)
        
        scene = AnimationScene(
            scene_id=f"intro_{context.concept.replace(' ', '_')}",
            title="Introduction",
            narration=f"Let's explore {context.concept} and understand how it works.",
            elements=elements,
            camera_movements=[
                {
                    "type": "zoom",
                    "start_time": 0,
                    "duration": intro_config["duration"],
                    "from": 1.2,
                    "to": 1.0
                }
            ],
            transitions={"next": "fade"},
            total_duration=intro_config["duration"]
        )
        
        return scene
    
    async def _create_development_scene(
        self,
        context: AnimationContext,
        segment: Dict[str, Any],
        metaphors: List[VisualMetaphor],
        start_time: float
    ) -> AnimationScene:
        """Create a development scene based on the segment and metaphor."""
        
        metaphor = VisualMetaphor(segment["metaphor"])
        elements = []
        
        # Generate elements based on the metaphor
        if metaphor == VisualMetaphor.FLOW:
            elements.extend(await self._create_flow_elements(context, segment))
        elif metaphor == VisualMetaphor.CONTAINER:
            elements.extend(await self._create_container_elements(context, segment))
        elif metaphor == VisualMetaphor.CONNECTION:
            elements.extend(await self._create_connection_elements(context, segment))
        elif metaphor == VisualMetaphor.TRANSFORMATION:
            elements.extend(await self._create_transformation_elements(context, segment))
        else:
            # Default hierarchical representation
            elements.extend(await self._create_hierarchy_elements(context, segment))
        
        scene = AnimationScene(
            scene_id=f"dev_{segment['index']}_{context.concept.replace(' ', '_')}",
            title=f"Understanding {segment['focus']}",
            narration=f"Now let's look at how {segment['focus']} works within {context.concept}.",
            elements=elements,
            camera_movements=[
                {
                    "type": "pan_zoom",
                    "start_time": 0,
                    "duration": segment["duration"],
                    "focus_points": [el.properties.get("position", {"x": 0.5, "y": 0.5}) 
                                   for el in elements[:3]]  # Focus on first 3 elements
                }
            ],
            transitions={"previous": "fade", "next": "slide"},
            total_duration=segment["duration"]
        )
        
        return scene
    
    async def _create_flow_elements(
        self, 
        context: AnimationContext,
        segment: Dict[str, Any]
    ) -> List[AnimationElement]:
        """Create elements for flow metaphor."""
        
        elements = []
        
        # Source node
        source = AnimationElement(
            element_type="shape",
            properties={
                "shape": "circle",
                "radius": 0.05,
                "color": "#4CAF50",
                "position": {"x": 0.2, "y": 0.5},
                "label": "Input"
            },
            enter_animation={
                "type": "grow",
                "duration": 0.5,
                "from": {"scale": 0},
                "to": {"scale": 1}
            },
            exit_animation={
                "type": "fade",
                "duration": 0.3
            },
            duration=segment["duration"],
            start_time=0
        )
        elements.append(source)
        
        # Flow particles
        for i in range(5):
            particle = AnimationElement(
                element_type="particle",
                properties={
                    "size": 0.02,
                    "color": "#2196F3",
                    "path": {
                        "type": "bezier",
                        "points": [
                            {"x": 0.2, "y": 0.5},
                            {"x": 0.5, "y": 0.3 + i * 0.1},
                            {"x": 0.8, "y": 0.5}
                        ]
                    }
                },
                enter_animation={
                    "type": "path_follow",
                    "duration": 2.0,
                    "delay": i * 0.3
                },
                exit_animation={
                    "type": "fade",
                    "duration": 0.1
                },
                duration=2.0,
                start_time=0.5 + i * 0.3
            )
            elements.append(particle)
        
        # Destination node
        destination = AnimationElement(
            element_type="shape",
            properties={
                "shape": "square",
                "size": 0.1,
                "color": "#FF9800",
                "position": {"x": 0.8, "y": 0.5},
                "label": "Output"
            },
            enter_animation={
                "type": "grow",
                "duration": 0.5,
                "from": {"scale": 0},
                "to": {"scale": 1}
            },
            exit_animation={
                "type": "fade",
                "duration": 0.3
            },
            duration=segment["duration"],
            start_time=0.3
        )
        elements.append(destination)
        
        return elements
    
    async def _create_container_elements(
        self,
        context: AnimationContext,
        segment: Dict[str, Any]
    ) -> List[AnimationElement]:
        """Create elements for container metaphor."""
        
        elements = []
        
        # Container outline
        container = AnimationElement(
            element_type="shape",
            properties={
                "shape": "rounded_rect",
                "width": 0.4,
                "height": 0.3,
                "color": "transparent",
                "stroke": "#1976D2",
                "stroke_width": 2,
                "position": {"x": 0.5, "y": 0.5},
                "label": segment["focus"]
            },
            enter_animation={
                "type": "draw",
                "duration": 1.0
            },
            exit_animation={
                "type": "fade",
                "duration": 0.3
            },
            duration=segment["duration"],
            start_time=0
        )
        elements.append(container)
        
        # Items inside container
        for i in range(3):
            item = AnimationElement(
                element_type="shape",
                properties={
                    "shape": "circle",
                    "radius": 0.03,
                    "color": f"hsl({i * 120}, 70%, 50%)",
                    "position": {"x": 0.4 + i * 0.1, "y": 0.5}
                },
                enter_animation={
                    "type": "drop",
                    "duration": 0.5,
                    "from": {"y": 0.2},
                    "to": {"y": 0.5},
                    "delay": i * 0.2
                },
                exit_animation={
                    "type": "fade",
                    "duration": 0.2
                },
                duration=segment["duration"] - 1.0,
                start_time=1.0 + i * 0.2
            )
            elements.append(item)
        
        return elements
    
    async def _create_connection_elements(
        self,
        context: AnimationContext,
        segment: Dict[str, Any]
    ) -> List[AnimationElement]:
        """Create elements for connection metaphor."""
        
        elements = []
        nodes = []
        
        # Create network nodes
        positions = [
            {"x": 0.5, "y": 0.3},
            {"x": 0.3, "y": 0.5},
            {"x": 0.7, "y": 0.5},
            {"x": 0.4, "y": 0.7},
            {"x": 0.6, "y": 0.7}
        ]
        
        for i, pos in enumerate(positions):
            node = AnimationElement(
                element_type="shape",
                properties={
                    "shape": "circle",
                    "radius": 0.04,
                    "color": "#673AB7" if i == 0 else "#9C27B0",
                    "position": pos,
                    "label": f"Node {i+1}" if i == 0 else ""
                },
                enter_animation={
                    "type": "grow_fade",
                    "duration": 0.5,
                    "delay": i * 0.1
                },
                exit_animation={
                    "type": "shrink_fade",
                    "duration": 0.3
                },
                duration=segment["duration"],
                start_time=i * 0.1
            )
            elements.append(node)
            nodes.append(node)
        
        # Create connections
        connections = [
            (0, 1), (0, 2), (1, 3), (2, 4), (3, 4)
        ]
        
        for i, (start_idx, end_idx) in enumerate(connections):
            connection = AnimationElement(
                element_type="line",
                properties={
                    "start": positions[start_idx],
                    "end": positions[end_idx],
                    "color": "#E91E63",
                    "width": 2,
                    "style": "solid"
                },
                enter_animation={
                    "type": "draw_line",
                    "duration": 0.5,
                    "delay": 0.5 + i * 0.2
                },
                exit_animation={
                    "type": "fade",
                    "duration": 0.2
                },
                duration=segment["duration"] - 1.0,
                start_time=0.5 + i * 0.2
            )
            elements.append(connection)
        
        return elements
    
    async def _create_transformation_elements(
        self,
        context: AnimationContext,
        segment: Dict[str, Any]
    ) -> List[AnimationElement]:
        """Create elements for transformation metaphor."""
        
        elements = []
        
        # Input shape
        input_shape = AnimationElement(
            element_type="shape",
            properties={
                "shape": "triangle",
                "size": 0.08,
                "color": "#FF5722",
                "position": {"x": 0.3, "y": 0.5},
                "label": "Input"
            },
            enter_animation={
                "type": "slide_fade",
                "duration": 0.5,
                "from": {"x": 0.1, "opacity": 0},
                "to": {"x": 0.3, "opacity": 1}
            },
            exit_animation={
                "type": "morph",
                "duration": 1.0,
                "to": {"shape": "circle", "color": "#4CAF50"}
            },
            duration=2.0,
            start_time=0
        )
        elements.append(input_shape)
        
        # Transformation box
        transform_box = AnimationElement(
            element_type="shape",
            properties={
                "shape": "rounded_rect",
                "width": 0.15,
                "height": 0.15,
                "color": "#9E9E9E",
                "position": {"x": 0.5, "y": 0.5},
                "label": "Transform",
                "effects": ["glow", "rotate"]
            },
            enter_animation={
                "type": "fade",
                "duration": 0.5,
                "delay": 0.5
            },
            exit_animation={
                "type": "fade",
                "duration": 0.3
            },
            interactions=[
                {
                    "type": "pulse",
                    "trigger": "on_transform",
                    "duration": 0.5
                }
            ],
            duration=segment["duration"],
            start_time=0.5
        )
        elements.append(transform_box)
        
        # Output shape
        output_shape = AnimationElement(
            element_type="shape",
            properties={
                "shape": "circle",
                "radius": 0.06,
                "color": "#4CAF50",
                "position": {"x": 0.7, "y": 0.5},
                "label": "Output"
            },
            enter_animation={
                "type": "grow_fade",
                "duration": 0.5,
                "delay": 2.0
            },
            exit_animation={
                "type": "fade",
                "duration": 0.3
            },
            duration=segment["duration"] - 2.0,
            start_time=2.0
        )
        elements.append(output_shape)
        
        return elements
    
    async def _create_hierarchy_elements(
        self,
        context: AnimationContext,
        segment: Dict[str, Any]
    ) -> List[AnimationElement]:
        """Create elements for hierarchy metaphor (default)."""
        
        elements = []
        
        # Root node
        root = AnimationElement(
            element_type="shape",
            properties={
                "shape": "rounded_rect",
                "width": 0.15,
                "height": 0.08,
                "color": "#3F51B5",
                "position": {"x": 0.5, "y": 0.3},
                "label": context.concept
            },
            enter_animation={
                "type": "fade_scale",
                "duration": 0.5,
                "from": {"scale": 0.8, "opacity": 0},
                "to": {"scale": 1.0, "opacity": 1}
            },
            exit_animation={
                "type": "fade",
                "duration": 0.3
            },
            duration=segment["duration"],
            start_time=0
        )
        elements.append(root)
        
        # Child nodes
        child_positions = [
            {"x": 0.3, "y": 0.5},
            {"x": 0.5, "y": 0.5},
            {"x": 0.7, "y": 0.5}
        ]
        
        for i, pos in enumerate(child_positions):
            # Connection line
            line = AnimationElement(
                element_type="line",
                properties={
                    "start": {"x": 0.5, "y": 0.35},
                    "end": pos,
                    "color": "#757575",
                    "width": 1,
                    "style": "solid"
                },
                enter_animation={
                    "type": "draw_line",
                    "duration": 0.3,
                    "delay": 0.5 + i * 0.1
                },
                exit_animation={
                    "type": "fade",
                    "duration": 0.2
                },
                duration=segment["duration"] - 0.8,
                start_time=0.5 + i * 0.1
            )
            elements.append(line)
            
            # Child node
            child = AnimationElement(
                element_type="shape",
                properties={
                    "shape": "rounded_rect",
                    "width": 0.12,
                    "height": 0.06,
                    "color": "#7986CB",
                    "position": pos,
                    "label": f"Component {i+1}"
                },
                enter_animation={
                    "type": "grow_fade",
                    "duration": 0.3,
                    "delay": 0.8 + i * 0.1
                },
                exit_animation={
                    "type": "fade",
                    "duration": 0.3
                },
                duration=segment["duration"] - 1.1,
                start_time=0.8 + i * 0.1
            )
            elements.append(child)
        
        return elements
    
    async def _create_climax_scene(
        self,
        context: AnimationContext,
        climax_config: Dict[str, Any],
        metaphors: List[VisualMetaphor],
        start_time: float
    ) -> AnimationScene:
        """Create the climax scene showing everything together."""
        
        elements = []
        
        # Create a comprehensive view combining all metaphors
        # This is where we show how all components work together
        
        # Background system diagram
        system_bg = AnimationElement(
            element_type="shape",
            properties={
                "shape": "rounded_rect",
                "width": 0.8,
                "height": 0.6,
                "color": "rgba(0, 0, 0, 0.05)",
                "stroke": "#E0E0E0",
                "stroke_width": 1,
                "position": {"x": 0.5, "y": 0.5}
            },
            enter_animation={
                "type": "fade",
                "duration": 0.5
            },
            exit_animation={
                "type": "fade",
                "duration": 0.3
            },
            duration=climax_config["duration"],
            start_time=0
        )
        elements.append(system_bg)
        
        # Add all components with their interactions
        # This would be customized based on the specific concept
        # For now, showing a generic interconnected system
        
        components = [
            {"pos": {"x": 0.3, "y": 0.3}, "label": "Input Layer"},
            {"pos": {"x": 0.5, "y": 0.3}, "label": "Processing"},
            {"pos": {"x": 0.7, "y": 0.3}, "label": "Output Layer"},
            {"pos": {"x": 0.3, "y": 0.6}, "label": "Storage"},
            {"pos": {"x": 0.5, "y": 0.6}, "label": "Control"},
            {"pos": {"x": 0.7, "y": 0.6}, "label": "Monitoring"}
        ]
        
        for i, comp in enumerate(components):
            element = AnimationElement(
                element_type="composite",
                properties={
                    "components": [
                        {
                            "type": "shape",
                            "shape": "rounded_rect",
                            "width": 0.12,
                            "height": 0.08,
                            "color": f"hsl({i * 60}, 70%, 60%)",
                            "position": comp["pos"]
                        },
                        {
                            "type": "text",
                            "content": comp["label"],
                            "font_size": 12,
                            "color": "white",
                            "position": comp["pos"]
                        }
                    ]
                },
                enter_animation={
                    "type": "grow_fade",
                    "duration": 0.5,
                    "delay": i * 0.2
                },
                exit_animation={
                    "type": "fade",
                    "duration": 0.3
                },
                duration=climax_config["duration"] - i * 0.2,
                start_time=i * 0.2
            )
            elements.append(element)
        
        # Add data flow animations
        flow_paths = [
            ({"x": 0.3, "y": 0.3}, {"x": 0.5, "y": 0.3}),
            ({"x": 0.5, "y": 0.3}, {"x": 0.7, "y": 0.3}),
            ({"x": 0.5, "y": 0.35}, {"x": 0.5, "y": 0.55}),
            ({"x": 0.3, "y": 0.55}, {"x": 0.5, "y": 0.6}),
            ({"x": 0.5, "y": 0.6}, {"x": 0.7, "y": 0.6})
        ]
        
        for i, (start, end) in enumerate(flow_paths):
            flow = AnimationElement(
                element_type="particle_stream",
                properties={
                    "path": {"start": start, "end": end},
                    "particle_count": 3,
                    "particle_size": 0.01,
                    "color": "#2196F3",
                    "speed": 2.0
                },
                enter_animation={
                    "type": "fade",
                    "duration": 0.5,
                    "delay": 1.5 + i * 0.3
                },
                exit_animation={
                    "type": "fade",
                    "duration": 0.2
                },
                duration=climax_config["duration"] - 2.0,
                start_time=1.5 + i * 0.3
            )
            elements.append(flow)
        
        scene = AnimationScene(
            scene_id=f"climax_{context.concept.replace(' ', '_')}",
            title="The Complete Picture",
            narration=f"Here's how all the components of {context.concept} work together as a unified system.",
            elements=elements,
            camera_movements=[
                {
                    "type": "zoom_out",
                    "start_time": 0,
                    "duration": 2.0,
                    "from": 1.5,
                    "to": 1.0
                },
                {
                    "type": "orbit",
                    "start_time": 2.0,
                    "duration": 3.0,
                    "angle": 15,
                    "axis": "y"
                }
            ],
            transitions={"previous": "fade", "next": "fade"},
            total_duration=climax_config["duration"],
            learning_checkpoints=[
                {
                    "time": 2.5,
                    "type": "pause_for_understanding",
                    "prompt": "Notice how data flows through the system"
                },
                {
                    "time": 4.0,
                    "type": "highlight",
                    "target": "control_component",
                    "message": "The control component orchestrates everything"
                }
            ]
        )
        
        return scene
    
    async def _create_resolution_scene(
        self,
        context: AnimationContext,
        resolution_config: Dict[str, Any],
        start_time: float
    ) -> AnimationScene:
        """Create the resolution/summary scene."""
        
        elements = []
        
        # Key takeaways
        takeaways = [
            f"✓ {context.concept} enables efficient processing",
            "✓ Components work together seamlessly",
            "✓ Scalable and maintainable architecture"
        ]
        
        if context.learning_objectives:
            takeaways = [f"✓ {obj}" for obj in context.learning_objectives[:3]]
        
        # Title
        summary_title = AnimationElement(
            element_type="text",
            properties={
                "content": "Key Takeaways",
                "font_size": 36,
                "font_weight": "bold",
                "color": "#1a73e8",
                "position": {"x": 0.5, "y": 0.2}
            },
            enter_animation={
                "type": "fade_slide",
                "duration": 0.5,
                "from": {"y": 0.1, "opacity": 0},
                "to": {"y": 0.2, "opacity": 1}
            },
            exit_animation={
                "type": "fade",
                "duration": 0.3
            },
            duration=resolution_config["duration"],
            start_time=0
        )
        elements.append(summary_title)
        
        # Takeaway points
        for i, takeaway in enumerate(takeaways):
            point = AnimationElement(
                element_type="text",
                properties={
                    "content": takeaway,
                    "font_size": 20,
                    "color": "#424242",
                    "position": {"x": 0.5, "y": 0.4 + i * 0.1},
                    "alignment": "left"
                },
                enter_animation={
                    "type": "slide_fade",
                    "duration": 0.5,
                    "delay": 0.5 + i * 0.3,
                    "from": {"x": -0.1, "opacity": 0},
                    "to": {"x": 0, "opacity": 1}
                },
                exit_animation={
                    "type": "fade",
                    "duration": 0.3
                },
                duration=resolution_config["duration"] - (0.5 + i * 0.3),
                start_time=0.5 + i * 0.3
            )
            elements.append(point)
        
        # Call to action
        cta = AnimationElement(
            element_type="composite",
            properties={
                "components": [
                    {
                        "type": "shape",
                        "shape": "rounded_rect",
                        "width": 0.3,
                        "height": 0.08,
                        "color": "#4CAF50",
                        "position": {"x": 0.5, "y": 0.8}
                    },
                    {
                        "type": "text",
                        "content": "Practice & Apply",
                        "font_size": 18,
                        "color": "white",
                        "position": {"x": 0.5, "y": 0.8}
                    }
                ]
            },
            enter_animation={
                "type": "grow_fade",
                "duration": 0.5,
                "delay": 2.0
            },
            exit_animation={
                "type": "fade",
                "duration": 0.3
            },
            interactions=[
                {
                    "type": "hover",
                    "effect": "glow",
                    "color": "#81C784"
                }
            ],
            duration=resolution_config["duration"] - 2.0,
            start_time=2.0
        )
        elements.append(cta)
        
        scene = AnimationScene(
            scene_id=f"resolution_{context.concept.replace(' ', '_')}",
            title="Summary",
            narration=f"Now you understand the key concepts of {context.concept}. Time to practice and apply this knowledge!",
            elements=elements,
            camera_movements=[
                {
                    "type": "static",
                    "position": {"x": 0.5, "y": 0.5},
                    "zoom": 1.0
                }
            ],
            transitions={"previous": "fade"},
            total_duration=resolution_config["duration"]
        )
        
        return scene
    
    async def _enhance_with_interactivity(
        self,
        scenes: List[AnimationScene],
        context: AnimationContext
    ) -> List[AnimationScene]:
        """Add interactive elements and learning checkpoints."""
        
        for scene in scenes:
            # Add interactive elements based on complexity
            if context.complexity_level > 5:
                # Add pause points for complex topics
                for i, element in enumerate(scene.elements):
                    if i % 3 == 0 and element.duration > 2.0:
                        scene.learning_checkpoints.append({
                            "time": element.start_time + 1.0,
                            "type": "optional_pause",
                            "prompt": "Take a moment to understand this component"
                        })
            
            # Add hover interactions for all labeled elements
            for element in scene.elements:
                if "label" in element.properties and element.properties["label"]:
                    element.interactions.append({
                        "type": "hover",
                        "effect": "tooltip",
                        "content": f"Learn more about {element.properties['label']}"
                    })
            
            # Add click interactions for deeper exploration
            if scene.scene_id.startswith("climax_"):
                for element in scene.elements:
                    if element.element_type == "composite":
                        element.interactions.append({
                            "type": "click",
                            "action": "expand_detail",
                            "target": element.properties.get("label", "component")
                        })
        
        return scenes


class AnimationChoreographyAgent:
    """Main agent that orchestrates animation creation."""
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.strategy = IntelligentAnimationStrategy(llm)
        self.renderer = None  # Will be connected to Manim renderer
        self.export_formats = ["mp4", "webm", "gif", "interactive_html"]
    
    async def create_animation(
        self,
        concept: str,
        domain: str,
        complexity: int,
        audience: str,
        learning_objectives: List[str],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a complete animation for a concept."""
        
        logger.info(f"Creating animation for concept: {concept}")
        
        # Build context
        context = AnimationContext(
            concept=concept,
            domain=domain,
            complexity_level=complexity,
            target_audience=audience,
            learning_objectives=learning_objectives,
            time_constraints=constraints.get("max_duration") if constraints else None
        )
        
        # Generate animation plan
        scenes = await self.strategy.generate_animation_plan(context)
        
        # Optimize for rendering
        scenes = await self._optimize_scenes(scenes, constraints)
        
        # Generate export specification
        export_spec = await self._create_export_specification(scenes, context)
        
        result = {
            "animation_id": f"anim_{concept.replace(' ', '_')}_{hash(concept) % 10000}",
            "concept": concept,
            "total_duration": sum(scene.total_duration for scene in scenes),
            "scene_count": len(scenes),
            "scenes": [self._scene_to_dict(scene) for scene in scenes],
            "export_spec": export_spec,
            "metadata": {
                "created_at": "2024-01-20T10:00:00Z",
                "complexity": complexity,
                "audience": audience,
                "interactive_elements": sum(
                    len(element.interactions) 
                    for scene in scenes 
                    for element in scene.elements
                )
            }
        }
        
        logger.info(f"Animation plan created: {result['animation_id']}")
        return result
    
    async def _optimize_scenes(
        self,
        scenes: List[AnimationScene],
        constraints: Optional[Dict[str, Any]]
    ) -> List[AnimationScene]:
        """Optimize scenes for rendering performance."""
        
        if not constraints:
            return scenes
        
        max_duration = constraints.get("max_duration")
        if max_duration:
            current_duration = sum(scene.total_duration for scene in scenes)
            if current_duration > max_duration:
                # Scale down durations proportionally
                scale_factor = max_duration / current_duration
                for scene in scenes:
                    scene.total_duration *= scale_factor
                    for element in scene.elements:
                        element.duration *= scale_factor
                        element.start_time *= scale_factor
        
        return scenes
    
    async def _create_export_specification(
        self,
        scenes: List[AnimationScene],
        context: AnimationContext
    ) -> Dict[str, Any]:
        """Create specification for different export formats."""
        
        return {
            "video": {
                "resolution": "1920x1080",
                "fps": 60,
                "codec": "h264",
                "quality": "high"
            },
            "interactive": {
                "format": "html5",
                "features": ["pause", "skip", "annotations", "quiz"],
                "compatibility": ["modern_browsers", "mobile"]
            },
            "accessibility": {
                "captions": True,
                "audio_description": True,
                "keyboard_navigation": True
            }
        }
    
    def _scene_to_dict(self, scene: AnimationScene) -> Dict[str, Any]:
        """Convert scene to dictionary for serialization."""
        
        return {
            "scene_id": scene.scene_id,
            "title": scene.title,
            "narration": scene.narration,
            "duration": scene.total_duration,
            "elements": [
                {
                    "type": element.element_type,
                    "properties": element.properties,
                    "animations": {
                        "enter": element.enter_animation,
                        "exit": element.exit_animation
                    },
                    "interactions": element.interactions,
                    "timing": {
                        "start": element.start_time,
                        "duration": element.duration
                    }
                }
                for element in scene.elements
            ],
            "camera": scene.camera_movements,
            "transitions": scene.transitions,
            "checkpoints": scene.learning_checkpoints
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_animation():
        agent = AnimationChoreographyAgent()
        
        result = await agent.create_animation(
            concept="AWS S3 Data Flow",
            domain="cloud_storage",
            complexity=6,
            audience="intermediate_developers",
            learning_objectives=[
                "Understand S3 bucket structure",
                "Learn about object storage patterns",
                "Master data transfer methods"
            ],
            constraints={
                "max_duration": 180  # 3 minutes
            }
        )
        
        print(json.dumps(result, indent=2))
    
    asyncio.run(test_animation())
