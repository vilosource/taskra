"""Tests for the worklog module."""

import pytest
from unittest.mock import Mock, patch, call
import datetime

from taskra.core.worklogs import add_worklog, list_worklogs, get_user_worklogs


@pytest.fixture
def mock_client():
    """Mock the Jira client."""
    return Mock()


@pytest.fixture
def mock_worklog_service():
    """Mock the WorklogService."""
    mock_service = Mock()
    mock_service.add_worklog.return_value = {"id": "123", "timeSpent": "1h"}
    mock_service.list_worklogs.return_value = [{"id": "123", "timeSpent": "1h"}]
    mock_service.get_user_worklogs.return_value = [
        {"id": "123", "timeSpent": "1h", "issue": {"key": "TEST-123"}}
    ]
    return mock_service


class TestAddWorklog:
    """Tests for the add_worklog function."""

    @patch("taskra.core.worklogs.get_client")
    @patch("taskra.core.worklogs.WorklogService")
    def test_add_worklog_with_comment(self, mock_service_class, mock_get_client, mock_client):
        """Test adding a worklog with a comment."""
        mock_get_client.return_value = mock_client
        mock_service = mock_service_class.return_value
        mock_service.add_worklog.return_value = {"id": "123", "timeSpent": "1h"}

        result = add_worklog("TEST-123", "1h", "Test comment")

        mock_get_client.assert_called_once()
        mock_service_class.assert_called_once_with(mock_client)
        mock_service.add_worklog.assert_called_once_with("TEST-123", "1h", "Test comment")
        assert result == {"id": "123", "timeSpent": "1h"}

    @patch("taskra.core.worklogs.get_client")
    @patch("taskra.core.worklogs.WorklogService")
    def test_add_worklog_without_comment(self, mock_service_class, mock_get_client, mock_client):
        """Test adding a worklog without a comment."""
        mock_get_client.return_value = mock_client
        mock_service = mock_service_class.return_value
        mock_service.add_worklog.return_value = {"id": "123", "timeSpent": "1h"}

        result = add_worklog("TEST-123", "1h")

        mock_service.add_worklog.assert_called_once_with("TEST-123", "1h", None)
        assert result == {"id": "123", "timeSpent": "1h"}


class TestListWorklogs:
    """Tests for the list_worklogs function."""

    @patch("taskra.core.worklogs.generate_cache_key")
    @patch("taskra.core.worklogs.get_from_cache")
    @patch("taskra.core.worklogs.save_to_cache")
    @patch("taskra.core.worklogs.get_client")
    @patch("taskra.core.worklogs.WorklogService")
    def test_list_worklogs_cache_hit(
        self, mock_service_class, mock_get_client, 
        mock_save_to_cache, mock_get_from_cache, mock_generate_cache_key
    ):
        """Test listing worklogs with cache hit."""
        mock_generate_cache_key.return_value = "cache-key-123"
        mock_get_from_cache.return_value = [{"id": "123", "timeSpent": "1h"}]

        result = list_worklogs("TEST-123")

        mock_generate_cache_key.assert_called_once_with(
            function="list_worklogs", issue_key="TEST-123"
        )
        mock_get_from_cache.assert_called_once_with("cache-key-123")
        mock_get_client.assert_not_called()
        mock_service_class.assert_not_called()
        mock_save_to_cache.assert_not_called()
        assert result == [{"id": "123", "timeSpent": "1h"}]

    @patch("taskra.core.worklogs.generate_cache_key")
    @patch("taskra.core.worklogs.get_from_cache")
    @patch("taskra.core.worklogs.save_to_cache")
    @patch("taskra.core.worklogs.get_client")
    @patch("taskra.core.worklogs.WorklogService")
    def test_list_worklogs_cache_miss(
        self, mock_service_class, mock_get_client, 
        mock_save_to_cache, mock_get_from_cache, mock_generate_cache_key, mock_client
    ):
        """Test listing worklogs with cache miss."""
        mock_generate_cache_key.return_value = "cache-key-123"
        mock_get_from_cache.return_value = None
        mock_get_client.return_value = mock_client
        mock_service = mock_service_class.return_value
        mock_service.list_worklogs.return_value = [{"id": "123", "timeSpent": "1h"}]

        result = list_worklogs("TEST-123")

        mock_generate_cache_key.assert_called_once_with(
            function="list_worklogs", issue_key="TEST-123"
        )
        mock_get_from_cache.assert_called_once_with("cache-key-123")
        mock_get_client.assert_called_once()
        mock_service_class.assert_called_once_with(mock_client)
        mock_service.list_worklogs.assert_called_once_with("TEST-123")
        mock_save_to_cache.assert_called_once_with(
            "cache-key-123", [{"id": "123", "timeSpent": "1h"}]
        )
        assert result == [{"id": "123", "timeSpent": "1h"}]

    @patch("taskra.core.worklogs.generate_cache_key")
    @patch("taskra.core.worklogs.get_from_cache")
    @patch("taskra.core.worklogs.save_to_cache")
    @patch("taskra.core.worklogs.get_client")
    @patch("taskra.core.worklogs.WorklogService")
    def test_list_worklogs_refresh_cache(
        self, mock_service_class, mock_get_client, 
        mock_save_to_cache, mock_get_from_cache, mock_generate_cache_key, mock_client
    ):
        """Test listing worklogs with refresh_cache=True."""
        mock_generate_cache_key.return_value = "cache-key-123"
        mock_get_client.return_value = mock_client
        mock_service = mock_service_class.return_value
        mock_service.list_worklogs.return_value = [{"id": "123", "timeSpent": "1h"}]

        result = list_worklogs("TEST-123", refresh_cache=True)

        mock_generate_cache_key.assert_called_once_with(
            function="list_worklogs", issue_key="TEST-123"
        )
        mock_get_from_cache.assert_not_called()
        mock_get_client.assert_called_once()
        mock_service_class.assert_called_once_with(mock_client)
        mock_service.list_worklogs.assert_called_once_with("TEST-123")
        mock_save_to_cache.assert_called_once_with(
            "cache-key-123", [{"id": "123", "timeSpent": "1h"}]
        )
        assert result == [{"id": "123", "timeSpent": "1h"}]


