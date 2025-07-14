"""
Unit tests for database models.

Tests model creation, validation, relationships, and methods.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from decimal import Decimal

from certify_studio.database.models import (
    # User models
    User, Role, Permission, UserRole, UserPermission,
    UserProfile, UserSettings, RefreshToken, PasswordResetToken,
    APIKey, OAuthConnection,
    
    # Content models
    ContentGeneration, ContentPiece, MediaAsset, MediaReference,
    ContentInteraction, ExportTask, ContentVersion,
    
    # Domain models
    ExtractedConcept, CanonicalConcept, ConceptRelationship,
    LearningObjective, PrerequisiteMapping, LearningPath,
    DomainTaxonomy,
    
    # Quality models
    QualityCheck, QualityMetric, QualityIssue, QualityBenchmark,
    UserFeedback, ConceptQualityScore, ContentImprovement,
    QualityReport,
    
    # Analytics models
    UserActivity, GenerationAnalytics, DailyMetrics, FeatureUsage,
    PerformanceMetric, BusinessMetric, UserSegment, ABTestExperiment,
    
    # Enums
    ContentType, GenerationStatus, QualityStatus, ExportFormat,
    InteractionType, MetricType, ActivityType, BloomLevel,
    RelationshipType, IssueType, IssueSeverity, FeedbackType,
    ConceptType, QualityDimension, ImprovementStatus,
    ContentFormat
)


@pytest.mark.unit
class TestUserModels:
    """Test user-related models."""
    
    async def test_user_creation(self, db):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            full_name="Test User"
        )
        db.add(user)
        await db.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at is not None
        
    async def test_user_role_assignment(self, db, test_user):
        """Test assigning roles to users."""
        # Create role
        role = Role(
            name="editor",
            description="Can edit content"
        )
        db.add(role)
        await db.flush()
        
        # Create permissions
        perm1 = Permission(resource="content", action="edit")
        perm2 = Permission(resource="content", action="publish")
        db.add_all([perm1, perm2])
        await db.flush()
        
        # Add permissions to role
        role.permissions.extend([perm1, perm2])
        
        # Assign role to user
        user_role = UserRole(user_id=test_user.id, role_id=role.id)
        db.add(user_role)
        await db.commit()
        
        # Verify
        await db.refresh(test_user)
        assert len(test_user.roles) == 2  # test role + editor role
        editor_role = next(r for r in test_user.roles if r.name == "editor")
        assert len(editor_role.permissions) == 2
        
    async def test_user_profile(self, db, test_user):
        """Test user profile creation and update."""
        profile = UserProfile(
            user_id=test_user.id,
            bio="AI enthusiast",
            company="Tech Corp",
            location="San Francisco",
            website="https://example.com",
            linkedin_url="https://linkedin.com/in/testuser",
            preferences={"theme": "dark", "notifications": True}
        )
        db.add(profile)
        await db.commit()
        
        await db.refresh(test_user)
        assert test_user.profile is not None
        assert test_user.profile.bio == "AI enthusiast"
        assert test_user.profile.preferences["theme"] == "dark"
        
    async def test_api_key_generation(self, db, test_user):
        """Test API key creation and management."""
        api_key = APIKey(
            user_id=test_user.id,
            name="Production API",
            key_hash="hashed_key_value",
            last_used_at=datetime.utcnow()
        )
        db.add(api_key)
        await db.commit()
        
        assert api_key.id is not None
        assert api_key.is_active is True
        assert api_key.last_used_at is not None
        
        # Test deactivation
        api_key.is_active = False
        await db.commit()
        
        await db.refresh(api_key)
        assert api_key.is_active is False


@pytest.mark.unit
class TestContentModels:
    """Test content-related models."""
    
    async def test_content_generation_creation(self, db, test_user):
        """Test creating a content generation task."""
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/uploads/test.pdf",
            source_file_name="AWS_Guide.pdf",
            source_file_size=1024 * 1024,  # 1MB
            title="AWS Solutions Architect",
            description="Complete certification guide",
            content_type=ContentType.FULL_CERTIFICATION,
            settings={
                "difficulty": "intermediate",
                "include_labs": True
            }
        )
        db.add(generation)
        await db.commit()
        
        assert generation.id is not None
        assert generation.status == GenerationStatus.PENDING
        assert generation.progress == 0
        assert generation.settings["include_labs"] is True
        
    async def test_content_piece_hierarchy(self, db, test_user):
        """Test hierarchical content structure."""
        # Create generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test Course",
            content_type=ContentType.MINI_COURSE
        )
        db.add(generation)
        await db.flush()
        
        # Create parent section
        section = ContentPiece(
            generation_id=generation.id,
            piece_type="section",
            title="Chapter 1: Introduction",
            content="Welcome to the course",
            order_index=1
        )
        db.add(section)
        await db.flush()
        
        # Create child pieces
        lesson1 = ContentPiece(
            generation_id=generation.id,
            parent_id=section.id,
            piece_type="lesson",
            title="Lesson 1.1",
            content="First lesson content",
            order_index=1
        )
        lesson2 = ContentPiece(
            generation_id=generation.id,
            parent_id=section.id,
            piece_type="lesson",
            title="Lesson 1.2",
            content="Second lesson content",
            order_index=2
        )
        db.add_all([lesson1, lesson2])
        await db.commit()
        
        # Verify hierarchy
        await db.refresh(section)
        assert len(section.children) == 2
        assert section.children[0].title == "Lesson 1.1"
        assert section.children[1].title == "Lesson 1.2"
        
    async def test_media_assets_and_references(self, db, test_user):
        """Test media asset management."""
        # Create generation and content
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test",
            content_type=ContentType.QUICK_REVIEW
        )
        db.add(generation)
        await db.flush()
        
        content = ContentPiece(
            generation_id=generation.id,
            piece_type="lesson",
            title="Visual Lesson",
            content="Content with visuals",
            order_index=1
        )
        db.add(content)
        await db.flush()
        
        # Create media asset
        asset = MediaAsset(
            generation_id=generation.id,
            asset_type="animation",
            file_path="/assets/animation1.mp4",
            file_name="intro_animation.mp4",
            file_size=5 * 1024 * 1024,  # 5MB
            mime_type="video/mp4",
            duration=30.5,
            metadata={
                "resolution": "1920x1080",
                "fps": 30,
                "codec": "h264"
            }
        )
        db.add(asset)
        await db.flush()
        
        # Create reference
        reference = MediaReference(
            content_piece_id=content.id,
            media_asset_id=asset.id,
            reference_type="primary",
            order_index=1,
            start_time=0.0,
            end_time=30.5,
            settings={"autoplay": True}
        )
        db.add(reference)
        await db.commit()
        
        # Verify relationships
        await db.refresh(content)
        assert len(content.media_references) == 1
        assert content.media_references[0].media_asset.asset_type == "animation"
        assert content.media_references[0].settings["autoplay"] is True
        
    async def test_content_versioning(self, db, test_user):
        """Test content version tracking."""
        # Create content
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test",
            content_type=ContentType.EXAM_PREP
        )
        db.add(generation)
        await db.flush()
        
        content = ContentPiece(
            generation_id=generation.id,
            piece_type="lesson",
            title="Version Test",
            content="Original content",
            order_index=1
        )
        db.add(content)
        await db.commit()
        
        # Create version
        version = ContentVersion(
            content_piece_id=content.id,
            version_number=1,
            title=content.title,
            content=content.content,
            metadata=content.metadata,
            change_summary="Initial version",
            created_by_id=test_user.id
        )
        db.add(version)
        await db.commit()
        
        # Update content
        content.content = "Updated content"
        version2 = ContentVersion(
            content_piece_id=content.id,
            version_number=2,
            title=content.title,
            content=content.content,
            metadata=content.metadata,
            change_summary="Updated lesson content",
            created_by_id=test_user.id
        )
        db.add(version2)
        await db.commit()
        
        # Verify versions
        await db.refresh(content)
        assert len(content.versions) == 2
        assert content.versions[0].content == "Original content"
        assert content.versions[1].content == "Updated content"


@pytest.mark.unit
class TestDomainModels:
    """Test domain knowledge models."""
    
    async def test_concept_extraction(self, db, test_user):
        """Test extracted concept creation."""
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test",
            content_type=ContentType.FULL_CERTIFICATION
        )
        db.add(generation)
        await db.flush()
        
        concept = ExtractedConcept(
            generation_id=generation.id,
            name="EC2 Instance",
            concept_type=ConceptType.SERVICE,
            description="Elastic Compute Cloud virtual server",
            importance_score=0.95,
            difficulty_level=0.6,
            source_location="Chapter 3, Page 45",
            context="AWS compute services",
            embeddings=[0.1, 0.2, 0.3] * 128,  # 384-dim embedding
            metadata={
                "aws_service": "EC2",
                "category": "compute"
            }
        )
        db.add(concept)
        await db.commit()
        
        assert concept.id is not None
        assert concept.importance_score == 0.95
        assert len(concept.embeddings) == 384
        
    async def test_canonical_concept_mapping(self, db, test_user):
        """Test canonical concept deduplication."""
        # Create canonical concept
        canonical = CanonicalConcept(
            name="Amazon EC2",
            concept_type=ConceptType.SERVICE,
            description="Amazon Elastic Compute Cloud",
            domain="AWS",
            metadata={
                "official_name": "Amazon EC2",
                "service_category": "Compute"
            }
        )
        db.add(canonical)
        await db.flush()
        
        # Create generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test",
            content_type=ContentType.FULL_CERTIFICATION
        )
        db.add(generation)
        await db.flush()
        
        # Create extracted concepts that map to canonical
        extracted1 = ExtractedConcept(
            generation_id=generation.id,
            name="EC2",
            concept_type=ConceptType.SERVICE,
            description="AWS compute service",
            canonical_id=canonical.id,
            importance_score=0.9
        )
        extracted2 = ExtractedConcept(
            generation_id=generation.id,
            name="EC2 Instances",
            concept_type=ConceptType.SERVICE,
            description="Virtual servers in AWS",
            canonical_id=canonical.id,
            importance_score=0.85
        )
        db.add_all([extracted1, extracted2])
        await db.commit()
        
        # Verify mapping
        await db.refresh(canonical)
        assert len(canonical.extracted_concepts) == 2
        assert all(e.canonical_id == canonical.id for e in canonical.extracted_concepts)
        
    async def test_concept_relationships(self, db):
        """Test concept relationship graph."""
        # Create concepts
        vpc = CanonicalConcept(
            name="VPC",
            concept_type=ConceptType.SERVICE,
            description="Virtual Private Cloud"
        )
        subnet = CanonicalConcept(
            name="Subnet",
            concept_type=ConceptType.COMPONENT,
            description="VPC subnet"
        )
        ec2 = CanonicalConcept(
            name="EC2",
            concept_type=ConceptType.SERVICE,
            description="Elastic Compute Cloud"
        )
        db.add_all([vpc, subnet, ec2])
        await db.flush()
        
        # Create relationships
        rel1 = ConceptRelationship(
            source_id=vpc.id,
            target_id=subnet.id,
            relationship_type=RelationshipType.CONTAINS,
            strength=1.0,
            metadata={"required": True}
        )
        rel2 = ConceptRelationship(
            source_id=subnet.id,
            target_id=ec2.id,
            relationship_type=RelationshipType.HOSTS,
            strength=0.8,
            metadata={"common_pattern": True}
        )
        db.add_all([rel1, rel2])
        await db.commit()
        
        # Verify relationships
        await db.refresh(vpc)
        assert len(vpc.outgoing_relationships) == 1
        assert vpc.outgoing_relationships[0].target.name == "Subnet"
        
    async def test_learning_objectives(self, db, test_user):
        """Test learning objectives with Bloom's taxonomy."""
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test",
            content_type=ContentType.FULL_CERTIFICATION
        )
        db.add(generation)
        await db.flush()
        
        # Create objectives at different Bloom levels
        objectives = [
            LearningObjective(
                generation_id=generation.id,
                objective="Remember EC2 instance types",
                bloom_level=BloomLevel.REMEMBER,
                estimated_time=15,
                order_index=1
            ),
            LearningObjective(
                generation_id=generation.id,
                objective="Explain VPC networking concepts",
                bloom_level=BloomLevel.UNDERSTAND,
                estimated_time=30,
                order_index=2
            ),
            LearningObjective(
                generation_id=generation.id,
                objective="Design multi-tier architecture",
                bloom_level=BloomLevel.CREATE,
                estimated_time=60,
                order_index=3
            )
        ]
        db.add_all(objectives)
        await db.commit()
        
        # Verify objectives
        await db.refresh(generation)
        assert len(generation.learning_objectives) == 3
        assert generation.learning_objectives[0].bloom_level == BloomLevel.REMEMBER
        assert generation.learning_objectives[2].bloom_level == BloomLevel.CREATE
        
    async def test_learning_path(self, db, test_user):
        """Test learning path optimization."""
        # Create concepts
        concepts = []
        for i in range(5):
            concept = CanonicalConcept(
                name=f"Concept {i}",
                concept_type=ConceptType.TOPIC,
                description=f"Test concept {i}"
            )
            concepts.append(concept)
        db.add_all(concepts)
        await db.flush()
        
        # Create learning path
        path = LearningPath(
            name="AWS Fundamentals Path",
            description="Optimized path for AWS basics",
            user_id=test_user.id,
            total_duration=180,  # 3 hours
            difficulty_progression=[0.2, 0.3, 0.4, 0.5, 0.6],
            concept_sequence=[str(c.id) for c in concepts],
            metadata={
                "optimization_score": 0.92,
                "algorithm": "cognitive_load_balanced"
            }
        )
        db.add(path)
        await db.commit()
        
        assert path.id is not None
        assert len(path.concept_sequence) == 5
        assert path.metadata["optimization_score"] == 0.92


