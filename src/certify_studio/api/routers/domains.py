"""
Domain extraction router - handles knowledge extraction from certification materials.
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from fastapi import (
    APIRouter, Depends, HTTPException, status,
    BackgroundTasks, Query
)

from ...core.logging import get_logger
from ...agents.specialized.domain_extraction import DomainExtractionAgent
from ...agents.specialized.domain_extraction.models import (
    ExtractionRequest as DomainExtractionRequestModel,
    SearchQuery
)
from sqlalchemy.ext.asyncio import AsyncSession
from ..dependencies import (
    get_current_verified_user,
    check_rate_limit,
    get_request_id,
    get_db
)
from ..schemas import (
    User,
    DomainExtractionRequest,
    DomainExtractionResponse,
    StatusEnum,
    ErrorResponse,
    ContentListResponse,
    BaseResponse
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/domains",
    tags=["domain-extraction"],
    dependencies=[Depends(check_rate_limit)],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)

# Global domain extraction agent (in production, use dependency injection)
# Domain extraction agent will be initialized per request
# to avoid module-level instantiation issues

async def get_domain_agent() -> DomainExtractionAgent:
    """Get or create domain extraction agent."""
    agent = DomainExtractionAgent()
    await agent.initialize()
    return agent

# Create a single instance for the module
domain_agent = None

# Active extraction tasks
extraction_tasks: Dict[UUID, Dict[str, Any]] = {}


@router.post(
    "/extract",
    response_model=DomainExtractionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Extract domain knowledge",
    description="Extract concepts, relationships, and learning paths from certification content"
)
async def extract_domain_knowledge(
    request: DomainExtractionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    request_id: str = Depends(get_request_id)
) -> DomainExtractionResponse:
    """Start domain knowledge extraction."""
    try:
        # Get or create domain agent
        global domain_agent
        if domain_agent is None:
            domain_agent = await get_domain_agent()
        
        # Get uploaded file path
        # upload = await db.get(Upload, request.upload_id)
        # if not upload or upload.user_id != current_user.id:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Upload not found"
        #     )
        
        # For demo, use a mock path
        file_path = f"/uploads/{request.upload_id}"
        
        # Create extraction task
        task_id = uuid4()
        extraction_request = DomainExtractionRequestModel(
            document_paths=[file_path],
            domain_name=request.certification_type.value,
            certification_name=request.certification_type.value,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            confidence_threshold=request.confidence_threshold,
            extract_prerequisites=request.extract_prerequisites,
            extract_learning_paths=request.extract_learning_paths,
            extract_exam_weights=request.extract_exam_weights
        )
        
        # Store task info
        extraction_tasks[task_id] = {
            "user_id": current_user.id,
            "status": StatusEnum.PROCESSING,
            "started_at": datetime.utcnow(),
            "request": extraction_request
        }
        
        # Start extraction in background
        background_tasks.add_task(
            run_extraction,
            task_id,
            extraction_request,
            current_user.id,
            db
        )
        
        # Return immediate response
        return DomainExtractionResponse(
            status=StatusEnum.SUCCESS,
            message="Domain extraction started",
            request_id=UUID(request_id),
            extraction_id=task_id,
            total_concepts=0,
            total_relationships=0,
            total_prerequisites=0,
            domains=[],
            overall_confidence=0.0,
            domain_confidences={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Domain extraction start error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start domain extraction"
        )


async def run_extraction(
    task_id: UUID,
    request: DomainExtractionRequestModel,
    user_id: UUID,
    db: AsyncSession
) -> None:
    """Run domain extraction in background."""
    try:
        # Run extraction
        result = await domain_agent.extract_domain_knowledge(request)
        
        if result.success:
            # Store results
            extraction_tasks[task_id].update({
                "status": StatusEnum.COMPLETED,
                "completed_at": datetime.utcnow(),
                "result": result
            })
            
            # Update user stats
            # await db.execute(
            #     update(User).where(User.id == user_id).values(
            #         total_extractions=User.total_extractions + 1
            #     )
            # )
            # await db.commit()
            
        else:
            extraction_tasks[task_id].update({
                "status": StatusEnum.FAILED,
                "error": result.error or "Unknown error"
            })
            
    except Exception as e:
        logger.error(f"Extraction error for task {task_id}: {e}")
        extraction_tasks[task_id].update({
            "status": StatusEnum.FAILED,
            "error": str(e)
        })


@router.get(
    "/extract/{task_id}",
    response_model=DomainExtractionResponse,
    summary="Get extraction results",
    description="Get the results of a domain extraction task"
)
async def get_extraction_results(
    task_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    request_id: str = Depends(get_request_id)
) -> DomainExtractionResponse:
    """Get extraction task results."""
    if task_id not in extraction_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction task not found"
        )
    
    task = extraction_tasks[task_id]
    
    # Check ownership
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build response based on status
    if task["status"] == StatusEnum.COMPLETED:
        result = task["result"]
        knowledge = result.domain_knowledge
        
        # Format domains
        domains = []
        for domain in knowledge.domains:
            domains.append({
                "name": domain.name,
                "weight": domain.weight,
                "concept_count": len([c for c in knowledge.concepts if c.domain == domain.name]),
                "confidence": domain.confidence
            })
        
        # Create concept graph summary
        graph_data = None
        if knowledge.relationships:
            graph_data = {
                "nodes": len(knowledge.concepts),
                "edges": len(knowledge.relationships),
                "density": len(knowledge.relationships) / (len(knowledge.concepts) * (len(knowledge.concepts) - 1))
                if len(knowledge.concepts) > 1 else 0
            }
        
        # Format learning paths
        learning_paths = []
        if hasattr(knowledge, 'learning_paths'):
            for path in knowledge.learning_paths[:5]:  # Top 5 paths
                learning_paths.append({
                    "name": path.name,
                    "steps": len(path.concepts),
                    "duration_hours": path.estimated_hours,
                    "difficulty": path.difficulty_level
                })
        
        return DomainExtractionResponse(
            status=StatusEnum.SUCCESS,
            message="Extraction completed successfully",
            request_id=UUID(request_id),
            extraction_id=task_id,
            total_concepts=knowledge.total_concepts,
            total_relationships=knowledge.total_relationships,
            total_prerequisites=len([r for r in knowledge.relationships if r.type == "prerequisite"]),
            domains=domains,
            concept_graph=graph_data,
            learning_paths=learning_paths,
            overall_confidence=result.confidence,
            domain_confidences={d.name: d.confidence for d in knowledge.domains}
        )
    
    elif task["status"] == StatusEnum.PROCESSING:
        # Return progress
        return DomainExtractionResponse(
            status=StatusEnum.SUCCESS,
            message="Extraction in progress",
            request_id=UUID(request_id),
            extraction_id=task_id,
            total_concepts=0,
            total_relationships=0,
            total_prerequisites=0,
            domains=[],
            overall_confidence=0.0,
            domain_confidences={}
        )
    
    else:  # Failed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=task.get("error", "Extraction failed")
        )


@router.post(
    "/search",
    response_model=ContentListResponse,
    summary="Search extracted knowledge",
    description="Search through extracted concepts and relationships"
)
async def search_knowledge(
    query: str = Query(..., description="Search query"),
    extraction_id: Optional[UUID] = Query(None, description="Limit to specific extraction"),
    max_results: int = Query(20, ge=1, le=100),
    include_relationships: bool = Query(True),
    current_user: User = Depends(get_current_verified_user),
    request_id: str = Depends(get_request_id)
) -> ContentListResponse:
    """Search extracted knowledge."""
    try:
        # Build search query
        search_query = SearchQuery(
            query=query,
            max_results=max_results,
            include_prerequisites=include_relationships,
            include_relationships=include_relationships,
            min_confidence=0.5
        )
        
        # Search across user's extractions
        results = []
        
        if extraction_id:
            # Search specific extraction
            if extraction_id in extraction_tasks:
                task = extraction_tasks[extraction_id]
                if task["user_id"] == current_user.id and task["status"] == StatusEnum.COMPLETED:
                    agent = await get_domain_agent()
                    search_results = await agent.search_knowledge(search_query)
                    results.extend(search_results.results)
        else:
            # Search all user's extractions
            for task_id, task in extraction_tasks.items():
                if task["user_id"] == current_user.id and task["status"] == StatusEnum.COMPLETED:
                    # In production, search would be across persistent storage
                    pass
        
        # Format results
        items = []
        for result in results[:max_results]:
            item = {
                "id": str(result.concept.id),
                "name": result.concept.name,
                "type": result.concept.type,
                "description": result.concept.description,
                "score": result.score,
                "domain": result.concept.domain,
                "difficulty": result.concept.difficulty_level
            }
            
            if include_relationships and hasattr(result, 'relationships'):
                item["relationships"] = [
                    {
                        "type": rel.type,
                        "target": rel.target_name,
                        "strength": rel.strength
                    }
                    for rel in result.relationships
                ]
            
            items.append(item)
        
        return ContentListResponse(
            status=StatusEnum.SUCCESS,
            message=f"Found {len(items)} results",
            request_id=UUID(request_id),
            items=items,
            total=len(items),
            page=1,
            page_size=max_results,
            pages=1
        )
        
    except Exception as e:
        logger.error(f"Knowledge search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


@router.get(
    "/graph/{extraction_id}",
    response_model=Dict[str, Any],
    summary="Get knowledge graph",
    description="Get the knowledge graph visualization data"
)
async def get_knowledge_graph(
    extraction_id: UUID,
    format: str = Query("json", pattern="^(json|gexf|graphml)$"),
    max_nodes: int = Query(100, ge=10, le=500),
    current_user: User = Depends(get_current_verified_user)
) -> Dict[str, Any]:
    """Get knowledge graph data."""
    if extraction_id not in extraction_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    
    task = extraction_tasks[extraction_id]
    
    # Check ownership and completion
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if task["status"] != StatusEnum.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extraction not completed"
        )
    
    try:
        # Export graph
        agent = await get_domain_agent()
        graph_data = await agent.export_knowledge_graph(
            format=format,
            max_nodes=max_nodes
        )
        
        return {
            "format": format,
            "data": graph_data,
            "metadata": {
                "total_nodes": task["result"].domain_knowledge.total_concepts,
                "total_edges": task["result"].domain_knowledge.total_relationships,
                "truncated": task["result"].domain_knowledge.total_concepts > max_nodes
            }
        }
        
    except Exception as e:
        logger.error(f"Graph export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export graph"
        )


@router.get(
    "/learning-paths/{extraction_id}",
    response_model=List[Dict[str, Any]],
    summary="Get learning paths",
    description="Get suggested learning paths from extracted knowledge"
)
async def get_learning_paths(
    extraction_id: UUID,
    target_concept: Optional[str] = Query(None, description="Target concept to reach"),
    max_paths: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_verified_user)
) -> List[Dict[str, Any]]:
    """Get learning paths."""
    if extraction_id not in extraction_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    
    task = extraction_tasks[extraction_id]
    
    # Check ownership and completion
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if task["status"] != StatusEnum.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extraction not completed"
        )
    
    try:
        # Get learning paths
        knowledge = task["result"].domain_knowledge
        paths = []
        
        # In production, this would use the graph to generate paths
        # For now, return mock paths
        for i in range(min(max_paths, 3)):
            path = {
                "id": str(uuid4()),
                "name": f"Learning Path {i+1}",
                "description": f"Path to master {target_concept or 'all concepts'}",
                "total_concepts": 10 + i * 5,
                "estimated_hours": 20 + i * 10,
                "difficulty": ["beginner", "intermediate", "advanced"][i],
                "concepts": [
                    {
                        "order": j + 1,
                        "name": f"Concept {j+1}",
                        "duration_hours": 2,
                        "prerequisites": [] if j == 0 else [f"Concept {j}"]
                    }
                    for j in range(5)
                ]
            }
            paths.append(path)
        
        return paths
        
    except Exception as e:
        logger.error(f"Learning paths error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get learning paths"
        )


@router.delete(
    "/extract/{task_id}",
    response_model=BaseResponse,
    summary="Delete extraction",
    description="Delete extraction results and free up resources"
)
async def delete_extraction(
    task_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    request_id: str = Depends(get_request_id)
) -> BaseResponse:
    """Delete extraction results."""
    if task_id not in extraction_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    
    task = extraction_tasks[task_id]
    
    # Check ownership
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Delete extraction
    del extraction_tasks[task_id]
    
    # In production, also delete from persistent storage
    
    return BaseResponse(
        status=StatusEnum.SUCCESS,
        message="Extraction deleted successfully",
        request_id=UUID(request_id)
    )


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Get extraction statistics",
    description="Get statistics about user's domain extractions"
)
async def get_extraction_stats(
    current_user: User = Depends(get_current_verified_user)
) -> Dict[str, Any]:
    """Get user's extraction statistics."""
    user_tasks = [
        task for task_id, task in extraction_tasks.items()
        if task["user_id"] == current_user.id
    ]
    
    completed_tasks = [
        task for task in user_tasks
        if task["status"] == StatusEnum.COMPLETED
    ]
    
    # Calculate stats
    total_concepts = sum(
        task["result"].domain_knowledge.total_concepts
        for task in completed_tasks
        if "result" in task
    )
    
    total_relationships = sum(
        task["result"].domain_knowledge.total_relationships
        for task in completed_tasks
        if "result" in task
    )
    
    certification_types = {}
    for task in completed_tasks:
        cert_type = task["request"].certification_name
        certification_types[cert_type] = certification_types.get(cert_type, 0) + 1
    
    return {
        "total_extractions": len(user_tasks),
        "completed_extractions": len(completed_tasks),
        "total_concepts_extracted": total_concepts,
        "total_relationships_found": total_relationships,
        "average_concepts_per_extraction": total_concepts / len(completed_tasks) if completed_tasks else 0,
        "certification_types": certification_types,
        "last_extraction_date": max(
            (task["started_at"] for task in user_tasks),
            default=None
        )
    }
