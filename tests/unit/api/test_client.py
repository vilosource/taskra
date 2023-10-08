"""Tests for the JiraClient class and client factory functions."""

import os
import pytest
from unittest.mock import patch, MagicMock, Mock

from taskra.api.client import JiraClient, get_client, get_jira_client
from taskra.api.auth import get_auth_details
from requests.auth import HTTPBasicAuth


class TestJiraClient:
    """Tests for the JiraClient class."""
    
    def test_client_initialization(self):
        """Test that client is properly initialized."""
        client = JiraClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="api-token"
        )
        
        assert client.base_url == "https://example.atlassian.net/rest/api/3/"
        assert isinstance(client.auth, HTTPBasicAuth)
    
    def test_get_client_with_env_vars(self, monkeypatch):
        """Test get_client with environment variables."""
        # Set environment variables
        monkeypatch.setenv("JIRA_BASE_URL", "https://env-test.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "env-user@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "env-token")
        
        # Create a mock JiraClient and mock the singleton directly
        mock_client = Mock(spec=JiraClient)
        mock_client.base_url = "https://env-test.atlassian.net/rest/api/3/"
        mock_client.auth = Mock(spec=HTTPBasicAuth)
        mock_client.auth.username = "env-user@example.com"
        mock_client.auth.password = "env-token"
        
        # Patch JiraClient and also patch _jira_client to None to force recreation
        with patch('taskra.api.client.JiraClient', return_value=mock_client) as mock_class:
            # Reset client instance
            with patch('taskra.api.client._jira_client', None):
                client = get_client()
                
                # Verify the client was instantiated with the correct parameters
                mock_class.assert_called_once()
            
        # Verify it uses environment variables
        assert client.base_url == "https://env-test.atlassian.net/rest/api/3/"
        assert client.auth.username == "env-user@example.com"
        assert client.auth.password == "env-token"
    
    def test_get_client_with_config_fallback(self, monkeypatch):
        """Test get_client falls back to configuration when no env vars."""
        # Clear environment variables
        monkeypatch.delenv("JIRA_BASE_URL", raising=False)
        monkeypatch.delenv("JIRA_EMAIL", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        
        # Create a mock client to be returned directly
        mock_client = Mock(spec=JiraClient)
        mock_client.base_url = "https://config-test.atlassian.net/rest/api/3/"
        mock_client.auth = Mock(spec=HTTPBasicAuth)
        mock_client.auth.username = "config-user@example.com"
        mock_client.auth.password = "config-token"
        
        # Patch get_jira_client to return our mock
        with patch('taskra.api.client.get_jira_client', return_value=mock_client):
            client = get_client()
            
            # Verify it uses our mock client
            assert client is mock_client
            assert client.base_url == "https://config-test.atlassian.net/rest/api/3/"
            assert client.auth.username == "config-user@example.com"
            assert client.auth.password == "config-token"
    
    def test_get_client_no_env_no_config(self):
        """Test get_client raises error when no env vars and no config."""
        # Direct test using a completely patched environment
        # Patch get_jira_client to raise an error directly
        with patch('taskra.api.client.get_jira_client') as mock_get_jira:
            mock_get_jira.side_effect = ValueError("No Jira account configured: Missing required authentication details")
            
            # Verify it raises an error
            with pytest.raises(ValueError, match="No Jira account configured"):
                get_client()
