"""Core projects module for interacting with Jira projects."""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from ..api.client import get_jira_client  # Changed from get_client to get_jira_client
from ..api.services.projects import ProjectsService

logger = logging.getLogger(__name__)

def list_projects(max_results: int = 50) -> List[Dict[str, Any]]:
    """
    List all accessible projects.
    
    Args:
        max_results: Maximum number of results to return
        
    Returns:
        List of project dictionaries
    """
    client = get_jira_client()
    service = ProjectsService(client)
    
    # Get projects as models
    projects = service.list_projects(max_results=max_results)
    
    # Convert to dictionaries for backward compatibility
    return [project.model_dump(by_alias=True) for project in projects]

def get_project(project_key: str) -> Dict[str, Any]:
    """
    Get a project by key.
    
    Args:
        project_key: Project key (e.g., 'PROJ')
        
    Returns:
        Project data as a dictionary
    """
    client = get_jira_client()
    service = ProjectsService(client)
    
    # Get the project as a model
    project = service.get_project(project_key)
    
    # Convert to dictionary for backward compatibility
    return project.model_dump(by_alias=True)

def get_project_categories() -> List[Dict[str, Any]]:
    """
    Get all project categories.
    
    Returns:
        List of project category dictionaries
    """
    client = get_jira_client()
    service = ProjectsService(client)
    
    # Get categories as models
    categories = service.get_project_categories()
    
    # Convert to dictionaries for backward compatibility
    return [category.model_dump(by_alias=True) for category in categories]

def search_projects(query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Search for projects by name.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of project dictionaries matching the query
    """
    client = get_jira_client()
    service = ProjectsService(client)
    
    # Search projects as models
    projects = service.search_projects(query, max_results=max_results)
    
    # Convert to dictionaries for backward compatibility
    return [project.model_dump(by_alias=True) for project in projects]
