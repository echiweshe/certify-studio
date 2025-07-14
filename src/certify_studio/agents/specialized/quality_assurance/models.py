"""
Data models for the Quality Assurance Agent.

This module defines all data structures used by the QA agent for validation,
benchmarking, and quality improvement.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class QATaskType(str, Enum):
    """Types of QA tasks."""
    VALIDATION = "validation"
    BENCHMARKING = "benchmarking"
    MONITORING = "monitoring"
    IMPROVEMENT = "improvement"
    CERTIFICATION_CHECK = "certification_check"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    FEEDBACK_ANALYSIS = "feedback_analysis"


@dataclass
class QATask:
    """Represents a QA task to be performed."""
    id: UUID = field(default_factory=uuid4)
    task_type: QATaskType = QATaskType.VALIDATION
    content_id: str = ""
    priority: int = 5  # 1-10, 10 being highest
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_for: Optional[datetime] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: Optional[Any] = None


@dataclass
class BenchmarkResult:
    """Result of benchmark comparison."""
    benchmark_id: str = ""
    benchmark_name: str = ""
    score: float = 0.0
    target_score: float = 0.0
    passed: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class QAMetrics:
    """Aggregated QA metrics."""
    total_validations: int = 0
    passed_validations: int = 0
    failed_validations: int = 0
    average_quality_score: float = 0.0
    common_issues: List[Dict[str, Any]] = field(default_factory=list)
    improvement_rate: float = 0.0
    processing_time_avg: float = 0.0


@dataclass
class ContinuousMonitoringData:
    """Data from continuous monitoring."""
    monitoring_id: str = ""
    content_id: str = ""
    metrics_over_time: List[Dict[str, Any]] = field(default_factory=list)
    alerts_triggered: List[Dict[str, Any]] = field(default_factory=list)
    trends: Dict[str, str] = field(default_factory=dict)
    last_check: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceReport:
    """Performance analysis report."""
    content_id: str = ""
    generation_time: float = 0.0
    processing_time: float = 0.0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    bottlenecks: List[str] = field(default_factory=list)
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class CertificationMapping:
    """Mapping of content to certification objectives."""
    certification_id: str = ""
    certification_name: str = ""
    objective_mappings: Dict[str, List[str]] = field(default_factory=dict)
    coverage_percentage: float = 0.0
    gap_analysis: List[str] = field(default_factory=list)


@dataclass
class FeedbackAnalysis:
    """Analysis of user feedback."""
    content_id: str = ""
    total_feedback: int = 0
    sentiment_score: float = 0.0
    common_themes: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    satisfaction_score: float = 0.0


@dataclass
class QAReportData:
    """Complete QA report data."""
    report_id: UUID = field(default_factory=uuid4)
    content_id: str = ""
    validation_report: Optional['ValidationReport'] = None
    benchmark_results: List[BenchmarkResult] = field(default_factory=list)
    performance_report: Optional[PerformanceReport] = None
    certification_mapping: Optional[CertificationMapping] = None
    feedback_analysis: Optional[FeedbackAnalysis] = None
    overall_recommendation: str = ""
    generated_at: datetime = field(default_factory=datetime.now)


class QualityDimension(str, Enum):
    """Dimensions of quality to assess."""
    TECHNICAL_ACCURACY = "technical_accuracy"
    PEDAGOGICAL_EFFECTIVENESS = "pedagogical_effectiveness"
    CERTIFICATION_ALIGNMENT = "certification_alignment"
    CONTENT_COMPLETENESS = "content_completeness"
    ACCESSIBILITY_COMPLIANCE = "accessibility_compliance"
    PERFORMANCE_EFFICIENCY = "performance_efficiency"
    USER_EXPERIENCE = "user_experience"
    VISUAL_QUALITY = "visual_quality"
    INTERACTIVE_ENGAGEMENT = "interactive_engagement"
    LEARNING_OUTCOMES = "learning_outcomes"


class ValidationStatus(str, Enum):
    """Status of validation process."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    REQUIRES_REVIEW = "requires_review"


