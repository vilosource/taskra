"""Fixtures for integration tests."""

import os
import pytest
from vcr import VCR

# Import the patch to fix VCR compatibility issue
from .vcr_patches import patch_vcr_response

# Configure VCR to handle Jira API recordings
vcr = VCR(
    cassette_library_dir='tests/fixtures/cassettes',
    filter_headers=['Authorization'],
    record_mode='once'
)

# Apply VCR patch at module initialization
patch_vcr_response()

@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        'filter_headers': ['Authorization'],
        'record_mode': 'once',
    }

@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing."""
    with pytest.MonkeyPatch().context() as m:
        m.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
        m.setenv("JIRA_API_TOKEN", "dummy-token")
        m.setenv("JIRA_EMAIL", "test@example.com")
        yield

@pytest.fixture
def test_issue_key():
    """Returns a test issue key from environment or a default."""
    return os.environ.get('TEST_ISSUE_KEY', 'TEST-1')

@pytest.fixture
def test_project_key():
    """Returns a test project key from environment or a default."""
    return os.environ.get('TEST_PROJECT_KEY', 'TEST')
