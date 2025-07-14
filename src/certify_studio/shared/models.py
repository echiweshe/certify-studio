"""
Shared models used across the Certify Studio platform.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


@dataclass
class LearningContent:
    """Represents educational content."""
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    content_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    quality_score: float = 0.0
    tags: List[str] = field(default_factory=list)


@dataclass
class QualityReport:
    """Comprehensive quality assessment report."""
    id: str = field(default_factory=lambda: str(uuid4()))
    content_id: str = ""
    overall_score: float = 0.0
    accuracy_score: float = 0.0
    completeness_score: float = 0.0
    clarity_score: float = 0.0
    engagement_score: float = 0.0
    accessibility_score: float = 0.0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    validator_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QARequest:
    """Request for quality assurance."""
    id: str = field(default_factory=lambda: str(uuid4()))
    content_id: str = ""
    content: Any = None
    check_types: List[str] = field(default_factory=list)
    priority: str = "normal"
    requester_id: str = ""
    requested_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QAResult:
    """Result of quality assurance check."""
    id: str = field(default_factory=lambda: str(uuid4()))
    request_id: str = ""
    status: str = "pending"
    report: Optional[QualityReport] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# Import from autonomous_agent to avoid circular imports
from ..agents.core.autonomous_agent import (
    AgentBelief,
    AgentGoal,
    AgentPlan
)


@dataclass
class PlanStep:
    """A single step in an agent's plan."""
    id: str = field(default_factory=lambda: str(uuid4()))
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_duration: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[Any] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
