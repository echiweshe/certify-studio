"""
Integration Tests for Agent Collaboration
========================================
Tests how agents work together in the system.
"""

import pytest
import asyncio
from pathlib import Path
import json
from typing import Dict, Any, List
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from certify_studio.config import Settings
from certify_studio.agents.content_generation_agent import ContentGenerationAgent
from certify_studio.agents.quality_assurance_agent import QualityAssuranceAgent
from certify_studio.agents.domain_extraction_agent import DomainExtractionAgent
from certify_studio.agents.export_agent import ExportAgent
from certify_studio.graphrag.unified_graphrag import UnifiedGraphRAGSystem


class TestAgentCollaboration:
    """Test agents working together"""
    
    @pytest.fixture
    async def agents(self):
        """Create all agents"""
        settings = Settings()
        
        agents = {
            "content": ContentGenerationAgent(settings),
            "qa": QualityAssuranceAgent(settings),
            "domain": DomainExtractionAgent(settings),
            "export": ExportAgent(settings)
        }
        
        # Initialize all agents
        for agent in agents.values():
            await agent.initialize()
            
        yield agents
        
        # Shutdown all agents
        for agent in agents.values():
            await agent.shutdown()
            
    @pytest.fixture
    async def graphrag(self):
        """Create GraphRAG system"""
        settings = Settings()
        system = UnifiedGraphRAGSystem(settings)
        await system.initialize()
        yield system
        await system.close()
    
    @pytest.mark.asyncio
    async def test_content_generation_qa_pipeline(self, agents):
        """Test content generation followed by QA validation"""
        content_agent = agents["content"]
        qa_agent = agents["qa"]
        
        # Step 1: Generate content
        generation_request = {
            "topic": "AWS Machine Learning Services",
            "difficulty": "intermediate",
            "format": "structured",
            "include_examples": True
        }
        
        content = await content_agent.generate_content(generation_request)
        assert content is not None
        assert "sections" in content
        
        # Step 2: Validate with QA
        qa_result = await qa_agent.validate_content(content)
        
        assert qa_result is not None
        assert qa_result["passed"] is True
        assert qa_result["scores"]["overall"] > 0.7
        
        # Step 3: If QA suggests improvements, regenerate
        if qa_result.get("suggestions"):
            improved_request = generation_request.copy()
            improved_request["improvements"] = qa_result["suggestions"]
            
            improved_content = await content_agent.generate_content(improved_request)
            
            # Validate improved content
            improved_qa = await qa_agent.validate_content(improved_content)
            assert improved_qa["scores"]["overall"] >= qa_result["scores"]["overall"]
    
    @pytest.mark.asyncio
    async def test_domain_extraction_to_content_generation(self, agents):
        """Test extracting domains and generating targeted content"""
        domain_agent = agents["domain"]
        content_agent = agents["content"]
        
        # Sample AWS documentation text
        sample_text = """
        Amazon SageMaker is a fully managed service that provides developers 
        and data scientists with the ability to build, train, and deploy 
        machine learning models quickly. SageMaker removes the heavy lifting 
        from each step of the machine learning process to make it easier to 
        develop high-quality models.
        
        Key features include:
        - Built-in algorithms optimized for speed and accuracy
        - Jupyter notebooks for exploration
        - Model training with automatic model tuning
        - One-click deployment to production
        """
        
        # Step 1: Extract domains
        domains = await domain_agent.extract_domains(sample_text)
        assert len(domains) > 0
        
        # Step 2: Generate content for each domain
        generated_contents = []
        for domain in domains[:3]:  # Test first 3 domains
            content_request = {
                "domain": domain,
                "topic": domain["name"],
                "concepts": domain["concepts"],
                "format": "detailed"
            }
            
            content = await content_agent.generate_from_domains(content_request)
            generated_contents.append(content)
            
        assert len(generated_contents) == min(3, len(domains))
        
        # Verify content covers extracted concepts
        for i, content in enumerate(generated_contents):
            domain_concepts = domains[i]["concepts"]
            content_text = json.dumps(content).lower()
            
            # At least some concepts should appear in generated content
            matching_concepts = sum(
                1 for concept in domain_concepts 
                if concept.lower() in content_text
            )
            assert matching_concepts > 0
    
    @pytest.mark.asyncio
    async def test_full_pipeline_with_export(self, agents):
        """Test complete pipeline from domain extraction to export"""
        domain_agent = agents["domain"]
        content_agent = agents["content"]
        qa_agent = agents["qa"]
        export_agent = agents["export"]
        
        # Step 1: Extract domains from text
        text = """
        AWS Lambda lets you run code without provisioning or managing servers. 
        You pay only for the compute time you consume. With Lambda, you can run 
        code for virtually any type of application or backend service.
        """
        
        domains = await domain_agent.extract_domains(text)
        
        # Step 2: Generate content
        content = await content_agent.generate_from_domains({
            "domains": domains,
            "format": "structured"
        })
        
        # Step 3: QA validation
        qa_result = await qa_agent.validate_content(content)
        assert qa_result["passed"]
        
        # Step 4: Export to multiple formats
        export_formats = ["html", "pdf"]
        export_results = {}
        
        for format_type in export_formats:
            if format_type == "html":
                result = await export_agent.export_to_html(content)
            elif format_type == "pdf":
                result = await export_agent.export_to_pdf(content)
                
            export_results[format_type] = result
            assert result is not None
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, agents):
        """Test how agents handle errors from other agents"""
        content_agent = agents["content"]
        qa_agent = agents["qa"]
        
        # Generate invalid content
        invalid_content = {
            "title": None,  # Missing title
            "sections": []  # Empty sections
        }
        
        # QA should handle invalid content gracefully
        qa_result = await qa_agent.validate_content(invalid_content)
        
        assert qa_result is not None
        assert qa_result["passed"] is False
        assert qa_result["scores"]["overall"] == 0
        assert len(qa_result.get("errors", [])) > 0
    
    @pytest.mark.asyncio
    async def test_graphrag_integration(self, agents, graphrag):
        """Test agents integrating with GraphRAG system"""
        domain_agent = agents["domain"]
        
        # Extract domains
        text = "Machine learning with TensorFlow and PyTorch frameworks."
        domains = await domain_agent.extract_domains(text)
        
        # Store in GraphRAG
        for domain in domains:
            await graphrag.store_domain(domain)
            
            # Store concepts
            for concept in domain["concepts"]:
                await graphrag.store_concept({
                    "name": concept,
                    "domain": domain["name"],
                    "description": f"Concept related to {domain['name']}"
                })
        
        # Query related concepts
        ml_concepts = await graphrag.find_related_concepts("machine learning")
        assert len(ml_concepts) > 0
        
        # Build knowledge graph
        graph = await graphrag.build_knowledge_graph(domains)
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) > 0


