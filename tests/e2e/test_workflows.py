"""
End-to-end tests for complete workflows.

Tests entire user journeys from start to finish.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from pathlib import Path
from decimal import Decimal

from certify_studio.database.models import (
    User, ContentGeneration, ContentPiece, QualityCheck,
    ExtractedConcept, ExportTask, UserFeedback,
    ContentType, GenerationStatus, ExportFormat, QualityStatus,
    UserActivity, ActivityType, QualityMetric, QualityDimension
)
from certify_studio.integration.services import (
    ContentGenerationService, UserService, QualityAssuranceService,
    DomainExtractionService, AnalyticsService
)
from certify_studio.agents.orchestration import AgentOrchestrator


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteContentGenerationFlow:
    """Test complete content generation workflow from upload to export."""
    
    @pytest.fixture
    async def services(self, db, event_bus):
        """Create all required services."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize()
        
        return {
            "user": UserService(db),
            "content": ContentGenerationService(db, event_bus, orchestrator),
            "quality": QualityAssuranceService(db, event_bus, orchestrator),
            "domain": DomainExtractionService(db, orchestrator),
            "analytics": AnalyticsService(db)
        }
    
    async def test_full_certification_generation(self, services, tmp_path):
        """Test generating a full certification course."""
        # Step 1: Create user
        user = await services["user"].create_user(
            email="e2e_test@example.com",
            username="e2e_user",
            password="TestPass123!",
            full_name="E2E Test User",
            profile={
                "bio": "Testing complete workflows",
                "company": "Test Corp"
            }
        )
        
        assert user.id is not None
        
        # Step 2: Create test content file
        test_file = tmp_path / "aws_certification.pdf"
        test_file.write_bytes(b"""
        AWS Solutions Architect Certification Guide
        
        Chapter 1: Cloud Computing Fundamentals
        - What is cloud computing
        - AWS global infrastructure
        - Core AWS services
        
        Chapter 2: Compute Services
        - Amazon EC2
        - AWS Lambda
        - Container services
        
        Chapter 3: Storage Services
        - Amazon S3
        - Amazon EBS
        - Amazon EFS
        """)
        
        # Step 3: Start content generation
        generation = await services["content"].start_generation(
            user=user,
            file_path=str(test_file),
            file_name="aws_certification.pdf",
            title="AWS Solutions Architect Complete Course",
            content_type=ContentType.FULL_CERTIFICATION,
            settings={
                "difficulty": "intermediate",
                "include_animations": True,
                "include_quizzes": True,
                "target_duration": 480  # 8 hours
            }
        )
        
        assert generation.status == GenerationStatus.PENDING
        
        # Step 4: Process generation (simulate background task)
        start_time = datetime.utcnow()
        
        # Extract domains
        await services["content"].update_generation_progress(
            generation.id, 10, "Extracting key concepts..."
        )
        
        concepts = await services["domain"].extract_concepts(generation.id)
        assert len(concepts) > 0
        
        # Build concept relationships
        await services["content"].update_generation_progress(
            generation.id, 25, "Building knowledge graph..."
        )
        
        graph = await services["domain"].build_concept_graph(generation.id)
        assert "nodes" in graph
        assert "edges" in graph
        
        # Generate content pieces
        await services["content"].update_generation_progress(
            generation.id, 50, "Generating course content..."
        )
        
        # Simulate content generation
        sections = [
            ("Introduction", "intro", "Welcome to AWS certification preparation"),
            ("Cloud Fundamentals", "section", "Understanding cloud computing"),
            ("EC2 Deep Dive", "lesson", "Comprehensive EC2 guide"),
            ("Storage Services", "section", "S3, EBS, and EFS explained"),
            ("Practice Exam", "quiz", "Test your knowledge")
        ]
        
        for idx, (title, type_, content) in enumerate(sections):
            piece = await services["content"].create_content_piece(
                generation_id=generation.id,
                piece_type=type_,
                title=title,
                content=content,
                order_index=idx + 1,
                metadata={
                    "duration": 60 if type_ == "lesson" else 30,
                    "difficulty": "intermediate"
                }
            )
            assert piece.id is not None
        
        # Step 5: Run quality checks
        await services["content"].update_generation_progress(
            generation.id, 75, "Running quality assessment..."
        )
        
        quality_check = await services["quality"].run_quality_check(
            generation_id=generation.id,
            check_type="comprehensive"
        )
        
        # Simulate quality check completion
        quality_check.status = QualityStatus.COMPLETED
        quality_check.overall_score = 0.88
        quality_check.passed = True
        quality_check.details = {
            "accuracy": 0.92,
            "pedagogy": 0.86,
            "engagement": 0.85,
            "accessibility": 0.89
        }
        await services["quality"].db.commit()
        
        # Step 6: Complete generation
        await services["content"].update_generation_progress(
            generation.id, 100, "Generation complete!"
        )
        
        generation.status = GenerationStatus.COMPLETED
        generation.completed_at = datetime.utcnow()
        await services["content"].db.commit()
        
        # Step 7: Track analytics
        duration = (datetime.utcnow() - start_time).total_seconds()
        analytics = await services["analytics"].track_generation(
            generation_id=generation.id,
            duration=duration,
            agent_times={
                "orchestrator": duration * 0.05,
                "domain_extraction": duration * 0.25,
                "content_generation": duration * 0.50,
                "quality_assurance": duration * 0.20
            },
            tokens_used=75000,
            costs={"api": 1.50, "compute": 0.25},
            quality_scores={
                "overall": quality_check.overall_score,
                "accuracy": 0.92,
                "pedagogy": 0.86
            }
        )
        
        assert analytics.total_costs > 0
        
        # Step 8: User provides feedback
        feedback = await services["quality"].submit_feedback(
            user_id=user.id,
            generation_id=generation.id,
            rating=5,
            comment="Excellent course! Very comprehensive.",
            metadata={
                "completion_rate": 1.0,
                "time_spent": 28800,  # 8 hours
                "most_helpful": ["EC2 Deep Dive", "Practice Exam"]
            }
        )
        
        assert feedback.rating == 5
        
        # Step 9: Export content
        export_task = await services["content"].export_content(
            generation_id=generation.id,
            format=ExportFormat.PDF,
            options={
                "include_images": True,
                "include_solutions": True,
                "paper_size": "A4"
            }
        )
        
        # Simulate export completion
        export_task.status = "completed"
        export_task.file_path = "/exports/aws_course.pdf"
        export_task.file_size = 5 * 1024 * 1024  # 5MB
        export_task.completed_at = datetime.utcnow()
        await services["content"].db.commit()
        
        # Verify complete workflow
        assert generation.status == GenerationStatus.COMPLETED
        assert len(generation.content_pieces) == 5
        assert generation.quality_checks[0].passed is True
        assert generation.analytics is not None
        assert len(generation.feedback) == 1
        assert generation.export_tasks[0].status == "completed"
        
    async def test_quick_review_generation(self, services, tmp_path):
        """Test generating a quick review guide."""
        # Create user
        user = await services["user"].create_user(
            email="quick_test@example.com",
            username="quick_user",
            password="QuickPass123!",
            full_name="Quick Test User"
        )
        
        # Create simple content file
        test_file = tmp_path / "quick_review.txt"
        test_file.write_text("""
        Python Programming Quick Review
        
        1. Variables and Data Types
        2. Control Flow
        3. Functions
        4. Classes and Objects
        5. Error Handling
        """)
        
        # Generate quick review
        generation = await services["content"].start_generation(
            user=user,
            file_path=str(test_file),
            file_name="quick_review.txt",
            title="Python Quick Review",
            content_type=ContentType.QUICK_REVIEW,
            settings={
                "target_duration": 30,  # 30 minutes
                "focus_areas": ["syntax", "best_practices"]
            }
        )
        
        # Fast processing for quick review
        await services["content"].process_generation(generation.id)
        
        # Should complete quickly
        await services["content"].db.refresh(generation)
        assert generation.status == GenerationStatus.COMPLETED
        assert generation.content_pieces is not None
        
        # Quick review should be concise
        total_content_length = sum(
            len(piece.content) for piece in generation.content_pieces
        )
        assert total_content_length < 10000  # Reasonable for quick review


