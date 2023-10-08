"""Test configuration and fixtures."""

import pytest
import logging

# Import timeout mechanism to ensure it's loaded for all tests
from tests.models.test_debug_timeout import apply_timeout_to_all_tests

# Log the fact that timeout protection is enabled
logging.info("Test timeout protection enabled")

# This is a test runner hook that marks all tests with the timeout marker
def pytest_collection_modifyitems(items):
    """Add timeout marker to all tests."""
    for item in items:
        if not item.get_closest_marker("timeout"):
            item.add_marker(pytest.mark.timeout(seconds=30))
