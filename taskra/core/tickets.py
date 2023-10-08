"""
Core module for handling tickets in Taskra.

This module provides functions for interacting with tickets, including
retrieving tickets for a specific project and applying filters.
"""

from typing import List, Dict, Any
from ..api.client import get_jira_client  # Changed from get_client to get_jira_client
from ..api.services.reports import ReportService

def get_project_tickets(project_key: str, **kwargs) -> List[Dict[str, Any]]:
    """
    Get tickets for a project.
    
    Args:
        project_key: Project key to get tickets for
        **kwargs: Additional arguments for filtering
        
    Returns:
        List of ticket dictionaries
    """
    debug = kwargs.pop('debug', False)
    
    # Create filters from the provided arguments
    filters = {
        'project_key': project_key,
        **kwargs
    }
    
    # Get the Jira client
    client = get_jira_client()
    
    # Generate the report using the ReportService
    report_service = ReportService(client)
    tickets = report_service.project_tickets_report(filters, debug=debug)
    
    return tickets