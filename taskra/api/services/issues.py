"""Issues service for interacting with Jira issues API."""

from typing import Dict, List, Any, Optional

from .base import BaseService
from ..models.issue import Issue, IssueCreate


class IssuesService(BaseService):
    """Service for interacting with Jira issues API."""
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific issue.
        
        Args:
            issue_key: The issue key (e.g., PROJECT-123)
            
        Returns:
            Issue data dictionary
        """
        response = self.client.get(self._get_endpoint(f"issue/{issue_key}"))
        issue = Issue.model_validate(response)
        
        return issue.model_dump(by_alias=False)
    
    def create_issue(self, project_key: str, summary: str, 
                     description: Optional[str] = None, 
                     issue_type: str = "Task") -> Dict[str, Any]:
        """
        Create a new issue in a project.
        
        Args:
            project_key: The project key
            summary: Issue summary
            description: Issue description (optional)
            issue_type: Type of issue (default: Task)
            
        Returns:
            Created issue data dictionary
        """
        # For simplicity, we're assuming "10001" is the ID for a Task
        # In a real implementation, you would look up the issue type ID
        issue_type_id = "10001"  # This would typically be looked up
        
        issue_data = IssueCreate.from_simple(
            project_key=project_key,
            summary=summary,
            description=description or "",
            issue_type_id=issue_type_id
        )
        
        response = self.client.post(
            self._get_endpoint("issue"),
            json_data=issue_data.model_dump(by_alias=True)
        )
        
        return response
