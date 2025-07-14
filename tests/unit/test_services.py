"""
Unit tests for service layer.

Tests business logic, workflows, and service methods.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4
from decimal import Decimal

from certify_studio.integration.services import (
    ContentGenerationService,
    UserService,
    QualityAssuranceService,
    DomainExtractionService,
    AnalyticsService
)
from certify_studio.database.models import (
    User, ContentGeneration, ContentPiece, QualityCheck,
    ExtractedConcept, GenerationAnalytics,
    ContentType, GenerationStatus, QualityStatus,
    MetricType, ActivityType, BloomLevel,
    QualityDimension, ExportFormat, FeedbackType
)
from certify_studio.integration.events import EventType


@pytest.mark.unit
class TestContentGenerationService:
    """Test content generation service."""
    
    @pytest.fixture
    def service(self, db, event_bus, mock_orchestrator):
        """Create service instance with mocks."""
        return ContentGenerationService(db, event_bus, mock_orchestrator)
    
    async def test_start_generation(self, service, test_user, tmp_path):
        """Test starting a new content generation."""
        # Create test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"test content")
        
        # Start generation
        generation = await service.start_generation(
            user=test_user,
            file_path=str(test_file),
            file_name="test.pdf",
            title="Test Course",
            content_type=ContentType.MINI_COURSE,
            settings={"difficulty": "intermediate"}
        )
        
        assert generation.id is not None
        assert generation.status == GenerationStatus.PENDING
        assert generation.title == "Test Course"
        assert generation.settings["difficulty"] == "intermediate"
        
        # Verify event was emitted
        assert service.event_bus.emit.called
        emit_call = service.event_bus.emit.call_args[0]
        assert emit_call[0] == EventType.GENERATION_STARTED
        
    async def test_process_generation_workflow(self, service, test_user, mocker):
        """Test complete generation workflow."""
        # Create generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test",
            content_type=ContentType.QUICK_REVIEW,
            status=GenerationStatus.PENDING
        )
        service.db.add(generation)
        await service.db.commit()
        
        # Mock orchestrator methods
        service.orchestrator.extract_domains = AsyncMock(return_value={
            "concepts": [
                {
                    "name": "Test Concept",
                    "type": "topic",
                    "importance": 0.9,
                    "description": "A test concept"
                }
            ],
            "relationships": []
        })
        
        service.orchestrator.generate_content = AsyncMock(return_value={
            "sections": [
                {
                    "title": "Introduction",
                    "content": "Welcome to the course",
                    "type": "lesson"
                }
            ]
        })
        
        service.orchestrator.check_quality = AsyncMock(return_value={
            "overall_score": 0.85,
            "passed": True,
            "metrics": {
                "accuracy": 0.9,
                "pedagogy": 0.85,
                "engagement": 0.8
            }
        })
        
        # Process generation
        result = await service.process_generation(generation.id)
        
        assert result.status == GenerationStatus.COMPLETED
        assert result.progress == 100
        
        # Verify concepts were saved
        concepts = await service.db.execute(
            "SELECT * FROM extracted_concepts WHERE generation_id = :gen_id",
            {"gen_id": generation.id}
        )
        assert len(concepts.fetchall()) > 0
        
        # Verify content was saved
        content = await service.db.execute(
            "SELECT * FROM content_pieces WHERE generation_id = :gen_id",
            {"gen_id": generation.id}
        )
        assert len(content.fetchall()) > 0
        
        # Verify quality check was performed
        quality = await service.db.execute(
            "SELECT * FROM quality_checks WHERE generation_id = :gen_id",
            {"gen_id": generation.id}
        )
        assert len(quality.fetchall()) > 0
        
    async def test_handle_generation_failure(self, service, test_user):
        """Test handling generation failures."""
        # Create generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test",
            content_type=ContentType.EXAM_PREP,
            status=GenerationStatus.PROCESSING
        )
        service.db.add(generation)
        await service.db.commit()
        
        # Mock orchestrator to raise error
        service.orchestrator.extract_domains = AsyncMock(
            side_effect=Exception("Processing failed")
        )
        
        # Process should handle error gracefully
        with pytest.raises(Exception):
            await service.process_generation(generation.id)
        
        # Verify generation marked as failed
        await service.db.refresh(generation)
        assert generation.status == GenerationStatus.FAILED
        assert "Processing failed" in generation.error_message
        
        # Verify failure event emitted
        assert service.event_bus.emit.called
        emit_calls = [call[0] for call in service.event_bus.emit.call_args_list]
        assert EventType.GENERATION_FAILED in [call[0] for call in emit_calls]
        
    async def test_export_content(self, service, test_user):
        """Test content export functionality."""
        # Create completed generation with content
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Export Test",
            content_type=ContentType.MINI_COURSE,
            status=GenerationStatus.COMPLETED
        )
        service.db.add(generation)
        await service.db.flush()
        
        # Add content
        content = ContentPiece(
            generation_id=generation.id,
            piece_type="lesson",
            title="Test Lesson",
            content="Test content for export",
            order_index=1,
            metadata={"duration": 300}
        )
        service.db.add(content)
        await service.db.commit()
        
        # Mock export methods
        with patch.object(service, '_export_to_pdf', new_callable=AsyncMock) as mock_pdf:
            mock_pdf.return_value = "/exports/test.pdf"
            
            export_task = await service.export_content(
                generation_id=generation.id,
                format=ExportFormat.PDF,
                options={"include_images": True}
            )
            
            assert export_task.id is not None
            assert export_task.format == ExportFormat.PDF
            assert export_task.options["include_images"] is True
            
            # Process export
            result = await service.process_export(export_task.id)
            assert result.status == "completed"
            assert result.file_path == "/exports/test.pdf"


@pytest.mark.unit
class TestUserService:
    """Test user service."""
    
    @pytest.fixture
    def service(self, db):
        """Create service instance."""
        return UserService(db)
    
    async def test_create_user(self, service):
        """Test user creation with profile."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePass123!",
            "full_name": "New User",
            "profile": {
                "bio": "Software developer",
                "company": "Tech Corp",
                "location": "San Francisco"
            }
        }
        
        user = await service.create_user(**user_data)
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.profile is not None
        assert user.profile.bio == "Software developer"
        
        # Verify password is hashed
        assert user.hashed_password != "SecurePass123!"
        assert await service.verify_password("SecurePass123!", user.hashed_password)
        
    async def test_authenticate_user(self, service, test_user):
        """Test user authentication."""
        # Set known password
        test_user.hashed_password = service.get_password_hash("testpass123")
        await service.db.commit()
        
        # Test valid credentials
        authenticated = await service.authenticate_user("testuser", "testpass123")
        assert authenticated is not None
        assert authenticated.id == test_user.id
        
        # Test invalid password
        authenticated = await service.authenticate_user("testuser", "wrongpass")
        assert authenticated is None
        
        # Test invalid username
        authenticated = await service.authenticate_user("nonexistent", "testpass123")
        assert authenticated is None
        
    async def test_token_management(self, service, test_user):
        """Test JWT token creation and validation."""
        # Create access token
        access_token = await service.create_access_token(test_user)
        assert access_token is not None
        
        # Validate token
        payload = service.decode_token(access_token)
        assert payload is not None
        assert payload.get("sub") == test_user.email
        assert payload.get("user_id") == str(test_user.id)
        
        # Create refresh token
        refresh_token = await service.create_refresh_token(test_user)
        assert refresh_token is not None
        
        # Use refresh token
        new_access_token = await service.refresh_access_token(refresh_token)
        assert new_access_token is not None
        assert new_access_token != access_token
        
    async def test_role_management(self, service, test_user):
        """Test role assignment and permission checking."""
        # Create role
        from certify_studio.database.models import Role, Permission
        
        editor_role = Role(
            name="editor",
            description="Content editor"
        )
        service.db.add(editor_role)
        await service.db.flush()
        
        # Add permissions
        permissions = [
            Permission(resource="content", action="create"),
            Permission(resource="content", action="edit"),
            Permission(resource="content", action="delete")
        ]
        service.db.add_all(permissions)
        await service.db.flush()
        
        editor_role.permissions.extend(permissions)
        await service.db.commit()
        
        # Assign role
        await service.assign_role(test_user.id, "editor")
        
        # Check permissions
        has_perm = await service.user_has_permission(
            test_user.id, "content", "edit"
        )
        assert has_perm is True
        
        has_perm = await service.user_has_permission(
            test_user.id, "users", "delete"
        )
        assert has_perm is False
        
    async def test_api_key_management(self, service, test_user):
        """Test API key creation and validation."""
        # Create API key
        api_key, key_string = await service.create_api_key(
            user_id=test_user.id,
            name="Test API Key"
        )
        
        assert api_key.id is not None
        assert key_string is not None
        assert api_key.key_hash != key_string
        
        # Validate API key
        validated_user = await service.get_user_by_api_key(key_string)
        assert validated_user is not None
        assert validated_user.id == test_user.id
        
        # Update last used
        await service.update_api_key_last_used(api_key.id)
        await service.db.refresh(api_key)
        assert api_key.last_used_at is not None
        
        # Deactivate key
        await service.deactivate_api_key(api_key.id)
        await service.db.refresh(api_key)
        assert api_key.is_active is False
        
        # Validation should fail
        validated_user = await service.get_user_by_api_key(key_string)
        assert validated_user is None


