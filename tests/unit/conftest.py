import os
import tempfile
from unittest.mock import Mock, MagicMock
import pytest

from taskra.config.manager import ConfigManager
from taskra.api.client import JiraClient
from taskra.api.services.users import UserService

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
    return Mock(spec=JiraClient)

@pytest.fixture
def mock_user_service():
    """Create a mock UserService for testing."""
    mock_service = Mock(spec=UserService)
    mock_service.validate_credentials.return_value = True
    return mock_service

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up environment variables for testing."""
    with monkeypatch.context() as m:
        m.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
        m.setenv("JIRA_API_TOKEN", "dummy-token")
        m.setenv("JIRA_EMAIL", "test@example.com")
        yield
