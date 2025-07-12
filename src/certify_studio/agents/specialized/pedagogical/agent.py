"""
Pedagogical Reasoning Agent - Main orchestrator

This agent coordinates all pedagogical modules to create optimal learning experiences.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from loguru import logger

from certify_studio.agents.core.autonomous_agent import (
    AutonomousAgent,
    AgentCapability,
    AgentState,
    Belief,
    Goal,
    Intention
)

from .models import (
    LearnerProfile,
    LearningObjective,
    LearningPath,
    LearningTheory,
    DifficultyLevel
)
from .theories import LearningTheoriesEngine
from .cognitive_load import CognitiveLoadManager
from .learning_path import LearningPathOptimizer
from .assessment import AssessmentGenerator
from .personalization import PersonalizationEngine
from .strategies import StrategyRecommender


class PedagogicalReasoningAgent(AutonomousAgent):
    """
    Agent that applies pedagogical theories to optimize learning experiences.
    
    This agent orchestrates multiple specialized modules to:
    - Design optimal learning paths
    - Manage cognitive load
    - Personalize content based on learner profiles
    - Generate assessments
    - Recommend learning strategies
    - Continuously improve based on outcomes
    """
    
    def __init__(self, agent_id: str, llm_provider: Any):
        """Initialize the pedagogical reasoning agent."""
        super().__init__(
            agent_id=agent_id,
            capabilities=[
                AgentCapability.TEACHING,
                AgentCapability.REASONING,
                AgentCapability.LEARNING,
                AgentCapability.OPTIMIZATION
            ],
            llm_provider=llm_provider
        )
        
        # Initialize specialized modules
        self.theories_engine = LearningTheoriesEngine()
        self.cognitive_load_manager = CognitiveLoadManager()
        self.path_optimizer = LearningPathOptimizer()
        self.assessment_generator = AssessmentGenerator()
        self.personalization_engine = PersonalizationEngine()
        self.strategy_recommender = StrategyRecommender()
        
        # Agent state
        self.learner_profiles: Dict[str, LearnerProfile] = {}
        self.learning_paths: Dict[str, LearningPath] = {}
        self.effectiveness_metrics: Dict[str, float] = {
            "completion_rate": 0.0,
            "engagement_score": 0.0,
            "knowledge_retention": 0.0,
            "satisfaction_rating": 0.0
        }
    
    async def design_learning_path(
        self,
        concepts: List[Dict[str, Any]],
        learner_profile: Optional[LearnerProfile] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> LearningPath:
        """
        Design an optimal learning path for given concepts.
        
        This is the main entry point that coordinates all modules.
        """
        try:
            self.state = AgentState.THINKING
            logger.info(f"Designing learning path for {len(concepts)} concepts")
            
            # Create learning objectives
            objectives = await self._create_learning_objectives(concepts)
            
            # Optimize learning path
            learning_path = await self.path_optimizer.create_optimized_path(
                objectives,
                learner_profile,
                constraints
            )
            
            # Assess cognitive load
            cognitive_load = await self.cognitive_load_manager.assess_cognitive_load(
                objectives,
                [obj for obj in objectives if obj.id in learning_path.sequence]
            )
            
            # Apply learning theories
            for theory in learning_path.theories_applied:
                theory_enhancements = await self.theories_engine.apply_theory(
                    theory,
                    {"objectives": objectives},
                    {"learner_profile": learner_profile}
                )
                # Merge enhancements into path
                if "scaffolds" in theory_enhancements:
                    learning_path.adaptations["scaffolding"] = theory_enhancements["scaffolds"]
            
            # Personalize if profile provided
            if learner_profile:
                personalized_content = await self.personalization_engine.personalize_content(
                    {"learning_path": learning_path},
                    learner_profile
                )
                learning_path.adaptations.update(personalized_content)
            
            # Store in memory
            self.memory_system.store_short_term({
                "task": "learning_path_design",
                "path_id": learning_path.id,
                "concepts_count": len(concepts),
                "cognitive_load": cognitive_load.total_load
            })
            
            # Track performance
            await self.self_improvement.track_performance(
                task="learning_path_design",
                metrics={
                    "concepts_processed": len(concepts),
                    "path_duration": learning_path.estimated_duration,
                    "cognitive_load": cognitive_load.total_load
                }
            )
            
            # Store path
            self.learning_paths[learning_path.id] = learning_path
            if learner_profile:
                self.learner_profiles[learner_profile.id] = learner_profile
            
            self.state = AgentState.IDLE
            return learning_path
            
        except Exception as e:
            logger.error(f"Failed to design learning path: {e}")
            self.state = AgentState.ERROR
            raise
    
    async def _create_learning_objectives(
        self,
        concepts: List[Dict[str, Any]]
    ) -> List[LearningObjective]:
        """Create learning objectives from concepts."""
        objectives = []
        
        for i, concept in enumerate(concepts):
            # Use theories engine to determine Bloom's level
            level = self.theories_engine.determine_blooms_level(concept)
            
            objective = LearningObjective(
                id=f"obj_{i}_{concept.get('name', '').replace(' ', '_')}",
                description=f"Learn and {level} {concept.get('name', 'concept')}",
                domain="cognitive",
                level=level,
                prerequisites=concept.get('prerequisites', []),
                estimated_time=self._estimate_learning_time(concept),
                difficulty=self._assess_difficulty(concept)
            )
            objectives.append(objective)
        
        return objectives
    
    def _estimate_learning_time(self, concept: Dict[str, Any]) -> int:
        """Estimate time needed to learn a concept."""
        base_time = 10
        complexity_multiplier = {
            'low': 0.5,
            'medium': 1.0,
            'high': 2.0,
            'very_high': 3.0
        }
        
        complexity = concept.get('complexity', 'medium')
        time = base_time * complexity_multiplier.get(complexity, 1.0)
        
        if 'content_size' in concept:
            if concept['content_size'] > 1000:
                time *= 1.5
            elif concept['content_size'] > 2000:
                time *= 2.0
        
        return int(time)
    
    def _assess_difficulty(self, concept: Dict[str, Any]) -> DifficultyLevel:
        """Assess difficulty level of a concept."""
        complexity = concept.get('complexity', 'medium')
        prerequisites_count = len(concept.get('prerequisites', []))
        
        if complexity == 'low' and prerequisites_count == 0:
            return DifficultyLevel.BEGINNER
        elif complexity == 'low' and prerequisites_count > 0:
            return DifficultyLevel.ELEMENTARY
        elif complexity == 'medium' and prerequisites_count <= 2:
            return DifficultyLevel.INTERMEDIATE
        elif complexity == 'high' or prerequisites_count > 2:
            return DifficultyLevel.ADVANCED
        else:
            return DifficultyLevel.EXPERT
    
    async def generate_assessment(
        self,
        learning_path_id: str,
        assessment_type: str = "formative"
    ) -> List[Dict[str, Any]]:
        """Generate assessment for a learning path."""
        try:
            learning_path = self.learning_paths.get(learning_path_id)
            if not learning_path:
                raise ValueError(f"Learning path {learning_path_id} not found")
            
            # Generate assessment questions
            questions = await self.assessment_generator.generate_assessment(
                learning_path.objectives,
                assessment_type
            )
            
            # Convert to dict format
            assessment = []
            for question in questions:
                assessment.append({
                    "id": question.id,
                    "type": question.type,
                    "question": question.question,
                    "objective_id": question.objective_id,
                    "difficulty": question.difficulty,
                    "bloom_level": question.bloom_level,
                    "estimated_time": question.estimated_time,
                    "options": getattr(question, 'options', None),
                    "rubric": getattr(question, 'rubric', None)
                })
            
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to generate assessment: {e}")
            raise
    
    async def recommend_strategies(
        self,
        learner_id: str,
        current_performance: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Recommend learning strategies for a learner."""
        try:
            learner_profile = self.learner_profiles.get(learner_id)
            if not learner_profile:
                raise ValueError(f"Learner profile {learner_id} not found")
            
            # Use default performance if not provided
            if not current_performance:
                current_performance = {
                    "average_score": 0.75,
                    "completion_rate": 0.8,
                    "engagement_score": 0.7
                }
            
            # Get strategy recommendations
            strategies = await self.strategy_recommender.recommend_strategies(
                learner_profile,
                current_performance
            )
            
            # Convert to dict format
            recommendations = []
            for strategy in strategies:
                recommendations.append({
                    "name": strategy.name,
                    "description": strategy.description,
                    "implementation": strategy.implementation,
                    "expected_benefit": strategy.expected_benefit,
                    "fit_score": strategy.effectiveness_data.get("fit_score", 0)
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to recommend strategies: {e}")
            raise
    
    async def adapt_to_progress(
        self,
        learner_id: str,
        progress_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt learning based on progress data."""
        try:
            learner_profile = self.learner_profiles.get(learner_id)
            if not learner_profile:
                raise ValueError(f"Learner profile {learner_id} not found")
            
            # Use personalization engine for adaptation
            adaptations = await self.personalization_engine.adapt_to_progress(
                learner_profile,
                progress_data
            )
            
            # Update beliefs about effective approaches
            self._update_pedagogical_beliefs(progress_data, adaptations)
            
            # Store adaptation in memory
            self.memory_system.store_long_term({
                "type": "progress_adaptation",
                "learner_id": learner_id,
                "adaptations": adaptations,
                "timestamp": datetime.now().isoformat()
            })
            
            return adaptations
            
        except Exception as e:
            logger.error(f"Failed to adapt to progress: {e}")
            raise
    
    async def evaluate_content_effectiveness(
        self,
        content_id: str,
        learner_feedback: Dict[str, Any],
        performance_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate the effectiveness of educational content."""
        try:
            logger.info(f"Evaluating content effectiveness for {content_id}")
            
            # Calculate effectiveness scores
            clarity_score = learner_feedback.get("clarity_rating", 0) / 5.0
            engagement_score = learner_feedback.get("engagement_rating", 0) / 5.0
            learning_outcome_score = performance_metrics.get("objective_achievement", 0)
            
            # Cognitive load assessment
            reported_difficulty = learner_feedback.get("difficulty_rating", 3) / 5.0
            cognitive_load_score = 1.0 - abs(reported_difficulty - 0.6)  # Optimal is 0.6
            
            # Overall effectiveness
            effectiveness = (
                clarity_score * 0.3 +
                engagement_score * 0.2 +
                learning_outcome_score * 0.4 +
                cognitive_load_score * 0.1
            )
            
            # Generate recommendations
            recommendations = []
            
            if clarity_score < 0.7:
                recommendations.append("Simplify explanations and add more examples")
            
            if engagement_score < 0.6:
                recommendations.append("Add interactive elements or real-world applications")
            
            if cognitive_load_score < 0.5:
                if reported_difficulty > 0.8:
                    recommendations.append("Break down complex concepts into smaller chunks")
                else:
                    recommendations.append("Add more challenging exercises for advanced learners")
            
            # Store evaluation for continuous improvement
            evaluation = {
                "content_id": content_id,
                "effectiveness_score": effectiveness,
                "clarity_score": clarity_score,
                "engagement_score": engagement_score,
                "learning_outcome_score": learning_outcome_score,
                "cognitive_load_score": cognitive_load_score,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }
            
            self.memory_system.store_long_term({
                "type": "content_evaluation",
                "evaluation": evaluation
            })
            
            # Update effectiveness metrics
            self.effectiveness_metrics["engagement_score"] = (
                self.effectiveness_metrics["engagement_score"] * 0.9 + engagement_score * 0.1
            )
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Failed to evaluate content effectiveness: {e}")
            raise
    
    async def create_study_plan(
        self,
        learner_id: str,
        learning_objectives: List[str],
        time_available: int,
        duration_weeks: int = 4
    ) -> Dict[str, Any]:
        """Create a personalized study plan."""
        try:
            learner_profile = self.learner_profiles.get(learner_id)
            if not learner_profile:
                raise ValueError(f"Learner profile {learner_id} not found")
            
            # Use strategy recommender to create plan
            study_plan = await self.strategy_recommender.create_study_plan(
                learner_profile,
                learning_objectives,
                time_available,
                duration_weeks
            )
            
            # Store plan
            self.memory_system.store_short_term({
                "type": "study_plan",
                "learner_id": learner_id,
                "plan": study_plan
            })
            
            return study_plan
            
        except Exception as e:
            logger.error(f"Failed to create study plan: {e}")
            raise
    
    async def think(self) -> Dict[str, Any]:
        """Pedagogical reasoning agent's thinking process."""
        current_task = self.memory_system.get_short_term_memory()
        
        thoughts = {
            "current_focus": "optimizing_learning_experience",
            "active_learners": len(self.learner_profiles),
            "active_paths": len(self.learning_paths),
            "considerations": [
                "learner_characteristics",
                "cognitive_load_management",
                "engagement_strategies",
                "assessment_alignment"
            ],
            "optimization_goals": [
                "maximize_retention",
                "minimize_cognitive_overload",
                "maintain_engagement",
                "ensure_mastery"
            ]
        }
        
        if current_task:
            thoughts["current_task"] = current_task[-1]
            thoughts["approach"] = self._determine_pedagogical_approach(current_task[-1])
        
        # Analyze effectiveness trends
        thoughts["effectiveness_trends"] = {
            metric: value for metric, value in self.effectiveness_metrics.items()
        }
        
        return thoughts
    
    def _determine_pedagogical_approach(self, task: Dict[str, Any]) -> str:
        """Determine the best pedagogical approach for a task."""
        task_type = task.get("type", "general")
        
        approaches = {
            "complex_concept": "scaffolding with worked examples",
            "skill_building": "deliberate practice with feedback",
            "knowledge_retention": "spaced repetition with elaboration",
            "problem_solving": "case-based learning with reflection",
            "assessment": "formative assessment with immediate feedback"
        }
        
        return approaches.get(task_type, "adaptive multi-strategy approach")
    
    async def act(self) -> Dict[str, Any]:
        """Execute pedagogical actions."""
        action_result = {
            "actions_taken": [],
            "optimizations_applied": [],
            "learner_support_provided": []
        }
        
        # Get current intention
        if self.intentions:
            current_intention = self.intentions[0]
            
            if current_intention.description == "optimize_learning_path":
                result = await self._execute_path_optimization(current_intention.parameters)
                action_result["actions_taken"].append("learning_path_optimized")
                action_result["optimizations_applied"].extend(result.get("optimizations", []))
            
            elif current_intention.description == "generate_assessment":
                result = await self._execute_assessment_generation(current_intention.parameters)
                action_result["actions_taken"].append("assessment_generated")
            
            elif current_intention.description == "adapt_content":
                result = await self._execute_content_adaptation(current_intention.parameters)
                action_result["actions_taken"].append("content_adapted")
                action_result["learner_support_provided"].extend(result.get("supports", []))
        
        return action_result
    
    async def _execute_path_optimization(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute learning path optimization."""
        concepts = parameters.get("concepts", [])
        learner_profile = parameters.get("learner_profile")
        
        # Design optimized path
        path = await self.design_learning_path(concepts, learner_profile)
        
        return {
            "path_id": path.id,
            "optimizations": [
                "Applied cognitive load balancing",
                "Inserted spaced review points",
                "Adjusted difficulty progression"
            ],
            "estimated_effectiveness": 0.85
        }
    
    async def _execute_assessment_generation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute assessment generation."""
        path_id = parameters.get("learning_path_id")
        assessment_type = parameters.get("type", "formative")
        
        # Generate assessment
        assessment = await self.generate_assessment(path_id, assessment_type)
        
        return {
            "assessment_generated": True,
            "question_count": len(assessment),
            "types": list(set(q["type"] for q in assessment))
        }
    
    async def _execute_content_adaptation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute content adaptation."""
        learner_id = parameters.get("learner_id")
        content = parameters.get("content", {})
        
        learner_profile = self.learner_profiles.get(learner_id)
        if not learner_profile:
            return {"error": "Learner profile not found"}
        
        # Personalize content
        personalized = await self.personalization_engine.personalize_content(
            content,
            learner_profile
        )
        
        return {
            "supports": [
                "Added visual diagrams for complex concepts",
                "Included worked examples",
                "Provided practice problems with hints"
            ],
            "personalization_applied": True,
            "adaptations": personalized.get("personalization_applied", {})
        }
    
    async def reflect(self) -> None:
        """Reflect on pedagogical decisions and outcomes."""
        recent_actions = self.memory_system.get_short_term_memory()
        
        # Analyze effectiveness of recent actions
        for action in recent_actions:
            if "learning_outcome" in action:
                effectiveness = action["learning_outcome"].get("effectiveness", 0)
                
                if effectiveness < 0.7:
                    # Learn from less effective approaches
                    self.memory_system.store_long_term({
                        "type": "pedagogical_insight",
                        "insight": "Approach less effective, consider alternatives",
                        "context": action,
                        "alternatives": self._generate_alternative_approaches(action)
                    })
                elif effectiveness > 0.9:
                    # Reinforce successful approaches
                    self.memory_system.store_long_term({
                        "type": "pedagogical_success",
                        "approach": action.get("approach"),
                        "context": action,
                        "effectiveness": effectiveness
                    })
        
        # Update beliefs about pedagogy
        self._update_pedagogical_beliefs()
        
        # Self-improvement based on patterns
        patterns = self._identify_effectiveness_patterns()
        if patterns:
            await self.self_improvement.experiment_with_strategies(
                patterns,
                "pedagogical_optimization"
            )
    
    def _generate_alternative_approaches(self, action: Dict[str, Any]) -> List[str]:
        """Generate alternative pedagogical approaches."""
        return [
            "Increase scaffolding support",
            "Break into smaller learning chunks",
            "Add more interactive elements",
            "Provide additional worked examples",
            "Use different instructional modality",
            "Apply different learning theory",
            "Adjust cognitive load balance"
        ]
    
    def _update_pedagogical_beliefs(self, progress_data: Optional[Dict[str, Any]] = None, adaptations: Optional[Dict[str, Any]] = None) -> None:
        """Update beliefs about effective pedagogy."""
        # Analyze patterns in long-term memory
        successes = self.memory_system.search_long_term("pedagogical_success")
        
        if len(successes) > 10:
            # Extract patterns
            effective_approaches = {}
            for success in successes:
                approach = success.get("approach")
                if approach:
                    effective_approaches[approach] = effective_approaches.get(approach, 0) + 1
            
            # Update beliefs
            if effective_approaches:
                most_effective = max(effective_approaches.items(), key=lambda x: x[1])
                self.beliefs.append(Belief(
                    description=f"Most effective approach: {most_effective[0]}",
                    confidence=min(0.9, most_effective[1] / len(successes)),
                    source="empirical_evidence"
                ))
        
        # Update based on current progress if provided
        if progress_data and adaptations:
            performance_level = adaptations.get("performance_level", "on_track")
            self.beliefs.append(Belief(
                description=f"Current approach effectiveness: {performance_level}",
                confidence=0.7,
                source="recent_observation"
            ))
    
    def _identify_effectiveness_patterns(self) -> List[Dict[str, Any]]:
        """Identify patterns in pedagogical effectiveness."""
        patterns = []
        
        # Analyze memory for patterns
        evaluations = self.memory_system.search_long_term("content_evaluation")
        
        if len(evaluations) > 5:
            # Look for common success factors
            high_effectiveness = [e for e in evaluations if e.get("evaluation", {}).get("effectiveness_score", 0) > 0.8]
            
            if high_effectiveness:
                common_factors = {
                    "interactive_elements": 0,
                    "visual_aids": 0,
                    "scaffolding": 0,
                    "practice_opportunities": 0
                }
                
                # Count occurrences (simplified)
                for evaluation in high_effectiveness:
                    for factor in common_factors:
                        if factor in str(evaluation):
                            common_factors[factor] += 1
                
                # Identify top factors
                top_factor = max(common_factors.items(), key=lambda x: x[1])
                patterns.append({
                    "pattern": "success_factor",
                    "factor": top_factor[0],
                    "frequency": top_factor[1] / len(high_effectiveness)
                })
        
        return patterns
