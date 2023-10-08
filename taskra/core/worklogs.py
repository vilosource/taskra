"""Worklog management functionality."""

import logging
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any, Union
from ..api.services.worklogs import WorklogService
from ..api.client import get_client
from ..utils.cache import generate_cache_key, get_from_cache, save_to_cache

# Create a logger for this module
logger = logging.getLogger(__name__)

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
        
        # Explicitly copy issue_key and issue_summary if they exist as attributes
        if hasattr(obj, 'issue_key') and getattr(obj, 'issue_key', None):
            result['issueKey'] = getattr(obj, 'issue_key')
            result['issue_key'] = getattr(obj, 'issue_key')
            
        if hasattr(obj, 'issue_summary') and getattr(obj, 'issue_summary', None):
            result['issueSummary'] = getattr(obj, 'issue_summary')
            result['issue_summary'] = getattr(obj, 'issue_summary')
            
        # Process the result to handle datetime objects
        return _to_json_serializable(result)
    elif hasattr(obj, 'dict'):
        # For Pydantic v1
        # IMPORTANT: Same reasoning as above - preserve the original API field names
        result = obj.dict(by_alias=True)
        
        # Explicitly copy issue_key and issue_summary if they exist as attributes
        if hasattr(obj, 'issue_key') and getattr(obj, 'issue_key', None):
            result['issueKey'] = getattr(obj, 'issue_key')
            result['issue_key'] = getattr(obj, 'issue_key')
            
        if hasattr(obj, 'issue_summary') and getattr(obj, 'issue_summary', None):
            result['issueSummary'] = getattr(obj, 'issue_summary')
            result['issue_summary'] = getattr(obj, 'issue_summary')
            
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
        
        # Ensure issue key and summary are available in both formats
        if "issue_key" in obj and "issueKey" not in obj:
            obj["issueKey"] = obj["issue_key"]
        elif "issueKey" in obj and "issue_key" not in obj:
            obj["issue_key"] = obj["issueKey"]
            
        if "issue_summary" in obj and "issueSummary" not in obj:
            obj["issueSummary"] = obj["issue_summary"]
        elif "issueSummary" in obj and "issue_summary" not in obj:
            obj["issue_summary"] = obj["issueSummary"]
            
        # Check for nested issue structure and extract key if needed
        if not obj.get("issueKey") and not obj.get("issue_key"):
            if "issue" in obj and isinstance(obj["issue"], dict) and "key" in obj["issue"]:
                obj["issueKey"] = obj["issue"]["key"]
                obj["issue_key"] = obj["issue"]["key"]
                
                # Also extract summary if available
                if "fields" in obj["issue"] and "summary" in obj["issue"]["fields"]:
                    obj["issueSummary"] = obj["issue"]["fields"]["summary"]
                    obj["issue_summary"] = obj["issue"]["fields"]["summary"]
        
        return {k: _to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, tuple):
        return tuple(_to_json_serializable(item) for item in obj)
    
    # Return primitive types and anything else as-is
    return obj

