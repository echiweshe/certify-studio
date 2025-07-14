"""
Unit tests for service layer.

Tests business logic in isolation from infrastructure.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from uuid import uuid4

from certify_studio.integration.services import (
    ContentGenerationService,
    DomainExtractionService,
    QualityAssuranceService,
    UserService,
    AnalyticsService
)
from certify_studio.database.models import (
    User, ContentGeneration, ContentType, GenerationStatus
)
from certify_studio.integration.events import ContentGenerationStartedEvent


@pytest.mark.unit
class TestContentGenerationService:
    """Test content generation service."""
    
    @pytest.fixture
    def mock_repos(self, mocker):
        """Mock repositories."""
        return {
            'content_repo': mocker.Mock(),
            'domain_repo': mocker.Mock(),
            'quality_repo': mocker.Mock(),
            'analytics_repo': mocker.Mock()
        }
    
    @pytest.fixture
    def service(self, mocker, mock_repos):
        """Create service with mocked dependencies."""
        mock_db = mocker.Mock()
        service = ContentGenerationService(mock_db)
        
        # Replace repositories
        service.content_repo = mock_repos['content_repo']
        service.domain_repo = mock_repos['domain_repo']
        service.quality_repo = mock_repos['quality_repo']
        service.analytics_repo = mock_repos['analytics_repo']
        
        # Mock orchestrator and event bus
        service.orchestrator = mocker.AsyncMock()
        service.event_bus = mocker.AsyncMock()
        
        return service
    
    async def test_start_generation(self, service, mock_repos, test_user, mocker):
        """Test starting a content generation."""
        # Mock file operations
        mock_file = mocker.Mock()
        mock_file.read = mocker.AsyncMock(return_value=b"test content")
        
        # Mock repository response
        mock_generation = ContentGeneration(
            id=uuid4(),
            user_id=test_user.id,
            source_file_path="/uploads/test.pdf",
            source_file_name="test.pdf",
            title="Test Certification",
            content_type=ContentType.FULL_CERTIFICATION,
            status=GenerationStatus.PENDING
        )
        mock_repos['content_repo'].create_generation.return_value = mock_generation
        
        # Mock Celery
        with patch('certify_studio.integration.services.celery_app') as mock_celery:
            mock_celery.send_task.return_value = Mock(id="task-123")
            
            # Call service
            result = await service.start_generation(
                user=test_user,
                source_file=mock_file,
                filename="test.pdf",
                title="Test Certification",
                content_type=ContentType.FULL_CERTIFICATION
            )
        
        # Verify generation created
        assert result.id == mock_generation.id
        assert result.title == "Test Certification"
        
        # Verify event emitted
        service.event_bus.emit.assert_called_once()
        event = service.event_bus.emit.call_args[0][0]
        assert isinstance(event, ContentGenerationStartedEvent)
        
        # Verify background task started
        mock_celery.send_task.assert_called_once_with(
            'process_content_generation',
            args=[str(mock_generation.id)]
        )
    
    async def test_process_generation_success(self, service, mock_repos, mocker):
        """Test successful generation processing."""
        generation_id = uuid4()
        
        # Mock generation
        mock_generation = Mock(
            id=generation_id,
            user_id=uuid4(),
            source_file_path="/test.pdf",
            status=GenerationStatus.PENDING
        )
        mock_repos['content_repo'].get_generation.return_value = mock_generation
        
        # Mock agent responses
        mock_domain_knowledge = {
            'concepts': [
                {'name': 'EC2', 'description': 'Compute service'},
                {'name': 'S3', 'description': 'Storage service'}
            ],
            'relationships': []
        }
        
        mock_learning_design = {
            'sections': [
                {
                    'type': 'introduction',
                    'title': 'Introduction to AWS',
                    'order': 1,
                    'duration': 10
                }
            ],
            'style_guide': {}
        }
        
        mock_content_result = {
            'content': 'Generated content here',
            'tokens_used': 1000
        }
        
        mock_quality_result = {
            'overall_score': 0.9,
            'passed': True,
            'metrics': {
                'clarity': 0.95,
                'accuracy': 0.88
            }
        }
        
        # Mock methods
        service._extract_domain_knowledge = mocker.AsyncMock(return_value=mock_domain_knowledge)
        service._generate_content = mocker.AsyncMock(return_value=[Mock()])
        service._run_quality_checks = mocker.AsyncMock(return_value=mock_quality_result)
        
        # Process generation
        result = await service.process_generation(generation_id)
        
        # Verify status updates
        assert mock_generation.status == GenerationStatus.COMPLETED
        assert mock_generation.progress == 100
        assert mock_generation.completed_at is not None
        
        # Verify all steps called
        service._extract_domain_knowledge.assert_called_once()
        service._generate_content.assert_called_once()
        service._run_quality_checks.assert_called_once()


@pytest.mark.unit
class TestUserService:
    """Test user service."""
    
    @pytest.fixture
    def service(self, mocker):
        """Create service with mocked dependencies."""
        mock_db = mocker.Mock()
        service = UserService(mock_db)
        service.user_repo = mocker.Mock()
        return service
    
    async def test_create_user(self, service, mocker):
        """Test user creation."""
        # Mock password hashing
        with patch('certify_studio.integration.services.CryptContext') as mock_crypt:
            mock_pwd_context = Mock()
            mock_pwd_context.hash.return_value = "hashed_password"
            mock_crypt.return_value = mock_pwd_context
            
            # Mock repository
            mock_user = User(
                id=uuid4(),
                email="new@example.com",
                username="newuser"
            )
            service.user_repo.create_user.return_value = mock_user
            service.user_repo.assign_role = mocker.AsyncMock()
            
            # Create user
            result = await service.create_user(
                email="new@example.com",
                username="newuser",
                password="password123",
                full_name="New User"
            )
            
            # Verify
            assert result.email == "new@example.com"
            mock_pwd_context.hash.assert_called_once_with("password123")
            service.user_repo.assign_role.assert_called_once_with(mock_user.id, "user")
    
    async def test_authenticate_user_success(self, service, mocker):
        """Test successful authentication."""
        # Mock user
        mock_user = User(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed"
        )
        service.user_repo.get_by_username.return_value = mock_user
        
        # Mock password verification
        with patch('certify_studio.integration.services.CryptContext') as mock_crypt:
            mock_pwd_context = Mock()
            mock_pwd_context.verify.return_value = True
            mock_crypt.return_value = mock_pwd_context
            
            # Authenticate
            result = await service.authenticate_user("testuser", "password123")
            
            # Verify
            assert result == mock_user
            mock_pwd_context.verify.assert_called_once_with("password123", "hashed")
    
    async def test_authenticate_user_invalid_password(self, service, mocker):
        """Test authentication with invalid password."""
        # Mock user
        mock_user = User(
            id=uuid4(),
            username="testuser",
            hashed_password="hashed"
        )
        service.user_repo.get_by_username.return_value = mock_user
        
        # Mock password verification failure
        with patch('certify_studio.integration.services.CryptContext') as mock_crypt:
            mock_pwd_context = Mock()
            mock_pwd_context.verify.return_value = False
            mock_crypt.return_value = mock_pwd_context
            
            # Authenticate
            result = await service.authenticate_user("testuser", "wrongpassword")
            
            # Verify
            assert result is None
    
    async def test_create_access_token(self, service):
        """Test JWT token creation."""
        user = User(
            id=uuid4(),
            username="testuser",
            email="test@example.com"
        )
        
        with patch('certify_studio.integration.services.jwt') as mock_jwt:
            mock_jwt.encode.return_value = "test-token"
            
            # Create token
            token = await service.create_access_token(user, expires_delta=3600)
            
            # Verify
            assert token == "test-token"
            mock_jwt.encode.assert_called_once()
            
            # Check payload
            payload = mock_jwt.encode.call_args[0][0]
            assert payload["sub"] == str(user.id)
            assert payload["username"] == user.username
            assert payload["email"] == user.email


@pytest.mark.unit
class TestQualityAssuranceService:
    """Test quality assurance service."""
    
    @pytest.fixture
    def service(self, mocker):
        """Create service with mocked dependencies."""
        mock_db = mocker.Mock()
        service = QualityAssuranceService(mock_db)
        service.quality_repo = mocker.Mock()
        service.analytics_repo = mocker.Mock()
        return service
    
    async def test_submit_user_feedback(self, service, test_user):
        """Test submitting user feedback."""
        generation_id = uuid4()
        
        # Mock repository methods
        service.quality_repo.create_user_feedback = AsyncMock()
        service._update_generation_quality_score = AsyncMock()
        service.analytics_repo.record_user_feedback = AsyncMock()
        
        # Submit feedback
        await service.submit_user_feedback(
            user=test_user,
            generation_id=generation_id,
            rating=4,
            feedback_text="Good but could be better",
            feedback_type="quality"
        )
        
        # Verify feedback created
        service.quality_repo.create_user_feedback.assert_called_once_with(
            user_id=test_user.id,
            generation_id=generation_id,
            feedback_type="quality",
            rating=4,
            feedback_text="Good but could be better"
        )
        
        # Verify quality score updated
        service._update_generation_quality_score.assert_called_once_with(generation_id)
        
        # Verify analytics recorded
        service.analytics_repo.record_user_feedback.assert_called_once()


@pytest.mark.unit
class TestDomainExtractionService:
    """Test domain extraction service."""
    
    @pytest.fixture
    def service(self, mocker):
        """Create service with mocked dependencies."""
        mock_db = mocker.Mock()
        service = DomainExtractionService(mock_db)
        service.domain_repo = mocker.Mock()
        return service
    
    async def test_extract_concepts_from_text(self, service, mocker):
        """Test concept extraction from text."""
        # Mock agent
        mock_agent = mocker.AsyncMock()
        mock_agent.extract_concepts_from_text.return_value = {
            'concepts': [
                {
                    'name': 'Machine Learning',
                    'description': 'AI subset',
                    'type': 'topic',
                    'importance': 0.9
                }
            ]
        }
        
        with patch('certify_studio.integration.services.DomainExtractionAgent', return_value=mock_agent):
            # Mock repository
            mock_concept = Mock(id=uuid4())
            service.domain_repo.create_extracted_concept = AsyncMock(return_value=mock_concept)
            
            # Extract concepts
            result = await service.extract_concepts_from_text(
                "Machine learning is a subset of AI",
                source_id=uuid4()
            )
            
            # Verify
            assert len(result) == 1
            assert result[0] == mock_concept
            service.domain_repo.create_extracted_concept.assert_called_once()


@pytest.mark.unit  
class TestAnalyticsService:
    """Test analytics service."""
    
    @pytest.fixture
    def service(self, mocker):
        """Create service with mocked dependencies."""
        mock_db = mocker.Mock()
        service = AnalyticsService(mock_db)
        service.analytics_repo = mocker.Mock()
        return service
    
    async def test_get_user_analytics(self, service):
        """Test getting user analytics."""
        user_id = uuid4()
        
        # Mock repository responses
        mock_activities = [
            Mock(action="login", created_at=datetime.utcnow()),
            Mock(action="generate", created_at=datetime.utcnow())
        ]
        
        mock_generations = [
            Mock(
                completed_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                tokens_used=1000,
                content_type="full_certification"
            )
        ]
        
        service.analytics_repo.get_user_activities.return_value = mock_activities
        service.analytics_repo.get_user_generation_analytics.return_value = mock_generations
        
        # Get analytics
        result = await service.get_user_analytics(user_id)
        
        # Verify structure
        assert 'user_id' in result
        assert 'activity' in result
        assert 'generations' in result
        assert result['activity']['total_actions'] == 2
        assert result['generations']['total'] == 1
