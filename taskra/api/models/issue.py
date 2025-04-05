"""Models for Jira issues."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import Field, field_validator

from .base import BaseJiraModel, ApiResource, TimestampedResource
from .user import User

class IssueType(BaseJiraModel):
    """
    Represents a Jira issue type.
    
    This class models the different types of issues in Jira, such as Bug, Task, Epic, and Story.
    Issue types are fundamental to Jira's workflow as they help categorize and organize work items.
    Each issue type has its own workflow, fields, and behaviors, and this model captures the
    essential information needed to identify and display them appropriately.
    
    This model includes validation for all required fields and provides optional fields
    for additional metadata that might be available from some API endpoints.
    """
    
    id: str = Field(..., description="Issue type ID")
    name: str = Field(..., description="Issue type name (e.g., 'Bug', 'Task')")
    description: Optional[str] = Field(None, description="Issue type description")
    icon_url: Optional[str] = Field(None, alias="iconUrl", description="URL to the issue type icon")
    subtask: bool = Field(False, description="Whether this is a subtask type")

class IssueStatus(BaseJiraModel):
    """
    Represents a Jira issue status.
    
    This class models the status of an issue in Jira's workflow, such as "To Do", "In Progress",
    or "Done". Status is a key part of tracking an issue through its lifecycle, and this model 
    captures the essential information about a status as well as its category (which determines 
    how it's handled in reporting and visualization).
    
    Default values are provided for the most common status ("To Do") to ensure graceful handling
    of missing data in API responses.
    """
    
    id: str = Field(default="1", description="Status ID") # Default value added
    name: str = Field(default="To Do", description="Status name (e.g., 'To Do', 'In Progress')")
    description: Optional[str] = Field(None, description="Status description")
    status_category: Optional[Dict[str, Any]] = Field(None, alias="statusCategory")

class IssueFields(BaseJiraModel):
    """
    Fields for an issue.
    
    This class represents the dynamic fields section of a Jira issue. The fields section
    contains most of the detailed information about an issue, including its summary,
    description, status, type, assignee, and many other attributes. Since Jira allows
    for custom fields and different configurations across instances, this model is designed
    to be flexible and handle varying field structures.
    
    The class includes utility methods for safely extracting commonly needed information
    with appropriate fallbacks for different data structures that might be returned by
    the API, ensuring robustness when dealing with different Jira configurations.
    """
    summary: Optional[str] = None
    # Handle description as either string or ADF object
    description: Optional[Union[str, Dict[str, Any]]] = None
    status: Optional[IssueStatus] = None
    issue_type: Optional[IssueType] = Field(None, alias="issuetype")
    assignee: Optional[User] = None
    priority: Optional[Dict[str, Any]] = None  # Priority can have a complex structure
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    
    # Allow any additional fields to be stored dynamically
    model_config = {
        "extra": "allow",
    }
    
    def get_status_name(self) -> str:
        """
        Get status name with fallback.
        
        This method extracts the status name from the status field, with appropriate
        fallbacks for different data structures. It handles both object and dictionary
        representations of the status field.
        
        Returns:
            The name of the issue's status, or "Unknown" if not available
        """
        if self.status and hasattr(self.status, "name"):
            return self.status.name
        # Direct string access as fallback
        if isinstance(self.status, dict) and "name" in self.status:
            return self.status["name"]
        return "Unknown"
        
    def get_assignee_name(self) -> str:
        """
        Get assignee display name with fallback.
        
        This method extracts the assignee's name from the assignee field, with appropriate
        fallbacks. It handles various representational formats that might be returned by
        different API endpoints.
        
        Returns:
            The display name of the assigned user, or "Unassigned" if no assignee
        """
        if self.assignee and hasattr(self.assignee, "display_name"):
            return self.assignee.display_name
        if self.assignee and hasattr(self.assignee, "emailAddress"):
            return self.assignee.emailAddress
        # Direct dictionary access as fallback
        if isinstance(self.assignee, dict):
            return self.assignee.get("displayName") or self.assignee.get("emailAddress", "Unassigned")
        return "Unassigned"
        
    def get_priority_name(self) -> str:
        """
        Get priority name with fallback.
        
        This method extracts the priority name from the priority field, with appropriate
        fallback. Priority is often represented as a complex object in Jira.
        
        Returns:
            The name of the priority level, or "Unknown" if not available
        """
        if isinstance(self.priority, dict) and "name" in self.priority:
            return self.priority["name"]
        return "Unknown"

class Issue(ApiResource):
    """
    Represents a complete Jira issue.
    
    This class is the primary model for Jira issues, representing the full issue data structure
    as returned by the Jira API. It contains key identifiers (id, key), a self-reference URL,
    and the fields object which contains most of the issue's attributes.
    
    This class extends ApiResource to inherit standard functionality for Jira API resources.
    It serves as the foundation for many operations in the codebase, as issues are central to
    Jira's functionality.
    
    API Endpoint: /rest/api/3/issue/{issueIdOrKey}
    """
    id: str
    key: str
    self_url: str = Field(..., alias="self")
    fields: IssueFields
    
    @property
    def self(self) -> str:
        """
        Property getter for backward compatibility.
        
        Returns:
            The self URL string
        """
        return self.self_url

class IssueSummary(BaseJiraModel):
    """
    Summary representation of a Jira issue.
    
    This class provides a lightweight representation of a Jira issue, containing only the
    essential information needed for listing and reference purposes. It is designed to be
    more efficient than the full Issue model when only basic information is needed, such as
    in search results, dropdown lists, or references from other objects.
    
    The class includes a utility method to construct a summary from a full Issue object,
    making it easy to create consistent summarized representations.
    """
    
    id: str = Field(..., description="Issue ID")
    key: str = Field(..., description="Issue key (e.g., 'PROJECT-123')")
    summary: str = Field(..., description="Issue summary")
    issue_type: Optional[str] = Field(None, alias="issueType", description="Type of issue")
    status: Optional[str] = Field(None, description="Issue status")
    assignee: Optional[str] = Field(None, description="Assigned user's display name")
    
    @classmethod
    def from_issue(cls, issue: Issue) -> "IssueSummary":
        """
        Create a summary from a full Issue model.
        
        This method extracts the key information from a full Issue object to create
        a lightweight summary representation suitable for listing and references.
        
        Args:
            issue: The full Issue object
            
        Returns:
            An IssueSummary instance containing the essential information
        """
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
    
    This class provides a specialized model for creating new issues in Jira. It focuses
    on the essential fields needed to create a valid issue, with optional fields for additional
    customization. The model includes a method to convert its data into the specific format
    expected by the Jira API, handling the complex nesting and formatting requirements.
    
    This model simplifies issue creation by abstracting away the complex structure of the
    Jira API request payload, allowing clients to provide just the necessary information
    in a more straightforward format.
    
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

class IssueSearchResults(BaseJiraModel):
    """
    Search results from the Jira search API.
    
    This class models the paginated results returned by Jira's search API. It contains
    metadata about the search (pagination information, total results) along with the actual
    list of issues matching the search criteria. This structure is used when searching for
    issues using JQL (Jira Query Language) or other search parameters.
    
    The model handles pagination fields consistently with other paginated resources in the
    Jira API, making it easier to implement features like result pagination and iterating
    through large result sets.
    
    API Endpoint: /rest/api/3/search
    """
    expand: Optional[str] = None
    start_at: int = Field(..., alias="startAt")
    max_results: int = Field(..., alias="maxResults")
    total: int
    issues: List[Issue]
