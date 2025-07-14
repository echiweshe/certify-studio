"""
Standalone setup script for Certify Studio.
Run this to set up the project environment.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


async def setup_neo4j():
    """Setup Neo4j database with required indexes and constraints."""
    try:
        from neo4j import AsyncGraphDatabase
        
        # Neo4j connection details
        uri = "bolt://localhost:7687"
        auth = ("neo4j", "password")  # Change this!
        
        print("Connecting to Neo4j...")
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
                    print(f"✓ Executed: {query.split()[2]} {query.split()[3]}")
                except Exception as e:
                    print(f"⚠ Query failed (may already exist): {e}")
        
        await driver.close()
        print("✓ Neo4j setup completed!")
        
    except ImportError:
        print("❌ neo4j package not installed. Run: uv pip install neo4j")
        print("   Skipping Neo4j setup...")
    except Exception as e:
        print(f"⚠ Neo4j setup failed: {e}")
        print("  Make sure Neo4j is running on localhost:7687")
        print("  You can set it up later.")


def create_directories():
    """Create required directories."""
    base_dir = Path(__file__).parent.parent.parent.parent  # Project root
    
    dirs = [
        "uploads",
        "exports",
        "exports/videos",
        "temp",
        "logs",
        "data/vector_store",
        "data/knowledge_base"
    ]
    
    print("\nCreating directories...")
    for dir_path in dirs:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {dir_path}")


def check_dependencies():
    """Check if required dependencies are installed."""
    print("\nChecking dependencies...")
    
    required = {
        "fastapi": "FastAPI web framework",
        "uvicorn": "ASGI server",
        "pydantic": "Data validation",
        "sqlalchemy": "Database ORM",
        "redis": "Caching/Queue",
        "openai": "OpenAI API",
        "neo4j": "Graph database",
    }
    
    missing = []
    for package, description in required.items():
        try:
            __import__(package)
            print(f"✓ {package}: {description}")
        except ImportError:
            print(f"❌ {package}: {description} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n⚠ Missing packages: {', '.join(missing)}")
        print("Install with: uv pip install " + " ".join(missing))
        return False
    return True


def create_env_file():
    """Create .env file if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        print("\n✓ Created .env file from .env.example")
        print("⚠ Please update .env with your actual values (API keys, etc.)")
    elif env_file.exists():
        print("\n✓ .env file already exists")
    else:
        print("\n⚠ No .env.example found, skipping .env creation")


async def main():
    """Run all setup tasks."""
    print("🚀 Setting up Certify Studio...")
    print("=" * 50)
    
    # Check dependencies first
    deps_ok = check_dependencies()
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Setup Neo4j if available
    if deps_ok:
        print("\n📊 Setting up Neo4j...")
        await setup_neo4j()
    
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    
    if not deps_ok:
        print("\n⚠ Some dependencies are missing. Install them first:")
        print("  uv pip install -e .")
    
    print("\nNext steps:")
    print("1. Install any missing dependencies")
    print("2. Update .env file with your API keys")
    print("3. Make sure Neo4j is running (optional for initial testing)")
    print("4. Run: uvicorn certify_studio.api.main:app --reload")
    print("\nAPI will be available at: http://localhost:8000/api/docs")


if __name__ == "__main__":
    # Run async main
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
