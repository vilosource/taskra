"""Issue management functionality."""

import logging
from typing import Dict, List, Any, Optional, cast

from ..api.services.issues import IssuesService
from ..api.models.issue import Issue, IssueCreate
from ..api.client import get_client
from ..utils.cache import generate_cache_key, get_from_cache, save_to_cache
from ..utils.serialization import to_serializable

# Define a type alias for backward compatibility
IssueDict = Dict[str, Any]

def get_issue(issue_key: str, refresh_cache: bool = False) -> IssueDict:
    """
    Get an issue by key.
    
    Args:
        issue_key: The issue key (e.g., PROJECT-123)
        refresh_cache: If True, bypass the cache and get fresh data
        
    Returns:
        Dictionary representation of the issue (for backward compatibility)
    """
    # Generate cache key
    cache_key = generate_cache_key(function="get_issue", issue_key=issue_key)
    
    # Try to get from cache unless refresh is requested
    if not refresh_cache:
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            logging.info(f"Using cached issue data for {issue_key}")
            return cached_data
    
    # If we got here, we need to fetch fresh data
    logging.info(f"Fetching fresh issue data for {issue_key}")
    client = get_client()
    issue_service = IssuesService(client)
    
    # Get the issue model from the service
    issue_model = issue_service.get_issue(issue_key)
    
    # Convert to serializable format for caching and backward compatibility
    serializable_issue = to_serializable(issue_model)
    save_to_cache(cache_key, serializable_issue)
    
    return serializable_issue

def create_issue(project_key, summary, description, issue_type="Task"):
    """
    Create a new issue.
    
    Args:
        project_key: The key of the project
        summary: Issue summary
        description: Issue description
        issue_type: Type of issue (default: Task)
        
    Returns:
        dict: Created issue data
    """
    # Get the client and use the IssuesService
    client = get_client()
    issues_service = IssuesService(client)
    return issues_service.create_issue(
        project_key=project_key,
        summary=summary,
        description=description,
        issue_type=issue_type
    )

def get_issue_comments(issue_key, get_all=True):
    """
    Get comments for a specific issue.
    
    Args:
        issue_key: The JIRA issue key (e.g., PROJECT-123)
        get_all: If True, retrieve all comments
        
    Returns:
        list: Issue comments
    """
    client = get_client()
    issues_service = IssuesService(client)
    return issues_service.get_comments(issue_key, get_all=get_all)
