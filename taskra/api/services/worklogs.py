"""Worklog service for interacting with Jira worklogs API."""

from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import BaseService
from ..models.worklog import WorklogCreate, WorklogList


class WorklogService(BaseService):
    """Service for interacting with Jira worklogs API."""
    
    def add_worklog(self, issue_key: str, time_spent: str, 
                    comment: Optional[str] = None,
                    started: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Add a worklog to an issue.
        
        Args:
            issue_key: The issue key (e.g., PROJECT-123)
            time_spent: Time spent in format like "2h 30m" or "3h"
            comment: Optional comment for the worklog
            started: Optional start time (defaults to now)
            
        Returns:
            Created worklog data dictionary
        """
        worklog_data = WorklogCreate.from_simple(
            time_spent=time_spent,
            comment=comment,
            started=started
        )
        
        response = self.client.post(
            self._get_endpoint(f"issue/{issue_key}/worklog"),
            json_data=worklog_data.model_dump(by_alias=True)
        )
        
        return response
    
    def list_worklogs(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get all worklogs for an issue.
        
        Args:
            issue_key: The issue key (e.g., PROJECT-123)
            
        Returns:
            List of worklog data dictionaries
        """
        response = self.client.get(self._get_endpoint(f"issue/{issue_key}/worklog"))
        worklog_list = WorklogList.model_validate(response)
        
        return worklog_list.worklogs
