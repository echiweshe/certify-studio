"""
Service Layer - Business Logic

This module contains service classes that orchestrate agents, repositories,
and background tasks to implement business logic.
"""

from typing import List, Dict, Any, Optional, BinaryIO
from datetime import datetime
from uuid import UUID
import asyncio
import aiofiles
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import (
    User, ContentGeneration, ContentPiece, 
    ExtractedConcept, QualityCheck, GenerationAnalytics,
    ContentType, TaskStatus, QualityStatus, ExportFormat
)
from ..database.repositories import (
    ContentGenerationRepository, ContentPieceRepository,
    MediaAssetRepository, ExportTaskRepository,
    DomainRepository, QualityRepository, AnalyticsRepository,
    UserRepository, RoleRepository, UserRoleRepository
)
from ..agents.orchestrator import AgenticOrchestrator
from ..agents.specialized.pedagogical.agent import PedagogicalReasoningAgent
from ..agents.specialized.content_generation.agent import ContentGenerationAgent
from ..agents.specialized.domain_extraction.agent import DomainExtractionAgent
from ..agents.specialized.quality_assurance.agent import QualityAssuranceAgent
from ..knowledge import UnifiedGraphRAG
from ..core.logging import get_logger
from ..core.config import settings
from .events import EventBus, ContentGenerationStartedEvent, ContentGenerationCompletedEvent
from .background import celery_app

logger = get_logger(__name__)


