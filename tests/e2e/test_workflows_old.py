"""
End-to-end tests for complete workflows.

Tests entire user journeys from start to finish.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, Mock, AsyncMock
from pathlib import Path

from httpx import AsyncClient

from certify_studio.app import app
from certify_studio.database.models import (
    ContentType, GenerationStatus, QualityStatus, ExportFormat
)
from certify_studio.integration.services import ContentGenerationService
from certify_studio.database import get_db_session


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteContentGenerationFlow:
    """Test complete content generation workflow."""
    
    @pytest.fixture
    def mock_agents(self, mocker):
        """Mock all agents for e2e testing."""
        # Mock domain extraction agent
        domain_agent = mocker.AsyncMock()
        domain_agent.process.return_value = {
            'concepts': [
                {
                    'name': 'AWS EC2',
                    'description': 'Elastic Compute Cloud',
                    'type': 'service',
                    'importance': 0.9,
                    'metadata': {'category': 'compute'}
                },
                {
                    'name': 'AWS S3',
                    'description': 'Simple Storage Service',
                    'type': 'service',
                    'importance': 0.85,
                    'metadata': {'category': 'storage'}
                }
            ],
            'relationships': [
                {
                    'source_id': 'ec2_id',
                    'target_id': 's3_id',
                    'type': 'uses',
                    'strength': 0.7
                }
            ]
        }
        
        # Mock pedagogical agent
        pedagogical_agent = mocker.AsyncMock()
        pedagogical_agent.process.return_value = {
            'sections': [
                {
                    'type': 'introduction',
                    'title': 'Introduction to AWS',
                    'order': 1,
                    'cognitive_load': 0.3,
                    'duration': 10,
                    'objectives': ['Understand AWS basics']
                },
                {
                    'type': 'core_content',
                    'title': 'Core AWS Services',
                    'order': 2,
                    'cognitive_load': 0.6,
                    'duration': 30,
                    'objectives': ['Master EC2', 'Master S3']
                }
            ],
            'style_guide': {
                'tone': 'professional',
                'level': 'beginner'
            }
        }
        
        # Mock content generation agent
        content_agent = mocker.AsyncMock()
        content_agent.process.return_value = {
            'content': """
            # Introduction to AWS
            
            Amazon Web Services (AWS) is the world's leading cloud platform...
            
            ## Key Concepts
            - Cloud Computing
            - Infrastructure as a Service
            - Pay-as-you-go pricing
            """,
            'tokens_used': 1500
        }
        
        # Mock quality agent
        quality_agent = mocker.AsyncMock()
        quality_agent.process.return_value = {
            'overall_score': 0.92,
            'passed': True,
            'metrics': {
                'clarity': 0.95,
                'accuracy': 0.90,
                'completeness': 0.88,
                'pedagogy': 0.94
            }
        }
        
        return {
            'domain': domain_agent,
            'pedagogical': pedagogical_agent,
            'content': content_agent,
            'quality': quality_agent
        }
    
    async def test_full_generation_workflow(
        self,
        db,
        test_user,
        auth_headers,
        sample_pdf_file,
        mock_agents,
        mocker
    ):
        """Test complete workflow from upload to export."""
        # Patch agents
        with patch('certify_studio.integration.services.DomainExtractionAgent', return_value=mock_agents['domain']), \
             patch('certify_studio.integration.services.PedagogicalReasoningAgent', return_value=mock_agents['pedagogical']), \
             patch('certify_studio.integration.services.ContentGenerationAgent', return_value=mock_agents['content']), \
             patch('certify_studio.integration.services.QualityAssuranceAgent', return_value=mock_agents['quality']):
            
            # Step 1: Start generation
            async with AsyncClient(app=app, base_url="http://test") as client:
                with open(sample_pdf_file, 'rb') as f:
                    response = await client.post(
                        "/api/v1/content/generate",
                        headers=auth_headers,
                        files={"file": ("test.pdf", f, "application/pdf")},
                        data={
                            "title": "AWS Certification Guide",
                            "content_type": ContentType.FULL_CERTIFICATION.value,
                            "target_audience": "Cloud beginners"
                        }
                    )
            
            assert response.status_code == 200
            generation_data = response.json()
            generation_id = generation_data["id"]
            
            # Step 2: Process generation (simulate background task)
            async with get_db_session() as db_session:
                service = ContentGenerationService(db_session.session)
                await service.process_generation(generation_id)
                await db_session.commit()
            
            # Step 3: Check generation status
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/content/generations/{generation_id}",
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            status_data = response.json()
            assert status_data["status"] == GenerationStatus.COMPLETED.value
            assert status_data["progress"] == 100
            
            # Step 4: Get content pieces
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/content/generations/{generation_id}/pieces",
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            pieces = response.json()
            assert len(pieces) == 2  # Two sections from mock
            
            # Step 5: Submit feedback
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/quality/feedback",
                    headers=auth_headers,
                    json={
                        "generation_id": generation_id,
                        "rating": 5,
                        "feedback_text": "Excellent content!",
                        "feedback_type": "general"
                    }
                )
            
            assert response.status_code == 200
            
            # Step 6: Get quality report
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/quality/report/{generation_id}",
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            report = response.json()
            assert report["quality_checks"]["average_score"] > 0.9
            assert report["user_feedback"]["average_rating"] == 5.0
            
            # Step 7: Export content (start export task)
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/content/generations/{generation_id}/export",
                    headers=auth_headers,
                    json={"format": ExportFormat.PDF.value}
                )
            
            assert response.status_code == 200
            export_data = response.json()
            assert "export_task_id" in export_data


@pytest.mark.e2e
class TestUserJourneyFlow:
    """Test complete user journey from registration to content generation."""
    
    async def test_new_user_journey(self, db, mock_agents):
        """Test journey of a new user."""
        # Step 1: Register
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "journey@example.com",
                    "username": "journeyuser",
                    "password": "JourneyPass123!",
                    "full_name": "Journey User"
                }
            )
        
        assert response.status_code == 200
        user_data = response.json()
        
        # Step 2: Login
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                data={
                    "username": "journeyuser",
                    "password": "JourneyPass123!"
                }
            )
        
        assert response.status_code == 200
        token_data = response.json()
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        
        # Step 3: Check profile
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers=headers
            )
        
        assert response.status_code == 200
        profile = response.json()
        assert profile["email"] == "journey@example.com"
        
        # Step 4: Create API key
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/api-key",
                headers=headers,
                params={"name": "My API Key"}
            )
        
        assert response.status_code == 200
        api_key_data = response.json()
        assert "key" in api_key_data
        
        # Step 5: Check analytics (should be empty)
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/user",
                headers=headers
            )
        
        assert response.status_code == 200
        analytics = response.json()
        assert analytics["generations"]["total"] == 0


@pytest.mark.e2e
@pytest.mark.slow
class TestConcurrentOperations:
    """Test system behavior under concurrent operations."""
    
    async def test_concurrent_generations(self, db, test_user, auth_headers, sample_pdf_file, mock_celery):
        """Test multiple concurrent generation requests."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Start 5 concurrent generations
            tasks = []
            for i in range(5):
                with open(sample_pdf_file, 'rb') as f:
                    task = client.post(
                        "/api/v1/content/generate",
                        headers=auth_headers,
                        files={"file": ("test.pdf", f, "application/pdf")},
                        data={
                            "title": f"Concurrent Test {i}",
                            "content_type": ContentType.TOPIC_SUMMARY.value
                        }
                    )
                    tasks.append(task)
            
            # Wait for all to complete
            responses = await asyncio.gather(*tasks)
            
            # Verify all succeeded
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert "id" in data
                assert data["status"] == GenerationStatus.PENDING.value
            
            # Verify all generations were created
            generation_ids = [r.json()["id"] for r in responses]
            assert len(set(generation_ids)) == 5  # All unique IDs


