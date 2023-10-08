"""Report generation functionality."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import json

from ..api.client import get_jira_client
from ..api.services.reports import ReportService


def generate_project_tickets_report(
    filters: Dict[str, Any],
    max_results: int = 100,
    debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Generate a report of project tickets based on filters.
    
    Args:
        filters: Dictionary of filters to apply
        max_results: Maximum number of tickets to return
        debug: Enable debug output
        
    Returns:
        List of issue data dictionaries
    """
    client = get_jira_client()
    report_service = ReportService(client)
    
    if debug:
        print("[DEBUG] Executing report with filters:", filters)
        print("[DEBUG] Maximum results:", max_results)
        print("[DEBUG] Using date filters:", filters.get("start_date_explicit", False))
    
    try:
        # Call the report service to generate the report
        result = report_service.project_tickets_report(filters, max_results=max_results, debug=debug)
        
        # Return the properly formatted result
        return result
    except Exception as e:
        if debug:
            print(f"[DEBUG] Error generating project tickets report: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'content'):
                try:
                    error_json = e.response.json()
                    print(f"[DEBUG] API error details: {json.dumps(error_json, indent=2)}")
                except Exception:
                    print(f"[DEBUG] Raw response: {e.response.content.decode('utf-8', errors='replace')}")
        raise


def generate_cross_project_report(project_keys: List[str], filters: Dict[str, Any] = None, debug: bool = False) -> Dict[str, Any]:
    """
    Generate a report that spans multiple projects.
    
    Args:
        project_keys: List of project keys to include in the report
        filters: Optional filters to apply
        debug: Enable debug output
        
    Returns:
        Processed report data
    """
    if filters is None:
        filters = {}
        
    if debug:
        print(f"[DEBUG] Generating cross-project report for projects: {project_keys}")
    
    try:
        # Get the API client
        client = get_jira_client()
        report_service = ReportService(client)
        
        # Generate the raw report
        raw_report = report_service.cross_project_report(project_keys, filters, debug)
        
        # Process and enhance the report data
        processed_report = {
            "projects": {},
            "summary": raw_report["summary"]
        }
        
        # Process each project's data
        for project_key, project_data in raw_report["projects"].items():
            processed_issues = []
            
            for issue in project_data.get("issues", []):
                fields = issue.get("fields", {})
                
                # Process issue data (similar to other report processing)
                processed_issue = {
                    "key": issue.get("key", ""),
                    "summary": fields.get("summary", "No summary"),
                    "status": _extract_status_name(fields),
                    "assignee": _extract_assignee_name(fields),
                    "created": _format_date(fields.get("created", "")),
                }
                processed_issues.append(processed_issue)
            
            # Store processed issues back in the result
            processed_project = {
                "name": project_data["name"],
                "issues_count": project_data["issues_count"],
                "issues": processed_issues
            }
            processed_report["projects"][project_key] = processed_project
        
        return processed_report
        
    except Exception as e:
        if debug:
            print(f"[DEBUG] Exception in generate_cross_project_report: {str(e)}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        raise


def _format_date(date_str: str) -> str:
    """Format a date string for display."""
    if not date_str:
        return ""
        
    try:
        if "T" in date_str:
            parts = date_str.split("T")
            return parts[0]
        return date_str
    except Exception:
        return date_str


def _format_time_spent(seconds: int) -> str:
    """Convert seconds to a human-readable time format."""
    if seconds == 0:
        return "0h"
        
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0 and minutes > 0:
        return f"{hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{minutes}m"


def _matches_user(author: Dict[str, Any], username: str) -> bool:
    """Check if an author matches a username filter."""
    if not username or not author:
        return False
        
    # Try different author fields
    display_name = author.get("displayName", "").lower()
    name = author.get("name", "").lower()
    email = author.get("emailAddress", "").lower()
    
    username = username.lower()
    
    return (username in display_name or 
            username in name or 
            username in email)


def _extract_status_name(fields):
    status_obj = fields.get("status")
    if status_obj and isinstance(status_obj, dict):
        return status_obj.get("name", "Unknown")
    return "Unknown"


def _extract_assignee_name(fields):
    assignee_obj = fields.get("assignee")
    if assignee_obj and isinstance(assignee_obj, dict):
        return assignee_obj.get("displayName", "Unknown")
    return "Unassigned"
