"""Account management functionality for Taskra."""

import os
import re
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse

from .manager import config_manager


def get_subdomain_from_url(url: str) -> str:
    """
    Extract the subdomain from a Jira URL.
    
    Args:
        url: Jira instance URL (e.g., https://mycompany.atlassian.net)
    
    Returns:
        Subdomain name (e.g., "mycompany")
    """
    # Remove protocol (http/https) if present
    url = url.strip().lower()
    if "://" in url:
        url = url.split("://")[1]
    
    # Remove path if present
    if "/" in url:
        url = url.split("/")[0]
        
    # Check if it's an Atlassian cloud URL
    if ".atlassian.net" in url:
        return url.split(".atlassian.net")[0]
    
    # If not an Atlassian cloud URL, return the full domain
    return url


def list_accounts() -> List[Dict[str, Any]]:
    """
    List configured Jira accounts.
    
    Returns:
        List of account information dictionaries
    """
    config = config_manager.read_config()
    default_account = config.get("default_account")
    accounts_dict = config.get("accounts", {})
    
    result = []
    for name, account in accounts_dict.items():
        result.append({
            "name": name,
            "url": account.get("url", ""),
            "email": account.get("email", ""),
            "is_default": name == default_account
        })
    
    return result


def get_current_account() -> Optional[Dict[str, Any]]:
    """
    Get the current active account.
    
    Returns:
        Account information dictionary or None if no account is configured
    """
    # Check if environment variable override is set
    env_account = os.environ.get("TASKRA_ACCOUNT")
    
    config = config_manager.read_config()
    accounts = config.get("accounts", {})
    
    if not accounts:
        return None
        
    # First try env var override
    if env_account and env_account in accounts:
        account_data = accounts[env_account]
        return {
            "name": env_account,
            **account_data
        }
    
    # Then try default account
    default_account = config.get("default_account")
    if default_account and default_account in accounts:
        account_data = accounts[default_account]
        return {
            "name": default_account,
            **account_data
        }
    
    # If no default, return first account
    name = next(iter(accounts))
    return {
        "name": name,
        **accounts[name]
    }


def validate_credentials(url: str, email: str, token: str, debug: bool = False) -> bool:
    """
    Validate account credentials by making a test API call.

    Args:
        url: Jira instance URL
        email: User email
        token: API token
        debug: Enable debug logging

    Returns:
        True if credentials are valid, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from ..api.client import JiraClient
        from ..api.services.users import UserService

        if debug:
            print(f"DEBUG: Creating JiraClient for validation with URL: {url}")

        # Pass email and token as separate arguments
        temp_client = JiraClient(
            base_url=url,
            email=email,
            api_token=token,
            debug=debug
        )
        user_service = UserService(temp_client)

        if debug:
            print("DEBUG: Calling validate_credentials on UserService")

        return user_service.validate_credentials()
    except Exception as e:
        if debug:
            print(f"DEBUG: Exception in validate_credentials: {str(e)}")
        return False


def add_account(url: str, email: str, token: str, name: Optional[str] = None, debug: bool = False) -> Tuple[bool, str]:
    """
    Add a new Jira account configuration.
    
    Args:
        url: Jira instance URL
        email: User email address
        token: API token
        name: Custom account name (optional)
        debug: Enable debug output
    
    Returns:
        Tuple of (success, message)
    """
    if debug:
        print(f"DEBUG: Adding account - URL: {url}, Email: {email}, Name: {name or '(auto)'}")
    
    # Normalize the URL (remove trailing slashes)
    url = url.rstrip("/")
    
    # Add protocol if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    # If name is not provided, derive it from the URL
    if not name:
        name = get_subdomain_from_url(url)
        if debug:
            print(f"DEBUG: Derived account name: {name}")
    
    # Check if account already exists
    config = config_manager.read_config()
    accounts = config.get("accounts", {})
    if name in accounts:
        return False, f"Account '{name}' already exists."
    
    # Validate credentials
    if debug:
        print(f"DEBUG: Validating credentials")
        
    if not validate_credentials(url, email, token, debug):
        return False, "Invalid credentials. Please check your email and API token."
    
    if debug:
        print(f"DEBUG: Credentials validated successfully")
    
    # Add the account to the configuration
    try:
        if debug:
            print(f"DEBUG: Updating configuration with new account")
        
        def update_config_with_account(config):
            """Add the account to the configuration."""
            if "accounts" not in config:
                config["accounts"] = {}
                
            config["accounts"][name] = {
                "url": url,
                "email": email,
                "token": token
            }
            
            # If this is the first account, set it as default
            if not config.get("default_account"):
                if debug:
                    print(f"DEBUG: Setting {name} as default account")
                config["default_account"] = name
            
            return config
        
        config_manager.update_config(update_config_with_account)
        
        if debug:
            print(f"DEBUG: Configuration updated successfully")
            # Verify the account was added
            config = config_manager.read_config()
            print(f"DEBUG: Account in config after update: {name in config['accounts']}")
            print(f"DEBUG: Default account after update: {config['default_account']}")
        
        return True, f"Account '{name}' added successfully"
        
    except Exception as e:
        error_message = f"Error saving account configuration: {str(e)}"
        if debug:
            print(f"DEBUG: {error_message}")
            import traceback
            print(f"DEBUG: {traceback.format_exc()}")
        return False, error_message


def remove_account(name: str) -> Tuple[bool, str]:
    """
    Remove an account configuration.
    
    Args:
        name: Account name to remove
    
    Returns:
        Tuple of (success, message)
    """
    config = config_manager.read_config()
    accounts = config.get("accounts", {})
    
    if name not in accounts:
        return False, f"Account '{name}' does not exist."
    
    def update_config_remove_account(config):
        """Remove the account from the configuration."""
        accounts = config.get("accounts", {})
        accounts.pop(name, None)
        
        # If we removed the default account, pick a new default
        if config.get("default_account") == name:
            if accounts:
                config["default_account"] = next(iter(accounts))
            else:
                config["default_account"] = None
                
        return config
    
    try:
        config_manager.update_config(update_config_remove_account)
        return True, f"Account '{name}' removed successfully"
    except Exception as e:
        return False, f"Error removing account: {str(e)}"


def set_default_account(name: str) -> Tuple[bool, str]:
    """
    Set the default account.
    
    Args:
        name: Account name to set as default
    
    Returns:
        Tuple of (success, message)
    """
    config = config_manager.read_config()
    accounts = config.get("accounts", {})
    
    if name not in accounts:
        return False, f"Account '{name}' does not exist"
    
    def update_config(config):
        config["default_account"] = name
        return config
    
    config_manager.update_config(update_config)
    return True, f"Default account set to '{name}'"
