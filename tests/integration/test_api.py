"""
Integration tests for API endpoints.

Tests API endpoints with database integration.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from uuid import uuid4
import json

from certify_studio.app import app
from certify_studio.database.models import (
    User, ContentGeneration, ContentPiece, QualityCheck,
    ContentType, GenerationStatus, ExportFormat, QualityDimension,
    QualityMetric, UserActivity, ActivityType, GenerationAnalytics
)


@pytest.mark.integration
class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    async def test_register_user(self, client, db):
        """Test user registration endpoint."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "password" not in data
        
        # Verify user in database
        user = await db.execute(
            "SELECT * FROM users WHERE email = :email",
            {"email": "newuser@example.com"}
        )
        assert user.fetchone() is not None
        
    async def test_register_duplicate_user(self, client, test_user):
        """Test registering duplicate user fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "username": "anotheruser",
                "password": "Password123!",
                "full_name": "Another User"
            }
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
        
    async def test_login(self, client, test_user, db):
        """Test login endpoint."""
        # Set password
        from certify_studio.integration.services import UserService
        service = UserService(db)
        test_user.hashed_password = service.get_password_hash("testpass123")
        await db.commit()
        
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.username,
                "password": "testpass123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
    async def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.username,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
        
    async def test_refresh_token(self, client, test_user, db):
        """Test token refresh endpoint."""
        # Login first
        from certify_studio.integration.services import UserService
        service = UserService(db)
        test_user.hashed_password = service.get_password_hash("testpass123")
        await db.commit()
        
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.username,
                "password": "testpass123"
            }
        )
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] != login_response.json()["access_token"]
        
    async def test_get_current_user(self, client, auth_headers):
        """Test get current user endpoint."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
        
    async def test_update_profile(self, client, auth_headers):
        """Test update user profile endpoint."""
        response = await client.put(
            "/api/v1/auth/profile",
            headers=auth_headers,
            json={
                "bio": "Updated bio",
                "company": "New Company",
                "location": "New York"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "Updated bio"
        assert data["company"] == "New Company"
        
    async def test_change_password(self, client, auth_headers, test_user, db):
        """Test change password endpoint."""
        # Set current password
        from certify_studio.integration.services import UserService
        service = UserService(db)
        test_user.hashed_password = service.get_password_hash("oldpass123")
        await db.commit()
        
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "oldpass123",
                "new_password": "NewSecurePass123!"
            }
        )
        
        assert response.status_code == 200
        
        # Verify can login with new password
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.username,
                "password": "NewSecurePass123!"
            }
        )
        assert login_response.status_code == 200


