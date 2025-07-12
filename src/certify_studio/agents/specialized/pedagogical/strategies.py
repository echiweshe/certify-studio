"""
Learning strategy recommendations module.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from loguru import logger

from .models import LearnerProfile, LearningStrategy


class StrategyRecommender:
    """Recommends learning strategies based on learner characteristics and performance."""
    
    def __init__(self):
        """Initialize the strategy recommender."""
        self.strategy_database = self._initialize_strategy_database()
        self.effectiveness_data = {}
    
    def _initialize_strategy_database(self) -> Dict[str, LearningStrategy]:
        """Initialize database of learning strategies."""
        return {
            "spaced_repetition": LearningStrategy(
                name="Spaced Repetition",
                description="Review material at increasing intervals to improve retention",
                implementation=[
                    "Review new material within 24 hours",
                    "Second review after 3 days",
                    "Third review after 1 week",
                    "Monthly reviews thereafter"
                ],
                expected_benefit="70-80% improvement in long-term retention",
                target_profile={"goals": ["retention", "certification"]},
                effectiveness_data={"average_improvement": 0.75}
            ),
            
            "feynman_technique": LearningStrategy(
                name="Feynman Technique",
                description="Explain concepts in simple terms to identify knowledge gaps",
                implementation=[
                    "Choose a concept to learn",
                    "Explain it in simple language",
                    "Identify gaps in explanation",
                    "Review and simplify again"
                ],
                expected_benefit="Deeper understanding and better retention",
                target_profile={"learning_style": ["verbal", "analytical"]},
                effectiveness_data={"comprehension_improvement": 0.65}
            ),
            
            "pomodoro_technique": LearningStrategy(
                name="Pomodoro Technique",
                description="Structured time management for focused learning",
                implementation=[
                    "Set timer for 25 minutes",
                    "Focus on single task",
                    "Take 5-minute break",
                    "Longer break after 4 pomodoros"
                ],
                expected_benefit="Improved focus and reduced mental fatigue",
                target_profile={"challenges": ["focus", "time_management"]},
                effectiveness_data={"productivity_increase": 0.40}
            ),
            
            "mind_mapping": LearningStrategy(
                name="Mind Mapping",
                description="Visual representation of information and relationships",
                implementation=[
                    "Start with central concept",
                    "Add main branches for key topics",
                    "Use colors and images",
                    "Show connections between ideas"
                ],
                expected_benefit="Better concept visualization and memory",
                target_profile={"learning_style": ["visual"]},
                effectiveness_data={"recall_improvement": 0.60}
            ),
            
            "active_recall": LearningStrategy(
                name="Active Recall",
                description="Test yourself without looking at materials",
                implementation=[
                    "Read material once thoroughly",
                    "Close materials",
                    "Write down everything remembered",
                    "Check and fill gaps"
                ],
                expected_benefit="Stronger memory formation",
                target_profile={"goals": ["mastery", "exam_preparation"]},
                effectiveness_data={"retention_improvement": 0.70}
            ),
            
            "interleaving": LearningStrategy(
                name="Interleaving Practice",
                description="Mix different topics or skills in practice sessions",
                implementation=[
                    "Identify 3-4 related topics",
                    "Practice each for short periods",
                    "Switch between topics frequently",
                    "Review connections between topics"
                ],
                expected_benefit="Better discrimination and transfer learning",
                target_profile={"content_type": ["problem_solving", "skills"]},
                effectiveness_data={"transfer_improvement": 0.55}
            ),
            
            "elaborative_interrogation": LearningStrategy(
                name="Elaborative Interrogation",
                description="Ask 'why' and 'how' questions about material",
                implementation=[
                    "Read a fact or concept",
                    "Ask why this is true",
                    "Generate detailed explanations",
                    "Connect to prior knowledge"
                ],
                expected_benefit="Deeper understanding and integration",
                target_profile={"learning_style": ["analytical", "curious"]},
                effectiveness_data={"understanding_depth": 0.65}
            ),
            
            "dual_coding": LearningStrategy(
                name="Dual Coding",
                description="Combine verbal and visual information",
                implementation=[
                    "Read text materials",
                    "Create visual representations",
                    "Use both when reviewing",
                    "Switch between formats"
                ],
                expected_benefit="Enhanced memory through multiple pathways",
                target_profile={"learning_style": ["visual", "verbal"]},
                effectiveness_data={"memory_improvement": 0.65}
            ),
            
            "practice_testing": LearningStrategy(
                name="Practice Testing",
                description="Regular self-testing to improve retention",
                implementation=[
                    "Create practice questions",
                    "Test without materials",
                    "Check answers thoroughly",
                    "Focus on missed items"
                ],
                expected_benefit="Improved exam performance and retention",
                target_profile={"goals": ["certification", "exam_success"]},
                effectiveness_data={"exam_improvement": 0.80}
            ),
            
            "metacognitive_reflection": LearningStrategy(
                name="Metacognitive Reflection",
                description="Reflect on your learning process",
                implementation=[
                    "After each session, ask what worked",
                    "Identify challenging areas",
                    "Plan improvements",
                    "Track progress over time"
                ],
                expected_benefit="Improved self-directed learning",
                target_profile={"maturity": ["self_directed", "reflective"]},
                effectiveness_data={"learning_efficiency": 0.45}
            )
        }
    
    async def recommend_strategies(
        self,
        learner_profile: LearnerProfile,
        current_performance: Dict[str, Any],
        num_recommendations: int = 3
    ) -> List[LearningStrategy]:
        """Recommend learning strategies for a learner."""
        try:
            # Score each strategy based on fit
            strategy_scores = {}
            
            for strategy_id, strategy in self.strategy_database.items():
                score = await self._calculate_strategy_fit(
                    strategy,
                    learner_profile,
                    current_performance
                )
                strategy_scores[strategy_id] = score
            
            # Sort by score and return top recommendations
            sorted_strategies = sorted(
                strategy_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            recommendations = []
            for strategy_id, score in sorted_strategies[:num_recommendations]:
                strategy = self.strategy_database[strategy_id]
                # Add personalization note
                strategy.effectiveness_data["fit_score"] = score
                recommendations.append(strategy)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to recommend strategies: {e}")
            return []
    
    async def _calculate_strategy_fit(
        self,
        strategy: LearningStrategy,
        learner_profile: LearnerProfile,
        performance: Dict[str, Any]
    ) -> float:
        """Calculate how well a strategy fits a learner."""
        score = 0.0
        
        # Check learning style match
        target_profile = strategy.target_profile
        if "learning_style" in target_profile:
            if learner_profile.learning_style in target_profile["learning_style"]:
                score += 0.3
        
        # Check goal alignment
        if "goals" in target_profile:
            for goal in target_profile["goals"]:
                if any(goal in learner_goal.lower() for learner_goal in learner_profile.goals):
                    score += 0.2
                    break
        
        # Check for addressing challenges
        if "challenges" in target_profile:
            # Infer challenges from performance
            if performance.get("average_score", 1.0) < 0.7:
                if "retention" in target_profile["challenges"]:
                    score += 0.25
            
            if performance.get("completion_rate", 1.0) < 0.8:
                if "focus" in target_profile["challenges"] or "time_management" in target_profile["challenges"]:
                    score += 0.25
        
        # Consider effectiveness data
        avg_effectiveness = sum(
            strategy.effectiveness_data.values()
        ) / len(strategy.effectiveness_data) if strategy.effectiveness_data else 0.5
        
        score += avg_effectiveness * 0.2
        
        # Boost score for exam prep if certification is a goal
        if "certification" in str(learner_profile.goals).lower():
            if strategy.name in ["Practice Testing", "Active Recall", "Spaced Repetition"]:
                score += 0.1
        
        return min(score, 1.0)
    
    async def create_study_plan(
        self,
        learner_profile: LearnerProfile,
        learning_objectives: List[str],
        time_available: int,  # minutes per day
        duration_weeks: int = 4
    ) -> Dict[str, Any]:
        """Create a personalized study plan."""
        try:
            study_plan = {
                "learner_id": learner_profile.id,
                "duration_weeks": duration_weeks,
                "daily_time": time_available,
                "total_hours": (time_available * 7 * duration_weeks) / 60,
                "schedule": [],
                "strategies": [],
                "milestones": []
            }
            
            # Recommend strategies
            strategies = await self.recommend_strategies(
                learner_profile,
                {"average_score": 0.7, "completion_rate": 0.8}  # Default performance
            )
            study_plan["strategies"] = [s.name for s in strategies]
            
            # Create weekly schedule
            objectives_per_week = len(learning_objectives) / duration_weeks
            
            for week in range(1, duration_weeks + 1):
                week_schedule = {
                    "week": week,
                    "objectives": [],
                    "activities": [],
                    "time_allocation": {}
                }
                
                # Assign objectives
                start_idx = int((week - 1) * objectives_per_week)
                end_idx = int(week * objectives_per_week)
                week_objectives = learning_objectives[start_idx:end_idx]
                week_schedule["objectives"] = week_objectives
                
                # Plan activities based on strategies
                if "Spaced Repetition" in [s.name for s in strategies]:
                    week_schedule["activities"].append({
                        "type": "review",
                        "frequency": "daily",
                        "duration": min(15, time_available * 0.2)
                    })
                
                if "Practice Testing" in [s.name for s in strategies]:
                    week_schedule["activities"].append({
                        "type": "practice_test",
                        "frequency": "twice_weekly",
                        "duration": min(30, time_available * 0.3)
                    })
                
                # Time allocation
                week_schedule["time_allocation"] = {
                    "new_material": time_available * 0.5,
                    "practice": time_available * 0.3,
                    "review": time_available * 0.2
                }
                
                study_plan["schedule"].append(week_schedule)
            
            # Add milestones
            study_plan["milestones"] = self._create_milestones(
                duration_weeks,
                learning_objectives
            )
            
            return study_plan
            
        except Exception as e:
            logger.error(f"Failed to create study plan: {e}")
            raise
    
    def _create_milestones(
        self,
        duration_weeks: int,
        objectives: List[str]
    ) -> List[Dict[str, Any]]:
        """Create milestones for the study plan."""
        milestones = []
        
        # Week 1 milestone
        milestones.append({
            "week": 1,
            "goal": "Complete foundational concepts",
            "assessment": "Self-assessment quiz",
            "success_criteria": "70% understanding of basics"
        })
        
        # Mid-point milestone
        mid_week = duration_weeks // 2
        milestones.append({
            "week": mid_week,
            "goal": "Master core concepts",
            "assessment": "Practice exam",
            "success_criteria": "75% on practice test"
        })
        
        # Final milestone
        milestones.append({
            "week": duration_weeks,
            "goal": "Ready for certification",
            "assessment": "Full mock exam",
            "success_criteria": "85% on mock exam"
        })
        
        return milestones
    
    async def adapt_strategy(
        self,
        strategy: LearningStrategy,
        learner_profile: LearnerProfile,
        effectiveness_feedback: Dict[str, Any]
    ) -> LearningStrategy:
        """Adapt a strategy based on learner feedback."""
        try:
            adapted = LearningStrategy(
                name=strategy.name,
                description=strategy.description,
                implementation=strategy.implementation.copy(),
                expected_benefit=strategy.expected_benefit,
                target_profile=strategy.target_profile.copy(),
                effectiveness_data=strategy.effectiveness_data.copy()
            )
            
            # Update effectiveness data
            if "effectiveness_score" in effectiveness_feedback:
                adapted.effectiveness_data["user_reported"] = effectiveness_feedback["effectiveness_score"]
            
            # Modify implementation based on feedback
            if effectiveness_feedback.get("too_complex", False):
                # Simplify implementation steps
                adapted.implementation = adapted.implementation[:3]  # Keep only first 3 steps
                adapted.description += " (simplified version)"
            
            if effectiveness_feedback.get("time_constraint", False):
                # Add time-saving modification
                adapted.implementation.insert(0, "Start with just 10-15 minutes")
            
            # Personalize for learning style
            if learner_profile.learning_style == "visual" and "visual" not in adapted.description.lower():
                adapted.implementation.append("Add visual elements like diagrams or colors")
            
            return adapted
            
        except Exception as e:
            logger.error(f"Failed to adapt strategy: {e}")
            return strategy
