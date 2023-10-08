"""Models for Jira comments."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import Field, field_validator

from .base import BaseJiraModel, ApiResource, TimestampedResource
from .user import User

class CommentVisibility(BaseJiraModel):
    """Visibility settings for comments."""
    
    type: str = Field(..., description="Type of visibility restriction (e.g., 'group', 'role')")
    value: str = Field(..., description="Value for the visibility type (group name, role name)")


class Comment(TimestampedResource):
    """
    Model for a Jira issue comment.
    
    API Endpoint: /rest/api/3/issue/{issueIdOrKey}/comment/{id}
    """
    
    id: str = Field(..., description="Comment ID")
    author: User = Field(..., description="User who created the comment")
    body: Union[str, Dict[str, Any]] = Field(..., description="Comment content (text or Atlassian Document Format)")
    update_author: Optional[User] = Field(None, alias="updateAuthor", description="User who last updated the comment")
    jsd_public: Optional[bool] = Field(None, alias="jsdPublic", description="Whether the comment is public in Service Desk")
    visibility: Optional[CommentVisibility] = Field(None, description="Comment visibility restrictions")
    
    # Properties for normalized access to content
    @property
    def text_content(self) -> str:
        """
        Extract plain text content from the comment body.
        
        Returns:
            Plain text representation of the comment
        """
        if isinstance(self.body, str):
            return self.body
        
        # Handle Atlassian Document Format (ADF)
        if isinstance(self.body, dict):
            return self._extract_text_from_adf(self.body)
        
        return str(self.body)
    
    def _extract_text_from_adf(self, adf_content: Dict[str, Any]) -> str:
        """Extract plain text from Atlassian Document Format."""
        text_parts = []
        
        # Process content array if it exists
        content_items = adf_content.get("content", [])
        for item in content_items:
            # Direct text node
            if item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            
            # Paragraph, heading, etc. with nested content
            elif "content" in item and isinstance(item["content"], list):
                for child in item["content"]:
                    if isinstance(child, dict):
                        # Recursively extract text from child nodes
                        if child.get("type") == "text":
                            text_parts.append(child.get("text", ""))
                        elif "content" in child:
                            text_parts.append(self._extract_text_from_adf(child))
        
        return " ".join(text_parts)


class CommentCreate(BaseJiraModel):
    """
    Model for creating a new comment.
    
    API Endpoint: POST /rest/api/3/issue/{issueIdOrKey}/comment
    """
    
    body: str = Field(..., description="Comment text content")
    visibility: Optional[CommentVisibility] = Field(None, description="Comment visibility")
    
    def to_api_payload(self) -> Dict[str, Any]:
        """
        Convert to API-compatible payload format.
        
        Returns:
            Dictionary in the format expected by the Jira API
        """
        # Convert simple text to Atlassian Document Format
        adf_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": self.body
                        }
                    ]
                }
            ]
        }
        
        payload = {
            "body": adf_body
        }
        
        # Add visibility if specified
        if self.visibility:
            payload["visibility"] = self.visibility.model_dump(by_alias=True)
            
        return payload


class CommentList(BaseJiraModel):
    """
    List of comments from the Jira API.
    
    API Endpoint: GET /rest/api/3/issue/{issueIdOrKey}/comment
    """
    
    comments: List[Comment] = Field(..., description="List of comments")
    start_at: int = Field(..., alias="startAt", description="Index of the first item")
    max_results: int = Field(..., alias="maxResults", description="Maximum results per page")
    total: int = Field(..., description="Total number of comments")
