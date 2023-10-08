"""Client for interacting with the Jira REST API."""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin
from requests.auth import HTTPBasicAuth
from .auth import get_auth_details

# Set up logger
logger = logging.getLogger("jira_client")

class JiraClient:
    """
    Client for interacting with the Jira REST API.
    
    Handles authentication and HTTP operations against the Jira API endpoints.
    """
    
    def __init__(self, base_url: str, email: str, api_token: str, debug: bool = False):
        """
        Initialize a new Jira client.
        
        Args:
            base_url: Base URL for the Jira instance (e.g., https://mycompany.atlassian.net)
            email: User email for authentication
            api_token: API token for authentication
            debug: Enable debug output
        """
        self.debug = debug
        self.email = email  # Store email as an attribute for user identification
        
        # Ensure base URL ends with a trailing slash
        if not base_url.endswith('/'):
            base_url = f"{base_url}/"
            
        # Add API path if not already present
        if not base_url.endswith("/rest/api/3/"):
            self.base_url = urljoin(base_url, "rest/api/3/")
        else:
            self.base_url = base_url
            
        self.auth = HTTPBasicAuth(email, api_token)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        if debug:
            logging.basicConfig(level=logging.DEBUG)
            self.logger = logging.getLogger("jira_client")
            self.logger.debug(f"Initialized JiraClient with base URL: {self.base_url}")
    
    def _log_request(self, method: str, url: str, **kwargs):
        """Log request details if debug mode is enabled."""
        if not self.debug:
            return
            
        self.logger.debug(f"Request: {method} {url}")
        
        if "params" in kwargs and kwargs["params"]:
            self.logger.debug(f"Params: {kwargs['params']}")
            
        if "json" in kwargs and kwargs["json"]:
            # Truncate large JSON objects for readability
            json_str = json.dumps(kwargs["json"])
            if len(json_str) > 1000:
                json_str = f"{json_str[:1000]}... (truncated)"
            self.logger.debug(f"JSON: {json_str}")
    
    def _log_response(self, response: requests.Response):
        """Log response details if debug mode is enabled."""
        if not self.debug:
            return
            
        self.logger.debug(f"Response: {response.status_code}")
        
        # Truncate large responses for readability
        content = response.content.decode('utf-8', errors='replace')
        if len(content) > 1000:
            content = f"{content[:1000]}... (truncated)"
        self.logger.debug(f"Content: {content}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], list]:
        """
        Make a GET request to the Jira API.
        
        Args:
            endpoint: API endpoint relative to the base URL
            params: Optional query parameters
            
        Returns:
            Response data as dictionary or list
        """
        url = urljoin(self.base_url, endpoint)
        self._log_request("GET", url, params=params)
        
        response = self.session.get(url, params=params)
        self._log_response(response)
        
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if self.debug:
                print(f"[DEBUG] HTTP error: {str(e)}")
                print(f"[DEBUG] Response content: {response.content.decode('utf-8', errors='replace')}")
                print(f"[DEBUG] Status code: {response.status_code}")
            raise
    
    def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a POST request to the Jira API.
        
        Args:
            endpoint: API endpoint relative to the base URL
            json_data: Optional JSON data to send
            params: Optional query parameters
            
        Returns:
            Response data as dictionary
        """
        url = urljoin(self.base_url, endpoint)
        self._log_request("POST", url, json=json_data, params=params)
        
        response = self.session.post(url, json=json_data, params=params)
        self._log_response(response)
        
        response.raise_for_status()
        return response.json()
    
    def put(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None,
           params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a PUT request to the Jira API.
        
        Args:
            endpoint: API endpoint relative to the base URL
            json_data: Optional JSON data to send
            params: Optional query parameters
            
        Returns:
            Response data as dictionary
        """
        url = urljoin(self.base_url, endpoint)
        self._log_request("PUT", url, json=json_data, params=params)
        
        response = self.session.put(url, json=json_data, params=params)
        self._log_response(response)
        
        response.raise_for_status()
        return response.json()
    
    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Make a DELETE request to the Jira API.
        
        Args:
            endpoint: API endpoint relative to the base URL
            params: Optional query parameters
        """
        url = urljoin(self.base_url, endpoint)
        self._log_request("DELETE", url, params=params)
        
        response = self.session.delete(url, params=params)
        self._log_response(response)
        
        response.raise_for_status()


# Global client instance
_jira_client = None

def get_jira_client() -> JiraClient:
    """
    Get a singleton instance of the JiraClient.
    
    Returns:
        JiraClient instance
    
    Raises:
        ValueError: If no account is configured
    """
    global _jira_client
    
    if _jira_client is None:
        # Get authentication details from auth module
        try:
            auth_details = get_auth_details()
            
            # Get auth details, falling back to environment variables
            base_url = auth_details.get('base_url')
            email = auth_details.get('email')
            api_token = auth_details.get('token')
            
            # Validate we have the required credentials
            if not base_url or not email or not api_token:
                raise ValueError("Missing required authentication details")
            
            # Create client
            _jira_client = JiraClient(base_url, email, api_token)
            
        except Exception as e:
            # Re-raise any exceptions from get_auth_details
            raise ValueError(f"No Jira account configured: {str(e)}")
        
    return _jira_client

# Alias for backward compatibility
def get_client() -> JiraClient:
    """
    Alias for get_jira_client() for backward compatibility.
    
    Returns:
        JiraClient instance
    """
    import warnings
    warnings.warn(
        "get_client() is deprecated, use get_jira_client() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return get_jira_client()
