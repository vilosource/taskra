"""Tests for User models and serialization."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from taskra.api.models.user import User
from taskra.utils.model_adapters import adapt_user_for_presentation
from taskra.api.services.users import UserService

class TestUserModels:
    """Test User models."""
    
    def test_user_serialization(self):
        """Test serializing User models."""
        # Create a user model - use self_url instead of self
        user = User(
            self_url="https://example.atlassian.net/rest/api/3/user?accountId=user123",
            accountId="user123",
            displayName="Test User",
            emailAddress="test@example.com",
            active=True,
            timeZone="UTC"
        )
        
        # Serialize to dictionary
        result = user.model_dump_api()
        
        # Verify serialization - the API will still see "self" in the output
        assert isinstance(result, dict)
        assert "self" in result  # The alias is applied in serialization
        assert result["accountId"] == "user123"
        assert result["displayName"] == "Test User"
        assert result["emailAddress"] == "test@example.com"
        
    def test_user_adapter(self):
        """Test User adapter functions."""
        # Create a user dictionary (simulating old code)
        user_dict = {
            "self": "https://example.atlassian.net/rest/api/3/user?accountId=user123",
            "account_id": "user123",
            "display_name": "Test User", 
            "email_address": "test@example.com"
        }
        
        # Adapt for presentation
        result = adapt_user_for_presentation(user_dict)
        
        # Verify adaptation
        assert "accountId" in result
        assert result["accountId"] == "user123"
        assert "displayName" in result
        assert result["displayName"] == "Test User"