@pytest.mark.unit
class TestQualityAssuranceService:
    """Test quality assurance service."""
    
    @pytest.fixture
    def service(self, db, event_bus, mock_orchestrator):
        """Create service instance."""
        return QualityAssuranceService(db, event_bus, mock_orchestrator)
    
    async def test_run_quality_check(self, service, test_user):
        """Test running quality checks."""
        # Create generation with content
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Quality Test",
            content_type=ContentType.FULL_CERTIFICATION,
            status=GenerationStatus.COMPLETED
        )
        service.db.add(generation)
        await service.db.flush()
        
        content = ContentPiece(
            generation_id=generation.id,
            piece_type="lesson",
            title="Test Lesson",
            content="Content to check",
            order_index=1
        )
        service.db.add(content)
        await service.db.commit()
        
        # Mock quality check results
        service.orchestrator.check_quality = AsyncMock(return_value={
            "overall_score": 0.88,
            "passed": True,
            "metrics": {
                "accuracy": 0.92,
                "pedagogy": 0.86,
                "engagement": 0.85,
                "accessibility": 0.89
            },
            "issues": [
                {
                    "type": "clarity",
                    "severity": "low",
                    "location": "paragraph 2",
                    "description": "Technical term needs definition"
                }
            ]
        })
        
        # Run quality check
        quality_check = await service.run_quality_check(
            generation_id=generation.id,
            check_type="comprehensive"
        )
        
        assert quality_check.id is not None
        assert quality_check.overall_score == 0.88
        assert quality_check.passed is True
        assert quality_check.status == QualityStatus.COMPLETED
        
        # Verify metrics saved
        assert len(quality_check.metrics) == 4
        accuracy_metric = next(m for m in quality_check.metrics if m.dimension == QualityDimension.ACCURACY)
        assert accuracy_metric.score == 0.92
        
        # Verify issues saved
        assert len(quality_check.issues) == 1
        assert quality_check.issues[0].severity.value == "low"
        
    async def test_process_user_feedback(self, service, test_user):
        """Test processing user feedback."""
        # Create generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Feedback Test",
            content_type=ContentType.MINI_COURSE,
            status=GenerationStatus.COMPLETED
        )
        service.db.add(generation)
        await service.db.commit()
        
        # Submit feedback
        feedback = await service.submit_feedback(
            user_id=test_user.id,
            generation_id=generation.id,
            rating=4,
            comment="Good content but needs more examples",
            metadata={
                "completion_rate": 0.75,
                "helpful_sections": ["intro", "concepts"],
                "suggestions": ["Add more practical examples", "Include diagrams"]
            }
        )
        
        assert feedback.id is not None
        assert feedback.rating == 4
        assert feedback.metadata["completion_rate"] == 0.75
        
        # Aggregate feedback
        summary = await service.get_feedback_summary(generation.id)
        assert summary["total_feedback"] == 1
        assert summary["average_rating"] == 4.0
        
    async def test_quality_benchmarking(self, service):
        """Test quality benchmarking."""
        # Create benchmark
        from certify_studio.database.models import QualityBenchmark
        
        benchmark = QualityBenchmark(
            name="Industry Standard",
            content_type=ContentType.FULL_CERTIFICATION,
            dimension="overall",
            target_score=0.85,
            description="Industry standard for certification content"
        )
        service.db.add(benchmark)
        await service.db.commit()
        
        # Compare against benchmark
        scores = {
            "accuracy": 0.88,
            "pedagogy": 0.82,
            "engagement": 0.79,
            "overall": 0.83
        }
        
        comparison = await service.compare_to_benchmark(
            scores=scores,
            content_type=ContentType.FULL_CERTIFICATION
        )
        
        assert comparison["overall"]["score"] == 0.83
        assert comparison["overall"]["target"] == 0.85
        assert comparison["overall"]["meets_benchmark"] is False
        assert comparison["overall"]["gap"] == -0.02