class SeverityLevel(str, Enum):
    """Severity levels for issues found."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class BenchmarkType(str, Enum):
    """Types of quality benchmarks."""
    INDUSTRY_STANDARD = "industry_standard"
    CERTIFICATION_REQUIREMENT = "certification_requirement"
    BEST_PRACTICE = "best_practice"
    ACCESSIBILITY_STANDARD = "accessibility_standard"
    PERFORMANCE_TARGET = "performance_target"
    USER_SATISFACTION = "user_satisfaction"


class ImprovementType(str, Enum):
    """Types of improvements that can be suggested."""
    CONTENT_CORRECTION = "content_correction"
    PEDAGOGICAL_ENHANCEMENT = "pedagogical_enhancement"
    VISUAL_IMPROVEMENT = "visual_improvement"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ACCESSIBILITY_FIX = "accessibility_fix"
    STRUCTURAL_CHANGE = "structural_change"
    INTERACTIVE_ADDITION = "interactive_addition"


@dataclass
class ValidationIssue:
    """Represents an issue found during validation."""
    id: UUID = field(default_factory=uuid4)
    dimension: QualityDimension = QualityDimension.TECHNICAL_ACCURACY
    severity: SeverityLevel = SeverityLevel.MEDIUM
    title: str = ""
    description: str = ""
    location: Dict[str, Any] = field(default_factory=dict)  # Where in content
    evidence: List[str] = field(default_factory=list)
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False
    confidence: float = 0.8
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class QualityScore:
    """Score for a specific quality dimension."""
    dimension: QualityDimension
    score: float  # 0.0 to 1.0
    confidence: float  # How confident we are in this score
    evidence: List[str] = field(default_factory=list)
    sub_scores: Dict[str, float] = field(default_factory=dict)
    benchmark_comparison: Optional[float] = None  # How we compare to benchmark


@dataclass
class TechnicalAccuracy:
    """Technical accuracy validation results."""
    is_accurate: bool = True
    accuracy_score: float = 0.0
    verified_facts: List[Dict[str, Any]] = field(default_factory=list)
    incorrect_statements: List[ValidationIssue] = field(default_factory=list)
    outdated_information: List[ValidationIssue] = field(default_factory=list)
    missing_context: List[ValidationIssue] = field(default_factory=list)
    code_validation_results: Dict[str, Any] = field(default_factory=dict)
    reference_sources: List[str] = field(default_factory=list)


@dataclass
class CertificationAlignment:
    """Certification alignment validation results."""
    certification_id: str = ""
    alignment_score: float = 0.0
    covered_objectives: List[str] = field(default_factory=list)
    missing_objectives: List[str] = field(default_factory=list)
    partial_objectives: List[Dict[str, float]] = field(default_factory=list)
    depth_analysis: Dict[str, float] = field(default_factory=dict)
    weight_distribution: Dict[str, float] = field(default_factory=dict)
    exam_readiness_score: float = 0.0


@dataclass
class PerformanceMetrics:
    """Performance metrics for content generation and delivery."""
    generation_time: float = 0.0  # seconds
    render_time: float = 0.0
    file_size: Dict[str, int] = field(default_factory=dict)  # bytes by format
    memory_usage: float = 0.0  # MB
    cpu_usage: float = 0.0  # percentage
    gpu_usage: float = 0.0  # percentage
    api_calls: int = 0
    api_costs: float = 0.0  # USD
    optimization_opportunities: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AccessibilityReport:
    """Accessibility compliance report."""
    wcag_level: str = "AA"  # AA or AAA
    compliance_score: float = 0.0
    passed_criteria: List[str] = field(default_factory=list)
    failed_criteria: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    alt_text_coverage: float = 1.0
    color_contrast_issues: List[Dict[str, Any]] = field(default_factory=list)
    keyboard_navigation: bool = True
    screen_reader_compatible: bool = True
    captions_available: bool = True


@dataclass
class PedagogicalEffectiveness:
    """Pedagogical effectiveness assessment."""
    effectiveness_score: float = 0.0
    cognitive_load_optimization: float = 0.0
    learning_objectives_clarity: float = 0.0
    engagement_prediction: float = 0.0
    retention_prediction: float = 0.0
    difficulty_progression: Dict[str, float] = field(default_factory=dict)
    teaching_method_variety: float = 0.0
    assessment_quality: float = 0.0
    feedback_quality: float = 0.0


@dataclass
class VisualQualityAssessment:
    """Visual quality assessment results."""
    overall_quality: float = 0.0
    clarity_score: float = 0.0
    consistency_score: float = 0.0
    aesthetic_score: float = 0.0
    brand_compliance: float = 0.0
    animation_smoothness: float = 0.0
    color_harmony: float = 0.0
    typography_quality: float = 0.0
    layout_effectiveness: float = 0.0
    visual_hierarchy: float = 0.0


@dataclass
class InteractiveQualityAssessment:
    """Interactive elements quality assessment."""
    interactivity_score: float = 0.0
    responsiveness: float = 0.0
    feedback_quality: float = 0.0
    error_handling: float = 0.0
    user_guidance: float = 0.0
    engagement_mechanics: float = 0.0
    quiz_quality: float = 0.0
    simulation_effectiveness: float = 0.0


@dataclass
class QualityBenchmark:
    """Quality benchmark for comparison."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    type: BenchmarkType = BenchmarkType.INDUSTRY_STANDARD
    dimension: QualityDimension = QualityDimension.TECHNICAL_ACCURACY
    target_score: float = 0.85
    description: str = ""
    source: str = ""
    criteria: Dict[str, Any] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ImprovementSuggestion:
    """Suggestion for content improvement."""
    id: UUID = field(default_factory=uuid4)
    type: ImprovementType = ImprovementType.CONTENT_CORRECTION
    priority: SeverityLevel = SeverityLevel.MEDIUM
    title: str = ""
    description: str = ""
    rationale: str = ""
    expected_impact: Dict[QualityDimension, float] = field(default_factory=dict)
    implementation_steps: List[str] = field(default_factory=list)
    estimated_effort: float = 0.0  # hours
    auto_implementable: bool = False
    implementation_code: Optional[str] = None
    before_example: Optional[str] = None
    after_example: Optional[str] = None


