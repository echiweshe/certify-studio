"""
Test Utilities for Certify Studio

Common utilities and helpers for testing.
"""

import asyncio
import time
from typing import Optional, Dict, Any
from pathlib import Path
import httpx
from httpx import AsyncClient


async def create_test_client(base_url: str = "http://localhost:8000") -> AsyncClient:
    """Create an async HTTP client for testing"""
    return AsyncClient(base_url=base_url, timeout=30.0)


async def authenticate_test_user(
    client: AsyncClient,
    email: str = "test@example.com",
    password: str = "TestPassword123!"
) -> Optional[str]:
    """Authenticate a test user and return access token"""
    
    # Try to login first
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    
    if login_response.status_code == 200:
        return login_response.json()["access_token"]
    
    # If login fails, try to register
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User"
        }
    )
    
    if register_response.status_code in [200, 201]:
        return register_response.json()["access_token"]
    
    return None


async def upload_file_async(
    client: AsyncClient,
    file_path: Path,
    endpoint: str,
    headers: Dict[str, str]
) -> Dict[str, Any]:
    """Upload a file asynchronously"""
    
    with open(file_path, "rb") as f:
        files = {
            "file": (
                file_path.name,
                f,
                "application/pdf" if file_path.suffix == ".pdf" else "application/octet-stream"
            )
        }
        
        response = await client.post(
            endpoint,
            files=files,
            headers=headers
        )
    
    response.raise_for_status()
    return response.json()


async def wait_for_job_completion(
    client: AsyncClient,
    job_id: str,
    headers: Dict[str, str],
    check_endpoint: str = "/api/v1/jobs/{job_id}",
    timeout: int = 300,
    poll_interval: int = 2
) -> Dict[str, Any]:
    """Wait for an async job to complete"""
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = await client.get(
            check_endpoint.format(job_id=job_id),
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") in ["completed", "failed", "error"]:
                return data
        
        await asyncio.sleep(poll_interval)
    
    raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")


async def download_export(
    client: AsyncClient,
    download_url: str,
    headers: Dict[str, str],
    output_path: Path
) -> Path:
    """Download an exported file"""
    
    response = await client.get(download_url, headers=headers)
    response.raise_for_status()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    return output_path


def assert_response_ok(response: httpx.Response, expected_status: int = 200):
    """Assert that response has expected status code"""
    if response.status_code != expected_status:
        raise AssertionError(
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )


def assert_json_contains(response_json: Dict[str, Any], required_keys: list):
    """Assert that JSON response contains required keys"""
    missing_keys = [key for key in required_keys if key not in response_json]
    if missing_keys:
        raise AssertionError(f"Response missing required keys: {missing_keys}")


class TestTimer:
    """Context manager for timing test operations"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        print(f"{self.name} took {self.duration:.2f} seconds")


# Mock data generators

def generate_test_pdf_content() -> bytes:
    """Generate mock PDF content for testing"""
    # This would normally create actual PDF bytes
    # For testing, we'll return a simple placeholder
    return b"%PDF-1.4\n%Mock PDF content for testing\n"


def generate_test_user(index: int = 0) -> Dict[str, str]:
    """Generate test user data"""
    return {
        "email": f"test_user_{index}_{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "full_name": f"Test User {index}"
    }


def generate_test_generation_config() -> Dict[str, Any]:
    """Generate test generation configuration"""
    return {
        "difficulty_level": "intermediate",
        "target_audience": "IT professionals",
        "include_hands_on_labs": True,
        "include_quizzes": True,
        "include_animations": True,
        "cognitive_load_optimization": True,
        "language": "en",
        "estimated_duration_hours": 10
    }


# Validation helpers

def validate_generation_result(result: Dict[str, Any]):
    """Validate generation result structure"""
    required_fields = ["content_id", "status", "modules"]
    assert all(field in result for field in required_fields), \
        f"Generation result missing required fields. Got: {result.keys()}"
    
    assert result["status"] == "completed", \
        f"Generation did not complete successfully. Status: {result['status']}"
    
    assert len(result["modules"]) > 0, \
        "Generation produced no modules"


def validate_export_result(result: Dict[str, Any]):
    """Validate export result structure"""
    required_fields = ["export_id", "status", "download_url"]
    assert all(field in result for field in required_fields), \
        f"Export result missing required fields. Got: {result.keys()}"
    
    assert result["status"] == "completed", \
        f"Export did not complete successfully. Status: {result['status']}"


def validate_qa_result(result: Dict[str, Any]):
    """Validate QA result structure"""
    required_fields = ["overall_score", "results", "issues"]
    assert all(field in result for field in required_fields), \
        f"QA result missing required fields. Got: {result.keys()}"
    
    assert 0 <= result["overall_score"] <= 1, \
        f"QA score out of range: {result['overall_score']}"
