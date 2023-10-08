"""User service for interacting with Jira users API."""

from typing import Dict, List, Any, Optional, Union
from ..models.user import User, CurrentUser
from ...utils.serialization import to_serializable
from .base import BaseService

class UserService(BaseService):
    """Service for interacting with Jira users API."""
    
    def validate_credentials(self) -> bool:
        """
        Validate the current authentication credentials.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            # Make a simple API call to verify credentials
            self.client.get("/rest/api/3/myself")
            return True
        except Exception:
            return False
    
    def get_current_user(self) -> User:
        """
        Get the current authenticated user.
        
        Returns:
            User model for the authenticated user
        """
        response = self.client.get("/rest/api/3/myself")
        # Convert response to User model
        return CurrentUser.model_validate(response)
        
    def find_users(self, query: str, max_results: int = 10) -> List[User]:
        """
        Find users by name, email, or display name.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of matching User models
        """
        params = {
            "query": query,
            "maxResults": max_results
        }
        response = self.client.get("/rest/api/3/user/search", params=params)
        # Convert response list to User models
        return [User.model_validate(user_data) for user_data in response]
    
    def get_user(self, account_id: str) -> User:
        """
        Get a user by account ID.
        
        Args:
            account_id: User's account ID
            
        Returns:
            User model for the specified user
        """
        params = {
            "accountId": account_id
        }
        response = self.client.get("/rest/api/3/user", params=params)
        return User.model_validate(response)


# Create a core-layer compatible version of the User service
class UserServiceBackwardCompat:
    """
    Backward compatibility wrapper for UserService.
    
    This class provides methods that return dictionaries instead of models,
    maintaining compatibility with older code that expects dictionary returns.
    """
    
    def __init__(self, service: UserService):
        """
        Initialize with an underlying UserService.
        
        Args:
            service: The actual UserService instance to wrap
        """
        self._service = service
    
    def get_current_user(self) -> Dict[str, Any]:
        """
        Get current user with backward compatible return format.
        
        Returns:
            Dictionary representation of the user
        """
        user_model = self._service.get_current_user()
        # Convert model to dictionary for backward compatibility
        return to_serializable(user_model)
    
    def find_users(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Find users with backward compatible return format.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of dictionary representations of users
        """
        user_models = self._service.find_users(query, max_results)
        # Convert models to dictionaries for backward compatibility
        return [to_serializable(user) for user in user_models]
    
    def get_user(self, account_id: str) -> Dict[str, Any]:
        """
        Get a user by account ID with backward compatible return format.
        
        Args:
            account_id: User's account ID
            
        Returns:
            Dictionary representation of the user
        """
        user_model = self._service.get_user(account_id)
        # Convert model to dictionary for backward compatibility
        return to_serializable(user_model)
