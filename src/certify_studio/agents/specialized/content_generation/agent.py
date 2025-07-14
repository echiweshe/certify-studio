"""
Content Generation Agent - Main Orchestrator.

This agent coordinates all content generation modules to create high-quality,
accessible, and pedagogically effective educational content.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid

from loguru import logger
from pydantic import BaseModel, Field

from .models import (
    ContentGenerationRequest,
    ContentPiece,
    MediaType,
    ContentType,
    InteractionType,
    QualityMetrics,
    ContentMetadata
)
from .diagram_generator import DiagramGenerator
from .animation_engine import AnimationEngine
from .interactive_builder import InteractiveBuilder
from .style_manager import StyleManager, DomainStyle
from .accessibility import AccessibilityManager, AccessibilityStandard
from .quality_validator import QualityValidator

from ....agents.core.autonomous_agent import (
    AutonomousAgent,
    AgentCapability,
    AgentState,
    AgentBelief,
    AgentGoal,
    AgentPlan
)
from ....config import settings


class PlanStep(BaseModel):
    """A single step in a content generation plan."""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str
    module: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    expected_output: str
    duration_estimate: float = 0.0
    dependencies: List[str] = Field(default_factory=list)


class ContentGenerationGoal(BaseModel):
    """Specific goal for content generation."""
    request_id: str
    content_type: ContentType
    learning_objectives: List[str]
    target_quality: float = 0.85
    accessibility_standard: AccessibilityStandard = AccessibilityStandard.WCAG_AA
    style_guide: Optional[str] = None
    deadline: Optional[datetime] = None


class ContentGenerationPlan(BaseModel):
    """Plan for generating content."""
    goal: ContentGenerationGoal
    steps: List[PlanStep]
    estimated_duration: float
    required_modules: List[str]
    quality_checkpoints: List[Dict[str, Any]]


class ContentGenerationAgent(AutonomousAgent):
    """Orchestrates all content generation modules."""
    
    def __init__(self):
        super().__init__(
            agent_id=str(uuid.uuid4()),
            name="ContentGenerationAgent",
            capabilities=[
                AgentCapability.GENERATION,
                AgentCapability.EVALUATION,
                AgentCapability.LEARNING,
                AgentCapability.COLLABORATION
            ]
        )
        
        # Initialize all modules
        self.diagram_generator = DiagramGenerator()
        self.animation_engine = AnimationEngine()
        self.interactive_builder = InteractiveBuilder()
        self.style_manager = StyleManager()
        self.accessibility_manager = AccessibilityManager()
        self.quality_validator = QualityValidator()
        
        # Agent state
        self._current_request: Optional[ContentGenerationRequest] = None
        self._generation_history: List[Dict[str, Any]] = []
        self._quality_threshold = settings.QUALITY_THRESHOLD
        
    async def generate_content(
        self,
        request: ContentGenerationRequest
    ) -> ContentPiece:
        """Generate complete educational content piece."""
        try:
            logger.info(f"Starting content generation for: {request.topic}")
            
            # Update agent state
            self._current_request = request
            self.state = AgentState.EXECUTING
            
            # Create goal
            goal = ContentGenerationGoal(
                request_id=str(uuid.uuid4()),
                content_type=request.content_type,
                learning_objectives=request.learning_objectives,
                target_quality=request.quality_requirements.min_quality_score,
                accessibility_standard=AccessibilityStandard(
                    request.constraints.accessibility_standard
                ),
                style_guide=request.style_preferences.style_guide
            )
            
            # Plan generation
            plan = await self.plan(goal)
            
            # Execute plan
            result = await self.execute(plan)
            
            # Reflect on result
            learning_outcome = await self.reflect(result)
            
            # Store in history
            self._generation_history.append({
                "request": request.dict(),
                "result": result.dict() if hasattr(result, 'dict') else str(result),
                "learning": learning_outcome,
                "timestamp": datetime.utcnow()
            })
            
            logger.info("Content generation complete")
            return result
            
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            self.state = AgentState.ERROR
            raise
            
    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive the content generation environment."""
        observations = {
            "request": self._current_request,
            "available_modules": self._get_available_modules(),
            "resource_status": await self._check_resource_status(),
            "quality_benchmarks": await self._get_quality_benchmarks(),
            "style_guidelines": await self._get_style_guidelines()
        }
        
        return observations
        
    async def update_beliefs(self, observations: Dict[str, Any]) -> None:
        """Update beliefs based on observations."""
        # Update belief about available resources
        self.beliefs.add(AgentBelief(
            content={
                "type": "resource_availability",
                "modules": observations["available_modules"],
                "status": observations["resource_status"]
            },
            confidence=0.95,
            source="self_observation"
        ))
        
        # Update belief about quality requirements
        if observations["request"]:
            self.beliefs.add(AgentBelief(
                content={
                    "type": "quality_requirements",
                    "min_score": observations["request"].quality_requirements.min_quality_score,
                    "benchmarks": observations["quality_benchmarks"]
                },
                confidence=1.0,
                source="request"
            ))
            
    async def deliberate(self) -> AgentGoal:
        """Decide what content to generate next."""
        if not self._current_request:
            return None
            
        # Create goal based on request
        goal = ContentGenerationGoal(
            request_id=str(uuid.uuid4()),
            content_type=self._current_request.content_type,
            learning_objectives=self._current_request.learning_objectives,
            target_quality=self._current_request.quality_requirements.min_quality_score
        )
        
        return goal
        
    async def plan(self, goal: ContentGenerationGoal) -> ContentGenerationPlan:
        """Create plan to achieve content generation goal."""
        logger.info(f"Planning content generation for goal: {goal.request_id}")
        
        steps = []
        required_modules = []
        
        # Step 1: Apply style
        steps.append(PlanStep(
            action="apply_style",
            module="style_manager",
            inputs={
                "domain": self._current_request.metadata.get("domain", "general"),
                "style_guide": goal.style_guide
            },
            expected_output="styled_content",
            duration_estimate=5.0
        ))
        required_modules.append("style_manager")
        
        # Step 2: Generate base content based on type
        if goal.content_type == ContentType.DIAGRAM:
            steps.append(PlanStep(
                action="generate_diagram",
                parameters={
                    "concepts": self._current_request.concepts,
                    "relationships": self._current_request.relationships
                },
                expected_duration=30.0
            ))
            required_modules.append("diagram_generator")
            
        elif goal.content_type == ContentType.ANIMATION:
            steps.append(PlanStep(
                action="create_animation",
                parameters={
                    "concepts": self._current_request.concepts,
                    "duration": self._current_request.constraints.max_duration
                },
                expected_duration=60.0
            ))
            required_modules.append("animation_engine")
            
        elif goal.content_type == ContentType.INTERACTIVE:
            steps.append(PlanStep(
                action="build_interactive",
                parameters={
                    "interaction_type": self._current_request.interaction_preferences.preferred_types[0],
                    "content": self._current_request.concepts
                },
                expected_duration=45.0
            ))
            required_modules.append("interactive_builder")
            
        # Step 3: Ensure accessibility
        steps.append(PlanStep(
            action="ensure_accessibility",
            parameters={
                "standard": goal.accessibility_standard.value
            },
            expected_duration=15.0
        ))
        required_modules.append("accessibility_manager")
        
        # Step 4: Validate quality
        steps.append(PlanStep(
            action="validate_quality",
            parameters={
                "threshold": goal.target_quality
            },
            expected_duration=20.0
        ))
        required_modules.append("quality_validator")
        
        # Step 5: Iterative improvement if needed
        steps.append(PlanStep(
            action="improve_if_needed",
            parameters={
                "max_iterations": 3,
                "target_quality": goal.target_quality
            },
            expected_duration=30.0
        ))
        
        # Calculate total duration
        total_duration = sum(step.expected_duration for step in steps)
        
        # Define quality checkpoints
        checkpoints = [
            {"after_step": 2, "metric": "visual_quality", "threshold": 0.8},
            {"after_step": 3, "metric": "accessibility", "threshold": 0.9},
            {"after_step": 4, "metric": "overall_quality", "threshold": goal.target_quality}
        ]
        
        plan = ContentGenerationPlan(
            goal=goal,
            steps=steps,
            estimated_duration=total_duration,
            required_modules=list(set(required_modules)),
            quality_checkpoints=checkpoints
        )
        
        logger.info(f"Created plan with {len(steps)} steps, estimated duration: {total_duration}s")
        return plan
        
    async def execute(self, plan: ContentGenerationPlan) -> ContentPiece:
        """Execute the content generation plan."""
        logger.info(f"Executing plan for goal: {plan.goal.request_id}")
        
        content_data = {
            "topic": self._current_request.topic,
            "concepts": self._current_request.concepts,
            "metadata": {}
        }
        
        try:
            for idx, step in enumerate(plan.steps):
                logger.info(f"Executing step {idx + 1}/{len(plan.steps)}: {step.action}")
                
                if step.action == "apply_style":
                    content_data = await self._apply_style(content_data, step.parameters)
                    
                elif step.action == "generate_diagram":
                    diagram = await self._generate_diagram(content_data, step.parameters)
                    content_data["diagram"] = diagram
                    
                elif step.action == "create_animation":
                    animation = await self._create_animation(content_data, step.parameters)
                    content_data["animation"] = animation
                    
                elif step.action == "build_interactive":
                    interactive = await self._build_interactive(content_data, step.parameters)
                    content_data["interactive"] = interactive
                    
                elif step.action == "ensure_accessibility":
                    content_data = await self._ensure_accessibility(content_data, step.parameters)
                    
                elif step.action == "validate_quality":
                    metrics = await self._validate_quality(content_data, step.parameters)
                    content_data["quality_metrics"] = metrics
                    
                elif step.action == "improve_if_needed":
                    content_data = await self._improve_if_needed(content_data, step.parameters)
                    
                # Check quality checkpoint
                checkpoint = next(
                    (cp for cp in plan.quality_checkpoints if cp["after_step"] == idx + 1),
                    None
                )
                if checkpoint:
                    await self._check_quality_checkpoint(content_data, checkpoint)
                    
            # Create final content piece
            content_piece = await self._create_content_piece(content_data)
            
            logger.info("Plan execution complete")
            return content_piece
            
        except Exception as e:
            logger.error(f"Error executing plan: {str(e)}")
            raise
            
    async def reflect(self, result: ContentPiece) -> Dict[str, Any]:
        """Reflect on the generation result and learn."""
        logger.info("Reflecting on content generation result")
        
        learning_outcome = {
            "success": result.quality_metrics.overall_score >= self._quality_threshold,
            "quality_achieved": result.quality_metrics.overall_score,
            "time_taken": result.metadata.get("generation_time", 0),
            "modules_used": result.metadata.get("modules_used", []),
            "improvements_made": result.metadata.get("improvements_made", 0),
            "lessons_learned": []
        }
        
        # Analyze what worked well
        if result.quality_metrics.visual_quality > 0.9:
            learning_outcome["lessons_learned"].append({
                "aspect": "visual_quality",
                "insight": "Current visual generation approach is highly effective",
                "confidence": 0.9
            })
            
        # Analyze what needs improvement
        if result.quality_metrics.accessibility_score < 0.9:
            learning_outcome["lessons_learned"].append({
                "aspect": "accessibility",
                "insight": "Need to strengthen accessibility features earlier in process",
                "confidence": 0.85
            })
            
        # Store learning for future use
        self._update_generation_strategies(learning_outcome)
        
        logger.info(f"Reflection complete. Success: {learning_outcome['success']}")
        return learning_outcome
        
    async def collaborate(self, other_agents: List[AutonomousAgent]) -> Dict[str, Any]:
        """Collaborate with other agents for content generation."""
        collaboration_result = {
            "agents_involved": [agent.name for agent in other_agents],
            "contributions": {}
        }
        
        for agent in other_agents:
            if agent.name == "PedagogicalReasoningAgent":
                # Get learning path optimization
                learning_path = await agent.send_message(
                    "optimize_learning_path",
                    {"content": self._current_request}
                )
                collaboration_result["contributions"]["learning_path"] = learning_path
                
            elif agent.name == "QualityAssuranceAgent":
                # Get quality recommendations
                quality_advice = await agent.send_message(
                    "recommend_quality_improvements",
                    {"content_type": self._current_request.content_type}
                )
                collaboration_result["contributions"]["quality_advice"] = quality_advice
                
        return collaboration_result
        
    # Private helper methods
    
    def _get_available_modules(self) -> List[str]:
        """Get list of available content generation modules."""
        return [
            "diagram_generator",
            "animation_engine",
            "interactive_builder",
            "style_manager",
            "accessibility_manager",
            "quality_validator"
        ]
        
    async def _check_resource_status(self) -> Dict[str, Any]:
        """Check status of computational resources."""
        return {
            "cpu_available": True,
            "gpu_available": torch.cuda.is_available() if 'torch' in globals() else False,
            "memory_available": True,
            "api_quota": "sufficient"
        }
        
    async def _get_quality_benchmarks(self) -> Dict[str, float]:
        """Get current quality benchmarks."""
        return {
            "visual_quality": 0.85,
            "pedagogical_effectiveness": 0.9,
            "technical_accuracy": 0.95,
            "accessibility": 0.9,
            "engagement": 0.8
        }
        
    async def _get_style_guidelines(self) -> Dict[str, Any]:
        """Get applicable style guidelines."""
        domain = self._current_request.metadata.get("domain", "general") if self._current_request else "general"
        return {
            "domain": domain,
            "brand_guidelines": domain in ["aws", "azure", "gcp"],
            "custom_style": self._current_request.style_preferences.style_guide if self._current_request else None
        }
        
    async def _apply_style(self, content_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply visual style to content."""
        domain = parameters.get("domain", "general")
        
        if domain in [d.value for d in DomainStyle]:
            styled_content = await self.style_manager.apply_domain_style(
                content_data, domain
            )
        else:
            # Use custom or default style
            styled_content = content_data
            
        content_data.update(styled_content)
        return content_data
        
    async def _generate_diagram(self, content_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate educational diagram."""
        concepts = parameters.get("concepts", [])
        relationships = parameters.get("relationships", [])
        
        diagram = await self.diagram_generator.generate_architecture_diagram(
            components=concepts,
            connections=relationships,
            style="educational",
            layout="hierarchical"
        )
        
        return diagram
        
    async def _create_animation(self, content_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create educational animation."""
        concepts = parameters.get("concepts", [])
        duration = parameters.get("duration", 30)
        
        sequences = []
        for concept in concepts:
            sequence = await self.animation_engine.create_animation_sequence(
                elements=[{"type": "concept", "data": concept}],
                duration=duration / len(concepts),
                style="smooth"
            )
            sequences.append(sequence)
            
        animation = await self.animation_engine.compose_sequences(sequences)
        return animation.dict()
        
    async def _build_interactive(self, content_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Build interactive element."""
        interaction_type = InteractionType(parameters.get("interaction_type", "quiz"))
        content = parameters.get("content", {})
        
        interactive_element = await self.interactive_builder.create_interactive_element(
            element_type=interaction_type,
            content=content,
            learning_objective=self._current_request.learning_objectives[0]
        )
        
        return interactive_element.dict()
        
    async def _ensure_accessibility(self, content_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure content meets accessibility standards."""
        standard = AccessibilityStandard(parameters.get("standard", "wcag_aa"))
        
        # Add alt text for visual elements
        if "diagram" in content_data:
            alt_text = await self.accessibility_manager.generate_alt_text(
                content_data["diagram"],
                context=content_data["topic"]
            )
            content_data["diagram"]["alt_text"] = alt_text
            
        # Add captions for animations
        if "animation" in content_data:
            content_data["animation"] = await self.accessibility_manager.add_captions(
                content_data["animation"]
            )
            
        # Ensure keyboard navigation for interactive elements
        if "interactive" in content_data:
            content_data["interactive"] = await self.accessibility_manager.ensure_keyboard_navigation(
                content_data["interactive"]
            )
            
        return content_data
        
    async def _validate_quality(self, content_data: Dict[str, Any], parameters: Dict[str, Any]) -> QualityMetrics:
        """Validate content quality."""
        threshold = parameters.get("threshold", 0.85)
        
        metrics = await self.quality_validator.validate_visual_quality(
            content_data,
            quality_threshold=threshold
        )
        
        return metrics
        
    async def _improve_if_needed(self, content_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Improve content if quality is below threshold."""
        max_iterations = parameters.get("max_iterations", 3)
        target_quality = parameters.get("target_quality", 0.85)
        
        current_metrics = content_data.get("quality_metrics")
        if not current_metrics or current_metrics.overall_score < target_quality:
            # Create temporary content piece for improvement
            temp_content = ContentPiece(
                id=str(uuid.uuid4()),
                type=self._current_request.content_type,
                topic=content_data["topic"],
                content=content_data,
                quality_metrics=current_metrics or QualityMetrics(),
                metadata=ContentMetadata()
            )
            
            # Iteratively improve
            improved_content = await self.quality_validator.iterative_improvement(
                temp_content,
                current_metrics or QualityMetrics(),
                max_iterations=max_iterations
            )
            
            # Update content data
            content_data.update(improved_content.content)
            content_data["quality_metrics"] = improved_content.quality_metrics
            content_data["improvements_made"] = max_iterations
            
        return content_data
        
    async def _check_quality_checkpoint(self, content_data: Dict[str, Any], checkpoint: Dict[str, Any]) -> None:
        """Check quality at checkpoint."""
        metric = checkpoint["metric"]
        threshold = checkpoint["threshold"]
        
        if "quality_metrics" in content_data:
            if metric == "overall_quality":
                score = content_data["quality_metrics"].overall_score
            elif metric == "visual_quality":
                score = content_data["quality_metrics"].visual_quality
            elif metric == "accessibility":
                score = content_data["quality_metrics"].accessibility_score
            else:
                score = 0
                
            if score < threshold:
                logger.warning(f"Quality checkpoint failed: {metric}={score:.2f} < {threshold}")
                # Could trigger immediate improvement here
                
    async def _create_content_piece(self, content_data: Dict[str, Any]) -> ContentPiece:
        """Create final content piece from generated data."""
        # Determine primary media element
        media_elements = []
        if "diagram" in content_data:
            media_elements.append({
                "type": MediaType.DIAGRAM,
                "data": content_data["diagram"]
            })
        if "animation" in content_data:
            media_elements.append({
                "type": MediaType.ANIMATION,
                "data": content_data["animation"]
            })
            
        # Create metadata
        metadata = ContentMetadata(
            created_at=datetime.utcnow(),
            created_by="ContentGenerationAgent",
            version="1.0",
            tags=["generated", self._current_request.content_type.value],
            learning_objectives=self._current_request.learning_objectives,
            estimated_duration=content_data.get("estimated_duration", 300),
            difficulty_level=self._current_request.difficulty_level,
            prerequisites=self._current_request.prerequisites,
            domain=self._current_request.metadata.get("domain", "general"),
            modules_used=content_data.get("modules_used", []),
            generation_time=content_data.get("generation_time", 0),
            improvements_made=content_data.get("improvements_made", 0)
        )
        
        # Create content piece
        content_piece = ContentPiece(
            id=str(uuid.uuid4()),
            type=self._current_request.content_type,
            topic=self._current_request.topic,
            content=content_data,
            media_elements=media_elements,
            interactive_elements=[content_data["interactive"]] if "interactive" in content_data else [],
            quality_metrics=content_data.get("quality_metrics", QualityMetrics()),
            metadata=metadata
        )
        
        return content_piece
        
    def _update_generation_strategies(self, learning_outcome: Dict[str, Any]) -> None:
        """Update generation strategies based on learning."""
        # Store successful strategies
        if learning_outcome["success"]:
            self.memory.add_episodic_memory({
                "type": "successful_generation",
                "modules_used": learning_outcome["modules_used"],
                "quality_achieved": learning_outcome["quality_achieved"],
                "time_taken": learning_outcome["time_taken"]
            })
            
        # Update procedural memory with insights
        for lesson in learning_outcome["lessons_learned"]:
            self.memory.add_procedural_memory({
                "aspect": lesson["aspect"],
                "strategy": lesson["insight"],
                "confidence": lesson["confidence"]
            })
