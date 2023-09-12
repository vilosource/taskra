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
    
    def get_comments(self, issue_key: str, start_at: int = 0, max_results: int = 50, 
                     get_all: bool = True) -> List[Dict[str, Any]]:
        """
        Get comments for a specific issue.
        
        Args:
            issue_key: The issue key (e.g., PROJECT-123)
            start_at: Index of the first comment to return (for pagination)
            max_results: Maximum number of comments to return per request
            get_all: If True, retrieve all comments by handling pagination automatically
            
        Returns:
            List of comment data dictionaries
        """
        if get_all:
            return self._get_all_comments(issue_key, max_results_per_page=max_results)
        
        params = {
            "startAt": start_at,
            "maxResults": max_results
        }
        
        response = self.client.get(self._get_endpoint(f"issue/{issue_key}/comment"), params=params)
        return response.get("comments", [])
    
    def _get_all_comments(self, issue_key: str, max_results_per_page: int = 50) -> List[Dict[str, Any]]:
        """
        Get all comments for an issue by handling pagination.
        
        Args:
            issue_key: The issue key
            max_results_per_page: Maximum number of comments to return per request
            
        Returns:
            Complete list of comment data dictionaries
        """
        all_comments = []
        start_at = 0
        total = None
        
        while total is None or start_at < total:
            params = {
                "startAt": start_at,
                "maxResults": max_results_per_page
            }
            
            response = self.client.get(self._get_endpoint(f"issue/{issue_key}/comment"), params=params)
            comments = response.get("comments", [])
            all_comments.extend(comments)
            
            # If this is the first request, get the total count
            if total is None:
                total = response.get("total", 0)
            
            # Update the start_at parameter for the next page
            start_at += len(comments)
            
            # If we got fewer results than requested, we're done
            if len(comments) < max_results_per_page:
                break
        
        return all_comments

    def search_issues(self, jql: str, fields: Optional[List[str]] = None, 
                      start_at: int = 0, max_results: int = 50) -> Dict[str, Any]:
        """
        Search for issues using JQL.
        
        Args:
            jql: JQL query string
            fields: List of fields to include
            start_at: Index of the first result
            max_results: Maximum number of results to return
            
        Returns:
            Search results
        """
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results
        }
        
        if fields:
            params["fields"] = ",".join(fields)
        
        response = self.client.get(self._get_endpoint("search"), params=params)
        return response
    
    def search_all_issues(self, jql: str, fields: Optional[List[str]] = None,
                          max_results_per_page: int = 50) -> List[Dict[str, Any]]:
        """
        Search for all issues matching JQL, handling pagination.
        
        Args:
            jql: JQL query string
            fields: List of fields to include
            max_results_per_page: Maximum results per request
            
        Returns:
            List of all matching issues
        """
        all_issues = []
        start_at = 0
        total = None
        
        while total is None or start_at < total:
            response = self.search_issues(
                jql=jql, 
                fields=fields, 
                start_at=start_at, 
                max_results=max_results_per_page
            )
            
            issues = response.get("issues", [])
            all_issues.extend(issues)
            
            # If this is the first request, get the total count
            if total is None:
                total = response.get("total", 0)
            
            # Update the start_at parameter for the next page
            start_at += len(issues)
            
            # If we got fewer results than requested, we're done
            if len(issues) < max_results_per_page:
                break
        
        return all_issues
