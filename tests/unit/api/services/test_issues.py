"""Tests for the IssuesService class."""

import pytest
from unittest.mock import Mock, patch

from taskra.api.services.issues import IssuesService


class TestIssuesService:
    """Tests for the IssuesService class."""
    
    def test_get_issue(self):
        """Test retrieving a single issue."""
        # Create a mock client
        mock_client = Mock()
        
        # Set up the mock to return a sample response that matches the Issue model structure
        mock_response = {
            "id": "10000",
            "key": "TEST-1",
            "self": "https://example.com/rest/api/3/issue/10000",
            "fields": {
                "summary": "Test issue",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "This is a test issue"
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {
                    "id": "10001",
                    "name": "Task"
                }
            }
        }
        mock_client.get.return_value = mock_response
        
        # Create the service with the mock client
        service = IssuesService(mock_client)
        
        # Call the method and check results
        issue = service.get_issue("TEST-1")
        
        assert issue["key"] == "TEST-1"
        assert issue["fields"]["summary"] == "Test issue"
        
        # Verify the client was called correctly
        mock_client.get.assert_called_once_with("issue/TEST-1")
    
    def test_get_comments_single_page(self):
        """Test retrieving comments when they fit in a single page."""
        # Create a mock client
        mock_client = Mock()
        
        # Set up the mock to return a sample response
        mock_response = {
            "comments": [
                {
                    "id": "10000",
                    "body": "This is a comment",
                    "author": {
                        "accountId": "user123",
                        "displayName": "John Doe"
                    }
                },
                {
                    "id": "10001",
                    "body": "This is another comment",
                    "author": {
                        "accountId": "user456",
                        "displayName": "Jane Smith"
                    }
                }
            ],
            "startAt": 0,
            "maxResults": 50,
            "total": 2
        }
        mock_client.get.return_value = mock_response
        
        # Create the service with the mock client
        service = IssuesService(mock_client)
        
        # Call the method and check results
        comments = service.get_comments("TEST-1", get_all=False)
        
        assert len(comments) == 2
        assert comments[0]["id"] == "10000"
        assert comments[0]["body"] == "This is a comment"
        assert comments[1]["id"] == "10001"
        
        # Verify the client was called correctly
        mock_client.get.assert_called_once_with(
            "issue/TEST-1/comment", params={"startAt": 0, "maxResults": 50}
        )
    
    def test_get_all_comments_pagination(self):
        """Test retrieving all comments across multiple pages."""
        # Create a mock client
        mock_client = Mock()
        
        # Set up the mock to return multiple pages of results
        mock_responses = [
            # First page
            {
                "comments": [
                    {
                        "id": "10000",
                        "body": "First comment",
                        "author": {"displayName": "User 1"}
                    },
                    {
                        "id": "10001",
                        "body": "Second comment",
                        "author": {"displayName": "User 2"}
                    }
                ],
                "startAt": 0,
                "maxResults": 2,
                "total": 5
            },
            # Second page
            {
                "comments": [
                    {
                        "id": "10002",
                        "body": "Third comment",
                        "author": {"displayName": "User 3"}
                    },
                    {
                        "id": "10003",
                        "body": "Fourth comment",
                        "author": {"displayName": "User 1"}
                    }
                ],
                "startAt": 2,
                "maxResults": 2,
                "total": 5
            },
            # Third page
            {
                "comments": [
                    {
                        "id": "10004",
                        "body": "Fifth comment",
                        "author": {"displayName": "User 2"}
                    }
                ],
                "startAt": 4,
                "maxResults": 2,
                "total": 5
            }
        ]
        
        mock_client.get.side_effect = mock_responses
        
        # Create the service with the mock client
        service = IssuesService(mock_client)
        
        # Call the method and check results
        comments = service.get_comments("TEST-1", max_results=2)
        
        # Verify we got all comments
        assert len(comments) == 5
        assert comments[0]["id"] == "10000"
        assert comments[4]["id"] == "10004"
        
        # Verify the client was called correctly for each page
        assert mock_client.get.call_count == 3
        mock_client.get.assert_any_call(
            "issue/TEST-1/comment", params={"startAt": 0, "maxResults": 2}
        )
        mock_client.get.assert_any_call(
            "issue/TEST-1/comment", params={"startAt": 2, "maxResults": 2}
        )
        mock_client.get.assert_any_call(
            "issue/TEST-1/comment", params={"startAt": 4, "maxResults": 2}
        )
