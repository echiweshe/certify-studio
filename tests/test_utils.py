"""
Test utilities for Certify Studio tests
"""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, Optional
import httpx
import pytest


async def create_test_client(base_url: str = "http://localhost:8000") -> httpx.AsyncClient:
    """Create an async HTTP client for testing"""
    return httpx.AsyncClient(base_url=base_url, timeout=30.0)


async def authenticate_test_user(
    client: httpx.AsyncClient, 
    email: str = "test@certifystudio.com",
    password: str = "TestPassword123!"
) -> str:
    """Authenticate a test user and return the token"""
    # Try to login first
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
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
    
    raise Exception(f"Failed to authenticate: {register_response.text}")


async def upload_file_async(
    client: httpx.AsyncClient,
    file_path: Path,
    token: str,
    endpoint: str = "/api/v1/generation/upload"
) -> Dict[str, Any]:
    """Upload a file asynchronously"""
    with open(file_path, "rb") as f:
        files = {
            "file": (file_path.name, f, "application/pdf")
        }
        
        response = await client.post(
            endpoint,
            files=files,
            headers={"Authorization": f"Bearer {token}"}
        )
    
    if response.status_code != 200:
        raise Exception(f"Upload failed: {response.text}")
    
    return response.json()


async def wait_for_job_completion(
    client: httpx.AsyncClient,
    job_id: str,
    token: str,
    timeout: int = 300,
    poll_interval: int = 2
) -> Dict[str, Any]:
    """Wait for an async job to complete"""
    headers = {"Authorization": f"Bearer {token}"}
    start_time = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start_time < timeout:
        response = await client.get(
            f"/api/v1/jobs/{job_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["status"] in ["completed", "failed"]:
                if data["status"] == "failed":
                    raise Exception(f"Job failed: {data.get('error', 'Unknown error')}")
                return data
        
        await asyncio.sleep(poll_interval)
    
    raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")


async def download_export(
    client: httpx.AsyncClient,
    download_url: str,
    token: str,
    output_path: Path
) -> Path:
    """Download an exported file"""
    response = await client.get(
        download_url,
        headers={"Authorization": f"Bearer {token}"},
        follow_redirects=True
    )
    
    if response.status_code != 200:
        raise Exception(f"Download failed: {response.text}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    return output_path


class MockResponse:
    """Mock HTTP response for testing"""
    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.content = str(json_data).encode()
        self.text = str(json_data)
    
    def json(self):
        return self.json_data


def mock_successful_upload():
    """Mock a successful file upload response"""
    return MockResponse({
        "file_id": "test-file-123",
        "status": "uploaded",
        "file_size": 1024 * 1024,  # 1MB
        "page_count": 42
    })


def mock_domain_extraction():
    """Mock domain extraction response"""
    return MockResponse({
        "domains": [
            {
                "name": "Fundamentals of AI and ML",
                "weight": 0.25,
                "concepts": ["Machine Learning", "Deep Learning", "Neural Networks"]
            },
            {
                "name": "Fundamentals of Generative AI",
                "weight": 0.20,
                "concepts": ["LLMs", "Transformers", "Prompt Engineering"]
            },
            {
                "name": "Applications of Foundation Models",
                "weight": 0.20,
                "concepts": ["AWS Bedrock", "SageMaker", "Model Deployment"]
            },
            {
                "name": "Guidelines for Responsible AI",
                "weight": 0.20,
                "concepts": ["Bias", "Fairness", "Explainability"]
            },
            {
                "name": "Security, Compliance, and Governance for AI Solutions",
                "weight": 0.15,
                "concepts": ["Data Privacy", "Model Security", "Compliance"]
            }
        ]
    })


def mock_generation_complete():
    """Mock content generation completion"""
    return MockResponse({
        "status": "completed",
        "content_id": "content-456",
        "modules": [
            {"name": "Introduction to AI", "duration": 300},
            {"name": "Machine Learning Fundamentals", "duration": 600},
            {"name": "AWS AI Services", "duration": 900}
        ],
        "cognitive_optimization_applied": True
    })


def mock_quality_check():
    """Mock quality check results"""
    return MockResponse({
        "overall_score": 0.92,
        "results": {
            "content_accuracy": 0.95,
            "pedagogical_quality": 0.90,
            "accessibility_compliance": 0.93,
            "technical_accuracy": 0.91,
            "cognitive_load_balance": 0.89
        },
        "issues": [],
        "recommendations": [
            "Consider adding more interactive elements in Module 2",
            "Add captions to all video content"
        ]
    })


# Test fixtures
@pytest.fixture
async def test_client():
    """Fixture that provides an async HTTP client"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture
async def authenticated_client(test_client):
    """Fixture that provides an authenticated client"""
    token = await authenticate_test_user(test_client)
    test_client.headers["Authorization"] = f"Bearer {token}"
    yield test_client


@pytest.fixture
def test_pdf_path():
    """Fixture that provides a test PDF path"""
    # Create a simple test PDF if it doesn't exist
    test_path = Path("tests/fixtures/test.pdf")
    if not test_path.exists():
        test_path.parent.mkdir(parents=True, exist_ok=True)
        # Would create a simple PDF here in a real test
        test_path.write_text("Test PDF content")
    return test_path


# Utility functions for test assertions
def assert_valid_file_id(file_id: str):
    """Assert that a file ID is valid"""
    assert isinstance(file_id, str)
    assert len(file_id) > 0
    assert file_id != "null"
    assert file_id != "undefined"


def assert_valid_job_id(job_id: str):
    """Assert that a job ID is valid"""
    assert isinstance(job_id, str)
    assert len(job_id) > 0
    # Job IDs are typically UUIDs
    assert len(job_id.split("-")) == 5  # UUID format


def assert_valid_content_id(content_id: str):
    """Assert that a content ID is valid"""
    assert isinstance(content_id, str)
    assert len(content_id) > 0


def assert_quality_scores(scores: Dict[str, float], min_threshold: float = 0.8):
    """Assert that quality scores meet minimum thresholds"""
    for metric, score in scores.items():
        assert isinstance(score, (int, float))
        assert 0 <= score <= 1
        assert score >= min_threshold, f"{metric} score {score} is below threshold {min_threshold}"
