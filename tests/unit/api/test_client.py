"""Tests for the JiraClient class and client factory functions."""

import os
import pytest
from unittest.mock import patch, MagicMock

from taskra.api.client import JiraClient, get_client
from taskra.api.auth import get_auth_details  # Import auth function instead


class TestJiraClient:
    """Tests for the JiraClient class."""
    
    def test_client_initialization(self):
        """Test that client is properly initialized."""
        client = JiraClient(
            base_url="https://example.atlassian.net",
            auth={"email": "test@example.com", "token": "api-token"}
        )
        
        assert client.base_url == "https://example.atlassian.net/rest/api/3/"
        assert client.auth == {"email": "test@example.com", "token": "api-token"}
    
    def test_get_client_with_env_vars(self, monkeypatch):
        """Test get_client with environment variables."""
        # Set environment variables
        monkeypatch.setenv("JIRA_BASE_URL", "https://env-test.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "env-user@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "env-token")
        
        # Mock get_auth_details to use environment variables
        def mock_get_auth():
            return {
                'base_url': os.environ.get('JIRA_BASE_URL'),
                'email': os.environ.get('JIRA_EMAIL'),
                'token': os.environ.get('JIRA_API_TOKEN')
            }
        
        monkeypatch.setattr("taskra.api.client.get_auth_details", mock_get_auth)
        
        # Call get_client
        client = get_client()
        
        # Verify it uses environment variables
        assert client.base_url == "https://env-test.atlassian.net/rest/api/3/"
        assert client.auth == {
            "email": "env-user@example.com", 
            "token": "env-token"
        }
    
    def test_get_client_with_config_fallback(self, monkeypatch):
        """Test get_client falls back to configuration when no env vars."""
        # Clear environment variables
        monkeypatch.delenv("JIRA_BASE_URL", raising=False)
        monkeypatch.delenv("JIRA_EMAIL", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        
        # Mock get_auth_details to return test account info
        def mock_get_auth():
            return {
                'base_url': "https://config-test.atlassian.net",
                'email': "config-user@example.com",
                'token': "config-token"
            }
        
        monkeypatch.setattr("taskra.api.client.get_auth_details", mock_get_auth)
        
        # Call get_client
        client = get_client()
        
        # Verify it uses account configuration
        assert client.base_url == "https://config-test.atlassian.net/rest/api/3/"
        assert client.auth == {
            "email": "config-user@example.com", 
            "token": "config-token"
        }
    
    def test_get_client_no_env_no_config(self, monkeypatch):
        """Test get_client raises error when no env vars and no config."""
        # Clear environment variables
        monkeypatch.delenv("JIRA_BASE_URL", raising=False)
        monkeypatch.delenv("JIRA_EMAIL", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        
        # Mock get_auth_details to raise an error
        def mock_get_auth():
            raise ValueError("No Jira account configured.")
        
        monkeypatch.setattr("taskra.api.client.get_auth_details", mock_get_auth)
        
        # Verify it raises an error
        with pytest.raises(ValueError):
            get_client()
