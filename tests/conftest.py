"""Common test fixtures for Taskra tests."""

import pytest
import tempfile
from unittest.mock import Mock

from taskra.config.manager import ConfigManager
from taskra.api.client import JiraClient


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for test configurations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def test_config_manager(temp_config_dir):
    """Create a ConfigManager instance using a temporary directory."""
    return ConfigManager(config_dir=temp_config_dir)


@pytest.fixture
def mock_jira_client():
    """Create a mock JiraClient for testing."""
    mock_client = Mock(spec=JiraClient)
    mock_client.get.return_value = {}
    mock_client.post.return_value = {}
    mock_client.put.return_value = {}
    mock_client.delete.return_value = {}
    return mock_client


@pytest.fixture
def sample_worklog_data():
    """Return sample worklog data for testing."""
    return [
        {
            "id": "12345",
            "timeSpent": "1h",
            "timeSpentSeconds": 3600,
            "author": {
                "displayName": "Test User",
                "accountId": "test-user-id"
            },
            "created": "2023-01-01T10:00:00.000+0000",
            "started": "2023-01-01T09:00:00.000+0000",
            "comment": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Test comment"
                            }
                        ]
                    }
                ]
            },
            "issue": {
                "id": "10001",
                "key": "TEST-123",
                "self": "https://example.atlassian.net/rest/api/3/issue/10001"
            }
        }
    ]
