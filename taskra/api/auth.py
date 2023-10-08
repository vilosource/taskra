"""Authentication utilities for Jira API."""

import os
from typing import Dict, Any, Optional

def get_auth_details() -> Dict[str, Any]:
    """
    Get authentication details from environment variables or configuration.
    
    First checks environment variables, then falls back to configuration file.
    
    Returns:
        Dictionary containing base_url, email, and token
    """
    # First try environment variables
    env_base_url = os.environ.get('JIRA_BASE_URL')
    env_email = os.environ.get('JIRA_EMAIL')
    env_token = os.environ.get('JIRA_API_TOKEN')
    
    # If all environment variables are set, use them
    if env_base_url and env_email and env_token:
        return {
            'base_url': env_base_url,
            'email': env_email,
            'token': env_token
        }
    
    # Otherwise, fall back to the configuration file
    try:
        from ..config.account import get_current_account
        
        account = get_current_account()
        if account:
            return {
                'base_url': account.get('url'),
                'email': account.get('email'),
                'token': account.get('token')
            }
    except ImportError:
        pass
    except Exception as e:
        import logging
        logging.debug(f"Error getting account from config: {str(e)}")
    
    # Return environment variables (which could be None) if no config is found
    return {
        'base_url': env_base_url,
        'email': env_email,
        'token': env_token
    }
