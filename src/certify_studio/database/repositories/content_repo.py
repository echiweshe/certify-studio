"""
Content repository for database operations.

This module provides repository classes for content-related
database operations including generations, media, and exports.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from loguru import logger

from .base_repo import BaseRepository, RepositoryError
from ..models.content import (
    ContentGeneration, ContentPiece, MediaAsset,
    MediaReference, ContentInteraction, ExportTask,
    ContentVersion, ContentType, InteractionType
)
from ..models.base import TaskStatus, ContentStatus, utcnow


class ContentGenerationRepository(BaseRepository[ContentGeneration]):
    """Repository for ContentGeneration operations."""
    
    @property
    def model(self):
        return ContentGeneration
    
    async def create_generation(
        self,
        user_id: UUID,
        source_file_path: str,
        source_file_name: str,
        title: str,
        content_type: ContentType,
        **kwargs
    ) -> ContentGeneration:
        """Create a new content generation task."""
        return await self.create(
            user_id=user_id,
            source_file_path=source_file_path,
            source_file_name=source_file_name,
            title=title,
            content_type=content_type,
            status=TaskStatus.PENDING,
            **kwargs
        )
    
    async def get_with_content(self, generation_id: UUID) -> Optional[ContentGeneration]:
        """Get generation with all content pieces loaded."""
        query = select(ContentGeneration).where(
            ContentGeneration.id == generation_id
        ).options(
            selectinload(ContentGeneration.content_pieces),
            selectinload(ContentGeneration.media_assets),
            selectinload(ContentGeneration.export_tasks)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_generations(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        content_type: Optional[ContentType] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[ContentGeneration]:
        """Get all generations for a user with filters."""
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status
        if content_type:
            filters["content_type"] = content_type
        
        return await self.filter(
            filters,
            skip=skip,
            limit=limit,
            order_by="created_at",
            order_desc=True
        )
    
    async def update_status(
        self,
        generation_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        current_step: Optional[str] = None
    ) -> Optional[ContentGeneration]:
        """Update generation status."""
        updates = {"status": status}
        
        if status == TaskStatus.PROCESSING and "started_at" not in updates:
            updates["started_at"] = utcnow()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            updates["completed_at"] = utcnow()
        
        if error_message:
            updates["error_message"] = error_message
        if current_step:
            updates["current_step"] = current_step
        
        return await self.update_by_id(generation_id, **updates)
    
    async def update_progress(
        self,
        generation_id: UUID,
        progress: float,
        current_step: Optional[str] = None
    ) -> None:
        """Update generation progress."""
        updates = {"progress": min(100.0, max(0.0, progress))}
        if current_step:
            updates["current_step"] = current_step
        
        await self.update_by_id(generation_id, **updates)
    
    async def get_active_generations(self) -> List[ContentGeneration]:
        """Get all active (processing) generations."""
        return await self.filter(
            {"status": TaskStatus.PROCESSING},
            order_by="started_at"
        )
    
    async def get_stuck_generations(self, timeout_minutes: int = 60) -> List[ContentGeneration]:
        """Get generations that seem to be stuck."""
        cutoff_time = utcnow() - timedelta(minutes=timeout_minutes)
        
        query = select(ContentGeneration).where(
            and_(
                ContentGeneration.status == TaskStatus.PROCESSING,
                ContentGeneration.started_at < cutoff_time
            )
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def calculate_user_usage(self, user_id: UUID, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Calculate user's content generation usage."""
        query = select(
            func.count(ContentGeneration.id).label("total_count"),
            func.sum(ContentGeneration.processing_time_seconds).label("total_time"),
            func.avg(ContentGeneration.processing_time_seconds).label("avg_time")
        ).where(ContentGeneration.user_id == user_id)
        
        if since:
            query = query.where(ContentGeneration.created_at >= since)
        
        result = await self.session.execute(query)
        row = result.one()
        
        return {
            "total_generations": row.total_count or 0,
            "total_processing_time": row.total_time or 0.0,
            "average_processing_time": row.avg_time or 0.0
        }


