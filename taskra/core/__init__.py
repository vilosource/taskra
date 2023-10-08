"""Core functionality for Taskra."""

from .issues import get_issue, create_issue, get_issue_comments
from .projects import list_projects, get_project
from .worklogs import add_worklog, list_worklogs, get_user_worklogs
from .reports import generate_project_tickets_report, generate_cross_project_report

__all__ = [
    "get_issue", 
    "create_issue",
    "get_issue_comments",
    "list_projects", 
    "get_project", 
    "add_worklog", 
    "list_worklogs",
    "get_user_worklogs",
    "generate_project_tickets_report",
    "generate_cross_project_report"  # Added the new report function
]
