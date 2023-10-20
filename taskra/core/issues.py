"""Issue management functionality."""

from ..api.services.issues import IssuesService
from ..api.client import get_client

def get_issue(issue_key):
    """
    Get information about a specific issue.
    
    Args:
        issue_key: The JIRA issue key (e.g., PROJECT-123)
        
    Returns:
        dict: Issue data
    """
    # Get the client and use the IssuesService
    client = get_client()  # This would get a configured client
    issues_service = IssuesService(client)
    return issues_service.get_issue(issue_key)

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
