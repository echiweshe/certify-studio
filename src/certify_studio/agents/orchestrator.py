"""
Master orchestrator for the agentic animation system.

This orchestrator coordinates all agents to create a seamless pipeline from
certification content to animated educational videos.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from pathlib import Path
import json

from langchain.chat_models.base import BaseChatModel

from ..core.logging import get_logger
from .certification.domain_extraction_agent import DomainExtractionAgent, LearningDomain
from .content.animation_choreography_agent import AnimationChoreographyAgent
from .content.diagram_generation_agent import DiagramGenerationAgent

logger = get_logger(__name__)


class GenerationPhase(Enum):
    """Phases of the generation pipeline."""
    EXTRACTION = "extraction"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    GENERATION = "generation"
    RENDERING = "rendering"
    EXPORT = "export"


@dataclass
class GenerationConfig:
    """Configuration for the generation pipeline."""
    certification_path: Path
    output_path: Path
    certification_name: str
    exam_code: str
    target_audience: str = "intermediate_developers"
    video_duration_target: int = 300  # seconds
    export_formats: List[str] = None
    style_theme: str = "modern"
    enable_interactivity: bool = True
    progressive_learning: bool = True
    
    def __post_init__(self):
        if self.export_formats is None:
            self.export_formats = ["mp4", "interactive_html"]


@dataclass
class GenerationResult:
    """Result of the generation pipeline."""
    success: bool
    domain: Optional[LearningDomain]
    animations: List[Dict[str, Any]]
    diagrams: List[Dict[str, Any]]
    exports: Dict[str, Path]
    metadata: Dict[str, Any]
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class AgenticOrchestrator:
    """Master orchestrator for coordinating all agents."""
    
    def __init__(self, llm: Optional[BaseChatModel] = None):
        self.llm = llm
        self.domain_agent = DomainExtractionAgent(llm)
        self.animation_agent = AnimationChoreographyAgent(llm)
        self.diagram_agent = DiagramGenerationAgent(llm)
        self.current_phase = None
        self.generation_cache = {}
    
    async def generate_educational_content(
        self,
        config: GenerationConfig,
        progress_callback: Optional[callable] = None
    ) -> GenerationResult:
        """Generate complete educational content from certification."""
        
        logger.info(f"Starting generation for {config.certification_name}")
        
        errors = []
        
        try:
            # Phase 1: Extract domain knowledge
            await self._update_progress(GenerationPhase.EXTRACTION, progress_callback)
            domain = await self._extract_domain(config)
            
            # Phase 2: Analyze and plan content
            await self._update_progress(GenerationPhase.ANALYSIS, progress_callback)
            content_plan = await self._analyze_and_plan(domain, config)
            
            # Phase 3: Generate animations and diagrams
            await self._update_progress(GenerationPhase.GENERATION, progress_callback)
            animations, diagrams = await self._generate_visual_content(
                domain, content_plan, config
            )
            
            # Phase 4: Render content
            await self._update_progress(GenerationPhase.RENDERING, progress_callback)
            rendered_content = await self._render_content(
                animations, diagrams, config
            )
            
            # Phase 5: Export in requested formats
            await self._update_progress(GenerationPhase.EXPORT, progress_callback)
            exports = await self._export_content(
                rendered_content, config
            )
            
            # Create result
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
                    "config": config.__dict__
                }
            )
            
            logger.info("Generation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            errors.append(str(e))
            
            return GenerationResult(
                success=False,
                domain=None,
                animations=[],
                diagrams=[],
                exports={},
                metadata={"error": str(e)},
                errors=errors
            )
    
    async def _update_progress(
        self,
        phase: GenerationPhase,
        callback: Optional[callable]
    ) -> None:
        """Update progress through callback."""
        
        self.current_phase = phase
        if callback:
            await callback(phase, phase.value)
    
    async def _extract_domain(
        self,
        config: GenerationConfig
    ) -> LearningDomain:
        """Extract domain knowledge from certification content."""
        
        logger.info(f"Extracting domain from {config.certification_path}")
        
        domain = await self.domain_agent.extract_domain(
            file_path=config.certification_path,
            certification_name=config.certification_name,
            exam_code=config.exam_code
        )
        
        # Cache the domain for potential reuse
        cache_key = f"{config.certification_name}_{config.exam_code}"
        self.generation_cache[cache_key] = domain
        
        logger.info(f"Extracted {len(domain.concepts)} concepts")
        return domain
    
    async def _analyze_and_plan(
        self,
        domain: LearningDomain,
        config: GenerationConfig
    ) -> Dict[str, Any]:
        """Analyze domain and create content plan."""
        
        logger.info("Analyzing domain and planning content")
        
        # Calculate time allocation
        time_per_concept = config.video_duration_target / len(domain.concepts)
        
        # Group concepts by learning paths
        content_sections = []
        
        for path_index, learning_path in enumerate(domain.learning_paths):
            section_concepts = [
                domain.concepts[concept_id]
                for concept_id in learning_path
                if concept_id in domain.concepts
            ]
            
            if section_concepts:
                content_sections.append({
                    "section_id": f"section_{path_index}",
                    "title": f"Learning Path {path_index + 1}",
                    "concepts": section_concepts,
                    "duration": len(section_concepts) * time_per_concept,
                    "complexity_progression": [c.complexity for c in section_concepts]
                })
        
        # Create visual strategy
        visual_strategy = await self._determine_visual_strategy(
            domain, config
        )
        
        content_plan = {
            "sections": content_sections,
            "total_duration": config.video_duration_target,
            "visual_strategy": visual_strategy,
            "transitions": self._plan_transitions(content_sections),
            "narrative_structure": self._create_narrative_structure(domain)
        }
        
        logger.info(f"Created plan with {len(content_sections)} sections")
        return content_plan
    
    async def _determine_visual_strategy(
        self,
        domain: LearningDomain,
        config: GenerationConfig
    ) -> Dict[str, Any]:
        """Determine the visual strategy based on content."""
        
        # Analyze concept types to determine best visual approaches
        concept_types = {}
        for concept in domain.concepts.values():
            concept_types[concept.type] = concept_types.get(concept.type, 0) + 1
        
        # Determine primary visual style
        if domain.domain_name.startswith("cloud"):
            primary_style = "technical_modern"
            color_scheme = "aws" if "aws" in domain.domain_name else "modern"
        elif "security" in domain.domain_name:
            primary_style = "security_focused"
            color_scheme = "security"
        else:
            primary_style = "educational_clean"
            color_scheme = "modern"
        
        return {
            "primary_style": primary_style,
            "color_scheme": color_scheme,
            "animation_pacing": "dynamic" if config.target_audience == "experts" else "measured",
            "diagram_complexity": "detailed" if len(domain.concepts) < 20 else "simplified",
            "interaction_level": "high" if config.enable_interactivity else "low"
        }
    
    def _plan_transitions(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Plan transitions between sections."""
        
        transitions = []
        
        for i in range(len(sections) - 1):
            current_section = sections[i]
            next_section = sections[i + 1]
            
            # Determine transition type based on complexity change
            complexity_change = (
                next_section["complexity_progression"][0] - 
                current_section["complexity_progression"][-1]
            )
            
            if complexity_change > 2:
                transition_type = "fade_with_summary"
            elif complexity_change < -2:
                transition_type = "quick_recap"
            else:
                transition_type = "smooth_flow"
            
            transitions.append({
                "from_section": current_section["section_id"],
                "to_section": next_section["section_id"],
                "type": transition_type,
                "duration": 2.0
            })
        
        return transitions
    
    def _create_narrative_structure(
        self,
        domain: LearningDomain
    ) -> Dict[str, Any]:
        """Create narrative structure for the content."""
        
        return {
            "opening": {
                "type": "problem_statement",
                "duration": 10,
                "content": f"Understanding {domain.certification_name}"
            },
            "development": {
                "type": "progressive_disclosure",
                "key_themes": domain.key_themes[:3]
            },
            "conclusion": {
                "type": "summary_with_applications",
                "duration": 15,
                "key_takeaways": [
                    f"Master {theme}" for theme in domain.key_themes[:3]
                ]
            }
        }
    
    async def _generate_visual_content(
        self,
        domain: LearningDomain,
        content_plan: Dict[str, Any],
        config: GenerationConfig
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Generate animations and diagrams."""
        
        logger.info("Generating visual content")
        
        animations = []
        diagrams = []
        
        for section in content_plan["sections"]:
            # Generate animations for each concept
            for concept in section["concepts"]:
                # Create animation
                animation = await self.animation_agent.create_animation(
                    concept=concept.name,
                    domain=domain.domain_name,
                    complexity=concept.complexity,
                    audience=config.target_audience,
                    learning_objectives=concept.prerequisites,
                    constraints={
                        "max_duration": content_plan["total_duration"] / len(domain.concepts)
                    }
                )
                animations.append(animation)
            
            # Generate diagrams showing relationships
            section_relationships = [
                (r.source_id, r.target_id, r.relationship_type.value)
                for r in domain.relationships
                if r.source_id in [c.id for c in section["concepts"]]
                or r.target_id in [c.id for c in section["concepts"]]
            ]
            
            if section_relationships:
                diagram = await self.diagram_agent.generate_diagram(
                    concepts=section["concepts"],
                    relationships=section_relationships,
                    requirements={
                        "viewer_profile": {
                            "expertise": self._map_audience_to_expertise(config.target_audience)
                        }
                    }
                )
                diagrams.append(diagram)
        
        # Generate overview diagram
        overview_diagram = await self._generate_overview_diagram(
            domain, content_plan
        )
        diagrams.insert(0, overview_diagram)
        
        logger.info(f"Generated {len(animations)} animations and {len(diagrams)} diagrams")
        return animations, diagrams
    
    def _map_audience_to_expertise(self, audience: str) -> str:
        """Map target audience to expertise level."""
        
        mapping = {
            "beginner_developers": "beginner",
            "intermediate_developers": "intermediate",
            "senior_developers": "expert",
            "architects": "expert",
            "students": "beginner"
        }
        
        return mapping.get(audience, "intermediate")
    
    async def _generate_overview_diagram(
        self,
        domain: LearningDomain,
        content_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate overview diagram of entire domain."""
        
        # Select most important concepts
        important_concepts = sorted(
            domain.concepts.values(),
            key=lambda c: c.importance,
            reverse=True
        )[:15]  # Limit to 15 for clarity
        
        # Get relationships between important concepts
        important_ids = {c.id for c in important_concepts}
        overview_relationships = [
            (r.source_id, r.target_id, r.relationship_type.value)
            for r in domain.relationships
            if r.source_id in important_ids and r.target_id in important_ids
        ]
        
        overview_diagram = await self.diagram_agent.generate_diagram(
            concepts=important_concepts,
            relationships=overview_relationships,
            requirements={
                "type": "ARCHITECTURE",
                "viewer_profile": {"expertise": "intermediate"}
            }
        )
        
        overview_diagram["title"] = f"{domain.certification_name} Overview"
        return overview_diagram
    
    async def _render_content(
        self,
        animations: List[Dict[str, Any]],
        diagrams: List[Dict[str, Any]],
        config: GenerationConfig
    ) -> Dict[str, Any]:
        """Render animations and diagrams using Manim."""
        
        logger.info("Rendering content with Manim")
        
        # This would integrate with the Manim rendering service
        # For now, we'll create a specification
        
        rendered_content = {
            "scenes": [],
            "total_duration": 0
        }
        
        # Add overview diagram as first scene
        if diagrams:
            overview_scene = {
                "type": "diagram",
                "content": diagrams[0],
                "duration": 5.0,
                "transitions": {
                    "in": "fade",
                    "out": "zoom_to_detail"
                }
            }
            rendered_content["scenes"].append(overview_scene)
            rendered_content["total_duration"] += 5.0
        
        # Interleave animations and diagrams
        for i, animation in enumerate(animations):
            # Add animation scene
            animation_scene = {
                "type": "animation",
                "content": animation,
                "duration": animation["total_duration"],
                "transitions": {
                    "in": "smooth",
                    "out": "fade"
                }
            }
            rendered_content["scenes"].append(animation_scene)
            rendered_content["total_duration"] += animation["total_duration"]
            
            # Add diagram after every 3 animations
            if (i + 1) % 3 == 0 and (i // 3 + 1) < len(diagrams):
                diagram_scene = {
                    "type": "diagram",
                    "content": diagrams[i // 3 + 1],
                    "duration": 3.0,
                    "transitions": {
                        "in": "fade",
                        "out": "fade"
                    }
                }
                rendered_content["scenes"].append(diagram_scene)
                rendered_content["total_duration"] += 3.0
        
        logger.info(f"Created {len(rendered_content['scenes'])} scenes")
        return rendered_content
    
    async def _export_content(
        self,
        rendered_content: Dict[str, Any],
        config: GenerationConfig
    ) -> Dict[str, Path]:
        """Export content in requested formats."""
        
        logger.info(f"Exporting content in formats: {config.export_formats}")
        
        exports = {}
        
        for format in config.export_formats:
            if format == "mp4":
                export_path = config.output_path / f"{config.exam_code}_educational.mp4"
                # In production, this would call Manim's export
                exports["mp4"] = export_path
                
            elif format == "interactive_html":
                export_path = config.output_path / f"{config.exam_code}_interactive.html"
                await self._export_interactive_html(
                    rendered_content, export_path, config
                )
                exports["interactive_html"] = export_path
                
            elif format == "pdf":
                export_path = config.output_path / f"{config.exam_code}_slides.pdf"
                # Export as PDF slides
                exports["pdf"] = export_path
        
        # Save metadata
        metadata_path = config.output_path / f"{config.exam_code}_metadata.json"
        await self._save_metadata(rendered_content, metadata_path, config)
        exports["metadata"] = metadata_path
        
        logger.info(f"Exported content to {len(exports)} formats")
        return exports
    
    async def _export_interactive_html(
        self,
        content: Dict[str, Any],
        output_path: Path,
        config: GenerationConfig
    ) -> None:
        """Export as interactive HTML with navigation."""
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Interactive Educational Content</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .scene {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .controls {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }}
        .btn {{
            padding: 10px 20px;
            background: #1976D2;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        .btn:hover {{
            background: #1565C0;
        }}
        .progress {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: #E3F2FD;
        }}
        .progress-bar {{
            height: 100%;
            background: #1976D2;
            width: 0%;
            transition: width 0.3s;
        }}
    </style>
</head>
<body>
    <div class="progress">
        <div class="progress-bar"></div>
    </div>
    
    <div class="container">
        <h1>{title}</h1>
        
        <div id="scenes">
            {scenes_html}
        </div>
    </div>
    
    <div class="controls">
        <button class="btn" onclick="previousScene()">Previous</button>
        <button class="btn" onclick="playPause()">Play/Pause</button>
        <button class="btn" onclick="nextScene()">Next</button>
    </div>
    
    <script>
        let currentScene = 0;
        const totalScenes = {total_scenes};
        
        function showScene(index) {{
            // Implementation for showing specific scene
            currentScene = index;
            updateProgress();
        }}
        
        function nextScene() {{
            if (currentScene < totalScenes - 1) {{
                showScene(currentScene + 1);
            }}
        }}
        
        function previousScene() {{
            if (currentScene > 0) {{
                showScene(currentScene - 1);
            }}
        }}
        
        function updateProgress() {{
            const progress = ((currentScene + 1) / totalScenes) * 100;
            document.querySelector('.progress-bar').style.width = progress + '%';
        }}
        
        function playPause() {{
            // Implementation for play/pause functionality
        }}
        
        // Initialize
        showScene(0);
    </script>
</body>
</html>
        """
        
        # Generate HTML for scenes
        scenes_html = []
        for i, scene in enumerate(content["scenes"]):
            scene_html = f"""
            <div class="scene" id="scene-{i}">
                <h2>Scene {i + 1}: {scene['type'].title()}</h2>
                <div class="scene-content">
                    <!-- Rendered content would go here -->
                    <pre>{json.dumps(scene['content'], indent=2)}</pre>
                </div>
            </div>
            """
            scenes_html.append(scene_html)
        
        # Format and save HTML
        html_content = html_template.format(
            title=config.certification_name,
            scenes_html="\n".join(scenes_html),
            total_scenes=len(content["scenes"])
        )
        
        output_path.write_text(html_content)
        logger.info(f"Exported interactive HTML to {output_path}")
    
    async def _save_metadata(
        self,
        content: Dict[str, Any],
        output_path: Path,
        config: GenerationConfig
    ) -> None:
        """Save generation metadata."""
        
        metadata = {
            "certification": {
                "name": config.certification_name,
                "exam_code": config.exam_code,
                "source_file": str(config.certification_path)
            },
            "generation": {
                "timestamp": "2024-01-20T10:00:00Z",
                "total_scenes": len(content["scenes"]),
                "total_duration": content["total_duration"],
                "target_audience": config.target_audience
            },
            "content_stats": {
                "animation_count": sum(1 for s in content["scenes"] if s["type"] == "animation"),
                "diagram_count": sum(1 for s in content["scenes"] if s["type"] == "diagram")
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved metadata to {output_path}")


# Example usage
if __name__ == "__main__":
    async def progress_callback(phase: GenerationPhase, message: str):
        print(f"[{phase.value}] {message}")
    
    async def test_orchestrator():
        config = GenerationConfig(
            certification_path=Path("aws_saa_c03.pdf"),
            output_path=Path("output/"),
            certification_name="AWS Solutions Architect Associate",
            exam_code="SAA-C03",
            target_audience="intermediate_developers",
            video_duration_target=600,  # 10 minutes
            export_formats=["mp4", "interactive_html"]
        )
        
        orchestrator = AgenticOrchestrator()
        result = await orchestrator.generate_educational_content(
            config,
            progress_callback
        )
        
        if result.success:
            print(f"Successfully generated content!")
            print(f"Total concepts: {result.metadata['total_concepts']}")
            print(f"Total animations: {result.metadata['total_animations']}")
            print(f"Exports: {list(result.exports.keys())}")
        else:
            print(f"Generation failed: {result.errors}")
    
    asyncio.run(test_orchestrator())
