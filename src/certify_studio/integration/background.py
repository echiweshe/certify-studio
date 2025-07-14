"""
Background Task Processing with Celery

This module defines all background tasks for asynchronous processing.
Uses Celery for distributed task execution.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from pathlib import Path
import asyncio
import os

from celery import Celery, Task
from celery.utils.log import get_task_logger
from kombu import Queue

from ..core.config import settings
from ..core.logging import setup_logging

# Setup logging
setup_logging()
logger = get_task_logger(__name__)

# Create Celery app
celery_app = Celery(
    'certify_studio',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['certify_studio.integration.background']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_soft_time_limit=3600,  # 1 hour soft limit
    task_time_limit=3900,  # 1 hour 5 min hard limit
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Task routing
    task_routes={
        'process_content_generation': {'queue': 'generation'},
        'process_domain_extraction': {'queue': 'extraction'},
        'process_quality_check': {'queue': 'quality'},
        'process_export_task': {'queue': 'export'},
        'cleanup_old_files': {'queue': 'maintenance'},
    },
    
    # Queue configuration
    task_queues=(
        Queue('generation', priority=10),
        Queue('extraction', priority=8),
        Queue('quality', priority=6),
        Queue('export', priority=4),
        Queue('maintenance', priority=2),
    ),
    
    # Result expiration
    result_expires=3600,  # 1 hour
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-old-files': {
            'task': 'cleanup_old_files',
            'schedule': 3600.0,  # Every hour
        },
        'update-daily-metrics': {
            'task': 'update_daily_metrics',
            'schedule': 300.0,  # Every 5 minutes
        },
    }
)


class AsyncTask(Task):
    """
    Base task class that properly handles async functions.
    """
    def run(self, *args, **kwargs):
        """Run the async task in an event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._run(*args, **kwargs))
        finally:
            loop.close()
            
    async def _run(self, *args, **kwargs):
        """Override this method in subclasses."""
        raise NotImplementedError()


@celery_app.task(base=AsyncTask, name='process_content_generation', bind=True)
class ProcessContentGenerationTask(AsyncTask):
    """Process a content generation request."""
    
    async def _run(self, generation_id: str):
        """
        Process content generation.
        
        Args:
            generation_id: UUID of the generation task
        """
        logger.info(f"Starting content generation: {generation_id}")
        
        try:
            # Import here to avoid circular imports
            from ..database import get_db_session
            from .services import ContentGenerationService
            
            async with get_db_session() as db:
                service = ContentGenerationService(db.session)
                generation = await service.process_generation(UUID(generation_id))
                
                await db.commit()
                
            logger.info(f"Completed content generation: {generation_id}")
            return {
                'generation_id': generation_id,
                'status': generation.status.value,
                'completed_at': generation.completed_at.isoformat() if generation.completed_at else None
            }
            
        except Exception as e:
            logger.error(f"Failed to process generation {generation_id}: {str(e)}")
            # Update task status to failed
            from ..database import get_db_session
            from ..database.repositories import ContentRepository
            from ..database.models import GenerationStatus
            
            async with get_db_session() as db:
                repo = ContentRepository(db.session)
                generation = await repo.get_generation(UUID(generation_id))
                if generation:
                    generation.status = GenerationStatus.FAILED
                    generation.error_message = str(e)
                    generation.completed_at = datetime.utcnow()
                    await db.commit()
                    
            raise


