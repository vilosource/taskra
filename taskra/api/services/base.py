"""Base service class for all Jira API services."""

from abc import ABC
from typing import Any

from ..client import JiraClient


class BaseService(ABC):
    """
    Abstract base class for all Jira API services.
    
    Provides common functionality and enforces consistent patterns
    across all service implementations.
    """
    
    def __init__(self, client: JiraClient):
        """
        Initialize the service with a Jira client.
        
        Args:
            client: Configured JiraClient instance
        """
        self.client = client
    
    def _get_endpoint(self, path: str) -> str:
        """
        Build an endpoint path, ensuring consistent formatting.
        
        Args:
            path: The API endpoint path
            
        Returns:
            Formatted endpoint path
        """
        return path.lstrip('/')
