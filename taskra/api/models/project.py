"""Models for Jira projects."""

from typing import Dict, List, Optional, Any
from pydantic import Field

from .base import BaseJiraModel, ApiResource

class ProjectCategory(BaseJiraModel):
    """Project category model."""
    
    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")

class ProjectLead(BaseJiraModel):
    """Project lead model."""
    
    account_id: str = Field(..., alias="accountId")
    display_name: str = Field(..., alias="displayName")
    
class Project(ApiResource):
    """
    Project model representing a Jira project.
    
    API Endpoint: /rest/api/3/project/{projectIdOrKey}
    """
    
    self_url: str = Field(..., alias="self", description="URL to this resource")
    id: str = Field(..., description="Project ID")
    key: str = Field(..., description="Project key")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    lead: Optional[ProjectLead] = Field(None, description="Project lead")
    category: Optional[ProjectCategory] = Field(None, description="Project category")
    project_type_key: Optional[str] = Field(None, alias="projectTypeKey", description="Project type")
    simplified: Optional[bool] = Field(None, description="Whether this is a simplified project")
    style: Optional[str] = Field(None, description="Project style")
    is_private: Optional[bool] = Field(None, alias="isPrivate", description="Whether project is private")

class ProjectSummary(BaseJiraModel):
    """
    Lightweight summary of a project, used for listings and references.
    
    Contains only essential project information.
    """
    
    id: str = Field(..., description="Project ID")
    key: str = Field(..., description="Project key") 
    name: str = Field(..., description="Project name")
    project_type_key: Optional[str] = Field(None, alias="projectTypeKey", description="Project type key")
    
    @classmethod
    def from_project(cls, project: Project) -> "ProjectSummary":
        """Create a summary from a full Project model."""
        return cls(
            id=project.id,
            key=project.key,
            name=project.name,
            projectTypeKey=project.project_type_key
        )
    
class ProjectList(BaseJiraModel):
    """List of projects from the Jira API response."""
    
    # Update fields to match the Jira API search endpoint response structure
    start_at: int = Field(..., alias="startAt", description="Index of the first item")
    max_results: int = Field(..., alias="maxResults", description="Maximum results per page")
    total: int = Field(..., description="Total number of projects available")
    is_last: bool = Field(..., alias="isLast", description="Whether this is the last page")
    values: List[Project] = Field(..., description="List of projects")
    
    @property
    def projects(self) -> List[Project]:
        """Property for backward compatibility."""
        return self.values
