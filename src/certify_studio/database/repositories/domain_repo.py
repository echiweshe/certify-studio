"""
Domain extraction and knowledge graph repository for Certify Studio.

This module provides data access layer for domain-related operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from ..models.domain import (
    ExtractedConcept, CanonicalConcept, ConceptRelationship,
    LearningObjective, PrerequisiteMapping, LearningPath,
    LearningPathNode, DomainTaxonomy,
    ConceptType, RelationshipType, DifficultyLevel
)
from .base_repo import BaseRepository, RepositoryError


class DomainRepository(BaseRepository[ExtractedConcept]):
    """Repository for domain-related operations."""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(ExtractedConcept, db_session)
    
    # ExtractedConcept operations
    
    async def create_extracted_concept(
        self,
        generation_id: UUID,
        name: str,
        description: str,
        concept_type: str,
        importance_score: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExtractedConcept:
        """Create a new extracted concept."""
        concept = ExtractedConcept(
            generation_id=generation_id,
            name=name,
            display_name=name,  # Can be enhanced later
            slug=name.lower().replace(" ", "-"),
            concept_type=ConceptType(concept_type),
            description=description,
            importance_score=importance_score,
            difficulty_level=DifficultyLevel.INTERMEDIATE,  # Default
            extra_metadata=metadata or {}
        )
        
        self.db_session.add(concept)
        await self.db_session.flush()
        return concept
    
    async def get_concepts_by_generation(
        self,
        generation_id: UUID,
        include_relationships: bool = False
    ) -> List[ExtractedConcept]:
        """Get all concepts extracted from a generation."""
        query = select(ExtractedConcept).where(
            ExtractedConcept.generation_id == generation_id
        ).order_by(ExtractedConcept.importance_score.desc())
        
        if include_relationships:
            query = query.options(
                selectinload(ExtractedConcept.source_relationships),
                selectinload(ExtractedConcept.target_relationships)
            )
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def update_concept_embedding(
        self,
        concept_id: UUID,
        embedding: List[float]
    ) -> None:
        """Update concept embedding vector."""
        await self.db_session.execute(
            update(ExtractedConcept)
            .where(ExtractedConcept.id == concept_id)
            .values(embedding_vector=embedding)
        )
    
    # ConceptRelationship operations
    
    async def create_concept_relationship(
        self,
        source_concept_id: UUID,
        target_concept_id: UUID,
        relationship_type: str,
        strength: float = 1.0,
        confidence: float = 1.0
    ) -> ConceptRelationship:
        """Create a relationship between concepts."""
        relationship = ConceptRelationship(
            source_concept_id=source_concept_id,
            target_concept_id=target_concept_id,
            relationship_type=RelationshipType(relationship_type),
            strength=strength,
            confidence=confidence
        )
        
        self.db_session.add(relationship)
        await self.db_session.flush()
        return relationship
    
    async def get_concept_relationships(
        self,
        concept_id: UUID,
        relationship_type: Optional[RelationshipType] = None
    ) -> List[ConceptRelationship]:
        """Get all relationships for a concept."""
        query = select(ConceptRelationship).where(
            or_(
                ConceptRelationship.source_concept_id == concept_id,
                ConceptRelationship.target_concept_id == concept_id
            )
        )
        
        if relationship_type:
            query = query.where(ConceptRelationship.relationship_type == relationship_type)
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    # CanonicalConcept operations
    
    async def find_canonical_concept(
        self,
        name: str,
        concept_type: Optional[ConceptType] = None
    ) -> Optional[CanonicalConcept]:
        """Find a canonical concept by name."""
        query = select(CanonicalConcept).where(
            CanonicalConcept.name.ilike(f"%{name}%")
        )
        
        if concept_type:
            query = query.where(CanonicalConcept.concept_type == concept_type)
        
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_canonical_concept(self, concept_id: UUID) -> Optional[CanonicalConcept]:
        """Get a canonical concept by ID."""
        result = await self.db_session.execute(
            select(CanonicalConcept).where(CanonicalConcept.id == concept_id)
        )
        return result.scalar_one_or_none()
    
    async def create_or_update_canonical_concept(
        self,
        extracted_concept: ExtractedConcept
    ) -> CanonicalConcept:
        """Create or update canonical concept from extracted concept."""
        # Check if exists
        canonical = await self.find_canonical_concept(
            extracted_concept.name,
            extracted_concept.concept_type
        )
        
        if canonical:
            # Update usage count and scores
            canonical.usage_count += 1
            canonical.last_seen_at = datetime.utcnow()
            
            # Update average scores
            total_count = canonical.usage_count
            canonical.avg_importance_score = (
                (canonical.avg_importance_score * (total_count - 1) + extracted_concept.importance_score) / total_count
            )
            
            # Add any new aliases
            if extracted_concept.aliases:
                canonical.all_aliases = list(set(canonical.all_aliases + extracted_concept.aliases))
        else:
            # Create new canonical concept
            canonical = CanonicalConcept(
                name=extracted_concept.name,
                display_name=extracted_concept.display_name,
                concept_type=extracted_concept.concept_type,
                description=extracted_concept.description,
                definition=extracted_concept.definition,
                all_aliases=extracted_concept.aliases or [],
                all_tags=extracted_concept.tags or [],
                usage_count=1,
                last_seen_at=datetime.utcnow(),
                avg_importance_score=extracted_concept.importance_score,
                avg_difficulty_score=0.5  # Default
            )
            self.db_session.add(canonical)
        
        await self.db_session.flush()
        
        # Link extracted concept to canonical
        extracted_concept.canonical_id = canonical.id
        
        return canonical
    
    # LearningPath operations
    
    async def create_learning_path(
        self,
        generation_id: UUID,
        path_name: str,
        concept_sequence: List[UUID],
        target_concept_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LearningPath:
        """Create a new learning path."""
        path = LearningPath(
            generation_id=generation_id,
            path_name=path_name,
            concept_sequence=concept_sequence,
            target_concept_id=target_concept_id,
            total_concepts=len(concept_sequence),
            path_metadata=metadata or {}
        )
        
        self.db_session.add(path)
        await self.db_session.flush()
        
        # Create path nodes
        for i, concept_id in enumerate(concept_sequence):
            node = LearningPathNode(
                learning_path_id=path.id,
                concept_id=concept_id,
                sequence_order=i
            )
            self.db_session.add(node)
        
        await self.db_session.flush()
        return path
    
    async def get_learning_paths_for_generation(
        self,
        generation_id: UUID
    ) -> List[LearningPath]:
        """Get all learning paths for a generation."""
        result = await self.db_session.execute(
            select(LearningPath)
            .where(LearningPath.generation_id == generation_id)
            .options(selectinload(LearningPath.path_nodes))
        )
        return result.scalars().all()
    
    # PrerequisiteMapping operations
    
    async def create_prerequisite_mapping(
        self,
        concept_id: UUID,
        prerequisite_id: UUID,
        is_hard_requirement: bool = True,
        minimum_mastery_level: float = 0.7,
        rationale: Optional[str] = None
    ) -> PrerequisiteMapping:
        """Create a prerequisite mapping."""
        mapping = PrerequisiteMapping(
            concept_id=concept_id,
            prerequisite_id=prerequisite_id,
            is_hard_requirement=is_hard_requirement,
            minimum_mastery_level=minimum_mastery_level,
            rationale=rationale
        )
        
        self.db_session.add(mapping)
        await self.db_session.flush()
        return mapping
    
    async def get_prerequisites_for_concept(
        self,
        concept_id: UUID,
        only_hard_requirements: bool = False
    ) -> List[PrerequisiteMapping]:
        """Get prerequisites for a concept."""
        query = select(PrerequisiteMapping).where(
            PrerequisiteMapping.concept_id == concept_id
        )
        
        if only_hard_requirements:
            query = query.where(PrerequisiteMapping.is_hard_requirement == True)
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    # LearningObjective operations
    
    async def create_learning_objective(
        self,
        concept_id: UUID,
        objective_text: str,
        bloom_level: str,
        measurable_outcome: str,
        success_criteria: Optional[List[str]] = None
    ) -> LearningObjective:
        """Create a learning objective for a concept."""
        objective = LearningObjective(
            concept_id=concept_id,
            objective_text=objective_text,
            bloom_level=bloom_level,
            measurable_outcome=measurable_outcome,
            success_criteria=success_criteria or []
        )
        
        self.db_session.add(objective)
        await self.db_session.flush()
        return objective
    
    async def get_learning_objectives_for_concept(
        self,
        concept_id: UUID
    ) -> List[LearningObjective]:
        """Get all learning objectives for a concept."""
        result = await self.db_session.execute(
            select(LearningObjective)
            .where(LearningObjective.concept_id == concept_id)
            .order_by(LearningObjective.order_index)
        )
        return result.scalars().all()
    
    # DomainTaxonomy operations
    
    async def get_or_create_taxonomy(
        self,
        domain: str,
        category: str,
        subcategory: Optional[str] = None
    ) -> DomainTaxonomy:
        """Get or create a domain taxonomy entry."""
        result = await self.db_session.execute(
            select(DomainTaxonomy).where(
                and_(
                    DomainTaxonomy.domain == domain,
                    DomainTaxonomy.category == category,
                    DomainTaxonomy.subcategory == subcategory
                )
            )
        )
        
        taxonomy = result.scalar_one_or_none()
        
        if not taxonomy:
            taxonomy = DomainTaxonomy(
                domain=domain,
                category=category,
                subcategory=subcategory
            )
            self.db_session.add(taxonomy)
            await self.db_session.flush()
        
        return taxonomy
    
    # Search operations
    
    async def search_concepts(
        self,
        query: str,
        generation_id: Optional[UUID] = None,
        concept_types: Optional[List[ConceptType]] = None,
        limit: int = 20
    ) -> List[ExtractedConcept]:
        """Search for concepts by text query."""
        search_query = select(ExtractedConcept).where(
            or_(
                ExtractedConcept.name.ilike(f"%{query}%"),
                ExtractedConcept.description.ilike(f"%{query}%"),
                ExtractedConcept.aliases.contains([query])
            )
        )
        
        if generation_id:
            search_query = search_query.where(ExtractedConcept.generation_id == generation_id)
        
        if concept_types:
            search_query = search_query.where(ExtractedConcept.concept_type.in_(concept_types))
        
        search_query = search_query.order_by(
            ExtractedConcept.importance_score.desc()
        ).limit(limit)
        
        result = await self.db_session.execute(search_query)
        return result.scalars().all()
