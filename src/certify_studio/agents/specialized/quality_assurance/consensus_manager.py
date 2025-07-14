"""
Multi-Agent Consensus for Quality Assurance

Implements true multi-agent architecture where multiple QA agents
critique content and reach consensus on quality.
"""

import asyncio
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from uuid import UUID, uuid4
import logging

from .models import (
    ValidationReport,
    QualityMetrics,
    QualityDimension,
    QualityScore,
    ValidationIssue,
    SeverityLevel,
    ValidationStatus
)
from ....agents.core.autonomous_agent import AutonomousAgent, AgentCapability
from ....shared.models import AgentBelief, AgentGoal, AgentPlan

logger = logging.getLogger(__name__)


class QualityConsensusOrchestrator:
    """Orchestrates multiple QA critics to reach consensus on quality."""
    
    def __init__(self, num_critics: int = 5):
        self.num_critics = num_critics
        self.critics: List[QACriticAgent] = []
        
    async def initialize(self):
        """Initialize critic agents with different biases."""
        perspectives = [
            ("strict_technical", {"technical_accuracy": 2.0, "performance_efficiency": 1.5}),
            ("pedagogy_focused", {"pedagogical_effectiveness": 2.0, "learning_outcomes": 1.8}),
            ("user_advocate", {"user_experience": 2.0, "accessibility_compliance": 1.8}),
            ("cert_specialist", {"certification_alignment": 2.0, "content_completeness": 1.5}),
            ("balanced_critic", {})  # No bias
        ]
        
        for i in range(self.num_critics):
            name, bias = perspectives[i % len(perspectives)]
            critic = QACriticAgent(f"{name}_{i}", bias)
            await critic.initialize()
            self.critics.append(critic)
            
    async def evaluate_with_consensus(
        self,
        content: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> ValidationReport:
        """Multiple critics evaluate and reach consensus."""
        
        # Phase 1: Independent evaluation
        evaluations = await asyncio.gather(*[
            critic.evaluate_content(content, requirements)
            for critic in self.critics
        ])
        
        # Phase 2: Critics review each other's work
        for i, critic in enumerate(self.critics):
            other_evals = [e for j, e in enumerate(evaluations) if j != i]
            await critic.review_other_evaluations(evaluations[i], other_evals)
            
        # Phase 3: Debate and consensus
        final_report = await self._reach_consensus(evaluations, content)
        
        return final_report
        
    async def _reach_consensus(
        self,
        evaluations: List[ValidationReport],
        content: Dict[str, Any]
    ) -> ValidationReport:
        """Aggregate evaluations into consensus report."""
        
        # Collect all issues with voting
        issue_votes = {}
        for eval in evaluations:
            for issue in eval.issues:
                key = (issue.dimension, issue.title)
                if key not in issue_votes:
                    issue_votes[key] = {"issue": issue, "votes": 0}
                issue_votes[key]["votes"] += 1
                
        # Include issues with majority agreement
        consensus_issues = [
            data["issue"] for data in issue_votes.values()
            if data["votes"] >= len(evaluations) / 2
        ]
        
        # Average quality scores weighted by confidence
        dimension_scores = {}
        for dim in QualityDimension:
            scores = []
            weights = []
            for eval in evaluations:
                if dim in eval.quality_metrics.dimension_scores:
                    score_data = eval.quality_metrics.dimension_scores[dim]
                    scores.append(score_data.score)
                    weights.append(score_data.confidence)
                    
            if scores:
                weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
                dimension_scores[dim] = QualityScore(
                    dimension=dim,
                    score=weighted_score,
                    confidence=sum(weights) / len(weights)
                )
                
        overall_score = sum(s.score for s in dimension_scores.values()) / len(dimension_scores)
        
        return ValidationReport(
            content_id=content.get("id", str(uuid4())),
            status=self._determine_status(overall_score),
            quality_metrics=QualityMetrics(
                overall_score=overall_score,
                dimension_scores=dimension_scores
            ),
            issues=consensus_issues,
            validated_by="ConsensusOf" + str(len(evaluations)) + "Critics"
        )
        
    def _determine_status(self, score: float) -> ValidationStatus:
        if score >= 0.9:
            return ValidationStatus.PASSED
        elif score >= 0.7:
            return ValidationStatus.PASSED_WITH_WARNINGS
        else:
            return ValidationStatus.FAILED


class QACriticAgent(AutonomousAgent):
    """Individual critic agent with specific evaluation bias."""
    
    def __init__(self, name: str, bias: Dict[str, float]):
        super().__init__(
            name=f"QACritic_{name}",
            capabilities={
                AgentCapability.QUALITY_ASSESSMENT,
                AgentCapability.REASONING,
                AgentCapability.COLLABORATION
            }
        )
        self.evaluation_bias = bias
        
    async def evaluate_content(
        self,
        content: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> ValidationReport:
        """Evaluate content with personal bias."""
        
        issues = []
        dimension_scores = {}
        
        # Evaluate each dimension
        for dimension in QualityDimension:
            score = await self._evaluate_dimension(dimension, content)
            
            # Apply bias
            bias_factor = self.evaluation_bias.get(dimension.value, 1.0)
            if bias_factor > 1.0:
                # More critical of this dimension
                score *= 0.9 / bias_factor
                
            dimension_scores[dimension] = QualityScore(
                dimension=dimension,
                score=min(score, 1.0),
                confidence=0.8 if bias_factor > 1.0 else 0.6
            )
            
            # Find issues based on score
            if score < 0.7:
                issues.append(ValidationIssue(
                    dimension=dimension,
                    severity=SeverityLevel.HIGH if score < 0.5 else SeverityLevel.MEDIUM,
                    title=f"Low {dimension.value} score",
                    description=f"Score of {score:.2f} indicates issues",
                    confidence=0.7
                ))
                
        overall_score = sum(s.score for s in dimension_scores.values()) / len(dimension_scores)
        
        return ValidationReport(
            content_id=content.get("id", str(uuid4())),
            status=ValidationStatus.PENDING,
            quality_metrics=QualityMetrics(
                overall_score=overall_score,
                dimension_scores=dimension_scores
            ),
            issues=issues,
            validated_by=self.name
        )
        
    async def _evaluate_dimension(
        self,
        dimension: QualityDimension,
        content: Dict[str, Any]
    ) -> float:
        """Evaluate a specific quality dimension."""
        # Simplified scoring - in production would use specialized validators
        base_score = 0.8
        
        # Adjust based on content characteristics
        if dimension == QualityDimension.TECHNICAL_ACCURACY:
            if "code" in content and content.get("validated", False):
                base_score = 0.95
            elif "code" in content:
                base_score = 0.7
                
        elif dimension == QualityDimension.PEDAGOGICAL_EFFECTIVENESS:
            if content.get("learning_objectives") and content.get("assessments"):
                base_score = 0.9
                
        return base_score
        
    async def review_other_evaluations(
        self,
        own_eval: ValidationReport,
        other_evals: List[ValidationReport]
    ) -> None:
        """Review and potentially update based on others' findings."""
        
        # Check if others found issues I missed
        my_issue_keys = {(i.dimension, i.title) for i in own_eval.issues}
        
        for other_eval in other_evals:
            for issue in other_eval.issues:
                key = (issue.dimension, issue.title)
                if key not in my_issue_keys:
                    # Consider adopting this issue
                    if self._should_adopt_issue(issue):
                        own_eval.issues.append(issue)
                        
        # Adjust confidence based on consensus
        for dim, score in own_eval.quality_metrics.dimension_scores.items():
            other_scores = [
                e.quality_metrics.dimension_scores[dim].score
                for e in other_evals
                if dim in e.quality_metrics.dimension_scores
            ]
            if other_scores:
                avg_other = sum(other_scores) / len(other_scores)
                if abs(score.score - avg_other) > 0.2:
                    # Large disagreement reduces confidence
                    score.confidence *= 0.8
                    
    def _should_adopt_issue(self, issue: ValidationIssue) -> bool:
        """Decide whether to adopt an issue found by another critic."""
        # More likely to adopt issues in areas of bias
        if issue.dimension.value in self.evaluation_bias:
            return issue.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
        return issue.severity == SeverityLevel.CRITICAL
