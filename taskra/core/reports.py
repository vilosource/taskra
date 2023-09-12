"""Report generation functionality."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from ..api.client import get_client
from ..api.services.reports import ReportService


def generate_project_tickets_report(filters: Dict[str, Any], max_results: int = 100, debug: bool = False) -> List[Dict[str, Any]]:
    """
    Generate a report of tickets for a project.
    
    Args:
        filters: Dictionary of filters to apply
        max_results: Maximum number of tickets to return (default: 100)
        debug: Enable debug output
        
    Returns:
        List of ticket data dictionaries
    """
    client = get_client(debug=debug)
    report_service = ReportService(client)
    
    # Process date filters
    # Track if date filters were explicitly provided by the user
    filters["start_date_explicit"] = "start_date" in filters
    filters["end_date_explicit"] = "end_date" in filters
    
    # Only set default dates if no max_results specified or dates were explicitly provided
    if "start_date" not in filters:
        # Default to 30 days ago
        filters["start_date"] = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        # Not explicitly provided
        filters["start_date_explicit"] = False
        
    if "end_date" not in filters:
        # Default to today
        filters["end_date"] = datetime.now().strftime("%Y-%m-%d")
        # Not explicitly provided
        filters["end_date_explicit"] = False
    
    if debug:
        print(f"[DEBUG] Executing report with filters: {filters}")
        print(f"[DEBUG] Maximum results: {max_results}")
        print(f"[DEBUG] Using date filters: {filters['start_date_explicit'] or filters['end_date_explicit']}")
    
    try:
        # Generate the report
        report_data = report_service.project_tickets_report(filters, max_results=max_results, debug=debug)
        
        # Post-process the data if needed
        processed_data = []
        for ticket in report_data:
            fields = ticket.get("fields", {})
            
            # Handle assignee safely - check if it exists or is None
            assignee_obj = fields.get("assignee")
            if assignee_obj and isinstance(assignee_obj, dict):
                assignee = assignee_obj.get("displayName", "Unknown")
            else:
                assignee = "Unassigned"
                
            # Handle status safely
            status_obj = fields.get("status")
            if status_obj and isinstance(status_obj, dict):
                status = status_obj.get("name", "Unknown")
            else:
                status = "Unknown"
                
            # Handle priority safely
            priority_obj = fields.get("priority")
            if priority_obj and isinstance(priority_obj, dict):
                priority = priority_obj.get("name", "Unknown")
            else:
                priority = "Unknown"
            
            # Extract only the fields we want to show in the report
            processed_ticket = {
                "key": ticket.get("key", ""),
                "summary": fields.get("summary", "No summary"),
                "status": status,
                "assignee": assignee,
                "priority": priority,
                "created": _format_date(fields.get("created", "")),
                "updated": _format_date(fields.get("updated", "")),
            }
            
            # Add worklog information if requested
            if "worklog_user" in filters:
                worklog_obj = fields.get("worklog", {})
                worklogs = worklog_obj.get("worklogs", []) if worklog_obj else []
                worklog_total = sum(
                    w.get("timeSpentSeconds", 0) 
                    for w in worklogs 
                    if _matches_user(w.get("author", {}), filters["worklog_user"])
                )
                processed_ticket["worklog_time"] = _format_time_spent(worklog_total)
                
            processed_data.append(processed_ticket)
            
        return processed_data
    except Exception as e:
        if debug:
            print(f"[DEBUG] Exception in generate_project_tickets_report: {str(e)}")
            # Print the traceback for better debugging
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