@pytest.mark.integration
class TestContentEndpoints:
    """Test content generation endpoints."""
    
    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    async def test_start_generation(self, client, auth_headers, tmp_path):
        """Test start content generation endpoint."""
        # Create test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"test content")
        
        with open(test_file, "rb") as f:
            response = await client.post(
                "/api/v1/content/generate",
                headers=auth_headers,
                files={"file": ("test.pdf", f, "application/pdf")},
                data={
                    "title": "Test Course",
                    "content_type": ContentType.MINI_COURSE.value,
                    "settings": json.dumps({"difficulty": "intermediate"})
                }
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Course"
        assert data["status"] == GenerationStatus.PENDING.value
        assert "id" in data
        
    async def test_get_generation_status(self, client, auth_headers, test_user, db):
        """Test get generation status endpoint."""
        # Create generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test Generation",
            content_type=ContentType.QUICK_REVIEW,
            status=GenerationStatus.PROCESSING,
            progress=50
        )
        db.add(generation)
        await db.commit()
        
        response = await client.get(
            f"/api/v1/content/generations/{generation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(generation.id)
        assert data["status"] == GenerationStatus.PROCESSING.value
        assert data["progress"] == 50
        
    async def test_list_user_generations(self, client, auth_headers, test_user, db):
        """Test list user generations endpoint."""
        # Create multiple generations
        for i in range(5):
            generation = ContentGeneration(
                user_id=test_user.id,
                source_file_path=f"/test{i}.pdf",
                source_file_name=f"test{i}.pdf",
                title=f"Test Generation {i}",
                content_type=ContentType.MINI_COURSE,
                status=GenerationStatus.COMPLETED if i % 2 == 0 else GenerationStatus.PROCESSING
            )
            db.add(generation)
        await db.commit()
        
        response = await client.get(
            "/api/v1/content/generations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 5
        assert len(data["items"]) >= 5
        
        # Test filtering
        response = await client.get(
            "/api/v1/content/generations?status=completed",
            headers=auth_headers
        )
        
        data = response.json()
        assert all(item["status"] == GenerationStatus.COMPLETED.value for item in data["items"])
        
    async def test_get_generation_content(self, client, auth_headers, test_user, db):
        """Test get generation content endpoint."""
        # Create generation with content
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Test",
            content_type=ContentType.MINI_COURSE,
            status=GenerationStatus.COMPLETED
        )
        db.add(generation)
        await db.flush()
        
        # Add content pieces
        for i in range(3):
            piece = ContentPiece(
                generation_id=generation.id,
                piece_type="lesson",
                title=f"Lesson {i+1}",
                content=f"Content for lesson {i+1}",
                order_index=i+1
            )
            db.add(piece)
        await db.commit()
        
        response = await client.get(
            f"/api/v1/content/generations/{generation.id}/content",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["title"] == "Lesson 1"
        
    async def test_export_content(self, client, auth_headers, test_user, db):
        """Test export content endpoint."""
        # Create completed generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Export Test",
            content_type=ContentType.EXAM_PREP,
            status=GenerationStatus.COMPLETED
        )
        db.add(generation)
        await db.commit()
        
        response = await client.post(
            f"/api/v1/content/generations/{generation.id}/export",
            headers=auth_headers,
            json={
                "format": ExportFormat.PDF.value,
                "options": {"include_images": True}
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["format"] == ExportFormat.PDF.value
        assert data["status"] == "pending"
        assert "id" in data
        
    async def test_delete_generation(self, client, auth_headers, test_user, db):
        """Test delete generation endpoint."""
        # Create generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="To Delete",
            content_type=ContentType.QUICK_REVIEW
        )
        db.add(generation)
        await db.commit()
        
        response = await client.delete(
            f"/api/v1/content/generations/{generation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify soft deleted
        await db.refresh(generation)
        assert generation.deleted_at is not None


@pytest.mark.integration
class TestQualityEndpoints:
    """Test quality assurance endpoints."""
    
    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    async def test_get_quality_check(self, client, auth_headers, test_user, db):
        """Test get quality check endpoint."""
        # Create generation and quality check
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Quality Test",
            content_type=ContentType.FULL_CERTIFICATION,
            status=GenerationStatus.COMPLETED
        )
        db.add(generation)
        await db.flush()
        
        quality_check = QualityCheck(
            generation_id=generation.id,
            check_type="automated",
            check_name="Full Quality Assessment",
            status="completed",
            overall_score=0.88,
            passed=True,
            details={
                "accuracy": 0.92,
                "pedagogy": 0.86,
                "engagement": 0.85
            }
        )
        db.add(quality_check)
        await db.commit()
        
        response = await client.get(
            f"/api/v1/quality/checks/{quality_check.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 0.88
        assert data["passed"] is True
        
    async def test_run_quality_check(self, client, auth_headers, test_user, db):
        """Test run quality check endpoint."""
        # Create completed generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Quality Test",
            content_type=ContentType.MINI_COURSE,
            status=GenerationStatus.COMPLETED
        )
        db.add(generation)
        await db.commit()
        
        response = await client.post(
            f"/api/v1/quality/generations/{generation.id}/check",
            headers=auth_headers,
            json={
                "check_type": "comprehensive"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["generation_id"] == str(generation.id)
        assert data["check_type"] == "comprehensive"
        assert data["status"] == "pending"
        
    async def test_submit_feedback(self, client, auth_headers, test_user, db):
        """Test submit feedback endpoint."""
        # Create generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Feedback Test",
            content_type=ContentType.EXAM_PREP,
            status=GenerationStatus.COMPLETED
        )
        db.add(generation)
        await db.commit()
        
        response = await client.post(
            f"/api/v1/quality/generations/{generation.id}/feedback",
            headers=auth_headers,
            json={
                "rating": 4,
                "comment": "Good content, needs more examples",
                "feedback_type": "general",
                "metadata": {
                    "completion_rate": 0.85,
                    "helpful_sections": ["intro", "concepts"]
                }
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 4
        assert data["user_id"] == str(test_user.id)
        
    async def test_get_quality_metrics(self, client, auth_headers, test_user, db):
        """Test get quality metrics endpoint."""
        # Create generation with quality data
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Metrics Test",
            content_type=ContentType.FULL_CERTIFICATION,
            status=GenerationStatus.COMPLETED
        )
        db.add(generation)
        await db.flush()
        
        # Add quality check with metrics
        quality_check = QualityCheck(
            generation_id=generation.id,
            check_type="automated",
            check_name="Standard Check",
            status="completed",
            overall_score=0.87,
            passed=True
        )
        db.add(quality_check)
        await db.flush()
        
        metrics = [
            QualityMetric(
                quality_check_id=quality_check.id,
                dimension=QualityDimension.ACCURACY,
                score=0.92,
                details={"errors": 2, "total": 50}
            ),
            QualityMetric(
                quality_check_id=quality_check.id,
                dimension=QualityDimension.PEDAGOGY,
                score=0.85,
                details={"cognitive_load": "optimal"}
            )
        ]
        db.add_all(metrics)
        await db.commit()
        
        response = await client.get(
            f"/api/v1/quality/generations/{generation.id}/metrics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "accuracy" in data
        assert data["accuracy"]["score"] == 0.92


@pytest.mark.integration
class TestAnalyticsEndpoints:
    """Test analytics endpoints."""
    
    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    async def test_get_user_analytics(self, client, auth_headers, test_user, db):
        """Test get user analytics endpoint."""
        # Create some user activity
        activities = [
            UserActivity(
                user_id=test_user.id,
                activity_type=ActivityType.LOGIN,
                metadata={"ip": "127.0.0.1"}
            ),
            UserActivity(
                user_id=test_user.id,
                activity_type=ActivityType.GENERATION_STARTED,
                metadata={"content_type": "mini_course"}
            )
        ]
        db.add_all(activities)
        await db.commit()
        
        response = await client.get(
            "/api/v1/analytics/users/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_activities" in data
        assert "activity_breakdown" in data
        assert data["total_activities"] >= 2
        
    async def test_get_generation_analytics(self, client, auth_headers, test_user, db):
        """Test get generation analytics endpoint."""
        # Create generation with analytics
        from decimal import Decimal
        
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Analytics Test",
            content_type=ContentType.FULL_CERTIFICATION,
            status=GenerationStatus.COMPLETED
        )
        db.add(generation)
        await db.flush()
        
        analytics = GenerationAnalytics(
            generation_id=generation.id,
            total_duration=3600.0,
            agent_time_breakdown={
                "orchestrator": 120.0,
                "domain_extraction": 900.0,
                "content_generation": 1800.0,
                "quality_assurance": 780.0
            },
            tokens_used=150000,
            api_costs=Decimal("2.50"),
            compute_costs=Decimal("0.75"),
            total_costs=Decimal("3.25"),
            quality_scores={"overall": 0.88}
        )
        db.add(analytics)
        await db.commit()
        
        response = await client.get(
            f"/api/v1/analytics/generations/{generation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_duration"] == 3600.0
        assert data["tokens_used"] == 150000
        assert float(data["total_costs"]) == 3.25
        
    async def test_get_platform_metrics(self, client, admin_headers):
        """Test get platform metrics endpoint (admin only)."""
        response = await client.get(
            "/api/v1/analytics/platform/metrics",
            headers=admin_headers,
            params={"days": 7}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_generations" in data
        assert "daily_metrics" in data
        
    async def test_export_analytics_report(self, client, admin_headers):
        """Test export analytics report endpoint."""
        response = await client.post(
            "/api/v1/analytics/reports/export",
            headers=admin_headers,
            json={
                "report_type": "user_activity",
                "date_range": {
                    "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                    "end": datetime.utcnow().isoformat()
                },
                "format": "csv"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "processing"
        assert "report_id" in data


@pytest.mark.integration
class TestAdminEndpoints:
    """Test admin-only endpoints."""
    
    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    async def test_list_all_users(self, client, admin_headers, db):
        """Test list all users endpoint."""
        # Create additional users
        for i in range(3):
            user = User(
                email=f"user{i}@example.com",
                username=f"user{i}",
                hashed_password="hashed",
                full_name=f"User {i}"
            )
            db.add(user)
        await db.commit()
        
        response = await client.get(
            "/api/v1/admin/users",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 4  # 3 new + admin
        
    async def test_update_user_status(self, client, admin_headers, test_user):
        """Test update user status endpoint."""
        response = await client.patch(
            f"/api/v1/admin/users/{test_user.id}/status",
            headers=admin_headers,
            json={
                "is_active": False,
                "reason": "Suspicious activity"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        
    async def test_system_health_check(self, client, admin_headers):
        """Test system health check endpoint."""
        response = await client.get(
            "/api/v1/admin/system/health",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "redis" in data
        assert "agents" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        
    async def test_regenerate_content(self, client, admin_headers, test_user, db):
        """Test regenerate content endpoint."""
        # Create failed generation
        generation = ContentGeneration(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Failed Generation",
            content_type=ContentType.MINI_COURSE,
            status=GenerationStatus.FAILED,
            error_message="Processing error"
        )
        db.add(generation)
        await db.commit()
        
        response = await client.post(
            f"/api/v1/admin/generations/{generation.id}/regenerate",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == GenerationStatus.PENDING.value
        assert data["error_message"] is None


@pytest.mark.integration
class TestWebSocketEndpoints:
    """Test WebSocket endpoints for real-time updates."""
    
    async def test_generation_progress_websocket(self, test_user, db):
        """Test WebSocket for generation progress updates."""
        from fastapi.testclient import TestClient
        
        with TestClient(app) as client:
            # Get auth token
            from certify_studio.integration.services import UserService
            service = UserService(db)
            token = await service.create_access_token(test_user)
            
            with client.websocket_connect(
                f"/ws/generations?token={token}"
            ) as websocket:
                # Send subscription
                websocket.send_json({
                    "action": "subscribe",
                    "generation_id": str(uuid4())
                })
                
                # Receive confirmation
                data = websocket.receive_json()
                assert data["type"] == "subscribed"
                
    async def test_notifications_websocket(self, test_user, db):
        """Test WebSocket for user notifications."""
        from fastapi.testclient import TestClient
        
        with TestClient(app) as client:
            # Get auth token
            from certify_studio.integration.services import UserService
            service = UserService(db)
            token = await service.create_access_token(test_user)
            
            with client.websocket_connect(
                f"/ws/notifications?token={token}"
            ) as websocket:
                # Should receive connection confirmation
                data = websocket.receive_json()
                assert data["type"] == "connected"
                assert data["user_id"] == str(test_user.id)


@pytest.mark.integration
class TestErrorHandling:
    """Test API error handling."""
    
    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    async def test_404_not_found(self, client, auth_headers):
        """Test 404 error handling."""
        response = await client.get(
            f"/api/v1/content/generations/{uuid4()}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
    async def test_403_forbidden(self, client, auth_headers, admin_user, db):
        """Test 403 forbidden error."""
        # Create generation for different user
        generation = ContentGeneration(
            user_id=admin_user.id,
            source_file_path="/admin.pdf",
            source_file_name="admin.pdf",
            title="Admin Content",
            content_type=ContentType.MINI_COURSE
        )
        db.add(generation)
        await db.commit()
        
        # Try to access as regular user
        response = await client.get(
            f"/api/v1/content/generations/{generation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
        
    async def test_422_validation_error(self, client, auth_headers):
        """Test 422 validation error."""
        response = await client.post(
            "/api/v1/content/generate",
            headers=auth_headers,
            json={
                "title": "Test",
                # Missing required fields
            }
        )
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert isinstance(errors, list)
        assert any("content_type" in str(error) for error in errors)
        
    async def test_rate_limiting(self, client, auth_headers):
        """Test rate limiting."""
        # Make many requests quickly
        responses = []
        for _ in range(101):  # Assuming rate limit is 100/minute
            response = await client.get(
                "/api/v1/content/generations",
                headers=auth_headers
            )
            responses.append(response)
        
        # At least one should be rate limited
        assert any(r.status_code == 429 for r in responses)
        
        # Check rate limit headers
        limited_response = next(r for r in responses if r.status_code == 429)
        assert "X-RateLimit-Limit" in limited_response.headers
        assert "X-RateLimit-Remaining" in limited_response.headers
        assert "X-RateLimit-Reset" in limited_response.headers
