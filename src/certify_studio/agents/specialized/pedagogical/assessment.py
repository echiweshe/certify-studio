"""
Assessment generation and evaluation module.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .models import (
    LearningObjective,
    AssessmentQuestion,
    DifficultyLevel
)


class AssessmentGenerator:
    """Generates and evaluates assessments based on learning objectives."""
    
    def __init__(self):
        """Initialize the assessment generator."""
        self.question_templates = self._initialize_question_templates()
        self.rubric_criteria = self._initialize_rubric_criteria()
    
    def _initialize_question_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize question templates for different Bloom's levels."""
        return {
            "remember": {
                "types": ["multiple_choice", "true_false", "fill_blank"],
                "templates": [
                    "What is the definition of {concept}?",
                    "Which of the following correctly describes {concept}?",
                    "True or False: {statement}",
                    "The term '{term}' refers to ____."
                ]
            },
            "understand": {
                "types": ["short_answer", "multiple_choice", "matching"],
                "templates": [
                    "Explain {concept} in your own words.",
                    "What is the main purpose of {concept}?",
                    "How does {concept_a} relate to {concept_b}?",
                    "Give an example of {concept}."
                ]
            },
            "apply": {
                "types": ["scenario", "problem_solving", "demonstration"],
                "templates": [
                    "Given {scenario}, how would you use {concept}?",
                    "Solve the following problem using {concept}:",
                    "Demonstrate how to {action} using {tool}.",
                    "Apply {concept} to resolve {situation}."
                ]
            },
            "analyze": {
                "types": ["case_study", "comparison", "investigation"],
                "templates": [
                    "Analyze the following {artifact} and identify {elements}.",
                    "Compare and contrast {option_a} with {option_b}.",
                    "What patterns do you observe in {data}?",
                    "Break down {system} into its components."
                ]
            },
            "evaluate": {
                "types": ["critique", "judgment", "recommendation"],
                "templates": [
                    "Evaluate the effectiveness of {approach} for {purpose}.",
                    "Critique the following {solution} based on {criteria}.",
                    "Which option would you recommend and why?",
                    "Assess the strengths and weaknesses of {method}."
                ]
            },
            "create": {
                "types": ["design", "project", "synthesis"],
                "templates": [
                    "Design a {solution} that addresses {problem}.",
                    "Create a {artifact} that demonstrates {concept}.",
                    "Develop a plan to {objective} using {resources}.",
                    "Synthesize {concepts} into a coherent {output}."
                ]
            }
        }
    
    def _initialize_rubric_criteria(self) -> Dict[str, List[str]]:
        """Initialize rubric criteria for different question types."""
        return {
            "short_answer": [
                "accuracy",
                "completeness",
                "clarity",
                "use_of_terminology"
            ],
            "scenario": [
                "problem_identification",
                "solution_appropriateness",
                "reasoning",
                "practical_application"
            ],
            "case_study": [
                "analysis_depth",
                "evidence_use",
                "critical_thinking",
                "conclusions"
            ],
            "project": [
                "creativity",
                "technical_implementation",
                "requirements_met",
                "documentation"
            ]
        }
    
    async def generate_assessment(
        self,
        objectives: List[LearningObjective],
        assessment_type: str = "formative",
        num_questions: Optional[int] = None
    ) -> List[AssessmentQuestion]:
        """Generate assessment questions for learning objectives."""
        try:
            questions = []
            
            # Determine number of questions
            if num_questions is None:
                num_questions = len(objectives) if assessment_type == "formative" else len(objectives) * 2
            
            # Generate questions for each objective
            for i, objective in enumerate(objectives[:num_questions]):
                question = await self._generate_question(objective, assessment_type)
                questions.append(question)
            
            # Enhance for summative assessment
            if assessment_type == "summative":
                questions = self._enhance_for_summative(questions, objectives)
            
            # Order by difficulty
            questions.sort(key=lambda q: q.difficulty)
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to generate assessment: {e}")
            raise
    
    async def _generate_question(
        self,
        objective: LearningObjective,
        assessment_type: str
    ) -> AssessmentQuestion:
        """Generate a single assessment question."""
        level = objective.level
        templates = self.question_templates.get(level, {})
        
        # Select appropriate question type
        question_types = templates.get("types", ["short_answer"])
        question_type = question_types[0]  # In production, this would be more sophisticated
        
        # Generate question text
        template = templates.get("templates", ["Explain {concept}."])[0]
        question_text = template.format(
            concept=objective.description,
            statement=f"{objective.description} is important",
            term=objective.description.split()[0]
        )
        
        # Create question
        question = AssessmentQuestion(
            id=f"q_{objective.id}_{datetime.now().timestamp()}",
            type=question_type,
            objective_id=objective.id,
            question=question_text,
            difficulty=objective.difficulty.value,
            bloom_level=objective.level,
            estimated_time=self._estimate_question_time(question_type, objective.level)
        )
        
        # Add type-specific elements
        if question_type == "multiple_choice":
            question.options = self._generate_options(objective)
            question.correct_answer = 0  # First option is correct
        
        # Add rubric for open-ended questions
        if question_type in ["short_answer", "scenario", "case_study", "project"]:
            question.rubric = self._generate_rubric(question_type, objective)
        
        return question
    
    def _estimate_question_time(self, question_type: str, bloom_level: str) -> int:
        """Estimate time needed to answer a question in minutes."""
        base_times = {
            "multiple_choice": 1,
            "true_false": 0.5,
            "fill_blank": 1,
            "short_answer": 3,
            "matching": 2,
            "scenario": 5,
            "problem_solving": 10,
            "case_study": 15,
            "project": 30,
            "design": 45
        }
        
        # Adjust for Bloom's level
        level_multipliers = {
            "remember": 0.8,
            "understand": 1.0,
            "apply": 1.2,
            "analyze": 1.5,
            "evaluate": 1.8,
            "create": 2.0
        }
        
        base_time = base_times.get(question_type, 5)
        multiplier = level_multipliers.get(bloom_level, 1.0)
        
        return int(base_time * multiplier)
    
    def _generate_options(self, objective: LearningObjective) -> List[str]:
        """Generate multiple choice options."""
        # In a real implementation, these would be contextually relevant
        correct = f"Correct answer for {objective.description}"
        distractors = [
            f"Plausible but incorrect option 1",
            f"Common misconception about {objective.description}",
            f"Partially correct but incomplete answer"
        ]
        
        # Randomize order (in production)
        options = [correct] + distractors
        return options
    
    def _generate_rubric(
        self,
        question_type: str,
        objective: LearningObjective
    ) -> Dict[str, Any]:
        """Generate a rubric for open-ended questions."""
        criteria = self.rubric_criteria.get(question_type, ["accuracy"])
        
        rubric = {
            "total_points": 10,
            "criteria": {}
        }
        
        points_per_criterion = 10 // len(criteria)
        
        for criterion in criteria:
            rubric["criteria"][criterion] = {
                "points": points_per_criterion,
                "levels": {
                    "excellent": {
                        "points": points_per_criterion,
                        "description": f"Demonstrates excellent {criterion}"
                    },
                    "good": {
                        "points": int(points_per_criterion * 0.75),
                        "description": f"Shows good {criterion}"
                    },
                    "satisfactory": {
                        "points": int(points_per_criterion * 0.5),
                        "description": f"Adequate {criterion}"
                    },
                    "needs_improvement": {
                        "points": int(points_per_criterion * 0.25),
                        "description": f"Limited {criterion}"
                    }
                }
            }
        
        return rubric
    
    def _enhance_for_summative(
        self,
        questions: List[AssessmentQuestion],
        objectives: List[LearningObjective]
    ) -> List[AssessmentQuestion]:
        """Enhance questions for summative assessment."""
        enhanced = []
        
        # Add integrated questions that cover multiple objectives
        for i in range(0, len(questions), 3):
            group = questions[i:i+3]
            
            if len(group) >= 2:
                # Create an integrated question
                integrated = AssessmentQuestion(
                    id=f"integrated_{datetime.now().timestamp()}",
                    type="integrated",
                    objective_id=",".join([q.objective_id for q in group]),
                    question=self._create_integrated_question(group),
                    difficulty=max(q.difficulty for q in group),
                    bloom_level="analyze",  # Integrated questions require analysis
                    estimated_time=sum(q.estimated_time for q in group)
                )
                enhanced.append(integrated)
            
            enhanced.extend(group)
        
        # Add a capstone project question
        if len(objectives) > 5:
            capstone = AssessmentQuestion(
                id=f"capstone_{datetime.now().timestamp()}",
                type="project",
                objective_id="all",
                question=self._create_capstone_question(objectives),
                difficulty=DifficultyLevel.ADVANCED.value,
                bloom_level="create",
                estimated_time=60,
                rubric=self._generate_rubric("project", objectives[0])
            )
            enhanced.append(capstone)
        
        return enhanced
    
    def _create_integrated_question(self, questions: List[AssessmentQuestion]) -> str:
        """Create an integrated question from multiple questions."""
        topics = [q.question.split()[2] for q in questions[:2]]  # Extract key topics
        return f"Analyze how {topics[0]} relates to {topics[1]} and explain their combined impact."
    
    def _create_capstone_question(self, objectives: List[LearningObjective]) -> str:
        """Create a capstone project question."""
        key_concepts = [obj.description.split()[-1] for obj in objectives[:3]]
        return (
            f"Design and implement a comprehensive solution that demonstrates "
            f"your understanding of {', '.join(key_concepts)}, and related concepts. "
            f"Your solution should address a real-world scenario and include "
            f"documentation of your design decisions."
        )
    
    async def evaluate_response(
        self,
        question: AssessmentQuestion,
        response: str,
        rubric_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluate a response to an assessment question."""
        try:
            evaluation = {
                "question_id": question.id,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            
            if question.type == "multiple_choice":
                # Simple correct/incorrect for MC
                is_correct = response == str(question.correct_answer)
                evaluation["score"] = 1.0 if is_correct else 0.0
                evaluation["feedback"] = "Correct!" if is_correct else "Incorrect. Review the material."
            
            elif question.rubric:
                # Rubric-based evaluation
                rubric = rubric_override or question.rubric
                scores = {}
                total_points = 0
                earned_points = 0
                
                for criterion, details in rubric["criteria"].items():
                    # In production, this would use NLP or instructor input
                    # For now, simulate with response length as proxy
                    score_level = self._determine_score_level(response, criterion)
                    points = details["levels"][score_level]["points"]
                    
                    scores[criterion] = {
                        "level": score_level,
                        "points": points,
                        "max_points": details["points"]
                    }
                    
                    total_points += details["points"]
                    earned_points += points
                
                evaluation["score"] = earned_points / total_points if total_points > 0 else 0
                evaluation["rubric_scores"] = scores
                evaluation["feedback"] = self._generate_feedback(scores)
            
            else:
                # Default evaluation
                evaluation["score"] = 0.5  # Placeholder
                evaluation["feedback"] = "Response recorded. Manual review required."
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Failed to evaluate response: {e}")
            raise
    
    def _determine_score_level(self, response: str, criterion: str) -> str:
        """Determine score level for a criterion (simplified)."""
        # In production, this would use sophisticated NLP
        response_length = len(response.split())
        
        if response_length > 100:
            return "excellent"
        elif response_length > 50:
            return "good"
        elif response_length > 20:
            return "satisfactory"
        else:
            return "needs_improvement"
    
    def _generate_feedback(self, rubric_scores: Dict[str, Any]) -> str:
        """Generate feedback based on rubric scores."""
        strengths = []
        improvements = []
        
        for criterion, score_data in rubric_scores.items():
            if score_data["level"] in ["excellent", "good"]:
                strengths.append(criterion)
            elif score_data["level"] == "needs_improvement":
                improvements.append(criterion)
        
        feedback = ""
        
        if strengths:
            feedback += f"Strengths: {', '.join(strengths)}. "
        
        if improvements:
            feedback += f"Areas for improvement: {', '.join(improvements)}. "
        
        if not strengths and not improvements:
            feedback = "Your response has been recorded for review."
        
        return feedback
    
    async def analyze_assessment_effectiveness(
        self,
        assessment_results: List[Dict[str, Any]],
        objectives: List[LearningObjective]
    ) -> Dict[str, Any]:
        """Analyze the effectiveness of an assessment."""
        try:
            analysis = {
                "total_questions": len(assessment_results),
                "average_score": 0.0,
                "objective_coverage": {},
                "difficulty_analysis": {},
                "time_analysis": {},
                "recommendations": []
            }
            
            # Calculate average score
            scores = [r.get("score", 0) for r in assessment_results]
            analysis["average_score"] = sum(scores) / len(scores) if scores else 0
            
            # Analyze objective coverage
            covered_objectives = set()
            for result in assessment_results:
                obj_id = result.get("objective_id")
                if obj_id:
                    covered_objectives.add(obj_id)
            
            total_objectives = len(objectives)
            coverage_rate = len(covered_objectives) / total_objectives if total_objectives > 0 else 0
            
            analysis["objective_coverage"] = {
                "covered": len(covered_objectives),
                "total": total_objectives,
                "coverage_rate": coverage_rate,
                "missing_objectives": [obj.id for obj in objectives if obj.id not in covered_objectives]
            }
            
            # Difficulty analysis
            difficulty_scores = {}
            for result in assessment_results:
                difficulty = result.get("difficulty", 3)
                if difficulty not in difficulty_scores:
                    difficulty_scores[difficulty] = []
                difficulty_scores[difficulty].append(result.get("score", 0))
            
            for difficulty, scores in difficulty_scores.items():
                analysis["difficulty_analysis"][f"level_{difficulty}"] = {
                    "average_score": sum(scores) / len(scores) if scores else 0,
                    "num_questions": len(scores)
                }
            
            # Generate recommendations
            if analysis["average_score"] < 0.6:
                analysis["recommendations"].append(
                    "Consider adding more scaffolding or practice opportunities"
                )
            
            if coverage_rate < 0.8:
                analysis["recommendations"].append(
                    "Increase objective coverage in assessment"
                )
            
            # Check for difficulty imbalance
            if len(difficulty_scores) == 1:
                analysis["recommendations"].append(
                    "Vary difficulty levels for better assessment"
                )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze assessment effectiveness: {e}")
            raise
