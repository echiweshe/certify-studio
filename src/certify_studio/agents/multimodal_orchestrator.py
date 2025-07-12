"""
Enhanced orchestrator with full multimodal capabilities.
"""

from typing import Dict, List, Any, Optional, Callable, Tuple
from pathlib import Path
import asyncio
import json

from ..core.llm import MultimodalLLM, LLMProvider, PromptManager, PromptType
from ..core.llm.multimodal_llm import MultimodalMessage
from ..core.logging import get_logger
from .orchestrator import (
    AgenticOrchestrator as BaseOrchestrator,
    GenerationConfig, GenerationResult, GenerationPhase
)
from .certification.multimodal_domain_extraction_agent import MultimodalDomainExtractionAgent
from .content.multimodal_animation_agent import MultimodalAnimationChoreographyAgent
from .content.diagram_generation.multimodal_diagram_agent import MultimodalDiagramGenerationAgent

logger = get_logger(__name__)


class MultimodalOrchestrator(BaseOrchestrator):
    """Enhanced orchestrator with full multimodal LLM integration."""
    
    def __init__(
        self,
        llm_provider: LLMProvider = LLMProvider.ANTHROPIC_CLAUDE_VISION,
        enable_vision: bool = True,
        enable_audio: bool = True
    ):
        # Initialize multimodal LLM
        self.llm = MultimodalLLM(provider=llm_provider)
        
        # Initialize enhanced agents
        self.domain_agent = MultimodalDomainExtractionAgent(
            llm=self.llm,
            use_vision=enable_vision
        )
        self.animation_agent = MultimodalAnimationChoreographyAgent(
            llm=self.llm,
            enable_vision_analysis=enable_vision
        )
        self.diagram_agent = MultimodalDiagramGenerationAgent(
            llm=self.llm,
            enable_sketch_analysis=enable_vision
        )
        
        self.prompt_manager = PromptManager()
        self.enable_vision = enable_vision
        self.enable_audio = enable_audio
        
        # Enhanced caches
        self.visual_style_cache = {}
        self.learning_insights_cache = {}
        self.quality_metrics = {}
    
    async def generate_educational_content(
        self,
        config: GenerationConfig,
        progress_callback: Optional[Callable] = None,
        quality_threshold: float = 0.8
    ) -> GenerationResult:
        """Generate educational content with multimodal understanding."""
        
        logger.info(f"Starting multimodal generation for {config.certification_name}")
        
        try:
            # Phase 1: Enhanced domain extraction with vision
            await self._update_progress(GenerationPhase.EXTRACTION, progress_callback)
            domain = await self._extract_domain_multimodal(config)
            
            # Phase 2: Intelligent analysis and planning
            await self._update_progress(GenerationPhase.ANALYSIS, progress_callback)
            content_plan = await self._analyze_and_plan_multimodal(domain, config)
            
            # Phase 3: Generate visual content with quality checks
            await self._update_progress(GenerationPhase.GENERATION, progress_callback)
            animations, diagrams = await self._generate_visual_content_multimodal(
                domain, content_plan, config
            )
            
            # Quality assessment and iteration
            quality_score = await self._assess_content_quality(
                animations, diagrams, domain, config
            )
            
            if quality_score < quality_threshold:
                logger.info(f"Quality score {quality_score} below threshold, iterating...")
                animations, diagrams = await self._improve_content_quality(
                    animations, diagrams, domain, config
                )
            
            # Phase 4: Intelligent rendering
            await self._update_progress(GenerationPhase.RENDERING, progress_callback)
            rendered_content = await self._render_content_multimodal(
                animations, diagrams, config
            )
            
            # Phase 5: Smart export with optimization
            await self._update_progress(GenerationPhase.EXPORT, progress_callback)
            exports = await self._export_content_multimodal(
                rendered_content, config
            )
            
            # Create enhanced result
            result = GenerationResult(
                success=True,
                domain=domain,
                animations=animations,
                diagrams=diagrams,
                exports=exports,
                metadata={
                    "total_concepts": len(domain.concepts),
                    "total_animations": len(animations),
                    "total_diagrams": len(diagrams),
                    "generation_time": "2024-01-20T10:00:00Z",
                    "quality_score": quality_score,
                    "llm_provider": self.llm.provider.value,
                    "multimodal_features": {
                        "vision_enabled": self.enable_vision,
                        "audio_enabled": self.enable_audio
                    },
                    "config": config.__dict__
                }
            )
            
            logger.info("Multimodal generation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Multimodal generation failed: {str(e)}")
            return GenerationResult(
                success=False,
                domain=None,
                animations=[],
                diagrams=[],
                exports={},
                metadata={"error": str(e)},
                errors=[str(e)]
            )
    
    async def _extract_domain_multimodal(
        self,
        config: GenerationConfig
    ) -> Any:
        """Extract domain with multimodal understanding."""
        
        # Use enhanced extraction
        domain = await self.domain_agent.extract_domain(
            file_path=config.certification_path,
            certification_name=config.certification_name,
            exam_code=config.exam_code
        )
        
        # Analyze visual learning potential for each concept
        for concept_id, concept in domain.concepts.items():
            visual_analysis = await self.domain_agent.analyze_concept_visual_potential(
                concept
            )
            concept.animation_hints.update(visual_analysis)
        
        return domain
    
    async def _analyze_and_plan_multimodal(
        self,
        domain: Any,
        config: GenerationConfig
    ) -> Dict[str, Any]:
        """Create content plan with multimodal insights."""
        
        # Get base plan
        base_plan = await self._analyze_and_plan(domain, config)
        
        # Enhance with multimodal synthesis
        synthesis_prompt = self.prompt_manager.get_prompt(
            PromptType.CONTENT_SYNTHESIS,
            {
                "concepts": json.dumps([
                    {"name": c.name, "type": c.type.value}
                    for c in list(domain.concepts.values())[:20]
                ]),
                "objectives": json.dumps(domain.key_themes),
                "duration": config.video_duration_target,
                "audience": config.target_audience
            }
        )
        
        message = MultimodalMessage(text=synthesis_prompt, role="user")
        synthesis_response = await self.llm.generate(
            [message],
            response_format={"type": "json"}
        )
        
        if synthesis_response.structured_data:
            # Merge synthesis insights
            base_plan["narrative_theme"] = synthesis_response.structured_data.get(
                "narrative_theme", {}
            )
            base_plan["multimodal_elements"] = synthesis_response.structured_data.get(
                "multimodal_elements", {}
            )
            base_plan["content_modules"] = synthesis_response.structured_data.get(
                "content_modules", base_plan["sections"]
            )
        
        return base_plan
    
    async def _generate_visual_content_multimodal(
        self,
        domain: Any,
        content_plan: Dict[str, Any],
        config: GenerationConfig
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Generate visual content with multimodal understanding."""
        
        animations = []
        diagrams = []
        
        # Extract visual style from plan
        visual_style = content_plan.get("multimodal_elements", {}).get(
            "visual_anchors", "modern"
        )
        
        # Generate content for each module
        for module in content_plan.get("content_modules", content_plan["sections"]):
            module_concepts = module.get("concepts", [])
            
            # Generate animations with visual coherence
            for concept in module_concepts:
                # Check if we have reference materials
                reference_materials = await self._gather_reference_materials(
                    concept, domain
                )
                
                animation = await self.animation_agent.create_animation(
                    concept=concept.name,
                    domain=domain.domain_name,
                    complexity=concept.complexity,
                    audience=config.target_audience,
                    learning_objectives=concept.prerequisites[:3],
                    constraints={
                        "max_duration": module.get("duration", 60)
                    },
                    reference_materials=reference_materials
                )
                
                animations.append(animation)
            
            # Generate module diagram with consistent style
            if module_concepts:
                module_relationships = [
                    (r.source_id, r.target_id, r.relationship_type.value)
                    for r in domain.relationships
                    if any(r.source_id == c.id or r.target_id == c.id 
                          for c in module_concepts)
                ]
                
                if module_relationships:
                    # Get reference diagrams from cache
                    reference_diagrams = self.visual_style_cache.get(
                        f"{domain.domain_name}_diagrams", []
                    )
                    
                    diagram = await self.diagram_agent.generate_diagram(
                        concepts=module_concepts,
                        relationships=module_relationships,
                        requirements={
                            "viewer_profile": {
                                "expertise": self._map_audience_to_expertise(
                                    config.target_audience
                                )
                            },
                            "style_theme": config.style_theme
                        },
                        reference_diagrams=reference_diagrams[:3]
                    )
                    
                    diagrams.append(diagram)
        
        # Generate comprehensive overview with all insights
        overview_diagram = await self._generate_intelligent_overview(
            domain, content_plan, animations, diagrams
        )
        diagrams.insert(0, overview_diagram)
        
        logger.info(
            f"Generated {len(animations)} animations and {len(diagrams)} diagrams "
            f"with multimodal understanding"
        )
        
        return animations, diagrams
    
    async def _gather_reference_materials(
        self,
        concept: Any,
        domain: Any
    ) -> Optional[Dict[str, Any]]:
        """Gather reference materials for concept."""
        
        materials = {}
        
        # Check cache for existing materials
        cache_key = f"{domain.domain_name}_{concept.type.value}"
        if cache_key in self.visual_style_cache:
            materials["images"] = self.visual_style_cache[cache_key]
        
        # Add concept-specific visual hints
        if concept.visual_metaphor_suggestions:
            materials["metaphors"] = concept.visual_metaphor_suggestions
        
        return materials if materials else None
    
    async def _generate_intelligent_overview(
        self,
        domain: Any,
        content_plan: Dict[str, Any],
        animations: List[Dict[str, Any]],
        diagrams: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate intelligent overview diagram."""
        
        # Analyze all generated content
        content_summary = {
            "total_concepts": len(domain.concepts),
            "animated_concepts": len(animations),
            "diagram_count": len(diagrams),
            "key_themes": domain.key_themes,
            "narrative_arc": content_plan.get("narrative_theme", {})
        }
        
        prompt = f"""
Design an overview diagram that synthesizes this educational content:

{json.dumps(content_summary, indent=2)}

Create a visual overview that:
1. Shows the learning journey
2. Highlights key connections
3. Provides navigation structure
4. Maintains visual consistency
5. Engages learners

Output the most important 15-20 concepts and their relationships.
"""
        
        message = MultimodalMessage(text=prompt, role="user")
        response = await self.llm.generate([message])
        
        # Generate overview using insights
        return await self.diagram_agent.generate_sketch_from_description(
            response.text,
            style_preferences={
                "type": "overview",
                "emphasis": "learning_path",
                "style": content_plan.get("visual_strategy", {})
            }
        )
    
    async def _assess_content_quality(
        self,
        animations: List[Dict[str, Any]],
        diagrams: List[Dict[str, Any]],
        domain: Any,
        config: GenerationConfig
    ) -> float:
        """Assess quality of generated content."""
        
        # Prepare content summary
        content_spec = {
            "animations": [
                {
                    "concept": a["concept"],
                    "duration": a["total_duration"],
                    "scene_count": a["scene_count"],
                    "complexity": a.get("metadata", {}).get("visual_complexity", 0.5)
                }
                for a in animations[:10]
            ],
            "diagrams": [
                {
                    "type": d["type"],
                    "elements": d["element_count"],
                    "complexity": d.get("metadata", {}).get("complexity_score", 0.5)
                }
                for d in diagrams[:10]
            ],
            "learning_objectives": domain.key_themes,
            "target_audience": config.target_audience,
            "total_duration": sum(a["total_duration"] for a in animations)
        }
        
        # Get quality assessment prompt
        prompt = self.prompt_manager.get_prompt(
            PromptType.QUALITY_ASSESSMENT,
            {"content_spec": json.dumps(content_spec, indent=2)}
        )
        
        message = MultimodalMessage(text=prompt, role="user")
        response = await self.llm.generate(
            [message],
            response_format={"type": "json"}
        )
        
        if response.structured_data:
            quality_data = response.structured_data
            
            # Store quality metrics
            self.quality_metrics = {
                "overall_score": quality_data.get("overall_score", 80),
                "dimensions": quality_data.get("dimension_scores", {}),
                "strengths": quality_data.get("strengths", []),
                "improvements": quality_data.get("improvements_needed", [])
            }
            
            return quality_data.get("overall_score", 80) / 100
        
        return 0.8  # Default quality score
    
    async def _improve_content_quality(
        self,
        animations: List[Dict[str, Any]],
        diagrams: List[Dict[str, Any]],
        domain: Any,
        config: GenerationConfig
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Improve content based on quality assessment."""
        
        improvements = self.quality_metrics.get("improvements", [])
        
        for improvement in improvements:
            if improvement.get("priority") in ["critical", "high"]:
                issue = improvement["issue"]
                
                if "pacing" in issue.lower():
                    # Adjust animation pacing
                    animations = await self._adjust_pacing(
                        animations, improvement["suggestion"]
                    )
                
                elif "clarity" in issue.lower():
                    # Simplify complex diagrams
                    diagrams = await self._improve_diagram_clarity(
                        diagrams, domain
                    )
                
                elif "engagement" in issue.lower():
                    # Add more interactive elements
                    animations = await self._enhance_engagement(
                        animations, config.target_audience
                    )
        
        return animations, diagrams
    
    async def _adjust_pacing(
        self,
        animations: List[Dict[str, Any]],
        suggestion: str
    ) -> List[Dict[str, Any]]:
        """Adjust animation pacing based on suggestion."""
        
        if "slow" in suggestion.lower():
            # Slow down animations
            for animation in animations:
                for scene in animation.get("scenes", []):
                    scene["duration"] *= 1.3
                animation["total_duration"] *= 1.3
        
        elif "fast" in suggestion.lower():
            # Speed up animations
            for animation in animations:
                for scene in animation.get("scenes", []):
                    scene["duration"] *= 0.8
                animation["total_duration"] *= 0.8
        
        return animations
    
    async def _improve_diagram_clarity(
        self,
        diagrams: List[Dict[str, Any]],
        domain: Any
    ) -> List[Dict[str, Any]]:
        """Improve diagram clarity."""
        
        improved_diagrams = []
        
        for diagram in diagrams:
            if diagram["element_count"] > 15:
                # Simplify complex diagrams
                logger.info(f"Simplifying diagram {diagram['diagram_id']}")
                
                # Re-generate with simplification
                concepts = [
                    domain.concepts[el_id]
                    for el_id in list(diagram["diagram"]["elements"].keys())[:10]
                    if el_id in domain.concepts
                ]
                
                relationships = [
                    (e["source"], e["target"], e["type"])
                    for e in diagram["diagram"]["edges"][:15]
                ]
                
                simplified = await self.diagram_agent.generate_diagram(
                    concepts,
                    relationships,
                    {"simplify": True}
                )
                
                improved_diagrams.append(simplified)
            else:
                improved_diagrams.append(diagram)
        
        return improved_diagrams
    
    async def _enhance_engagement(
        self,
        animations: List[Dict[str, Any]],
        audience: str
    ) -> List[Dict[str, Any]]:
        """Enhance engagement with interactive elements."""
        
        for animation in animations:
            # Add interaction points
            for scene in animation.get("scenes", []):
                if not scene.get("interaction_prompts"):
                    scene["interaction_prompts"] = [
                        "Click to explore details",
                        "Hover for more information"
                    ]
                
                # Add learning checkpoints
                if len(scene.get("elements", [])) > 5:
                    scene["learning_checkpoints"] = [
                        {
                            "time": scene["duration"] / 2,
                            "type": "pause_for_understanding",
                            "prompt": "Take a moment to understand the connections"
                        }
                    ]
        
        return animations
    
    async def _render_content_multimodal(
        self,
        animations: List[Dict[str, Any]],
        diagrams: List[Dict[str, Any]],
        config: GenerationConfig
    ) -> Dict[str, Any]:
        """Render content with multimodal enhancements."""
        
        # Base rendering
        rendered = await self._render_content(animations, diagrams, config)
        
        # Add multimodal enhancements
        rendered["multimodal_features"] = {
            "narration": await self._generate_narration(
                rendered["scenes"], config
            ),
            "background_music": await self._select_background_music(
                rendered, config
            ),
            "sound_effects": await self._generate_sound_effects(
                rendered["scenes"]
            ),
            "captions": await self._generate_captions(
                rendered["scenes"]
            )
        }
        
        return rendered
    
    async def _generate_narration(
        self,
        scenes: List[Dict[str, Any]],
        config: GenerationConfig
    ) -> List[Dict[str, Any]]:
        """Generate narration for scenes."""
        
        narrations = []
        
        for scene in scenes:
            prompt = f"""
Generate engaging narration for this educational scene:

Scene Type: {scene['type']}
Duration: {scene['duration']} seconds
Content: {scene.get('content', {}).get('title', 'Educational content')}
Audience: {config.target_audience}

Create narration that:
1. Explains clearly
2. Maintains engagement
3. Uses appropriate pace
4. Includes learning cues

Output Format:
```json
{{
  "text": "Narration text",
  "timing": [{"start": 0, "end": 2, "text": "segment"}],
  "emphasis_words": ["important", "key", "concept"],
  "pace": "slow|normal|energetic"
}}
```
"""
            
            message = MultimodalMessage(text=prompt, role="user")
            response = await self.llm.generate(
                [message],
                response_format={"type": "json"}
            )
            
            if response.structured_data:
                narrations.append(response.structured_data)
            else:
                # Fallback narration
                narrations.append({
                    "text": f"Let's explore {scene.get('content', {}).get('title', 'this concept')}.",
                    "pace": "normal"
                })
        
        return narrations
    
    async def _select_background_music(
        self,
        rendered_content: Dict[str, Any],
        config: GenerationConfig
    ) -> Dict[str, Any]:
        """Select appropriate background music."""
        
        # Analyze content mood
        total_duration = rendered_content["total_duration"]
        scene_types = [s["type"] for s in rendered_content["scenes"]]
        
        prompt = f"""
Select background music for educational content:

Duration: {total_duration} seconds
Scene Types: {scene_types}
Target Audience: {config.target_audience}
Style: {config.style_theme}

Recommend:
1. Music style/genre
2. Tempo and energy level
3. Key moments for emphasis
4. Volume dynamics
"""
        
        message = MultimodalMessage(text=prompt, role="user")
        response = await self.llm.generate([message])
        
        return {
            "style": "ambient_educational",
            "tempo": "moderate",
            "volume_profile": "dynamic",
            "recommendations": response.text
        }
    
    async def _generate_sound_effects(
        self,
        scenes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate sound effect specifications."""
        
        sound_effects = []
        
        for scene in scenes:
            effects = []
            
            # Analyze scene for sound opportunities
            if scene["type"] == "animation":
                content = scene.get("content", {})
                
                # Add effects for animations
                for element in content.get("elements", []):
                    if element.get("animations", {}).get("enter", {}).get("type") == "grow":
                        effects.append({
                            "type": "whoosh",
                            "timing": element.get("enter_time", 0),
                            "volume": 0.3
                        })
                    
                    if "click" in str(element.get("interactions", [])):
                        effects.append({
                            "type": "click",
                            "trigger": "on_interaction",
                            "volume": 0.5
                        })
            
            sound_effects.append(effects)
        
        return sound_effects
    
    async def _generate_captions(
        self,
        scenes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate accessibility captions."""
        
        captions = []
        
        for scene in scenes:
            scene_captions = {
                "narration": scene.get("narration", ""),
                "visual_descriptions": [],
                "sound_descriptions": []
            }
            
            # Add visual descriptions for accessibility
            if scene["type"] == "diagram":
                scene_captions["visual_descriptions"].append(
                    f"Diagram showing {scene.get('content', {}).get('title', 'relationships')}"
                )
            elif scene["type"] == "animation":
                scene_captions["visual_descriptions"].append(
                    f"Animation demonstrating {scene.get('content', {}).get('concept', 'concept')}"
                )
            
            captions.append(scene_captions)
        
        return captions
    
    async def _export_content_multimodal(
        self,
        rendered_content: Dict[str, Any],
        config: GenerationConfig
    ) -> Dict[str, Path]:
        """Export content with multimodal features."""
        
        exports = await self._export_content(rendered_content, config)
        
        # Add multimodal exports
        if "narration" in rendered_content.get("multimodal_features", {}):
            # Export narration script
            narration_path = config.output_path / f"{config.exam_code}_narration.txt"
            await self._export_narration_script(
                rendered_content["multimodal_features"]["narration"],
                narration_path
            )
            exports["narration"] = narration_path
        
        # Export accessibility package
        if config.enable_interactivity:
            accessibility_path = config.output_path / f"{config.exam_code}_accessibility.json"
            await self._export_accessibility_data(
                rendered_content,
                accessibility_path
            )
            exports["accessibility"] = accessibility_path
        
        return exports
    
    async def _export_narration_script(
        self,
        narrations: List[Dict[str, Any]],
        output_path: Path
    ) -> None:
        """Export narration as script."""
        
        script_lines = []
        
        for i, narration in enumerate(narrations):
            script_lines.append(f"Scene {i + 1}:")
            script_lines.append(narration.get("text", ""))
            script_lines.append(f"Pace: {narration.get('pace', 'normal')}")
            
            if narration.get("emphasis_words"):
                script_lines.append(
                    f"Emphasize: {', '.join(narration['emphasis_words'])}"
                )
            
            script_lines.append("")  # Empty line between scenes
        
        output_path.write_text("\n".join(script_lines))
        logger.info(f"Exported narration script to {output_path}")
    
    async def _export_accessibility_data(
        self,
        rendered_content: Dict[str, Any],
        output_path: Path
    ) -> None:
        """Export accessibility data."""
        
        accessibility_data = {
            "captions": rendered_content.get("multimodal_features", {}).get("captions", []),
            "audio_descriptions": rendered_content.get("multimodal_features", {}).get("narration", []),
            "interaction_guides": self._generate_interaction_guides(rendered_content),
            "navigation_structure": self._generate_navigation_structure(rendered_content)
        }
        
        with open(output_path, 'w') as f:
            json.dump(accessibility_data, f, indent=2)
        
        logger.info(f"Exported accessibility data to {output_path}")
    
    def _generate_interaction_guides(
        self,
        rendered_content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate guides for interactions."""
        
        guides = []
        
        for scene in rendered_content.get("scenes", []):
            if scene["type"] == "animation":
                content = scene.get("content", {})
                interactions = content.get("interaction_design", {})
                
                if interactions:
                    guides.append({
                        "scene_index": len(guides),
                        "interactions": interactions,
                        "keyboard_shortcuts": {
                            "space": "pause/play",
                            "arrow_right": "next element",
                            "arrow_left": "previous element",
                            "enter": "activate interaction"
                        }
                    })
        
        return guides
    
    def _generate_navigation_structure(
        self,
        rendered_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate navigation structure for content."""
        
        structure = {
            "total_scenes": len(rendered_content.get("scenes", [])),
            "chapters": [],
            "bookmarks": []
        }
        
        current_time = 0
        for i, scene in enumerate(rendered_content.get("scenes", [])):
            chapter = {
                "index": i,
                "title": scene.get("content", {}).get("title", f"Scene {i + 1}"),
                "start_time": current_time,
                "duration": scene.get("duration", 0),
                "type": scene["type"]
            }
            structure["chapters"].append(chapter)
            
            # Add bookmarks for important moments
            if scene["type"] == "diagram" or i == 0:
                structure["bookmarks"].append({
                    "time": current_time,
                    "label": chapter["title"],
                    "importance": "high" if i == 0 else "medium"
                })
            
            current_time += scene.get("duration", 0)
        
        return structure
