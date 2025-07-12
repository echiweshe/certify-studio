"""
Personalization engine for adaptive learning.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .models import (
    LearnerProfile,
    LearningObjective,
    DifficultyLevel
)


class PersonalizationEngine:
    """Engine for personalizing learning experiences."""
    
    def __init__(self):
        """Initialize the personalization engine."""
        self.adaptation_strategies = self._initialize_adaptation_strategies()
        self.learning_style_mappings = self._initialize_style_mappings()
    
    def _initialize_adaptation_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize adaptation strategies."""
        return {
            "pace_adaptation": {
                "slow": {
                    "time_multiplier": 1.5,
                    "additional_practice": True,
                    "review_frequency": "high",
                    "scaffolding_level": "high"
                },
                "moderate": {
                    "time_multiplier": 1.0,
                    "additional_practice": False,
                    "review_frequency": "normal",
                    "scaffolding_level": "medium"
                },
                "fast": {
                    "time_multiplier": 0.8,
                    "additional_practice": False,
                    "review_frequency": "low",
                    "scaffolding_level": "low"
                }
            },
            "difficulty_adaptation": {
                "struggling": {
                    "difficulty_adjustment": -1,
                    "support_resources": ["worked_examples", "step_by_step", "tutoring"],
                    "assessment_modifications": ["extended_time", "partial_credit"]
                },
                "on_track": {
                    "difficulty_adjustment": 0,
                    "support_resources": ["practice_problems", "self_check"],
                    "assessment_modifications": []
                },
                "excelling": {
                    "difficulty_adjustment": 1,
                    "support_resources": ["challenge_problems", "extension_activities"],
                    "assessment_modifications": ["bonus_questions"]
                }
            }
        }
    
    def _initialize_style_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize learning style content mappings."""
        return {
            "visual": {
                "preferred_formats": ["diagrams", "infographics", "videos", "animations"],
                "content_emphasis": {
                    "visual_elements": 0.7,
                    "text_elements": 0.3
                },
                "interaction_types": ["drag_drop", "drawing", "mapping"],
                "avoid": ["long_text_blocks", "audio_only"]
            },
            "auditory": {
                "preferred_formats": ["narration", "discussions", "podcasts", "verbal_explanations"],
                "content_emphasis": {
                    "audio_elements": 0.6,
                    "visual_elements": 0.4
                },
                "interaction_types": ["voice_response", "discussion_forums"],
                "avoid": ["silent_reading", "text_heavy"]
            },
            "kinesthetic": {
                "preferred_formats": ["simulations", "labs", "hands_on", "interactive"],
                "content_emphasis": {
                    "interactive_elements": 0.8,
                    "passive_elements": 0.2
                },
                "interaction_types": ["build", "experiment", "manipulate"],
                "avoid": ["passive_watching", "long_lectures"]
            },
            "reading_writing": {
                "preferred_formats": ["articles", "notes", "lists", "text_summaries"],
                "content_emphasis": {
                    "text_elements": 0.7,
                    "visual_elements": 0.3
                },
                "interaction_types": ["note_taking", "summarizing", "essay_writing"],
                "avoid": ["pure_visual", "audio_only"]
            }
        }
    
    async def personalize_content(
        self,
        content: Dict[str, Any],
        learner_profile: LearnerProfile
    ) -> Dict[str, Any]:
        """Personalize content based on learner profile."""
        try:
            personalized = content.copy()
            
            # Apply learning style adaptations
            style_adaptations = await self._apply_learning_style(
                content,
                learner_profile.learning_style
            )
            personalized.update(style_adaptations)
            
            # Apply pace adaptations
            pace_adaptations = await self._apply_pace_preferences(
                content,
                learner_profile.pace_preference
            )
            personalized.update(pace_adaptations)
            
            # Apply goal-based adaptations
            if learner_profile.goals:
                goal_adaptations = await self._apply_goal_alignment(
                    content,
                    learner_profile.goals
                )
                personalized.update(goal_adaptations)
            
            # Apply strength/weakness adaptations
            if learner_profile.strengths or learner_profile.weaknesses:
                skill_adaptations = await self._apply_skill_adaptations(
                    content,
                    learner_profile.strengths,
                    learner_profile.weaknesses
                )
                personalized.update(skill_adaptations)
            
            # Add personalization metadata
            personalized["personalization_applied"] = {
                "learner_id": learner_profile.id,
                "adaptations": {
                    "learning_style": learner_profile.learning_style,
                    "pace": learner_profile.pace_preference,
                    "goals_targeted": len(learner_profile.goals) > 0,
                    "skills_considered": True
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return personalized
            
        except Exception as e:
            logger.error(f"Failed to personalize content: {e}")
            raise
    
    async def _apply_learning_style(
        self,
        content: Dict[str, Any],
        learning_style: str
    ) -> Dict[str, Any]:
        """Apply learning style specific adaptations."""
        style_config = self.learning_style_mappings.get(learning_style, {})
        
        adaptations = {
            "format_preferences": style_config.get("preferred_formats", []),
            "content_modifications": []
        }
        
        # Modify content presentation
        if learning_style == "visual":
            adaptations["content_modifications"] = [
                {
                    "type": "add_visuals",
                    "elements": ["concept_maps", "flowcharts", "infographics"],
                    "ratio": style_config["content_emphasis"]["visual_elements"]
                }
            ]
        elif learning_style == "kinesthetic":
            adaptations["content_modifications"] = [
                {
                    "type": "add_interactivity",
                    "elements": ["simulations", "drag_drop_exercises", "virtual_labs"],
                    "ratio": style_config["content_emphasis"]["interactive_elements"]
                }
            ]
        
        # Add interaction preferences
        adaptations["interaction_preferences"] = style_config.get("interaction_types", [])
        
        return adaptations
    
    async def _apply_pace_preferences(
        self,
        content: Dict[str, Any],
        pace_preference: str
    ) -> Dict[str, Any]:
        """Apply pace-based adaptations."""
        pace_config = self.adaptation_strategies["pace_adaptation"].get(
            pace_preference,
            self.adaptation_strategies["pace_adaptation"]["moderate"]
        )
        
        adaptations = {
            "timing_adjustments": {
                "time_multiplier": pace_config["time_multiplier"],
                "estimated_duration": int(
                    content.get("base_duration", 30) * pace_config["time_multiplier"]
                )
            },
            "content_density": {
                "chunks_per_session": 5 if pace_preference == "slow" else 10,
                "break_frequency": "frequent" if pace_preference == "slow" else "normal"
            }
        }
        
        # Add practice and review elements
        if pace_config["additional_practice"]:
            adaptations["additional_elements"] = {
                "practice_problems": True,
                "worked_examples": True,
                "review_sessions": pace_config["review_frequency"]
            }
        
        # Scaffolding level
        adaptations["scaffolding_level"] = pace_config["scaffolding_level"]
        
        return adaptations
    
    async def _apply_goal_alignment(
        self,
        content: Dict[str, Any],
        goals: List[str]
    ) -> Dict[str, Any]:
        """Align content with learner goals."""
        adaptations = {
            "goal_alignment": {
                "primary_goals": goals[:3],  # Focus on top 3 goals
                "content_prioritization": []
            }
        }
        
        # Prioritize content related to goals
        for goal in goals:
            if "certification" in goal.lower():
                adaptations["goal_alignment"]["content_prioritization"].append({
                    "type": "certification_focus",
                    "elements": ["exam_tips", "practice_tests", "key_concepts"],
                    "weight": 0.7
                })
            elif "practical" in goal.lower() or "hands-on" in goal.lower():
                adaptations["goal_alignment"]["content_prioritization"].append({
                    "type": "practical_focus",
                    "elements": ["labs", "projects", "real_world_scenarios"],
                    "weight": 0.8
                })
            elif "career" in goal.lower():
                adaptations["goal_alignment"]["content_prioritization"].append({
                    "type": "career_focus",
                    "elements": ["industry_examples", "job_relevant_skills", "portfolio_projects"],
                    "weight": 0.6
                })
        
        return adaptations
    
    async def _apply_skill_adaptations(
        self,
        content: Dict[str, Any],
        strengths: List[str],
        weaknesses: List[str]
    ) -> Dict[str, Any]:
        """Apply adaptations based on learner strengths and weaknesses."""
        adaptations = {
            "skill_adaptations": {
                "leverage_strengths": [],
                "support_weaknesses": []
            }
        }
        
        # Leverage strengths
        for strength in strengths:
            if "problem_solving" in strength.lower():
                adaptations["skill_adaptations"]["leverage_strengths"].append({
                    "strategy": "challenge_through_problems",
                    "elements": ["complex_scenarios", "open_ended_questions"]
                })
            elif "visual" in strength.lower():
                adaptations["skill_adaptations"]["leverage_strengths"].append({
                    "strategy": "visual_learning_emphasis",
                    "elements": ["diagram_creation", "visual_note_taking"]
                })
        
        # Support weaknesses
        for weakness in weaknesses:
            if "math" in weakness.lower() or "calculation" in weakness.lower():
                adaptations["skill_adaptations"]["support_weaknesses"].append({
                    "area": "mathematical_concepts",
                    "support": ["step_by_step_solutions", "calculator_tools", "visual_representations"]
                })
            elif "reading" in weakness.lower():
                adaptations["skill_adaptations"]["support_weaknesses"].append({
                    "area": "text_comprehension",
                    "support": ["summaries", "audio_narration", "visual_aids"]
                })
        
        return adaptations
    
    async def adapt_to_progress(
        self,
        learner_profile: LearnerProfile,
        progress_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt learning based on progress data."""
        try:
            adaptations = {
                "performance_level": self._determine_performance_level(progress_data),
                "recommendations": [],
                "content_adjustments": [],
                "support_modifications": []
            }
            
            performance = adaptations["performance_level"]
            
            # Get adaptation strategy
            strategy = self.adaptation_strategies["difficulty_adaptation"].get(
                performance,
                self.adaptation_strategies["difficulty_adaptation"]["on_track"]
            )
            
            # Apply difficulty adjustments
            if strategy["difficulty_adjustment"] != 0:
                adaptations["content_adjustments"].append({
                    "type": "difficulty_modification",
                    "adjustment": strategy["difficulty_adjustment"],
                    "apply_to": "upcoming_content"
                })
            
            # Add support resources
            adaptations["support_modifications"] = strategy["support_resources"]
            
            # Assessment modifications
            if strategy["assessment_modifications"]:
                adaptations["assessment_adjustments"] = strategy["assessment_modifications"]
            
            # Generate specific recommendations
            adaptations["recommendations"] = await self._generate_progress_recommendations(
                learner_profile,
                progress_data,
                performance
            )
            
            return adaptations
            
        except Exception as e:
            logger.error(f"Failed to adapt to progress: {e}")
            raise
    
    def _determine_performance_level(self, progress_data: Dict[str, Any]) -> str:
        """Determine learner's performance level from progress data."""
        avg_score = progress_data.get("average_score", 0.7)
        completion_rate = progress_data.get("completion_rate", 0.8)
        time_ratio = progress_data.get("actual_time", 1.0) / progress_data.get("expected_time", 1.0)
        
        # Weighted performance calculation
        performance_score = (
            avg_score * 0.5 +
            completion_rate * 0.3 +
            (1.0 / time_ratio if time_ratio > 0 else 0) * 0.2
        )
        
        if performance_score < 0.6:
            return "struggling"
        elif performance_score > 0.85:
            return "excelling"
        else:
            return "on_track"
    
    async def _generate_progress_recommendations(
        self,
        learner_profile: LearnerProfile,
        progress_data: Dict[str, Any],
        performance_level: str
    ) -> List[str]:
        """Generate specific recommendations based on progress."""
        recommendations = []
        
        if performance_level == "struggling":
            recommendations.extend([
                "Consider spending more time on foundational concepts",
                "Utilize worked examples before attempting practice problems",
                "Schedule regular review sessions for recent material"
            ])
            
            # Specific to learning style
            if learner_profile.learning_style == "visual":
                recommendations.append("Use concept maps to visualize relationships")
            elif learner_profile.learning_style == "kinesthetic":
                recommendations.append("Try hands-on labs for better understanding")
        
        elif performance_level == "excelling":
            recommendations.extend([
                "Challenge yourself with advanced problems",
                "Consider peer tutoring to reinforce learning",
                "Explore related topics for deeper understanding"
            ])
        
        else:  # on_track
            recommendations.extend([
                "Maintain current study pace",
                "Continue regular practice sessions",
                "Focus on areas with lower scores"
            ])
        
        # Time-based recommendations
        if progress_data.get("actual_time", 0) > progress_data.get("expected_time", 1) * 1.5:
            recommendations.append("Break study sessions into smaller chunks")
        
        return recommendations
    
    async def generate_personalized_feedback(
        self,
        learner_profile: LearnerProfile,
        assessment_result: Dict[str, Any]
    ) -> str:
        """Generate personalized feedback for assessment results."""
        try:
            score = assessment_result.get("score", 0)
            objective = assessment_result.get("objective", "the material")
            
            # Base feedback on performance
            if score >= 0.9:
                feedback = f"Excellent work on {objective}! "
                tone = "encouraging"
            elif score >= 0.7:
                feedback = f"Good progress on {objective}. "
                tone = "supportive"
            else:
                feedback = f"Let's work together on {objective}. "
                tone = "constructive"
            
            # Personalize based on learning style
            if learner_profile.learning_style == "visual":
                if score < 0.7:
                    feedback += "Try creating a visual diagram of the concepts. "
                else:
                    feedback += "Your visual understanding is strong! "
            
            elif learner_profile.learning_style == "kinesthetic":
                if score < 0.7:
                    feedback += "Practice with hands-on examples to solidify understanding. "
                else:
                    feedback += "Keep applying concepts practically! "
            
            # Add goal-relevant feedback
            if learner_profile.goals and "certification" in str(learner_profile.goals):
                feedback += f"This is {'key' if score >= 0.7 else 'important'} for your certification goal. "
            
            # Encouragement based on pace preference
            if learner_profile.pace_preference == "slow" and score < 0.7:
                feedback += "Take your time to review, you're making progress. "
            elif learner_profile.pace_preference == "fast" and score >= 0.9:
                feedback += "Ready for the next challenge? "
            
            return feedback
            
        except Exception as e:
            logger.error(f"Failed to generate personalized feedback: {e}")
            return "Keep up the good work!"