@pytest.mark.e2e
class TestErrorHandling:
    """Test system error handling and recovery."""
    
    async def test_invalid_file_type(self, db, test_user, auth_headers):
        """Test uploading invalid file type."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Try to upload a .txt file (not allowed)
            response = await client.post(
                "/api/v1/content/generate",
                headers=auth_headers,
                files={"file": ("test.exe", b"fake exe content", "application/x-msdownload")},
                data={
                    "title": "Test",
                    "content_type": ContentType.FULL_CERTIFICATION.value
                }
            )
        
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]
    
    async def test_generation_failure_handling(self, db, test_user, helpers, mocker):
        """Test handling of generation failures."""
        generation = await helpers.create_test_generation(db, test_user)
        await db.commit()
        
        # Mock agent to fail
        failing_agent = mocker.AsyncMock()
        failing_agent.process.side_effect = Exception("Agent processing failed")
        
        with patch('certify_studio.integration.services.DomainExtractionAgent', return_value=failing_agent):
            # Process generation (should fail)
            from certify_studio.database import get_db_session
            async with get_db_session() as db_session:
                service = ContentGenerationService(db_session.session)
                
                with pytest.raises(Exception, match="Agent processing failed"):
                    await service.process_generation(generation.id)
                
                await db_session.commit()
        
        # Verify generation marked as failed
        await db.refresh(generation)
        assert generation.status == GenerationStatus.FAILED
        assert "Agent processing failed" in generation.error_message
    
    async def test_rate_limiting(self, db, test_user, auth_headers):
        """Test API rate limiting."""
        # This would test rate limiting if implemented
        # For now, just verify multiple rapid requests work
        async with AsyncClient(app=app, base_url="http://test") as client:
            for _ in range(10):
                response = await client.get(
                    "/api/v1/auth/me",
                    headers=auth_headers
                )
                assert response.status_code == 200


@pytest.mark.e2e
class TestDataConsistency:
    """Test data consistency across operations."""
    
    async def test_transaction_rollback(self, db, test_user, mocker):
        """Test transaction rollback on error."""
        from certify_studio.database.repositories import ContentRepository
        from certify_studio.database.models import ContentPiece
        
        repo = ContentRepository(db)
        
        # Start a transaction
        generation = await repo.create_generation(
            user_id=test_user.id,
            source_file_path="/test.pdf",
            source_file_name="test.pdf",
            title="Transaction Test",
            content_type=ContentType.FULL_CERTIFICATION
        )
        
        # Create a piece
        piece1 = await repo.create_content_piece(
            generation_id=generation.id,
            piece_type="section",
            title="Section 1",
            content="Content",
            order_index=1
        )
        
        # Force an error before commit
        try:
            # Try to create piece with duplicate order (if we had such constraint)
            piece2 = ContentPiece(
                generation_id=generation.id,
                piece_type="section",
                title="Section 2",
                content="Content",
                order_index=1  # Duplicate
            )
            db.add(piece2)
            
            # Simulate an error
            raise Exception("Simulated error")
            
        except Exception:
            await db.rollback()
        
        # Verify nothing was saved
        result = await repo.get_generation(generation.id)
        assert result is None
    
    async def test_concurrent_updates(self, db, test_user, helpers):
        """Test handling concurrent updates to same resource."""
        generation = await helpers.create_test_generation(db, test_user)
        await db.commit()
        
        # Simulate concurrent updates
        from certify_studio.database import get_db_session
        
        async def update_progress(progress: int):
            async with get_db_session() as session:
                repo = ContentRepository(session.session)
                gen = await repo.get_generation(generation.id)
                gen.progress = progress
                await session.commit()
        
        # Run concurrent updates
        tasks = [
            update_progress(25),
            update_progress(50),
            update_progress(75)
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify final state is consistent
        await db.refresh(generation)
        assert generation.progress in [25, 50, 75]  # One of them won


@pytest.mark.e2e
@pytest.mark.slow
class TestPerformance:
    """Test system performance characteristics."""
    
    async def test_large_file_handling(self, db, test_user, auth_headers, tmp_path, mock_celery):
        """Test handling large file uploads."""
        # Create a 10MB file
        large_file = tmp_path / "large.pdf"
        large_file.write_bytes(b"PDF" + b"0" * (10 * 1024 * 1024))
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            with open(large_file, 'rb') as f:
                response = await client.post(
                    "/api/v1/content/generate",
                    headers=auth_headers,
                    files={"file": ("large.pdf", f, "application/pdf")},
                    data={
                        "title": "Large File Test",
                        "content_type": ContentType.FULL_CERTIFICATION.value
                    },
                    timeout=30.0  # Longer timeout for large file
                )
        
        assert response.status_code == 200
    
    async def test_pagination_performance(self, db, test_user, auth_headers, helpers):
        """Test pagination with many items."""
        # Create 100 generations
        for i in range(100):
            await helpers.create_test_generation(db, test_user)
        await db.commit()
        
        # Test pagination
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First page
            response = await client.get(
                "/api/v1/content/generations?skip=0&limit=20",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 20
            
            # Last page
            response = await client.get(
                "/api/v1/content/generations?skip=80&limit=20",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 20
                assert response.status_code == 200
                data = response.json()
                assert "id" in data
                assert data["status"] == GenerationStatus.PENDING.value


@pytest.mark.e2e
class TestErrorHandlingFlow:
    """Test error handling and recovery."""
    
    async def test_generation_failure_handling(self, db, test_user, auth_headers, sample_pdf_file, mocker):
        """Test handling of generation failures."""
        # Mock agent to fail
        failing_agent = mocker.AsyncMock()
        failing_agent.process.side_effect = Exception("Agent processing failed")
        
        with patch('certify_studio.integration.services.DomainExtractionAgent', return_value=failing_agent):
            # Start generation
            async with AsyncClient(app=app, base_url="http://test") as client:
                with open(sample_pdf_file, 'rb') as f:
                    response = await client.post(
                        "/api/v1/content/generate",
                        headers=auth_headers,
                        files={"file": ("test.pdf", f, "application/pdf")},
                        data={
                            "title": "Failing Test",
                            "content_type": ContentType.TOPIC_SUMMARY.value
                        }
                    )
            
            assert response.status_code == 200
            generation_id = response.json()["id"]
            
            # Try to process (should fail)
            async with get_db_session() as db_session:
                service = ContentGenerationService(db_session.session)
                with pytest.raises(Exception):
                    await service.process_generation(generation_id)
                await db_session.commit()
            
            # Check status is failed
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/content/generations/{generation_id}",
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == GenerationStatus.FAILED.value
            assert "error_message" in data
    
    async def test_invalid_file_type(self, db, test_user, auth_headers, tmp_path):
        """Test uploading invalid file type."""
        # Create a .exe file
        exe_file = tmp_path / "malicious.exe"
        exe_file.write_bytes(b"MZ\x90\x00")  # Fake exe header
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            with open(exe_file, 'rb') as f:
                response = await client.post(
                    "/api/v1/content/generate",
                    headers=auth_headers,
                    files={"file": ("malicious.exe", f, "application/x-msdownload")},
                    data={
                        "title": "Invalid Test",
                        "content_type": ContentType.TOPIC_SUMMARY.value
                    }
                )
        
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]


@pytest.mark.e2e
@pytest.mark.slow
class TestPerformanceScenarios:
    """Test performance under various scenarios."""
    
    async def test_large_file_upload(self, db, test_user, auth_headers, tmp_path, mock_celery):
        """Test uploading a large file."""
        # Create a 10MB PDF-like file
        large_file = tmp_path / "large.pdf"
        pdf_header = b"%PDF-1.4\n"
        pdf_content = b"0" * (10 * 1024 * 1024 - len(pdf_header))  # 10MB
        large_file.write_bytes(pdf_header + pdf_content)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            with open(large_file, 'rb') as f:
                response = await client.post(
                    "/api/v1/content/generate",
                    headers=auth_headers,
                    files={"file": ("large.pdf", f, "application/pdf")},
                    data={
                        "title": "Large File Test",
                        "content_type": ContentType.FULL_CERTIFICATION.value
                    },
                    timeout=30.0  # Increase timeout for large file
                )
        
        assert response.status_code == 200
    
    async def test_rapid_api_calls(self, db, test_user, auth_headers):
        """Test rapid successive API calls."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make 20 rapid requests
            tasks = []
            for _ in range(20):
                task = client.get(
                    "/api/v1/content/generations",
                    headers=auth_headers
                )
                tasks.append(task)
            
            # Execute all at once
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            for response in responses:
                assert response.status_code == 200


