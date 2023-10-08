"""Comment service for interacting with Jira comments API."""

from typing import Dict, List, Any, Optional, Union
from ..models.comment import Comment, CommentCreate, CommentList
from ...utils.serialization import to_serializable
from .base import BaseService

class CommentsService(BaseService):
    """Service for interacting with Jira comments API."""
    
    def get_comment(self, issue_key: str, comment_id: str) -> Comment:
        """
        Get a specific comment by ID.
        
        Args:
            issue_key: The issue key (e.g., 'PROJECT-123')
            comment_id: The comment ID
            
        Returns:
            Comment model
        """
        endpoint = self._get_endpoint(f"issue/{issue_key}/comment/{comment_id}")
        response = self.client.get(endpoint)
        return Comment.from_api(response)
    
    def list_comments(self, issue_key: str, start_at: int = 0, 
                     max_results: int = 50, get_all: bool = False) -> List[Comment]:
        """
        List comments for an issue.
        
        Args:
            issue_key: The issue key (e.g., 'PROJECT-123')
            start_at: Index of the first comment to return
            max_results: Maximum number of comments to return per request
            get_all: Whether to fetch all comments (multiple requests if needed)
            
        Returns:
            List of Comment models
        """
        if get_all:
            return self._get_all_comments(issue_key)
        
        # Make API request
        endpoint = self._get_endpoint(f"issue/{issue_key}/comment")
        params = {"startAt": start_at, "maxResults": max_results}
        response = self.client.get(endpoint, params=params)
        
        # Convert to CommentList model
        comment_list = CommentList.from_api(response)
        
        return comment_list.comments
    
    def _get_all_comments(self, issue_key: str, max_results_per_page: int = 50) -> List[Comment]:
        """
        Get all comments for an issue by handling pagination.
        
        Args:
            issue_key: The issue key
            max_results_per_page: Max results per API request
            
        Returns:
            Complete list of all Comment models
        """
        all_comments = []
        start_at = 0
        total = None
        
        while total is None or start_at < total:
            # Make API request
            endpoint = self._get_endpoint(f"issue/{issue_key}/comment")
            params = {"startAt": start_at, "maxResults": max_results_per_page}
            response = self.client.get(endpoint, params=params)
            
            # Convert to CommentList model
            comment_list = CommentList.from_api(response)
            comments = comment_list.comments
            
            # Add comments to result list
            all_comments.extend(comments)
            
            if total is None:
                total = comment_list.total
            
            # Update the start_at parameter for the next page
            start_at += len(comments)
            
            # If we got fewer results than requested, we're done
            if len(comments) < max_results_per_page:
                break
        
        return all_comments
    
    def add_comment(self, issue_key: str, body: str, 
                   visibility_type: Optional[str] = None, 
                   visibility_value: Optional[str] = None) -> Comment:
        """
        Add a comment to an issue.
        
        Args:
            issue_key: The issue key (e.g., 'PROJECT-123')
            body: Comment text content
            visibility_type: Optional visibility restriction type (e.g., 'group', 'role')
            visibility_value: Optional value for the visibility type
            
        Returns:
            Created Comment model
        """
        # Create the comment create model
        comment_create = CommentCreate(
            body=body
        )
        
        # Add visibility if specified
        if visibility_type and visibility_value:
            from ..models.comment import CommentVisibility
            comment_create.visibility = CommentVisibility(
                type=visibility_type,
                value=visibility_value
            )
        
        # Convert to API payload
        payload = comment_create.to_api_payload()
        
        # Send request
        endpoint = self._get_endpoint(f"issue/{issue_key}/comment")
        response = self.client.post(endpoint, json=payload)
        
        # Convert response to Comment model
        return Comment.from_api(response)
