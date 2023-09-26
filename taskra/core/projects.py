"""Project management functionality."""

import logging
from typing import Dict, List, Any, Optional, cast

from ..api.services.projects import ProjectsService
from ..api.models.project import Project, ProjectSummary
from ..api.client import get_client
from ..utils.cache import generate_cache_key, get_from_cache, save_to_cache
from ..utils.serialization import to_serializable

# Define type alias for backward compatibility
ProjectDict = Dict[str, Any]

def list_projects(refresh_cache: bool = False) -> List[ProjectDict]:
    """
    Get a list of projects visible to the user.
    
    Args:
        refresh_cache: If True, bypass the cache and get fresh data
        
    Returns:
        Dictionary representations of projects (for backward compatibility)
    """
    # Generate cache key
    cache_key = generate_cache_key(function="list_projects")
    
    # Try to get from cache unless refresh is requested
    if not refresh_cache:
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            logging.info("Using cached project data")
            return cached_data
    
    # If we got here, we need to fetch fresh data
    logging.info("Fetching fresh project data")
    client = get_client()
    project_service = ProjectsService(client)
    
    # Get project models from the service
    project_models = project_service.list_all_projects()
    
    # Convert to serializable format for caching and backward compatibility
    serializable_projects = [to_serializable(project) for project in project_models]
    save_to_cache(cache_key, serializable_projects)
    
    return serializable_projects

def get_project(project_key: str, refresh_cache: bool = False) -> ProjectDict:
    """
    Get a project by key.
    
    Args:
        project_key: The project key
        refresh_cache: If True, bypass the cache and get fresh data
        
    Returns:
        Dictionary representation of the project (for backward compatibility)
    """
    # Generate cache key
    cache_key = generate_cache_key(function="get_project", project_key=project_key)
    
    # Try to get from cache unless refresh is requested
    if not refresh_cache:
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            logging.info(f"Using cached project data for {project_key}")
            return cached_data
    
    # If we got here, we need to fetch fresh data
    logging.info(f"Fetching fresh project data for {project_key}")
    client = get_client()
    project_service = ProjectsService(client)
    
    # Get the project model from the service
    project_model = project_service.get_project(project_key)
    
    # Convert to serializable format for caching and backward compatibility
    serializable_project = to_serializable(project_model)
    save_to_cache(cache_key, serializable_project)
    
    return serializable_project
