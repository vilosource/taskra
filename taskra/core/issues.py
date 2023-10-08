"""Core issues module for interacting with Jira issues."""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from ..api.client import get_jira_client  # Changed from get_client to get_jira_client
from ..api.services.issues import IssuesService
from ..api.models.issue import Issue, IssueCreate, IssueFields

logger = logging.getLogger(__name__)

def get_issue(issue_key: str) -> Dict[str, Any]:
    """
    Get an issue by key.
    
    Args:
        issue_key: Issue key (e.g., 'PROJECT-123')
        
    Returns:
        Issue data as a dictionary
    """
    client = get_jira_client()
    service = IssuesService(client)
    
    # Get the issue as a model
    issue_model = service.get_issue(issue_key)
    
    # Convert to dictionary for backward compatibility
    return issue_model.model_dump(by_alias=True)

def create_issue(
    project_key: str,
    summary: str,
    description: Optional[str] = None,
    issue_type: str = "Task"
) -> Dict[str, Any]:
    """
    Create a new issue.
    
    Args:
        project_key: Project key
        summary: Issue summary
        description: Issue description
        issue_type: Type of issue (default: Task)
        
    Returns:
        Created issue data
    """
    client = get_jira_client()
    service = IssuesService(client)
    
    # Create the issue
    issue_model = service.create_issue(
        project_key=project_key,
        summary=summary,
        description=description,
        issue_type=issue_type
    )
    
    # Convert to dictionary for backward compatibility
    return issue_model.model_dump(by_alias=True)

def get_issue_comments(issue_key: str, get_all: bool = True) -> List[Dict[str, Any]]:
    """
    Get comments for an issue.
    
    Args:
        issue_key: Issue key (e.g., 'PROJECT-123')
        get_all: Whether to fetch all comments or just the first page
        
    Returns:
        List of comments
    """
    client = get_jira_client()
    service = IssuesService(client)
    
    return service.get_comments(issue_key, get_all=get_all)

def search_issues(
    jql: str,
    max_results: int = 50,
    fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Search for issues using JQL.
    
    Args:
        jql: JQL query string
        max_results: Maximum number of results to return
        fields: List of field names to include
        
    Returns:
        Search results
    """
    client = get_jira_client()
    service = IssuesService(client)
    
    # Perform the search
    results = service.search_issues(
        jql=jql,
        max_results=max_results,
        fields=fields
    )
    
    # Convert to dictionary for backward compatibility
    return results.model_dump(by_alias=True)
