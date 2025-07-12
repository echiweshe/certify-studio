"""
Pytest configuration and fixtures for Certify Studio test suite.

This module provides common fixtures and configuration for all tests.
"""

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from certify_studio.config import Settings
from certify_studio.database.base import Base


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Create test-specific settings."""
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/1",
        environment="test",
        debug=True,
        log_level="DEBUG",
        jwt_secret="test-secret-key-for-testing-only",
        jwt_algorithm="HS256",
        jwt_expiration_minutes=30,
    )


@pytest_asyncio.fixture(scope="function")
async def db_engine(test_settings: Settings):
    """Create async database engine for tests."""
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,
        future=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for tests."""
    async_session_maker = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def sample_pdf_path() -> Path:
    """Provide path to sample PDF for testing."""
    return Path(__file__).parent / "fixtures" / "sample_certification.pdf"


@pytest.fixture
def sample_image_path() -> Path:
    """Provide path to sample image for testing."""
    return Path(__file__).parent / "fixtures" / "sample_diagram.png"


@pytest.fixture
def mock_llm_response() -> dict:
    """Provide mock LLM response for testing."""
    return {
        "content": "This is a mock response from the LLM.",
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        },
        "model": "claude-3-opus-20240229"
    }


@pytest.fixture
def mock_vision_response() -> dict:
    """Provide mock vision analysis response for testing."""
    return {
        "description": "AWS VPC architecture diagram showing public and private subnets",
        "objects": ["VPC", "Subnet", "EC2", "RDS", "NAT Gateway"],
        "relationships": [
            {"from": "EC2", "to": "Subnet", "type": "contained_in"},
            {"from": "Subnet", "to": "VPC", "type": "part_of"}
        ],
        "technical_accuracy": 0.95,
        "visual_clarity": 0.88
    }


@pytest.fixture
def learner_profile() -> dict:
    """Provide sample learner profile for testing."""
    return {
        "id": "test-learner-001",
        "experience_level": "intermediate",
        "learning_style": "visual",
        "pace_preference": "moderate",
        "prior_knowledge": ["networking", "linux", "python"],
        "goal": "aws_solutions_architect",
        "time_availability": "2_hours_daily"
    }


@pytest.fixture
def certification_metadata() -> dict:
    """Provide sample certification metadata for testing."""
    return {
        "name": "AWS Solutions Architect Associate",
        "code": "SAA-C03",
        "provider": "AWS",
        "duration": 130,
        "questions": 65,
        "passing_score": 720,
        "domains": [
            {
                "name": "Design Secure Architectures",
                "weight": 0.30,
                "topics": ["IAM", "VPC", "Security Groups"]
            },
            {
                "name": "Design Resilient Architectures", 
                "weight": 0.26,
                "topics": ["Multi-AZ", "Backup", "Disaster Recovery"]
            }
        ]
    }


# Markers for test categorization
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "agent_tests: marks tests related to agent functionality"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests that require external services"
    )
    config.addinivalue_line(
        "markers", "multimodal: marks tests that involve vision/audio processing"
    )
