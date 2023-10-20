"""Integration tests for CLI commands."""

import os
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner

from taskra.cmd.main import cli


class TestCliIntegration:
    """Tests CLI commands integration with core functionality."""
    
    @pytest.fixture
    def runner(self):
        """Set up CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def mock_env_vars(self):
        """Set up environment variables for testing."""
        with pytest.MonkeyPatch().context() as m:
            m.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
            m.setenv("JIRA_API_TOKEN", "dummy-token")
            m.setenv("JIRA_EMAIL", "test@example.com")
            m.setenv("TASKRA_TESTING", "1")  # Add this line
            yield
    
    def test_projects_command(self, runner, mock_env_vars):
        """Test the projects command shows project list."""
        # Patch the core module that gets imported inside the CLI command function
        # The function imports "from ..core import list_projects", so we need to patch there
        with patch("taskra.core.list_projects") as mock_list_projects:
            # Setup mock to return test data
            test_projects = [
                {"key": "TEST", "name": "Test Project"},
                {"key": "DEMO", "name": "Demo Project"}
            ]
            
            # Make mock print the expected output and return data
            def mock_impl():
                print("TEST: Test Project")
                print("DEMO: Demo Project")
                return test_projects
                
            mock_list_projects.side_effect = mock_impl
            
            # Run the command
            result = runner.invoke(cli, ["projects"])
            
            # Print debugging information
            print(f"\nActual output:\n{result.output}")
            
            # Check the command executed successfully
            assert result.exit_code == 0
            assert "Available Projects:" in result.output
            
            # Verify our mock was called
            mock_list_projects.assert_called_once()
            
            # Check that the expected output is there
            assert "TEST: Test Project" in result.output
            assert "DEMO: Demo Project" in result.output
            assert f"Total projects: {len(test_projects)}" in result.output
    
    def test_issue_command(self, runner, mock_env_vars):
        """Test the issue command shows issue details."""
        # Patch the core module function that gets imported
        # The CLI command uses "from ..core import get_issue"
        with patch("taskra.core.get_issue") as mock_get_issue:
            # Setup mock to return test data
            test_issue = {
                "key": "TEST-123",
                "fields": {
                    "summary": "Test issue",
                    "status": {"name": "In Progress"}
                }
            }
            mock_get_issue.return_value = test_issue
            
            # Run the command
            result = runner.invoke(cli, ["issue", "TEST-123"])
            
            # Print debugging information
            print(f"\nActual output:\n{result.output}")
            if result.exception:
                print(f"Exception: {result.exception}")
            
            # Check the command executed successfully
            assert result.exit_code == 0
            
            # Check that the issue details are in the output
            assert "Issue details for TEST-123" in result.output
            
            # Verify our mock was called with the right argument
            mock_get_issue.assert_called_once_with("TEST-123")
    
    @pytest.mark.skipif(not os.environ.get("RUN_LIVE_TESTS"), 
                       reason="Live tests disabled. Set RUN_LIVE_TESTS=1 to enable.")
    def test_end_to_end_workflow(self, runner):
        """
        Test a complete workflow with real API calls.
        
        This test is skipped by default since it requires real credentials.
        To run it, you need to set the environment variables:
        - RUN_LIVE_TESTS=1
        - JIRA_BASE_URL
        - JIRA_API_TOKEN
        - JIRA_EMAIL
        - TEST_PROJECT_KEY
        """
        # Test the projects command
        result = runner.invoke(cli, ["projects"])
        assert result.exit_code == 0
        
        # Get a project key from the output or use the test one
        project_key = os.environ.get("TEST_PROJECT_KEY")
        assert project_key, "TEST_PROJECT_KEY environment variable must be set"
        
        # Create an issue
        with patch("builtins.input", side_effect=["Test Issue", "This is a test issue"]):
            result = runner.invoke(cli, ["issue", "create", project_key])
            assert result.exit_code == 0
            
        # The last line of output should contain the created issue key
        issue_key = result.output.strip().split("\n")[-1]
        
        # Get the issue details
        result = runner.invoke(cli, ["issue", issue_key])
        assert result.exit_code == 0
        assert issue_key in result.output
        assert "Test Issue" in result.output
