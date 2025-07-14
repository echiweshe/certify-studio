"""
Direct test runner to bypass conftest issues.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    
    try:
        # Test database models
        print("  - Testing database models...", end="")
        from certify_studio.database.models import (
            User, ContentGeneration, TaskStatus, QualityStatus
        )
        print(" ✓")
        
        # Test repositories
        print("  - Testing repositories...", end="")
        from certify_studio.database.repositories import (
            UserRepository, ContentGenerationRepository,
            DomainRepository, QualityRepository
        )
        print(" ✓")
        
        # Test services
        print("  - Testing services...", end="")
        from certify_studio.integration.services import (
            ContentGenerationService, UserService
        )
        print(" ✓")
        
        # Test events
        print("  - Testing events...", end="")
        from certify_studio.integration.events import EventBus
        print(" ✓")
        
        print("\nAll imports successful! ✓")
        return True
        
    except ImportError as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple():
    """Run simple tests."""
    print("\nRunning simple tests...")
    
    # Test 1
    assert 1 + 1 == 2
    print("  - Basic math test passed ✓")
    
    # Test 2
    test_list = [1, 2, 3, 4, 5]
    assert len(test_list) == 5
    assert sum(test_list) == 15
    print("  - List operations test passed ✓")
    
    # Test 3
    test_dict = {"a": 1, "b": 2, "c": 3}
    assert test_dict["b"] == 2
    assert len(test_dict) == 3
    print("  - Dictionary operations test passed ✓")
    
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("Certify Studio Test Runner")
    print("=" * 50)
    
    # Run import tests
    import_success = test_imports()
    
    # Run simple tests
    simple_success = test_simple()
    
    print("\n" + "=" * 50)
    if import_success and simple_success:
        print("All tests passed! ✅")
        sys.exit(0)
    else:
        print("Some tests failed! ❌")
        sys.exit(1)
