"""
Data models for the pedagogical reasoning system.
"""

from typing import List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class LearningTheory(Enum):
    """Educational theories and approaches."""
    BLOOMS_TAXONOMY = "blooms_taxonomy"
    COGNITIVE_LOAD = "cognitive_load"
    SPACED_REPETITION = "spaced_repetition"
    CONSTRUCTIVISM = "constructivism"
    EXPERIENTIAL = "experiential"
    MASTERY_LEARNING = "mastery_learning"
    SCAFFOLDING = "scaffolding"
    ZONE_PROXIMAL_DEVELOPMENT = "zpd"


class DifficultyLevel(Enum):
    """Content difficulty levels."""
    BEGINNER = 1
    ELEMENTARY = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5


@dataclass
class LearningObjective:
    """Represents a learning objective."""
    id: str
    description: str
    domain: str  # cognitive, affective, psychomotor
    level: str  # remember, understand, apply, analyze, evaluate, create
    prerequisites: List[str] = field(default_factory=list)
    estimated_time: int = 10  # minutes
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE


@dataclass
class LearnerProfile:
    """Comprehensive learner profile."""
    id: str
    experience_level: str
    learning_style: str  # visual, auditory, kinesthetic, reading/writing
    pace_preference: str  # slow, moderate, fast
    prior_knowledge: List[str]
    goals: List[str]
    time_availability: str
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    progress_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class LearningPath:
    """Optimized learning path."""
    id: str
    objectives: List[LearningObjective]
    sequence: List[str]  # ordered objective IDs
    estimated_duration: int  # total minutes
    difficulty_progression: List[DifficultyLevel]
    personalization_notes: List[str]
    theories_applied: List[LearningTheory]
    checkpoints: List[Dict[str, Any]]
    adaptations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CognitiveLoadAssessment:
    """Assessment of cognitive load for content."""
    intrinsic_load: float  # 0-1, complexity of material
    extraneous_load: float  # 0-1, presentation complexity
    germane_load: float  # 0-1, schema construction effort
    total_load: float  # 0-1, combined load
    recommendations: List[str]
    optimizations: List[Dict[str, Any]]


@dataclass
class AssessmentQuestion:
    """Represents an assessment question."""
    id: str
    type: str  # multiple_choice, short_answer, scenario, case_study, project
    objective_id: str
    question: str
    difficulty: int
    bloom_level: str
    estimated_time: int
    options: List[str] = field(default_factory=list)
    correct_answer: Any = None
    rubric: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningStrategy:
    """Represents a learning strategy recommendation."""
    name: str
    description: str
    implementation: List[str]
    expected_benefit: str
    target_profile: Dict[str, Any] = field(default_factory=dict)
    effectiveness_data: Dict[str, float] = field(default_factory=dict)