@pytest.mark.e2e
class TestDataIntegrity:
    """Test data integrity across operations."""
    
    async def test_transaction_rollback(self, db, test_user, mocker):
        """Test that failed operations rollback properly."""
        from certify_studio.database.repositories import ContentRepository
        
        # Count initial generations
        repo = ContentRepository(db)
        initial_count = len(await repo.get_all())
        
        # Create a service that will fail mid-operation
        service = ContentGenerationService(db)
        service.content_repo.create_content_piece = mocker.AsyncMock(
            side_effect=Exception("Database error")
        )
        
        # Try to process (should fail)
        with pytest.raises(Exception):
            generation = await service.content_repo.create_generation(
                user_id=test_user.id,
                source_file_path="/test.pdf",
                source_file_name="test.pdf",
                title="Rollback Test",
                content_type=ContentType.TOPIC_SUMMARY
            )
            # This should fail
            await service._generate_content(generation, {})
        
        # Rollback should have occurred
        await db.rollback()
        
        # Count should be unchanged
        final_count = len(await repo.get_all())
        assert final_count == initial_count
    
    async def test_concurrent_updates(self, db, test_user, helpers):
        """Test concurrent updates to same resource."""
        # Create a generation
        generation = await helpers.create_test_generation(db, test_user)
        await db.commit()
        
        # Simulate two concurrent sessions updating the same generation
        async def update_progress(progress_value):
            async with get_db_session() as session:
                from sqlalchemy import select
                from certify_studio.database.models import ContentGeneration
                
                stmt = select(ContentGeneration).where(
                    ContentGeneration.id == generation.id
                )
                result = await session.session.execute(stmt)
                gen = result.scalar_one()
                
                gen.progress = progress_value
                await asyncio.sleep(0.1)  # Simulate processing
                await session.commit()
        
        # Run concurrent updates
        await asyncio.gather(
            update_progress(50),
            update_progress(75)
        )
        
        # Check final state (one should win)
        await db.refresh(generation)
        assert generation.progress in [50, 75]