@dataclass
class QualityMetrics:
    """Comprehensive quality metrics."""
    overall_score: float = 0.0
    dimension_scores: Dict[QualityDimension, QualityScore] = field(default_factory=dict)
    technical_accuracy: TechnicalAccuracy = field(default_factory=TechnicalAccuracy)
    certification_alignment: CertificationAlignment = field(default_factory=CertificationAlignment)
    performance_metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    accessibility_report: AccessibilityReport = field(default_factory=AccessibilityReport)
    pedagogical_effectiveness: PedagogicalEffectiveness = field(default_factory=PedagogicalEffectiveness)
    visual_quality: VisualQualityAssessment = field(default_factory=VisualQualityAssessment)
    interactive_quality: InteractiveQualityAssessment = field(default_factory=InteractiveQualityAssessment)
    benchmark_comparisons: Dict[str, float] = field(default_factory=dict)
    confidence_level: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationReport:
    """Complete validation report."""
    id: UUID = field(default_factory=uuid4)
    content_id: str = ""
    status: ValidationStatus = ValidationStatus.PENDING
    quality_metrics: QualityMetrics = field(default_factory=QualityMetrics)
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    improvement_suggestions: List[ImprovementSuggestion] = field(default_factory=list)
    auto_fixes_applied: List[str] = field(default_factory=list)
    manual_review_required: bool = False
    review_notes: List[str] = field(default_factory=list)
    generation_metadata: Dict[str, Any] = field(default_factory=dict)
    validation_duration: float = 0.0  # seconds
    created_at: datetime = field(default_factory=datetime.now)
    validated_by: str = "QualityAssuranceAgent"


