"""Tests for Issue model adapters."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from taskra.api.models.issue import Issue, IssueFields, IssueType, IssueStatus
from taskra.utils.model_adapters import adapt_issue_for_presentation
from taskra.api.services.issues import IssuesService

class TestIssueAdapters:
    """Test Issue model adapters."""
    
    def test_issue_adapter(self):
        """Test adapting issues for presentation."""
        # Create an issue type
        issue_type = IssueType(
            id="10001",
            name="Task",
            description="A task that needs to be done",
            iconUrl="https://example.com/icons/task.png",
            subtask=False
        )
        
        # Create issue status
        status = IssueStatus(
            id="3",
            name="In Progress",
            description="Work has begun on this issue"
        )
        
        # Create issue fields
        fields = IssueFields(
            summary="Test Issue",
            description=None,
            issuetype=issue_type,
            status=status,
            assignee=None,
            reporter=None,
            created=datetime.now(),
            updated=datetime.now()
        )
        
        # Create the issue
        issue = Issue(
            self_url="https://example.com/rest/api/3/issue/TEST-123",
            id="10002",
            key="TEST-123",
            fields=fields
        )
        
        # Adapt for presentation
        result = adapt_issue_for_presentation(issue)
        
        # Verify adaptation
        assert isinstance(result, dict)
        assert "key" in result
        assert result["key"] == "TEST-123"
        assert "summary" in result  # Should be extracted from fields
        assert result["summary"] == "Test Issue"
        assert "statusName" in result  # Should be extracted from fields.status
        assert result["statusName"] == "In Progress"
        
    def test_issue_dict_adapter(self):
        """Test adapting issue dictionaries for presentation."""
        # Create an issue dictionary (simulating old code)
        issue_dict = {
            "self": "https://example.com/rest/api/3/issue/TEST-123",
            "id": "10002",
            "key": "TEST-123",
            "fields": {
                "summary": "Test Issue",
                "issuetype": {
                    "id": "10001",
                    "name": "Task"
                },
                "status": {
                    "id": "3",
                    "name": "In Progress"
                }
            }
        }
        
        # Adapt for presentation
        result = adapt_issue_for_presentation(issue_dict)
        
        # Verify adaptation
        assert isinstance(result, dict)
        assert "key" in result
        assert result["key"] == "TEST-123"
        assert "summary" in result
        assert result["summary"] == "Test Issue"
        assert "statusName" in result
        assert result["statusName"] == "In Progress"
