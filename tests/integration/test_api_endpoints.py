"""
Integration tests for API endpoints.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch
from uuid import uuid4

from certify_studio.api.main import app
from certify_studio.api.schemas import (
    StatusEnum,
    CertificationType,
    OutputFormat,
    QualityLevel
)


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health and monitoring endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "version" in data
        assert "services" in data
    
    @pytest.mark.asyncio
    async def test_api_info(self):
        """Test API info endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/info")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Certify Studio API"
        assert "version" in data
        assert "capabilities" in data
        assert len(data["agents"]) == 4
        assert len(data["supported_formats"]) >= 6


@pytest.mark.integration
class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_endpoint(self):
        """Test login endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/login",
                data={
                    "username": "test@example.com",
                    "password": "password123"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, auth_headers):
        """Test get current user endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Mock the get_current_user dependency
            mock_user = {
                "id": str(uuid4()),
                "email": "test@example.com",
                "username": "testuser",
                "is_active": True,
                "is_verified": True,
                "plan_type": "free",
                "total_generations": 0,
                "total_storage_mb": 0,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
            
            with patch("certify_studio.api.routers.auth.get_current_user", return_value=mock_user):
                response = await client.get(
                    "/api/auth/me",
                    headers=auth_headers
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"


@pytest.mark.integration
class TestGenerationEndpoints:
    """Test content generation endpoints."""
    
    @pytest.mark.asyncio
    async def test_start_generation(self, auth_headers):
        """Test starting content generation."""
        request_data = {
            "certification_type": CertificationType.AWS_SAA.value,
            "upload_id": str(uuid4()),
            "title": "AWS Solutions Architect Course",
            "duration_minutes": 30,
            "output_formats": [OutputFormat.VIDEO_MP4.value],
            "quality_level": QualityLevel.STANDARD.value
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Mock dependencies
            with patch("certify_studio.api.routers.generation.get_current_verified_user"):
                with patch("certify_studio.api.routers.generation.orchestrator") as mock_orchestrator:
                    response = await client.post(
                        "/api/generation/generate",
                        json=request_data,
                        headers=auth_headers
                    )
        
        assert response.status_code == 202  # Accepted
        data = response.json()
        assert data["status"] == StatusEnum.SUCCESS.value
        assert "task_id" in data
        assert data["generation_status"] == StatusEnum.PENDING.value
    
    @pytest.mark.asyncio
    async def test_upload_file(self, auth_headers):
        """Test file upload endpoint."""
        # Create a mock file
        file_content = b"Mock PDF content"
        files = {
            "file": ("test.pdf", file_content, "application/pdf")
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("certify_studio.api.routers.generation.get_current_verified_user"):
                with patch("certify_studio.api.dependencies.UploadFile.__call__") as mock_upload:
                    mock_upload.return_value = {
                        "upload_id": uuid4(),
                        "filename": "test.pdf",
                        "content_type": "application/pdf",
                        "size": len(file_content),
                        "path": "/uploads/test.pdf"
                    }
                    
                    response = await client.post(
                        "/api/generation/upload",
                        files=files,
                        headers=auth_headers
                    )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "upload_id" in data


@pytest.mark.integration
class TestDomainExtractionEndpoints:
    """Test domain extraction endpoints."""
    
    @pytest.mark.asyncio
    async def test_extract_domain_knowledge(self, auth_headers):
        """Test domain extraction endpoint."""
        request_data = {
            "upload_id": str(uuid4()),
            "certification_type": CertificationType.AWS_SAA.value,
            "extract_prerequisites": True,
            "extract_learning_paths": True,
            "chunk_size": 500
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("certify_studio.api.routers.domains.get_current_verified_user"):
                with patch("certify_studio.api.routers.domains.domain_agent") as mock_agent:
                    mock_agent._initialized = True
                    
                    response = await client.post(
                        "/api/domains/extract",
                        json=request_data,
                        headers=auth_headers
                    )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == StatusEnum.SUCCESS.value
        assert "extraction_id" in data
    
    @pytest.mark.asyncio
    async def test_search_knowledge(self, auth_headers):
        """Test knowledge search endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("certify_studio.api.routers.domains.get_current_verified_user"):
                response = await client.post(
                    "/api/domains/search",
                    params={"query": "EC2 instances", "max_results": 10},
                    headers=auth_headers
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == StatusEnum.SUCCESS.value
        assert "items" in data


@pytest.mark.integration
class TestQualityEndpoints:
    """Test quality assurance endpoints."""
    
    @pytest.mark.asyncio
    async def test_check_quality(self, auth_headers):
        """Test quality check endpoint."""
        request_data = {
            "content_id": str(uuid4()),
            "check_technical_accuracy": True,
            "check_pedagogical_effectiveness": True,
            "check_accessibility": True
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("certify_studio.api.routers.quality.get_current_verified_user"):
                with patch("certify_studio.api.routers.quality.qa_agent") as mock_agent:
                    mock_agent._initialized = True
                    
                    response = await client.post(
                        "/api/quality/check",
                        json=request_data,
                        headers=auth_headers
                    )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == StatusEnum.SUCCESS.value
        assert "check_id" in data
    
    @pytest.mark.asyncio
    async def test_submit_feedback(self, auth_headers):
        """Test feedback submission endpoint."""
        feedback_data = {
            "content_id": str(uuid4()),
            "overall_rating": 4,
            "technical_accuracy_rating": 5,
            "clarity_rating": 4,
            "comments": "Great content!"
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("certify_studio.api.routers.quality.get_current_verified_user"):
                with patch("certify_studio.api.routers.quality.qa_agent") as mock_agent:
                    mock_agent.feedback_analyzer.analyze_feedback.return_value = Mock()
                    
                    response = await client.post(
                        "/api/quality/feedback",
                        json=feedback_data,
                        headers=auth_headers
                    )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == StatusEnum.SUCCESS.value
        assert "feedback_id" in data


@pytest.mark.integration
class TestExportEndpoints:
    """Test export endpoints."""
    
    @pytest.mark.asyncio
    async def test_export_content(self, auth_headers):
        """Test content export endpoint."""
        export_request = {
            "content_id": str(uuid4()),
            "export_options": {
                "format": OutputFormat.VIDEO_MP4.value,
                "video_resolution": "1920x1080",
                "video_fps": 30,
                "include_captions": True
            }
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("certify_studio.api.routers.export.get_current_verified_user"):
                response = await client.post(
                    "/api/export/",
                    json=export_request,
                    headers=auth_headers
                )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == StatusEnum.SUCCESS.value
        assert "export_id" in data
    
    @pytest.mark.asyncio
    async def test_get_export_formats(self):
        """Test get export formats endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/export/formats")
        
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert len(data["formats"]) >= 6
        
        # Check format structure
        for format_info in data["formats"]:
            assert "format" in format_info
            assert "name" in format_info
            assert "description" in format_info
            assert "options" in format_info
