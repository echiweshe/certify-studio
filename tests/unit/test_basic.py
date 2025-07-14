"""
Very simple test to verify pytest is working without database imports
"""

import pytest


@pytest.mark.unit
def test_basic_math():
    """Basic test that doesn't import anything from our code."""
    assert 1 + 1 == 2
    assert 2 * 3 == 6


@pytest.mark.unit 
def test_basic_string():
    """Another basic test."""
    assert "hello" + " world" == "hello world"
    assert len("test") == 4