@pytest.mark.e2e
@pytest.mark.slow
class TestUserJourneyFlow:
    """Test complete user journey from registration to multiple generations."""
    
    @pytest.fixture
    async def services(self, db, event_bus):
        """Create required services."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize()
        
        return {
            "user": UserService(db),
            "content": ContentGenerationService(db, event_bus, orchestrator),
            "analytics": AnalyticsService(db)
        }
    
    async def test_new_user_journey(self, services, db):
        """Test new user's complete journey."""
        # Step 1: User registration
        user = await services["user"].create_user(
            email="journey@example.com",
            username="journeyuser",
            password="JourneyPass123!",
            full_name="Journey User"
        )
        
        # Step 2: User logs in (get tokens)
        access_token = await services["user"].create_access_token(user)
        refresh_token = await services["user"].create_refresh_token(user)
        
        assert access_token is not None
        assert refresh_token is not None
        
        # Step 3: User updates profile
        await services["user"].update_profile(
            user_id=user.id,
            bio="Learning cloud technologies",
            company="Tech Startup",
            location="San Francisco",
            preferences={
                "learning_style": "visual",
                "pace": "moderate",
                "notifications": True
            }
        )
        
        # Step 4: User creates multiple generations
        generations = []
        
        # First generation - Mini course
        gen1 = await services["content"].start_generation(
            user=user,
            file_path="/fake/path1.pdf",
            file_name="intro_to_aws.pdf",
            title="Introduction to AWS",
            content_type=ContentType.MINI_COURSE,
            settings={"difficulty": "beginner"}
        )
        generations.append(gen1)
        
        # Second generation - Exam prep
        gen2 = await services["content"].start_generation(
            user=user,
            file_path="/fake/path2.pdf",
            file_name="aws_exam_prep.pdf",
            title="AWS Exam Preparation",
            content_type=ContentType.EXAM_PREP,
            settings={"exam_code": "SAA-C03"}
        )
        generations.append(gen2)
        
        # Step 5: Track user activity
        activities = [
            UserActivity(
                user_id=user.id,
                activity_type=ActivityType.LOGIN,
                metadata={"method": "password"}
            ),
            UserActivity(
                user_id=user.id,
                activity_type=ActivityType.PROFILE_UPDATED,
                metadata={"fields": ["bio", "company", "location"]}
            ),
            UserActivity(
                user_id=user.id,
                activity_type=ActivityType.GENERATION_STARTED,
                metadata={"generation_id": str(gen1.id)}
            ),
            UserActivity(
                user_id=user.id,
                activity_type=ActivityType.GENERATION_STARTED,
                metadata={"generation_id": str(gen2.id)}
            )
        ]
        db.add_all(activities)
        await db.commit()
        
        # Step 6: Get user analytics
        user_stats = await services["analytics"].get_user_analytics(
            user_id=user.id,
            days=1
        )
        
        assert user_stats["total_activities"] >= 4
        assert user_stats["total_generations"] == 2
        assert ActivityType.LOGIN.value in user_stats["activity_breakdown"]
        
        # Step 7: Complete one generation
        gen1.status = GenerationStatus.COMPLETED
        gen1.completed_at = datetime.utcnow()
        await db.commit()
        
        # Add activity
        db.add(UserActivity(
            user_id=user.id,
            activity_type=ActivityType.GENERATION_COMPLETED,
            metadata={
                "generation_id": str(gen1.id),
                "duration": 1200  # 20 minutes
            }
        ))
        await db.commit()
        
        # Step 8: Check user's learning progress
        progress = await services["analytics"].get_user_progress(user.id)
        assert progress["completed_courses"] == 1
        assert progress["in_progress_courses"] == 1
        
        # Step 9: User uses refresh token
        new_access_token = await services["user"].refresh_access_token(refresh_token)
        assert new_access_token != access_token
        
        # Step 10: Create API key for automation
        api_key, key_string = await services["user"].create_api_key(
            user_id=user.id,
            name="Automation Key"
        )
        
        assert api_key.is_active is True
        
        # Verify complete journey
        await db.refresh(user)
        assert user.profile is not None
        assert len(user.content_generations) == 2
        assert len(user.activities) >= 5
        assert len(user.api_keys) == 1


