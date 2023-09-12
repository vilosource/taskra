"""Worklog service for interacting with Jira worklogs API."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

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
    
    def list_worklogs(self, issue_key: str, start_at: int = 0, 
                      max_results: int = 50, get_all: bool = True) -> List[Dict[str, Any]]:
        """
        Get worklogs for an issue with pagination support.
        
        Args:
            issue_key: The issue key (e.g., PROJECT-123)
            start_at: Index of the first worklog to return (for pagination)
            max_results: Maximum number of worklogs to return per request
            get_all: If True, retrieve all worklogs by handling pagination automatically
            
        Returns:
            List of worklog data dictionaries
        """
        if get_all:
            return self._get_all_worklogs(issue_key, max_results_per_page=max_results)
        
        params = {
            "startAt": start_at,
            "maxResults": max_results
        }
        
        response = self.client.get(self._get_endpoint(f"issue/{issue_key}/worklog"), params=params)
        worklog_list = WorklogList.model_validate(response)
        
        return worklog_list.worklogs
    
    def _get_all_worklogs(self, issue_key: str, max_results_per_page: int = 50) -> List[Dict[str, Any]]:
        """
        Get all worklogs for an issue by handling pagination.
        
        Args:
            issue_key: The issue key
            max_results_per_page: Maximum number of worklogs to return per request
            
        Returns:
            Complete list of worklog data dictionaries
        """
        all_worklogs = []
        start_at = 0
        total = None
        
        while total is None or start_at < total:
            params = {
                "startAt": start_at,
                "maxResults": max_results_per_page
            }
            
            response = self.client.get(self._get_endpoint(f"issue/{issue_key}/worklog"), params=params)
            worklog_list = WorklogList.model_validate(response)
            worklogs = worklog_list.worklogs
            
            all_worklogs.extend(worklogs)
            
            # If this is the first request, get the total count
            if total is None:
                total = worklog_list.total
            
            # Update the start_at parameter for the next page
            start_at += len(worklogs)
            
            # If we got fewer results than requested, we're done
            if len(worklogs) < max_results_per_page:
                break
        
        return all_worklogs
    
    def get_user_worklogs(self, username: Optional[str] = None, 
                          start_date: Optional[str] = None, 
                          end_date: Optional[str] = None,
                          debug_level: str = 'none') -> List[Dict[str, Any]]:
        """
        Get worklogs for a specific user.
        
        Args:
            username: The username to filter by (defaults to current user if None)
            start_date: Start date in format 'YYYY-MM-DD' (defaults to yesterday if None)
            end_date: End date in format 'YYYY-MM-DD' (defaults to today if None)
            debug_level: Debug output level ('none', 'error', 'info', 'verbose')
            
        Returns:
            List of worklog data dictionaries
        """
        # Set up logging based on debug level
        show_debug = debug_level == 'verbose'
        show_info = debug_level in ('info', 'verbose')
        
        # Set default dates if not provided
        if not start_date:
            # Default to yesterday (last 24 hours) instead of 7 days ago
            yesterday = datetime.now() - timedelta(days=1)
            start_date = yesterday.strftime("%Y-%m-%d")
            
        if not end_date:
            # Default to today
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Format the dates with single quotes as required by JQL
        formatted_start = f"'{start_date}'"
        formatted_end = f"'{end_date}'"
        
        # Use JQL to search for worklogs within the date range
        # Use worklogDate >= '2023-04-01' format for dates
        jql = f"worklogDate >= {formatted_start} AND worklogDate <= {formatted_end}"
        
        # Add username constraint if provided - ensure email addresses are properly quoted
        if username:
            # Make sure we properly quote the username, especially for email addresses
            quoted_username = f'"{username}"'
            jql += f" AND worklogAuthor = {quoted_username}"
        
        if show_info:
            logging.info(f"Searching with JQL: {jql}")
        
        # Search for issues with matching worklogs
        params = {
            "jql": jql,
            "fields": "summary,worklog",
            "maxResults": 50  # Adjust as needed
        }
        
        try:
            # Get issues with worklogs matching our criteria
            if show_debug:
                print(f"DEBUG: Executing JQL query: {jql}")
            
            response = self.client.get(self._get_endpoint("search"), params=params)
            
            if "issues" not in response:
                if show_info:
                    logging.info(f"No issues found with JQL: {jql}")
                return []
            
            if show_info:
                logging.info(f"Found {len(response.get('issues', []))} issues with worklogs")
                
            # Collect all worklogs from the returned issues
            all_worklogs = []
            
            for issue in response.get("issues", []):
                issue_key = issue.get("key", "")
                issue_summary = issue.get("fields", {}).get("summary", "")
                
                if show_debug:
                    print(f"DEBUG: Processing issue {issue_key}: {issue_summary}")
                
                # Get detailed worklogs for this issue
                try:
                    worklogs_response = self.client.get(
                        self._get_endpoint(f"issue/{issue_key}/worklog")
                    )
                    issue_worklogs = worklogs_response.get("worklogs", [])
                    
                    if show_debug:
                        print(f"DEBUG: Found {len(issue_worklogs)} worklogs for issue {issue_key}")
                    
                    # Filter by date range and username if specified
                    for worklog in issue_worklogs:
                        # Add issue information to each worklog
                        worklog["issueKey"] = issue_key
                        worklog["issueSummary"] = issue_summary
                        
                        # Apply date filter
                        if "started" in worklog:
                            worklog_date = worklog["started"].split("T")[0]
                            if worklog_date >= start_date and worklog_date <= end_date:
                                # Apply username filter if specified
                                if username:
                                    author_name = worklog.get("author", {}).get("displayName", "")
                                    author_email = worklog.get("author", {}).get("emailAddress", "")
                                    author_id = worklog.get("author", {}).get("accountId", "")
                                    
                                    # Check if any author field contains our username
                                    username_lower = username.lower()
                                    if (username_lower in author_name.lower() or 
                                        username_lower in (author_email or "").lower() or
                                        username_lower == author_id):
                                        all_worklogs.append(worklog)
                                        if show_debug:
                                            print(f"DEBUG: Added worklog by {author_name} for {issue_key}")
                                else:
                                    all_worklogs.append(worklog)
                                    if show_debug:
                                        author_name = worklog.get("author", {}).get("displayName", "")
                                        print(f"DEBUG: Added worklog by {author_name} for {issue_key}")
                            
                except Exception as e:
                    # Log the error but continue with other issues
                    logging.warning(f"Error retrieving worklogs for issue {issue_key}: {str(e)}")
                    continue
            
            if show_info:
                logging.info(f"Total worklogs found: {len(all_worklogs)}")
            
            return all_worklogs
            
        except Exception as e:
            logging.error(f"Error searching for worklogs: {str(e)}")
            return []