class ContentPieceRepository(BaseRepository[ContentPiece]):
    """Repository for ContentPiece operations."""
    
    @property
    def model(self):
        return ContentPiece
    
    async def create_content_piece(
        self,
        generation_id: UUID,
        title: str,
        slug: str,
        content_type: str,
        order_index: int,
        parent_id: Optional[UUID] = None,
        **kwargs
    ) -> ContentPiece:
        """Create a new content piece."""
        # Calculate depth level
        depth_level = 0
        if parent_id:
            parent = await self.get_by_id(parent_id)
            if parent:
                depth_level = parent.depth_level + 1
        
        return await self.create(
            generation_id=generation_id,
            title=title,
            slug=slug,
            content_type=content_type,
            order_index=order_index,
            parent_id=parent_id,
            depth_level=depth_level,
            status=ContentStatus.DRAFT,
            **kwargs
        )
    
    async def get_generation_pieces(
        self,
        generation_id: UUID,
        parent_id: Optional[UUID] = None
    ) -> List[ContentPiece]:
        """Get all content pieces for a generation."""
        filters = {"generation_id": generation_id}
        if parent_id is not None:
            filters["parent_id"] = parent_id
        
        return await self.filter(
            filters,
            order_by="order_index",
            include=["children", "media_references", "interactions"]
        )
    
    async def get_piece_tree(self, generation_id: UUID) -> List[ContentPiece]:
        """Get content pieces organized as a tree."""
        # Get all pieces
        pieces = await self.filter(
            {"generation_id": generation_id},
            order_by="order_index"
        )
        
        # Organize into tree structure
        piece_map = {piece.id: piece for piece in pieces}
        roots = []
        
        for piece in pieces:
            if piece.parent_id is None:
                roots.append(piece)
            else:
                parent = piece_map.get(piece.parent_id)
                if parent:
                    if not hasattr(parent, '_children'):
                        parent._children = []
                    parent._children.append(piece)
        
        return roots
    
    async def update_content(
        self,
        piece_id: UUID,
        content_text: Optional[str] = None,
        content_markdown: Optional[str] = None,
        content_html: Optional[str] = None,
        content_data: Optional[Dict[str, Any]] = None
    ) -> Optional[ContentPiece]:
        """Update content piece content."""
        updates = {}
        if content_text is not None:
            updates["content_text"] = content_text
        if content_markdown is not None:
            updates["content_markdown"] = content_markdown
        if content_html is not None:
            updates["content_html"] = content_html
        if content_data is not None:
            updates["content_data"] = content_data
        
        if updates:
            updates["version"] = ContentPiece.version + 1
        
        return await self.update_by_id(piece_id, **updates)
    
    async def publish_piece(self, piece_id: UUID) -> Optional[ContentPiece]:
        """Publish a content piece."""
        return await self.update_by_id(
            piece_id,
            status=ContentStatus.PUBLISHED,
            is_published=True,
            published_at=utcnow()
        )
    
    async def create_version(self, piece_id: UUID, change_summary: str) -> ContentVersion:
        """Create a version snapshot of a content piece."""
        piece = await self.get_by_id_or_fail(piece_id)
        
        # Create snapshot
        snapshot = {
            "title": piece.title,
            "content_text": piece.content_text,
            "content_markdown": piece.content_markdown,
            "content_html": piece.content_html,
            "content_data": piece.content_data,
            "learning_objectives": piece.learning_objectives,
            "cognitive_load_intrinsic": piece.cognitive_load_intrinsic,
            "cognitive_load_extraneous": piece.cognitive_load_extraneous,
            "cognitive_load_germane": piece.cognitive_load_germane
        }
        
        version = ContentVersion(
            content_piece_id=piece_id,
            version_number=piece.version,
            content_snapshot=snapshot,
            change_summary=change_summary,
            change_type="manual"
        )
        
        self.session.add(version)
        await self.session.flush()
        return version


class MediaAssetRepository(BaseRepository[MediaAsset]):
    """Repository for MediaAsset operations."""
    
    @property
    def model(self):
        return MediaAsset
    
    async def create_media_asset(
        self,
        generation_id: UUID,
        file_name: str,
        file_path: str,
        file_hash: str,
        mime_type: str,
        media_type: str,
        **kwargs
    ) -> MediaAsset:
        """Create a new media asset."""
        # Check for duplicate
        existing = await self.get_by(file_hash=file_hash)
        if existing:
            # Return existing asset instead of creating duplicate
            return existing
        
        return await self.create(
            generation_id=generation_id,
            file_name=file_name,
            file_path=file_path,
            file_hash=file_hash,
            mime_type=mime_type,
            media_type=media_type,
            **kwargs
        )
    
    async def get_generation_media(
        self,
        generation_id: UUID,
        media_type: Optional[str] = None
    ) -> List[MediaAsset]:
        """Get all media assets for a generation."""
        filters = {"generation_id": generation_id}
        if media_type:
            filters["media_type"] = media_type
        
        return await self.filter(filters, order_by="created_at")
    
    async def add_media_reference(
        self,
        content_piece_id: UUID,
        media_asset_id: UUID,
        reference_key: str,
        reference_type: str,
        position_index: int = 0,
        **kwargs
    ) -> MediaReference:
        """Add a media reference to a content piece."""
        # Check if reference already exists
        existing = await self.session.execute(
            select(MediaReference).where(
                and_(
                    MediaReference.content_piece_id == content_piece_id,
                    MediaReference.media_asset_id == media_asset_id,
                    MediaReference.reference_key == reference_key
                )
            )
        )
        
        if existing.scalar_one_or_none():
            raise RepositoryError("Media reference already exists")
        
        reference = MediaReference(
            content_piece_id=content_piece_id,
            media_asset_id=media_asset_id,
            reference_key=reference_key,
            reference_type=reference_type,
            position_index=position_index,
            **kwargs
        )
        
        self.session.add(reference)
        await self.session.flush()
        return reference
    
    async def update_cdn_info(
        self,
        asset_id: UUID,
        cdn_url: str,
        thumbnail_url: Optional[str] = None,
        variants: Optional[Dict[str, Any]] = None
    ) -> Optional[MediaAsset]:
        """Update CDN information for a media asset."""
        updates = {"cdn_url": cdn_url}
        if thumbnail_url:
            updates["thumbnail_url"] = thumbnail_url
        if variants:
            updates["variants"] = variants
        
        return await self.update_by_id(asset_id, **updates)


