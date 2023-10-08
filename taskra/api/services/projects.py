"""Project service for interacting with Jira projects API."""

from typing import Dict, List, Any, Optional, Union
from ..models.project import Project, ProjectList, ProjectSummary
from ...utils.serialization import to_serializable
from .base import BaseService

class ProjectsService(BaseService):
    """Service for interacting with Jira projects API."""
    
    def list_projects(self, start_at: int = 0, max_results: int = 50) -> List[Project]:
        """
        Get a list of projects visible to the user.
        
        Args:
            start_at: Index of the first project to return
            max_results: Maximum number of projects to return
            
        Returns:
            List of Project models
        """
        params = {
            "startAt": start_at,
            "maxResults": max_results
        }
        
        response = self.client.get(self._get_endpoint("project/search"), params=params)
        project_list = ProjectList.model_validate(response)
        return project_list.values
    
    def list_all_projects(self, max_results_per_page: int = 50) -> List[Project]:
        """
        Get all projects visible to the user, handling pagination.
        
        Args:
            max_results_per_page: Maximum number of projects to return per request
            
        Returns:
            Complete list of Project models
        """
        all_projects = []
        start_at = 0
        is_last_page = False
        
        while not is_last_page:
            params = {
                "startAt": start_at,
                "maxResults": max_results_per_page
            }
            
            response = self.client.get(self._get_endpoint("project/search"), params=params)
            project_list = ProjectList.model_validate(response)
            
            all_projects.extend(project_list.values)
            is_last_page = project_list.is_last
            
            if not is_last_page:
                start_at += len(project_list.values)
        
        return all_projects
    
    def get_project(self, project_key: str) -> Project:
        """
        Get a project by key.
        
        Args:
            project_key: Project key (e.g., 'PROJECT')
            
        Returns:
            Project model
        """
        response = self.client.get(self._get_endpoint(f"project/{project_key}"))
        return Project.model_validate(response)
