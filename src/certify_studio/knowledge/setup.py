"""
Setup script for Certify Studio knowledge system.
This can be run with: python -m certify_studio.knowledge.setup
"""

import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def setup_neo4j():
    """Setup Neo4j database with required indexes and constraints."""
    try:
        from neo4j import AsyncGraphDatabase
        
        # Neo4j connection details
        uri = "bolt://localhost:7687"
        auth = ("neo4j", "password")  # Change this!
        
        driver = AsyncGraphDatabase.driver(uri, auth=auth)
        
        async with driver.session() as session:
            # Create indexes
            queries = [
                # Vector indexes for GraphRAG
                """
                CREATE VECTOR INDEX concept_embedding IF NOT EXISTS
                FOR (n:Concept)
                ON (n.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                }}
                """,
                """
                CREATE VECTOR INDEX issue_embedding IF NOT EXISTS
                FOR (n:Issue)
                ON (n.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                }}
                """,
                # Regular indexes
                "CREATE INDEX concept_name IF NOT EXISTS FOR (n:Concept) ON (n.name)",
                "CREATE INDEX concept_type IF NOT EXISTS FOR (n:Concept) ON (n.type)",
                "CREATE INDEX issue_type IF NOT EXISTS FOR (n:Issue) ON (n.type)",
                "CREATE INDEX solution_type IF NOT EXISTS FOR (n:Solution) ON (n.type)",
                # Constraints
                "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (n:Concept) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT issue_id IF NOT EXISTS FOR (n:Issue) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT solution_id IF NOT EXISTS FOR (n:Solution) REQUIRE n.id IS UNIQUE"
            ]
            
            for query in queries:
                try:
                    await session.run(query)
                    logger.info(f"Executed: {query.split()[2]} {query.split()[3]}")
                except Exception as e:
                    logger.warning(f"Query failed (may already exist): {e}")
        
        await driver.close()
        logger.info("Neo4j setup completed!")
        
    except ImportError:
        logger.error("neo4j package not installed. Run: pip install neo4j")
    except Exception as e:
        logger.error(f"Neo4j setup failed: {e}")
        logger.info("Make sure Neo4j is running on localhost:7687")


async def create_directories():
    """Create required directories."""
    dirs = [
        "uploads",
        "exports",
        "exports/videos",
        "temp",
        "logs",
        "data/vector_store",
        "data/knowledge_base"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")


async def setup_unified_system():
    """Setup the unified knowledge system."""
    logger.info("Setting up unified knowledge system...")
    
    # Create directories
    await create_directories()
    
    # Setup Neo4j if available
    try:
        await setup_neo4j()
    except Exception as e:
        logger.warning(f"Neo4j setup skipped: {e}")
        logger.info("The system will work without Neo4j, using in-memory storage")
    
    logger.info("Unified system setup complete")
    return True


async def main():
    """Run all setup tasks."""
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Setting up Certify Studio...")
    
    # Create directories
    await create_directories()
    
    # Setup Neo4j
    print("\n📊 Setting up Neo4j...")
    await setup_neo4j()
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Make sure Neo4j is running")
    print("2. Update Neo4j credentials in your .env file")
    print("3. Run: uvicorn certify_studio.api.main:app --reload")


if __name__ == "__main__":
    asyncio.run(main())