@pytest.mark.unit
class TestDomainExtractionService:
    """Test domain extraction service."""
    
    @pytest.fixture
    def service(self, db, mock_orchestrator):
        """Create service instance."""
        return DomainExtractionService(db, mock_orchestrator)
    
    async def test_extract_concepts(self, service, test_user):
        """Test concept extraction from content."""
        # Create generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Domain Test",
            content_type=ContentType.FULL_CERTIFICATION
        )
        service.db.add(generation)
        await service.db.commit()
        
        # Mock extraction results
        service.orchestrator.extract_domains = AsyncMock(return_value={
            "concepts": [
                {
                    "name": "Cloud Computing",
                    "type": "topic",
                    "description": "Computing services over the internet",
                    "importance": 0.95,
                    "difficulty": 0.3,
                    "embeddings": [0.1] * 384
                },
                {
                    "name": "EC2",
                    "type": "service",
                    "description": "Elastic Compute Cloud",
                    "importance": 0.9,
                    "difficulty": 0.5,
                    "embeddings": [0.2] * 384
                }
            ],
            "relationships": [
                {
                    "source": "Cloud Computing",
                    "target": "EC2",
                    "type": "contains",
                    "strength": 0.8
                }
            ]
        })
        
        # Extract concepts
        concepts = await service.extract_concepts(generation.id)
        
        assert len(concepts) == 2
        assert concepts[0].name == "Cloud Computing"
        assert concepts[0].importance_score == 0.95
        assert len(concepts[0].embeddings) == 384
        
        # Verify relationships saved
        from certify_studio.database.models import ConceptRelationship
        relationships = await service.db.execute(
            f"SELECT * FROM {ConceptRelationship.__tablename__}"
        )
        assert len(relationships.fetchall()) > 0
        
    async def test_find_canonical_concepts(self, service):
        """Test canonical concept matching."""
        # Create canonical concepts
        from certify_studio.database.models import CanonicalConcept, ConceptType
        
        canonical_ec2 = CanonicalConcept(
            name="Amazon EC2",
            concept_type=ConceptType.SERVICE,
            description="Amazon Elastic Compute Cloud",
            domain="AWS",
            embeddings=[0.2] * 384
        )
        service.db.add(canonical_ec2)
        await service.db.commit()
        
        # Test matching
        matches = await service.find_canonical_match(
            name="EC2 Instances",
            embeddings=[0.21] * 384,  # Similar embeddings
            threshold=0.8
        )
        
        assert matches is not None
        assert matches.name == "Amazon EC2"
        
    async def test_build_concept_graph(self, service, test_user):
        """Test concept graph construction."""
        # Create concepts
        from certify_studio.database.models import ExtractedConcept, ConceptType
        
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Graph Test",
            content_type=ContentType.MINI_COURSE
        )
        service.db.add(generation)
        await service.db.flush()
        
        concepts = []
        for i in range(5):
            concept = ExtractedConcept(
                generation_id=generation.id,
                name=f"Concept {i}",
                concept_type=ConceptType.TOPIC,
                description=f"Test concept {i}",
                importance_score=0.5 + i * 0.1
            )
            concepts.append(concept)
        service.db.add_all(concepts)
        await service.db.commit()
        
        # Build graph
        graph = await service.build_concept_graph(generation.id)
        
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) == 5
        
        # Test graph traversal
        path = await service.find_learning_path(
            start_concept_id=concepts[0].id,
            end_concept_id=concepts[4].id,
            max_length=5
        )
        
        assert path is not None
        assert len(path) <= 5


