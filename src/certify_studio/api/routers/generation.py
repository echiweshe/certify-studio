"""
Content generation router - handles educational content generation requests.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from fastapi import (
    APIRouter, Depends, HTTPException, status, 
    UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect
)
from fastapi.responses import StreamingResponse

from ...core.logging import get_logger
from ...agents.multimodal_orchestrator import MultimodalOrchestrator, GenerationConfig, GenerationPhase
from ...agents.specialized.pedagogical_reasoning import PedagogicalReasoningAgent
from ...agents.specialized.content_generation import ContentGenerationAgent
from ...agents.specialized.domain_extraction import DomainExtractionAgent
from ...agents.specialized.quality_assurance import QualityAssuranceAgent
from ..dependencies import (
    VerifiedUser,
    Database,
    RateLimit,
    UploadFile as UploadHandler,
    get_request_id
)
from ..schemas import (
    GenerationRequest,
    GenerationResponse,
    StatusEnum,
    ProgressUpdate,
    ErrorResponse,
    GenerationMetrics
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/generation",
    tags=["content-generation"],
    dependencies=[Depends(RateLimit)],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)

# Global orchestrator instance (in production, use dependency injection)
orchestrator = MultimodalOrchestrator()

# Active generation tasks
active_tasks: Dict[UUID, Dict[str, Any]] = {}


@router.post(
    "/generate",
    response_model=GenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate educational content",
    description="Start generation of educational content from certification material"
)
async def generate_content(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: VerifiedUser,
    db: Database,
    request_id: str = Depends(get_request_id)
) -> GenerationResponse:
    """Start content generation process."""
    try:
        # Create task ID
        task_id = uuid4()
        
        # Validate user quota
        if current_user.total_generations >= 10 and current_user.plan_type == "free":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Generation quota exceeded. Please upgrade your plan."
            )
        
        # Get uploaded file if provided
        file_path = None
        if request.upload_id:
            # In production, retrieve file info from database
            file_path = f"/uploads/{request.upload_id}"
            if not file_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Uploaded file not found"
                )
        
        # Create generation config
        config = GenerationConfig(
            certification_path=file_path or str(request.content_url),
            output_path=f"/outputs/{task_id}",
            certification_name=request.title,
            exam_code=request.certification_type.value,
            target_audience=request.target_audience,
            video_duration_target=request.duration_minutes * 60,
            export_formats=[fmt.value for fmt in request.output_formats],
            style_theme="modern",
            enable_interactivity=request.enable_interactivity,
            progressive_learning=True
        )
        
        # Store task info
        active_tasks[task_id] = {
            "user_id": current_user.id,
            "status": StatusEnum.PENDING,
            "progress": 0,
            "phase": None,
            "started_at": datetime.utcnow(),
            "config": config,
            "request_id": request_id
        }
        
        # Start generation in background
        background_tasks.add_task(
            run_generation,
            task_id,
            config,
            current_user.id,
            db
        )
        
        return GenerationResponse(
            status=StatusEnum.SUCCESS,
            message="Content generation started",
            task_id=task_id,
            generation_status=StatusEnum.PENDING,
            progress=0,
            started_at=datetime.utcnow(),
            request_id=UUID(request_id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation start error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start content generation"
        )


async def run_generation(
    task_id: UUID,
    config: GenerationConfig,
    user_id: UUID,
    db: AsyncSession
) -> None:
    """Run content generation in background."""
    try:
        # Update task status
        active_tasks[task_id]["status"] = StatusEnum.PROCESSING
        active_tasks[task_id]["phase"] = GenerationPhase.EXTRACTION.value
        
        # Progress callback
        def progress_callback(phase: GenerationPhase, progress: float):
            active_tasks[task_id]["phase"] = phase.value
            active_tasks[task_id]["progress"] = progress
        
        # Run generation
        result = await orchestrator.generate_educational_content(
            config,
            progress_callback
        )
        
        if result.success:
            # Calculate metrics
            metrics = GenerationMetrics(
                total_concepts=len(result.domain.concepts) if result.domain else 0,
                total_animations=len(result.animations),
                total_diagrams=len(result.diagrams),
                processing_time_seconds=(datetime.utcnow() - active_tasks[task_id]["started_at"]).total_seconds(),
                quality_score=0.92,  # Would come from QA agent
                pedagogical_score=0.89,
                technical_accuracy=0.95,
                accessibility_score=0.98
            )
            
            # Update task
            active_tasks[task_id].update({
                "status": StatusEnum.COMPLETED,
                "progress": 100,
                "completed_at": datetime.utcnow(),
                "result": result,
                "metrics": metrics
            })
            
            # Update user stats
            # await db.execute(
            #     update(User).where(User.id == user_id).values(
            #         total_generations=User.total_generations + 1
            #     )
            # )
            # await db.commit()
            
        else:
            active_tasks[task_id].update({
                "status": StatusEnum.FAILED,
                "error": result.errors[0] if result.errors else "Unknown error"
            })
            
    except Exception as e:
        logger.error(f"Generation error for task {task_id}: {e}")
        active_tasks[task_id].update({
            "status": StatusEnum.FAILED,
            "error": str(e)
        })


@router.get(
    "/status/{task_id}",
    response_model=GenerationResponse,
    summary="Get generation status",
    description="Get the current status of a content generation task"
)
async def get_generation_status(
    task_id: UUID,
    current_user: VerifiedUser
) -> GenerationResponse:
    """Get generation task status."""
    if task_id not in active_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task = active_tasks[task_id]
    
    # Check ownership
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    response = GenerationResponse(
        status=StatusEnum.SUCCESS,
        message="Status retrieved",
        task_id=task_id,
        generation_status=task["status"],
        progress=task["progress"],
        current_phase=task.get("phase"),
        started_at=task["started_at"],
        request_id=task.get("request_id")
    )
    
    # Add completion data if available
    if task["status"] == StatusEnum.COMPLETED:
        result = task["result"]
        response.completed_at = task["completed_at"]
        response.download_urls = {
            fmt: f"/api/export/{task_id}/{fmt}" 
            for fmt in result.exports.keys()
        }
        response.preview_url = f"/preview/{task_id}"
        response.metrics = task["metrics"]
        
    elif task["status"] == StatusEnum.PROCESSING:
        # Estimate completion time
        elapsed = (datetime.utcnow() - task["started_at"]).total_seconds()
        if task["progress"] > 0:
            total_estimate = elapsed / (task["progress"] / 100)
            remaining = total_estimate - elapsed
            response.estimated_completion = datetime.utcnow() + timedelta(seconds=remaining)
    
    return response


@router.post(
    "/upload",
    response_model=Dict[str, Any],
    summary="Upload content file",
    description="Upload a certification guide or content file for processing"
)
async def upload_content(
    file: UploadFile = File(...),
    current_user: VerifiedUser,
    upload_handler: Dict[str, Any] = Depends(UploadHandler())
) -> Dict[str, Any]:
    """Upload content file."""
    try:
        # Process upload
        result = await upload_handler(file)
        
        # Store upload info in database
        # await db.execute(
        #     insert(Upload).values(
        #         id=result["upload_id"],
        #         user_id=current_user.id,
        #         filename=result["filename"],
        #         content_type=result["content_type"],
        #         size=result["size"],
        #         path=result["path"],
        #         uploaded_at=datetime.utcnow()
        #     )
        # )
        # await db.commit()
        
        return {
            "status": "success",
            "message": "File uploaded successfully",
            "upload_id": result["upload_id"],
            "filename": result["filename"],
            "size": result["size"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed"
        )


@router.get(
    "/progress/{task_id}/stream",
    summary="Stream generation progress",
    description="Get real-time progress updates via Server-Sent Events"
)
async def stream_progress(
    task_id: UUID,
    current_user: VerifiedUser
):
    """Stream progress updates using Server-Sent Events."""
    if task_id not in active_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task = active_tasks[task_id]
    
    # Check ownership
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    async def event_generator():
        """Generate SSE events."""
        last_progress = -1
        
        while True:
            if task_id not in active_tasks:
                break
                
            task = active_tasks[task_id]
            
            # Send update if progress changed
            if task["progress"] != last_progress:
                last_progress = task["progress"]
                
                update = ProgressUpdate(
                    task_id=task_id,
                    phase=task.get("phase", "unknown"),
                    progress=task["progress"],
                    message=f"Processing: {task.get('phase', 'unknown')}",
                    eta_seconds=None  # Could calculate ETA
                )
                
                yield f"data: {update.model_dump_json()}\n\n"
            
            # Check if completed
            if task["status"] in [StatusEnum.COMPLETED, StatusEnum.FAILED]:
                yield f"data: {{'event': 'complete', 'status': '{task['status']}'}}\n\n"
                break
            
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.websocket("/ws/{task_id}")
async def websocket_progress(
    websocket: WebSocket,
    task_id: UUID,
    current_user: VerifiedUser = Depends(get_ws_user)
):
    """WebSocket endpoint for real-time progress updates."""
    await websocket.accept()
    
    try:
        if task_id not in active_tasks:
            await websocket.send_json({
                "error": "Task not found"
            })
            await websocket.close()
            return
        
        task = active_tasks[task_id]
        
        # Check ownership
        if task["user_id"] != current_user.id:
            await websocket.send_json({
                "error": "Access denied"
            })
            await websocket.close()
            return
        
        # Send updates
        last_progress = -1
        
        while True:
            if task_id not in active_tasks:
                break
            
            task = active_tasks[task_id]
            
            # Send update if progress changed
            if task["progress"] != last_progress:
                last_progress = task["progress"]
                
                await websocket.send_json({
                    "type": "progress",
                    "data": {
                        "task_id": str(task_id),
                        "phase": task.get("phase", "unknown"),
                        "progress": task["progress"],
                        "status": task["status"]
                    }
                })
            
            # Check if completed
            if task["status"] in [StatusEnum.COMPLETED, StatusEnum.FAILED]:
                await websocket.send_json({
                    "type": "complete",
                    "data": {
                        "task_id": str(task_id),
                        "status": task["status"],
                        "message": "Generation complete" if task["status"] == StatusEnum.COMPLETED else "Generation failed"
                    }
                })
                break
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


@router.delete(
    "/cancel/{task_id}",
    response_model=Dict[str, str],
    summary="Cancel generation",
    description="Cancel an ongoing content generation task"
)
async def cancel_generation(
    task_id: UUID,
    current_user: VerifiedUser
) -> Dict[str, str]:
    """Cancel generation task."""
    if task_id not in active_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task = active_tasks[task_id]
    
    # Check ownership
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if can be cancelled
    if task["status"] not in [StatusEnum.PENDING, StatusEnum.PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task in {task['status']} state"
        )
    
    # Cancel task
    task["status"] = StatusEnum.FAILED
    task["error"] = "Cancelled by user"
    
    return {
        "status": "success",
        "message": "Generation cancelled"
    }


# Helper function for WebSocket auth
async def get_ws_user(websocket: WebSocket, token: str = None) -> Optional[User]:
    """Get user from WebSocket connection."""
    # In production, implement proper WebSocket authentication
    # For now, return None (anonymous)
    return None