class ContentGenerationService:
    """
    Service for managing content generation workflow.
    
    This orchestrates the entire content generation process:
    1. Create generation task in database
    2. Extract domain knowledge
    3. Generate content with agents
    4. Run quality checks
    5. Store results
    """
    
    def __init__(
        self,
        db: AsyncSession,
        orchestrator: Optional[AgenticOrchestrator] = None,
        event_bus: Optional[EventBus] = None
    ):
        self.db = db
        self.content_repo = ContentGenerationRepository(db)
        self.content_piece_repo = ContentPieceRepository(db)
        self.media_asset_repo = MediaAssetRepository(db)
        self.export_task_repo = ExportTaskRepository(db)
        self.domain_repo = DomainRepository(db)
        self.quality_repo = QualityRepository(db)
        self.analytics_repo = AnalyticsRepository(db)
        
        # Initialize orchestrator if not provided
        self.orchestrator = orchestrator or AgenticOrchestrator()
        self.event_bus = event_bus or EventBus()
        
    async def start_generation(
        self,
        user: User,
        source_file: BinaryIO,
        filename: str,
        title: str,
        content_type: ContentType,
        target_audience: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContentGeneration:
        """
        Start a new content generation task.
        
        Args:
            user: User initiating the generation
            source_file: Uploaded file content
            filename: Original filename
            title: Title for the generated content
            content_type: Type of content to generate
            target_audience: Target audience description
            metadata: Additional metadata
            
        Returns:
            Created ContentGeneration task
        """
        # Save uploaded file
        upload_path = Path(settings.UPLOAD_DIR) / f"{user.id}" / filename
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(upload_path, 'wb') as f:
            await f.write(await source_file.read())
            
        # Create generation task in database
        generation = await self.content_repo.create_generation(
            user_id=user.id,
            source_file_path=str(upload_path),
            source_file_name=filename,
            title=title,
            content_type=content_type,
            target_audience=target_audience,
            metadata=metadata
        )
        
        # Emit event
        await self.event_bus.emit(ContentGenerationStartedEvent(
            generation_id=generation.id,
            user_id=user.id,
            content_type=content_type
        ))
        
        # Start background processing
        celery_app.send_task(
            'process_content_generation',
            args=[str(generation.id)]
        )
        
        # Record analytics
        await self.analytics_repo.record_generation_start(
            user_id=user.id,
            generation_id=generation.id,
            content_type=content_type
        )
        
        return generation
        
    async def process_generation(self, generation_id: UUID) -> ContentGeneration:
        """
        Process a content generation task (called by background worker).
        
        Args:
            generation_id: ID of the generation task
            
        Returns:
            Updated ContentGeneration with results
        """
        # Get generation task
        generation = await self.content_repo.get(generation_id)
        if not generation:
            raise ValueError(f"Generation {generation_id} not found")
            
        try:
            # Update status
            generation.status = TaskStatus.PROCESSING
            generation.started_at = datetime.utcnow()
            await self.db.commit()
            
            # Step 1: Domain extraction
            logger.info(f"Starting domain extraction for {generation_id}")
            domain_knowledge = await self._extract_domain_knowledge(generation)
            
            # Step 2: Content generation
            logger.info(f"Starting content generation for {generation_id}")
            content_pieces = await self._generate_content(generation, domain_knowledge)
            
            # Step 3: Quality assurance
            logger.info(f"Starting quality checks for {generation_id}")
            quality_results = await self._run_quality_checks(generation, content_pieces)
            
            # Update generation status
            generation.status = TaskStatus.COMPLETED
            generation.completed_at = datetime.utcnow()
            generation.progress = 100
            
            # Calculate total tokens used
            total_tokens = sum(p.generation_tokens for p in content_pieces)
            generation.total_tokens_used = total_tokens
            
            await self.db.commit()
            
            # Emit completion event
            await self.event_bus.emit(ContentGenerationCompletedEvent(
                generation_id=generation.id,
                user_id=generation.user_id,
                success=True,
                content_pieces=len(content_pieces)
            ))
            
            # Record analytics
            await self.analytics_repo.record_generation_complete(
                generation_id=generation.id,
                duration_seconds=(generation.completed_at - generation.started_at).total_seconds(),
                tokens_used=total_tokens,
                quality_score=quality_results.get('overall_score', 0)
            )
            
            return generation
            
        except Exception as e:
            # Handle failure
            logger.error(f"Generation {generation_id} failed: {str(e)}")
            generation.status = TaskStatus.FAILED
            generation.error_message = str(e)
            generation.completed_at = datetime.utcnow()
            await self.db.commit()
            
            # Emit failure event
            await self.event_bus.emit(ContentGenerationCompletedEvent(
                generation_id=generation.id,
                user_id=generation.user_id,
                success=False,
                error=str(e)
            ))
            
            raise
            
    async def _extract_domain_knowledge(self, generation: ContentGeneration) -> Dict[str, Any]:
        """Extract domain knowledge from source material."""
        # Initialize domain extraction agent
        extraction_agent = DomainExtractionAgent()
        
        # Extract knowledge
        result = await extraction_agent.process({
            'file_path': generation.source_file_path,
            'content_type': generation.content_type.value
        })
        
        # Store extracted concepts in database
        for concept in result.get('concepts', []):
            extracted_concept = await self.domain_repo.create_extracted_concept(
                generation_id=generation.id,
                name=concept['name'],
                description=concept['description'],
                concept_type=concept.get('type', 'general'),
                importance_score=concept.get('importance', 0.5),
                metadata=concept.get('metadata', {})
            )
            
            # Generate and store embedding
            if 'embedding' in concept:
                extracted_concept.embedding = concept['embedding']
                await self.db.commit()
                
        # Store relationships
        for relationship in result.get('relationships', []):
            await self.domain_repo.create_concept_relationship(
                source_concept_id=relationship['source_id'],
                target_concept_id=relationship['target_id'],
                relationship_type=relationship['type'],
                strength=relationship.get('strength', 0.5)
            )
            
        return result
        
    async def _generate_content(
        self, 
        generation: ContentGeneration,
        domain_knowledge: Dict[str, Any]
    ) -> List[ContentPiece]:
        """Generate content pieces using agents."""
        # Initialize agents
        pedagogical_agent = PedagogicalReasoningAgent()
        content_agent = ContentGenerationAgent()
        
        # Create learning design
        learning_design = await pedagogical_agent.process({
            'domain_knowledge': domain_knowledge,
            'target_audience': generation.target_audience,
            'content_type': generation.content_type.value
        })
        
        # Generate content pieces
        content_pieces = []
        
        for section in learning_design.get('sections', []):
            # Generate content for section
            content_result = await content_agent.process({
                'section': section,
                'domain_knowledge': domain_knowledge,
                'style_guide': learning_design.get('style_guide', {})
            })
            
            # Store content piece
            piece = await self.content_piece_repo.create(
                generation_id=generation.id,
                piece_type=section['type'],
                title=section['title'],
                content=content_result['content'],
                order_index=section['order'],
                metadata={
                    'cognitive_load': section.get('cognitive_load', 0.5),
                    'learning_objectives': section.get('objectives', []),
                    'duration_minutes': section.get('duration', 10)
                },
                generation_tokens=content_result.get('tokens_used', 0)
            )
            
            content_pieces.append(piece)
            
            # Update progress
            progress = (len(content_pieces) / len(learning_design['sections'])) * 70 + 20
            generation.progress = int(progress)
            await self.db.commit()
            
        return content_pieces
        
    async def _run_quality_checks(
        self,
        generation: ContentGeneration,
        content_pieces: List[ContentPiece]
    ) -> Dict[str, Any]:
        """Run quality checks on generated content."""
        # Initialize quality agent
        quality_agent = QualityAssuranceAgent()
        
        results = {}
        
        # Check each content piece
        for piece in content_pieces:
            check_result = await quality_agent.process({
                'content': piece.content,
                'metadata': piece.metadata,
                'content_type': piece.piece_type
            })
            
            # Store quality check
            quality_check = await self.quality_repo.create_quality_check(
                generation_id=generation.id,
                check_type='automated',
                check_name=f"Quality check for {piece.title}",
                status=QualityStatus.COMPLETED,
                overall_score=check_result['overall_score'],
                passed=check_result['passed'],
                details=check_result
            )
            
            # Store individual metrics
            for metric_name, metric_value in check_result.get('metrics', {}).items():
                await self.quality_repo.create_quality_metric(
                    quality_check_id=quality_check.id,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    threshold=0.8,
                    passed=metric_value >= 0.8
                )
                
        # Calculate overall score
        all_checks = await self.quality_repo.get_generation_quality_checks(generation.id)
        if all_checks:
            results['overall_score'] = sum(c.overall_score for c in all_checks) / len(all_checks)
            results['all_passed'] = all(c.passed for c in all_checks)
        else:
            results['overall_score'] = 0
            results['all_passed'] = False
            
        return results
        
    async def get_generation_status(
        self,
        generation_id: UUID,
        user: User
    ) -> Optional[ContentGeneration]:
        """
        Get generation status.
        
        Args:
            generation_id: Generation ID
            user: Current user
            
        Returns:
            ContentGeneration if found and user has access
        """
        generation = await self.content_repo.get(generation_id)
        
        # Check access
        if generation and generation.user_id != user.id and not user.is_superuser:
            return None
            
        return generation
        
    async def export_content(
        self,
        generation_id: UUID,
        format: ExportFormat,
        user: User
    ) -> str:
        """
        Export content in specified format.
        
        Args:
            generation_id: Generation ID
            format: Export format
            user: Current user
            
        Returns:
            Export task ID
        """
        # Verify access
        generation = await self.get_generation_status(generation_id, user)
        if not generation:
            raise ValueError("Generation not found or access denied")
            
        # Create export task
        export_task = await self.export_task_repo.create(
            generation_id=generation_id,
            format=format,
            requested_by_id=user.id
        )
        
        # Start background export
        celery_app.send_task(
            'process_export_task',
            args=[str(export_task.id)]
        )
        
        return str(export_task.id)


class DomainExtractionService:
    """Service for domain knowledge extraction and management."""
    
    def __init__(self, db: AsyncSession, graphrag: Optional[UnifiedGraphRAG] = None):
        self.db = db
        self.domain_repo = DomainRepository(db)
        self.graphrag = graphrag
        
    async def extract_concepts_from_text(
        self,
        text: str,
        source_id: Optional[UUID] = None
    ) -> List[ExtractedConcept]:
        """
        Extract concepts from text.
        
        Args:
            text: Text to analyze
            source_id: Optional source generation ID
            
        Returns:
            List of extracted concepts
        """
        # Use domain extraction agent
        agent = DomainExtractionAgent()
        result = await agent.extract_concepts_from_text(text)
        
        concepts = []
        for concept_data in result['concepts']:
            concept = await self.domain_repo.create_extracted_concept(
                generation_id=source_id,
                name=concept_data['name'],
                description=concept_data['description'],
                concept_type=concept_data.get('type', 'general'),
                importance_score=concept_data.get('importance', 0.5),
                metadata=concept_data.get('metadata', {})
            )
            concepts.append(concept)
            
        # Add to knowledge graph if available
        if self.graphrag:
            for concept in concepts:
                await self.graphrag.add_concept_node(concept)
                
        return concepts
        
    async def find_learning_path(
        self,
        target_concept: str,
        known_concepts: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Find optimal learning path to target concept.
        
        Args:
            target_concept: Target concept to learn
            known_concepts: Concepts already known
            
        Returns:
            Learning path as list of concepts
        """
        # Find canonical concepts
        canonical_target = await self.domain_repo.find_canonical_concept(target_concept)
        if not canonical_target:
            return []
            
        canonical_known = []
        for concept in known_concepts:
            canonical = await self.domain_repo.find_canonical_concept(concept)
            if canonical:
                canonical_known.append(canonical)
                
        # Use knowledge graph to find path
        if self.graphrag:
            path = await self.graphrag.find_learning_path(
                start_concepts=[c.id for c in canonical_known],
                target_concept=canonical_target.id
            )
            
            # Convert to readable format
            result_path = []
            for concept_id in path:
                concept = await self.domain_repo.get_canonical_concept(concept_id)
                if concept:
                    result_path.append({
                        'id': str(concept.id),
                        'name': concept.name,
                        'description': concept.description,
                        'difficulty': concept.difficulty_level
                    })
                    
            return result_path
            
        return []


class QualityAssuranceService:
    """Service for quality assurance and feedback management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.quality_repo = QualityRepository(db)
        self.analytics_repo = AnalyticsRepository(db)
        
    async def submit_user_feedback(
        self,
        user: User,
        generation_id: UUID,
        rating: int,
        feedback_text: Optional[str] = None,
        feedback_type: str = "general"
    ) -> None:
        """
        Submit user feedback for generated content.
        
        Args:
            user: User providing feedback
            generation_id: Generation to provide feedback for
            rating: Rating (1-5)
            feedback_text: Optional text feedback
            feedback_type: Type of feedback
        """
        # Create feedback
        await self.quality_repo.create_user_feedback(
            user_id=user.id,
            generation_id=generation_id,
            feedback_type=feedback_type,
            rating=rating,
            feedback_text=feedback_text
        )
        
        # Update generation quality score
        await self._update_generation_quality_score(generation_id)
        
        # Record analytics
        await self.analytics_repo.record_user_feedback(
            user_id=user.id,
            generation_id=generation_id,
            rating=rating
        )
        
    async def _update_generation_quality_score(self, generation_id: UUID):
        """Update overall quality score based on feedback."""
        # Get all feedback
        feedback_list = await self.quality_repo.get_generation_feedback(generation_id)
        
        if feedback_list:
            # Calculate average rating
            avg_rating = sum(f.rating for f in feedback_list) / len(feedback_list)
            
            # Update generation
            content_repo = ContentGenerationRepository(self.db)
            generation = await content_repo.get(generation_id)
            if generation:
                generation.user_rating = avg_rating
                await self.db.commit()
                
    async def get_quality_report(
        self,
        generation_id: UUID
    ) -> Dict[str, Any]:
        """
        Get comprehensive quality report for a generation.
        
        Args:
            generation_id: Generation ID
            
        Returns:
            Quality report with metrics and feedback
        """
        # Get quality checks
        checks = await self.quality_repo.get_generation_quality_checks(generation_id)
        
        # Get user feedback
        feedback = await self.quality_repo.get_generation_feedback(generation_id)
        
        # Aggregate metrics
        report = {
            'generation_id': str(generation_id),
            'quality_checks': {
                'total': len(checks),
                'passed': sum(1 for c in checks if c.passed),
                'average_score': sum(c.overall_score for c in checks) / len(checks) if checks else 0
            },
            'user_feedback': {
                'count': len(feedback),
                'average_rating': sum(f.rating for f in feedback) / len(feedback) if feedback else 0,
                'ratings_distribution': {}
            },
            'metrics': {},
            'recommendations': []
        }
        
        # Get detailed metrics
        for check in checks:
            metrics = await self.quality_repo.get_quality_metrics(check.id)
            for metric in metrics:
                if metric.metric_name not in report['metrics']:
                    report['metrics'][metric.metric_name] = {
                        'values': [],
                        'average': 0,
                        'passed_count': 0
                    }
                report['metrics'][metric.metric_name]['values'].append(metric.metric_value)
                if metric.passed:
                    report['metrics'][metric.metric_name]['passed_count'] += 1
                    
        # Calculate metric averages
        for metric_name, data in report['metrics'].items():
            if data['values']:
                data['average'] = sum(data['values']) / len(data['values'])
                data['pass_rate'] = data['passed_count'] / len(data['values'])
                
        # Generate recommendations
        if report['quality_checks']['average_score'] < 0.8:
            report['recommendations'].append(
                "Overall quality score is below threshold. Consider reviewing content structure."
            )
            
        if report['user_feedback']['average_rating'] < 4:
            report['recommendations'].append(
                "User satisfaction is low. Review user feedback for improvement areas."
            )
            
        return report


class UserService:
    """Service for user management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        
    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None
    ) -> User:
        """
        Create a new user.
        
        Args:
            email: User email
            username: Username
            password: Plain text password
            full_name: Optional full name
            
        Returns:
            Created user
        """
        # Hash password
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(password)
        
        # Create user
        user = await self.user_repo.create_user(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name
        )
        
        # Create default role assignment
        role_repo = RoleRepository(self.db)
        user_role_repo = UserRoleRepository(self.db)
        
        # Get the default user role
        user_role = await role_repo.get_by_name("user")
        if user_role:
            await user_role_repo.assign_role(user.id, user_role.id)
        
        return user
        
    async def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user with username and password.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User if authentication successful, None otherwise
        """
        # Get user
        user = await self.user_repo.get_by_username(username)
        if not user:
            user = await self.user_repo.get_by_email(username)
            
        if not user:
            return None
            
        # Verify password
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        if not pwd_context.verify(password, user.hashed_password):
            return None
            
        return user
        
    async def create_access_token(
        self,
        user: User,
        expires_delta: Optional[int] = None
    ) -> str:
        """
        Create JWT access token for user.
        
        Args:
            user: User to create token for
            expires_delta: Token lifetime in seconds
            
        Returns:
            JWT token string
        """
        import jwt
        from datetime import timedelta
        
        # Token data
        now = datetime.utcnow()
        expires = now + timedelta(seconds=expires_delta or settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "exp": expires,
            "iat": now
        }
        
        # Create token
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return token


class AnalyticsService:
    """Service for analytics and reporting."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_repo = AnalyticsRepository(db)
        
    async def get_user_analytics(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific user.
        
        Args:
            user_id: User ID
            start_date: Start date for analytics
            end_date: End date for analytics
            
        Returns:
            Analytics data
        """
        # Get user activity
        activities = await self.analytics_repo.get_user_activities(
            user_id, start_date, end_date
        )
        
        # Get generation analytics
        generations = await self.analytics_repo.get_user_generation_analytics(
            user_id, start_date, end_date
        )
        
        # Aggregate data
        analytics = {
            'user_id': str(user_id),
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'activity': {
                'total_actions': len(activities),
                'unique_days': len(set(a.created_at.date() for a in activities)),
                'actions_by_type': {}
            },
            'generations': {
                'total': len(generations),
                'completed': sum(1 for g in generations if g.completed_at),
                'total_tokens': sum(g.tokens_used or 0 for g in generations),
                'average_duration': 0,
                'by_content_type': {}
            }
        }
        
        # Count actions by type
        for activity in activities:
            action = activity.action
            analytics['activity']['actions_by_type'][action] = \
                analytics['activity']['actions_by_type'].get(action, 0) + 1
                
        # Calculate generation metrics
        completed_gens = [g for g in generations if g.completed_at and g.started_at]
        if completed_gens:
            durations = [(g.completed_at - g.started_at).total_seconds() for g in completed_gens]
            analytics['generations']['average_duration'] = sum(durations) / len(durations)
            
        # Count by content type
        for gen in generations:
            content_type = gen.content_type
            analytics['generations']['by_content_type'][content_type] = \
                analytics['generations']['by_content_type'].get(content_type, 0) + 1
                
        return analytics
        
    async def get_platform_metrics(
        self,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get platform-wide metrics for a specific date.
        
        Args:
            date: Date to get metrics for (defaults to today)
            
        Returns:
            Platform metrics
        """
        if not date:
            date = datetime.utcnow().date()
            
        # Get or create daily metrics
        metrics = await self.analytics_repo.get_or_create_daily_metrics(date)
        
        return {
            'date': date.isoformat(),
            'users': {
                'active': metrics.active_users,
                'new': metrics.new_users
            },
            'generations': {
                'total': metrics.total_generations,
                'completed': metrics.completed_generations,
                'failed': metrics.failed_generations
            },
            'usage': {
                'total_tokens': metrics.total_tokens_used,
                'storage_gb': metrics.storage_used_gb
            },
            'revenue': {
                'daily': float(metrics.revenue_cents / 100) if metrics.revenue_cents else 0
            }
        }
