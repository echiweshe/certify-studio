"""
Simple test to verify pytest is working
"""

import pytest


@pytest.mark.unit
def test_simple():
    """Basic test to verify pytest setup."""
    assert 1 + 1 == 2


@pytest.mark.unit 
def test_import():
    """Test basic imports work."""
    from certify_studio.database.models import User
    assert User is not None
