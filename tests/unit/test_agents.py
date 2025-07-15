"""
Unit Tests for Individual Agents
=================================
Tests individual agent functionality in isolation.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
from typing import Dict, Any
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from certify_studio.config import Settings
from certify_studio.agents.content_generation_agent import ContentGenerationAgent
from certify_studio.agents.quality_assurance_agent import QualityAssuranceAgent
from certify_studio.agents.domain_extraction_agent import DomainExtractionAgent
from certify_studio.agents.export_agent import ExportAgent


class TestContentGenerationAgent:
    """Unit tests for Content Generation Agent"""
    
    @pytest.fixture
    async def agent(self):
        """Create agent instance"""
        settings = Settings()
        agent = ContentGenerationAgent(settings)
        await agent.initialize()
        yield agent
        await agent.shutdown()
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent is not None
        assert agent.status == "ready"
        assert agent.agent_id is not None
        assert agent.name == "ContentGenerationAgent"
        
    @pytest.mark.asyncio
    async def test_content_generation_simple(self, agent):
        """Test simple content generation"""
        request = {
            "topic": "Introduction to Machine Learning",
            "difficulty": "beginner",
            "format": "simple"
        }
        
        result = await agent.generate_content(request)
        
        assert result is not None
        assert "title" in result
        assert "sections" in result
        assert len(result["sections"]) > 0
        
    @pytest.mark.asyncio
    async def test_cognitive_load_calculation(self, agent):
        """Test cognitive load is calculated correctly"""
        request = {
            "topic": "Complex AWS Architecture",
            "difficulty": "advanced",
            "format": "detailed"
        }
        
        result = await agent.generate_content(request)
        
        assert "total_cognitive_load" in result
        assert 0 <= result["total_cognitive_load"] <= 1
        
        # Check each section has cognitive load
        for section in result["sections"]:
            assert "cognitive_load" in section
            assert 0 <= section["cognitive_load"] <= 1


class TestQualityAssuranceAgent:
    """Unit tests for Quality Assurance Agent"""
    
    @pytest.fixture
    async def agent(self):
        """Create agent instance"""
        settings = Settings()
        agent = QualityAssuranceAgent(settings)
        await agent.initialize()
        yield agent
        await agent.shutdown()
    
    @pytest.mark.asyncio
    async def test_content_validation(self, agent):
        """Test content validation logic"""
        sample_content = {
            "title": "Test Content",
            "sections": [
                {
                    "title": "Introduction",
                    "content": "This is test content for validation.",
                    "cognitive_load": 0.3
                },
                {
                    "title": "Main Content",
                    "content": "More detailed content here with examples.",
                    "cognitive_load": 0.5
                }
            ],
            "total_cognitive_load": 0.8
        }
        
        result = await agent.validate_content(sample_content)
        
        assert result is not None
        assert "scores" in result
        assert "passed" in result
        assert "feedback" in result
        
        # Check all score categories
        scores = result["scores"]
        assert "overall" in scores
        assert "pedagogical" in scores
        assert "technical" in scores
        assert "accessibility" in scores
        
        # Scores should be between 0 and 1
        for score in scores.values():
            assert 0 <= score <= 1
            
    @pytest.mark.asyncio
    async def test_accessibility_check(self, agent):
        """Test accessibility validation"""
        content_with_images = {
            "title": "Visual Content",
            "sections": [
                {
                    "title": "Diagrams",
                    "content": "Content with images",
                    "images": [
                        {"url": "image1.png", "alt_text": "Diagram showing architecture"},
                        {"url": "image2.png", "alt_text": ""}  # Missing alt text
                    ]
                }
            ]
        }
        
        result = await agent.validate_content(content_with_images)
        
        # Should flag missing alt text
        assert result["scores"]["accessibility"] < 1.0
        assert any("alt text" in feedback.lower() 
                  for feedback in result.get("feedback", []))


class TestDomainExtractionAgent:
    """Unit tests for Domain Extraction Agent"""
    
    @pytest.fixture
    async def agent(self):
        """Create agent instance"""
        settings = Settings()
        agent = DomainExtractionAgent(settings)
        await agent.initialize()
        yield agent
        await agent.shutdown()
    
    @pytest.mark.asyncio
    async def test_domain_extraction_from_text(self, agent):
        """Test domain extraction from plain text"""
        sample_text = """
        AWS AI Services include:
        - Amazon SageMaker for machine learning model development
        - Amazon Rekognition for computer vision and image analysis
        - Amazon Comprehend for natural language processing
        - Amazon Polly for text-to-speech conversion
        
        These services enable developers to build intelligent applications
        without deep ML expertise.
        """
        
        domains = await agent.extract_domains(sample_text)
        
        assert domains is not None
        assert len(domains) > 0
        
        # Check domain structure
        for domain in domains:
            assert "name" in domain
            assert "weight" in domain
            assert "concepts" in domain
            assert 0 <= domain["weight"] <= 100
            
        # Should identify key AWS AI services
        domain_names = [d["name"].lower() for d in domains]
        assert any("machine learning" in name or "sagemaker" in name 
                  for name in domain_names)
        
    @pytest.mark.asyncio
    async def test_concept_extraction(self, agent):
        """Test concept extraction within domains"""
        text = "Amazon EC2 provides scalable compute capacity in the cloud."
        
        domains = await agent.extract_domains(text)
        
        # Should extract EC2 and cloud computing concepts
        all_concepts = []
        for domain in domains:
            all_concepts.extend(domain["concepts"])
            
        assert len(all_concepts) > 0
        assert any("EC2" in concept or "compute" in concept 
                  for concept in all_concepts)


class TestExportAgent:
    """Unit tests for Export Agent"""
    
    @pytest.fixture
    async def agent(self):
        """Create agent instance"""
        settings = Settings()
        agent = ExportAgent(settings)
        await agent.initialize()
        yield agent
        await agent.shutdown()
        
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for exports"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.mark.asyncio
    async def test_pdf_export(self, agent, temp_dir):
        """Test PDF export functionality"""
        sample_content = {
            "title": "Test Course",
            "author": "Test System",
            "sections": [
                {
                    "title": "Chapter 1: Introduction",
                    "content": "This is the introduction to our test course."
                },
                {
                    "title": "Chapter 2: Main Content",
                    "content": "This chapter contains the main content."
                }
            ]
        }
        
        output_path = temp_dir / "test_export.pdf"
        result = await agent.export_to_pdf(sample_content, str(output_path))
        
        assert result is not None
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        assert result["format"] == "pdf"
        assert result["path"] == str(output_path)
        
    @pytest.mark.asyncio
    async def test_html_export(self, agent, temp_dir):
        """Test HTML export functionality"""
        sample_content = {
            "title": "HTML Test",
            "sections": [
                {
                    "title": "Web Content",
                    "content": "Content for web export with **markdown** support."
                }
            ]
        }
        
        output_path = temp_dir / "test_export.html"
        result = await agent.export_to_html(sample_content, str(output_path))
        
        assert result is not None
        assert output_path.exists()
        
        # Check HTML content
        html_content = output_path.read_text()
        assert "<html>" in html_content
        assert sample_content["title"] in html_content
        assert "<strong>markdown</strong>" in html_content  # Markdown processed
        
    @pytest.mark.asyncio
    async def test_scorm_export(self, agent, temp_dir):
        """Test SCORM package export"""
        sample_content = {
            "title": "SCORM Course",
            "identifier": "test-course-001",
            "sections": [
                {
                    "title": "Module 1",
                    "content": "Learning content",
                    "objectives": ["Understand basics"]
                }
            ]
        }
        
        output_path = temp_dir / "test_scorm.zip"
        result = await agent.export_to_scorm(sample_content, str(output_path))
        
        assert result is not None
        assert output_path.exists()
        assert output_path.suffix == ".zip"
        assert result["format"] == "scorm"
        assert result["version"] == "1.2"  # or "2004" depending on implementation


class TestAgentPerformance:
    """Performance tests for agents"""
    
    @pytest.mark.asyncio
    async def test_agent_response_time(self):
        """Test agent response times"""
        settings = Settings()
        agent = ContentGenerationAgent(settings)
        await agent.initialize()
        
        try:
            request = {
                "topic": "Quick test",
                "format": "simple"
            }
            
            import time
            start_time = time.time()
            result = await agent.generate_content(request)
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response_time < 5.0  # Should respond within 5 seconds
            assert result is not None
            
        finally:
            await agent.shutdown()
            
    @pytest.mark.asyncio
    async def test_concurrent_agent_operations(self):
        """Test agents can handle concurrent operations"""
        settings = Settings()
        agent = ContentGenerationAgent(settings)
        await agent.initialize()
        
        try:
            # Create multiple concurrent requests
            requests = [
                {"topic": f"Topic {i}", "format": "simple"}
                for i in range(5)
            ]
            
            # Execute concurrently
            tasks = [agent.generate_content(req) for req in requests]
            results = await asyncio.gather(*tasks)
            
            # All should complete successfully
            assert len(results) == 5
            assert all(r is not None for r in results)
            assert all("title" in r for r in results)
            
        finally:
            await agent.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
