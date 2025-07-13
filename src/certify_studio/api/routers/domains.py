"""
Domain extraction router - handles knowledge extraction from certification content.
"""

from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Query

from ...core.logging import get_logger
from ...agents.specialized.domain_extraction import DomainExtractionAgent
from ..dependencies import (
    VerifiedUser,
    Database,
    RateLimit,
    get_request_id
)
from ..schemas import (
    DomainExtractionRequest,
    DomainExtractionResponse,
    StatusEnum,
    ErrorResponse
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/domains",
    tags=["domain-extraction"],
    dependencies=[Depends(RateLimit)],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)

# Domain extraction agent instance
domain_agent = DomainExtractionAgent()


@router.post(
    "/extract",
    response_model=DomainExtractionResponse,
    summary="Extract domain knowledge",
    description="Extract concepts, relationships, and learning paths from certification content"
)
async def extract_domain(
    request: DomainExtractionRequest,
    current_user: VerifiedUser,
    db: Database,
    request_id: str = Depends(get_request_id)
) -> DomainExtractionResponse:
    """Extract domain knowledge from uploaded content."""
    try:
        # Initialize agent if needed
        if not domain_agent.is_initialized:
            await domain_agent.initialize()
        
        # Get uploaded file
        # In production, retrieve from database
        file_path = f"/uploads/{request.upload_id}"
        
        # Create extraction request
        extraction_request = {
            "document_paths": [file_path],
            "domain_name": request.certification_type.value,
            "certification_name": request.certification_type.value,
            "chunk_size": request.chunk_size,
            "chunk_overlap": request.chunk_overlap,
            "extract_prerequisites": request.extract_prerequisites,
            "extract_exam_weights": request.extract_exam_weights,
            "confidence_threshold": request.confidence_threshold
        }
        
        # Extract domain knowledge
        result = await domain_agent.extract_domain_knowledge(extraction_request)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Domain extraction failed"
            )
        
        knowledge = result.domain_knowledge
        
        # Build response
        response = DomainExtractionResponse(
            status=StatusEnum.SUCCESS,
            message="Domain extraction completed",
            extraction_id=uuid4(),
            total_concepts=knowledge.total_concepts,
            total_relationships=knowledge.total_relationships,
            total_domains=len(knowledge.domains),
            domains=[
                {
                    "name": domain.name,
                    "weight": domain.weight,
                    "concepts_count": len(domain.concepts),
                    "description": domain.description
                }
                for domain in knowledge.domains
            ],
            concepts=[
                {
                    "id": str(concept.id),
                    "name": concept.name,
                    "type": concept.type.value,
                    "importance": concept.importance_score,
                    "prerequisites": [str(p) for p in concept.prerequisites]
                }
                for concept in knowledge.concepts[:100]  # Limit for response size
            ],
            prerequisites=[
                {
                    "concept": str(rel.source_id),
                    "prerequisite": str(rel.target_id),
                    "strength": rel.strength
                }
                for rel in knowledge.relationships
                if rel.type.value == "prerequisite"
            ][:100],  # Limit for response size
            extraction_confidence=knowledge.extraction_confidence,
            coverage_score=0.95,  # Would be calculated
            request_id=UUID(request_id)
        )
        
        # Generate learning paths if requested
        if request.extract_learning_paths:
            paths = await domain_agent.generate_learning_paths(knowledge)
            response.learning_paths = [
                {
                    "path_id": str(uuid4()),
                    "difficulty": "intermediate",
                    "estimated_hours": len(path) * 2,
                    "concepts": [str(c.id) for c in path]
                }
                for path in paths[:5]  # Top 5 paths
            ]
        
        # Generate knowledge graph URL
        response.knowledge_graph_url = f"/api/domains/graph/{response.extraction_id}"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Domain extraction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Domain extraction failed"
        )


@router.get(
    "/search",
    response_model=Dict[str, Any],
    summary="Search domain knowledge",
    description="Search extracted concepts and relationships"
)
async def search_knowledge(
    query: str = Query(..., description="Search query"),
    extraction_id: UUID = Query(..., description="Extraction ID"),
    max_results: int = Query(10, ge=1, le=50, description="Maximum results"),
    current_user: VerifiedUser
) -> Dict[str, Any]:
    """Search extracted domain knowledge."""
    try:
        # In production, retrieve knowledge from database
        # For now, use agent's search capability
        
        search_results = await domain_agent.search_knowledge({
            "query": query,
            "max_results": max_results,
            "filters": {
                "extraction_id": str(extraction_id)
            }
        })
        
        return {
            "status": "success",
            "query": query,
            "total_results": len(search_results.results),
            "results": [
                {
                    "concept_id": str(result.concept.id),
                    "name": result.concept.name,
                    "type": result.concept.type.value,
                    "relevance_score": result.relevance_score,
                    "snippet": result.snippet,
                    "context": result.context
                }
                for result in search_results.results
            ]
        }
        
    except Exception as e:
        logger.error(f"Knowledge search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Knowledge search failed"
        )


