"""
Core interfaces and data models for Certify Studio.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class ValidationStatus(Enum):
    """Status of validation."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass
class ContentValidationResult:
    """Result of content validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    validation_timestamp: datetime
    validator_id: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class QualityMetrics:
    """Quality metrics for content."""
    accuracy_score: float
    completeness_score: float
    clarity_score: float
    engagement_score: float
    accessibility_score: float
    overall_score: float
    detailed_scores: Dict[str, float] = None
    
    def __post_init__(self):
        if self.detailed_scores is None:
            self.detailed_scores = {}
            
    def calculate_overall(self):
        """Calculate overall score from individual metrics."""
        scores = [
            self.accuracy_score,
            self.completeness_score,
            self.clarity_score,
            self.engagement_score,
            self.accessibility_score
        ]
        self.overall_score = sum(scores) / len(scores)


@dataclass
class PerformanceMetrics:
    """Performance metrics for the system."""
    generation_time: float
    validation_time: float
    total_time: float
    memory_usage: float
    cpu_usage: float
    gpu_usage: Optional[float] = None
    api_calls: int = 0
    tokens_used: int = 0
    cost_estimate: float = 0.0


@dataclass
class CertificationAlignment:
    """Alignment with certification requirements."""
    certification_id: str
    certification_name: str
    alignment_score: float
    covered_objectives: List[str]
    missing_objectives: List[str]
    coverage_percentage: float
    recommendations: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FeedbackSummary:
    """Summary of feedback received."""
    total_feedback_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    average_rating: float
    common_issues: List[str]
    improvement_suggestions: List[str]
    sentiment_score: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
