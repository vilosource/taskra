"""Tests for integration between core worklogs and Pydantic models."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from taskra.api.models.worklog import Worklog, Author
from taskra.core.worklogs import add_worklog, list_worklogs, get_user_worklogs

class TestCoreWorklogIntegration:
    """Tests for integration between core worklogs module and Pydantic models."""
    
    @patch('taskra.core.worklogs.WorklogService')
    @patch('taskra.core.worklogs.get_client')
    def test_add_worklog_with_models(self, mock_get_client, mock_service_class):
        """Test add_worklog with model return values."""
        # Setup
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Create a model instance that the service will return
        author = Author(accountId="user123", displayName="Test User")
        worklog_model = Worklog(
            id="12345",
            self="https://example.com/rest/api/3/issue/TEST-123/worklog/12345",
            author=author,
            timeSpent="1h 30m",
            timeSpentSeconds=5400,
            started=datetime.now(),
            created=datetime.now(),
            updated=datetime.now()
        )
        mock_service.add_worklog.return_value = worklog_model
        
        # Execute
        result = add_worklog("TEST-123", "1h 30m", "Test comment")
        
        # Verify
        mock_get_client.assert_called_once()
        mock_service_class.assert_called_once_with(mock_client)
        mock_service.add_worklog.assert_called_once_with("TEST-123", "1h 30m", "Test comment", None)
        
        # The result should be a dictionary with the correct values
        assert isinstance(result, dict)
        assert result["id"] == "12345"
        assert result["timeSpent"] == "1h 30m"
        assert result["timeSpentSeconds"] == 5400
        assert "author" in result
        assert result["author"]["displayName"] == "Test User"
    
    @patch('taskra.core.worklogs.WorklogService')
    @patch('taskra.core.worklogs.get_client')
    @patch('taskra.core.worklogs.get_from_cache')
    @patch('taskra.core.worklogs.save_to_cache')
    def test_list_worklogs_with_models(self, mock_save_to_cache, mock_get_from_cache, 
                                       mock_get_client, mock_service_class):
        """Test list_worklogs with model return values."""
        # Setup for cache miss
        mock_get_from_cache.return_value = None
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Create model instances that the service will return
        author = Author(accountId="user123", displayName="Test User")
        worklog_models = [
            Worklog(
                id="12345",
                self="https://example.com/rest/api/3/issue/TEST-123/worklog/12345",
                author=author,
                timeSpent="1h 30m",
                timeSpentSeconds=5400,
                started=datetime.now(),
                created=datetime.now(),
                updated=datetime.now()
            ),
            Worklog(
                id="67890",
                self="https://example.com/rest/api/3/issue/TEST-123/worklog/67890",
                author=author,
                timeSpent="2h",
                timeSpentSeconds=7200,
                started=datetime.now(),
                created=datetime.now(),
                updated=datetime.now()
            )
        ]
        mock_service.list_worklogs.return_value = worklog_models
        
        # Execute
        result = list_worklogs("TEST-123", refresh_cache=True)
        
        # Verify
        mock_get_from_cache.assert_not_called()  # refresh_cache=True should skip cache lookup
        mock_get_client.assert_called_once()
        mock_service_class.assert_called_once_with(mock_client)
        mock_service.list_worklogs.assert_called_once_with("TEST-123")
        mock_save_to_cache.assert_called_once()
        
        # The result should be a list of dictionaries with the correct values
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == "12345"
        assert result[1]["id"] == "67890"
