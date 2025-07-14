"""
Import diagnostic script for Certify Studio.

This script helps identify import issues systematically.
"""

import sys
import traceback
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def test_import(module_path: str, item: str = None):
    """Test importing a module or specific item."""
    try:
        if item:
            exec(f"from {module_path} import {item}")
            print(f"✓ Successfully imported {item} from {module_path}")
        else:
            exec(f"import {module_path}")
            print(f"✓ Successfully imported {module_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to import {module_path}{f'.{item}' if item else ''}")
        print(f"  Error: {type(e).__name__}: {str(e)}")
        if "--verbose" in sys.argv:
            traceback.print_exc()
        return False

def main():
    """Run import diagnostics."""
    print("Certify Studio Import Diagnostics")
    print("=" * 50)
    print()
    
    # Test basic imports
    print("Testing basic imports...")
    test_import("certify_studio")
    test_import("certify_studio.config")
    test_import("certify_studio.core.config")
    test_import("certify_studio.core.logging")
    print()
    
    # Test database imports
    print("Testing database imports...")
    test_import("certify_studio.database")
    test_import("certify_studio.database.models")
    test_import("certify_studio.database.repositories")
    print()
    
    # Test specific repository imports
    print("Testing repository imports...")
    repositories = [
        "BaseRepository",
        "UserRepository",
        "ContentGenerationRepository",
        "ContentPieceRepository",
        "MediaAssetRepository",
        "ExportTaskRepository",
        "DomainRepository",
        "QualityRepository",
        "AnalyticsRepository"
    ]
    
    for repo in repositories:
        test_import("certify_studio.database.repositories", repo)
    print()
    
    # Test integration imports
    print("Testing integration imports...")
    test_import("certify_studio.integration")
    test_import("certify_studio.integration.dependencies")
    test_import("certify_studio.integration.services")
    test_import("certify_studio.integration.events")
    print()
    
    # Test agent imports
    print("Testing agent imports...")
    test_import("certify_studio.agents")
    test_import("certify_studio.agents.core")
    test_import("certify_studio.agents.orchestrator")
    print()
    
    # Test API imports
    print("Testing API imports...")
    test_import("certify_studio.api")
    test_import("certify_studio.api.main")
    test_import("certify_studio.api.routers")
    print()
    
    print("=" * 50)
    print("Import diagnostics completed.")

if __name__ == "__main__":
    main()
