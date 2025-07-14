"""
Unit tests for API schemas and validation.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from pydantic import ValidationError

from certify_studio.api.schemas import (
    GenerationRequest,
    DomainExtractionRequest,
    QualityCheckRequest,
    ExportRequest,
    ExportOptions,
    OutputFormat,
    CertificationType,
    QualityLevel,
    StatusEnum,
    GenerationMetrics,
    User,
    PlanType
)


class TestGenerationRequest:
    """Test content generation request schema."""
    
    def test_valid_generation_request(self):
        """Test valid generation request."""
        request = GenerationRequest(
            certification_type=CertificationType.AWS_SAA,
            upload_id=uuid4(),
            title="AWS Solutions Architect Course",
            duration_minutes=30,
            output_formats=[OutputFormat.VIDEO_MP4, OutputFormat.PDF_DOCUMENT]
        )
        
        assert request.certification_type == CertificationType.AWS_SAA
        assert request.title == "AWS Solutions Architect Course"
        assert request.duration_minutes == 30
        assert len(request.output_formats) == 2
        assert request.quality_level == QualityLevel.STANDARD  # Default
        assert request.enable_interactivity is True  # Default
    
    def test_generation_request_validation(self):
        """Test generation request validation."""
        # Missing required field
        with pytest.raises(ValidationError) as exc_info:
            GenerationRequest(
                certification_type=CertificationType.AWS_SAA,
                # Missing upload_id or content_url
                title="Test"
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("output_formats",) for e in errors)
        
        # Invalid duration
        with pytest.raises(ValidationError) as exc_info:
            GenerationRequest(
                certification_type=CertificationType.AWS_SAA,
                upload_id=uuid4(),
                title="Test",
                duration_minutes=200,  # Max is 180
                output_formats=[OutputFormat.VIDEO_MP4]
            )
        errors = exc_info.value.errors()
        assert any("less than or equal to 180" in str(e) for e in errors)
    
    def test_generation_request_content_source_validation(self):
        """Test that either upload_id or content_url is required."""
        # Both missing should fail
        with pytest.raises(ValidationError):
            GenerationRequest(
                certification_type=CertificationType.AWS_SAA,
                title="Test",
                output_formats=[OutputFormat.VIDEO_MP4]
                # Missing both upload_id and content_url
            )
        
        # With upload_id should work
        request1 = GenerationRequest(
            certification_type=CertificationType.AWS_SAA,
            upload_id=uuid4(),
            title="Test",
            output_formats=[OutputFormat.VIDEO_MP4]
        )
        assert request1.upload_id is not None
        
        # With content_url should work
        request2 = GenerationRequest(
            certification_type=CertificationType.AWS_SAA,
            content_url="https://example.com/guide.pdf",
            title="Test",
            output_formats=[OutputFormat.VIDEO_MP4]
        )
        assert request2.content_url is not None


class TestExportOptions:
    """Test export options schema."""
    
    def test_valid_export_options(self):
        """Test valid export options."""
        options = ExportOptions(
            format=OutputFormat.VIDEO_MP4,
            video_resolution="1920x1080",
            video_fps=30,
            include_captions=True
        )
        
        assert options.format == OutputFormat.VIDEO_MP4
        assert options.video_resolution == "1920x1080"
        assert options.video_fps == 30
        assert options.include_captions is True
    
    def test_export_options_defaults(self):
        """Test export options default values."""
        options = ExportOptions(format=OutputFormat.PDF_DOCUMENT)
        
        assert options.format == OutputFormat.PDF_DOCUMENT
        assert options.video_resolution == "1920x1080"  # Default
        assert options.video_fps == 30  # Default
        assert options.include_captions is True  # Default
        assert options.pdf_layout == "portrait"  # Default
        assert options.include_toc is True  # Default
    
    def test_export_options_validation(self):
        """Test export options validation."""
        # Invalid PDF layout
        with pytest.raises(ValidationError) as exc_info:
            ExportOptions(
                format=OutputFormat.PDF_DOCUMENT,
                pdf_layout="invalid"
            )
        errors = exc_info.value.errors()
        assert any("string does not match regex" in str(e) for e in errors)
        
        # Invalid SCORM version
        with pytest.raises(ValidationError) as exc_info:
            ExportOptions(
                format=OutputFormat.SCORM_PACKAGE,
                scorm_version="3.0"  # Only 1.2 or 2004
            )
        errors = exc_info.value.errors()
        assert any("string does not match regex" in str(e) for e in errors)


class TestGenerationMetrics:
    """Test generation metrics schema."""
    
    def test_valid_generation_metrics(self):
        """Test valid generation metrics."""
        metrics = GenerationMetrics(
            total_concepts=50,
            total_animations=15,
            total_diagrams=20,
            processing_time_seconds=1234.5,
            quality_score=0.92,
            pedagogical_score=0.89,
            technical_accuracy=0.95,
            accessibility_score=0.98
        )
        
        assert metrics.total_concepts == 50
        assert metrics.processing_time_seconds == 1234.5
        assert metrics.quality_score == 0.92
        assert 0 <= metrics.quality_score <= 1
    
    def test_generation_metrics_validation(self):
        """Test generation metrics validation."""
        # Score out of range
        with pytest.raises(ValidationError) as exc_info:
            GenerationMetrics(
                total_concepts=10,
                total_animations=5,
                total_diagrams=3,
                processing_time_seconds=100,
                quality_score=1.5,  # Max is 1.0
                pedagogical_score=0.8,
                technical_accuracy=0.9,
                accessibility_score=0.85
            )
        errors = exc_info.value.errors()
        assert any("less than or equal to 1" in str(e) for e in errors)


class TestUserSchema:
    """Test user schema."""
    
    def test_valid_user(self):
        """Test valid user schema."""
        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            is_active=True,
            is_verified=False,
            is_admin=False,
            plan_type=PlanType.STARTER,
            total_generations=5,
            total_storage_mb=123.45,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.plan_type == PlanType.STARTER
        assert user.total_storage_mb == 123.45
    
    def test_user_defaults(self):
        """Test user default values."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert user.full_name is None  # Optional
        assert user.is_active is True  # Default
        assert user.is_verified is False  # Default
        assert user.is_admin is False  # Default
        assert user.plan_type == PlanType.FREE  # Default
        assert user.total_generations == 0  # Default
        assert user.total_storage_mb == 0  # Default


class TestEnums:
    """Test enum values."""
    
    def test_status_enum(self):
        """Test status enum values."""
        assert StatusEnum.SUCCESS == "success"
        assert StatusEnum.PENDING == "pending"
        assert StatusEnum.PROCESSING == "processing"
        assert StatusEnum.COMPLETED == "completed"
        assert StatusEnum.FAILED == "failed"
        assert StatusEnum.CANCELLED == "cancelled"
    
    def test_certification_type_enum(self):
        """Test certification type enum."""
        assert CertificationType.AWS_SAA == "aws-saa"
        assert CertificationType.AZURE_AZ104 == "azure-az104"
        assert CertificationType.KUBERNETES_CKA == "kubernetes-cka"
        assert CertificationType.CUSTOM == "custom"
        
        # Test that we have many certification types
        assert len(CertificationType.__members__) > 30
    
    def test_output_format_enum(self):
        """Test output format enum."""
        assert OutputFormat.VIDEO_MP4 == "video/mp4"
        assert OutputFormat.PDF_DOCUMENT == "pdf/document"
        assert OutputFormat.SCORM_PACKAGE == "scorm/package"
        
        # All formats should have proper MIME-like format
        for format in OutputFormat:
            assert "/" in format.value
