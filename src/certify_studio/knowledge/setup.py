"""
Clean setup for Unified GraphRAG System - No migration needed!

This is the recommended setup for new Certify Studio deployments.
"""

from typing import Optional
from pathlib import Path

from loguru import logger

from ..knowledge import UnifiedGraphRAG, UnifiedVectorStore
from ..agents.specialized.domain_extraction import DomainExtractionAgent


async def setup_unified_system(
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "certify-studio-2024"
):
    """
    Set up the unified GraphRAG system for Certify Studio.
    
    This is the clean setup - no migration needed since there's no legacy data.
    """
    logger.info("Setting up Unified GraphRAG system")
    
    # 1. Create and initialize the unified GraphRAG
    graphrag = UnifiedGraphRAG(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password
    )
    await graphrag.initialize()
    logger.success("Unified GraphRAG initialized")
    
    # 2. Create Domain Extraction Agent
    domain_agent = DomainExtractionAgent()
    await domain_agent.initialize()
    
    # 3. Connect Domain Extraction to Unified GraphRAG
    # Replace the old vector store with unified system
    domain_agent.vector_store = UnifiedVectorStore(graphrag)
    
    # 4. Enhance extraction to automatically import into unified graph
    original_extract = domain_agent.extract_domain_knowledge
    
    async def enhanced_extract(request):
        """Extract knowledge and import into unified graph."""
        # Run extraction
        result = await original_extract(request)
        
        if result.success and result.domain_knowledge:
            # Import into unified graph
            stats = await graphrag.import_from_domain_extraction(
                result.domain_knowledge
            )
            logger.info(f"Imported into unified graph: {stats}")
            
            # Add stats to result metadata
            result.metadata["unified_graph_stats"] = stats
            
        return result
    
    # Replace the method
    domain_agent.extract_domain_knowledge = enhanced_extract
    
    logger.success("Domain Extraction connected to Unified GraphRAG")
    
    return graphrag, domain_agent


# Example usage
async def main():
    """Example of using the unified system."""
    # Set up the system
    graphrag, domain_agent = await setup_unified_system()
    
    # Extract knowledge from a document
    from ..agents.specialized.domain_extraction.models import ExtractionRequest
    
    request = ExtractionRequest(
        document_paths=["path/to/certification-guide.pdf"],
        domain_name="AWS Solutions Architect",
        certification_name="AWS-SAA-C03"
    )
    
    # This will automatically extract AND import into unified graph
    result = await domain_agent.extract_domain_knowledge(request)
    
    if result.success:
        print(f"Extracted and imported: {result.metadata['unified_graph_stats']}")
    
    # Now you can query the unified system
    from ..knowledge import GraphRAGQuery
    
    # Educational query
    edu_result = await graphrag.search(GraphRAGQuery(
        query_text="What are VPC endpoints?",
        query_type="educational"
    ))
    
    # Troubleshooting query
    trouble_result = await graphrag.search(GraphRAGQuery(
        query_text="Lambda function timeout in VPC",
        query_type="troubleshooting"
    ))
    
    # The system has both educational content AND troubleshooting in ONE graph!
    
    await graphrag.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
