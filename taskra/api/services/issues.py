"""Issue service for interacting with Jira issues API."""

from typing import Dict, List, Any, Optional, Union
from ..models.issue import Issue, IssueFields, IssueCreate, IssueSearchResults
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
    
    def search_issues(
        self, 
        jql: str, 
        start_at: int = 0, 
        max_results: int = 50, 
        fields: Optional[List[str]] = None,
        debug: bool = False,
        **kwargs
    ) -> IssueSearchResults:
        """
        Search issues using JQL.
        
        Args:
            jql: JQL query string
            start_at: Index of the first result to return (for pagination)
            max_results: Maximum number of results to return
            fields: List of field names to include in the response
            debug: Enable debug output
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            IssueSearchResults object containing the search results
        """
        # Safety check - don't send empty JQL
        if not jql:
            if debug:
                print("[DEBUG] Empty JQL query, using default ordering")
            jql = "order by created DESC"
        
        # Make sure project and status values are properly quoted
        jql = self._ensure_proper_jql_quoting(jql)
        
        if debug:
            print(f"[DEBUG] Final JQL query: {jql}")
            
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
        }
        
        if fields is not None:
            params["fields"] = ",".join(fields)
            
        # Add any additional parameters
        params.update({k: v for k, v in kwargs.items() if v is not None})
        
        if debug:
            print(f"[DEBUG] Search parameters: {params}")
        
        try:
            response = self.client.get("/rest/api/3/search", params=params)
            
            # Check if response is already a dict (meaning the client might have already parsed it)
            if isinstance(response, dict):
                response_data = response
            else:
                response_data = response.json()
            
            # Debug the structure of the first issue if requested
            if debug and "issues" in response_data and response_data["issues"]:
                from ...utils.debug import dump_model_structure
                print("\nDEBUG: First issue structure:")
                first_issue = response_data["issues"][0]
                dump_model_structure(first_issue)

            # Create model instance
            return IssueSearchResults.model_validate(response_data)
        except Exception as e:
            if debug:
                print(f"[DEBUG] Error searching issues: {str(e)}")
                if hasattr(e, 'response') and hasattr(e.response, 'text'):
                    print(f"[DEBUG] Response content: {e.response.text}")
            # Re-raise the exception to be handled by the caller
            raise
    
    def _ensure_proper_jql_quoting(self, jql: str) -> str:
        """
        Ensure JQL values are properly quoted.
        
        Args:
            jql: Original JQL query string
            
        Returns:
            Properly quoted JQL query
        """
        # This is a simple implementation. For production use,
        # a more robust JQL parser would be preferred.
        
        # Look for project = X without quotes and add them
        import re
        jql = re.sub(r'project\s*=\s*([^"\s]+)', r'project = "\1"', jql)
        
        # Handle status in (...) without quotes
        def quote_status_values(match):
            values = match.group(1).split(',')
            quoted_values = [f'"{v.strip()}"' if not v.strip().startswith('"') else v.strip() for v in values]
            return f'status in ({", ".join(quoted_values)})'
        
        jql = re.sub(r'status\s+in\s*\(([^)]+)\)', quote_status_values, jql)
        
        return jql
        
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
