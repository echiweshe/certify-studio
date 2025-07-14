"""
Quality assurance and metrics repository for Certify Studio.

This module provides data access layer for quality-related operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from ..models.quality import (
    QualityCheck, QualityMetric, QualityIssue, QualityBenchmark,
    UserFeedback, ConceptQualityScore, ContentImprovement, QualityReport,
    QualityDimension, FeedbackType, BenchmarkType
)
from ..models.base import QualityStatus
from .base_repo import BaseRepository, RepositoryError


class QualityRepository(BaseRepository[QualityCheck]):
    """Repository for quality-related operations."""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(QualityCheck, db_session)
    
    # QualityCheck operations
    
    async def create_quality_check(
        self,
        generation_id: UUID,
        check_type: str,
        check_name: str,
        status: str = QualityStatus.PENDING,
        overall_score: Optional[float] = None,
        passed: Optional[bool] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> QualityCheck:
        """Create a new quality check."""
        check = QualityCheck(
            generation_id=generation_id,
            check_type=check_type,
            check_name=check_name,
            status=status,
            overall_score=overall_score,
            passed=passed,
            findings=details or {}
        )
        
        if status == QualityStatus.COMPLETED:
            check.completed_at = datetime.utcnow()
        
        self.db_session.add(check)
        await self.db_session.flush()
        return check
    
    async def get_generation_quality_checks(
        self,
        generation_id: UUID,
        include_metrics: bool = False
    ) -> List[QualityCheck]:
        """Get all quality checks for a generation."""
        query = select(QualityCheck).where(
            QualityCheck.generation_id == generation_id
        ).order_by(QualityCheck.created_at.desc())
        
        if include_metrics:
            query = query.options(selectinload(QualityCheck.metrics))
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def update_quality_check_status(
        self,
        check_id: UUID,
        status: str,
        overall_score: Optional[float] = None,
        passed: Optional[bool] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Update quality check status."""
        update_data = {"status": status}
        
        if overall_score is not None:
            update_data["overall_score"] = overall_score
        if passed is not None:
            update_data["passed"] = passed
        if error_message is not None:
            update_data["error_message"] = error_message
        
        if status == QualityStatus.PROCESSING and "started_at" not in update_data:
            update_data["started_at"] = datetime.utcnow()
        elif status in [QualityStatus.COMPLETED, QualityStatus.FAILED]:
            update_data["completed_at"] = datetime.utcnow()
        
        await self.db_session.execute(
            update(QualityCheck)
            .where(QualityCheck.id == check_id)
            .values(**update_data)
        )
    
    # QualityMetric operations
    
    async def create_quality_metric(
        self,
        quality_check_id: UUID,
        metric_name: str,
        metric_value: float,
        dimension: Optional[str] = None,
        threshold: Optional[float] = None,
        passed: Optional[bool] = None
    ) -> QualityMetric:
        """Create a quality metric."""
        if passed is None and threshold is not None:
            passed = metric_value >= threshold
        
        metric = QualityMetric(
            quality_check_id=quality_check_id,
            dimension=QualityDimension(dimension) if dimension else QualityDimension.ACCURACY,
            metric_name=metric_name,
            metric_display_name=metric_name.replace("_", " ").title(),
            value=metric_value,
            threshold_value=threshold,
            passed=passed if passed is not None else True
        )
        
        self.db_session.add(metric)
        await self.db_session.flush()
        return metric
    
    async def get_quality_metrics(
        self,
        quality_check_id: UUID
    ) -> List[QualityMetric]:
        """Get all metrics for a quality check."""
        result = await self.db_session.execute(
            select(QualityMetric)
            .where(QualityMetric.quality_check_id == quality_check_id)
            .order_by(QualityMetric.dimension, QualityMetric.metric_name)
        )
        return result.scalars().all()
    
    # QualityIssue operations
    
    async def create_quality_issue(
        self,
        quality_check_id: UUID,
        issue_type: str,
        issue_code: str,
        severity: str,
        title: str,
        description: str,
        suggestion: Optional[str] = None,
        content_piece_id: Optional[UUID] = None
    ) -> QualityIssue:
        """Create a quality issue."""
        issue = QualityIssue(
            quality_check_id=quality_check_id,
            content_piece_id=content_piece_id,
            issue_type=issue_type,
            issue_code=issue_code,
            severity=severity,
            title=title,
            description=description,
            suggestion=suggestion
        )
        
        self.db_session.add(issue)
        await self.db_session.flush()
        return issue
    
    async def get_quality_issues(
        self,
        quality_check_id: UUID,
        severity: Optional[str] = None
    ) -> List[QualityIssue]:
        """Get quality issues for a check."""
        query = select(QualityIssue).where(
            QualityIssue.quality_check_id == quality_check_id
        )
        
        if severity:
            query = query.where(QualityIssue.severity == severity)
        
        query = query.order_by(QualityIssue.severity, QualityIssue.impact_score.desc())
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    # UserFeedback operations
    
    async def create_user_feedback(
        self,
        user_id: UUID,
        generation_id: UUID,
        feedback_type: str,
        rating: Optional[int] = None,
        feedback_text: Optional[str] = None,
        categories: Optional[List[str]] = None
    ) -> UserFeedback:
        """Create user feedback."""
        feedback = UserFeedback(
            user_id=user_id,
            generation_id=generation_id,
            feedback_type=FeedbackType(feedback_type),
            rating=rating,
            comment=feedback_text,
            categories=categories or []
        )
        
        self.db_session.add(feedback)
        await self.db_session.flush()
        return feedback
    
    async def get_generation_feedback(
        self,
        generation_id: UUID,
        feedback_type: Optional[FeedbackType] = None
    ) -> List[UserFeedback]:
        """Get all feedback for a generation."""
        query = select(UserFeedback).where(
            UserFeedback.generation_id == generation_id
        )
        
        if feedback_type:
            query = query.where(UserFeedback.feedback_type == feedback_type)
        
        query = query.order_by(UserFeedback.created_at.desc())
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def get_user_feedback(
        self,
        user_id: UUID,
        limit: int = 50
    ) -> List[UserFeedback]:
        """Get feedback from a specific user."""
        result = await self.db_session.execute(
            select(UserFeedback)
            .where(UserFeedback.user_id == user_id)
            .order_by(UserFeedback.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    # QualityBenchmark operations
    
    async def get_active_benchmarks(
        self,
        benchmark_type: Optional[BenchmarkType] = None
    ) -> List[QualityBenchmark]:
        """Get active quality benchmarks."""
        query = select(QualityBenchmark).where(
            QualityBenchmark.is_active == True
        )
        
        if benchmark_type:
            query = query.where(QualityBenchmark.benchmark_type == benchmark_type)
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def create_benchmark(
        self,
        name: str,
        benchmark_type: str,
        version: str,
        metrics: Dict[str, float],
        description: Optional[str] = None,
        source: Optional[str] = None
    ) -> QualityBenchmark:
        """Create a quality benchmark."""
        benchmark = QualityBenchmark(
            name=name,
            benchmark_type=BenchmarkType(benchmark_type),
            version=version,
            metrics=metrics,
            description=description,
            source=source
        )
        
        self.db_session.add(benchmark)
        await self.db_session.flush()
        return benchmark
    
    # ContentImprovement operations
    
    async def create_content_improvement(
        self,
        content_piece_id: UUID,
        improvement_type: str,
        trigger_source: str,
        changes_summary: str,
        before_snapshot: Dict[str, Any],
        after_snapshot: Dict[str, Any],
        quality_score_before: Optional[float] = None,
        quality_score_after: Optional[float] = None
    ) -> ContentImprovement:
        """Record a content improvement."""
        improvement = ContentImprovement(
            content_piece_id=content_piece_id,
            improvement_type=improvement_type,
            trigger_source=trigger_source,
            changes_summary=changes_summary,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            quality_score_before=quality_score_before,
            quality_score_after=quality_score_after
        )
        
        if quality_score_before and quality_score_after:
            improvement.improvement_percentage = (
                (quality_score_after - quality_score_before) / quality_score_before * 100
            )
        
        self.db_session.add(improvement)
        await self.db_session.flush()
        return improvement
    
    async def get_content_improvements(
        self,
        content_piece_id: UUID
    ) -> List[ContentImprovement]:
        """Get improvement history for content."""
        result = await self.db_session.execute(
            select(ContentImprovement)
            .where(ContentImprovement.content_piece_id == content_piece_id)
            .order_by(ContentImprovement.created_at.desc())
        )
        return result.scalars().all()
    
    # QualityReport operations
    
    async def create_quality_report(
        self,
        generation_id: UUID,
        report_type: str,
        report_name: str,
        overall_quality_score: float,
        dimension_scores: Dict[str, float],
        full_report: Dict[str, Any],
        strengths: Optional[List[str]] = None,
        weaknesses: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None
    ) -> QualityReport:
        """Create a quality report."""
        report = QualityReport(
            generation_id=generation_id,
            report_type=report_type,
            report_name=report_name,
            overall_quality_score=overall_quality_score,
            dimension_scores=dimension_scores,
            full_report=full_report,
            strengths=strengths or [],
            weaknesses=weaknesses or [],
            recommendations=recommendations or []
        )
        
        self.db_session.add(report)
        await self.db_session.flush()
        return report
    
    async def get_generation_reports(
        self,
        generation_id: UUID,
        report_type: Optional[str] = None
    ) -> List[QualityReport]:
        """Get quality reports for a generation."""
        query = select(QualityReport).where(
            QualityReport.generation_id == generation_id
        )
        
        if report_type:
            query = query.where(QualityReport.report_type == report_type)
        
        query = query.order_by(QualityReport.created_at.desc())
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    # Aggregate operations
    
    async def get_average_quality_score(
        self,
        generation_id: UUID
    ) -> Optional[float]:
        """Get average quality score for a generation."""
        result = await self.db_session.execute(
            select(func.avg(QualityCheck.overall_score))
            .where(
                and_(
                    QualityCheck.generation_id == generation_id,
                    QualityCheck.status == QualityStatus.COMPLETED,
                    QualityCheck.overall_score.isnot(None)
                )
            )
        )
        return result.scalar()
    
    async def get_feedback_summary(
        self,
        generation_id: UUID
    ) -> Dict[str, Any]:
        """Get feedback summary for a generation."""
        # Count feedback by type
        feedback_counts = await self.db_session.execute(
            select(
                UserFeedback.feedback_type,
                func.count(UserFeedback.id).label("count")
            )
            .where(UserFeedback.generation_id == generation_id)
            .group_by(UserFeedback.feedback_type)
        )
        
        # Average rating
        avg_rating = await self.db_session.execute(
            select(func.avg(UserFeedback.rating))
            .where(
                and_(
                    UserFeedback.generation_id == generation_id,
                    UserFeedback.rating.isnot(None)
                )
            )
        )
        
        # Rating distribution
        rating_dist = await self.db_session.execute(
            select(
                UserFeedback.rating,
                func.count(UserFeedback.id).label("count")
            )
            .where(
                and_(
                    UserFeedback.generation_id == generation_id,
                    UserFeedback.rating.isnot(None)
                )
            )
            .group_by(UserFeedback.rating)
        )
        
        return {
            "feedback_by_type": {row[0].value: row[1] for row in feedback_counts},
            "average_rating": avg_rating.scalar() or 0,
            "rating_distribution": {row[0]: row[1] for row in rating_dist},
            "total_feedback": sum(row[1] for row in feedback_counts)
        }
