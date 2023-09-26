"""Worklog management functionality."""

import logging
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any, Union
from ..api.services.worklogs import WorklogService
from ..api.client import get_client
from ..utils.cache import generate_cache_key, get_from_cache, save_to_cache

def _to_json_serializable(obj):
    """
    Convert Pydantic models and other non-JSON serializable objects to JSON serializable dictionaries.
    
    This handles two key challenges:
    1. Converting non-serializable objects (like datetime) to JSON-compatible formats
    2. Preserving original field names from the Jira API (camelCase) that the presentation
       layer expects, rather than the snake_case names used internally by Pydantic models
    """
    # Check for Pydantic models
    if hasattr(obj, 'model_dump'):
        # For Pydantic v2+
        # IMPORTANT: We use by_alias=True to preserve the original camelCase field names from the API
        # Without this, fields would be serialized as snake_case and the presentation layer wouldn't find them
        result = obj.model_dump(by_alias=True)
        # Process the result to handle datetime objects
        return _to_json_serializable(result)
    elif hasattr(obj, 'dict'):
        # For Pydantic v1
        # IMPORTANT: Same reasoning as above - preserve the original API field names
        result = obj.dict(by_alias=True)
        # Process the result to handle datetime objects
        return _to_json_serializable(result)
    
    # Check for datetime objects
    if isinstance(obj, (datetime, date, time)):
        # Convert datetime to ISO format string
        return obj.isoformat()
    
    # Check for other datetime-like objects
    if hasattr(obj, 'isoformat') and callable(obj.isoformat):
        return obj.isoformat()


    
    # Handle collections
    if isinstance(obj, list):
        return [_to_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        # Special handling for worklog entries to preserve critical fields
        # This ensures compatibility between fresh API data and cached data
        if "author" in obj and isinstance(obj["author"], dict):
            # The presentation layer looks for author.displayName, so we ensure it exists
            # This provides a fallback if the field was somehow converted to snake_case
            if "display_name" in obj["author"] and "displayName" not in obj["author"]:
                obj["author"]["displayName"] = obj["author"]["display_name"]
        
        # Similar fallbacks for other critical fields used by the presentation layer
        # These ensure the fields are available regardless of naming convention changes
        if "time_spent" in obj and "timeSpent" not in obj:
            obj["timeSpent"] = obj["time_spent"]
        
        if "time_spent_seconds" in obj and "timeSpentSeconds" not in obj:
            obj["timeSpentSeconds"] = obj["time_spent_seconds"]
        
        return {k: _to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, tuple):
        return tuple(_to_json_serializable(item) for item in obj)
    
    # Return primitive types and anything else as-is
    return obj

def add_worklog(issue_key: str, time_spent: str, comment: Optional[str] = None) -> dict:
    """
    Add a worklog entry to an issue.
    
    Args:
        issue_key: The issue key (e.g., PROJECT-123)
        time_spent: Time spent in format like '1h 30m'
        comment: Optional comment for the worklog
        
    Returns:
        Dictionary representation of the created worklog
    """
    client = get_client()
    worklog_service = WorklogService(client)
    
    # Use the new model-based API
    worklog_model = worklog_service.add_worklog(issue_key, time_spent, comment)
    
    # Convert the model to a dictionary for backward compatibility
    return _to_json_serializable(worklog_model)

def list_worklogs(issue_key, refresh_cache=False):
    """
    Get worklogs for an issue.
    
    Args:
        issue_key: The issue key (e.g., PROJECT-123)
        refresh_cache: If True, bypass the cache and get fresh data
    
    Returns:
        list: Worklog entries for the issue
    """
    # Generate cache key for this specific issue
    cache_key = generate_cache_key(function="list_worklogs", issue_key=issue_key)
    
    # Try to get from cache unless refresh is requested
    if not refresh_cache:
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            logging.info(f"Using cached worklogs for {issue_key}")
            return cached_data
    
    # If we got here, we need to fetch fresh data
    logging.info(f"Fetching fresh worklogs for {issue_key}")
    client = get_client()
    worklog_service = WorklogService(client)
    worklogs = worklog_service.list_worklogs(issue_key)
    
    # Convert to JSON-serializable format before saving to cache
    serializable_worklogs = _to_json_serializable(worklogs)
    save_to_cache(cache_key, serializable_worklogs)
    
    return serializable_worklogs

def get_user_worklogs(username=None, start_date=None, end_date=None, debug_level='none', refresh_cache=False, timeout=30):
    """
    Get worklogs for a user.
    
    Args:
        username: The username (defaults to current user if None)
        start_date: Start date in format 'YYYY-MM-DD' (defaults to yesterday if None)
        end_date: End date in format 'YYYY-MM-DD' (defaults to today if None)
        debug_level: Debug output level ('none', 'error', 'info', 'verbose')
        refresh_cache: If True, bypass the cache and get fresh data
        timeout: Maximum execution time in seconds (default: 30)
        
    Returns:
        list: Worklog entries for the user
    """
    # Generate cache key based on function parameters
    cache_key = generate_cache_key(
        function="get_user_worklogs",
        username=username,
        start_date=start_date,
        end_date=end_date
    )
    
    # Try to get from cache unless refresh is requested
    if not refresh_cache:
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            if debug_level in ['info', 'verbose']:
                logging.info("Using cached worklog data")
            return cached_data
    
    # If we got here, we need to fetch fresh data - log this message first to match test expectations
    if debug_level in ['info', 'verbose']:
        logging.info("Fetching fresh worklog data")
    
    # Pass debug=True only for info or verbose levels
    client = get_client(debug=(debug_level in ['info', 'verbose']))
    # Add timeout parameter to client calls
    client.timeout = timeout
    worklog_service = WorklogService(client)
    
    # Add logging before service call to determine if it's hanging here
    if debug_level in ['info', 'verbose']:
        logging.info(f"Starting worklog service call with timeout={timeout}s")
    
    worklogs = worklog_service.get_user_worklogs(
        username=username,
        start_date=start_date,
        end_date=end_date,
        debug_level=debug_level
    )
    
    # Log successful completion of service call
    if debug_level in ['info', 'verbose']:
        logging.info(f"Completed worklog service call. Found {len(worklogs)} worklogs.")
    
    # Convert to JSON-serializable format before saving to cache
    serializable_worklogs = _to_json_serializable(worklogs)
    save_to_cache(cache_key, serializable_worklogs)
    
    return serializable_worklogs
