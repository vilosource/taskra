"""User management functionality."""

import logging
from typing import Dict, List, Any, Optional, cast

from ..api.services.users import UserService
from ..api.models.user import User, CurrentUser
from ..api.client import get_client
from ..utils.cache import generate_cache_key, get_from_cache, save_to_cache
from ..utils.serialization import to_serializable

# Define a type alias for backward compatibility
UserDict = Dict[str, Any]

def get_current_user(refresh_cache: bool = False) -> UserDict:
    """
    Get the current authenticated user.
    
    Args:
        refresh_cache: If True, bypass the cache and get fresh data
        
    Returns:
        Dictionary representation of the current user (for backward compatibility)
    """
    # Generate cache key
    cache_key = generate_cache_key(function="get_current_user")
    
    # Try to get from cache unless refresh is requested
    if not refresh_cache:
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            logging.info("Using cached current user data")
            return cached_data
    
    # If we got here, we need to fetch fresh data
    logging.info("Fetching fresh current user data")
    client = get_client()
    user_service = UserService(client)
    
    # Get the user model from the service
    user_model = user_service.get_current_user()
    
    # Convert to serializable format for caching and backward compatibility
    serializable_user = to_serializable(user_model)
    save_to_cache(cache_key, serializable_user)
    
    return serializable_user

def find_users(query: str, max_results: int = 10, refresh_cache: bool = False) -> List[UserDict]:
    """
    Find users by name, email, or display name.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        refresh_cache: If True, bypass the cache and get fresh data
        
    Returns:
        List of user dictionaries (for backward compatibility)
    """
    # Generate cache key based on function parameters
    cache_key = generate_cache_key(
        function="find_users",
        query=query,
        max_results=max_results
    )
    
    # Try to get from cache unless refresh is requested
    if not refresh_cache:
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            logging.info("Using cached user search results")
            return cached_data
    
    # If we got here, we need to fetch fresh data
    logging.info("Fetching fresh user search results")
    client = get_client()
    user_service = UserService(client)
    
    # Get the user models from the service
    user_models = user_service.find_users(query, max_results)
    
    # Convert to serializable format for caching and backward compatibility
    serializable_users = [to_serializable(user) for user in user_models]
    save_to_cache(cache_key, serializable_users)
    
    return serializable_users