@celery_app.task(base=AsyncTask, name='process_domain_extraction', bind=True)
class ProcessDomainExtractionTask(AsyncTask):
    """Extract domain knowledge from content."""
    
    async def _run(self, file_path: str, generation_id: Optional[str] = None):
        """
        Extract domain knowledge.
        
        Args:
            file_path: Path to file to process
            generation_id: Optional generation ID
        """
        logger.info(f"Starting domain extraction: {file_path}")
        
        try:
            from ..agents.specialized import DomainExtractionAgent
            from ..database import get_db_session
            from ..database.repositories import DomainRepository
            
            # Initialize agent
            agent = DomainExtractionAgent()
            
            # Extract knowledge
            result = await agent.process({
                'file_path': file_path,
                'extract_all': True
            })
            
            # Store in database if generation_id provided
            if generation_id:
                async with get_db_session() as db:
                    repo = DomainRepository(db.session)
                    
                    # Store concepts
                    for concept in result.get('concepts', []):
                        await repo.create_extracted_concept(
                            generation_id=UUID(generation_id),
                            name=concept['name'],
                            description=concept['description'],
                            concept_type=concept.get('type', 'general'),
                            importance_score=concept.get('importance', 0.5),
                            metadata=concept.get('metadata', {})
                        )
                        
                    await db.commit()
                    
            logger.info(f"Completed domain extraction: {file_path}")
            return {
                'file_path': file_path,
                'concepts_extracted': len(result.get('concepts', [])),
                'relationships_found': len(result.get('relationships', []))
            }
            
        except Exception as e:
            logger.error(f"Failed to extract domain knowledge from {file_path}: {str(e)}")
            raise


@celery_app.task(base=AsyncTask, name='process_quality_check', bind=True)
class ProcessQualityCheckTask(AsyncTask):
    """Run quality checks on content."""
    
    async def _run(self, generation_id: str, check_types: Optional[list] = None):
        """
        Run quality checks.
        
        Args:
            generation_id: Generation to check
            check_types: Specific check types to run
        """
        logger.info(f"Starting quality checks: {generation_id}")
        
        try:
            from ..agents.specialized import QualityAssuranceAgent
            from ..database import get_db_session
            from ..database.repositories import QualityRepository, ContentRepository
            from ..database.models import QualityStatus
            
            async with get_db_session() as db:
                content_repo = ContentRepository(db.session)
                quality_repo = QualityRepository(db.session)
                
                # Get content pieces
                pieces = await content_repo.get_content_pieces(UUID(generation_id))
                
                # Initialize agent
                agent = QualityAssuranceAgent()
                
                # Run checks on each piece
                for piece in pieces:
                    result = await agent.process({
                        'content': piece.content,
                        'metadata': piece.metadata,
                        'check_types': check_types or ['all']
                    })
                    
                    # Store quality check
                    check = await quality_repo.create_quality_check(
                        generation_id=UUID(generation_id),
                        check_type='automated',
                        check_name=f"Quality check for {piece.title}",
                        status=QualityStatus.COMPLETED,
                        overall_score=result['overall_score'],
                        passed=result['passed'],
                        details=result
                    )
                    
                    # Store metrics
                    for metric_name, metric_value in result.get('metrics', {}).items():
                        await quality_repo.create_quality_metric(
                            quality_check_id=check.id,
                            metric_name=metric_name,
                            metric_value=metric_value,
                            threshold=0.8,
                            passed=metric_value >= 0.8
                        )
                        
                await db.commit()
                
            logger.info(f"Completed quality checks: {generation_id}")
            return {
                'generation_id': generation_id,
                'pieces_checked': len(pieces)
            }
            
        except Exception as e:
            logger.error(f"Failed to run quality checks for {generation_id}: {str(e)}")
            raise


