"""
AWS AI Practitioner Certification Test Workflow
==============================================
Real-world test using actual AWS certification materials.
This tests the complete Certify Studio platform capabilities.
"""

import asyncio
import aiohttp
import os
import sys
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

class AWSCertificationWorkflowTest:
    """Complete workflow test for AWS AI Practitioner certification"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "summary": {}
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: Dict[str, Any] = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results["tests"].append(result)
        
        status = "✅" if success else "❌"
        print(f"\n{status} {test_name}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2)}")
    
    async def test_server_health(self) -> bool:
        """Test 1: Server Health Check"""
        try:
            async with self.session.get(f"{self.base_url}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log_test("Server Health Check", True, data)
                    return True
                else:
                    self.log_test("Server Health Check", False, {"status": resp.status})
                    return False
        except Exception as e:
            self.log_test("Server Health Check", False, {"error": str(e)})
            return False
    
    async def test_api_info(self) -> bool:
        """Test 2: API Information and Agent Status"""
        try:
            async with self.session.get(f"{self.base_url}/api/v1/info") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log_test("API Info Check", True, data)
                    
                    # Check agent statuses
                    agents = data.get("agents", {})
                    all_ready = all(agent.get("status") == "ready" for agent in agents.values())
                    
                    if all_ready:
                        print("   ✅ All agents are ready!")
                    else:
                        print("   ⚠️ Some agents are not ready")
                        
                    return True
                else:
                    self.log_test("API Info Check", False, {"status": resp.status})
                    return False
        except Exception as e:
            self.log_test("API Info Check", False, {"error": str(e)})
            return False
    
    async def test_authentication(self) -> bool:
        """Test 3: Authentication Flow"""
        try:
            # Register a test user
            register_data = {
                "email": "aws-test@certify-studio.com",
                "password": "AWSTest123!",
                "full_name": "AWS Certification Tester"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=register_data
            ) as resp:
                if resp.status in [200, 201]:
                    self.log_test("User Registration", True)
                elif resp.status == 400:
                    # User already exists
                    self.log_test("User Registration", True, {"note": "User already exists"})
                    
            # Login
            login_data = {
                "username": register_data["email"],
                "password": register_data["password"]
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data  # Form data for OAuth2
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get("access_token")
                    self.log_test("User Login", True, {"token_type": data.get("token_type")})
                    return True
                else:
                    self.log_test("User Login", False, {"status": resp.status})
                    return False
                    
        except Exception as e:
            self.log_test("Authentication Flow", False, {"error": str(e)})
            return False
    
    async def test_pdf_upload(self, pdf_path: str) -> Optional[str]:
        """Test 4: PDF Upload"""
        if not os.path.exists(pdf_path):
            self.log_test("PDF Upload", False, {"error": f"File not found: {pdf_path}"})
            return None
            
        try:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
                
            file_size = os.path.getsize(pdf_path)
            file_name = os.path.basename(pdf_path)
            
            with open(pdf_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file',
                              f,
                              filename=file_name,
                              content_type='application/pdf')
                
                start_time = time.time()
                async with self.session.post(
                    f"{self.base_url}/api/v1/generation/upload",
                    data=data,
                    headers=headers
                ) as resp:
                    upload_time = time.time() - start_time
                    
                    if resp.status == 200:
                        result = await resp.json()
                        self.log_test("PDF Upload", True, {
                            "file": file_name,
                            "size": f"{file_size / 1024 / 1024:.2f} MB",
                            "upload_time": f"{upload_time:.2f}s",
                            "upload_id": result.get("upload_id")
                        })
                        return result.get("upload_id")
                    else:
                        error = await resp.text()
                        self.log_test("PDF Upload", False, {
                            "status": resp.status,
                            "error": error
                        })
                        return None
                        
        except Exception as e:
            self.log_test("PDF Upload", False, {"error": str(e)})
            return None
    
    async def test_domain_extraction(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """Test 5: Domain Knowledge Extraction"""
        try:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
                
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/domains/extract/{upload_id}",
                headers=headers
            ) as resp:
                extraction_time = time.time() - start_time
                
                if resp.status == 200:
                    result = await resp.json()
                    
                    # Analyze extracted domains
                    domains = result.get("domains", [])
                    total_weight = sum(d.get("weight", 0) for d in domains)
                    
                    self.log_test("Domain Extraction", True, {
                        "extraction_time": f"{extraction_time:.2f}s",
                        "domains_found": len(domains),
                        "total_weight": f"{total_weight:.1f}%",
                        "top_domains": [d["name"] for d in domains[:3]]
                    })
                    return result
                else:
                    error = await resp.text()
                    self.log_test("Domain Extraction", False, {
                        "status": resp.status,
                        "error": error
                    })
                    return None
                    
        except Exception as e:
            self.log_test("Domain Extraction", False, {"error": str(e)})
            return None
    
    async def test_content_generation(self, upload_id: str) -> Optional[str]:
        """Test 6: Content Generation"""
        try:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
                
            # Configure generation for AWS certification
            generation_config = {
                "format": "structured",
                "include_animations": True,
                "difficulty_level": "professional",
                "target_audience": "aws_practitioners",
                "features": {
                    "interactive_labs": True,
                    "practice_questions": True,
                    "visual_explanations": True,
                    "code_examples": True
                }
            }
            
            generation_data = {
                "upload_id": upload_id,
                "config": generation_config
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/generation/generate",
                json=generation_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.log_test("Content Generation Start", True, {
                        "job_id": result.get("job_id"),
                        "estimated_time": result.get("estimated_time", "unknown")
                    })
                    return result.get("job_id")
                else:
                    error = await resp.text()
                    self.log_test("Content Generation Start", False, {
                        "status": resp.status,
                        "error": error
                    })
                    return None
                    
        except Exception as e:
            self.log_test("Content Generation Start", False, {"error": str(e)})
            return None
    
    async def test_generation_status(self, job_id: str) -> Dict[str, Any]:
        """Test 7: Monitor Generation Progress"""
        try:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
                
            max_wait = 300  # 5 minutes max
            check_interval = 5  # Check every 5 seconds
            elapsed = 0
            
            while elapsed < max_wait:
                async with self.session.get(
                    f"{self.base_url}/api/v1/generation/status/{job_id}",
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        status = await resp.json()
                        
                        progress = status.get("progress", 0)
                        state = status.get("status", "unknown")
                        
                        print(f"\r   Progress: {progress}% - Status: {state}", end="")
                        
                        if state == "completed":
                            print()  # New line
                            self.log_test("Generation Completion", True, {
                                "total_time": f"{elapsed}s",
                                "final_status": state,
                                "content_id": status.get("content_id")
                            })
                            return status
                        elif state == "failed":
                            print()  # New line
                            self.log_test("Generation Completion", False, {
                                "total_time": f"{elapsed}s",
                                "final_status": state,
                                "error": status.get("error")
                            })
                            return status
                            
                await asyncio.sleep(check_interval)
                elapsed += check_interval
                
            self.log_test("Generation Completion", False, {"error": "Timeout"})
            return {"status": "timeout"}
            
        except Exception as e:
            self.log_test("Generation Status Check", False, {"error": str(e)})
            return {"status": "error", "error": str(e)}
    
    async def test_quality_check(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Test 8: Quality Assurance Check"""
        try:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
                
            async with self.session.post(
                f"{self.base_url}/api/v1/quality/check/{content_id}",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    
                    scores = result.get("scores", {})
                    passed = result.get("passed", False)
                    
                    self.log_test("Quality Check", passed, {
                        "overall_score": scores.get("overall", 0),
                        "pedagogical_score": scores.get("pedagogical", 0),
                        "technical_accuracy": scores.get("technical", 0),
                        "accessibility_score": scores.get("accessibility", 0),
                        "passed": passed
                    })
                    return result
                else:
                    error = await resp.text()
                    self.log_test("Quality Check", False, {
                        "status": resp.status,
                        "error": error
                    })
                    return None
                    
        except Exception as e:
            self.log_test("Quality Check", False, {"error": str(e)})
            return None
    
    async def test_export_formats(self, content_id: str) -> Dict[str, bool]:
        """Test 9: Export to Multiple Formats"""
        export_results = {}
        
        formats = ["pdf", "html", "scorm", "video", "interactive"]
        
        for format_type in formats:
            try:
                headers = {}
                if self.auth_token:
                    headers["Authorization"] = f"Bearer {self.auth_token}"
                    
                export_data = {
                    "format": format_type,
                    "options": {
                        "include_answers": True,
                        "include_animations": True,
                        "quality": "high"
                    }
                }
                
                async with self.session.post(
                    f"{self.base_url}/api/v1/export/{content_id}",
                    json=export_data,
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        export_results[format_type] = True
                        self.log_test(f"Export to {format_type.upper()}", True, {
                            "export_id": result.get("export_id"),
                            "file_size": result.get("file_size")
                        })
                    else:
                        export_results[format_type] = False
                        self.log_test(f"Export to {format_type.upper()}", False, {
                            "status": resp.status
                        })
                        
            except Exception as e:
                export_results[format_type] = False
                self.log_test(f"Export to {format_type.upper()}", False, {"error": str(e)})
                
        return export_results
    
    async def test_real_time_updates(self) -> bool:
        """Test 10: WebSocket Real-time Updates"""
        try:
            # Test WebSocket connection
            ws_url = self.base_url.replace("http://", "ws://") + "/ws"
            
            async with self.session.ws_connect(ws_url) as ws:
                # Send test message
                await ws.send_json({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                })
                
                # Wait for response
                msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    self.log_test("WebSocket Connection", True, data)
                    return True
                else:
                    self.log_test("WebSocket Connection", False, {"msg_type": str(msg.type)})
                    return False
                    
        except asyncio.TimeoutError:
            self.log_test("WebSocket Connection", False, {"error": "Timeout"})
            return False
        except Exception as e:
            self.log_test("WebSocket Connection", False, {"error": str(e)})
            return False
    
    async def run_complete_workflow(self):
        """Run the complete AWS certification workflow test"""
        print("="*60)
        print("AWS AI Practitioner Certification Workflow Test")
        print("="*60)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {self.base_url}")
        print("="*60)
        
        # Define test files
        exam_guide = r"C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio\downloads\aws\AIF-C01\AWS-Certified-AI-Practitioner_Exam-Guide.pdf"
        course_material = r"C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio\downloads\aws\AIF-C01\Secitons-1-to-7-AI1-C01-Official-Course.pdf"
        
        # Run tests
        success_count = 0
        total_tests = 0
        
        # Test 1: Server Health
        total_tests += 1
        if await self.test_server_health():
            success_count += 1
        else:
            print("\n⚠️ Server not responding. Please start the server first!")
            return
            
        # Test 2: API Info
        total_tests += 1
        if await self.test_api_info():
            success_count += 1
            
        # Test 3: Authentication
        total_tests += 1
        if await self.test_authentication():
            success_count += 1
            
        # Test 4: Upload Exam Guide
        print(f"\n📄 Uploading AWS AI Practitioner Exam Guide...")
        total_tests += 1
        upload_id = await self.test_pdf_upload(exam_guide)
        if upload_id:
            success_count += 1
            
            # Test 5: Domain Extraction
            total_tests += 1
            domains = await self.test_domain_extraction(upload_id)
            if domains:
                success_count += 1
                
                # Test 6: Content Generation
                total_tests += 1
                job_id = await self.test_content_generation(upload_id)
                if job_id:
                    success_count += 1
                    
                    # Test 7: Monitor Progress
                    total_tests += 1
                    status = await self.test_generation_status(job_id)
                    if status.get("status") == "completed":
                        success_count += 1
                        
                        content_id = status.get("content_id")
                        if content_id:
                            # Test 8: Quality Check
                            total_tests += 1
                            qa_result = await self.test_quality_check(content_id)
                            if qa_result and qa_result.get("passed"):
                                success_count += 1
                                
                            # Test 9: Export Formats
                            total_tests += 1
                            export_results = await self.test_export_formats(content_id)
                            if any(export_results.values()):
                                success_count += 1
        
        # Test 10: WebSocket
        total_tests += 1
        if await self.test_real_time_updates():
            success_count += 1
            
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {success_count}")
        print(f"Failed: {total_tests - success_count}")
        print(f"Success Rate: {(success_count/total_tests)*100:.1f}%")
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save results
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed": success_count,
            "failed": total_tests - success_count,
            "success_rate": (success_count/total_tests)*100,
            "end_time": datetime.now().isoformat()
        }
        
        # Write results to file
        results_file = Path(__file__).parent / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
            
        print(f"\n📊 Detailed results saved to: {results_file}")
        
        # Overall verdict
        if success_count == total_tests:
            print("\n🎉 ALL TESTS PASSED! The system is ready for production!")
        elif success_count >= total_tests * 0.8:
            print("\n✅ Most tests passed. System is mostly functional.")
        else:
            print("\n❌ Many tests failed. System needs attention.")

async def main():
    """Run the test suite"""
    async with AWSCertificationWorkflowTest() as tester:
        await tester.run_complete_workflow()

if __name__ == "__main__":
    asyncio.run(main())
