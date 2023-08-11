"""Fixtures for integration tests."""

import os
import pytest
from vcr import VCR

# Configure VCR to handle Jira API recordings
vcr = VCR(
    cassette_library_dir='tests/fixtures/cassettes',
    filter_headers=['Authorization'],
    record_mode='once'
)

@pytest.fixture
def vcr_config():
    """VCR configuration."""
    return {
        'filter_headers': ['Authorization'],
        'record_mode': 'once',
    }

@pytest.fixture
def test_issue_key():
    """Returns a test issue key from environment or a default."""
    return os.environ.get('TEST_ISSUE_KEY', 'TEST-1')

@pytest.fixture
def test_project_key():
    """Returns a test project key from environment or a default."""
    return os.environ.get('TEST_PROJECT_KEY', 'TEST')