class ContentInteractionRepository(BaseRepository[ContentInteraction]):
    """Repository for ContentInteraction operations."""
    
    @property
    def model(self):
        return ContentInteraction
    
    async def create_interaction(
        self,
        content_piece_id: UUID,
        interaction_type: InteractionType,
        title: str,
        interaction_data: Dict[str, Any],
        **kwargs
    ) -> ContentInteraction:
        """Create a new content interaction."""
        return await self.create(
            content_piece_id=content_piece_id,
            interaction_type=interaction_type,
            title=title,
            interaction_data=interaction_data,
            **kwargs
        )
    
    async def get_piece_interactions(
        self,
        content_piece_id: UUID,
        interaction_type: Optional[InteractionType] = None
    ) -> List[ContentInteraction]:
        """Get all interactions for a content piece."""
        filters = {"content_piece_id": content_piece_id}
        if interaction_type:
            filters["interaction_type"] = interaction_type
        
        return await self.filter(filters, order_by="position_index")
    
    async def update_interaction_data(
        self,
        interaction_id: UUID,
        interaction_data: Dict[str, Any],
        correct_responses: Optional[Dict[str, Any]] = None,
        feedback_data: Optional[Dict[str, Any]] = None
    ) -> Optional[ContentInteraction]:
        """Update interaction data."""
        updates = {"interaction_data": interaction_data}
        if correct_responses is not None:
            updates["correct_responses"] = correct_responses
        if feedback_data is not None:
            updates["feedback_data"] = feedback_data
        
        return await self.update_by_id(interaction_id, **updates)


class ExportTaskRepository(BaseRepository[ExportTask]):
    """Repository for ExportTask operations."""
    
    @property
    def model(self):
        return ExportTask
    
    async def create_export_task(
        self,
        generation_id: UUID,
        format: str,
        export_options: Optional[Dict[str, Any]] = None
    ) -> ExportTask:
        """Create a new export task."""
        return await self.create(
            generation_id=generation_id,
            format=format,
            export_options=export_options or {},
            status=TaskStatus.PENDING
        )
    
    async def get_generation_exports(
        self,
        generation_id: UUID,
        status: Optional[str] = None
    ) -> List[ExportTask]:
        """Get all export tasks for a generation."""
        filters = {"generation_id": generation_id}
        if status:
            filters["status"] = status
        
        return await self.filter(
            filters,
            order_by="created_at",
            order_desc=True
        )
    
    async def update_export_status(
        self,
        export_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        progress: Optional[float] = None
    ) -> Optional[ExportTask]:
        """Update export task status."""
        updates = {"status": status}
        
        if status == TaskStatus.PROCESSING and "started_at" not in updates:
            updates["started_at"] = utcnow()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            updates["completed_at"] = utcnow()
        
        if error_message:
            updates["error_message"] = error_message
        if progress is not None:
            updates["progress"] = min(100.0, max(0.0, progress))
        
        return await self.update_by_id(export_id, **updates)
    
    async def complete_export(
        self,
        export_id: UUID,
        output_file_path: str,
        output_file_size: int,
        output_file_hash: str,
        download_url: str,
        download_expires_at: datetime,
        export_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ExportTask]:
        """Mark export as completed with output information."""
        export_task = await self.get_by_id(export_id)
        if not export_task:
            return None
        
        processing_time = None
        if export_task.started_at:
            processing_time = (utcnow() - export_task.started_at).total_seconds()
        
        return await self.update(
            export_task,
            status=TaskStatus.COMPLETED,
            completed_at=utcnow(),
            processing_time_seconds=processing_time,
            output_file_path=output_file_path,
            output_file_size=output_file_size,
            output_file_hash=output_file_hash,
            download_url=download_url,
            download_expires_at=download_expires_at,
            export_metadata=export_metadata or {},
            progress=100.0
        )
    
    async def get_expired_exports(self) -> List[ExportTask]:
        """Get exports with expired download links."""
        query = select(ExportTask).where(
            and_(
                ExportTask.status == TaskStatus.COMPLETED,
                ExportTask.download_expires_at < utcnow()
            )
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def cleanup_old_exports(self, days_old: int = 30) -> int:
        """Delete old export tasks and their files."""
        cutoff_date = utcnow() - timedelta(days=days_old)
        
        return await self.delete_many({
            "completed_at": {"lt": cutoff_date}
        })


# Export repositories
__all__ = [
    "ContentGenerationRepository",
    "ContentPieceRepository",
    "MediaAssetRepository",
    "ContentInteractionRepository",
    "ExportTaskRepository"
]
