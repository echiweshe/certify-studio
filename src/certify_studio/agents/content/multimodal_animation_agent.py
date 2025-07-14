"""
Enhanced Animation Choreography Agent with multimodal LLM capabilities.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import asyncio
import json
from pathlib import Path

from ...core.llm import MultimodalLLM, LLMProvider, PromptManager, PromptType
from ...core.llm.multimodal_llm import MultimodalMessage, MultimodalResponse
from ...core.logging import get_logger
from .animation_choreography_agent import (
    AnimationChoreographyAgent as BaseAnimationAgent,
    AnimationContext, AnimationScene, AnimationElement,
    AnimationPrinciple, VisualMetaphor
)

logger = get_logger(__name__)


class MultimodalAnimationChoreographyAgent(BaseAnimationAgent):
    """Enhanced animation choreography with multimodal LLM capabilities."""
    
    def __init__(
        self,
        llm: Optional[MultimodalLLM] = None,
        enable_vision_analysis: bool = True
    ):
        # Initialize base agent
        super().__init__(llm=None)
        
        # Initialize multimodal LLM
        self.llm = llm or MultimodalLLM(
            provider=LLMProvider.ANTHROPIC_CLAUDE_VISION,
            temperature=0.8  # Higher temperature for creative generation
        )
        
        self.enable_vision_analysis = enable_vision_analysis
        self.prompt_manager = PromptManager()
        self.reference_animations_cache = {}
    
    async def create_animation(
        self,
        concept: str,
        domain: str,
        complexity: int,
        audience: str,
        learning_objectives: List[str],
        constraints: Optional[Dict[str, Any]] = None,
        reference_materials: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create animation with multimodal understanding."""
        
        logger.info(f"Creating animation for {concept} with multimodal LLM")
        
        # Build enhanced context with multimodal analysis
        context = AnimationContext(
            concept=concept,
            domain=domain,
            complexity_level=complexity,
            target_audience=audience,
            learning_objectives=learning_objectives,
            time_constraints=constraints.get("max_duration") if constraints else None
        )
        
        # Analyze reference materials if provided
        if reference_materials:
            context = await self._enhance_context_with_references(
                context, reference_materials
            )
        
        # Generate animation plan with LLM
        animation_plan = await self._generate_animation_plan_llm(context)
        
        # Refine with visual analysis if enabled
        if self.enable_vision_analysis:
            animation_plan = await self._refine_with_visual_analysis(
                animation_plan, context
            )
        
        # Generate final animation specification
        result = await self._create_animation_specification(
            animation_plan, context
        )
        
        return result
    
    async def _enhance_context_with_references(
        self,
        context: AnimationContext,
        reference_materials: Dict[str, Any]
    ) -> AnimationContext:
        """Enhance context by analyzing reference materials."""
        
        # Analyze reference images
        if "images" in reference_materials:
            visual_insights = await self._analyze_reference_images(
                reference_materials["images"],
                context.concept
            )
            context.prior_animations.extend(visual_insights.get("animation_ideas", []))
        
        # Analyze reference animations
        if "animations" in reference_materials:
            animation_insights = await self._analyze_reference_animations(
                reference_materials["animations"]
            )
            context.prior_animations.extend(animation_insights)
        
        return context
    
    async def _analyze_reference_images(
        self,
        images: List[Union[Path, str]],
        concept: str
    ) -> Dict[str, Any]:
        """Analyze reference images for animation ideas."""
        
        prompt = f"""
Analyze these reference images for creating an animation about "{concept}".

Consider:
1. Visual elements that effectively communicate the concept
2. Color schemes and visual hierarchy
3. Metaphors and analogies used
4. Layout and composition patterns
5. Animation opportunities within static images

Provide insights on:
- What visual elements work well
- What could be animated to enhance understanding
- Visual metaphors to adopt or avoid
- Timing and pacing suggestions based on visual complexity

Output Format:
```json
{{
  "effective_elements": ["element1", "element2"],
  "color_insights": {{
    "primary_colors": ["#hex1", "#hex2"],
    "semantic_associations": {{"color": "meaning"}}
  }},
  "animation_ideas": [
    {{
      "element": "what to animate",
      "animation_type": "how to animate",
      "learning_benefit": "why this helps"
    }}
  ],
  "visual_metaphors": [
    {{
      "metaphor": "description",
      "effectiveness": "high|medium|low",
      "adaptation": "how to use in animation"
    }}
  ],
  "complexity_assessment": {{
    "visual_density": "high|medium|low",
    "suggested_pacing": "fast|moderate|slow",
    "progressive_disclosure": ["stage1", "stage2", "stage3"]
  }}
}}
```
"""
        
        message = MultimodalMessage(
            text=prompt,
            images=images[:5],  # Limit to 5 images
            role="user"
        )
        
        response = await self.llm.generate(
            [message],
            response_format={"type": "json"}
        )
        
        if response.structured_data:
            return response.structured_data
        
        return {"animation_ideas": []}
    
    async def _analyze_reference_animations(
        self,
        animations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze reference animations for patterns."""
        
        # This would analyze video files or animation specifications
        # For now, return processed metadata
        insights = []
        
        for anim in animations:
            insights.append({
                "timing_pattern": anim.get("duration", 30),
                "transition_style": anim.get("transitions", "smooth"),
                "interaction_level": anim.get("interactivity", "medium")
            })
        
        return insights
    
    async def _generate_animation_plan_llm(
        self,
        context: AnimationContext
    ) -> Dict[str, Any]:
        """Generate animation plan using LLM."""
        
        # Get specialized prompt
        prompt = self.prompt_manager.get_prompt(
            PromptType.ANIMATION_PLANNING,
            {
                "concept_name": context.concept,
                "objectives": json.dumps(context.learning_objectives),
                "duration": context.time_constraints or 60,
                "expertise_level": context.target_audience
            }
        )
        
        # Add context about prior animations
        if context.prior_animations:
            prompt += f"\n\nConsider these animation patterns that worked well:\n"
            prompt += json.dumps(context.prior_animations[:3], indent=2)
        
        message = MultimodalMessage(text=prompt, role="user")
        
        response = await self.llm.generate(
            [message],
            response_format={"type": "json"}
        )
        
        if response.structured_data:
            return response.structured_data
        
        # Fallback to algorithmic generation
        logger.warning("LLM animation planning failed, using fallback")
        scenes = await self.strategy.generate_animation_plan(context)
        return {"scenes": [self._scene_to_dict(s) for s in scenes]}
    
    async def _refine_with_visual_analysis(
        self,
        animation_plan: Dict[str, Any],
        context: AnimationContext
    ) -> Dict[str, Any]:
        """Refine animation plan with visual analysis."""
        
        # Generate sample frames for key moments
        key_frames = await self._generate_key_frames(
            animation_plan, context
        )
        
        # Analyze visual flow and coherence
        visual_analysis = await self._analyze_visual_flow(
            key_frames, animation_plan
        )
        
        # Apply refinements
        if visual_analysis.get("improvements"):
            animation_plan = self._apply_visual_improvements(
                animation_plan, visual_analysis["improvements"]
            )
        
        return animation_plan
    
    async def _generate_key_frames(
        self,
        animation_plan: Dict[str, Any],
        context: AnimationContext
    ) -> List[Dict[str, Any]]:
        """Generate key frame descriptions for visual analysis."""
        
        key_frames = []
        
        for scene_data in animation_plan.get("scenes", []):
            # Extract key moments
            key_moments = [
                {
                    "time": 0,
                    "description": f"Opening of {scene_data.get('purpose', 'scene')}"
                },
                {
                    "time": scene_data.get("duration", 5) / 2,
                    "description": "Midpoint with all elements visible"
                },
                {
                    "time": scene_data.get("duration", 5),
                    "description": "Scene conclusion"
                }
            ]
            
            for moment in key_moments:
                frame = {
                    "scene_id": scene_data.get("scene_id", "unknown"),
                    "timestamp": moment["time"],
                    "elements": self._get_visible_elements_at_time(
                        scene_data.get("elements", []),
                        moment["time"]
                    ),
                    "description": moment["description"]
                }
                key_frames.append(frame)
        
        return key_frames
    
    def _get_visible_elements_at_time(
        self,
        elements: List[Dict[str, Any]],
        time: float
    ) -> List[Dict[str, Any]]:
        """Get elements visible at a specific time."""
        
        visible = []
        
        for element in elements:
            enter_time = element.get("enter_time", 0)
            exit_time = element.get("exit_time", float('inf'))
            
            if enter_time <= time < exit_time:
                visible.append({
                    "type": element.get("element_type", "unknown"),
                    "content": element.get("content", ""),
                    "position": element.get("properties", {}).get("position", {})
                })
        
        return visible
    
    async def _analyze_visual_flow(
        self,
        key_frames: List[Dict[str, Any]],
        animation_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze visual flow and coherence."""
        
        prompt = f"""
Analyze the visual flow of this animation sequence:

Key Frames:
{json.dumps(key_frames, indent=2)}

Animation Structure:
Total Scenes: {len(animation_plan.get('scenes', []))}
Total Duration: {sum(s.get('duration', 0) for s in animation_plan.get('scenes', []))} seconds

Evaluate:
1. Visual continuity between frames
2. Cognitive load at each moment
3. Attention guidance effectiveness
4. Pacing and rhythm
5. Visual hierarchy clarity

Provide improvements for:
- Moments with too many elements
- Unclear transitions
- Poor visual hierarchy
- Pacing issues
- Missing visual cues

Output Format:
```json
{{
  "flow_score": 0-100,
  "continuity_score": 0-100,
  "cognitive_load_assessment": {{
    "peak_moments": ["timestamp1", "timestamp2"],
    "recommendations": ["reduce elements at X", "slow down transition Y"]
  }},
  "improvements": [
    {{
      "type": "timing|composition|transition|hierarchy",
      "target": "scene_id or element_id",
      "issue": "Description of problem",
      "solution": "Specific improvement",
      "priority": "high|medium|low"
    }}
  ],
  "visual_strengths": ["strength1", "strength2"],
  "accessibility_notes": ["consideration1", "consideration2"]
}}
```
"""
        
        message = MultimodalMessage(text=prompt, role="user")
        
        response = await self.llm.generate(
            [message],
            response_format={"type": "json"}
        )
        
        if response.structured_data:
            return response.structured_data
        
        return {"improvements": []}
    
    def _apply_visual_improvements(
        self,
        animation_plan: Dict[str, Any],
        improvements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply visual improvements to animation plan."""
        
        for improvement in improvements:
            if improvement["priority"] != "high":
                continue
            
            imp_type = improvement["type"]
            target = improvement["target"]
            
            if imp_type == "timing":
                # Adjust timing of elements or scenes
                for scene in animation_plan.get("scenes", []):
                    if scene.get("scene_id") == target:
                        # Apply timing adjustment
                        if "slow down" in improvement["solution"]:
                            scene["duration"] *= 1.5
                        elif "speed up" in improvement["solution"]:
                            scene["duration"] *= 0.75
            
            elif imp_type == "composition":
                # Adjust element positions or grouping
                for scene in animation_plan.get("scenes", []):
                    for element in scene.get("elements", []):
                        if element.get("id") == target:
                            # Apply composition improvement
                            if "reposition" in improvement["solution"]:
                                # Adjust position based on solution
                                pass
            
            elif imp_type == "transition":
                # Improve transitions between elements or scenes
                if "add fade" in improvement["solution"]:
                    # Add fade transition
                    pass
        
        return animation_plan
    
    async def _create_animation_specification(
        self,
        animation_plan: Dict[str, Any],
        context: AnimationContext
    ) -> Dict[str, Any]:
        """Create final animation specification."""
        
        # Calculate total duration
        total_duration = sum(
            scene.get("duration", 0)
            for scene in animation_plan.get("scenes", [])
        )
        
        # Generate export specifications
        export_spec = await self._generate_export_spec_llm(
            animation_plan, context
        )
        
        # Create metadata
        metadata = {
            "created_with": "multimodal_llm",
            "llm_confidence": animation_plan.get("confidence_score", 0.85),
            "visual_complexity": self._calculate_visual_complexity(animation_plan),
            "accessibility_features": animation_plan.get("accessibility", {}),
            "optimization_notes": animation_plan.get("visual_consistency", {})
        }
        
        result = {
            "animation_id": f"anim_{context.concept.replace(' ', '_')}_{hash(context.concept) % 10000}",
            "concept": context.concept,
            "total_duration": total_duration,
            "scene_count": len(animation_plan.get("scenes", [])),
            "scenes": animation_plan.get("scenes", []),
            "export_spec": export_spec,
            "metadata": metadata,
            "narrative_structure": animation_plan.get("narrative_arc", {}),
            "visual_strategy": animation_plan.get("visual_consistency", {}),
            "interaction_design": self._extract_interaction_design(animation_plan)
        }
        
        logger.info(f"Created animation specification: {result['animation_id']}")
        return result
    
    async def _generate_export_spec_llm(
        self,
        animation_plan: Dict[str, Any],
        context: AnimationContext
    ) -> Dict[str, Any]:
        """Generate export specifications using LLM."""
        
        prompt = f"""
Based on this animation plan, generate optimal export specifications:

Animation Summary:
- Concept: {context.concept}
- Duration: {sum(s.get('duration', 0) for s in animation_plan.get('scenes', []))} seconds
- Scene Count: {len(animation_plan.get('scenes', []))}
- Complexity: {context.complexity_level}/10
- Audience: {context.target_audience}

Determine optimal settings for:
1. Video quality and format
2. Interactive HTML features
3. Accessibility options
4. File size optimization
5. Platform compatibility

Output Format:
```json
{{
  "video": {{
    "resolution": "1920x1080|1280x720|4K",
    "fps": 30|60,
    "codec": "h264|h265|vp9",
    "bitrate": "target bitrate",
    "quality_preset": "high|medium|adaptive"
  }},
  "interactive": {{
    "features": ["pause_points", "annotations", "quizzes", "navigation"],
    "fallback_support": true|false,
    "offline_capable": true|false
  }},
  "accessibility": {{
    "captions": true,
    "audio_description": true,
    "keyboard_navigation": true,
    "high_contrast_mode": true,
    "playback_speed_control": true
  }},
  "optimization": {{
    "adaptive_streaming": true|false,
    "preload_strategy": "auto|metadata|none",
    "chunk_size": "seconds per chunk"
  }}
}}
```
"""
        
        message = MultimodalMessage(text=prompt, role="user")
        
        response = await self.llm.generate(
            [message],
            response_format={"type": "json"}
        )
        
        if response.structured_data:
            return response.structured_data
        
        # Fallback specifications
        return {
            "video": {
                "resolution": "1920x1080",
                "fps": 60,
                "codec": "h264",
                "quality_preset": "high"
            },
            "interactive": {
                "features": ["pause_points", "annotations"],
                "fallback_support": True
            }
        }
    
    def _calculate_visual_complexity(
        self,
        animation_plan: Dict[str, Any]
    ) -> float:
        """Calculate visual complexity score."""
        
        complexity_factors = []
        
        for scene in animation_plan.get("scenes", []):
            # Element count factor
            element_count = len(scene.get("elements", []))
            complexity_factors.append(min(element_count / 10, 1.0))
            
            # Animation complexity
            total_animations = sum(
                len(el.get("animations", {}).keys())
                for el in scene.get("elements", [])
            )
            complexity_factors.append(min(total_animations / 20, 1.0))
            
            # Interaction complexity
            interaction_count = len(scene.get("interaction_prompts", []))
            complexity_factors.append(min(interaction_count / 5, 1.0))
        
        if complexity_factors:
            return round(sum(complexity_factors) / len(complexity_factors), 2)
        return 0.5
    
    def _extract_interaction_design(
        self,
        animation_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract interaction design from animation plan."""
        
        interactions = {
            "pause_points": [],
            "hover_zones": [],
            "click_targets": [],
            "exploration_areas": []
        }
        
        for scene in animation_plan.get("scenes", []):
            # Extract pause points
            for checkpoint in scene.get("learning_checkpoints", []):
                interactions["pause_points"].append({
                    "time": checkpoint.get("time", 0),
                    "type": checkpoint.get("type", "optional_pause"),
                    "prompt": checkpoint.get("prompt", "")
                })
            
            # Extract interactive elements
            for element in scene.get("elements", []):
                for interaction in element.get("interactions", []):
                    int_type = interaction.get("type", "hover")
                    
                    if int_type == "hover":
                        interactions["hover_zones"].append({
                            "element_id": element.get("id"),
                            "action": interaction.get("effect", "tooltip")
                        })
                    elif int_type == "click":
                        interactions["click_targets"].append({
                            "element_id": element.get("id"),
                            "action": interaction.get("action", "show_details")
                        })
        
        return interactions
    
    async def generate_adaptive_animation(
        self,
        concept: str,
        learner_profile: Dict[str, Any],
        performance_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate animation adapted to specific learner."""
        
        prompt = f"""
Create a personalized animation plan for teaching "{concept}" to this learner:

Learner Profile:
{json.dumps(learner_profile, indent=2)}

{f"Performance Data: {json.dumps(performance_data, indent=2)}" if performance_data else ""}

Adapt the animation to:
1. Match the learner's pace and style
2. Address identified knowledge gaps
3. Build on existing understanding
4. Maintain optimal challenge level
5. Support preferred learning modalities

Output Format:
```json
{{
  "personalization_strategy": {{
    "pacing": "faster|normal|slower",
    "detail_level": "high|medium|low",
    "interaction_frequency": "high|medium|low",
    "visual_style": "abstract|concrete|mixed",
    "scaffolding_level": "minimal|moderate|extensive"
  }},
  "adapted_scenes": [
    {{
      "focus": "What this scene emphasizes for this learner",
      "modifications": ["modification1", "modification2"],
      "skip_if_understood": true|false
    }}
  ],
  "checkpoint_strategy": {{
    "assessment_points": ["where to check understanding"],
    "remediation_ready": ["concepts to reinforce if needed"]
  }}
}}
```
"""
        
        message = MultimodalMessage(text=prompt, role="user")
        
        response = await self.llm.generate([message], response_format={"type": "json"})
        
        if response.structured_data:
            # Apply personalization to standard animation
            base_animation = await self.create_animation(
                concept=concept,
                domain=learner_profile.get("domain", "general"),
                complexity=learner_profile.get("skill_level", 5),
                audience=learner_profile.get("role", "learner"),
                learning_objectives=learner_profile.get("goals", [])
            )
            
            # Apply adaptations
            return self._apply_personalization(
                base_animation,
                response.structured_data
            )
        
        # Fallback to standard animation
        return await self.create_animation(
            concept=concept,
            domain="general",
            complexity=5,
            audience="general",
            learning_objectives=[]
        )
    
    def _apply_personalization(
        self,
        base_animation: Dict[str, Any],
        personalization: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply personalization to base animation."""
        
        strategy = personalization.get("personalization_strategy", {})
        
        # Adjust pacing
        if strategy.get("pacing") == "slower":
            for scene in base_animation.get("scenes", []):
                scene["duration"] *= 1.5
        elif strategy.get("pacing") == "faster":
            for scene in base_animation.get("scenes", []):
                scene["duration"] *= 0.75
        
        # Add personalization metadata
        base_animation["personalization"] = personalization
        
        return base_animation
