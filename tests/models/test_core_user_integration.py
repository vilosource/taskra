"""Tests for User model integration with the core layer."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from taskra.api.models.user import User, CurrentUser
from taskra.core.users import get_current_user, find_users

class TestCoreUserIntegration:
    """Test the integration between User models and core layer functions."""
    
    @patch('taskra.core.users.UserService')
    @patch('taskra.core.users.get_client')
    def test_get_current_user_with_models(self, mock_get_client, mock_service_class):
        """Test get_current_user with model return values."""
        # Setup
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Create a model instance that the service will return
        user_model = CurrentUser(
            self_url="https://example.com/rest/api/3/user?accountId=user123",
            accountId="user123",
            displayName="Test User",
            emailAddress="test@example.com",
            active=True,
            timeZone="UTC"
        )
        mock_service.get_current_user.return_value = user_model
        
        # Execute
        result = get_current_user(refresh_cache=True)
        
        # Verify
        mock_get_client.assert_called_once()
        mock_service_class.assert_called_once_with(mock_client)
        mock_service.get_current_user.assert_called_once()
        
        # The result should be a dictionary with the correct values
        assert isinstance(result, dict)
        assert result["accountId"] == "user123"
        assert result["displayName"] == "Test User"
        assert "self" in result  # Ensure API URL is preserved
        
    @patch('taskra.core.users.UserService')
    @patch('taskra.core.users.get_client')
    def test_find_users_with_models(self, mock_get_client, mock_service_class):
        """Test find_users with model return values."""
        # Setup
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Create a list of model instances that the service will return
        user_models = [
            User(
                self_url=f"https://example.com/rest/api/3/user?accountId=user{i}",
                accountId=f"user{i}",
                displayName=f"Test User {i}",
                emailAddress=f"user{i}@example.com",
                active=True,
                timeZone="UTC"
            )
            for i in range(3)
        ]
        mock_service.find_users.return_value = user_models
        
        # Execute
        result = find_users("test", refresh_cache=True)
        
        # Verify
        mock_get_client.assert_called_once()
        mock_service_class.assert_called_once_with(mock_client)
        mock_service.find_users.assert_called_once()
        
        # The result should be a list of dictionaries with the correct values
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(item, dict) for item in result)
        assert result[0]["accountId"] == "user0"
        assert result[1]["displayName"] == "Test User 1"
        assert "self" in result[2]  # Ensure API URL is preserved
