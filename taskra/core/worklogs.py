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
