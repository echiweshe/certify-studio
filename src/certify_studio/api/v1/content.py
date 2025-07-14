"""
Updated Content Router with Database Integration

This module handles content generation endpoints,
now fully integrated with the database and background tasks.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from ...integration.dependencies import (
    get_db,
    get_current_user,
    PermissionChecker,
    PaginationParams
)
from ...integration.services import ContentGenerationService
from ...integration.events import get_event_bus
from ...database.models import (
    User, ContentGeneration, ContentPiece,
    ContentType, GenerationStatus, ExportFormat
)
from ...core.config import settings
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/content", tags=["content"])


# Request/Response models
class GenerationRequest(BaseModel):
    """Content generation request."""
    title: str
    content_type: ContentType
    target_audience: Optional[str] = None
    metadata: Optional[dict] = {}


class GenerationResponse(BaseModel):
    """Content generation response."""
    id: str
    title: str
    content_type: ContentType
    status: GenerationStatus
    progress: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    total_tokens_used: Optional[int]
    user_rating: Optional[float]
    
    class Config:
        from_attributes = True


class ContentPieceResponse(BaseModel):
    """Content piece response."""
    id: str
    piece_type: str
    title: str
    order_index: int
    metadata: dict
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExportRequest(BaseModel):
    """Export request."""
    format: ExportFormat


@router.post("/generate", response_model=GenerationResponse)
async def start_generation(
    title: str = Form(...),
    content_type: ContentType = Form(...),
    target_audience: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    has_permission = Depends(PermissionChecker("content", "create")),
    db = Depends(get_db)
):
    """
    Start a new content generation task.
    
    Args:
        title: Title for the generated content
        content_type: Type of content to generate
        target_audience: Target audience description
        file: Source file (PDF, etc.)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created generation task
        
    Raises:
        HTTPException: If file type not supported
    """
    # Validate file type
    allowed_types = {".pdf", ".txt", ".docx", ".md"}
    file_ext = "." + file.filename.split(".")[-1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not supported. Allowed: {allowed_types}"
        )
    
    # Check file size
    if file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    # Start generation
    service = ContentGenerationService(db)
    generation = await service.start_generation(
        user=current_user,
        source_file=file.file,
        filename=file.filename,
        title=title,
        content_type=content_type,
        target_audience=target_audience
    )
    
    logger.info(f"Started generation {generation.id} for user {current_user.username}")
    
    return GenerationResponse.from_orm(generation)


@router.get("/generations", response_model=List[GenerationResponse])
async def list_generations(
    pagination: PaginationParams = Depends(),
    status_filter: Optional[GenerationStatus] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    List user's content generations.
    
    Args:
        pagination: Pagination parameters
        status_filter: Optional status filter
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of generations
    """
    from ...database.repositories import ContentRepository
    
    repo = ContentRepository(db)
    
    # Build filters
    filters = {"user_id": current_user.id}
    if status_filter:
        filters["status"] = status_filter
    
    # Get generations
    generations = await repo.get_all(
        filters=filters,
        skip=pagination.skip,
        limit=pagination.limit,
        order_by="created_at",
        order_desc=True
    )
    
    return [GenerationResponse.from_orm(g) for g in generations]


@router.get("/generations/{generation_id}", response_model=GenerationResponse)
async def get_generation(
    generation_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get generation details.
    
    Args:
        generation_id: Generation ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Generation details
        
    Raises:
        HTTPException: If generation not found or access denied
    """
    service = ContentGenerationService(db)
    generation = await service.get_generation_status(generation_id, current_user)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found"
        )
    
    return GenerationResponse.from_orm(generation)


@router.get("/generations/{generation_id}/pieces", response_model=List[ContentPieceResponse])
async def get_content_pieces(
    generation_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get content pieces for a generation.
    
    Args:
        generation_id: Generation ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of content pieces
        
    Raises:
        HTTPException: If generation not found or access denied
    """
    from ...database.repositories import ContentRepository
    
    # Verify access
    service = ContentGenerationService(db)
    generation = await service.get_generation_status(generation_id, current_user)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found"
        )
    
    # Get pieces
    repo = ContentRepository(db)
    pieces = await repo.get_content_pieces(generation_id)
    
    return [ContentPieceResponse.from_orm(p) for p in pieces]


