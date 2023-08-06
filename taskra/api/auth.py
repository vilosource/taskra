"""Authentication handlers for Jira API."""

import os
from typing import Dict, Any, Optional


class AuthProvider:
    """
    Base class for authentication providers.
    
    This follows the Strategy pattern, allowing different ways to obtain authentication.
    """
    
    def get_auth(self) -> Dict[str, Any]:
        """
        Get authentication details.
        
        Returns:
            Dictionary containing auth details
        """
        raise NotImplementedError("Subclasses must implement get_auth()")


class EnvironmentAuthProvider(AuthProvider):
    """Authentication provider that uses environment variables."""
    
    def get_auth(self) -> Optional[Dict[str, Any]]:
        """Get authentication details from environment variables."""
        base_url = os.environ.get('JIRA_BASE_URL')
        email = os.environ.get('JIRA_EMAIL')
        token = os.environ.get('JIRA_API_TOKEN')
        
        if base_url and email and token:
            return {
                'base_url': base_url,
                'email': email,
                'token': token
            }
        return None


class ConfigAuthProvider(AuthProvider):
    """Authentication provider that uses configuration files."""
    
    def get_auth(self) -> Optional[Dict[str, Any]]:
        """Get authentication details from configuration."""
        # To avoid circular imports, import here
        from ..config.account import get_current_account
        
        account = get_current_account()
        if account:
            return {
                'base_url': account['url'],
                'email': account['email'],
                'token': account['token']
            }
        return None


def get_auth_details() -> Dict[str, Any]:
    """
    Get authentication details from available providers.
    
    Returns:
        Dictionary with authentication details
        
    Raises:
        ValueError: If no authentication details are found
    """
    # Try environment variables first
    env_provider = EnvironmentAuthProvider()
    auth = env_provider.get_auth()
    
    # If not found, try configuration
    if not auth:
        config_provider = ConfigAuthProvider()
        auth = config_provider.get_auth()
    
    # If still not found, raise an error
    if not auth:
        raise ValueError(
            "No Jira account configured. Either set JIRA_BASE_URL, JIRA_EMAIL, and "
            "JIRA_API_TOKEN environment variables, or add an account with "
            "'taskra config add'."
        )
    
    return auth
