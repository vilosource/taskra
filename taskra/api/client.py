"""
Jira API client implementation.

This module provides the base JiraClient class for interacting with the Jira REST API v3,
as well as a factory function to obtain a configured client instance.
"""

import os
from typing import Dict, Optional, Any, Union
from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth


class JiraClient:
    """
    Client for interacting with the Jira REST API.
    
    This client handles authentication, request formation, and basic error handling
    for communicating with the Jira REST API v3.
    """
    
    def __init__(self, base_url: str, auth: Union[HTTPBasicAuth, Dict[str, str]], timeout: int = 30):
        """
        Initialize the Jira client.
        
        Args:
            base_url: Base URL for the Jira instance (e.g., https://your-domain.atlassian.net)
            auth: Authentication credentials, either HTTPBasicAuth object or dict with token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/') + '/rest/api/3/'
        self.auth = auth
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Configure authentication
        if isinstance(auth, dict) and 'token' in auth:
            self.session.headers.update({
                'Authorization': f"Bearer {auth['token']}"
            })
        elif isinstance(auth, HTTPBasicAuth):
            self.session.auth = auth
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build a complete API URL from the given endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Complete URL
        """
        return urljoin(self.base_url, endpoint.lstrip('/'))
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response, raising appropriate exceptions if needed.
        
        Args:
            response: Response object from requests
            
        Returns:
            Parsed JSON response
            
        Raises:
            requests.HTTPError: If the response status code indicates an error
        """
        response.raise_for_status()
        
        if response.status_code == 204:  # No content
            return {}
            
        return response.json()
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a GET request to the API.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            
        Returns:
            Parsed JSON response
        """
        url = self._build_url(endpoint)
        response = self.session.get(url, params=params, timeout=self.timeout)
        return self._handle_response(response)
    
    def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a POST request to the API.
        
        Args:
            endpoint: API endpoint path
            json_data: JSON payload
            
        Returns:
            Parsed JSON response
        """
        url = self._build_url(endpoint)
        response = self.session.post(url, json=json_data, timeout=self.timeout)
        return self._handle_response(response)
    
    def put(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a PUT request to the API.
        
        Args:
            endpoint: API endpoint path
            json_data: JSON payload
            
        Returns:
            Parsed JSON response
        """
        url = self._build_url(endpoint)
        response = self.session.put(url, json=json_data, timeout=self.timeout)
        return self._handle_response(response)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Send a DELETE request to the API.
        
        Args:
            endpoint: API endpoint path
            
        Raises:
            NotImplementedError: DELETE operations are not allowed
        """
        raise NotImplementedError("DELETE operations are not allowed in this application")


def get_client() -> JiraClient:
    """
    Factory function to create a configured Jira client instance.
    
    This function reads configuration from environment variables:
    - JIRA_BASE_URL: Base URL of the Jira instance
    - JIRA_API_TOKEN: API token for authentication
    - JIRA_EMAIL: Email address for authentication
    
    Returns:
        Configured JiraClient instance
    
    Raises:
        ValueError: If required environment variables are missing
    """
    base_url = os.environ.get('JIRA_BASE_URL')
    api_token = os.environ.get('JIRA_API_TOKEN')
    email = os.environ.get('JIRA_EMAIL')
    
    if not base_url:
        raise ValueError("JIRA_BASE_URL environment variable is required")
    
    if email and api_token:
        auth = HTTPBasicAuth(email, api_token)
    elif api_token:
        auth = {'token': api_token}
    else:
        raise ValueError("Either JIRA_API_TOKEN or both JIRA_EMAIL and JIRA_API_TOKEN must be set")
    
    return JiraClient(base_url=base_url, auth=auth)
