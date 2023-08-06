"""Unit tests for CLI commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from taskra.cmd.main import cli


class TestCliCommands:
    """Tests for Taskra CLI commands."""
    
    @pytest.fixture
    def runner(self):
        """Set up CLI test runner."""
        return CliRunner()

    def test_main_cli_displays_help(self, runner):
        """Test that CLI displays help information."""
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "Task and project management" in result.output
        assert "projects" in result.output
        assert "issue" in result.output
        assert "config" in result.output

    def test_projects_command(self, runner):
        """Test projects command calls the list_projects function."""
        with patch("taskra.cmd.main.list_projects") as mock_list_projects:
            mock_list_projects.return_value = [
                {"key": "TEST", "name": "Test Project"}
            ]
            
            result = runner.invoke(cli, ["projects"])
            
            assert result.exit_code == 0
            assert "Available Projects" in result.output
            mock_list_projects.assert_called_once()

    def test_issue_command(self, runner):
        """Test issue command calls the get_issue function."""
        with patch("taskra.cmd.main.get_issue") as mock_get_issue:
            mock_get_issue.return_value = {
                "key": "TEST-123",
                "fields": {"summary": "Test issue"}
            }
            
            result = runner.invoke(cli, ["issue", "TEST-123"])
            
            assert result.exit_code == 0
            assert "Issue details for TEST-123" in result.output
            mock_get_issue.assert_called_once_with("TEST-123")

    def test_config_list_command_with_accounts(self, runner):
        """Test config list command when accounts exist."""
        mock_accounts = [
            {"name": "test", "url": "https://test.atlassian.net", 
             "email": "test@example.com", "is_default": True},
            {"name": "dev", "url": "https://dev.atlassian.net", 
             "email": "dev@example.com", "is_default": False}
        ]
        
        with patch("taskra.config.account.list_accounts", return_value=mock_accounts):
            result = runner.invoke(cli, ["config", "list"])
            
            assert result.exit_code == 0
            assert "Configured Accounts" in result.output
            assert "test" in result.output
            assert "dev" in result.output
            assert "https://test.atlassian.net" in result.output
            assert "https://dev.atlassian.net" in result.output

    def test_config_list_command_without_accounts(self, runner):
        """Test config list command when no accounts exist."""
        with patch("taskra.config.account.list_accounts", return_value=[]):
            result = runner.invoke(cli, ["config", "list"])
            
            assert result.exit_code == 0
            assert "No accounts configured" in result.output

    def test_config_add_command(self, runner):
        """Test config add command."""
        with patch("taskra.config.account.add_account") as mock_add_account:
            mock_add_account.return_value = (True, "Account 'test' added successfully")
            
            result = runner.invoke(cli, ["config", "add", 
                                        "--url", "https://test.atlassian.net",
                                        "--email", "test@example.com",
                                        "--token", "secret-token"])
            
            assert result.exit_code == 0
            assert "Account 'test' added successfully" in result.output
            mock_add_account.assert_called_once_with(
                "https://test.atlassian.net", "test@example.com", "secret-token", None
            )

    def test_config_add_command_with_name(self, runner):
        """Test config add command with custom name."""
        with patch("taskra.config.account.add_account") as mock_add_account:
            mock_add_account.return_value = (True, "Account 'custom' added successfully")
            
            result = runner.invoke(cli, ["config", "add", 
                                        "--name", "custom",
                                        "--url", "https://test.atlassian.net",
                                        "--email", "test@example.com",
                                        "--token", "secret-token"])
            
            assert result.exit_code == 0
            assert "Account 'custom' added successfully" in result.output
            mock_add_account.assert_called_once_with(
                "https://test.atlassian.net", "test@example.com", "secret-token", "custom"
            )

    def test_config_remove_command_confirmed(self, runner):
        """Test config remove command with confirmation."""
        with patch("taskra.config.account.remove_account") as mock_remove_account:
            mock_remove_account.return_value = (True, "Account 'test' removed successfully")
            
            # Simulate user confirming with 'y'
            result = runner.invoke(cli, ["config", "remove", "test"], input="y\n")
            
            assert result.exit_code == 0
            assert "Account 'test' removed successfully" in result.output
            mock_remove_account.assert_called_once_with("test")

    def test_config_remove_command_cancelled(self, runner):
        """Test config remove command when user cancels."""
        with patch("taskra.config.account.remove_account") as mock_remove_account:
            # Simulate user cancelling with 'n'
            result = runner.invoke(cli, ["config", "remove", "test"], input="n\n")
            
            assert result.exit_code == 0
            assert "Operation cancelled" in result.output
            mock_remove_account.assert_not_called()

    def test_config_remove_command_force(self, runner):
        """Test config remove command with force flag."""
        with patch("taskra.config.account.remove_account") as mock_remove_account:
            mock_remove_account.return_value = (True, "Account 'test' removed successfully")
            
            # Use --force to skip confirmation
            result = runner.invoke(cli, ["config", "remove", "test", "--force"])
            
            assert result.exit_code == 0
            assert "Account 'test' removed successfully" in result.output
            mock_remove_account.assert_called_once_with("test")

    def test_config_default_command(self, runner):
        """Test setting default account."""
        with patch("taskra.config.account.set_default_account") as mock_set_default:
            mock_set_default.return_value = (True, "Default account set to 'test'")
            
            result = runner.invoke(cli, ["config", "default", "test"])
            
            assert result.exit_code == 0
            assert "Default account set to 'test'" in result.output
            mock_set_default.assert_called_once_with("test")

    def test_config_default_command_error(self, runner):
        """Test setting invalid default account."""
        with patch("taskra.config.account.set_default_account") as mock_set_default:
            mock_set_default.return_value = (False, "Account 'invalid' does not exist")
            
            result = runner.invoke(cli, ["config", "default", "invalid"])
            
            assert result.exit_code == 0  # CLI still exits successfully
            assert "Account 'invalid' does not exist" in result.output
            mock_set_default.assert_called_once_with("invalid")

    def test_config_current_command_with_account(self, runner):
        """Test showing current account when one exists."""
        mock_account = {
            "name": "test",
            "url": "https://test.atlassian.net",
            "email": "test@example.com"
        }
        
        with patch("taskra.config.account.get_current_account", return_value=mock_account):
            result = runner.invoke(cli, ["config", "current"])
            
            assert result.exit_code == 0
            assert "Currently active account: test" in result.output
            assert "https://test.atlassian.net" in result.output
            assert "test@example.com" in result.output

    def test_config_current_command_without_account(self, runner):
        """Test showing current account when none exists."""
        with patch("taskra.config.account.get_current_account", return_value=None):
            result = runner.invoke(cli, ["config", "current"])
            
            assert result.exit_code == 0
            assert "No account is currently active" in result.output