@celery_app.task(base=AsyncTask, name='process_export_task', bind=True)
class ProcessExportTask(AsyncTask):
    """Export content to different formats."""
    
    async def _run(self, export_task_id: str):
        """
        Process export task.
        
        Args:
            export_task_id: Export task ID
        """
        logger.info(f"Starting export task: {export_task_id}")
        
        try:
            from ..database import get_db_session
            from ..database.repositories import ContentRepository
            from ..database.models import ExportStatus, ExportFormat
            from ..agents.specialized import ContentGenerationAgent
            
            async with get_db_session() as db:
                repo = ContentRepository(db.session)
                
                # Get export task
                export_task = await repo.get_export_task(UUID(export_task_id))
                if not export_task:
                    raise ValueError(f"Export task {export_task_id} not found")
                    
                # Update status
                export_task.status = ExportStatus.PROCESSING
                export_task.started_at = datetime.utcnow()
                await db.commit()
                
                # Get content pieces
                pieces = await repo.get_content_pieces(export_task.generation_id)
                
                # Initialize agent for formatting
                agent = ContentGenerationAgent()
                
                # Process based on format
                output_path = Path(settings.EXPORT_DIR) / f"{export_task_id}.{export_task.format.value}"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                if export_task.format == ExportFormat.PDF:
                    # Generate PDF
                    result = await agent.export_to_pdf(pieces, str(output_path))
                elif export_task.format == ExportFormat.DOCX:
                    # Generate DOCX
                    result = await agent.export_to_docx(pieces, str(output_path))
                elif export_task.format == ExportFormat.HTML:
                    # Generate HTML
                    result = await agent.export_to_html(pieces, str(output_path))
                elif export_task.format == ExportFormat.MARKDOWN:
                    # Generate Markdown
                    result = await agent.export_to_markdown(pieces, str(output_path))
                elif export_task.format == ExportFormat.SCORM:
                    # Generate SCORM package
                    result = await agent.export_to_scorm(pieces, str(output_path))
                else:
                    raise ValueError(f"Unsupported format: {export_task.format}")
                    
                # Update task
                export_task.status = ExportStatus.COMPLETED
                export_task.completed_at = datetime.utcnow()
                export_task.output_file_path = str(output_path)
                export_task.output_file_size = output_path.stat().st_size
                await db.commit()
                
            logger.info(f"Completed export task: {export_task_id}")
            return {
                'export_task_id': export_task_id,
                'output_path': str(output_path),
                'format': export_task.format.value
            }
            
        except Exception as e:
            logger.error(f"Failed to process export task {export_task_id}: {str(e)}")
            
            # Update status
            from ..database import get_db_session
            from ..database.repositories import ContentRepository
            from ..database.models import ExportStatus
            
            async with get_db_session() as db:
                repo = ContentRepository(db.session)
                export_task = await repo.get_export_task(UUID(export_task_id))
                if export_task:
                    export_task.status = ExportStatus.FAILED
                    export_task.error_message = str(e)
                    export_task.completed_at = datetime.utcnow()
                    await db.commit()
                    
            raise


@celery_app.task(name='cleanup_old_files')
def cleanup_old_files():
    """Clean up old temporary files."""
    logger.info("Starting file cleanup")
    
    try:
        # Clean upload directory
        upload_dir = Path(settings.UPLOAD_DIR)
        cutoff_time = datetime.utcnow().timestamp() - (7 * 24 * 3600)  # 7 days
        
        cleaned = 0
        for file_path in upload_dir.rglob('*'):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    cleaned += 1
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")
                    
        logger.info(f"Cleaned up {cleaned} old files")
        return {'cleaned_files': cleaned}
        
    except Exception as e:
        logger.error(f"File cleanup failed: {e}")
        raise


@celery_app.task(base=AsyncTask, name='update_daily_metrics')
class UpdateDailyMetricsTask(AsyncTask):
    """Update daily platform metrics."""
    
    async def _run(self):
        """Update metrics for current day."""
        logger.info("Updating daily metrics")
        
        try:
            from ..database import get_db_session
            from ..database.repositories import AnalyticsRepository
            from datetime import date
            
            async with get_db_session() as db:
                repo = AnalyticsRepository(db.session)
                
                # Update metrics for today
                today = date.today()
                metrics = await repo.update_daily_metrics(today)
                
                await db.commit()
                
            logger.info("Daily metrics updated")
            return {
                'date': today.isoformat(),
                'active_users': metrics.active_users,
                'total_generations': metrics.total_generations
            }
            
        except Exception as e:
            logger.error(f"Failed to update daily metrics: {e}")
            raise


# Task registration
process_content_generation = ProcessContentGenerationTask()
process_domain_extraction = ProcessDomainExtractionTask()
process_quality_check = ProcessQualityCheckTask()
process_export_task = ProcessExportTask()


# Celery startup/shutdown hooks
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks."""
    logger.info("Setting up periodic tasks")


# @celery_app.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, 
                        args=None, kwargs=None, traceback=None, 
                        einfo=None, **kw):
    """Handle task failures."""
    logger.error(f"Task {sender.name} [{task_id}] failed: {exception}")
    
    # Could send alerts, update metrics, etc.
    
# Register handler differently for newer Celery versions
try:
    from celery import signals
    signals.task_failure.connect(task_failure_handler)
except:
    pass
    
    
# Worker configuration
if __name__ == '__main__':
    celery_app.start()