@router.get("/generations/{generation_id}/pieces/{piece_id}/content")
async def get_piece_content(
    generation_id: UUID,
    piece_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get the actual content of a piece.
    
    Args:
        generation_id: Generation ID
        piece_id: Piece ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Content of the piece
        
    Raises:
        HTTPException: If not found or access denied
    """
    from ...database.repositories import ContentRepository
    
    # Verify access
    service = ContentGenerationService(db)
    generation = await service.get_generation_status(generation_id, current_user)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found"
        )
    
    # Get piece
    repo = ContentRepository(db)
    piece = await repo.get_content_piece(piece_id)
    
    if not piece or piece.generation_id != generation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content piece not found"
        )
    
    return {
        "id": str(piece.id),
        "title": piece.title,
        "content": piece.content,
        "metadata": piece.metadata
    }


@router.post("/generations/{generation_id}/export")
async def export_content(
    generation_id: UUID,
    export_request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Export content in specified format.
    
    Args:
        generation_id: Generation ID
        export_request: Export format
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Export task ID
        
    Raises:
        HTTPException: If generation not found or not completed
    """
    service = ContentGenerationService(db)
    generation = await service.get_generation_status(generation_id, current_user)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found"
        )
        
    if generation.status != GenerationStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only export completed generations"
        )
    
    # Start export
    export_task_id = await service.export_content(
        generation_id=generation_id,
        format=export_request.format,
        user=current_user
    )
    
    logger.info(f"Started export task {export_task_id} for generation {generation_id}")
    
    return {
        "export_task_id": export_task_id,
        "status": "processing"
    }


@router.get("/exports/{export_task_id}/status")
async def get_export_status(
    export_task_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get export task status.
    
    Args:
        export_task_id: Export task ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Export task status
        
    Raises:
        HTTPException: If export task not found
    """
    from ...database.repositories import ContentRepository
    
    repo = ContentRepository(db)
    export_task = await repo.get_export_task(export_task_id)
    
    if not export_task or export_task.requested_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export task not found"
        )
    
    return {
        "id": str(export_task.id),
        "status": export_task.status.value,
        "format": export_task.format.value,
        "started_at": export_task.started_at,
        "completed_at": export_task.completed_at,
        "error_message": export_task.error_message
    }


@router.get("/exports/{export_task_id}/download")
async def download_export(
    export_task_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Download exported content.
    
    Args:
        export_task_id: Export task ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        File download
        
    Raises:
        HTTPException: If export not ready or access denied
    """
    from ...database.repositories import ContentRepository
    from ...database.models import ExportStatus
    
    repo = ContentRepository(db)
    export_task = await repo.get_export_task(export_task_id)
    
    if not export_task or export_task.requested_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export task not found"
        )
        
    if export_task.status != ExportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export not ready. Status: {export_task.status.value}"
        )
        
    if not export_task.output_file_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export file not found"
        )
    
    # Return file
    from pathlib import Path
    file_path = Path(export_task.output_file_path)
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file no longer available"
        )
    
    # Get content type based on format
    content_types = {
        ExportFormat.PDF: "application/pdf",
        ExportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ExportFormat.HTML: "text/html",
        ExportFormat.MARKDOWN: "text/markdown",
        ExportFormat.SCORM: "application/zip"
    }
    
    return FileResponse(
        path=file_path,
        media_type=content_types.get(export_task.format, "application/octet-stream"),
        filename=f"{export_task.generation.title}.{export_task.format.value}"
    )


@router.delete("/generations/{generation_id}")
async def delete_generation(
    generation_id: UUID,
    current_user: User = Depends(get_current_user),
    has_permission = Depends(PermissionChecker("content", "delete")),
    db = Depends(get_db)
):
    """
    Delete a generation (soft delete).
    
    Args:
        generation_id: Generation ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If generation not found or access denied
    """
    from ...database.repositories import ContentRepository
    
    repo = ContentRepository(db)
    generation = await repo.get_generation(generation_id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found"
        )
        
    # Check ownership
    if generation.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Soft delete
    generation.deleted_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Deleted generation {generation_id}")
    
    return {"message": "Generation deleted successfully"}