@pytest.mark.unit
class TestAnalyticsService:
    """Test analytics service."""
    
    @pytest.fixture
    def service(self, db):
        """Create service instance."""
        return AnalyticsService(db)
    
    async def test_track_generation_analytics(self, service, test_user):
        """Test tracking generation analytics."""
        # Create generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Analytics Test",
            content_type=ContentType.FULL_CERTIFICATION,
            status=GenerationStatus.COMPLETED,
            completed_at=datetime.utcnow()
        )
        service.db.add(generation)
        await service.db.commit()
        
        # Track analytics
        analytics = await service.track_generation(
            generation_id=generation.id,
            duration=3600.0,
            agent_times={
                "orchestrator": 120.0,
                "domain_extraction": 900.0,
                "content_generation": 1800.0,
                "quality_assurance": 780.0
            },
            tokens_used=150000,
            costs={
                "api": 2.50,
                "compute": 0.75
            },
            quality_scores={
                "accuracy": 0.92,
                "pedagogy": 0.88,
                "engagement": 0.85
            }
        )
        
        assert analytics.id is not None
        assert analytics.total_duration == 3600.0
        assert analytics.total_costs == Decimal("3.25")
        assert analytics.tokens_used == 150000
        
    async def test_get_user_analytics(self, service, test_user):
        """Test retrieving user analytics."""
        # Create some activity
        from certify_studio.database.models import UserActivity
        
        activities = [
            UserActivity(
                user_id=test_user.id,
                activity_type=ActivityType.LOGIN,
                metadata={"ip": "192.168.1.1"}
            ),
            UserActivity(
                user_id=test_user.id,
                activity_type=ActivityType.GENERATION_STARTED,
                metadata={"content_type": "mini_course"}
            ),
            UserActivity(
                user_id=test_user.id,
                activity_type=ActivityType.GENERATION_COMPLETED,
                metadata={"duration": 2400}
            )
        ]
        service.db.add_all(activities)
        await service.db.commit()
        
        # Get analytics
        user_stats = await service.get_user_analytics(
            user_id=test_user.id,
            days=30
        )
        
        assert user_stats["total_generations"] >= 0
        assert user_stats["total_activities"] == 3
        assert "activity_breakdown" in user_stats
        assert user_stats["activity_breakdown"][ActivityType.LOGIN.value] == 1
        
    async def test_daily_metrics_aggregation(self, service):
        """Test daily metrics calculation."""
        # Create test data
        today = datetime.utcnow().date()
        
        from certify_studio.database.models import (
            GenerationAnalytics, DailyMetrics
        )
        
        # Create some generations for today
        for i in range(5):
            analytics = GenerationAnalytics(
                generation_id=uuid4(),
                total_duration=2400.0 + i * 300,
                tokens_used=100000 + i * 10000,
                api_costs=Decimal("2.0") + Decimal(str(i * 0.5)),
                compute_costs=Decimal("0.5") + Decimal(str(i * 0.1)),
                total_costs=Decimal("2.5") + Decimal(str(i * 0.6)),
                quality_scores={"overall": 0.85 + i * 0.02}
            )
            service.db.add(analytics)
        await service.db.commit()
        
        # Calculate daily metrics
        metrics = await service.calculate_daily_metrics(today)
        
        assert metrics is not None
        assert metrics.date == today
        assert metrics.total_count == 5
        assert metrics.average_duration > 0
        assert metrics.total_cost > 0
        
    async def test_performance_tracking(self, service):
        """Test performance metric tracking."""
        # Track API performance
        await service.track_api_performance(
            endpoint="/api/v1/content/generate",
            method="POST",
            response_time=245.5,
            status_code=200,
            user_id=None,
            metadata={"content_type": "mini_course"}
        )
        
        # Get performance stats
        stats = await service.get_endpoint_stats(
            endpoint="/api/v1/content/generate",
            hours=24
        )
        
        assert stats["total_requests"] == 1
        assert stats["average_response_time"] == 245.5
        assert stats["success_rate"] == 1.0
        
    async def test_business_metrics(self, service, test_user):
        """Test custom business metrics."""
        # Define custom metric
        await service.define_business_metric(
            name="user_engagement_score",
            description="Composite score of user engagement",
            calculation_method="weighted_average",
            components=[
                {"metric": "login_frequency", "weight": 0.2},
                {"metric": "content_generated", "weight": 0.5},
                {"metric": "feedback_given", "weight": 0.3}
            ]
        )
        
        # Calculate metric
        score = await service.calculate_business_metric(
            metric_name="user_engagement_score",
            user_id=test_user.id
        )
        
        assert score is not None
        assert 0 <= score <= 1
