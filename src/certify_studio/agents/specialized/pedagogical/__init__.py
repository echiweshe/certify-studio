"""
Pedagogical reasoning agent module.

This module provides a comprehensive pedagogical reasoning system for
optimizing learning experiences. It includes:

- Learning path optimization
- Cognitive load management
- Personalized content adaptation
- Assessment generation
- Learning strategy recommendations
- Educational theory application
"""

from .agent import PedagogicalReasoningAgent
from .models import (
    LearningTheory,
    DifficultyLevel,
    LearningObjective,
    LearnerProfile,
    LearningPath,
    CognitiveLoadAssessment,
    AssessmentQuestion,
    LearningStrategy
)

__all__ = [
    # Main agent
    "PedagogicalReasoningAgent",
    
    # Models
    "LearningTheory",
    "DifficultyLevel",
    "LearningObjective",
    "LearnerProfile",
    "LearningPath",
    "CognitiveLoadAssessment",
    "AssessmentQuestion",
    "LearningStrategy",
]

# Module metadata
__version__ = "1.0.0"
__author__ = "Certify Studio Team"
__description__ = "Pedagogical reasoning agent for educational content optimization"
