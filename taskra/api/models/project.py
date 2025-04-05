"""Models for Jira projects."""

from typing import Dict, List, Optional, Any
from pydantic import Field

from .base import BaseJiraModel, ApiResource

class ProjectCategory(BaseJiraModel):
    """
    Project category model.
    
    This class represents a category used to group and organize projects in Jira.
    Categories help administrators organize large numbers of projects and provide
    users with a way to filter and find related projects more easily. Each category
    has a unique ID, name, and optional description.
    """
    
    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")


class ProjectLead(BaseJiraModel):
    """
    Project lead model.
    
    This class represents the lead or owner of a Jira project. The project lead
    is typically responsible for managing the project, including configuration,
    permissions, and workflows. This simplified model includes just the essential
    identification information for the user designated as the project lead.
    """
    
    account_id: str = Field(..., alias="accountId")
    display_name: str = Field(..., alias="displayName")
    

class Project(ApiResource):
    """
    Project model representing a Jira project.
    
    This class provides a comprehensive representation of a Jira project, containing
    all the essential details about a project's configuration and metadata. Projects
    are foundational containers in Jira that organize issues, workflows, and permissions.
    
    The model extends ApiResource to inherit standard functionality for Jira API resources
    and includes fields for project identification, description, leadership, categorization,
    and access controls. This information is crucial for displaying project details and
    for operations that need to reference or modify project settings.
    
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
    
    This class provides a simplified representation of a Jira project, containing only
    the essential information needed for listings, dropdowns, and references. It is
    designed to be more efficient than the full Project model when only basic project
    identification is needed.
    
    The class includes a utility method to create a summary from a full Project object,
    making it easy to generate consistent summary representations for various use cases
    such as project selection interfaces or linking from other objects.
    """
    
    id: str = Field(..., description="Project ID")
    key: str = Field(..., description="Project key") 
    name: str = Field(..., description="Project name")
    project_type_key: Optional[str] = Field(None, alias="projectTypeKey", description="Project type key")
    
    @classmethod
    def from_project(cls, project: Project) -> "ProjectSummary":
        """
        Create a summary from a full Project model.
        
        This method extracts the key information from a full Project object to create
        a lightweight summary representation suitable for listings and references.
        
        Args:
            project: The full Project object
            
        Returns:
            A ProjectSummary instance containing the essential information
        """
        return cls(
            id=project.id,
            key=project.key,
            name=project.name,
            projectTypeKey=project.project_type_key
        )
    

class ProjectList(BaseJiraModel):
    """
    List of projects from the Jira API response.
    
    This class models the paginated results returned by Jira's project search API.
    It contains metadata about the search (pagination information, total projects)
    along with the actual list of projects matching the search criteria. This structure
    is used when retrieving multiple projects, either through direct listing or via
    search parameters.
    
    The class provides backward compatibility through a projects property that returns
    the same data as the values field, making it easier to transition existing code.
    
    API Endpoint: /rest/api/3/project/search
    """
    
    # Update fields to match the Jira API search endpoint response structure
    start_at: int = Field(..., alias="startAt", description="Index of the first item")
    max_results: int = Field(..., alias="maxResults", description="Maximum results per page")
    total: int = Field(..., description="Total number of projects available")
    is_last: bool = Field(..., alias="isLast", description="Whether this is the last page")
    values: List[Project] = Field(..., description="List of projects")
    
    @property
    def projects(self) -> List[Project]:
        """
        Property for backward compatibility.
        
        Returns:
            List of Project objects contained in the values field
        """
        return self.values
