"""
Placeholder performance test file.
This file will be removed once real performance tests are added.
"""

import pytest


@pytest.mark.performance
def test_performance_placeholder(benchmark):
    """Placeholder test to verify performance test marker works."""
    def dummy_function():
        return sum(range(100))
    
    result = benchmark(dummy_function)
    assert result == 4950

