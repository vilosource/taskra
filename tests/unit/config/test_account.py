"""Tests for account management functionality."""

import os
import pytest
from unittest.mock import patch, Mock

from taskra.config.account import (
    list_accounts,
    get_current_account,
    add_account,
    remove_account,
    set_default_account,
    get_subdomain_from_url
)


class TestAccountManagement:
    """Tests for the account management functionality."""
    
    def test_get_subdomain_from_url(self):
        """Test extracting subdomain from Jira URL."""
        # Test regular Atlassian cloud URL
        assert get_subdomain_from_url("https://mycompany.atlassian.net") == "mycompany"
        assert get_subdomain_from_url("http://test-team.atlassian.net") == "test-team"
        
        # Test URL with path
        assert get_subdomain_from_url("https://mycompany.atlassian.net/jira") == "mycompany"
        
        # Test non-Atlassian URL
        assert get_subdomain_from_url("https://example.com") == "example.com"
    
    def test_list_accounts_empty(self, monkeypatch):
        """Test listing accounts when none exist."""
        # Mock config_manager.read_config to return empty accounts
        monkeypatch.setattr("taskra.config.account.config_manager.read_config", 
                        lambda: {"accounts": {}, "default_account": None})
        
        accounts = list_accounts()
        assert len(accounts) == 0

    def test_list_accounts_with_default(self, monkeypatch):
        """Test listing accounts with a default account."""
        # Mock config with accounts including a default
        mock_config = {
            "accounts": {
                "account1": {"url": "https://a1.atlassian.net", "email": "a1@example.com"},
                "account2": {"url": "https://a2.atlassian.net", "email": "a2@example.com"}
            },
            "default_account": "account1"
        }
        monkeypatch.setattr("taskra.config.account.config_manager.read_config", lambda: mock_config)
        
        accounts = list_accounts()
        assert len(accounts) == 2
        # Find the default account
        default_account = next(a for a in accounts if a["is_default"])
        assert default_account["name"] == "account1"
        
        # Check the non-default account
        non_default = next(a for a in accounts if not a["is_default"])
        assert non_default["name"] == "account2"
    
    def test_get_current_account_default(self, monkeypatch):
        """Test getting the default account."""
        # Mock config with default account
        mock_config = {
            "accounts": {
                "account1": {"url": "https://a1.atlassian.net", "email": "a1@example.com"},
                "account2": {"url": "https://a2.atlassian.net", "email": "a2@example.com"}
            },
            "default_account": "account1"
        }
        monkeypatch.setattr("taskra.config.account.config_manager.read_config", lambda: mock_config)
        monkeypatch.delenv("TASKRA_ACCOUNT", raising=False)  # Ensure env var is not set
        
        account = get_current_account()
        assert account["name"] == "account1"
        assert account["url"] == "https://a1.atlassian.net"

    def test_get_current_account_env_override(self, monkeypatch):
        """Test getting account from environment variable override."""
        # Mock config with default account
        mock_config = {
            "accounts": {
                "account1": {"url": "https://a1.atlassian.net", "email": "a1@example.com"},
                "account2": {"url": "https://a2.atlassian.net", "email": "a2@example.com"}
            },
            "default_account": "account1"
        }
        monkeypatch.setattr("taskra.config.account.config_manager.read_config", lambda: mock_config)
        monkeypatch.setenv("TASKRA_ACCOUNT", "account2")
        
        account = get_current_account()
        assert account["name"] == "account2"  # Should use account2 from env var

    def test_get_current_account_none(self, monkeypatch):
        """Test getting current account when none is configured."""
        mock_config = {
            "accounts": {},
            "default_account": None
        }
        monkeypatch.setattr("taskra.config.account.config_manager.read_config", lambda: mock_config)
        monkeypatch.delenv("TASKRA_ACCOUNT", raising=False)
        
        account = get_current_account()
        assert account is None

    def test_add_first_account(self, monkeypatch, mock_user_service):
        """Test adding the first account (should become default)."""
        # Mock empty config
        monkeypatch.setattr("taskra.config.account.config_manager.read_config", 
                        lambda: {"accounts": {}, "default_account": None})
        
        # Mock update_config to capture the update function
        updated_config = {}
        def mock_update_config(update_func):
            nonlocal updated_config
            updated_config = update_func({"accounts": {}, "default_account": None})
            return updated_config
        monkeypatch.setattr("taskra.config.account.config_manager.update_config", mock_update_config)
        
        # Mock JiraClient and UserService
        monkeypatch.setattr("taskra.config.account.JiraClient", lambda *args, **kwargs: None)
        monkeypatch.setattr("taskra.config.account.UserService", lambda *args: mock_user_service)
        
        success, _ = add_account("https://test.atlassian.net", "test@example.com", "api-token")
        
        assert success
        assert "test" in updated_config["accounts"]
        assert updated_config["default_account"] == "test"
        assert updated_config["accounts"]["test"]["url"] == "https://test.atlassian.net"
        assert updated_config["accounts"]["test"]["email"] == "test@example.com"

    def test_add_account_custom_name(self, monkeypatch, mock_user_service):
        """Test adding an account with a custom name."""
        # Mock config
        monkeypatch.setattr("taskra.config.account.config_manager.read_config", 
                        lambda: {"accounts": {}, "default_account": None})
        
        # Mock update_config
        updated_config = {}
        def mock_update_config(update_func):
            nonlocal updated_config
            updated_config = update_func({"accounts": {}, "default_account": None})
            return updated_config
        monkeypatch.setattr("taskra.config.account.config_manager.update_config", mock_update_config)
        
        # Mock JiraClient and UserService
        monkeypatch.setattr("taskra.config.account.JiraClient", lambda *args, **kwargs: None)
        monkeypatch.setattr("taskra.config.account.UserService", lambda *args: mock_user_service)
        
        success, _ = add_account("https://test.atlassian.net", "test@example.com", "api-token", name="custom")
        
        assert success
        assert "custom" in updated_config["accounts"]
        assert updated_config["default_account"] == "custom"

    def test_add_account_validation_failure(self, monkeypatch):
        """Test adding an account with invalid credentials."""
        # Mock UserService to fail validation
        mock_service = Mock()
        mock_service.validate_credentials.return_value = False
        monkeypatch.setattr("taskra.config.account.UserService", lambda *args: mock_service)
        
        # Try to add an account with invalid credentials
        success, message = add_account("https://test.atlassian.net", "test@example.com", "bad-token")
        
        assert not success
        assert "Invalid credentials" in message

    def test_remove_account_standard(self, monkeypatch):
        """Test removing a non-default account."""
        # Mock config with multiple accounts
        mock_config = {
            "accounts": {
                "account1": {"url": "https://a1.atlassian.net"},
                "account2": {"url": "https://a2.atlassian.net"}
            },
            "default_account": "account1"
        }
        
        # Capture the updated configuration
        updated_config = {}
        def mock_update_config(update_func):
            nonlocal updated_config
            updated_config = update_func(mock_config)
            return updated_config
        
        monkeypatch.setattr("taskra.config.account.config_manager.update_config", mock_update_config)
        
        remove_account("account2")
        
        assert "account2" not in updated_config["accounts"]
        assert "account1" in updated_config["accounts"]
        assert updated_config["default_account"] == "account1"  # Unchanged

    def test_remove_default_account(self, monkeypatch):
        """Test removing the default account."""
        # Mock config with multiple accounts
        mock_config = {
            "accounts": {
                "account1": {"url": "https://a1.atlassian.net"},
                "account2": {"url": "https://a2.atlassian.net"}
            },
            "default_account": "account1"
        }
        
        # Capture the updated configuration
        updated_config = {}
        def mock_update_config(update_func):
            nonlocal updated_config
            updated_config = update_func(mock_config)
            return updated_config
        
        monkeypatch.setattr("taskra.config.account.config_manager.update_config", mock_update_config)
        
        remove_account("account1")
        
        assert "account1" not in updated_config["accounts"]
        assert "account2" in updated_config["accounts"]
        assert updated_config["default_account"] == "account2"  # Should change to the other account

    def test_remove_last_account(self, monkeypatch):
        """Test removing the last remaining account."""
        # Mock config with single account
        mock_config = {
            "accounts": {
                "account1": {"url": "https://a1.atlassian.net"}
            },
            "default_account": "account1"
        }
        
        # Capture the updated configuration
        updated_config = {}
        def mock_update_config(update_func):
            nonlocal updated_config
            updated_config = update_func(mock_config)
            return updated_config
        
        monkeypatch.setattr("taskra.config.account.config_manager.update_config", mock_update_config)
        
        remove_account("account1")
        
        assert "account1" not in updated_config["accounts"]
        assert len(updated_config["accounts"]) == 0
        assert updated_config["default_account"] is None  # Should be None when no accounts remain

    def test_set_default_account(self, monkeypatch):
        """Test setting the default account."""
        # Mock config with multiple accounts
        mock_config = {
            "accounts": {
                "account1": {"url": "https://a1.atlassian.net"},
                "account2": {"url": "https://a2.atlassian.net"}
            },
            "default_account": "account1"
        }
        
        monkeypatch.setattr("taskra.config.account.config_manager.read_config", lambda: mock_config)
        
        # Capture the updated configuration
        updated_config = {}
        def mock_update_config(update_func):
            nonlocal updated_config
            updated_config = update_func(mock_config)
            return updated_config
        
        monkeypatch.setattr("taskra.config.account.config_manager.update_config", mock_update_config)
        
        success, _ = set_default_account("account2")
        
        assert success
        assert updated_config["default_account"] == "account2"

    def test_set_default_nonexistent_account(self, monkeypatch):
        """Test setting a non-existent account as default."""
        # Mock config
        mock_config = {
            "accounts": {
                "account1": {"url": "https://a1.atlassian.net"}
            },
            "default_account": "account1"
        }
        
        monkeypatch.setattr("taskra.config.account.config_manager.read_config", lambda: mock_config)
        
        success, message = set_default_account("nonexistent")
        
        assert not success
        assert "does not exist" in message
