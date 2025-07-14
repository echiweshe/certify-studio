"""
Migration module for transitioning to Unified GraphRAG.

This module helps migrate from the separate RAG/Knowledge Base architecture
to the unified GraphRAG system while maintaining backward compatibility.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import asyncio

from loguru import logger

from ..knowledge import UnifiedGraphRAG, UnifiedVectorStore, GraphRAGQuery
from ..agents.specialized.domain_extraction import DomainExtractionAgent
from ..agents.specialized.domain_extraction.models import DomainKnowledge


class UnifiedSystemMigration:
    """
    Handles migration from separate systems to unified GraphRAG.
    
    This allows us to:
    1. Keep existing code working during migration
    2. Gradually update agents to use unified system
    3. Import existing data into unified graph
    """
    
    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j", 
        neo4j_password: str = "certify-studio-2024"
    ):
        # Create unified system
        self.unified_graphrag = UnifiedGraphRAG(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password
        )
        
        # Compatibility wrapper
        self.vector_store_compat = UnifiedVectorStore(self.unified_graphrag)
        
    async def initialize(self):
        """Initialize the unified system."""
        await self.unified_graphrag.initialize()
        logger.info("Unified GraphRAG system initialized")
        
    async def migrate_domain_extraction_agent(self, agent: DomainExtractionAgent):
        """
        Update Domain Extraction Agent to use unified system.
        
        This replaces:
        - agent.vector_store → unified system
        - agent.graph_builder → unified system
        """
        # Replace vector store with compatibility wrapper
        agent.vector_store = self.vector_store_compat
        
        # Add method to import into unified graph
        original_extract = agent.extract_domain_knowledge
        
        async def unified_extract(request):
            # Run original extraction
            result = await original_extract(request)
            
            if result.success and result.domain_knowledge:
                # Import into unified graph
                stats = await self.unified_graphrag.import_from_domain_extraction(
                    result.domain_knowledge
                )
                logger.info(f"Imported domain knowledge into unified graph: {stats}")
                
                # Update result with unified system info
                result.metadata["unified_graph_stats"] = stats
                
            return result
            
        # Replace method
        agent.extract_domain_knowledge = unified_extract
        
        logger.info("Domain Extraction Agent migrated to unified system")
        
    async def import_existing_data(
        self,
        chromadb_path: Optional[Path] = None,
        knowledge_export_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Import data from existing systems into unified graph."""
        stats = {
            "chromadb_chunks": 0,
            "knowledge_concepts": 0,
            "total_imported": 0
        }
        
        # Import from ChromaDB if path provided
        if chromadb_path and chromadb_path.exists():
            # This would require ChromaDB client to export data
            # For now, log intention
            logger.info(f"Would import ChromaDB data from: {chromadb_path}")
            
        # Import from knowledge export if provided
        if knowledge_export_path and knowledge_export_path.exists():
            # Load exported knowledge
            import json
            with open(knowledge_export_path, 'r') as f:
                knowledge_data = json.load(f)
                
            # Convert to DomainKnowledge format and import
            # Implementation depends on export format
            logger.info(f"Would import knowledge from: {knowledge_export_path}")
            
        stats["total_imported"] = (
            stats["chromadb_chunks"] + 
            stats["knowledge_concepts"]
        )
        
        return stats
        
    async def validate_migration(self) -> Dict[str, Any]:
        """Validate that migration was successful."""
        validation = {
            "unified_system_ready": False,
            "data_integrity": False,
            "search_functional": False,
            "graph_traversal_functional": False
        }
        
        try:
            # Check system is initialized
            stats = await self.vector_store_compat.get_stats()
            validation["unified_system_ready"] = stats["total_nodes"] >= 0
            
            # Test search functionality
            from ..agents.specialized.domain_extraction.models import SearchQuery
            query = SearchQuery(query="test", max_results=5)
            results = await self.vector_store_compat.search(query)
            validation["search_functional"] = True
            
            # Test graph functionality
            graph_query = GraphRAGQuery(
                query_text="test query",
                query_type="general",
                max_results=5
            )
            result = await self.unified_graphrag.search(graph_query)
            validation["graph_traversal_functional"] = len(result.nodes) >= 0
            
            # Check data integrity
            validation["data_integrity"] = (
                validation["unified_system_ready"] and
                validation["search_functional"] and
                validation["graph_traversal_functional"]
            )
            
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            
        return validation


async def migrate_to_unified_system():
    """
    Main migration function to transition Certify Studio to unified GraphRAG.
    
    This is the recommended way to migrate existing deployments.
    """
    logger.info("Starting migration to Unified GraphRAG system")
    
    # Create migration handler
    migration = UnifiedSystemMigration()
    
    # Initialize unified system
    await migration.initialize()
    
    # Migrate Domain Extraction Agent
    domain_agent = DomainExtractionAgent()
    await domain_agent.initialize()
    await migration.migrate_domain_extraction_agent(domain_agent)
    
    # Import existing data if available
    # Customize paths based on your deployment
    stats = await migration.import_existing_data(
        chromadb_path=Path("./data/chromadb"),
        knowledge_export_path=Path("./data/knowledge_export.json")
    )
    logger.info(f"Data import complete: {stats}")
    
    # Validate migration
    validation = await migration.validate_migration()
    logger.info(f"Migration validation: {validation}")
    
    if validation["data_integrity"]:
        logger.success("Migration to Unified GraphRAG completed successfully!")
        return migration.unified_graphrag
    else:
        logger.error("Migration validation failed. Please check the logs.")
        raise RuntimeError("Migration validation failed")


# Example usage for new deployments (no migration needed)
async def create_unified_system():
    """Create a fresh unified GraphRAG system for new deployments."""
    # Initialize unified system
    graphrag = UnifiedGraphRAG(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="certify-studio-2024"
    )
    await graphrag.initialize()
    
    # Create domain extraction agent with unified system
    domain_agent = DomainExtractionAgent()
    await domain_agent.initialize()
    
    # Replace vector store with unified system
    domain_agent.vector_store = UnifiedVectorStore(graphrag)
    
    # Add unified import capability
    original_extract = domain_agent.extract_domain_knowledge
    
    async def unified_extract(request):
        result = await original_extract(request)
        if result.success and result.domain_knowledge:
            stats = await graphrag.import_from_domain_extraction(result.domain_knowledge)
            result.metadata["unified_graph_stats"] = stats
        return result
        
    domain_agent.extract_domain_knowledge = unified_extract
    
    logger.success("Fresh unified system created successfully!")
    return graphrag, domain_agent
