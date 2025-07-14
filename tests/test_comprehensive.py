#!/usr/bin/env python3
"""
Comprehensive test suite for Certify Studio
Tests imports, API startup, and integration
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestImports:
    """Test all critical imports work"""
    
    def test_config_imports(self):
        from certify_studio.config import settings, Settings
        assert settings is not None
        assert isinstance(settings, Settings)
    
    def test_database_imports(self):
        from certify_studio.database import Base, get_db_session
        assert Base is not None
        assert get_db_session is not None
    
    def test_agent_imports(self):
        from certify_studio.agents import MultimodalOrchestrator, AgenticOrchestrator
        from certify_studio.agents.specialized.quality_assurance import QualityAssuranceAgent
        from certify_studio.agents.specialized.quality_assurance.consensus_manager import QualityConsensusOrchestrator
        assert all([MultimodalOrchestrator, AgenticOrchestrator, QualityAssuranceAgent, QualityConsensusOrchestrator])
    
    def test_api_imports(self):
        try:
            from certify_studio.api.main import api_router
            from certify_studio.main import app
            assert api_router is not None
            assert app is not None
        except Exception as e:
            print(f"API import error: {type(e).__name__}: {e}")
            raise


class TestAPIStartup:
    """Test API can start without errors"""
    
    @pytest.mark.asyncio
    async def test_app_creation(self):
        from certify_studio.main import create_application
        app = create_application()
        assert app is not None
        assert app.title == "Certify Studio API"
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        from certify_studio.main import app
        from httpx import AsyncClient
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "version" in data


class TestMultiAgentQA:
    """Test multi-agent consensus QA architecture"""
    
    @pytest.mark.asyncio
    async def test_consensus_orchestrator_creation(self):
        from certify_studio.agents.specialized.quality_assurance.consensus_manager import QualityConsensusOrchestrator
        
        orchestrator = QualityConsensusOrchestrator(num_critics=3)
        await orchestrator.initialize()
        
        assert len(orchestrator.critics) == 3
        assert all(critic.name.startswith("QACritic_") for critic in orchestrator.critics)
    
    @pytest.mark.asyncio
    async def test_critic_agents_have_different_biases(self):
        from certify_studio.agents.specialized.quality_assurance.consensus_manager import QualityConsensusOrchestrator
        
        orchestrator = QualityConsensusOrchestrator(num_critics=5)
        await orchestrator.initialize()
        
        # Check each critic has different bias
        biases = [critic.evaluation_bias for critic in orchestrator.critics]
        assert len(biases) == 5
        # At least some should have different biases
        assert len(set(str(b) for b in biases)) > 1
    
    @pytest.mark.asyncio
    async def test_consensus_evaluation(self):
        from certify_studio.agents.specialized.quality_assurance.consensus_manager import QualityConsensusOrchestrator
        
        orchestrator = QualityConsensusOrchestrator(num_critics=3)
        await orchestrator.initialize()
        
        # Mock content
        content = {
            "title": "Test Certification Guide",
            "sections": [
                {
                    "title": "Introduction",
                    "content": "This is a test introduction to certification."
                }
            ]
        }
        
        # Mock request
        request = MagicMock()
        request.quality_standards = {
            "accuracy_threshold": 0.8,
            "completeness_threshold": 0.7
        }
        
        # Test evaluation (with mocked LLM responses)
        with patch.object(orchestrator, '_get_critic_evaluation', return_value={
            "accuracy_score": 0.85,
            "completeness_score": 0.75,
            "technical_score": 0.80,
            "pedagogical_score": 0.82,
            "issues": [],
            "suggestions": ["Add more examples"],
            "confidence": 0.85
        }):
            result = await orchestrator.evaluate_quality(content, request)
            
            assert result is not None
            assert hasattr(result, 'consensus_score')
            assert 0.0 <= result.consensus_score <= 1.0


class TestCriticalPaths:
    """Test critical application paths"""
    
    def test_config_loads_env_file(self):
        from certify_studio.config import settings
        # Should not raise exception
        assert settings.APP_NAME == "Certify Studio"
    
    def test_secret_str_conversion(self):
        from certify_studio.config import settings
        # Test SecretStr can be converted properly
        if settings.ANTHROPIC_API_KEY:
            value = settings.ANTHROPIC_API_KEY.get_secret_value()
            assert isinstance(value, str)
    
    @pytest.mark.asyncio
    async def test_llm_initialization(self):
        from certify_studio.core.llm import MultimodalLLM, LLMProvider
        
        # Mock the API keys if not present
        with patch('certify_studio.core.llm.multimodal_llm.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = MagicMock()
            mock_settings.ANTHROPIC_API_KEY.get_secret_value.return_value = "test-key"
            mock_settings.OPENAI_API_KEY = None
            
            llm = MultimodalLLM(provider=LLMProvider.ANTHROPIC_CLAUDE)
            assert llm is not None
            assert llm.provider == LLMProvider.ANTHROPIC_CLAUDE


class TestRouterImports:
    """Test all API routers can be imported"""
    
    def test_router_imports(self):
        try:
            from certify_studio.api.routers import (
                auth_router,
                users_router,
                content_router,
                analytics_router,
                domains_router
            )
            assert all([auth_router, users_router, content_router, analytics_router, domains_router])
        except ImportError as e:
            print(f"Router import error: {type(e).__name__}: {e}")
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