def add_worklog(issue_key: str, time_spent: str, comment: Optional[str] = None, started: Optional[datetime] = None) -> dict:
    """
    Add a worklog entry to an issue.
    
    Args:
        issue_key: The issue key (e.g., PROJECT-123)
        time_spent: Time spent in format like '1h 30m'
        comment: Optional comment for the worklog
        started: Optional datetime when the work was started (defaults to now)
        
    Returns:
        Dictionary representation of the created worklog
    """
    logger.info(f"Adding worklog to issue {issue_key}")
    client = get_client()
    worklog_service = WorklogService(client)
    
    # Use the new model-based API
    worklog_model = worklog_service.add_worklog(issue_key, time_spent, comment, started)
    logger.debug(f"Worklog added successfully to {issue_key}")
    
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
            logger.info(f"Using cached worklogs for {issue_key}")
            return cached_data
    
    # If we got here, we need to fetch fresh data
    logger.info(f"Fetching fresh worklogs for {issue_key}")
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
        debug_level: Debug output level ('none', 'error', 'info', 'verbose') - deprecated, use logging instead
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
        logger.info("Checking cache for worklog data")
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            logger.info(f"Using cached worklog data ({len(cached_data)} entries)")
            return cached_data
    
    # If we got here, we need to fetch fresh data
    logger.info(f"Fetching fresh worklog data for {username or 'current user'}")
    logger.info(f"Date range: {start_date or 'yesterday'} to {end_date or 'today'}")
    
    # Get client without passing debug parameter
    client = get_client()
    # Add timeout parameter to client calls
    client.timeout = timeout
    worklog_service = WorklogService(client)
    
    # Add logging before service call
    logger.info(f"Starting worklog service call with timeout={timeout}s")
    worklogs = worklog_service.get_user_worklogs(
        username=username,
        start_date=start_date,
        end_date=end_date
    )
    
    # Log successful completion of service call
    logger.info(f"Completed worklog service call. Found {len(worklogs)} worklogs.")
    
    # Debug logging for the first worklog if available
    if worklogs and len(worklogs) > 0:
        first_worklog = worklogs[0]
        logger.debug(f"First worklog type: {type(first_worklog).__name__}")
        
        # Log all available fields to help diagnose the issue
        if hasattr(first_worklog, '__dict__'):
            logger.debug(f"First worklog fields: {first_worklog.__dict__.keys()}")
        elif hasattr(first_worklog, 'model_fields'):
            logger.debug(f"First worklog model fields: {first_worklog.model_fields.keys()}")
        
        # Check for issue field or issue_id field instead of issue_key
        if hasattr(first_worklog, 'issue'):
            logger.debug(f"First worklog has 'issue' field: {first_worklog.issue}")
        if hasattr(first_worklog, 'issue_id'):
            logger.debug(f"First worklog has 'issue_id' field: {first_worklog.issue_id}")
    
    # Convert to JSON-serializable format before saving to cache
    serializable_worklogs = _to_json_serializable(worklogs)
    
    # Debug the serialized data
    if serializable_worklogs and len(serializable_worklogs) > 0:
        logger.debug(f"First serialized worklog keys: {list(serializable_worklogs[0].keys())}")
    
    # Ensure issue keys are present in all worklogs
    for worklog in serializable_worklogs:
        # Try multiple possible field names for the issue key
        if 'issue' in worklog and isinstance(worklog['issue'], dict):
            # Extract from nested issue object
            if 'key' in worklog['issue']:
                worklog['issueKey'] = worklog['issue']['key']
                worklog['issue_key'] = worklog['issue']['key']
                
                # Also add summary if available
                if 'fields' in worklog['issue'] and 'summary' in worklog['issue']['fields']:
                    worklog['issueSummary'] = worklog['issue']['fields']['summary']
                    worklog['issue_summary'] = worklog['issue']['fields']['summary']
            elif 'id' in worklog['issue']:
                # If only ID is available, use that as a fallback
                worklog['issueKey'] = f"ID-{worklog['issue']['id']}"
                worklog['issue_key'] = f"ID-{worklog['issue']['id']}"
        
        # Check for issue_id field (common in some Jira API responses)
        elif 'issue_id' in worklog:
            worklog['issueKey'] = f"ID-{worklog['issue_id']}"
            worklog['issue_key'] = f"ID-{worklog['issue_id']}"
            
        # Check for issueId field (camelCase variant)
        elif 'issueId' in worklog:
            worklog['issueKey'] = f"ID-{worklog['issueId']}"
            worklog['issue_key'] = f"ID-{worklog['issueId']}"
    
    logger.info(f"Saving {len(serializable_worklogs)} worklogs to cache")
    save_to_cache(cache_key, serializable_worklogs)
    
    return serializable_worklogs
