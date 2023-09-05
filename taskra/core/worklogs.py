"""Worklog management functionality."""

import logging
from ..api.services.worklogs import WorklogService
from ..api.client import get_client
from ..utils.cache import generate_cache_key, get_from_cache, save_to_cache

def add_worklog(issue_key, time_spent, comment=None):
    """Add a worklog entry to an issue."""
    client = get_client()
    worklog_service = WorklogService(client)
    return worklog_service.add_worklog(issue_key, time_spent, comment)

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
    
    # Save to cache for future use
    save_to_cache(cache_key, worklogs)
    
    return worklogs

def get_user_worklogs(username=None, start_date=None, end_date=None, debug_level='none', refresh_cache=False):
    """
    Get worklogs for a user.
    
    Args:
        username: The username (defaults to current user if None)
        start_date: Start date in format 'YYYY-MM-DD' (defaults to yesterday if None)
        end_date: End date in format 'YYYY-MM-DD' (defaults to today if None)
        debug_level: Debug output level ('none', 'error', 'info', 'verbose')
        refresh_cache: If True, bypass the cache and get fresh data
        
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
    
    # If we got here, we need to fetch fresh data
    if debug_level in ['info', 'verbose']:
        logging.info("Fetching fresh worklog data")
    
    # Pass debug=True only for info or verbose levels
    client = get_client(debug=(debug_level in ['info', 'verbose']))
    worklog_service = WorklogService(client)
    worklogs = worklog_service.get_user_worklogs(
        username=username,
        start_date=start_date,
        end_date=end_date,
        debug_level=debug_level
    )
    
    # Save to cache for future use
    save_to_cache(cache_key, worklogs)
    
    return worklogs
