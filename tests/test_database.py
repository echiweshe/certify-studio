#!/usr/bin/env python3
"""
Database model tests for Certify Studio
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from certify_studio.database import Base
from certify_studio.database.models import (
    User, Content, Domain, Concept, Relationship, 
    LearningPath, QualityCheck, GenerationJob
)


@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


class TestDatabaseModels:
    """Test database models and relationships"""
    
    @pytest.mark.asyncio
    async def test_user_creation(self, test_db):
        """Test user model creation"""
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed_password_here"
        )
        test_db.add(user)
        await test_db.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.plan_type == "FREE"
    
    @pytest.mark.asyncio
    async def test_content_creation(self, test_db):
        """Test content model creation"""
        # Create user first
        user = User(
            email="content@example.com",
            username="contentuser",
            hashed_password="hashed"
        )
        test_db.add(user)
        await test_db.commit()
        
        # Create content
        content = Content(
            user_id=user.id,
            title="AWS Solutions Architect Guide",
            certification_type="AWS_SOLUTIONS_ARCHITECT",
            format="STUDY_GUIDE",
            content_data={"sections": []},
            quality_score=0.85
        )
        test_db.add(content)
        await test_db.commit()
        
        assert content.id is not None
        assert content.user_id == user.id
        assert content.title == "AWS Solutions Architect Guide"
        assert content.quality_score == 0.85
    
    @pytest.mark.asyncio
    async def test_domain_hierarchy(self, test_db):
        """Test domain and concept relationships"""
        # Create domain
        domain = Domain(
            name="Cloud Computing",
            description="AWS cloud computing concepts",
            certification_type="AWS_SOLUTIONS_ARCHITECT",
            weight=0.3
        )
        test_db.add(domain)
        await test_db.commit()
        
        # Create concepts
        concept1 = Concept(
            domain_id=domain.id,
            name="EC2",
            description="Elastic Compute Cloud",
            difficulty_level=2,
            importance_score=0.9
        )
        concept2 = Concept(
            domain_id=domain.id,
            name="S3",
            description="Simple Storage Service",
            difficulty_level=1,
            importance_score=0.95
        )
        test_db.add_all([concept1, concept2])
        await test_db.commit()
        
        # Create relationship
        relationship = Relationship(
            source_concept_id=concept1.id,
            target_concept_id=concept2.id,
            relationship_type="RELATED_TO",
            strength=0.7
        )
        test_db.add(relationship)
        await test_db.commit()
        
        assert domain.id is not None
        assert concept1.domain_id == domain.id
        assert relationship.strength == 0.7
    
    @pytest.mark.asyncio
    async def test_learning_path_creation(self, test_db):
        """Test learning path model"""
        # Create domain and concepts first
        domain = Domain(
            name="Security",
            certification_type="AWS_SECURITY",
            weight=0.4
        )
        test_db.add(domain)
        await test_db.commit()
        
        concepts = []
        for i in range(3):
            concept = Concept(
                domain_id=domain.id,
                name=f"Security Concept {i+1}",
                difficulty_level=i+1
            )
            concepts.append(concept)
        test_db.add_all(concepts)
        await test_db.commit()
        
        # Create learning path
        learning_path = LearningPath(
            name="Security Fundamentals Path",
            description="Learn AWS security basics",
            difficulty_level=2,
            estimated_hours=20,
            prerequisites=["Basic AWS knowledge"],
            concept_sequence=[str(c.id) for c in concepts]
        )
        test_db.add(learning_path)
        await test_db.commit()
        
        assert learning_path.id is not None
        assert learning_path.estimated_hours == 20
        assert len(learning_path.concept_sequence) == 3
    
    @pytest.mark.asyncio
    async def test_quality_check_workflow(self, test_db):
        """Test quality check model"""
        # Create user and content
        user = User(
            email="qa@example.com",
            username="qauser",
            hashed_password="hashed"
        )
        test_db.add(user)
        await test_db.commit()
        
        content = Content(
            user_id=user.id,
            title="Test Content",
            certification_type="AWS_DEVELOPER",
            format="PRACTICE_EXAM"
        )
        test_db.add(content)
        await test_db.commit()
        
        # Create quality check
        quality_check = QualityCheck(
            content_id=content.id,
            check_type="MULTI_AGENT_CONSENSUS",
            status="COMPLETED",
            overall_score=0.88,
            accuracy_score=0.9,
            completeness_score=0.85,
            technical_score=0.87,
            pedagogical_score=0.91,
            consensus_confidence=0.85,
            issues_found=[],
            suggestions=["Add more examples"],
            critic_evaluations={
                "critic_1": {"score": 0.89},
                "critic_2": {"score": 0.87},
                "critic_3": {"score": 0.88}
            }
        )
        test_db.add(quality_check)
        await test_db.commit()
        
        assert quality_check.id is not None
        assert quality_check.overall_score == 0.88
        assert len(quality_check.critic_evaluations) == 3
    
    @pytest.mark.asyncio
    async def test_generation_job_tracking(self, test_db):
        """Test generation job model"""
        user = User(
            email="job@example.com",
            username="jobuser",
            hashed_password="hashed"
        )
        test_db.add(user)
        await test_db.commit()
        
        job = GenerationJob(
            user_id=user.id,
            job_type="FULL_CONTENT_GENERATION",
            status="IN_PROGRESS",
            parameters={
                "certification_type": "AWS_SOLUTIONS_ARCHITECT",
                "format": "STUDY_GUIDE",
                "quality_level": "PREMIUM"
            },
            progress=45,
            current_phase="CONTENT_GENERATION"
        )
        test_db.add(job)
        await test_db.commit()
        
        assert job.id is not None
        assert job.progress == 45
        assert job.status == "IN_PROGRESS"
        
        # Update job progress
        job.progress = 100
        job.status = "COMPLETED"
        job.completed_at = datetime.utcnow()
        await test_db.commit()
        
        assert job.status == "COMPLETED"
        assert job.completed_at is not None


class TestDatabaseConstraints:
    """Test database constraints and validations"""
    
    @pytest.mark.asyncio
    async def test_unique_constraints(self, test_db):
        """Test unique constraints"""
        # Create first user
        user1 = User(
            email="unique@example.com",
            username="uniqueuser",
            hashed_password="hashed"
        )
        test_db.add(user1)
        await test_db.commit()
        
        # Try to create duplicate email
        user2 = User(
            email="unique@example.com",  # Same email
            username="differentuser",
            hashed_password="hashed"
        )
        test_db.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await test_db.commit()
    
    @pytest.mark.asyncio
    async def test_cascade_deletes(self, test_db):
        """Test cascade delete behavior"""
        # Create user with content
        user = User(
            email="cascade@example.com",
            username="cascadeuser",
            hashed_password="hashed"
        )
        test_db.add(user)
        await test_db.commit()
        
        content = Content(
            user_id=user.id,
            title="Test Content",
            certification_type="AWS_DEVELOPER",
            format="STUDY_GUIDE"
        )
        test_db.add(content)
        await test_db.commit()
        
        content_id = content.id
        
        # Delete user should cascade to content
        await test_db.delete(user)
        await test_db.commit()
        
        # Content should be gone
        result = await test_db.get(Content, content_id)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
