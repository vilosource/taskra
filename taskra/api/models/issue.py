"""Models for Jira issues."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class IssueType(BaseModel):
    """Issue type model."""
    
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = Field(None, alias="iconUrl")
    
    model_config = ConfigDict(populate_by_name=True)


class StatusCategory(BaseModel):
    """Status category model."""
    
    id: int
    key: str
    name: str
    color_name: Optional[str] = Field(None, alias="colorName")


class Status(BaseModel):
    """Issue status model."""
    
    id: str
    name: str
    description: Optional[str] = None
    status_category: Optional[StatusCategory] = Field(None, alias="statusCategory")
    
    model_config = ConfigDict(populate_by_name=True)


class User(BaseModel):
    """Basic user information."""
    
    account_id: str = Field(..., alias="accountId")
    display_name: str = Field(..., alias="displayName")
    email_address: Optional[str] = Field(None, alias="emailAddress")
    active: Optional[bool] = None
    
    model_config = ConfigDict(populate_by_name=True)


class DocNode(BaseModel):
    """Document node for Atlassian Document Format."""
    
    type: str
    content: Optional[List[Any]] = None
    text: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")


class Document(BaseModel):
    """Atlassian Document Format model."""
    
    type: str = "doc"
    version: int = 1
    content: List[DocNode]


class TextContent(BaseModel):
    """Text content for simple descriptions."""
    
    text: str


class IssueSummary(BaseModel):
    """Basic issue information."""
    
    id: str
    key: str
    self: str


class IssueFields(BaseModel):
    """Issue fields model."""
    
    summary: str
    description: Optional[Union[Document, TextContent, Dict[str, Any]]] = None
    status: Optional[Status] = None
    assignee: Optional[User] = None
    reporter: Optional[User] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    issue_type: Optional[IssueType] = Field(None, alias="issuetype")
    priority: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(populate_by_name=True, extra="allow")  # Allow extra fields returned by the API


class Issue(IssueSummary):
    """Detailed issue model."""
    
    fields: IssueFields
    
    model_config = ConfigDict(populate_by_name=True)


class ProjectRef(BaseModel):
    """Project reference for creating issues."""
    
    key: str


class IssueTypeRef(BaseModel):
    """Issue type reference for creating issues."""
    
    id: str


class DescriptionContent(BaseModel):
    """Content for description when creating an issue."""
    
    type: str = "paragraph"
    content: List[Dict[str, str]]


class DescriptionDoc(BaseModel):
    """Description document for creating an issue."""
    
    type: str = "doc"
    version: int = 1
    content: List[DescriptionContent]


class IssueCreateFields(BaseModel):
    """Fields for creating a new issue."""
    
    project: ProjectRef
    summary: str
    issuetype: IssueTypeRef
    description: Optional[DescriptionDoc] = None
    
    model_config = ConfigDict(populate_by_name=True)


class IssueCreate(BaseModel):
    """Model for creating a new issue."""
    
    fields: IssueCreateFields
    
    @classmethod
    def from_simple(cls, project_key: str, summary: str, description: str, issue_type_id: str = "10001"):
        """
        Create an IssueCreate instance from simple parameters.
        
        Args:
            project_key: The project key
            summary: Issue summary
            description: Plain text description
            issue_type_id: The issue type ID (default is "10001" for Task)
            
        Returns:
            IssueCreate instance
        """
        content = [DescriptionContent(
            content=[{"type": "text", "text": description}]
        )]
        
        return cls(
            fields=IssueCreateFields(
                project=ProjectRef(key=project_key),
                summary=summary,
                issuetype=IssueTypeRef(id=issue_type_id),
                description=DescriptionDoc(content=content) if description else None
            )
        )
