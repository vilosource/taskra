"""Worklog management functionality."""

from ..api.services.worklogs import WorklogService
from ..api.client import get_client

def add_worklog(issue_key, time_spent, comment=None):
    """
    Add a worklog to an issue.
    
    Args:
        issue_key: The JIRA issue key
        time_spent: Time spent (e.g., "2h 30m")
        comment: Optional comment
        
    Returns:
        dict: Worklog data
    """
    client = get_client()
    worklog_service = WorklogService(client)
    return worklog_service.add_worklog(
        issue_key=issue_key,
        time_spent=time_spent,
        comment=comment
    )

def list_worklogs(issue_key):
    """
    List worklogs for an issue.
    
    Args:
        issue_key: The JIRA issue key
        
    Returns:
        list: Worklog entries
    """
    client = get_client()
    worklog_service = WorklogService(client)
    return worklog_service.list_worklogs(issue_key)

def get_user_worklogs(username=None, start_date=None, end_date=None, debug_level='none'):
    """
    Get worklogs for a user.
    
    Args:
        username: The username (defaults to current user if None)
        start_date: Start date in format 'YYYY-MM-DD' (defaults to yesterday if None)
        end_date: End date in format 'YYYY-MM-DD' (defaults to today if None)
        debug_level: Debug output level ('none', 'error', 'info', 'verbose')
        
    Returns:
        list: Worklog entries for the user
    """
    # Pass debug=True only for info or verbose levels
    client = get_client(debug=(debug_level in ['info', 'verbose']))
    worklog_service = WorklogService(client)
    return worklog_service.get_user_worklogs(
        username=username,
        start_date=start_date,
        end_date=end_date,
        debug_level=debug_level
    )
