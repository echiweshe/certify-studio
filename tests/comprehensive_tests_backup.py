"""
Comprehensive Testing Suite for Certify Studio
============================================
Unit tests, integration tests, and end-to-end tests.
"""

import pytest
import asyncio
import aiohttp
from pathlib import Path
import json
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, List
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from certify_studio.config import Settings
from certify_studio.agents.content_generation_agent import ContentGenerationAgent
from certify_studio.agents.quality_assurance_agent import QualityAssuranceAgent
from certify_studio.agents.domain_extraction_agent import DomainExtractionAgent
from certify_studio.agents.export_agent import ExportAgent
from certify_studio.graphrag.unified_graphrag import UnifiedGraphRAGSystem

# Test fixtures
@pytest.fixture
def settings():
    """Test settings"""
    return Settings()

@pytest.fixture
def temp_dir():
    """Temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
async def content_agent(settings):
    """Content generation agent fixture"""
    agent = ContentGenerationAgent(settings)
    await agent.initialize()
    yield agent
    await agent.shutdown()

@pytest.fixture
async def qa_agent(settings):
    """Quality assurance agent fixture"""
    agent = QualityAssuranceAgent(settings)
    await agent.initialize()
    yield agent
    await agent.shutdown()

@pytest.fixture
async def domain_agent(settings):
    """Domain extraction agent fixture"""
    agent = DomainExtractionAgent(settings)
    await agent.initialize()
    yield agent
    await agent.shutdown()

@pytest.fixture
async def export_agent(settings):
    """Export agent fixture"""
    agent = ExportAgent(settings)
    await agent.initialize()
    yield agent
    await agent.shutdown()

@pytest.fixture
async def graphrag_system(settings):
    """GraphRAG system fixture"""
    system = UnifiedGraphRAGSystem(settings)
    await system.initialize()
    yield system
    await system.close()

# Unit Tests
class TestAgentUnits:
    """Unit tests for individual agents"""
    
    @pytest.mark.asyncio
    async def test_content_agent_initialization(self, content_agent):
        """Test content agent initializes correctly"""
        assert content_agent is not None
        assert content_agent.status == "ready"
        assert content_agent.agent_id is not None
        
    @pytest.mark.asyncio
    async def test_qa_agent_validation(self, qa_agent):
        """Test QA agent validation logic"""
        # Create sample content
        sample_content = {
            "title": "Test Content",
            "sections": [
                {
                    "title": "Introduction",
                    "content": "This is test content.",
                    "cognitive_load": 0.3
                }
            ],
            "total_cognitive_load": 0.3
        }
        
        # Validate content
        result = await qa_agent.validate_content(sample_content)
        
        assert result is not None
        assert "scores" in result
        assert "passed" in result
        assert result["scores"]["overall"] > 0
        
    @pytest.mark.asyncio
    async def test_domain_agent_extraction(self, domain_agent):
        """Test domain extraction from text"""
        sample_text = """
        AWS AI Services include Amazon SageMaker for machine learning,
        Amazon Rekognition for computer vision, and Amazon Comprehend
        for natural language processing. These services enable developers
        to build intelligent applications.
        """
        
        domains = await domain_agent.extract_domains(sample_text)
        
        assert domains is not None
        assert len(domains) > 0
        assert any("machine learning" in d["name"].lower() for d in domains)
        
    @pytest.mark.asyncio
    async def test_export_agent_pdf_generation(self, export_agent, temp_dir):
        """Test PDF export functionality"""
        sample_content = {
            "title": "Test Course",
            "sections": [
                {
                    "title": "Chapter 1",
                    "content": "Test content for PDF generation."
                }
            ]
        }
        
        output_path = temp_dir / "test_export.pdf"
        result = await export_agent.export_to_pdf(sample_content, output_path)
        
        assert result is not None
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
    @pytest.mark.asyncio
    async def test_graphrag_knowledge_storage(self, graphrag_system):
        """Test GraphRAG knowledge storage and retrieval"""
        # Store knowledge
        concept = {
            "id": "test_concept_1",
            "name": "Machine Learning",
            "description": "The study of algorithms that improve through experience",
            "category": "AI Fundamentals"
        }
        
        await graphrag_system.store_concept(concept)
        
        # Retrieve knowledge
        retrieved = await graphrag_system.get_concept("test_concept_1")
        
        assert retrieved is not None
        assert retrieved["name"] == concept["name"]
        assert retrieved["category"] == concept["category"]

# Integration Tests
class TestAgentIntegration:
    """Integration tests for agent collaboration"""
    
    @pytest.mark.asyncio
    async def test_content_qa_integration(self, content_agent, qa_agent):
        """Test content generation and QA validation integration"""
        # Generate content
        generation_request = {
            "topic": "AWS Machine Learning Services",
            "difficulty": "intermediate",
            "format": "structured"
        }
        
        content = await content_agent.generate_content(generation_request)
        assert content is not None
        
        # Validate with QA
        qa_result = await qa_agent.validate_content(content)
        assert qa_result["passed"] == True
        assert qa_result["scores"]["pedagogical"] > 0.7
        
    @pytest.mark.asyncio
    async def test_domain_graphrag_integration(self, domain_agent, graphrag_system):
        """Test domain extraction and GraphRAG storage integration"""
        # Extract domains
        sample_text = """
        Amazon SageMaker provides a complete set of tools for machine learning.
        It includes data labeling, model training, and deployment capabilities.
        """
        
        domains = await domain_agent.extract_domains(sample_text)
        
        # Store in GraphRAG
        for domain in domains:
            await graphrag_system.store_domain(domain)
            
        # Query related domains
        related = await graphrag_system.find_related_domains("machine learning")
        assert len(related) > 0
        
    @pytest.mark.asyncio
    async def test_full_agent_collaboration(self, content_agent, qa_agent, domain_agent, export_agent):
        """Test full agent collaboration workflow"""
        # Step 1: Extract domains
        text = "AWS offers various AI services for developers."
        domains = await domain_agent.extract_domains(text)
        
        # Step 2: Generate content based on domains
        content_request = {
            "domains": domains,
            "format": "interactive"
        }
        content = await content_agent.generate_from_domains(content_request)
        
        # Step 3: QA validation
        qa_result = await qa_agent.validate_content(content)
        assert qa_result["passed"]
        
        # Step 4: Export if passed
        if qa_result["passed"]:
            export_result = await export_agent.export_to_html(content)
            assert export_result is not None

# End-to-End Tests
class TestEndToEnd:
    """End-to-end tests simulating real user workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_certification_workflow(self):
        """Test complete certification content generation workflow"""
        base_url = "http://localhost:8000"
        
        async with aiohttp.ClientSession() as session:
            # 1. Health check
            async with session.get(f"{base_url}/health") as resp:
                assert resp.status == 200
                
            # 2. Register user
            register_data = {
                "email": "e2e_test@certify-studio.com",
                "password": "TestPass123!",
                "full_name": "E2E Test User"
            }
            
            async with session.post(f"{base_url}/api/v1/auth/register", json=register_data) as resp:
                assert resp.status in [200, 201, 400]  # 400 if already exists
                
            # 3. Login
            login_data = {
                "username": register_data["email"],
                "password": register_data["password"]
            }
            
            async with session.post(f"{base_url}/api/v1/auth/login", data=login_data) as resp:
                assert resp.status == 200
                auth_data = await resp.json()
                token = auth_data["access_token"]
                
            headers = {"Authorization": f"Bearer {token}"}
            
            # 4. Create test PDF content
            test_content = b"%PDF-1.4\n%Test PDF for E2E testing\n"
            
            # 5. Upload PDF
            data = aiohttp.FormData()
            data.add_field('file',
                          test_content,
                          filename='test_certification.pdf',
                          content_type='application/pdf')
            
            async with session.post(
                f"{base_url}/api/v1/generation/upload",
                data=data,
                headers=headers
            ) as resp:
                assert resp.status == 200
                upload_data = await resp.json()
                upload_id = upload_data["upload_id"]
                
            # 6. Extract domains
            async with session.post(
                f"{base_url}/api/v1/domains/extract/{upload_id}",
                headers=headers
            ) as resp:
                assert resp.status == 200
                domains = await resp.json()
                assert "domains" in domains
                
            # 7. Generate content
            gen_config = {
                "upload_id": upload_id,
                "config": {
                    "format": "structured",
                    "difficulty": "intermediate"
                }
            }
            
            async with session.post(
                f"{base_url}/api/v1/generation/generate",
                json=gen_config,
                headers=headers
            ) as resp:
                assert resp.status == 200
                gen_data = await resp.json()
                job_id = gen_data["job_id"]
                
            # 8. Check status (simplified - in real test would poll)
            await asyncio.sleep(2)  # Give it time to process
            
            async with session.get(
                f"{base_url}/api/v1/generation/status/{job_id}",
                headers=headers
            ) as resp:
                assert resp.status == 200
                status_data = await resp.json()
                # In real scenario, would wait for completion
                
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test system performance under concurrent load"""
        base_url = "http://localhost:8000"
        concurrent_requests = 10
        
        async def single_request(session, index):
            """Single request workflow"""
            try:
                async with session.get(f"{base_url}/health") as resp:
                    return resp.status == 200
            except:
                return False
                
        async with aiohttp.ClientSession() as session:
            # Launch concurrent requests
            tasks = [
                single_request(session, i)
                for i in range(concurrent_requests)
            ]
            
            start_time = asyncio.get_event_loop().time()
            results = await asyncio.gather(*tasks)
            end_time = asyncio.get_event_loop().time()
            
            # Check results
            success_count = sum(results)
            success_rate = success_count / concurrent_requests
            total_time = end_time - start_time
            avg_time = total_time / concurrent_requests
            
            assert success_rate > 0.95  # 95% success rate
            assert avg_time < 1.0  # Less than 1 second average

# Performance Tests
class TestPerformance:
    """Performance and stress tests"""
    
    @pytest.mark.asyncio
    async def test_agent_response_time(self, content_agent):
        """Test agent response time"""
        request = {
            "topic": "Quick test",
            "format": "simple"
        }
        
        start_time = asyncio.get_event_loop().time()
        result = await content_agent.generate_content(request)
        end_time = asyncio.get_event_loop().time()
        
        response_time = end_time - start_time
        assert response_time < 5.0  # Should respond within 5 seconds
        
    @pytest.mark.asyncio
    async def test_memory_usage(self, graphrag_system):
        """Test memory usage under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Store many concepts
        for i in range(1000):
            concept = {
                "id": f"concept_{i}",
                "name": f"Test Concept {i}",
                "description": f"Description for concept {i}"
            }
            await graphrag_system.store_concept(concept)
            
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        assert memory_increase < 100  # Should not use more than 100MB

# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
