"""Models for Jira issues."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import Field, field_validator

from .base import BaseJiraModel, ApiResource, TimestampedResource
from .user import User

class IssueType(BaseJiraModel):
    """Represents a Jira issue type."""
    
    id: str = Field(..., description="Issue type ID")
    name: str = Field(..., description="Issue type name (e.g., 'Bug', 'Task')")
    description: Optional[str] = Field(None, description="Issue type description")
    icon_url: Optional[str] = Field(None, alias="iconUrl", description="URL to the issue type icon")
    subtask: bool = Field(False, description="Whether this is a subtask type")

class IssueStatus(BaseJiraModel):
    """Represents a Jira issue status."""
    
    id: str = Field(default="1", description="Status ID") # Default value added
    name: str = Field(default="To Do", description="Status name (e.g., 'To Do', 'In Progress')")
    description: Optional[str] = Field(None, description="Status description")
    status_category: Optional[Dict[str, Any]] = Field(None, alias="statusCategory")

class IssueFields(BaseJiraModel):
    """Fields of a Jira issue."""
    
    summary: str = Field(..., description="Issue summary")
    description: Optional[Dict[str, Any]] = Field(None, description="Issue description in ADF format")
    issue_type: IssueType = Field(..., alias="issuetype", description="Issue type")
    status: IssueStatus = Field(default_factory=IssueStatus, description="Current issue status") # Default factory added
    assignee: Optional[User] = Field(None, description="User assigned to the issue")
    reporter: Optional[User] = Field(None, description="User who reported the issue")
    created: datetime = Field(default_factory=datetime.now, description="When the issue was created") # Default factory added
    updated: datetime = Field(default_factory=datetime.now, description="When the issue was last updated") # Default factory added
    # Add other fields as needed

class Issue(ApiResource):
    """
    Represents a Jira issue.
    
    API Endpoint: /rest/api/3/issue/{issueIdOrKey}
    """
    
    id: str = Field(..., description="Issue ID")
    key: str = Field(..., description="Issue key (e.g., 'PROJECT-123')")
    fields: IssueFields = Field(..., description="Issue fields")

class IssueSummary(BaseJiraModel):
    """
    Summary representation of a Jira issue.
    
    Used for lightweight listings and references.
    """
    
    id: str = Field(..., description="Issue ID")
    key: str = Field(..., description="Issue key (e.g., 'PROJECT-123')")
    summary: str = Field(..., description="Issue summary")
    issue_type: Optional[str] = Field(None, alias="issueType", description="Type of issue")
    status: Optional[str] = Field(None, description="Issue status")
    assignee: Optional[str] = Field(None, description="Assigned user's display name")
    
    @classmethod
    def from_issue(cls, issue: Issue) -> "IssueSummary":
        """Create a summary from a full Issue model."""
        return cls(
            id=issue.id,
            key=issue.key,
            summary=issue.fields.summary,
            issueType=issue.fields.issue_type.name if issue.fields.issue_type else None,
            status=issue.fields.status.name if issue.fields.status else None,
            assignee=issue.fields.assignee.display_name if issue.fields.assignee else None
        )

class IssueCreate(BaseJiraModel):
    """
    Model for creating a new issue.
    
    API Endpoint: POST /rest/api/3/issue
    """
    project_key: str = Field(..., description="Key of the project to create issue in")
    summary: str = Field(..., description="Issue summary")
    description: Optional[str] = Field(None, description="Issue description")
    issue_type: str = Field(..., description="Issue type name (e.g., 'Bug', 'Task')")
    assignee: Optional[str] = Field(None, description="Account ID of user to assign")
    
    def to_api_payload(self) -> Dict[str, Any]:
        """
        Convert to API-compatible payload format.
        
        Returns:
            Dictionary in the format expected by the Jira API
        """
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": self.summary,
                "issuetype": {"name": self.issue_type}
            }
        }
        
        if self.description:
            # Convert to Atlassian Document Format if it's a simple string
            payload["fields"]["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": self.description
                            }
                        ]
                    }
                ]
            }
            
        if self.assignee:
            payload["fields"]["assignee"] = {"accountId": self.assignee}
            
        return payload
