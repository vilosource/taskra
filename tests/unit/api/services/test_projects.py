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
        
        # Set up the mock to return a sample response with required fields
        mock_response = {
            "startAt": 0,
            "maxResults": 50,
            "total": 2,
            "isLast": True,
            "values": [
                {
                    "id": "10000", 
                    "key": "TEST", 
                    "name": "Test Project", 
                    "projectTypeKey": "software",
                    "self": "https://example.com/rest/api/3/project/10000"  # Using 'self' for API (alias for self_url)
                },
                {
                    "id": "10001", 
                    "key": "DEMO", 
                    "name": "Demo Project", 
                    "projectTypeKey": "business",
                    "self": "https://example.com/rest/api/3/project/10001"  # Add required self field
                }
            ]
        }
        mock_client.get.return_value = mock_response
        
        # Create the service with the mock client
        service = ProjectsService(mock_client)
        
        # Call the method and check results
        projects = service.list_projects()
        
        # Verify the results
        assert len(projects) == 2
        assert projects[0].key == "TEST"
        assert projects[1].key == "DEMO"
        
        # Verify the client was called correctly
        mock_client.get.assert_called_once_with(
            "project/search", params={"startAt": 0, "maxResults": 50}
        )
    
    def test_list_all_projects_pagination(self):
        """Test listing all projects with pagination."""
        # Create a mock client
        mock_client = Mock()
        
        # Set up the mock to return multiple pages of results with required fields
        mock_responses = [
            # First page
            {
                "startAt": 0,
                "maxResults": 2,
                "total": 5,
                "isLast": False,
                "values": [
                    {
                        "id": "10000", 
                        "key": "TEST1", 
                        "name": "Test Project 1", 
                        "projectTypeKey": "software",
                        "self": "https://example.com/rest/api/3/project/10000"  # Add required field
                    },
                    {
                        "id": "10001", 
                        "key": "TEST2", 
                        "name": "Test Project 2", 
                        "projectTypeKey": "software",
                        "self": "https://example.com/rest/api/3/project/10001"  # Add required field
                    }
                ]
            },
            # Second page
            {
                "startAt": 2,
                "maxResults": 2,
                "total": 5,
                "isLast": False,
                "values": [
                    {
                        "id": "10002", 
                        "key": "TEST3", 
                        "name": "Test Project 3", 
                        "projectTypeKey": "software",
                        "self": "https://example.com/rest/api/3/project/10002"  # Add required field
                    },
                    {
                        "id": "10003", 
                        "key": "TEST4", 
                        "name": "Test Project 4", 
                        "projectTypeKey": "software",
                        "self": "https://example.com/rest/api/3/project/10003"  # Add required field
                    }
                ]
            },
            # Third page
            {
                "startAt": 4,
                "maxResults": 2,
                "total": 5,
                "isLast": True,
                "values": [
                    {
                        "id": "10004", 
                        "key": "TEST5", 
                        "name": "Test Project 5", 
                        "projectTypeKey": "software",
                        "self": "https://example.com/rest/api/3/project/10004"  # Add required field
                    }
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
        assert projects[0].key == "TEST1"
        assert projects[4].key == "TEST5"
        
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
    
    def test_get_project(self):
        """Test getting a project by key."""
        # Create a mock client
        mock_client = Mock()
        
        # Set up the mock response with self field for API compatibility
        mock_response = {
            "id": "10000", 
            "key": "TEST", 
            "name": "Test Project", 
            "projectTypeKey": "software",
            "self": "https://example.com/rest/api/3/project/10000"  # API uses 'self'
        }
        mock_client.get.return_value = mock_response
        
        # Create the service with the mock client
        service = ProjectsService(mock_client)
        
        # Call the method and check results
        project = service.get_project("TEST")
        
        # Verify the results - using self_url in Python code
        assert project.self_url == "https://example.com/rest/api/3/project/10000"  # Using self_url internally
        assert project.self == "https://example.com/rest/api/3/project/10000"  # Property getter works too
        assert project.key == "TEST"
        
        # Verify the client was called correctly
        mock_client.get.assert_called_once_with("project/TEST")
