"""Comment management functionality."""

import logging
from typing import Dict, List, Any, Optional, cast

from ..api.services.comments import CommentsService
from ..api.models.comment import Comment
from ..api.client import get_client
from ..utils.cache import generate_cache_key, get_from_cache, save_to_cache
from ..utils.serialization import to_serializable

# Define a type alias for backward compatibility
CommentDict = Dict[str, Any]

def get_comments(issue_key: str, refresh_cache: bool = False) -> List[CommentDict]:
    """
    Get comments for an issue.
    
    Args:
        issue_key: The issue key (e.g., PROJECT-123)
        refresh_cache: If True, bypass the cache and get fresh data
        
    Returns:
        List of dictionary representations of comments (for backward compatibility)
    """
    # Generate cache key
    cache_key = generate_cache_key(function="get_comments", issue_key=issue_key)
    
    # Try to get from cache unless refresh is requested
    if not refresh_cache:
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            logging.info(f"Using cached comments for issue {issue_key}")
            return cached_data
    
    # If we got here, we need to fetch fresh data
    logging.info(f"Fetching fresh comments for issue {issue_key}")
    client = get_client()
    comments_service = CommentsService(client)
    
    # Get the comment models from the service
    comment_models = comments_service.list_comments(issue_key, get_all=True)
    
    # Convert to serializable format for caching and backward compatibility
    serializable_comments = [to_serializable(comment) for comment in comment_models]
    save_to_cache(cache_key, serializable_comments)
    
    return serializable_comments

def add_comment(issue_key: str, body: str, visibility_type: Optional[str] = None, 
               visibility_value: Optional[str] = None) -> CommentDict:
    """
    Add a comment to an issue.
    
    Args:
        issue_key: The issue key (e.g., PROJECT-123)
        body: Comment text
        visibility_type: Optional visibility type (e.g., 'group', 'role')
        visibility_value: Optional value for the visibility type
        
    Returns:
        Dictionary representation of the created comment
    """
    client = get_client()
    comments_service = CommentsService(client)
    
    # Add the comment using the service
    comment_model = comments_service.add_comment(
        issue_key=issue_key,
        body=body,
        visibility_type=visibility_type,
        visibility_value=visibility_value
    )
    
    # Clear cache for this issue's comments
    cache_key = generate_cache_key(function="get_comments", issue_key=issue_key)
    save_to_cache(cache_key, None)  # Invalidate the cache
    
    # Convert to serializable format for backward compatibility
    return to_serializable(comment_model)