@dataclass
class QAFeedback:
    """Feedback from QA process for learning."""
    id: UUID = field(default_factory=uuid4)
    content_id: str = ""
    feedback_type: str = ""  # "user", "automated", "expert"
    quality_impact: Dict[QualityDimension, float] = field(default_factory=dict)
    issues_found_post_release: List[ValidationIssue] = field(default_factory=list)
    user_satisfaction_score: Optional[float] = None
    learning_effectiveness_score: Optional[float] = None
    suggestions_implemented: List[str] = field(default_factory=list)
    suggestions_rejected: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ContinuousMonitoring:
    """Continuous monitoring configuration and results."""
    monitoring_id: UUID = field(default_factory=uuid4)
    content_id: str = ""
    monitoring_interval: int = 3600  # seconds
    quality_thresholds: Dict[QualityDimension, float] = field(default_factory=dict)
    alert_conditions: List[Dict[str, Any]] = field(default_factory=list)
    historical_metrics: List[QualityMetrics] = field(default_factory=list)
    trend_analysis: Dict[QualityDimension, str] = field(default_factory=dict)  # "improving", "declining", "stable"
    anomalies_detected: List[Dict[str, Any]] = field(default_factory=list)
    last_check: datetime = field(default_factory=datetime.now)
    next_check: datetime = field(default_factory=datetime.now)


class QARequest(BaseModel):
    """Request for quality assurance validation."""
    content_id: str = Field(..., description="ID of content to validate")
    content_type: str = Field(..., description="Type of content (course, lesson, etc)")
    content_data: Dict[str, Any] = Field(..., description="The content to validate")
    certification_id: Optional[str] = Field(None, description="Certification to align with")
    validation_dimensions: List[QualityDimension] = Field(
        default_factory=lambda: list(QualityDimension),
        description="Which dimensions to validate"
    )
    benchmarks: List[QualityBenchmark] = Field(
        default_factory=list,
        description="Benchmarks to compare against"
    )
    auto_fix: bool = Field(True, description="Automatically fix issues where possible")
    strict_mode: bool = Field(False, description="Fail on any issue")
    performance_budget: Dict[str, float] = Field(
        default_factory=dict,
        description="Performance constraints"
    )
    custom_checks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Custom validation checks"
    )

    class Config:
        arbitrary_types_allowed = True


class QAResult(BaseModel):
    """Result of quality assurance validation."""
    success: bool = Field(..., description="Whether validation passed")
    validation_report: ValidationReport = Field(..., description="Detailed validation report")
    quality_score: float = Field(..., description="Overall quality score (0-1)")
    improvements_applied: List[str] = Field(
        default_factory=list,
        description="Improvements automatically applied"
    )
    manual_review_required: bool = Field(False, description="Whether manual review is needed")
    next_steps: List[str] = Field(
        default_factory=list,
        description="Recommended next steps"
    )
    monitoring_enabled: bool = Field(False, description="Whether continuous monitoring is enabled")
    monitoring_config: Optional[ContinuousMonitoring] = Field(
        None,
        description="Continuous monitoring configuration"
    )

    class Config:
        arbitrary_types_allowed = True


@dataclass
class LearningRecord:
    """Record of what the QA agent has learned."""
    id: UUID = field(default_factory=uuid4)
    pattern_type: str = ""  # "common_error", "quality_indicator", "best_practice"
    pattern_description: str = ""
    occurrences: int = 0
    impact_on_quality: Dict[QualityDimension, float] = field(default_factory=dict)
    suggested_prevention: str = ""
    confidence: float = 0.0
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    applicable_contexts: List[str] = field(default_factory=list)
