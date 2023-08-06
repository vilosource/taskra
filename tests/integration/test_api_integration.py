"""Integration tests for Jira API interactions."""

import os
import pytest
from unittest.mock import patch

from taskra.api.client import JiraClient, get_client
from taskra.api.services.projects import ProjectsService
from taskra.api.services.issues import IssuesService
from taskra.api.services.worklogs import WorklogService


class TestJiraClientIntegration:
    """Tests JiraClient integration with API endpoints."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Set up environment variables for testing."""
        with patch.dict(os.environ, {
            "JIRA_BASE_URL": "https://example.atlassian.net",
            "JIRA_API_TOKEN": "dummy-token",
            "JIRA_EMAIL": "test@example.com"
        }):
            yield
            
    def test_client_initialization(self, mock_env_vars):
        """Test client is properly initialized from environment variables."""
        client = get_client()
        assert client.base_url == "https://example.atlassian.net/rest/api/3/"
        
    @pytest.mark.vcr(scope="module")  # Specify module scope for VCR
    def test_projects_service_list_projects(self, mock_env_vars):
        """Test ProjectsService can list projects through the API."""
        client = get_client()
        service = ProjectsService(client)
        projects = service.list_projects()
        
        assert isinstance(projects, list)
        if projects:  # If the test instance has projects
            assert "id" in projects[0]
            assert "key" in projects[0]
            assert "name" in projects[0]
    
    @pytest.mark.vcr(scope="module")  # Specify module scope for VCR
    def test_issues_service_get_issue(self, mock_env_vars):
        """Test IssuesService can retrieve an issue."""
        client = get_client()
        service = IssuesService(client)
        
        # This requires a known issue key from the test environment
        issue_key = os.environ.get("TEST_ISSUE_KEY", "TEST-1")
        issue = service.get_issue(issue_key)
        
        assert issue["key"] == issue_key
        
    @pytest.mark.vcr(scope="module")  # Specify module scope for VCR
    def test_create_and_get_worklog(self, mock_env_vars):
        """Test creating and retrieving a worklog - full integration flow."""
        client = get_client()
        issues_service = IssuesService(client)
        worklog_service = WorklogService(client)
        
        # 1. First create a test issue
        issue_key = os.environ.get("TEST_ISSUE_KEY", "TEST-1")
        
        # 2. Add a worklog to the issue
        worklog = worklog_service.add_worklog(
            issue_key=issue_key, 
            time_spent="1h", 
            comment="Integration test worklog"
        )
        
        # 3. Verify the worklog was added
        assert "id" in worklog
        
        # 4. Get all worklogs for the issue and verify our worklog is there
        worklogs = worklog_service.list_worklogs(issue_key)
        worklog_ids = [w.get("id") for w in worklogs]
        assert worklog["id"] in worklog_ids