class TestAgentCommunication:
    """Test inter-agent communication protocols"""
    
    @pytest.mark.asyncio
    async def test_agent_message_passing(self, agents):
        """Test agents can pass messages to each other"""
        content_agent = agents["content"]
        qa_agent = agents["qa"]
        
        # Simulate message passing
        message = {
            "type": "content_ready",
            "sender": "ContentAgent",
            "receiver": "QAAgent",
            "content_id": "test-content-123",
            "priority": "high"
        }
        
        # In a real system, this would go through a message bus
        # For testing, we simulate the behavior
        assert content_agent.agent_id is not None
        assert qa_agent.agent_id is not None
        
        # Agents should be able to handle messages
        assert hasattr(content_agent, "send_message")
        assert hasattr(qa_agent, "receive_message")
    
    @pytest.mark.asyncio
    async def test_agent_coordination(self, agents):
        """Test agent coordination for complex tasks"""
        # Simulate a coordinated task
        task = {
            "id": "complex-task-001",
            "type": "full_course_generation",
            "requirements": {
                "topic": "AWS Certified AI Practitioner",
                "modules": 5,
                "include_labs": True,
                "include_assessments": True
            }
        }
        
        # Coordinator would distribute subtasks
        subtasks = [
            ("domain_extraction", agents["domain"]),
            ("content_generation", agents["content"]),
            ("quality_assurance", agents["qa"]),
            ("export", agents["export"])
        ]
        
        results = {}
        for task_name, agent in subtasks:
            # Each agent processes its part
            if task_name == "domain_extraction":
                results[task_name] = await agent.extract_domains(
                    "AWS AI services and best practices"
                )
            elif task_name == "content_generation":
                results[task_name] = await agent.generate_content({
                    "topic": task["requirements"]["topic"],
                    "modules": task["requirements"]["modules"]
                })
            # Continue for other agents...
        
        assert all(results.values())


class TestAgentResilience:
    """Test system resilience and recovery"""
    
    @pytest.mark.asyncio
    async def test_agent_retry_mechanism(self, agents):
        """Test agents retry failed operations"""
        content_agent = agents["content"]
        
        # Simulate a request that might fail initially
        difficult_request = {
            "topic": "Very Complex Quantum Computing Topic",
            "difficulty": "expert",
            "retry_on_failure": True,
            "max_retries": 3
        }
        
        # Agent should handle retries internally
        result = await content_agent.generate_content(difficult_request)
        
        assert result is not None
        # Even complex topics should eventually generate something
        assert "sections" in result
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, agents):
        """Test system degrades gracefully when agents fail"""
        content_agent = agents["content"]
        qa_agent = agents["qa"]
        export_agent = agents["export"]
        
        # Generate content
        content = await content_agent.generate_content({
            "topic": "Test Topic",
            "format": "simple"
        })
        
        # Even if QA is strict and fails content
        qa_result = await qa_agent.validate_content(content)
        
        # Export should still work with warnings
        if not qa_result["passed"]:
            export_result = await export_agent.export_to_html(
                content,
                include_warnings=True
            )
            
            assert export_result is not None
            assert export_result["success"] is True
            assert "warnings" in export_result
            assert len(export_result["warnings"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