class TestGetUserWorklogs:
    """Tests for the get_user_worklogs function."""

    @patch("taskra.core.worklogs.generate_cache_key")
    @patch("taskra.core.worklogs.get_from_cache")
    @patch("taskra.core.worklogs.save_to_cache")
    @patch("taskra.core.worklogs.get_client")
    @patch("taskra.core.worklogs.WorklogService")
    def test_get_user_worklogs_cache_hit(
        self, mock_service_class, mock_get_client, 
        mock_save_to_cache, mock_get_from_cache, mock_generate_cache_key
    ):
        """Test getting user worklogs with cache hit."""
        mock_generate_cache_key.return_value = "cache-key-123"
        mock_get_from_cache.return_value = [
            {"id": "123", "timeSpent": "1h", "issue": {"key": "TEST-123"}}
        ]

        result = get_user_worklogs(
            username="user1", 
            start_date="2023-01-01", 
            end_date="2023-01-31", 
            debug_level="none"
        )

        mock_generate_cache_key.assert_called_once_with(
            function="get_user_worklogs",
            username="user1",
            start_date="2023-01-01",
            end_date="2023-01-31"
        )
        mock_get_from_cache.assert_called_once_with("cache-key-123")
        mock_get_client.assert_not_called()
        mock_service_class.assert_not_called()
        mock_save_to_cache.assert_not_called()
        assert result == [{"id": "123", "timeSpent": "1h", "issue": {"key": "TEST-123"}}]

    @patch("taskra.core.worklogs.generate_cache_key")
    @patch("taskra.core.worklogs.get_from_cache")
    @patch("taskra.core.worklogs.save_to_cache")
    @patch("taskra.core.worklogs.get_client")
    @patch("taskra.core.worklogs.WorklogService")
    def test_get_user_worklogs_cache_miss(
        self, mock_service_class, mock_get_client, 
        mock_save_to_cache, mock_get_from_cache, mock_generate_cache_key, mock_client
    ):
        """Test getting user worklogs with cache miss."""
        mock_generate_cache_key.return_value = "cache-key-123"
        mock_get_from_cache.return_value = None
        mock_get_client.return_value = mock_client
        mock_service = mock_service_class.return_value
        mock_service.get_user_worklogs.return_value = [
            {"id": "123", "timeSpent": "1h", "issue": {"key": "TEST-123"}}
        ]

        result = get_user_worklogs(
            username="user1", 
            start_date="2023-01-01", 
            end_date="2023-01-31", 
            debug_level="none"
        )

        mock_generate_cache_key.assert_called_once_with(
            function="get_user_worklogs",
            username="user1",
            start_date="2023-01-01",
            end_date="2023-01-31"
        )
        mock_get_from_cache.assert_called_once_with("cache-key-123")
        mock_get_client.assert_called_once_with(debug=False)
        mock_service_class.assert_called_once_with(mock_client)
        mock_service.get_user_worklogs.assert_called_once_with(
            username="user1",
            start_date="2023-01-01",
            end_date="2023-01-31",
            debug_level="none"
        )
        mock_save_to_cache.assert_called_once_with(
            "cache-key-123", 
            [{"id": "123", "timeSpent": "1h", "issue": {"key": "TEST-123"}}]
        )
        assert result == [{"id": "123", "timeSpent": "1h", "issue": {"key": "TEST-123"}}]

    @patch("taskra.core.worklogs.generate_cache_key")
    @patch("taskra.core.worklogs.get_from_cache")
    @patch("taskra.core.worklogs.save_to_cache")
    @patch("taskra.core.worklogs.get_client")
    @patch("taskra.core.worklogs.WorklogService")
    def test_get_user_worklogs_refresh_cache(
        self, mock_service_class, mock_get_client, 
        mock_save_to_cache, mock_get_from_cache, mock_generate_cache_key, mock_client
    ):
        """Test getting user worklogs with refresh_cache=True."""
        mock_generate_cache_key.return_value = "cache-key-123"
        mock_get_client.return_value = mock_client
        mock_service = mock_service_class.return_value
        mock_service.get_user_worklogs.return_value = [
            {"id": "123", "timeSpent": "1h", "issue": {"key": "TEST-123"}}
        ]

        result = get_user_worklogs(
            username="user1", 
            start_date="2023-01-01", 
            end_date="2023-01-31", 
            debug_level="none",
            refresh_cache=True
        )

        mock_generate_cache_key.assert_called_once_with(
            function="get_user_worklogs",
            username="user1",
            start_date="2023-01-01",
            end_date="2023-01-31"
        )
        mock_get_from_cache.assert_not_called()
        mock_get_client.assert_called_once_with(debug=False)
        mock_service_class.assert_called_once_with(mock_client)
        mock_service.get_user_worklogs.assert_called_once_with(
            username="user1",
            start_date="2023-01-01",
            end_date="2023-01-31",
            debug_level="none"
        )
        assert result == [{"id": "123", "timeSpent": "1h", "issue": {"key": "TEST-123"}}]

    @patch("taskra.core.worklogs.generate_cache_key")
    @patch("taskra.core.worklogs.get_from_cache")
    @patch("taskra.core.worklogs.save_to_cache")
    @patch("taskra.core.worklogs.get_client")
    @patch("taskra.core.worklogs.WorklogService")
    def test_get_user_worklogs_debug_levels(
        self, mock_service_class, mock_get_client, 
        mock_save_to_cache, mock_get_from_cache, mock_generate_cache_key, mock_client
    ):
        """Test getting user worklogs with different debug levels."""
        mock_generate_cache_key.return_value = "cache-key-123"
        mock_get_from_cache.return_value = None
        mock_get_client.return_value = mock_client
        mock_service = mock_service_class.return_value
        
        # Test with debug_level=info
        get_user_worklogs(debug_level="info")
        mock_get_client.assert_called_with(debug=True)
        
        # Test with debug_level=verbose
        get_user_worklogs(debug_level="verbose")
        mock_get_client.assert_called_with(debug=True)
        
        # Test with debug_level=error
        get_user_worklogs(debug_level="error")
        mock_get_client.assert_called_with(debug=False)

    @patch("taskra.core.worklogs.logging")
    @patch("taskra.core.worklogs.generate_cache_key")
    @patch("taskra.core.worklogs.get_from_cache")
    @patch("taskra.core.worklogs.get_client")
    @patch("taskra.core.worklogs.WorklogService")
    def test_get_user_worklogs_with_logging(
        self, mock_service_class, mock_get_client, 
        mock_get_from_cache, mock_generate_cache_key, mock_logging, mock_client
    ):
        """Test that logging is called appropriately based on debug level."""
        mock_generate_cache_key.return_value = "cache-key-123"
        
        # Test with cache hit and info debug level
        mock_get_from_cache.return_value = [{"id": "123"}]
        get_user_worklogs(debug_level="info")
        mock_logging.info.assert_called_with("Using cached worklog data")
        
        # Test with cache miss and info debug level
        mock_logging.info.reset_mock()
        mock_get_from_cache.return_value = None
        get_user_worklogs(debug_level="info")
        mock_logging.info.assert_called_with("Fetching fresh worklog data")
        
        # Test with none debug level - should not log
        mock_logging.info.reset_mock()
        mock_get_from_cache.return_value = [{"id": "123"}]
        get_user_worklogs(debug_level="none")
        mock_logging.info.assert_not_called()