@pytest.mark.unit
class TestQualityModels:
    """Test quality assurance models."""
    
    async def test_quality_check(self, db, test_user):
        """Test quality check creation and scoring."""
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test",
            content_type=ContentType.FULL_CERTIFICATION
        )
        db.add(generation)
        await db.flush()
        
        quality_check = QualityCheck(
            generation_id=generation.id,
            check_type="automated",
            check_name="Pedagogical Quality Assessment",
            status=QualityStatus.IN_PROGRESS,
            overall_score=0.0,
            passed=False,
            details={
                "content_accuracy": 0.95,
                "pedagogical_soundness": 0.88,
                "engagement_potential": 0.82
            }
        )
        db.add(quality_check)
        await db.flush()
        
        # Add metrics
        metrics = [
            QualityMetric(
                quality_check_id=quality_check.id,
                dimension=QualityDimension.ACCURACY,
                score=0.95,
                details={"errors_found": 2, "total_facts": 40}
            ),
            QualityMetric(
                quality_check_id=quality_check.id,
                dimension=QualityDimension.PEDAGOGY,
                score=0.88,
                details={"cognitive_load": "optimal", "scaffolding": "good"}
            ),
            QualityMetric(
                quality_check_id=quality_check.id,
                dimension=QualityDimension.ENGAGEMENT,
                score=0.82,
                details={"interactivity": "high", "visual_appeal": "moderate"}
            )
        ]
        db.add_all(metrics)
        
        # Update overall score
        quality_check.overall_score = sum(m.score for m in metrics) / len(metrics)
        quality_check.passed = quality_check.overall_score >= 0.8
        quality_check.status = QualityStatus.COMPLETED
        await db.commit()
        
        assert quality_check.overall_score > 0.8
        assert quality_check.passed is True
        assert len(quality_check.metrics) == 3
        
    async def test_quality_issues(self, db, test_user):
        """Test quality issue tracking."""
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test",
            content_type=ContentType.MINI_COURSE
        )
        db.add(generation)
        await db.flush()
        
        content = ContentPiece(
            generation_id=generation.id,
            piece_type="lesson",
            title="Test Lesson",
            content="Content with issues",
            order_index=1
        )
        db.add(content)
        await db.flush()
        
        # Create quality issues
        issues = [
            QualityIssue(
                generation_id=generation.id,
                content_piece_id=content.id,
                issue_type=IssueType.ACCURACY,
                severity=IssueSeverity.HIGH,
                description="Incorrect EC2 pricing information",
                location="Paragraph 3",
                suggested_fix="Update with current pricing tiers",
                metadata={"detected_by": "fact_checker"}
            ),
            QualityIssue(
                generation_id=generation.id,
                content_piece_id=content.id,
                issue_type=IssueType.CLARITY,
                severity=IssueSeverity.MEDIUM,
                description="Technical jargon without explanation",
                location="Throughout section",
                suggested_fix="Add glossary or inline definitions",
                metadata={"readability_score": 45}
            )
        ]
        db.add_all(issues)
        await db.commit()
        
        # Resolve an issue
        issues[0].status = "resolved"
        issues[0].resolved_at = datetime.utcnow()
        issues[0].resolved_by_id = test_user.id
        issues[0].resolution_notes = "Updated pricing information from AWS docs"
        await db.commit()
        
        await db.refresh(generation)
        assert len(generation.quality_issues) == 2
        assert generation.quality_issues[0].status == "resolved"
        
    async def test_user_feedback(self, db, test_user):
        """Test user feedback collection."""
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test",
            content_type=ContentType.QUICK_REVIEW
        )
        db.add(generation)
        await db.flush()
        
        feedback = UserFeedback(
            user_id=test_user.id,
            generation_id=generation.id,
            feedback_type=FeedbackType.RATING,
            rating=4,
            comment="Great content, but could use more examples",
            metadata={
                "completion_rate": 0.85,
                "time_spent": 3600,  # 1 hour
                "helpful_sections": ["intro", "concepts"]
            }
        )
        db.add(feedback)
        await db.commit()
        
        assert feedback.id is not None
        assert feedback.rating == 4
        assert feedback.metadata["completion_rate"] == 0.85


