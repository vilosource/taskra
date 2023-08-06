"""Tests for the ProjectsService class."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from taskra.api.services.projects import ProjectsService
from taskra.api.models.project import ProjectList


class TestProjectsService:
    """Tests for the ProjectsService class."""
    
    def test_list_projects_single_page(self):
        """Test listing projects when there's a single page."""
        # Create a mock client
        mock_client = Mock()
        
        # Set up the mock to return a sample response
        mock_response = {
            "startAt": 0,
            "maxResults": 50,
            "total": 2,
            "isLast": True,
            "values": [
                {"id": "10000", "key": "TEST", "name": "Test Project"},
                {"id": "10001", "key": "DEMO", "name": "Demo Project"}
            ]
        }
        mock_client.get.return_value = mock_response
        
        # Create the service with the mock client
        service = ProjectsService(mock_client)
        
        # Call the method and check results
        projects = service.list_projects()
        
        assert len(projects) == 2
        assert projects[0]["key"] == "TEST"
        assert projects[1]["key"] == "DEMO"
        
        # Verify the client was called correctly
        mock_client.get.assert_called_once_with(
            "project/search", params={"startAt": 0, "maxResults": 50}
        )
    
    def test_list_all_projects_pagination(self):
        """Test listing all projects with pagination."""
        # Create a mock client
        mock_client = Mock()
        
        # Set up the mock to return multiple pages of results
        mock_responses = [
            # First page
            {
                "startAt": 0,
                "maxResults": 2,
                "total": 5,
                "isLast": False,
                "values": [
                    {"id": "10000", "key": "TEST1", "name": "Test Project 1"},
                    {"id": "10001", "key": "TEST2", "name": "Test Project 2"}
                ]
            },
            # Second page
            {
                "startAt": 2,
                "maxResults": 2,
                "total": 5,
                "isLast": False,
                "values": [
                    {"id": "10002", "key": "TEST3", "name": "Test Project 3"},
                    {"id": "10003", "key": "TEST4", "name": "Test Project 4"}
                ]
            },
            # Third page
            {
                "startAt": 4,
                "maxResults": 2,
                "total": 5,
                "isLast": True,
                "values": [
                    {"id": "10004", "key": "TEST5", "name": "Test Project 5"}
                ]
            }
        ]
        
        mock_client.get.side_effect = mock_responses
        
        # Create the service with the mock client
        service = ProjectsService(mock_client)
        
        # Call the method and check results
        projects = service.list_all_projects(max_results_per_page=2)
        
        # Verify we got all projects
        assert len(projects) == 5
        assert projects[0]["key"] == "TEST1"
        assert projects[4]["key"] == "TEST5"
        
        # Verify the client was called correctly for each page
        assert mock_client.get.call_count == 3
        mock_client.get.assert_any_call(
            "project/search", params={"startAt": 0, "maxResults": 2}
        )
        mock_client.get.assert_any_call(
            "project/search", params={"startAt": 2, "maxResults": 2}
        )
        mock_client.get.assert_any_call(
            "project/search", params={"startAt": 4, "maxResults": 2}
        )
