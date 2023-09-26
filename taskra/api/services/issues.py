"""Issue service for interacting with Jira issues API."""

from typing import Dict, List, Any, Optional, Union
from ..models.issue import Issue, IssueFields, IssueCreate
from ...utils.serialization import to_serializable
from .base import BaseService

class IssuesService(BaseService):  # Renamed from IssueService to IssuesService
    """Service for interacting with Jira issues API."""
    
    def get_issue(self, issue_key: str) -> Issue:
        """
        Get an issue by key.
        
        Args:
            issue_key: Issue key (e.g., 'PROJECT-123')
            
        Returns:
            Issue model
        """
        endpoint = self._get_endpoint(f"issue/{issue_key}")
        response = self.client.get(endpoint)
        return Issue.from_api(response)
    
    def search_issues(self, jql: str, max_results: int = 50) -> List[Issue]:
        """
        Search for issues using JQL.
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results to return
            
        Returns:
            List of Issue models
        """
        endpoint = self._get_endpoint("search")
        params = {
            "jql": jql,
            "maxResults": max_results
        }
        response = self.client.get(endpoint, params=params)
        issues_data = response.get("issues", [])
        return [Issue.from_api(issue_data) for issue_data in issues_data]
        
    def get_comments(self, issue_key: str, start_at: int = 0, 
                    max_results: int = 50, get_all: bool = True) -> List[Dict[str, Any]]:
        """
        Get comments for an issue.
        
        Args:
            issue_key: Issue key (e.g., 'PROJECT-123')
            start_at: Index of first comment to return
            max_results: Maximum number of comments to return per request
            get_all: Whether to fetch all comments (multiple requests if needed)
            
        Returns:
            List of comment dictionaries
        """
        if get_all:
            return self._get_all_comments(issue_key, max_results)
            
        # Make API request
        endpoint = self._get_endpoint(f"issue/{issue_key}/comment")
        params = {"startAt": start_at, "maxResults": max_results}
        response = self.client.get(endpoint, params=params)
        
        # Extract comments from response
        return response.get("comments", [])
    
    def _get_all_comments(self, issue_key: str, max_results_per_page: int = 50) -> List[Dict[str, Any]]:
        """
        Get all comments for an issue by handling pagination.
        
        Args:
            issue_key: The issue key
            max_results_per_page: Max results per API request
            
        Returns:
            Complete list of all comments
        """
        all_comments = []
        start_at = 0
        total = None
        
        while total is None or start_at < total:
            # Make API request
            endpoint = self._get_endpoint(f"issue/{issue_key}/comment")
            params = {"startAt": start_at, "maxResults": max_results_per_page}
            response = self.client.get(endpoint, params=params)
            
            # Get comments and pagination info
            comments = response.get("comments", [])
            if total is None:
                total = response.get("total", 0)
            
            # Add comments to result list
            all_comments.extend(comments)
            
            # Update the start_at parameter for the next page
            start_at += len(comments)
            
            # If we got fewer results than requested, we're done
            if len(comments) < max_results_per_page:
                break
        
        return all_comments

    def create_issue(self, project_key: str, summary: str, 
                    description: Optional[str] = None,
                    issue_type: str = "Task") -> Issue:
        """
        Create a new issue.
        
        Args:
            project_key: The project key
            summary: Issue summary
            description: Issue description
            issue_type: Type of issue (default: Task)
            
        Returns:
            Issue model for the created issue
        """
        # Create the issue create model
        issue_create = IssueCreate(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type=issue_type
        )
        
        # Convert to API payload
        payload = issue_create.to_api_payload()
        
        # Send request
        endpoint = self._get_endpoint("issue")
        response = self.client.post(endpoint, json=payload)
        
        # If successful, get the created issue
        if "id" in response or "key" in response:
            issue_key = response.get("key")
            return self.get_issue(issue_key)
            
        # If we got here, something went wrong but the API didn't raise an error
        raise ValueError(f"Failed to create issue: {response}")

# Create an alias for backward compatibility
IssueService = IssuesService  # Backward compatibility alias