@pytest.mark.unit
class TestAnalyticsModels:
    """Test analytics and metrics models."""
    
    async def test_generation_analytics(self, db, test_user):
        """Test generation analytics tracking."""
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test",
            content_type=ContentType.FULL_CERTIFICATION
        )
        db.add(generation)
        await db.flush()
        
        analytics = GenerationAnalytics(
            generation_id=generation.id,
            total_duration=3600.5,  # 1 hour
            agent_time_breakdown={
                "orchestrator": 120.0,
                "domain_extraction": 900.0,
                "content_generation": 1800.0,
                "quality_assurance": 780.5
            },
            tokens_used=150000,
            api_costs=Decimal("2.50"),
            compute_costs=Decimal("0.75"),
            total_costs=Decimal("3.25"),
            quality_scores={
                "accuracy": 0.92,
                "pedagogy": 0.88,
                "engagement": 0.85
            },
            metadata={
                "model_versions": {
                    "llm": "gpt-4",
                    "embedding": "ada-002"
                },
                "retry_count": 1
            }
        )
        db.add(analytics)
        await db.commit()
        
        assert analytics.id is not None
        assert analytics.total_costs == Decimal("3.25")
        assert analytics.agent_time_breakdown["content_generation"] == 1800.0
        
    async def test_daily_metrics_aggregation(self, db):
        """Test daily metrics aggregation."""
        today = datetime.utcnow().date()
        
        metrics = DailyMetrics(
            date=today,
            metric_type=MetricType.GENERATION,
            total_count=25,
            successful_count=23,
            failed_count=2,
            average_duration=2400.0,  # 40 minutes average
            total_cost=Decimal("75.50"),
            breakdown={
                "by_content_type": {
                    "full_certification": 5,
                    "mini_course": 10,
                    "quick_review": 10
                },
                "by_hour": {str(i): 0 for i in range(24)}
            },
            metadata={
                "peak_hour": 14,
                "unique_users": 18
            }
        )
        db.add(metrics)
        await db.commit()
        
        assert metrics.id is not None
        assert metrics.successful_count == 23
        assert metrics.breakdown["by_content_type"]["mini_course"] == 10
        
    async def test_performance_metrics(self, db):
        """Test performance metric tracking."""
        metric = PerformanceMetric(
            endpoint="/api/v1/content/generate",
            method="POST",
            response_time=245.5,  # milliseconds
            status_code=200,
            user_id=None,  # Can be anonymous
            metadata={
                "content_type": "mini_course",
                "file_size": 2048000,  # 2MB
                "queue_time": 50.2
            }
        )
        db.add(metric)
        await db.commit()
        
        assert metric.id is not None
        assert metric.response_time == 245.5
        assert metric.metadata["queue_time"] == 50.2
        
    async def test_ab_test_experiment(self, db):
        """Test A/B testing framework."""
        experiment = ABTestExperiment(
            name="New Animation Style Test",
            description="Testing engagement with new animation components",
            status="active",
            start_date=datetime.utcnow(),
            variants={
                "control": {
                    "description": "Current animation style",
                    "weight": 0.5
                },
                "treatment": {
                    "description": "New dynamic animations",
                    "weight": 0.5
                }
            },
            success_metrics=["engagement_rate", "completion_rate"],
            metadata={
                "hypothesis": "New animations will increase engagement by 15%",
                "minimum_sample_size": 1000
            }
        )
        db.add(experiment)
        await db.commit()
        
        assert experiment.id is not None
        assert experiment.status == "active"
        assert len(experiment.variants) == 2
        assert "engagement_rate" in experiment.success_metrics


