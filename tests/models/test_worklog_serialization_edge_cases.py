"""Tests for edge cases in worklog model serialization."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from taskra.api.models.worklog import Worklog, Author, WorklogCreate
from taskra.api.models.user import User
from taskra.core.worklogs import _to_json_serializable, add_worklog

class TestWorklogSerializationEdgeCases:
    """Test edge cases in worklog serialization."""
    
    def test_complex_nested_objects(self):
        """Test serializing complex nested objects in a worklog."""
        # Create a complex nested structure
        author = Author(
            accountId="user123",
            displayName="Test User",
            emailAddress="test@example.com",
            avatarUrls={
                "48x48": "https://example.com/avatar.png",
                "24x24": "https://example.com/avatar-small.png"
            }
        )
        
        # Create a worklog with complex comment structure
        worklog = Worklog(
            id="12345",
            self="https://example.com/rest/api/3/issue/TEST-123/worklog/12345",
            author=author,
            timeSpent="1h 30m",
            timeSpentSeconds=5400,
            started=datetime.now(),
            created=datetime.now(),
            updated=datetime.now(),
            comment={
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "This is a complex comment"
                            }
                        ]
                    }
                ]
            }
        )
        
        # Serialize the worklog
        result = _to_json_serializable(worklog)
        
        # Verify structure is maintained
        assert isinstance(result, dict)
        assert "author" in result
        assert isinstance(result["author"], dict)
        assert "displayName" in result["author"]
        assert result["author"]["displayName"] == "Test User"
        assert "avatarUrls" in result["author"]
        assert "48x48" in result["author"]["avatarUrls"]
        
        # Check comment structure
        assert "comment" in result
        assert isinstance(result["comment"], dict)
        assert "content" in result["comment"]
        assert isinstance(result["comment"]["content"], list)
        assert len(result["comment"]["content"]) > 0
        
    def test_datetime_timezone_handling(self):
        """Test handling of datetime objects with timezones."""
        # Create a datetime with timezone info
        dt_with_tz = datetime.now(timezone.utc)
        
        # Create a worklog with timezone-aware datetime
        worklog = Worklog(
            id="12345",
            self="https://example.com/api",
            author=Author(accountId="123", displayName="User"),
            timeSpent="1h",
            timeSpentSeconds=3600,
            started=dt_with_tz,
            created=dt_with_tz,
            updated=dt_with_tz
        )
        
        # Serialize the worklog
        result = _to_json_serializable(worklog)
        
        # Check datetime fields are properly serialized to ISO format
        assert isinstance(result["started"], str)
        assert "T" in result["started"]
        assert "+" in result["started"] or "Z" in result["started"]  # Timezone marker
        
    def test_empty_fields(self):
        """Test handling of empty or None fields."""
        # Create a worklog with minimal fields
        worklog = Worklog(
            id="12345",
            self="https://example.com/api",
            author=Author(accountId="123", displayName="User"),
            timeSpent="1h",
            timeSpentSeconds=3600,
            started=datetime.now(),
            created=datetime.now(),
            updated=datetime.now(),
            # These are intentionally left as None
            comment=None,
            visibility=None,
            issue_id=None
        )
        
        # Serialize the worklog
        result = _to_json_serializable(worklog)
        
        # Check that None fields are included in output
        assert "comment" in result
        assert result["comment"] is None
        
    @patch('taskra.core.worklogs.WorklogService')
    @patch('taskra.core.worklogs.get_client')
    def test_add_worklog_with_complex_comment(self, mock_get_client, mock_service_class):
        """Test adding a worklog with a complex comment structure."""
        # Setup
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Create a complex comment structure that the service will return
        complex_comment = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Complex comment with formatting"
                        }
                    ]
                }
            ]
        }
        
        # Create model to return
        author = Author(accountId="user123", displayName="Test User")
        worklog_model = Worklog(
            id="12345",
            self="https://example.com/rest/api/3/issue/TEST-123/worklog/12345",
            author=author,
            timeSpent="1h 30m",
            timeSpentSeconds=5400,
            started=datetime.now(),
            created=datetime.now(),
            updated=datetime.now(),
            comment=complex_comment
        )
        mock_service.add_worklog.return_value = worklog_model
        
        # Execute
        result = add_worklog("TEST-123", "1h 30m", "Test comment")
        
        # Verify
        assert isinstance(result, dict)
        assert "comment" in result
        assert isinstance(result["comment"], dict)
        assert "content" in result["comment"]
