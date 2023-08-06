"""Project-related functionality."""

from ..api.services.projects import ProjectsService
from ..api.client import get_client

def list_projects():
    """
    List available projects.
    
    Returns:
        list: Project data
    """
    client = get_client()
    projects_service = ProjectsService(client)
    projects = projects_service.list_all_projects()
    
    for project in projects:
        print(f"{project['key']}: {project['name']}")
    
    return projects

def get_project(project_key):
    """
    Get information about a specific project.
    
    Args:
        project_key: The project key
        
    Returns:
        dict: Project data
    """
    client = get_client()
    projects_service = ProjectsService(client)
    return projects_service.get_project(project_key)
