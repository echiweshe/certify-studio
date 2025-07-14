"""
Test Utilities

Common utilities and helpers for tests.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path

from certify_studio.database.models import (
    User, ContentGeneration, ContentPiece,
    QualityCheck, GenerationAnalytics
)
from certify_studio.database import get_db_session


class TestDataBuilder:
    """Builder pattern for creating test data."""
    
    @staticmethod
    async def create_full_generation_with_data(user: User) -> Dict[str, Any]:
        """Create a complete generation with all related data."""
        async with get_db_session() as db:
            # Create generation
            generation = ContentGeneration(
                user_id=user.id,
                source_file_path="/test/complete.pdf",
                source_file_name="complete.pdf",
                title="Complete Test Generation",
                content_type="full_certification",
                status="completed",
                progress=100,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                total_tokens_used=5000
            )
            db.session.add(generation)
            await db.session.flush()
            
            # Create content pieces
            pieces = []
            for i in range(3):
                piece = ContentPiece(
                    generation_id=generation.id,
                    piece_type="chapter",
                    title=f"Chapter {i+1}",
                    content=f"Content for chapter {i+1}",
                    order_index=i,
                    metadata={"chapter_number": i+1}
                )
                db.session.add(piece)
                pieces.append(piece)
            
            # Create quality checks
            quality_check = QualityCheck(
                generation_id=generation.id,
                check_type="automated",
                check_name="Full Quality Check",
                status="completed",
                overall_score=0.88,
                passed=True,
                details={
                    "metrics": {
                        "clarity": 0.9,
                        "accuracy": 0.85,
                        "completeness": 0.88
                    }
                }
            )
            db.session.add(quality_check)
            
            # Create analytics
            analytics = GenerationAnalytics(
                generation_id=generation.id,
                user_id=user.id,
                content_type="full_certification",
                started_at=generation.started_at,
                completed_at=generation.completed_at,
                tokens_used=5000,
                cost_cents=150
            )
            db.session.add(analytics)
            
            await db.commit()
            
            return {
                "generation": generation,
                "pieces": pieces,
                "quality_check": quality_check,
                "analytics": analytics
            }


class MockFileGenerator:
    """Generate mock files for testing."""
    
    @staticmethod
    def create_pdf(path: Path, size_mb: float = 1.0) -> Path:
        """Create a mock PDF file."""
        pdf_header = b"%PDF-1.4\n"
        pdf_footer = b"\n%%EOF"
        
        # Calculate content size
        content_size = int(size_mb * 1024 * 1024) - len(pdf_header) - len(pdf_footer)
        
        # Create some "pages"
        pages = []
        page_template = """
        1 0 obj
        << /Type /Page /Parent 2 0 R /Resources << >> >>
        endobj
        """
        
        for i in range(max(1, content_size // 1000)):
            pages.append(page_template.encode())
        
        # Combine
        content = pdf_header + b''.join(pages) + b'0' * (content_size - sum(len(p) for p in pages)) + pdf_footer
        
        path.write_bytes(content)
        return path
    
    @staticmethod
    def create_text_file(path: Path, content: str = None) -> Path:
        """Create a text file with content."""
        if content is None:
            content = """
            # AWS Certification Study Guide
            
            ## Chapter 1: Introduction to Cloud Computing
            
            Cloud computing is the on-demand delivery of IT resources...
            
            ## Chapter 2: AWS Core Services
            
            ### EC2 - Elastic Compute Cloud
            Virtual servers in the cloud...
            
            ### S3 - Simple Storage Service
            Object storage built to retrieve any amount of data...
            """
        
        path.write_text(content)
        return path


class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        
    async def __aenter__(self):
        self.start_time = asyncio.get_event_loop().time()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = asyncio.get_event_loop().time()
        duration = self.end_time - self.start_time
        print(f"{self.name} took {duration:.2f} seconds")
        
    @property
    def duration(self) -> float:
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return 0.0


class APITestClient:
    """Enhanced test client with common operations."""
    
    def __init__(self, client, auth_headers: Optional[Dict[str, str]] = None):
        self.client = client
        self.auth_headers = auth_headers or {}
        
    async def create_generation(
        self,
        title: str,
        file_path: Path,
        content_type: str = "full_certification"
    ) -> Dict[str, Any]:
        """Create a content generation."""
        with open(file_path, 'rb') as f:
            response = await self.client.post(
                "/api/v1/content/generate",
                headers=self.auth_headers,
                files={"file": (file_path.name, f, "application/pdf")},
                data={
                    "title": title,
                    "content_type": content_type
                }
            )
        
        assert response.status_code == 200
        return response.json()
    
    async def wait_for_generation(
        self,
        generation_id: str,
        timeout: float = 30.0,
        poll_interval: float = 1.0
    ) -> Dict[str, Any]:
        """Wait for generation to complete."""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            response = await self.client.get(
                f"/api/v1/content/generations/{generation_id}",
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            if data["status"] in ["completed", "failed"]:
                return data
                
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Generation {generation_id} did not complete in {timeout}s")
                
            await asyncio.sleep(poll_interval)


def assert_valid_uuid(value: str):
    """Assert that a string is a valid UUID."""
    import uuid
    try:
        uuid.UUID(value)
    except ValueError:
        pytest.fail(f"Invalid UUID: {value}")


def assert_datetime_recent(dt_str: str, max_age_seconds: float = 60):
    """Assert that a datetime string represents a recent time."""
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    age = (datetime.utcnow() - dt).total_seconds()
    assert age >= 0, f"Datetime is in the future: {dt_str}"
    assert age <= max_age_seconds, f"Datetime is too old: {dt_str} (age: {age}s)"


def compare_json_structures(actual: Any, expected: Any, path: str = "root"):
    """Deep comparison of JSON structures with helpful error messages."""
    if type(actual) != type(expected):
        pytest.fail(f"Type mismatch at {path}: {type(actual)} != {type(expected)}")
        
    if isinstance(expected, dict):
        for key in expected:
            if key not in actual:
                pytest.fail(f"Missing key at {path}.{key}")
            compare_json_structures(actual[key], expected[key], f"{path}.{key}")
            
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            pytest.fail(f"List length mismatch at {path}: {len(actual)} != {len(expected)}")
        for i, (a, e) in enumerate(zip(actual, expected)):
            compare_json_structures(a, e, f"{path}[{i}]")
            
    else:
        # Allow some flexibility for generated values
        if expected == "<uuid>":
            assert_valid_uuid(actual)
        elif expected == "<datetime>":
            assert_datetime_recent(actual)
        elif expected == "<number>":
            assert isinstance(actual, (int, float))
        elif expected == "<string>":
            assert isinstance(actual, str)
        else:
            assert actual == expected, f"Value mismatch at {path}: {actual} != {expected}"
