"""Models for Jira projects."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ProjectCategory(BaseModel):
    """Project category model."""
    
    id: str
    name: str
    description: Optional[str] = None


class AvatarUrls(BaseModel):
    """Avatar URLs model with different sizes."""
    
    x16: str = Field(..., alias="16x16")
    x24: str = Field(..., alias="24x24")
    x32: str = Field(..., alias="32x32")
    x48: str = Field(..., alias="48x48")


class ProjectLead(BaseModel):
    """Project lead user information."""
    
    account_id: str = Field(..., alias="accountId")
    display_name: str = Field(..., alias="displayName")
    email: Optional[str] = None
    active: Optional[bool] = None


class ProjectInsight(BaseModel):
    """Project insight information."""
    
    total_issue_count: int = Field(..., alias="totalIssueCount")
    last_issue_update_time: Optional[datetime] = Field(None, alias="lastIssueUpdateTime")


class ProjectSummary(BaseModel):
    """Basic project information."""
    
    id: str
    key: str
    name: str
    project_type_key: str = Field(..., alias="projectTypeKey")
    avatar_urls: Optional[AvatarUrls] = Field(None, alias="avatarUrls")
    insight: Optional[ProjectInsight] = None


class Project(ProjectSummary):
    """Detailed project model."""
    
    description: Optional[str] = None
    lead: Optional[ProjectLead] = None
    url: Optional[str] = None
    project_category: Optional[ProjectCategory] = Field(None, alias="projectCategory")
    simplified: Optional[bool] = None
    style: Optional[str] = None
    is_private: Optional[bool] = Field(None, alias="isPrivate")
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore"  # Allow extra attributes that might be returned by the API
    )


class ProjectList(BaseModel):
    """List of projects with pagination info."""
    
    start_at: int = Field(..., alias="startAt")
    max_results: int = Field(..., alias="maxResults")
    total: int
    is_last: bool = Field(..., alias="isLast")
    values: List[ProjectSummary]
    
    model_config = ConfigDict(populate_by_name=True)
