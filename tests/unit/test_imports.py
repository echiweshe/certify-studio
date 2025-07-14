"""
Test to diagnose import issues.
"""

import sys
import traceback


def test_database_models_import():
    """Test importing from database.models."""
    try:
        from certify_studio.database.models import (
            User, ContentGeneration, TaskStatus, QualityStatus
        )
        assert User is not None
        assert ContentGeneration is not None
        assert TaskStatus is not None
        assert QualityStatus is not None
        print("✓ Database models import successful")
    except ImportError as e:
        print(f"✗ Database models import failed: {e}")
        traceback.print_exc()
        raise


def test_repositories_import():
    """Test importing from repositories."""
    try:
        from certify_studio.database.repositories import (
            UserRepository, ContentGenerationRepository,
            DomainRepository, QualityRepository
        )
        assert UserRepository is not None
        assert ContentGenerationRepository is not None
        assert DomainRepository is not None
        assert QualityRepository is not None
        print("✓ Repositories import successful")
    except ImportError as e:
        print(f"✗ Repositories import failed: {e}")
        traceback.print_exc()
        raise


def test_integration_services_import():
    """Test importing from integration.services."""
    try:
        from certify_studio.integration.services import (
            ContentGenerationService, UserService
        )
        assert ContentGenerationService is not None
        assert UserService is not None
        print("✓ Integration services import successful")
    except ImportError as e:
        print(f"✗ Integration services import failed: {e}")
        traceback.print_exc()
        raise


def test_events_import():
    """Test importing from integration.events."""
    try:
        from certify_studio.integration.events import EventBus
        assert EventBus is not None
        print("✓ Events import successful")
    except ImportError as e:
        print(f"✗ Events import failed: {e}")
        traceback.print_exc()
        raise
