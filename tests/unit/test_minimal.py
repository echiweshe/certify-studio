"""
Minimal test to check if basic imports are working without conftest.
"""


def test_basic_math():
    """Test that doesn't require any imports."""
    assert 2 + 2 == 4
    assert 10 * 5 == 50
    assert "hello" + " world" == "hello world"


def test_basic_python():
    """Test basic Python functionality."""
    my_list = [1, 2, 3, 4, 5]
    assert len(my_list) == 5
    assert sum(my_list) == 15
    
    my_dict = {"a": 1, "b": 2}
    assert my_dict["a"] == 1
    assert "b" in my_dict
