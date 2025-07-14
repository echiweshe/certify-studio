"""
Export router - handles content export in various formats.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pathlib import Path

from fastapi import (
    APIRouter, Depends, HTTPException, status,
    BackgroundTasks, Response
)
from fastapi.responses import FileResponse, StreamingResponse

from ...core.logging import get_logger
from ...agents.specialized.content_generation import ContentGenerationAgent
from ...agents.specialized.content_generation.models import (
    ExportRequest as ExportRequestModel,
    ExportFormat,
    ExportOptions as ExportOptionsModel
)
from sqlalchemy.ext.asyncio import AsyncSession
from ..dependencies import (
    get_current_verified_user,
    AsyncSession,
    check_rate_limit,
    get_request_id
)
from ..schemas import (
    ExportRequest,
    ExportResponse,
    StatusEnum,
    ErrorResponse,
    OutputFormat
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/export",
    tags=["export"],
    dependencies=[Depends(check_rate_limit)],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)

# Export tasks
export_tasks: Dict[UUID, Dict[str, Any]] = {}

# Temporary storage for exports (in production, use cloud storage)
EXPORT_DIR = Path("/tmp/certify_studio/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "/",
    response_model=ExportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Export content",
    description="Export generated content in specified format"
)
async def export_content(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: get_current_verified_user,
    db: AsyncSession,
    request_id: str = Depends(get_request_id)
) -> ExportResponse:
    """Start content export."""
    try:
        # Verify content ownership
        # content = await db.get(GeneratedContent, request.content_id)
        # if not content or content.user_id != current_user.id:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Content not found"
        #     )
        
        # For demo, create mock content
        content = {
            "id": request.content_id,
            "title": "AWS Solutions Architect Course",
            "animations": [],  # Would contain actual animations
            "diagrams": [],    # Would contain actual diagrams
            "interactives": [] # Would contain actual interactives
        }
        
        # Map output format to export format
        format_mapping = {
            OutputFormat.VIDEO_MP4: ExportFormat.VIDEO,
            OutputFormat.VIDEO_WEBM: ExportFormat.VIDEO,
            OutputFormat.INTERACTIVE_HTML: ExportFormat.INTERACTIVE,
            OutputFormat.SCORM_PACKAGE: ExportFormat.SCORM,
            OutputFormat.PDF_DOCUMENT: ExportFormat.PDF,
            OutputFormat.POWERPOINT: ExportFormat.POWERPOINT
        }
        
        export_format = format_mapping.get(
            request.export_options.format,
            ExportFormat.VIDEO
        )
        
        # Create export task
        task_id = uuid4()
        export_request = ExportRequestModel(
            content_id=str(request.content_id),
            format=export_format,
            options=ExportOptionsModel(
                resolution=request.export_options.video_resolution,
                fps=request.export_options.video_fps,
                include_captions=request.export_options.include_captions,
                include_navigation=request.export_options.include_navigation,
                include_assessments=request.export_options.include_assessments,
                scorm_version=request.export_options.scorm_version,
                custom_branding=request.export_options.custom_branding
            )
        )
        
        # Store task info
        export_tasks[task_id] = {
            "user_id": current_user.id,
            "content_id": request.content_id,
            "format": request.export_options.format,
            "status": StatusEnum.PROCESSING,
            "started_at": datetime.utcnow(),
            "request": export_request
        }
        
        # Start export in background
        background_tasks.add_task(
            run_export,
            task_id,
            export_request,
            content,
            current_user.id,
            db
        )
        
        # Send webhook notification if provided
        if request.webhook_url:
            background_tasks.add_task(
                send_webhook_notification,
                str(request.webhook_url),
                task_id,
                "started"
            )
        
        return ExportResponse(
            status=StatusEnum.SUCCESS,
            message="Export started",
            request_id=UUID(request_id),
            export_id=task_id,
            content_id=request.content_id,
            format=request.export_options.format,
            export_status=StatusEnum.PROCESSING
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export start error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start export"
        )


async def run_export(
    task_id: UUID,
    request: ExportRequestModel,
    content: Dict[str, Any],
    user_id: UUID,
    db: AsyncSession
) -> None:
    """Run export in background."""
    try:
        # Initialize content generation agent for export functionality
        content_agent = ContentGenerationAgent()
        if not content_agent._initialized:
            await content_agent.initialize()
        
        # Perform export
        # In production, this would use the actual content data
        output_path = EXPORT_DIR / f"{task_id}.{request.format.value}"
        
        # Simulate export process
        await asyncio.sleep(5)  # Simulate processing time
        
        # Create a sample file
        with open(output_path, "wb") as f:
            if request.format == ExportFormat.VIDEO:
                f.write(b"Sample video content")
            elif request.format == ExportFormat.PDF:
                f.write(b"Sample PDF content")
            else:
                f.write(b"Sample export content")
        
        file_size = output_path.stat().st_size
        
        # Update task
        export_tasks[task_id].update({
            "status": StatusEnum.COMPLETED,
            "completed_at": datetime.utcnow(),
            "output_path": str(output_path),
            "file_size": file_size,
            "expires_at": datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
        })
        
        # Update user storage usage
        # await db.execute(
        #     update(User).where(User.id == user_id).values(
        #         total_storage_mb=User.total_storage_mb + (file_size / 1024 / 1024)
        #     )
        # )
        # await db.commit()
        
    except Exception as e:
        logger.error(f"Export error for task {task_id}: {e}")
        export_tasks[task_id].update({
            "status": StatusEnum.FAILED,
            "error": str(e)
        })


@router.get(
    "/{task_id}/status",
    response_model=ExportResponse,
    summary="Get export status",
    description="Get the status of an export task"
)
async def get_export_status(
    task_id: UUID,
    current_user: get_current_verified_user,
    request_id: str = Depends(get_request_id)
) -> ExportResponse:
    """Get export task status."""
    if task_id not in export_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export task not found"
        )
    
    task = export_tasks[task_id]
    
    # Check ownership
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build response
    response = ExportResponse(
        status=StatusEnum.SUCCESS,
        message="Export status retrieved",
        request_id=UUID(request_id),
        export_id=task_id,
        content_id=task["content_id"],
        format=task["format"],
        export_status=task["status"]
    )
    
    if task["status"] == StatusEnum.COMPLETED:
        response.download_url = f"/api/export/{task_id}/download"
        response.file_size_bytes = task["file_size"]
        response.expires_at = task["expires_at"]
        response.metadata = {
            "duration": (task["completed_at"] - task["started_at"]).total_seconds(),
            "format": task["format"].value
        }
    
    return response


@router.get(
    "/{task_id}/download",
    summary="Download exported content",
    description="Download the exported content file"
)
async def download_export(
    task_id: UUID,
    current_user: get_current_verified_user
):
    """Download exported content."""
    if task_id not in export_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    task = export_tasks[task_id]
    
    # Check ownership
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if completed
    if task["status"] != StatusEnum.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Export not completed"
        )
    
    # Check if expired
    if datetime.utcnow() > task["expires_at"]:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Export has expired"
        )
    
    # Get file path
    file_path = Path(task["output_path"])
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )
    
    # Determine content type
    content_type_mapping = {
        OutputFormat.VIDEO_MP4: "video/mp4",
        OutputFormat.VIDEO_WEBM: "video/webm",
        OutputFormat.INTERACTIVE_HTML: "text/html",
        OutputFormat.SCORM_PACKAGE: "application/zip",
        OutputFormat.PDF_DOCUMENT: "application/pdf",
        OutputFormat.POWERPOINT: "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    }
    
    content_type = content_type_mapping.get(
        task["format"],
        "application/octet-stream"
    )
    
    # Generate filename
    filename = f"export_{task_id}.{file_path.suffix}"
    
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache"
        }
    )


@router.get(
    "/{task_id}/stream",
    summary="Stream exported content",
    description="Stream exported video content"
)
async def stream_export(
    task_id: UUID,
    current_user: get_current_verified_user,
    range: Optional[str] = None
):
    """Stream exported video content."""
    if task_id not in export_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    task = export_tasks[task_id]
    
    # Check ownership
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if video format
    if task["format"] not in [OutputFormat.VIDEO_MP4, OutputFormat.VIDEO_WEBM]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Streaming only available for video formats"
        )
    
    # Get file path
    file_path = Path(task["output_path"])
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )
    
    file_size = file_path.stat().st_size
    
    # Handle range requests for video streaming
    if range:
        # Parse range header
        range_start = 0
        range_end = file_size - 1
        
        if range.startswith("bytes="):
            range_spec = range[6:]
            parts = range_spec.split("-")
            if parts[0]:
                range_start = int(parts[0])
            if parts[1]:
                range_end = int(parts[1])
        
        # Read requested range
        async def iterfile():
            async with aiofiles.open(file_path, "rb") as f:
                await f.seek(range_start)
                chunk_size = 8192
                current = range_start
                
                while current <= range_end:
                    remaining = range_end - current + 1
                    read_size = min(chunk_size, remaining)
                    data = await f.read(read_size)
                    if not data:
                        break
                    current += len(data)
                    yield data
        
        headers = {
            "Content-Range": f"bytes {range_start}-{range_end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(range_end - range_start + 1),
            "Content-Type": "video/mp4" if task["format"] == OutputFormat.VIDEO_MP4 else "video/webm"
        }
        
        return StreamingResponse(
            iterfile(),
            status_code=206,
            headers=headers
        )
    
    else:
        # Stream entire file
        async def iterfile():
            async with aiofiles.open(file_path, "rb") as f:
                chunk_size = 8192
                while True:
                    data = await f.read(chunk_size)
                    if not data:
                        break
                    yield data
        
        return StreamingResponse(
            iterfile(),
            media_type="video/mp4" if task["format"] == OutputFormat.VIDEO_MP4 else "video/webm",
            headers={
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes"
            }
        )


@router.delete(
    "/{task_id}",
    response_model=BaseResponse,
    summary="Delete export",
    description="Delete exported content to free up space"
)
async def delete_export(
    task_id: UUID,
    current_user: get_current_verified_user,
    db: AsyncSession,
    request_id: str = Depends(get_request_id)
) -> BaseResponse:
    """Delete exported content."""
    if task_id not in export_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    task = export_tasks[task_id]
    
    # Check ownership
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Delete file if exists
    if "output_path" in task:
        file_path = Path(task["output_path"])
        if file_path.exists():
            file_size = file_path.stat().st_size
            file_path.unlink()
            
            # Update user storage
            # await db.execute(
            #     update(User).where(User.id == current_user.id).values(
            #         total_storage_mb=User.total_storage_mb - (file_size / 1024 / 1024)
            #     )
            # )
            # await db.commit()
    
    # Remove from tasks
    del export_tasks[task_id]
    
    return BaseResponse(
        status=StatusEnum.SUCCESS,
        message="Export deleted successfully",
        request_id=UUID(request_id)
    )


@router.get(
    "/formats",
    response_model=Dict[str, Any],
    summary="Get supported export formats",
    description="Get list of supported export formats with their options"
)
async def get_export_formats() -> Dict[str, Any]:
    """Get supported export formats."""
    return {
        "formats": [
            {
                "format": OutputFormat.VIDEO_MP4.value,
                "name": "MP4 Video",
                "description": "Standard video format compatible with most devices",
                "options": {
                    "resolutions": ["1920x1080", "1280x720", "854x480"],
                    "fps": [24, 30, 60],
                    "bitrates": ["2M", "5M", "10M"]
                }
            },
            {
                "format": OutputFormat.VIDEO_WEBM.value,
                "name": "WebM Video",
                "description": "Open format optimized for web streaming",
                "options": {
                    "resolutions": ["1920x1080", "1280x720"],
                    "fps": [24, 30],
                    "bitrates": ["2M", "5M"]
                }
            },
            {
                "format": OutputFormat.INTERACTIVE_HTML.value,
                "name": "Interactive HTML",
                "description": "Web-based interactive learning experience",
                "options": {
                    "navigation": True,
                    "progress_tracking": True,
                    "assessments": True
                }
            },
            {
                "format": OutputFormat.SCORM_PACKAGE.value,
                "name": "SCORM Package",
                "description": "LMS-compatible package for tracking and reporting",
                "options": {
                    "versions": ["1.2", "2004"],
                    "mastery_score": [60, 70, 80, 90, 100]
                }
            },
            {
                "format": OutputFormat.PDF_DOCUMENT.value,
                "name": "PDF Document",
                "description": "Printable document with all content",
                "options": {
                    "layouts": ["portrait", "landscape"],
                    "include_toc": True,
                    "include_glossary": True
                }
            },
            {
                "format": OutputFormat.POWERPOINT.value,
                "name": "PowerPoint Presentation",
                "description": "Editable presentation slides",
                "options": {
                    "templates": ["modern", "classic", "minimal"],
                    "include_notes": True
                }
            }
        ]
    }


async def send_webhook_notification(
    webhook_url: str,
    task_id: UUID,
    event: str
) -> None:
    """Send webhook notification."""
    try:
        # In production, implement actual webhook sending
        logger.info(f"Would send webhook to {webhook_url} for task {task_id} event {event}")
    except Exception as e:
        logger.error(f"Webhook error: {e}")


# Import required modules
import aiofiles
from ...api.schemas import BaseResponse, FeedbackResponse
from ...agents.specialized.quality_assurance.models import User