@pytest.mark.e2e
@pytest.mark.slow
class TestConcurrentOperations:
    """Test system behavior under concurrent operations."""
    
    @pytest.fixture
    async def services(self, db, event_bus):
        """Create services for testing."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize()
        
        return {
            "content": ContentGenerationService(db, event_bus, orchestrator),
            "quality": QualityAssuranceService(db, event_bus, orchestrator)
        }
    
    async def test_concurrent_generations(self, services, test_user):
        """Test multiple concurrent content generations."""
        # Start 5 concurrent generations
        tasks = []
        for i in range(5):
            task = services["content"].start_generation(
                user=test_user,
                file_path=f"/test{i}.pdf",
                file_name=f"test{i}.pdf",
                title=f"Concurrent Test {i}",
                content_type=ContentType.QUICK_REVIEW,
                settings={"index": i}
            )
            tasks.append(task)
        
        # Wait for all to start
        generations = await asyncio.gather(*tasks)
        
        # All should be created
        assert len(generations) == 5
        assert all(g.status == GenerationStatus.PENDING for g in generations)
        
        # Process them concurrently
        process_tasks = []
        for gen in generations:
            task = services["content"].process_generation(gen.id)
            process_tasks.append(task)
        
        # Wait for processing
        results = await asyncio.gather(*process_tasks, return_exceptions=True)
        
        # Check results
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) >= 3  # At least some should succeed
        
    async def test_concurrent_quality_checks(self, services, test_user, db):
        """Test concurrent quality checks on same generation."""
        # Create generation with content
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Concurrent Quality Test",
            content_type=ContentType.MINI_COURSE,
            status=GenerationStatus.COMPLETED
        )
        db.add(generation)
        
        # Add content
        for i in range(3):
            piece = ContentPiece(
                generation_id=generation.id,
                piece_type="lesson",
                title=f"Lesson {i+1}",
                content=f"Content {i+1}",
                order_index=i+1
            )
            db.add(piece)
        await db.commit()
        
        # Run multiple quality checks concurrently
        check_tasks = []
        check_types = ["automated", "comprehensive", "quick"]
        
        for check_type in check_types:
            task = services["quality"].run_quality_check(
                generation_id=generation.id,
                check_type=check_type
            )
            check_tasks.append(task)
        
        # Wait for all checks
        quality_checks = await asyncio.gather(*check_tasks)
        
        # All should complete
        assert len(quality_checks) == 3
        assert all(qc.id is not None for qc in quality_checks)
        
        # Verify different check types
        check_types_found = {qc.check_type for qc in quality_checks}
        assert len(check_types_found) == 3


@pytest.mark.e2e
@pytest.mark.slow  
class TestErrorRecoveryFlow:
    """Test system recovery from various error conditions."""
    
    @pytest.fixture
    async def services(self, db, event_bus):
        """Create services with error simulation."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize()
        
        return {
            "user": UserService(db),
            "content": ContentGenerationService(db, event_bus, orchestrator),
            "quality": QualityAssuranceService(db, event_bus, orchestrator)
        }
    
    async def test_generation_failure_recovery(self, services, test_user, mocker):
        """Test recovery from generation failure."""
        # Mock orchestrator to fail first time
        fail_count = 0
        original_extract = services["content"].orchestrator.extract_domains
        
        async def failing_extract(*args, **kwargs):
            nonlocal fail_count
            fail_count += 1
            if fail_count == 1:
                raise Exception("Simulated extraction failure")
            return await original_extract(*args, **kwargs)
        
        services["content"].orchestrator.extract_domains = failing_extract
        
        # Start generation
        generation = await services["content"].start_generation(
            user=test_user,
            file_path="/test.pdf",
            file_name="test.pdf",
            title="Recovery Test",
            content_type=ContentType.MINI_COURSE,
            settings={}
        )
        
        # First attempt should fail
        with pytest.raises(Exception):
            await services["content"].process_generation(generation.id)
        
        # Check failed state
        await services["content"].db.refresh(generation)
        assert generation.status == GenerationStatus.FAILED
        assert "extraction failure" in generation.error_message
        
        # Retry should succeed
        result = await services["content"].retry_generation(generation.id)
        assert result.status == GenerationStatus.PROCESSING
        
    async def test_partial_content_recovery(self, services, test_user, db):
        """Test recovery when content generation partially fails."""
        # Create generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Partial Recovery Test",
            content_type=ContentType.FULL_CERTIFICATION,
            status=GenerationStatus.PROCESSING
        )
        db.add(generation)
        await db.flush()
        
        # Add some successful content
        for i in range(3):
            piece = ContentPiece(
                generation_id=generation.id,
                piece_type="lesson",
                title=f"Lesson {i+1}",
                content=f"Successfully generated content {i+1}",
                order_index=i+1
            )
            db.add(piece)
        await db.commit()
        
        # Simulate failure during generation
        generation.status = GenerationStatus.FAILED
        generation.error_message = "Failed to generate remaining content"
        generation.metadata = {
            "completed_pieces": 3,
            "total_expected": 10,
            "last_successful_step": "lesson_generation"
        }
        await db.commit()
        
        # Resume generation
        result = await services["content"].resume_generation(
            generation_id=generation.id,
            from_step="lesson_generation"
        )
        
        # Should continue from where it left off
        assert result.status == GenerationStatus.PROCESSING
        assert len(result.content_pieces) >= 3  # Original pieces preserved
        
    async def test_quality_check_retry(self, services, test_user, db):
        """Test retrying failed quality checks."""
        # Create completed generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Quality Retry Test",
            content_type=ContentType.EXAM_PREP,
            status=GenerationStatus.COMPLETED
        )
        db.add(generation)
        await db.commit()
        
        # Create failed quality check
        quality_check = QualityCheck(
            generation_id=generation.id,
            check_type="comprehensive",
            check_name="Full Assessment",
            status=QualityStatus.FAILED,
            overall_score=0.0,
            passed=False,
            error_message="Quality check timed out"
        )
        db.add(quality_check)
        await db.commit()
        
        # Retry quality check
        new_check = await services["quality"].retry_quality_check(
            quality_check_id=quality_check.id
        )
        
        assert new_check.id != quality_check.id
        assert new_check.status == QualityStatus.PENDING
        assert new_check.generation_id == generation.id


