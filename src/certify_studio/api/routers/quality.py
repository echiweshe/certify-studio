"""
Quality assurance router - handles content quality checking and monitoring.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from fastapi import (
    APIRouter, Depends, HTTPException, status,
    BackgroundTasks, Query, WebSocket, WebSocketDisconnect
)

from ...core.logging import get_logger
from ...agents.specialized.quality_assurance import QualityAssuranceAgent
from ...agents.specialized.quality_assurance.models import (
    QARequest,
    QAReport,
    FeedbackData,
    ContinuousMonitoringConfig
)
from sqlalchemy.ext.asyncio import AsyncSession
from ..dependencies import (
    get_current_verified_user,
    AsyncSession,
    check_rate_limit,
    get_request_id
)
from ..schemas import (
    QualityCheckRequest,
    QualityCheckResponse,
    FeedbackSubmission,
    StatusEnum,
    ErrorResponse,
    BaseResponse
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/quality",
    tags=["quality-assurance"],
    dependencies=[Depends(check_rate_limit)],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)

# Global QA agent (in production, use dependency injection)
qa_agent = QualityAssuranceAgent()

# Active QA tasks
qa_tasks: Dict[UUID, Dict[str, Any]] = {}

# Monitoring tasks
monitoring_tasks: Dict[UUID, Dict[str, Any]] = {}


@router.post(
    "/check",
    response_model=QualityCheckResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Check content quality",
    description="Perform comprehensive quality assurance on generated content"
)
async def check_quality(
    request: QualityCheckRequest,
    background_tasks: BackgroundTasks,
    current_user: get_current_verified_user,
    db: AsyncSession,
    request_id: str = Depends(get_request_id)
) -> QualityCheckResponse:
    """Start quality check on content."""
    try:
        # Initialize agent if needed
        if not qa_agent._initialized:
            await qa_agent.initialize()
        
        # Verify content ownership
        # content = await db.get(Content, request.content_id)
        # if not content or content.user_id != current_user.id:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Content not found"
        #     )
        
        # For demo, create mock content
        content = {
            "id": request.content_id,
            "title": "AWS Solutions Architect Course",
            "type": "video",
            "data": {}  # Would contain actual content data
        }
        
        # Create QA task
        task_id = uuid4()
        qa_request = QARequest(
            content_id=str(request.content_id),
            content_type="educational_video",
            content_data=content["data"],
            check_technical_accuracy=request.check_technical_accuracy,
            check_pedagogical_effectiveness=request.check_pedagogical_effectiveness,
            check_accessibility=request.check_accessibility,
            check_certification_alignment=request.check_certification_alignment,
            certification_name="AWS-SAA-C03"  # Would come from content metadata
        )
        
        # Store task info
        qa_tasks[task_id] = {
            "user_id": current_user.id,
            "content_id": request.content_id,
            "status": StatusEnum.PROCESSING,
            "started_at": datetime.utcnow(),
            "request": qa_request
        }
        
        # Start QA in background
        background_tasks.add_task(
            run_quality_check,
            task_id,
            qa_request,
            current_user.id,
            db
        )
        
        # Enable continuous monitoring if requested
        if request.enable_continuous_monitoring:
            monitor_config = ContinuousMonitoringConfig(
                content_id=str(request.content_id),
                check_interval_minutes=request.monitoring_interval_minutes,
                quality_thresholds={
                    "technical_accuracy": 0.85,
                    "pedagogical_effectiveness": 0.80,
                    "accessibility_score": 0.90,
                    "certification_alignment": 0.85
                },
                alert_on_degradation=True
            )
            
            monitoring_tasks[request.content_id] = {
                "config": monitor_config,
                "active": True,
                "last_check": datetime.utcnow()
            }
            
            background_tasks.add_task(
                start_continuous_monitoring,
                request.content_id,
                monitor_config,
                current_user.id
            )
        
        return QualityCheckResponse(
            status=StatusEnum.SUCCESS,
            message="Quality check started",
            request_id=UUID(request_id),
            check_id=task_id,
            content_id=request.content_id,
            overall_quality=0.0,
            passed=False,
            technical_accuracy=0.0,
            pedagogical_effectiveness=0.0,
            accessibility_compliance=0.0,
            certification_alignment=0.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quality check start error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start quality check"
        )


async def run_quality_check(
    task_id: UUID,
    request: QARequest,
    user_id: UUID,
    db: AsyncSession
) -> None:
    """Run quality check in background."""
    try:
        # Perform QA
        report = await qa_agent.perform_qa(request)
        
        # Calculate overall quality
        scores = [
            report.technical_accuracy_score,
            report.pedagogical_effectiveness_score,
            report.accessibility_score,
            report.certification_alignment_score
        ]
        overall_quality = sum(scores) / len(scores)
        
        # Update task
        qa_tasks[task_id].update({
            "status": StatusEnum.COMPLETED,
            "completed_at": datetime.utcnow(),
            "report": report,
            "overall_quality": overall_quality,
            "passed": overall_quality >= 0.85  # 85% threshold
        })
        
        # Update content quality score in database
        # await db.execute(
        #     update(Content).where(Content.id == request.content_id).values(
        #         quality_score=overall_quality,
        #         last_qa_check=datetime.utcnow()
        #     )
        # )
        # await db.commit()
        
    except Exception as e:
        logger.error(f"Quality check error for task {task_id}: {e}")
        qa_tasks[task_id].update({
            "status": StatusEnum.FAILED,
            "error": str(e)
        })


@router.get(
    "/check/{task_id}",
    response_model=QualityCheckResponse,
    summary="Get quality check results",
    description="Get the results of a quality check task"
)
async def get_quality_results(
    task_id: UUID,
    current_user: get_current_verified_user,
    request_id: str = Depends(get_request_id)
) -> QualityCheckResponse:
    """Get quality check results."""
    if task_id not in qa_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quality check task not found"
        )
    
    task = qa_tasks[task_id]
    
    # Check ownership
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build response
    response = QualityCheckResponse(
        status=StatusEnum.SUCCESS,
        message="Quality check results retrieved",
        request_id=UUID(request_id),
        check_id=task_id,
        content_id=task["content_id"],
        overall_quality=task.get("overall_quality", 0.0),
        passed=task.get("passed", False),
        technical_accuracy=0.0,
        pedagogical_effectiveness=0.0,
        accessibility_compliance=0.0,
        certification_alignment=0.0
    )
    
    if task["status"] == StatusEnum.COMPLETED:
        report = task["report"]
        
        response.technical_accuracy = report.technical_accuracy_score
        response.pedagogical_effectiveness = report.pedagogical_effectiveness_score
        response.accessibility_compliance = report.accessibility_score
        response.certification_alignment = report.certification_alignment_score
        
        # Add issues and recommendations
        response.issues = [
            {
                "type": issue.type,
                "severity": issue.severity,
                "description": issue.description,
                "location": issue.location,
                "suggestion": issue.suggestion
            }
            for issue in report.issues
        ]
        
        response.recommendations = report.recommendations
        
        # Add benchmark comparison if available
        if hasattr(report, 'benchmark_comparison'):
            response.benchmark_comparison = {
                "industry_average": report.benchmark_comparison.industry_average,
                "percentile": report.benchmark_comparison.percentile,
                "comparison": report.benchmark_comparison.comparison
            }
    
    elif task["status"] == StatusEnum.PROCESSING:
        response.message = "Quality check in progress"
    
    else:  # Failed
        response.message = f"Quality check failed: {task.get('error', 'Unknown error')}"
    
    return response


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit feedback",
    description="Submit user feedback on content quality"
)
async def submit_feedback(
    feedback: FeedbackSubmission,
    current_user: get_current_verified_user,
    db: AsyncSession,
    request_id: str = Depends(get_request_id)
) -> FeedbackResponse:
    """Submit feedback on content."""
    try:
        # Verify content ownership
        # content = await db.get(Content, feedback.content_id)
        # if not content:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Content not found"
        #     )
        
        # Create feedback data
        feedback_data = FeedbackData(
            content_id=str(feedback.content_id),
            user_id=str(current_user.id),
            overall_rating=feedback.overall_rating,
            technical_accuracy_rating=feedback.technical_accuracy_rating,
            clarity_rating=feedback.clarity_rating,
            engagement_rating=feedback.engagement_rating,
            liked_sections=feedback.liked_sections or [],
            improvement_areas=feedback.improvement_areas or [],
            comments=feedback.comments,
            user_experience_level=feedback.user_experience_level,
            completion_percentage=feedback.completion_percentage,
            timestamp=datetime.utcnow()
        )
        
        # Analyze feedback
        analysis = await qa_agent.feedback_analyzer.analyze_feedback(
            [feedback_data],
            str(feedback.content_id)
        )
        
        # Store feedback in database
        feedback_id = uuid4()
        # await db.execute(
        #     insert(Feedback).values(
        #         id=feedback_id,
        #         content_id=feedback.content_id,
        #         user_id=current_user.id,
        #         overall_rating=feedback.overall_rating,
        #         data=feedback.dict(),
        #         created_at=datetime.utcnow()
        #     )
        # )
        # await db.commit()
        
        # Check for similar feedback
        similar_count = 0  # Would query database for similar feedback
        
        return FeedbackResponse(
            status=StatusEnum.SUCCESS,
            message="Thank you for your feedback!",
            request_id=UUID(request_id),
            feedback_id=feedback_id,
            content_id=feedback.content_id,
            thank_you_message="Your feedback helps us improve content quality for everyone.",
            will_impact_future_generations=True,
            similar_feedback_count=similar_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


@router.get(
    "/benchmarks/{certification_type}",
    response_model=Dict[str, Any],
    summary="Get quality benchmarks",
    description="Get industry quality benchmarks for certification type"
)
async def get_benchmarks(
    certification_type: str,
    current_user: get_current_verified_user = Depends()
) -> Dict[str, Any]:
    """Get quality benchmarks for certification type."""
    try:
        benchmarks = await qa_agent.benchmark_manager.get_benchmark(certification_type)
        
        if not benchmarks:
            # Return default benchmarks
            benchmarks = {
                "certification_type": certification_type,
                "technical_accuracy": {
                    "minimum": 0.85,
                    "target": 0.95,
                    "industry_average": 0.90
                },
                "pedagogical_effectiveness": {
                    "minimum": 0.80,
                    "target": 0.90,
                    "industry_average": 0.85
                },
                "accessibility_compliance": {
                    "minimum": 0.90,
                    "target": 1.00,
                    "industry_average": 0.85
                },
                "certification_alignment": {
                    "minimum": 0.85,
                    "target": 0.95,
                    "industry_average": 0.88
                }
            }
        
        return benchmarks
        
    except Exception as e:
        logger.error(f"Benchmark retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get benchmarks"
        )


@router.get(
    "/monitor/{content_id}",
    response_model=Dict[str, Any],
    summary="Get monitoring status",
    description="Get continuous monitoring status for content"
)
async def get_monitoring_status(
    content_id: UUID,
    current_user: get_current_verified_user = Depends()
) -> Dict[str, Any]:
    """Get monitoring status for content."""
    if content_id not in monitoring_tasks:
        return {
            "content_id": str(content_id),
            "monitoring_active": False,
            "message": "No active monitoring for this content"
        }
    
    monitor = monitoring_tasks[content_id]
    
    return {
        "content_id": str(content_id),
        "monitoring_active": monitor["active"],
        "check_interval_minutes": monitor["config"].check_interval_minutes,
        "last_check": monitor["last_check"],
        "next_check": monitor["last_check"] + timedelta(
            minutes=monitor["config"].check_interval_minutes
        ),
        "quality_thresholds": monitor["config"].quality_thresholds,
        "alert_on_degradation": monitor["config"].alert_on_degradation
    }


@router.post(
    "/monitor/{content_id}/stop",
    response_model=BaseResponse,
    summary="Stop monitoring",
    description="Stop continuous monitoring for content"
)
async def stop_monitoring(
    content_id: UUID,
    current_user: get_current_verified_user,
    request_id: str = Depends(get_request_id)
) -> BaseResponse:
    """Stop continuous monitoring."""
    if content_id not in monitoring_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active monitoring for this content"
        )
    
    # Stop monitoring
    monitoring_tasks[content_id]["active"] = False
    
    return BaseResponse(
        status=StatusEnum.SUCCESS,
        message="Monitoring stopped successfully",
        request_id=UUID(request_id)
    )


@router.websocket("/monitor/{content_id}/ws")
async def websocket_monitoring(
    websocket: WebSocket,
    content_id: UUID,
    current_user: get_current_verified_user = Depends(get_ws_user)
):
    """WebSocket endpoint for real-time quality monitoring."""
    await websocket.accept()
    
    try:
        if content_id not in monitoring_tasks:
            await websocket.send_json({
                "error": "No active monitoring for this content"
            })
            await websocket.close()
            return
        
        # Send monitoring updates
        while monitoring_tasks[content_id]["active"]:
            monitor = monitoring_tasks[content_id]
            
            # Get latest quality metrics
            metrics = await qa_agent.continuous_monitor.get_current_metrics(
                str(content_id)
            )
            
            await websocket.send_json({
                "type": "quality_update",
                "data": {
                    "content_id": str(content_id),
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": {
                        "technical_accuracy": metrics.get("technical_accuracy", 0),
                        "pedagogical_effectiveness": metrics.get("pedagogical_effectiveness", 0),
                        "accessibility_compliance": metrics.get("accessibility_compliance", 0),
                        "certification_alignment": metrics.get("certification_alignment", 0)
                    },
                    "overall_quality": metrics.get("overall_quality", 0),
                    "status": "healthy" if metrics.get("overall_quality", 0) >= 0.85 else "degraded"
                }
            })
            
            await asyncio.sleep(30)  # Send updates every 30 seconds
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket monitoring error: {e}")
        await websocket.close()


async def start_continuous_monitoring(
    content_id: UUID,
    config: ContinuousMonitoringConfig,
    user_id: UUID
) -> None:
    """Start continuous monitoring task."""
    try:
        while monitoring_tasks.get(content_id, {}).get("active", False):
            # Run quality check
            await qa_agent.continuous_monitor.start_monitoring(config)
            
            # Update last check time
            monitoring_tasks[content_id]["last_check"] = datetime.utcnow()
            
            # Wait for next check
            await asyncio.sleep(config.check_interval_minutes * 60)
            
    except Exception as e:
        logger.error(f"Continuous monitoring error: {e}")
        if content_id in monitoring_tasks:
            monitoring_tasks[content_id]["active"] = False


# Helper function for WebSocket auth
async def get_ws_user(websocket: WebSocket, token: str = None) -> Optional[User]:
    """Get user from WebSocket connection."""
    # In production, implement proper WebSocket authentication
    return None