@router.get(
    "/graph/{extraction_id}",
    response_model=Dict[str, Any],
    summary="Get knowledge graph",
    description="Get interactive knowledge graph visualization data"
)
async def get_knowledge_graph(
    extraction_id: UUID,
    current_user: VerifiedUser,
    include_prerequisites: bool = Query(True, description="Include prerequisite relationships"),
    include_related: bool = Query(True, description="Include related concepts"),
    max_nodes: int = Query(100, ge=10, le=500, description="Maximum nodes to display")
) -> Dict[str, Any]:
    """Get knowledge graph data."""
    try:
        # In production, retrieve from database
        # For now, generate sample data
        
        graph_data = await domain_agent.export_knowledge_graph(
            format="json",
            filters={
                "extraction_id": str(extraction_id),
                "include_prerequisites": include_prerequisites,
                "include_related": include_related,
                "max_nodes": max_nodes
            }
        )
        
        return {
            "status": "success",
            "extraction_id": str(extraction_id),
            "graph": graph_data,
            "statistics": {
                "total_nodes": len(graph_data.get("nodes", [])),
                "total_edges": len(graph_data.get("edges", [])),
                "node_types": {
                    "concept": sum(1 for n in graph_data.get("nodes", []) if n.get("type") == "concept"),
                    "domain": sum(1 for n in graph_data.get("nodes", []) if n.get("type") == "domain")
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Knowledge graph error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate knowledge graph"
        )


@router.get(
    "/concepts/{concept_id}",
    response_model=Dict[str, Any],
    summary="Get concept details",
    description="Get detailed information about a specific concept"
)
async def get_concept_details(
    concept_id: UUID,
    current_user: VerifiedUser
) -> Dict[str, Any]:
    """Get detailed concept information."""
    try:
        # In production, retrieve from database
        # For now, return sample data
        
        return {
            "status": "success",
            "concept": {
                "id": str(concept_id),
                "name": "Amazon EC2",
                "type": "service",
                "description": "Elastic Compute Cloud - Virtual servers in the cloud",
                "importance_score": 0.95,
                "difficulty_level": 0.6,
                "exam_weight": 0.15,
                "prerequisites": [
                    {"id": "uuid1", "name": "Cloud Computing Basics"},
                    {"id": "uuid2", "name": "Virtualization"}
                ],
                "related_concepts": [
                    {"id": "uuid3", "name": "Amazon EBS", "relationship": "storage"},
                    {"id": "uuid4", "name": "Security Groups", "relationship": "security"}
                ],
                "learning_resources": [
                    {
                        "type": "documentation",
                        "title": "EC2 User Guide",
                        "url": "https://docs.aws.amazon.com/ec2"
                    }
                ],
                "exam_topics": [
                    "Instance types and families",
                    "Pricing models",
                    "Security best practices"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Get concept error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve concept details"
        )


@router.post(
    "/compare",
    response_model=Dict[str, Any],
    summary="Compare domains",
    description="Compare knowledge domains from different certifications"
)
async def compare_domains(
    extraction_ids: List[UUID] = Query(..., description="Extraction IDs to compare"),
    current_user: VerifiedUser
) -> Dict[str, Any]:
    """Compare multiple domain extractions."""
    try:
        if len(extraction_ids) < 2 or len(extraction_ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide 2-5 extraction IDs to compare"
            )
        
        # In production, perform actual comparison
        # For now, return sample data
        
        return {
            "status": "success",
            "comparison": {
                "extraction_ids": [str(eid) for eid in extraction_ids],
                "common_concepts": [
                    {
                        "name": "Cloud Computing",
                        "presence": [True, True, True],
                        "importance_scores": [0.9, 0.85, 0.92]
                    }
                ],
                "unique_concepts": {
                    str(extraction_ids[0]): ["AWS Lambda", "Amazon S3"],
                    str(extraction_ids[1]): ["Azure Functions", "Blob Storage"]
                },
                "similarity_matrix": [
                    [1.0, 0.75, 0.68],
                    [0.75, 1.0, 0.72],
                    [0.68, 0.72, 1.0]
                ],
                "recommendations": [
                    "High overlap in cloud computing fundamentals",
                    "Platform-specific services differ significantly"
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Domain comparison error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Domain comparison failed"
        )


@router.get(
    "/learning-paths/{extraction_id}",
    response_model=Dict[str, Any],
    summary="Get learning paths",
    description="Get recommended learning paths for certification"
)
async def get_learning_paths(
    extraction_id: UUID,
    current_user: VerifiedUser,
    difficulty: str = Query("intermediate", description="Difficulty level"),
    max_paths: int = Query(5, ge=1, le=20, description="Maximum paths to return")
) -> Dict[str, Any]:
    """Get recommended learning paths."""
    try:
        # In production, generate actual learning paths
        # For now, return sample data
        
        paths = [
            {
                "path_id": str(uuid4()),
                "name": "AWS Fundamentals to Solutions Architect",
                "difficulty": difficulty,
                "estimated_hours": 120,
                "concepts_count": 45,
                "milestones": [
                    {
                        "name": "Cloud Computing Basics",
                        "concepts": 5,
                        "hours": 10
                    },
                    {
                        "name": "Core AWS Services",
                        "concepts": 15,
                        "hours": 40
                    },
                    {
                        "name": "Advanced Architecture",
                        "concepts": 25,
                        "hours": 70
                    }
                ],
                "prerequisites_met": 0.85,
                "completion_rate": 0.78
            }
            for i in range(min(max_paths, 5))
        ]
        
        return {
            "status": "success",
            "extraction_id": str(extraction_id),
            "total_paths": len(paths),
            "difficulty": difficulty,
            "paths": paths,
            "recommendations": [
                "Start with Cloud Computing Basics if new to cloud",
                "Focus on hands-on labs for better retention",
                "Review security best practices throughout"
            ]
        }
        
    except Exception as e:
        logger.error(f"Learning paths error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate learning paths"
        )
