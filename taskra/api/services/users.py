"""User service for interacting with Jira users API."""

from typing import Dict, Any, Optional

from .base import BaseService


class UserService(BaseService):
    """Service for interacting with Jira users API."""
    
    def get_current_user(self) -> Dict[str, Any]:
        """
        Get information about the currently authenticated user.
        
        Returns:
            User data dictionary
        """
        return self.client.get(self._get_endpoint("myself"))
    
    def validate_credentials(self) -> bool:
        """
        Validate the current authentication credentials.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            self.get_current_user()
            return True
        except Exception as e:
            if hasattr(self.client, 'debug') and self.client.debug:
                print(f"DEBUG: Credential validation failed: {str(e)}")
            return False
