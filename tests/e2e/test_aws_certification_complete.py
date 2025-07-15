"""
End-to-End AWS Certification Workflow Test
=========================================
Complete workflow test using real AWS AI Practitioner materials.
"""

import pytest
import asyncio
import aiohttp
import os
from pathlib import Path
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))


class TestAWSCertificationE2E:
    """End-to-end test for AWS AI Practitioner certification workflow"""
    
    BASE_URL = "http://localhost:8000"
    AWS_MATERIALS_PATH = Path(__file__).parent.parent.parent / "downloads" / "aws" / "AIF-C01"
    
    @pytest.fixture
    async def session(self):
        """Create aiohttp session"""
        async with aiohttp.ClientSession() as session:
            yield session
            
    @pytest.fixture
    async def auth_token(self, session):
        """Get authentication token"""
        # Register/login
        user_data = {
            "email": "aws-e2e-test@certify-studio.com",
            "password": "AWSTest123!",
            "full_name": "AWS E2E Tester"
        }
        
        # Try to register (might already exist)
        await session.post(
            f"{self.BASE_URL}/api/v1/auth/register",
            json=user_data
        )
        
        # Login
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        
        async with session.post(
            f"{self.BASE_URL}/api/v1/auth/login",
            data=login_data
        ) as resp:
            assert resp.status == 200
            data = await resp.json()
            return data["access_token"]
    
    @pytest.mark.asyncio
    async def test_server_health(self, session):
        """Test server is healthy and ready"""
        async with session.get(f"{self.BASE_URL}/health") as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "healthy"
            assert all(agent["status"] == "ready" 
                      for agent in data.get("agents", {}).values())
    
    @pytest.mark.asyncio
    async def test_exam_guide_workflow(self, session, auth_token):
        """Test complete workflow with exam guide PDF"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Check if exam guide exists
        exam_guide_path = self.AWS_MATERIALS_PATH / "AWS-Certified-AI-Practitioner_Exam-Guide.pdf"
        assert exam_guide_path.exists(), f"Exam guide not found at {exam_guide_path}"
        
        # Step 1: Upload PDF
        print("\n📄 Uploading AWS AI Practitioner Exam Guide...")
        with open(exam_guide_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file',
                          f,
                          filename='AWS-Certified-AI-Practitioner_Exam-Guide.pdf',
                          content_type='application/pdf')
            
            async with session.post(
                f"{self.BASE_URL}/api/v1/generation/upload",
                data=data,
                headers=headers
            ) as resp:
                assert resp.status == 200
                upload_data = await resp.json()
                upload_id = upload_data["upload_id"]
                print(f"✅ Upload successful: {upload_id}")
        
        # Step 2: Extract domains
        print("\n🔍 Extracting knowledge domains...")
        async with session.post(
            f"{self.BASE_URL}/api/v1/domains/extract/{upload_id}",
            headers=headers
        ) as resp:
            assert resp.status == 200
            domains_data = await resp.json()
            domains = domains_data["domains"]
            
            print(f"✅ Found {len(domains)} domains:")
            for domain in domains[:5]:  # Show first 5
                print(f"   - {domain['name']}: {domain['weight']:.1f}%")
        
        # Step 3: Generate content
        print("\n🎨 Generating certification content...")
        generation_config = {
            "upload_id": upload_id,
            "config": {
                "format": "structured",
                "include_animations": True,
                "difficulty_level": "professional",
                "target_audience": "aws_practitioners",
                "features": {
                    "interactive_labs": True,
                    "practice_questions": True,
                    "visual_explanations": True,
                    "code_examples": True,
                    "case_studies": True
                },
                "optimization": {
                    "cognitive_load_balanced": True,
                    "spaced_repetition": True,
                    "adaptive_learning": True
                }
            }
        }
        
        async with session.post(
            f"{self.BASE_URL}/api/v1/generation/generate",
            json=generation_config,
            headers=headers
        ) as resp:
            assert resp.status == 200
            gen_data = await resp.json()
            job_id = gen_data["job_id"]
            print(f"✅ Generation job started: {job_id}")
        
        # Step 4: Monitor progress
        print("\n⏳ Monitoring generation progress...")
        content_id = await self._wait_for_generation(session, job_id, headers)
        assert content_id is not None
        
        # Step 5: Quality check
        print("\n✔️ Running quality assurance...")
        async with session.post(
            f"{self.BASE_URL}/api/v1/quality/check/{content_id}",
            headers=headers
        ) as resp:
            assert resp.status == 200
            qa_data = await resp.json()
            
            print(f"✅ Quality scores:")
            for metric, score in qa_data["scores"].items():
                print(f"   - {metric}: {score:.2f}")
            
            assert qa_data["passed"], "Quality check failed"
        
        # Step 6: Export to multiple formats
        print("\n📦 Exporting to multiple formats...")
        export_formats = ["pdf", "html", "scorm"]
        
        for format_type in export_formats:
            export_config = {
                "format": format_type,
                "options": {
                    "include_answers": True,
                    "include_animations": True,
                    "quality": "high",
                    "branding": {
                        "logo": "aws_logo.png",
                        "colors": {
                            "primary": "#FF9900",
                            "secondary": "#232F3E"
                        }
                    }
                }
            }
            
            async with session.post(
                f"{self.BASE_URL}/api/v1/export/{content_id}",
                json=export_config,
                headers=headers
            ) as resp:
                assert resp.status == 200
                export_data = await resp.json()
                print(f"✅ Exported to {format_type}: {export_data['export_id']}")
    
    @pytest.mark.asyncio
    async def test_course_material_workflow(self, session, auth_token):
        """Test workflow with full course material PDF"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Check if course material exists
        course_path = self.AWS_MATERIALS_PATH / "Secitons-1-to-7-AI1-C01-Official-Course.pdf"
        if not course_path.exists():
            pytest.skip(f"Course material not found at {course_path}")
        
        # Similar workflow but with larger file
        print("\n📚 Processing full course material (Sections 1-7)...")
        
        # This would follow similar steps but with different configuration
        # optimized for larger content
        
    @pytest.mark.asyncio
    async def test_concurrent_workflows(self, session, auth_token):
        """Test system handles multiple concurrent workflows"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create test PDFs
        test_pdfs = []
        for i in range(3):
            test_pdfs.append({
                "name": f"test_module_{i}.pdf",
                "content": f"%PDF-1.4\n%Test PDF {i}\n".encode()
            })
        
        # Upload all PDFs concurrently
        upload_tasks = []
        for pdf in test_pdfs:
            data = aiohttp.FormData()
            data.add_field('file',
                          pdf["content"],
                          filename=pdf["name"],
                          content_type='application/pdf')
            
            task = session.post(
                f"{self.BASE_URL}/api/v1/generation/upload",
                data=data,
                headers=headers
            )
            upload_tasks.append(task)
        
        # Wait for all uploads
        upload_responses = await asyncio.gather(*upload_tasks)
        
        # Verify all succeeded
        for resp in upload_responses:
            assert resp.status == 200
        
        print(f"✅ Successfully handled {len(test_pdfs)} concurrent uploads")
    
    @pytest.mark.asyncio
    async def test_websocket_updates(self, session):
        """Test WebSocket real-time updates"""
        ws_url = self.BASE_URL.replace("http://", "ws://") + "/ws"
        
        try:
            async with session.ws_connect(ws_url) as ws:
                # Subscribe to updates
                await ws.send_json({
                    "type": "subscribe",
                    "channels": ["generation", "agents"]
                })
                
                # Wait for confirmation
                msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                assert msg.type == aiohttp.WSMsgType.TEXT
                
                data = json.loads(msg.data)
                assert data.get("type") == "subscribed"
                
                print("✅ WebSocket connection established")
                
        except asyncio.TimeoutError:
            pytest.fail("WebSocket connection timeout")
    
    async def _wait_for_generation(self, session, job_id: str, headers: Dict[str, str], 
                                  timeout: int = 300) -> Optional[str]:
        """Wait for generation to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            async with session.get(
                f"{self.BASE_URL}/api/v1/generation/status/{job_id}",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    status_data = await resp.json()
                    progress = status_data.get("progress", 0)
                    state = status_data.get("status", "unknown")
                    
                    print(f"\r   Progress: {progress}% - {state}", end="", flush=True)
                    
                    if state == "completed":
                        print()  # New line
                        return status_data.get("content_id")
                    elif state == "failed":
                        print(f"\n❌ Generation failed: {status_data.get('error')}")
                        return None
            
            await asyncio.sleep(5)
        
        print("\n❌ Generation timeout")
        return None


class TestPerformanceE2E:
    """End-to-end performance tests"""
    
    @pytest.mark.asyncio
    async def test_response_times(self, session):
        """Test API response times meet SLA"""
        endpoints = [
            ("/health", "GET", None),
            ("/api/v1/info", "GET", None),
        ]
        
        for endpoint, method, data in endpoints:
            start_time = time.time()
            
            async with session.request(
                method,
                f"{TestAWSCertificationE2E.BASE_URL}{endpoint}",
                json=data
            ) as resp:
                response_time = time.time() - start_time
                
                # Health endpoints should respond quickly
                if "health" in endpoint or "info" in endpoint:
                    assert response_time < 1.0, f"{endpoint} too slow: {response_time}s"
                else:
                    assert response_time < 5.0, f"{endpoint} too slow: {response_time}s"
    
    @pytest.mark.asyncio
    async def test_throughput(self, session):
        """Test system throughput"""
        # Send multiple health check requests
        num_requests = 50
        
        async def single_request():
            async with session.get(f"{TestAWSCertificationE2E.BASE_URL}/health") as resp:
                return resp.status == 200
        
        start_time = time.time()
        tasks = [single_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        success_rate = sum(results) / num_requests
        requests_per_second = num_requests / total_time
        
        print(f"\n📊 Throughput test results:")
        print(f"   - Requests: {num_requests}")
        print(f"   - Total time: {total_time:.2f}s")
        print(f"   - Success rate: {success_rate*100:.1f}%")
        print(f"   - Throughput: {requests_per_second:.1f} req/s")
        
        assert success_rate > 0.95  # 95% success rate
        assert requests_per_second > 10  # At least 10 req/s


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto", "-s"])
