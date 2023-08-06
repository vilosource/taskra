"""Client for interacting with the Jira REST API."""

import json
import logging
import requests
from typing import Dict, Any, Optional
from urllib.parse import urljoin

from .auth import get_auth_details


class JiraClient:
    """
    Client for interacting with the Jira REST API.
    
    Handles authentication and HTTP operations against the Jira API endpoints.
    """
    
    def __init__(self, base_url: str, auth: Dict[str, str], debug: bool = False):
        """
        Initialize a new Jira client.
        
        Args:
            base_url: Base URL for the Jira instance (e.g., https://mycompany.atlassian.net)
            auth: Authentication details (email and token)
            debug: Enable debug output
        """
        self.debug = debug
        
        # Ensure base URL ends with a trailing slash
        if not base_url.endswith('/'):
            base_url = f"{base_url}/"
            
        # Add API path if not already present
        if not base_url.endswith("/rest/api/3/"):
            self.base_url = urljoin(base_url, "rest/api/3/")
        else:
            self.base_url = base_url
            
        self.auth = auth
        self.session = requests.Session()
        self.session.auth = (auth["email"], auth["token"])
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
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request to the Jira API.
        
        Args:
            endpoint: API endpoint relative to the base URL
            params: Optional query parameters
            
        Returns:
            Response data as dictionary
        """
        url = urljoin(self.base_url, endpoint)
        self._log_request("GET", url, params=params)
        
        response = self.session.get(url, params=params)
        self._log_response(response)
        
        response.raise_for_status()
        return response.json()
    
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


def get_client(debug: bool = False) -> JiraClient:
    """
    Factory function to create a JiraClient from environment variables or configuration.
    
    Checks for environment variables first, then falls back to configuration.
    
    Args:
        debug: Enable debug output
        
    Returns:
        Configured JiraClient instance
    """
    auth_details = get_auth_details()
    
    return JiraClient(
        base_url=auth_details['base_url'],
        auth={'email': auth_details['email'], 'token': auth_details['token']},
        debug=debug
    )
