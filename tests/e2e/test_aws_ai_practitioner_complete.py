"""
Comprehensive Test Suite for AWS AI Practitioner Certification Content Generation
This module tests the complete workflow from PDF upload to content generation
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import pytest
from httpx import AsyncClient, Client
import websocket
from datetime import datetime
import base64

# Test configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
TEST_PDF_PATH = Path("C:/ZBDuo_Share/Labs/src/BttlnsCldMCP/certify-studio/downloads/aws/AIF-C01/AWS-Certified-AI-Practitioner_Exam-Guide.pdf")
COURSE_PDF_PATH = Path("C:/ZBDuo_Share/Labs/src/BttlnsCldMCP/certify-studio/downloads/aws/AIF-C01/Secitons-1-to-7-AI1-C01-Official-Course.pdf")
ICONS_PATH = Path("C:/ZBDuo_Share/Labs/src/BttlnsCldMCP/certify-studio/downloads/aws/icons/Asset-Package_02072025.dee42cd0a6eaacc3da1ad9519579357fb546f803.zip")


class TestAWSAIPractitioner:
    """End-to-end test suite for AWS AI Practitioner certification content generation"""

    @pytest.fixture
    async def auth_token(self):
        """Get authentication token for API access"""
        async with AsyncClient(base_url=BASE_URL) as client:
            # Register a test user
            register_data = {
                "email": "test@certifystudio.com",
                "password": "TestPassword123!",
                "full_name": "Test User"
            }
            
            # Try to register (might already exist)
            await client.post(f"{API_PREFIX}/auth/register", json=register_data)
            
            # Login to get token
            login_data = {
                "username": "test@certifystudio.com",
                "password": "TestPassword123!"
            }
            
            response = await client.post(f"{API_PREFIX}/auth/login", data=login_data)
            if response.status_code == 200:
                token_data = response.json()
                return token_data["access_token"]
            else:
                pytest.skip(f"Authentication failed: {response.status_code}")

    @pytest.fixture
    async def authenticated_client(self, auth_token):
        """Create authenticated HTTP client"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        async with AsyncClient(base_url=BASE_URL, headers=headers) as client:
            yield client

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test basic health check endpoint"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "version" in data
            assert "services" in data

    @pytest.mark.asyncio
    async def test_api_info(self):
        """Test API info endpoint"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f"{API_PREFIX}/info")
            assert response.status_code == 200
            data = response.json()
            assert "platform" in data
            assert "agents" in data
            assert data["agents"]["status"] == "operational"

    @pytest.mark.asyncio
    async def test_pdf_upload_workflow(self, authenticated_client):
        """Test complete PDF upload and processing workflow"""
        
        # Step 1: Upload PDF
        print("\n=== Step 1: Uploading PDF ===")
        assert TEST_PDF_PATH.exists(), f"Test PDF not found: {TEST_PDF_PATH}"
        
        with open(TEST_PDF_PATH, 'rb') as f:
            files = {'file': ('exam-guide.pdf', f, 'application/pdf')}
            response = await authenticated_client.post(
                f"{API_PREFIX}/generation/upload",
                files=files
            )
        
        assert response.status_code == 200
        upload_data = response.json()
        assert "file_id" in upload_data
        assert "status" in upload_data
        file_id = upload_data["file_id"]
        print(f"✓ PDF uploaded successfully. File ID: {file_id}")

        # Step 2: Extract domains
        print("\n=== Step 2: Extracting domains ===")
        extract_request = {
            "file_id": file_id,
            "extraction_type": "comprehensive"
        }
        
        response = await authenticated_client.post(
            f"{API_PREFIX}/domains/extract",
            json=extract_request
        )
        
        assert response.status_code == 200
        domains_data = response.json()
        assert "domains" in domains_data
        assert len(domains_data["domains"]) > 0
        print(f"✓ Extracted {len(domains_data['domains'])} domains")
        
        for domain in domains_data["domains"][:3]:  # Show first 3 domains
            print(f"  - {domain['name']}: {domain['weight']}%")

        # Step 3: Generate content
        print("\n=== Step 3: Generating content ===")
        generation_request = {
            "file_id": file_id,
            "output_format": "interactive",
            "target_audience": "intermediate",
            "duration": 60,
            "enable_animations": True,
            "accessibility_level": "wcag_aa"
        }
        
        response = await authenticated_client.post(
            f"{API_PREFIX}/generation/generate",
            json=generation_request
        )
        
        assert response.status_code in [200, 202]  # 202 for async processing
        generation_data = response.json()
        assert "generation_id" in generation_data
        generation_id = generation_data["generation_id"]
        print(f"✓ Content generation started. ID: {generation_id}")

        # Step 4: Monitor progress
        print("\n=== Step 4: Monitoring progress ===")
        max_wait = 300  # 5 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = await authenticated_client.get(
                f"{API_PREFIX}/generation/status/{generation_id}"
            )
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "unknown")
                progress = status_data.get("progress", 0)
                current_stage = status_data.get("current_stage", "initializing")
                
                print(f"  Status: {status} | Progress: {progress}% | Stage: {current_stage}")
                
                if status == "completed":
                    print("✓ Content generation completed!")
                    break
                elif status == "failed":
                    pytest.fail(f"Generation failed: {status_data.get('error', 'Unknown error')}")
            
            await asyncio.sleep(5)  # Check every 5 seconds
        else:
            pytest.fail("Content generation timed out")

        # Step 5: Quality check
        print("\n=== Step 5: Running quality checks ===")
        qa_request = {
            "generation_id": generation_id,
            "checks": ["pedagogical", "technical", "accessibility", "completeness"]
        }
        
        response = await authenticated_client.post(
            f"{API_PREFIX}/quality/check",
            json=qa_request
        )
        
        assert response.status_code == 200
        qa_data = response.json()
        assert "results" in qa_data
        assert "overall_score" in qa_data
        
        print(f"✓ Quality check completed. Overall score: {qa_data['overall_score']}/100")
        for check, result in qa_data["results"].items():
            print(f"  - {check}: {result['score']}/100 ({result['status']})")

        # Step 6: Export content
        print("\n=== Step 6: Exporting content ===")
        export_formats = ["pdf", "scorm", "video"]
        
        for format in export_formats:
            export_request = {
                "generation_id": generation_id,
                "format": format,
                "include_assessments": True,
                "include_certificates": True
            }
            
            response = await authenticated_client.post(
                f"{API_PREFIX}/export/create",
                json=export_request
            )
            
            if response.status_code == 200:
                export_data = response.json()
                print(f"✓ Exported to {format}: {export_data.get('download_url', 'Processing...')}")
            else:
                print(f"⚠ Export to {format} failed: {response.status_code}")

    @pytest.mark.asyncio
    async def test_agent_collaboration(self, authenticated_client):
        """Test real-time agent collaboration monitoring"""
        
        print("\n=== Testing Agent Collaboration ===")
        
        # Start a simple generation to trigger agent activity
        with open(TEST_PDF_PATH, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            response = await authenticated_client.post(
                f"{API_PREFIX}/generation/upload",
                files=files
            )
        
        file_id = response.json()["file_id"]
        
        # Connect to WebSocket for real-time updates
        ws_url = f"ws://localhost:8000/ws/agents"
        
        # Note: This is a simplified WebSocket test
        # In production, you'd use a proper WebSocket client
        
        # Monitor agent activities
        response = await authenticated_client.get(f"{API_PREFIX}/agents/activities")
        assert response.status_code == 200
        activities = response.json()
        
        print(f"✓ Found {len(activities)} agent activities")
        for activity in activities[:5]:  # Show first 5
            print(f"  - {activity['agent']}: {activity['action']} at {activity['timestamp']}")

    @pytest.mark.asyncio
    async def test_comprehensive_course_generation(self, authenticated_client):
        """Test generation with both exam guide and course materials"""
        
        print("\n=== Testing Comprehensive Course Generation ===")
        
        # Upload both PDFs
        files_to_upload = [
            ("exam-guide.pdf", TEST_PDF_PATH),
            ("course-materials.pdf", COURSE_PDF_PATH)
        ]
        
        file_ids = []
        for filename, filepath in files_to_upload:
            with open(filepath, 'rb') as f:
                files = {'file': (filename, f, 'application/pdf')}
                response = await authenticated_client.post(
                    f"{API_PREFIX}/generation/upload",
                    files=files
                )
                assert response.status_code == 200
                file_ids.append(response.json()["file_id"])
                print(f"✓ Uploaded {filename}")
        
        # Create comprehensive course
        course_request = {
            "file_ids": file_ids,
            "course_type": "certification_prep",
            "metadata": {
                "title": "AWS Certified AI Practitioner",
                "certification_code": "AIF-C01",
                "vendor": "AWS",
                "difficulty": "intermediate"
            },
            "generation_options": {
                "include_labs": True,
                "include_quizzes": True,
                "include_flashcards": True,
                "video_style": "animated",
                "language": "en"
            }
        }
        
        response = await authenticated_client.post(
            f"{API_PREFIX}/generation/course",
            json=course_request
        )
        
        assert response.status_code in [200, 202]
        course_data = response.json()
        print(f"✓ Course generation started: {course_data['course_id']}")
        
        # Wait for completion (simplified for demo)
        await asyncio.sleep(5)
        
        # Get course structure
        response = await authenticated_client.get(
            f"{API_PREFIX}/generation/course/{course_data['course_id']}/structure"
        )
        
        if response.status_code == 200:
            structure = response.json()
            print(f"✓ Course structure created:")
            print(f"  - Modules: {len(structure.get('modules', []))}")
            print(f"  - Total lessons: {structure.get('total_lessons', 0)}")
            print(f"  - Estimated duration: {structure.get('duration_hours', 0)} hours")


class TestAgentMetrics:
    """Test suite for agent performance metrics and monitoring"""
    
    @pytest.mark.asyncio
    async def test_agent_health_monitoring(self):
        """Test agent health monitoring endpoints"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f"{API_PREFIX}/agents/health")
            assert response.status_code == 200
            
            health_data = response.json()
            assert "agents" in health_data
            
            # Check each agent type
            expected_agents = [
                "content_generator",
                "domain_extractor",
                "quality_assurance",
                "export_manager"
            ]
            
            for agent_type in expected_agents:
                assert agent_type in health_data["agents"]
                agent_health = health_data["agents"][agent_type]
                assert "status" in agent_health
                assert "last_active" in agent_health
                assert "tasks_completed" in agent_health
                print(f"✓ {agent_type}: {agent_health['status']}")

    @pytest.mark.asyncio
    async def test_agent_performance_metrics(self):
        """Test agent performance metrics collection"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f"{API_PREFIX}/agents/metrics")
            assert response.status_code == 200
            
            metrics = response.json()
            assert "performance" in metrics
            assert "collaboration" in metrics
            
            print("\n=== Agent Performance Metrics ===")
            for agent, perf in metrics["performance"].items():
                print(f"{agent}:")
                print(f"  - Avg response time: {perf.get('avg_response_time', 0):.2f}s")
                print(f"  - Success rate: {perf.get('success_rate', 0):.1f}%")
                print(f"  - Tasks/hour: {perf.get('throughput', 0)}")


class TestDatabaseConnectivity:
    """Test database connectivity and operations"""
    
    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test database connectivity"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            
            health = response.json()
            db_status = health.get("services", {}).get("database", "unknown")
            
            if db_status == "not_configured":
                pytest.skip("Database not configured yet")
            else:
                assert db_status == "healthy"
                print("✓ Database connection healthy")

    @pytest.mark.asyncio
    async def test_data_persistence(self, authenticated_client):
        """Test data persistence across requests"""
        
        # Create a test project
        project_data = {
            "name": "AWS AI Practitioner Test",
            "description": "Test project for AWS certification",
            "tags": ["aws", "ai", "certification"]
        }
        
        response = await authenticated_client.post(
            f"{API_PREFIX}/projects/create",
            json=project_data
        )
        
        if response.status_code == 200:
            project = response.json()
            project_id = project["id"]
            print(f"✓ Project created: {project_id}")
            
            # Verify it persists
            response = await authenticated_client.get(
                f"{API_PREFIX}/projects/{project_id}"
            )
            assert response.status_code == 200
            retrieved = response.json()
            assert retrieved["name"] == project_data["name"]
            print("✓ Project data persisted correctly")
        else:
            pytest.skip("Project API not available")


class TestFrontendIntegration:
    """Test frontend-backend integration"""
    
    @pytest.mark.asyncio
    async def test_cors_headers(self):
        """Test CORS headers for frontend integration"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.options(
                f"{API_PREFIX}/info",
                headers={"Origin": "http://localhost:5173"}
            )
            
            # Check CORS headers
            assert "access-control-allow-origin" in response.headers
            assert "access-control-allow-methods" in response.headers
            print("✓ CORS properly configured for frontend")

    @pytest.mark.asyncio
    async def test_websocket_connectivity(self):
        """Test WebSocket connectivity for real-time updates"""
        # This is a placeholder - actual WebSocket testing would use websocket-client
        pass


if __name__ == "__main__":
    # Run specific test suites
    print("Starting Certify Studio Test Suite")
    print("==================================\n")
    
    # You can run specific tests with:
    # pytest test_aws_ai_practitioner_complete.py::TestAWSAIPractitioner::test_pdf_upload_workflow -v
    
    pytest.main([__file__, "-v", "-s"])
