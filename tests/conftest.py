"""
Test Configuration for Certify Studio

This module sets up pytest configuration, fixtures, and test utilities.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from certify_studio.database import Base, get_db_session
from certify_studio.database.models import User, Role, Permission
from certify_studio.database.repositories import UserRepository
from certify_studio.core.config import settings
from certify_studio.integration.events import EventBus
from certify_studio.agents import AgenticOrchestrator as AgentOrchestrator


# Override settings for testing
# settings.TESTING = True  # Field doesn't exist
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost/certify_studio_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Disable pooling for tests
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction
    from sqlalchemy.orm import sessionmaker
    
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def db(db_session):
    """Alias for db_session fixture."""
    return db_session


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user."""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user_repo = UserRepository(db)
    
    user = await user_repo.create_user(
        email="test@example.com",
        username="testuser",
        hashed_password=pwd_context.hash("testpass123"),
        full_name="Test User",
        is_active=True
    )
    
    # Create and assign user role
    user_role = Role(name="user", description="Test user role")
    db.add(user_role)
    await db.flush()
    
    await user_repo.assign_role(user.id, "user")
    
    return user


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    """Create an admin user."""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user_repo = UserRepository(db)
    
    admin = await user_repo.create_user(
        email="admin@example.com",
        username="admin",
        hashed_password=pwd_context.hash("adminpass123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True
    )
    
    # Create and assign admin role
    admin_role = Role(name="admin", description="Admin role")
    db.add(admin_role)
    await db.flush()
    
    # Add all permissions
    permission = Permission(resource="*", action="*")
    db.add(permission)
    await db.flush()
    
    await user_repo.assign_role(admin.id, "admin")
    
    return admin


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authorization headers for test user."""
    from certify_studio.integration.services import UserService
    
    # Create JWT token
    token = asyncio.run(UserService(None).create_access_token(test_user))
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    """Create authorization headers for admin user."""
    from certify_studio.integration.services import UserService
    
    # Create JWT token
    token = asyncio.run(UserService(None).create_access_token(admin_user))
    
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def event_bus() -> EventBus:
    """Create a test event bus."""
    bus = EventBus()
    await bus.start()
    yield bus
    await bus.stop()


@pytest_asyncio.fixture
async def mock_orchestrator(mocker):
    """Create a mock agent orchestrator."""
    mock = mocker.AsyncMock(spec=AgentOrchestrator)
    mock.initialize = mocker.AsyncMock()
    mock.shutdown = mocker.AsyncMock()
    return mock


@pytest.fixture
def sample_pdf_file(tmp_path):
    """Create a sample PDF file for testing."""
    # Create a minimal PDF
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Times-Roman >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Test Content) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000314 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
406
%%EOF"""
    
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(pdf_content)
    return pdf_path


@pytest.fixture
def mock_celery(mocker):
    """Mock Celery for testing."""
    mock_celery = mocker.patch("certify_studio.integration.background.celery_app")
    mock_celery.send_task = mocker.Mock(return_value=mocker.Mock(id="test-task-id"))
    return mock_celery


# Test utilities
class TestHelpers:
    """Helper functions for tests."""
    
    @staticmethod
    async def create_test_generation(db: AsyncSession, user: User):
        """Create a test content generation."""
        from certify_studio.database.models import ContentGeneration, ContentType
        from certify_studio.database.repositories import ContentRepository
        
        repo = ContentRepository(db)
        generation = await repo.create_generation(
            user_id=user.id,
            source_file_path="/test/file.pdf",
            source_file_name="test.pdf",
            title="Test Generation",
            content_type=ContentType.FULL_CERTIFICATION
        )
        
        return generation
    
    @staticmethod
    async def create_test_content_piece(db: AsyncSession, generation_id):
        """Create a test content piece."""
        from certify_studio.database.models import ContentPiece
        from certify_studio.database.repositories import ContentRepository
        
        repo = ContentRepository(db)
        piece = await repo.create_content_piece(
            generation_id=generation_id,
            piece_type="section",
            title="Test Section",
            content="Test content",
            order_index=1,
            metadata={"test": True}
        )
        
        return piece


@pytest.fixture
def helpers():
    """Provide test helpers."""
    return TestHelpers()


# Async test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
