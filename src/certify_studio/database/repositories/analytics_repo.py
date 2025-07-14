"""
Analytics and tracking repository for Certify Studio.

This module provides data access layer for analytics operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date, timedelta

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.analytics import (
    UserActivity, GenerationAnalytics, DailyMetrics, FeatureUsage,
    PerformanceMetrics, BusinessMetric, UserSegment, UserSegmentMembership,
    ABTestExperiment, EventType, MetricType
)
from .base_repo import BaseRepository, RepositoryError


class AnalyticsRepository(BaseRepository[UserActivity]):
    """Repository for analytics operations."""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(UserActivity, db_session)
    
    # UserActivity operations
    
    async def record_user_activity(
        self,
        user_id: UUID,
        event_type: str,
        event_name: str,
        session_id: str,
        properties: Optional[Dict[str, Any]] = None,
        page_url: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserActivity:
        """Record a user activity event."""
        activity = UserActivity(
            user_id=user_id,
            event_type=EventType(event_type),
            event_name=event_name,
            session_id=session_id,
            properties=properties or {},
            page_url=page_url,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db_session.add(activity)
        await self.db_session.flush()
        return activity
    
    async def get_user_activities(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[EventType]] = None,
        limit: int = 100
    ) -> List[UserActivity]:
        """Get user activities with optional filters."""
        query = select(UserActivity).where(UserActivity.user_id == user_id)
        
        if start_date:
            query = query.where(UserActivity.created_at >= start_date)
        if end_date:
            query = query.where(UserActivity.created_at <= end_date)
        if event_types:
            query = query.where(UserActivity.event_type.in_(event_types))
        
        query = query.order_by(UserActivity.created_at.desc()).limit(limit)
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def get_user_sessions(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user session summaries."""
        # Get unique sessions
        sessions_query = select(
            UserActivity.session_id,
            func.min(UserActivity.created_at).label("start_time"),
            func.max(UserActivity.created_at).label("end_time"),
            func.count(UserActivity.id).label("event_count")
        ).where(
            UserActivity.user_id == user_id
        ).group_by(
            UserActivity.session_id
        ).order_by(
            func.max(UserActivity.created_at).desc()
        ).limit(limit)
        
        result = await self.db_session.execute(sessions_query)
        
        sessions = []
        for row in result:
            duration = (row.end_time - row.start_time).total_seconds()
            sessions.append({
                "session_id": row.session_id,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "duration_seconds": duration,
                "event_count": row.event_count
            })
        
        return sessions
    
    # GenerationAnalytics operations
    
    async def record_generation_start(
        self,
        user_id: UUID,
        generation_id: UUID,
        content_type: str
    ) -> None:
        """Record generation start event."""
        await self.record_user_activity(
            user_id=user_id,
            event_type=EventType.GENERATION_START.value,
            event_name=f"Generation started: {content_type}",
            session_id="system",
            properties={
                "generation_id": str(generation_id),
                "content_type": content_type
            }
        )
    
    async def record_generation_complete(
        self,
        generation_id: UUID,
        duration_seconds: float,
        tokens_used: int,
        quality_score: float
    ) -> GenerationAnalytics:
        """Record generation completion analytics."""
        analytics = GenerationAnalytics(
            generation_id=generation_id,
            total_processing_time_seconds=duration_seconds,
            llm_tokens_used=tokens_used,
            quality_scores={"overall": quality_score}
        )
        
        # Calculate estimated cost (example rates)
        analytics.llm_cost_usd = tokens_used * 0.00002  # $0.02 per 1K tokens
        analytics.compute_cost_usd = duration_seconds * 0.0001  # $0.36 per hour
        analytics.total_cost_usd = analytics.llm_cost_usd + analytics.compute_cost_usd
        
        self.db_session.add(analytics)
        await self.db_session.flush()
        return analytics
    
    async def get_generation_analytics(
        self,
        generation_id: UUID
    ) -> Optional[GenerationAnalytics]:
        """Get analytics for a specific generation."""
        result = await self.db_session.execute(
            select(GenerationAnalytics).where(
                GenerationAnalytics.generation_id == generation_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_generation_analytics(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[GenerationAnalytics]:
        """Get generation analytics for a user."""
        from ..models.content import ContentGeneration
        
        query = select(GenerationAnalytics).join(
            ContentGeneration,
            GenerationAnalytics.generation_id == ContentGeneration.id
        ).where(ContentGeneration.user_id == user_id)
        
        if start_date:
            query = query.where(ContentGeneration.created_at >= start_date)
        if end_date:
            query = query.where(ContentGeneration.created_at <= end_date)
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    # DailyMetrics operations
    
    async def get_or_create_daily_metrics(
        self,
        metric_date: date
    ) -> DailyMetrics:
        """Get or create daily metrics for a date."""
        result = await self.db_session.execute(
            select(DailyMetrics).where(DailyMetrics.metric_date == metric_date)
        )
        metrics = result.scalar_one_or_none()
        
        if not metrics:
            metrics = DailyMetrics(metric_date=metric_date)
            self.db_session.add(metrics)
            await self.db_session.flush()
        
        return metrics
    
    async def update_daily_metrics(
        self,
        metric_date: date,
        updates: Dict[str, Any]
    ) -> None:
        """Update daily metrics."""
        await self.db_session.execute(
            update(DailyMetrics)
            .where(DailyMetrics.metric_date == metric_date)
            .values(**updates)
        )
    
    async def get_metrics_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[DailyMetrics]:
        """Get daily metrics for a date range."""
        result = await self.db_session.execute(
            select(DailyMetrics)
            .where(
                and_(
                    DailyMetrics.metric_date >= start_date,
                    DailyMetrics.metric_date <= end_date
                )
            )
            .order_by(DailyMetrics.metric_date)
        )
        return result.scalars().all()
    
    # FeatureUsage operations
    
    async def record_feature_usage(
        self,
        user_id: UUID,
        feature_name: str,
        feature_category: str,
        success: bool = True,
        duration_ms: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> FeatureUsage:
        """Record feature usage."""
        usage = FeatureUsage(
            user_id=user_id,
            feature_name=feature_name,
            feature_category=feature_category,
            success=success,
            duration_ms=duration_ms,
            context=context or {}
        )
        
        self.db_session.add(usage)
        await self.db_session.flush()
        return usage
    
    async def get_popular_features(
        self,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most popular features."""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db_session.execute(
            select(
                FeatureUsage.feature_name,
                FeatureUsage.feature_category,
                func.count(FeatureUsage.id).label("usage_count"),
                func.count(func.distinct(FeatureUsage.user_id)).label("unique_users"),
                func.avg(FeatureUsage.duration_ms).label("avg_duration_ms")
            )
            .where(FeatureUsage.used_at >= since_date)
            .group_by(FeatureUsage.feature_name, FeatureUsage.feature_category)
            .order_by(func.count(FeatureUsage.id).desc())
            .limit(limit)
        )
        
        features = []
        for row in result:
            features.append({
                "feature_name": row.feature_name,
                "feature_category": row.feature_category,
                "usage_count": row.usage_count,
                "unique_users": row.unique_users,
                "avg_duration_ms": float(row.avg_duration_ms) if row.avg_duration_ms else 0
            })
        
        return features
    
    # PerformanceMetrics operations
    
    async def record_performance_metric(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int,
        user_id: Optional[UUID] = None,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None
    ) -> PerformanceMetrics:
        """Record API performance metric."""
        metric = PerformanceMetrics(
            endpoint=endpoint,
            method=method,
            response_time_ms=response_time_ms,
            status_code=status_code,
            user_id=user_id,
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes
        )
        
        self.db_session.add(metric)
        await self.db_session.flush()
        return metric
    
    async def get_endpoint_performance(
        self,
        endpoint: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance statistics for an endpoint."""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.db_session.execute(
            select(
                func.count(PerformanceMetrics.id).label("request_count"),
                func.avg(PerformanceMetrics.response_time_ms).label("avg_response_time"),
                func.min(PerformanceMetrics.response_time_ms).label("min_response_time"),
                func.max(PerformanceMetrics.response_time_ms).label("max_response_time"),
                func.percentile_cont(0.5).within_group(PerformanceMetrics.response_time_ms).label("p50"),
                func.percentile_cont(0.95).within_group(PerformanceMetrics.response_time_ms).label("p95"),
                func.percentile_cont(0.99).within_group(PerformanceMetrics.response_time_ms).label("p99")
            )
            .where(
                and_(
                    PerformanceMetrics.endpoint == endpoint,
                    PerformanceMetrics.measured_at >= since
                )
            )
        )
        
        row = result.one()
        
        # Get error rate
        error_count = await self.db_session.execute(
            select(func.count(PerformanceMetrics.id))
            .where(
                and_(
                    PerformanceMetrics.endpoint == endpoint,
                    PerformanceMetrics.measured_at >= since,
                    PerformanceMetrics.status_code >= 400
                )
            )
        )
        
        return {
            "endpoint": endpoint,
            "period_hours": hours,
            "request_count": row.request_count or 0,
            "error_count": error_count.scalar() or 0,
            "error_rate": (error_count.scalar() or 0) / (row.request_count or 1),
            "avg_response_time_ms": float(row.avg_response_time) if row.avg_response_time else 0,
            "min_response_time_ms": float(row.min_response_time) if row.min_response_time else 0,
            "max_response_time_ms": float(row.max_response_time) if row.max_response_time else 0,
            "p50_response_time_ms": float(row.p50) if row.p50 else 0,
            "p95_response_time_ms": float(row.p95) if row.p95 else 0,
            "p99_response_time_ms": float(row.p99) if row.p99 else 0
        }
    
    # BusinessMetric operations
    
    async def record_business_metric(
        self,
        metric_type: str,
        metric_name: str,
        value: float,
        unit: Optional[str] = None,
        dimensions: Optional[Dict[str, str]] = None
    ) -> BusinessMetric:
        """Record a business metric."""
        metric = BusinessMetric(
            metric_type=MetricType(metric_type),
            metric_name=metric_name,
            value=value,
            unit=unit,
            dimensions=dimensions or {}
        )
        
        self.db_session.add(metric)
        await self.db_session.flush()
        return metric
    
    async def get_business_metrics(
        self,
        metric_type: MetricType,
        metric_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[BusinessMetric]:
        """Get business metrics."""
        query = select(BusinessMetric).where(
            BusinessMetric.metric_type == metric_type
        )
        
        if metric_name:
            query = query.where(BusinessMetric.metric_name == metric_name)
        if start_date:
            query = query.where(BusinessMetric.recorded_at >= start_date)
        if end_date:
            query = query.where(BusinessMetric.recorded_at <= end_date)
        
        query = query.order_by(BusinessMetric.recorded_at.desc())
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    # UserSegment operations
    
    async def create_user_segment(
        self,
        name: str,
        display_name: str,
        segment_type: str,
        criteria: Dict[str, Any],
        description: Optional[str] = None
    ) -> UserSegment:
        """Create a user segment."""
        segment = UserSegment(
            name=name,
            display_name=display_name,
            segment_type=segment_type,
            criteria=criteria,
            description=description
        )
        
        self.db_session.add(segment)
        await self.db_session.flush()
        return segment
    
    async def add_user_to_segment(
        self,
        user_id: UUID,
        segment_id: UUID,
        confidence_score: float = 1.0
    ) -> UserSegmentMembership:
        """Add user to a segment."""
        membership = UserSegmentMembership(
            user_id=user_id,
            segment_id=segment_id,
            confidence_score=confidence_score
        )
        
        self.db_session.add(membership)
        await self.db_session.flush()
        return membership
    
    async def get_user_segments(
        self,
        user_id: UUID
    ) -> List[UserSegment]:
        """Get segments a user belongs to."""
        result = await self.db_session.execute(
            select(UserSegment)
            .join(UserSegmentMembership)
            .where(UserSegmentMembership.user_id == user_id)
        )
        return result.scalars().all()
    
    # Aggregate analytics
    
    async def get_platform_overview(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get platform overview statistics."""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Active users
        active_users = await self.db_session.execute(
            select(func.count(func.distinct(UserActivity.user_id)))
            .where(UserActivity.created_at >= since_date)
        )
        
        # Total generations
        from ..models.content import ContentGeneration
        total_generations = await self.db_session.execute(
            select(func.count(ContentGeneration.id))
            .where(ContentGeneration.created_at >= since_date)
        )
        
        # Average quality score
        from ..models.quality import QualityCheck
        avg_quality = await self.db_session.execute(
            select(func.avg(QualityCheck.overall_score))
            .where(
                and_(
                    QualityCheck.created_at >= since_date,
                    QualityCheck.overall_score.isnot(None)
                )
            )
        )
        
        return {
            "period_days": days,
            "active_users": active_users.scalar() or 0,
            "total_generations": total_generations.scalar() or 0,
            "avg_quality_score": float(avg_quality.scalar() or 0)
        }
    
    async def record_user_feedback(
        self,
        user_id: UUID,
        generation_id: UUID,
        rating: int
    ) -> None:
        """Record user feedback as an activity."""
        await self.record_user_activity(
            user_id=user_id,
            event_type=EventType.FEATURE_USE.value,
            event_name="User feedback submitted",
            session_id="system",
            properties={
                "generation_id": str(generation_id),
                "rating": rating
            }
        )
