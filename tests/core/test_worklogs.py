"""Tests for the worklogs functionality."""

import pytest
from unittest.mock import patch, MagicMock, Mock
from taskra.core.worklogs import add_worklog, list_worklogs, get_user_worklogs


# A mock adapter to make model data compatible with old test expectations
class ModelCompatAdapter:
    """Adapter to make new model data compatible with old test expectations."""
    
    @staticmethod
    def adapt_worklog(worklog_data):
        """
        Convert between model and dict representations of worklogs for testing.
        
        This ensures tests work with both old dict-based and new model-based implementations.
        """
        # Safety check for mocks to prevent recursion
        if isinstance(worklog_data, MagicMock) or isinstance(worklog_data, Mock):
            return worklog_data
            
        if hasattr(worklog_data, 'model_dump_api'):
            # It's a model - convert to dict for old tests
            data = worklog_data.model_dump_api()
            # Add backwards compatibility properties
            if 'author' in data and isinstance(data['author'], dict):
                data['author']['displayName'] = data['author'].get('displayName', '')
            return data
        return worklog_data


# Create a fixture that applies the adapter to any worklog data
@pytest.fixture(autouse=True, scope="function")
def apply_model_compatibility():
    """Apply model compatibility to worklog testing."""
    try:
        # Get references to original functions if they exist
        import taskra.core.worklogs
        _original_list_worklogs = taskra.core.worklogs.list_worklogs
        _original_get_user_worklogs = taskra.core.worklogs.get_user_worklogs
        
        # Create custom adapter functions that handle mocks safely
        def safe_list_adapter(*args, **kwargs):
            result = _original_list_worklogs(*args, **kwargs)
            if isinstance(result, (Mock, MagicMock)):
                return result
            return [ModelCompatAdapter.adapt_worklog(w) for w in result]
            
        def safe_get_user_adapter(*args, **kwargs):
            result = _original_get_user_worklogs(*args, **kwargs)
            if isinstance(result, (Mock, MagicMock)):
                return result
            return [ModelCompatAdapter.adapt_worklog(w) for w in result]
        
        # Apply the patches
        with patch('taskra.core.worklogs.list_worklogs', side_effect=safe_list_adapter):
            with patch('taskra.core.worklogs.get_user_worklogs', side_effect=safe_get_user_adapter):
                yield
    except ImportError:
        # Module not loaded yet
        yield


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
    """Tests for getting user worklogs."""

    @patch("taskra.core.worklogs.generate_cache_key")
    @patch("taskra.core.worklogs.get_from_cache")
    @patch("taskra.core.worklogs.save_to_cache")
    @patch("taskra.core.worklogs.get_client")
    @patch("taskra.core.worklogs.WorklogService")
    def test_get_user_worklogs_cache_miss(
        self, mock_service_class, mock_get_client,
        mock_save_to_cache, mock_get_from_cache, mock_generate_cache_key
    ):
        """Test getting user worklogs with cache miss."""
        mock_generate_cache_key.return_value = "cache-key-123"
        mock_get_from_cache.return_value = None
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_service = mock_service_class.return_value
        mock_service.get_user_worklogs.return_value = [
            {"id": "123", "timeSpent": "1h", "issue": {"key": "TEST-123"}}
        ]

        result = get_user_worklogs(
            username="user1",
            start_date="2023-01-01",
            end_date="2023-01-31",
            refresh_cache=True
        )

        mock_generate_cache_key.assert_called_once_with(
            function="get_user_worklogs",
            username="user1",
            start_date="2023-01-01",
            end_date="2023-01-31"
        )
        mock_get_from_cache.assert_not_called()  # Cache should be bypassed
        mock_get_client.assert_called_once()  # No debug parameter expected
        mock_service_class.assert_called_once_with(mock_client)
        mock_service.get_user_worklogs.assert_called_once_with(
            username="user1",
            start_date="2023-01-01",
            end_date="2023-01-31"
        )
        
        # Include the additional fields in the expected data
        expected_data = [
            {"id": "123", "timeSpent": "1h", "issue": {"key": "TEST-123"}, 
             "issueKey": "TEST-123", "issue_key": "TEST-123"}
        ]
        mock_save_to_cache.assert_called_once_with("cache-key-123", expected_data)
        
        # The result should also include the extra fields
        assert result == expected_data

    @patch("taskra.core.worklogs.generate_cache_key")
    @patch("taskra.core.worklogs.get_from_cache")
    @patch("taskra.core.worklogs.save_to_cache") 
    @patch("taskra.core.worklogs.get_client")
    @patch("taskra.core.worklogs.WorklogService")
    def test_get_user_worklogs_with_logging(
        self, mock_service_class, mock_get_client,
        mock_save_to_cache, mock_get_from_cache, mock_generate_cache_key
    ):
        """Test that logging is called appropriately based on cache usage."""
        mock_generate_cache_key.return_value = "cache-key-123"

        # Create a service mock that returns a simple dict
        mock_service = mock_service_class.return_value
        mock_service.get_user_worklogs.return_value = [{"id": "123"}]

        # Test with cache hit
        mock_get_from_cache.return_value = [{"id": "123"}]
        result = get_user_worklogs(username="user1", start_date="2023-01-01", end_date="2023-01-31")

        mock_generate_cache_key.assert_called_once_with(
            function="get_user_worklogs",
            username="user1",
            start_date="2023-01-01",
            end_date="2023-01-31"
        )
        mock_get_from_cache.assert_called_once_with("cache-key-123")
        mock_get_client.assert_not_called()  # Client should not be called on cache hit
        mock_service.get_user_worklogs.assert_not_called()  # Service should not be called on cache hit
        assert result == [{"id": "123"}]