@pytest.mark.unit 
class TestModelMethods:
    """Test model methods and computed properties."""
    
    async def test_content_generation_progress_calculation(self, db, test_user):
        """Test progress calculation for content generation."""
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test",
            content_type=ContentType.MINI_COURSE,
            status=GenerationStatus.IN_PROGRESS
        )
        db.add(generation)
        await db.flush()
        
        # Add progress steps
        generation.progress = 25
        generation.current_step = "Extracting concepts"
        await db.commit()
        
        assert generation.progress == 25
        assert generation.status == GenerationStatus.IN_PROGRESS
        
        # Complete generation
        generation.progress = 100
        generation.status = GenerationStatus.COMPLETED
        generation.completed_at = datetime.utcnow()
        await db.commit()
        
        assert generation.completed_at is not None
        
    async def test_soft_delete_functionality(self, db, test_user):
        """Test soft delete mixin functionality."""
        # Create content
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test for deletion",
            content_type=ContentType.QUICK_REVIEW
        )
        db.add(generation)
        await db.commit()
        
        # Soft delete
        generation.deleted_at = datetime.utcnow()
        generation.deleted_by_id = test_user.id
        await db.commit()
        
        # Verify soft delete
        assert generation.deleted_at is not None
        assert generation.deleted_by_id == test_user.id
        
        # Test filtering (would need repository method)
        # Active items should not include soft-deleted ones
        
    async def test_audit_trail(self, db, test_user):
        """Test audit mixin functionality."""
        # Create content with audit fields
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Audited content",
            content_type=ContentType.EXAM_PREP,
            created_by_id=test_user.id
        )
        db.add(generation)
        await db.commit()
        
        original_created = generation.created_at
        
        # Update content
        generation.title = "Updated title"
        generation.updated_at = datetime.utcnow()
        generation.updated_by_id = test_user.id
        await db.commit()
        
        assert generation.updated_at > original_created
        assert generation.updated_by_id == test_user.id
        
    async def test_json_field_handling(self, db, test_user):
        """Test JSON field storage and retrieval."""
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="JSON test",
            content_type=ContentType.FULL_CERTIFICATION,
            settings={
                "difficulty": "intermediate",
                "features": ["animations", "quizzes", "labs"],
                "preferences": {
                    "theme": "professional",
                    "pace": "moderate"
                }
            }
        )
        db.add(generation)
        await db.commit()
        
        # Refresh and verify
        await db.refresh(generation)
        assert generation.settings["difficulty"] == "intermediate"
        assert "animations" in generation.settings["features"]
        assert generation.settings["preferences"]["theme"] == "professional"
        
    async def test_relationship_cascades(self, db, test_user):
        """Test relationship cascade behaviors."""
        # Create generation with content
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Cascade test",
            content_type=ContentType.MINI_COURSE
        )
        db.add(generation)
        await db.flush()
        
        # Add content pieces
        pieces = []
        for i in range(3):
            piece = ContentPiece(
                generation_id=generation.id,
                piece_type="lesson",
                title=f"Lesson {i+1}",
                content=f"Content {i+1}",
                order_index=i+1
            )
            pieces.append(piece)
        db.add_all(pieces)
        await db.commit()
        
        # Verify relationships
        await db.refresh(generation)
        assert len(generation.content_pieces) == 3
        
        # Test cascade behavior would depend on cascade settings
        # Currently most are set to restrict deletion
