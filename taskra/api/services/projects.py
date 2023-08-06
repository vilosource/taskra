"""Projects service for interacting with Jira projects API."""

from typing import Dict, List, Any, Optional

from .base import BaseService
from ..models.project import Project, ProjectList


class ProjectsService(BaseService):
    """Service for interacting with Jira projects API."""
    
    def list_projects(self, start_at: int = 0, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get a list of projects visible to the user.
        
        Args:
            start_at: Index of the first project to return
            max_results: Maximum number of projects to return
            
        Returns:
            List of project data dictionaries
        """
        params = {
            "startAt": start_at,
            "maxResults": max_results
        }
        
        response = self.client.get(self._get_endpoint("project/search"), params=params)
        project_list = ProjectList.model_validate(response)
        
        return [project.model_dump(by_alias=False) for project in project_list.values]
    
    def list_all_projects(self, max_results_per_page: int = 50) -> List[Dict[str, Any]]:
        """
        Get all projects visible to the user, handling pagination.
        
        Args:
            max_results_per_page: Maximum number of projects to return per request
            
        Returns:
            Complete list of project data dictionaries
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
            
            # Add projects from this page to our result
            all_projects.extend([project.model_dump(by_alias=False) for project in project_list.values])
            
            # Check if this is the last page
            is_last_page = project_list.is_last
            
            # Update start_at for next page
            start_at += len(project_list.values)
            
            # Safety check - if we got fewer results than requested, we're done
            if len(project_list.values) < max_results_per_page:
                break
        
        return all_projects
    
    def get_project(self, project_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific project.
        
        Args:
            project_key: The project key
            
        Returns:
            Project data dictionary
        """
        response = self.client.get(self._get_endpoint(f"project/{project_key}"))
        project = Project.model_validate(response)
        
        return project.model_dump(by_alias=False)
