"""Integration tests for account management."""

import os
import tempfile
from unittest.mock import patch
import pytest

from taskra.config.manager import ConfigManager
from taskra.config.account import (
    list_accounts,
    get_current_account,
    add_account,
    remove_account,
    set_default_account
)


class TestAccountIntegration:
    """Test complete account management workflow."""
    
    @pytest.fixture
    def setup_config_manager(self):
        """Set up a temporary config manager for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a config manager that uses the temp directory
            manager = ConfigManager(config_dir=temp_dir)
            
            # Patch the global instance with our test instance
            with patch("taskra.config.account.config_manager", manager):
                yield manager
    
    @pytest.fixture
    def mock_validation(self):
        """Mock the validation of Jira credentials."""
        with patch("taskra.config.account.JiraClient"):
            # Create a mock UserService that always validates successfully
            mock_service = pytest.MockFixture.MagicMock()
            mock_service.validate_credentials.return_value = True
            
            with patch("taskra.config.account.UserService", return_value=mock_service):
                yield
    
    def test_account_management_workflow(self, setup_config_manager, mock_validation):
        """Test the entire account management workflow."""
        # 1. Initially there should be no accounts
        accounts = list_accounts()
        assert len(accounts) == 0
        
        # 2. Add first account
        success, _ = add_account("https://first.atlassian.net", "first@example.com", "token1")
        assert success
        
        # 3. Add second account
        success, _ = add_account("https://second.atlassian.net", "second@example.com", "token2")
        assert success
        
        # 4. List accounts and verify both exist
        accounts = list_accounts()
        assert len(accounts) == 2
        assert any(a["name"] == "first" for a in accounts)
        assert any(a["name"] == "second" for a in accounts)
        
        # 5. Check default account is the first one added
        account = get_current_account()
        assert account["name"] == "first"
        
        # 6. Change default account
        success, _ = set_default_account("second")
        assert success
        
        # 7. Verify default changed
        account = get_current_account()
        assert account["name"] == "second"
        
        # 8. Remove an account
        success, _ = remove_account("first")
        assert success
        
        # 9. Verify account was removed
        accounts = list_accounts()
        assert len(accounts) == 1
        assert accounts[0]["name"] == "second"
        
        # 10. Remove last account
        success, _ = remove_account("second")
        assert success
        
        # 11. Verify no accounts remain
        accounts = list_accounts()
        assert len(accounts) == 0