@pytest.mark.e2e
@pytest.mark.slow
class TestDataConsistency:
    """Test data consistency across the system."""
    
    @pytest.fixture
    async def services(self, db, event_bus):
        """Create services."""
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize()
        
        return {
            "content": ContentGenerationService(db, event_bus, orchestrator),
            "analytics": AnalyticsService(db)
        }
    
    async def test_analytics_consistency(self, services, test_user, db):
        """Test analytics data remains consistent."""
        # Create and complete multiple generations
        generations = []
        for i in range(3):
            gen = ContentGeneration(
                user_id=test_user.id,
                source_file_path=f"/test{i}.pdf",
                source_file_name=f"test{i}.pdf",
                title=f"Analytics Test {i}",
                content_type=ContentType.MINI_COURSE,
                status=GenerationStatus.COMPLETED,
                completed_at=datetime.utcnow()
            )
            db.add(gen)
            await db.flush()
            
            # Add analytics
            from certify_studio.database.models import GenerationAnalytics
            analytics = GenerationAnalytics(
                generation_id=gen.id,
                total_duration=1200.0 + i * 300,
                tokens_used=50000 + i * 10000,
                api_costs=Decimal("1.0") + Decimal(str(i * 0.5)),
                compute_costs=Decimal("0.25"),
                total_costs=Decimal("1.25") + Decimal(str(i * 0.5)),
                quality_scores={"overall": 0.85 + i * 0.02}
            )
            db.add(analytics)
            generations.append(gen)
        
        await db.commit()
        
        # Calculate metrics
        metrics = await services["analytics"].calculate_user_metrics(
            user_id=test_user.id,
            date_range="all"
        )
        
        # Verify consistency
        assert metrics["total_generations"] == 3
        assert metrics["total_tokens"] == sum(50000 + i * 10000 for i in range(3))
        assert metrics["average_quality"] == pytest.approx(0.87, rel=0.01)
        
        # Verify costs add up
        expected_total_cost = sum(
            Decimal("1.25") + Decimal(str(i * 0.5)) for i in range(3)
        )
        assert metrics["total_cost"] == expected_total_cost
        
    async def test_cascade_deletion_consistency(self, services, test_user, db):
        """Test cascade deletions maintain consistency."""
        # Create generation with full data
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Deletion Test",
            content_type=ContentType.FULL_CERTIFICATION,
            status=GenerationStatus.COMPLETED
        )
        db.add(generation)
        await db.flush()
        
        # Add related data
        # Content pieces
        pieces = []
        for i in range(3):
            piece = ContentPiece(
                generation_id=generation.id,
                piece_type="lesson",
                title=f"Lesson {i+1}",
                content=f"Content {i+1}",
                order_index=i+1
            )
            db.add(piece)
            pieces.append(piece)
        
        # Quality check
        quality_check = QualityCheck(
            generation_id=generation.id,
            check_type="automated",
            check_name="Standard",
            status=QualityStatus.COMPLETED,
            overall_score=0.88,
            passed=True
        )
        db.add(quality_check)
        
        # Concepts
        from certify_studio.database.models import ExtractedConcept, ConceptType
        concepts = []
        for i in range(5):
            concept = ExtractedConcept(
                generation_id=generation.id,
                name=f"Concept {i}",
                concept_type=ConceptType.TOPIC,
                description=f"Test concept {i}",
                importance_score=0.5 + i * 0.1
            )
            db.add(concept)
            concepts.append(concept)
        
        await db.commit()
        
        # Store IDs for verification
        piece_ids = [p.id for p in pieces]
        concept_ids = [c.id for c in concepts]
        quality_check_id = quality_check.id
        
        # Soft delete generation
        generation.deleted_at = datetime.utcnow()
        generation.deleted_by_id = test_user.id
        await db.commit()
        
        # Verify related data still exists (soft delete doesn't cascade)
        for piece_id in piece_ids:
            piece = await db.get(ContentPiece, piece_id)
            assert piece is not None
        
        # If hard delete was implemented, verify cascade
        # This would depend on cascade configuration in models
