"""Worklog service for interacting with Jira worklogs API."""

from typing import Dict, List, Any, Optional, Union, cast
from datetime import datetime, timedelta
import logging

from ..models.worklog import (
    Worklog, WorklogCreate, WorklogList, Author, Visibility
)
from ..models.user import User
from ...utils.serialization import deserialize_model, to_serializable
from .base import BaseService


class WorklogService(BaseService):
    """Service for interacting with Jira worklogs API."""
    
    def add_worklog(self, issue_key: str, time_spent: str, 
                    comment: Optional[str] = None,
                    started: Optional[datetime] = None) -> Worklog:
        """
        Add a worklog entry to an issue.
        
        Args:
            issue_key: The issue key (e.g., 'PROJECT-123')
            time_spent: Time spent in format like '2h 30m'
            comment: Optional comment for the worklog
            started: Optional datetime when work started (defaults to now)
            
        Returns:
            Worklog model instance
        """
        # Create worklog model
        worklog_create = WorklogCreate.from_simple(
            time_spent=time_spent,
            comment=comment,
            started=started
        )
        
        # Convert to API format
        payload = worklog_create.model_dump_api()
        
        # Debug logging
        logging.info(f"Adding worklog to issue {issue_key}")
        logging.info(f"Payload: {payload}")
        
        # Send request
        endpoint = self._get_endpoint(f"issue/{issue_key}/worklog")
        
        try:
            # Try using the client's post method
            response = self.client.post(endpoint, json_data=payload)
            # Parse response to Worklog model
            return Worklog.from_api(response)
        except Exception as e:
            logging.error(f"Error adding worklog: {str(e)}")
            logging.error(f"Request payload was: {payload}")
            
            # Try to extract more detailed error information
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_response = e.response.json()
                    logging.error(f"API error response: {error_response}")
                    
                    # Extract specific error messages if available
                    if 'errorMessages' in error_response:
                        for msg in error_response['errorMessages']:
                            logging.error(f"API error message: {msg}")
                    
                    if 'errors' in error_response:
                        for field, msg in error_response['errors'].items():
                            logging.error(f"API field error - {field}: {msg}")
                except Exception as json_err:
                    # If we can't parse the JSON, try to get the raw response text
                    try:
                        raw_response = e.response.text
                        logging.error(f"API raw error response: {raw_response}")
                    except:
                        logging.error("Could not extract API error response")
            
            # Try a direct approach with requests as a fallback
            try:
                import requests
                import json
                
                logging.info("Attempting direct API call as fallback...")
                
                # Get authentication details from the client
                auth = self.client.auth
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                # Make a direct request
                direct_response = requests.post(
                    self.client.base_url + endpoint,
                    auth=auth,
                    headers=headers,
                    json=payload
                )
                
                logging.info(f"Direct API call status code: {direct_response.status_code}")
                
                if direct_response.ok:
                    logging.info("Direct API call succeeded!")
                    return Worklog.from_api(direct_response.json())
                else:
                    logging.error(f"Direct API call failed with status {direct_response.status_code}")
                    try:
                        error_content = direct_response.json()
                        logging.error(f"Direct API error response: {error_content}")
                    except:
                        logging.error(f"Direct API raw error response: {direct_response.text}")
            except Exception as direct_err:
                logging.error(f"Error in direct API call: {str(direct_err)}")
            
            # Re-raise the original exception
            raise
    
    def list_worklogs(self, issue_key: str, start_at: int = 0, 
                      max_results: int = 50, get_all: bool = True) -> List[Worklog]:
        """
        Get worklogs for an issue.
        
        Args:
            issue_key: The issue key (e.g., 'PROJECT-123')
            start_at: Index of first worklog to return
            max_results: Maximum number of worklogs to return per request
            get_all: Whether to fetch all worklogs (multiple requests if needed)
            
        Returns:
            List of Worklog model instances
        """
        if get_all:
            return self._get_all_worklogs(issue_key)
        
        # Make API request
        endpoint = self._get_endpoint(f"issue/{issue_key}/worklog")
        params = {"startAt": start_at, "maxResults": max_results}
        response = self.client.get(endpoint, params=params)
        
        # Convert to WorklogList model
        worklog_list = WorklogList.from_api(response)
        
        return worklog_list.worklogs
    
    def _get_all_worklogs(self, issue_key: str, max_results_per_page: int = 50) -> List[Worklog]:
        """
        Get all worklogs for an issue by handling pagination.
        
        Args:
            issue_key: The issue key
            max_results_per_page: Max results per API request
            
        Returns:
            Complete list of all Worklog model instances
        """
        all_worklogs = []
        start_at = 0
        total = None
        
        while total is None or start_at < total:
            # Make API request
            endpoint = self._get_endpoint(f"issue/{issue_key}/worklog")
            params = {"startAt": start_at, "maxResults": max_results_per_page}
            response = self.client.get(endpoint, params=params)
            
            # Convert to WorklogList model
            worklog_list = WorklogList.from_api(response)
            worklogs = worklog_list.worklogs
            
            # Add worklogs to result list
            all_worklogs.extend(worklogs)
            
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
                          debug_level: str = 'none') -> List[Worklog]:
        """
        Get worklogs for a specific user.
        
        Args:
            username: The username to filter by (defaults to current user if None)
            start_date: Start date in format 'YYYY-MM-DD' (defaults to yesterday if None)
            end_date: End date in format 'YYYY-MM-DD' (defaults to today if None)
            debug_level: Debug output level ('none', 'error', 'info', 'verbose')
            
        Returns:
            List of Worklog model instances
        """
        # Ensure debug_level is valid to prevent hanging
        if debug_level not in ['none', 'error', 'info', 'verbose']:
            logging.warning(f"Invalid debug_level: {debug_level}, defaulting to 'none'")
            debug_level = 'none'
            
        # Set up logging based on debug level
        show_debug = debug_level == 'verbose'
        show_info = debug_level in ('info', 'verbose')
        
        if show_info:
            logging.info("Starting get_user_worklogs in WorklogService")
        
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
        jql = f"worklogDate >= {formatted_start} AND worklogDate <= {formatted_end}"
        
        # Add username constraint if provided - ensure email addresses are properly quoted
        if username:
            # Make sure we properly quote the username, especially for email addresses
            quoted_username = f'"{username}"'
            jql += f" AND worklogAuthor = {quoted_username}"
        
        if show_info:
            logging.info(f"Using JQL: {jql}")
        
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
            
            if show_info:
                logging.info("Sending API request to search for issues")
            
            response = self.client.get(self._get_endpoint("search"), params=params)
            
            if show_info:
                logging.info("API request completed successfully")
                if "issues" in response:
                    logging.info(f"Found {len(response.get('issues', []))} issues with worklogs")
            
            if "issues" not in response:
                if show_info:
                    logging.info(f"No issues found with JQL: {jql}")
                return []
            
            if show_info:
                logging.info(f"Found {len(response.get('issues', []))} issues with worklogs")
                
            # Collect all worklogs from the returned issues
            all_worklogs: List[Worklog] = []
            
            # Add a debug timeout to prevent hanging
            max_issues = 100  # Prevent processing too many issues
            processed_issues = 0
            total_issues = len(response.get("issues", []))
            
            for i, issue in enumerate(response.get("issues", [])):
                # Safety check to prevent infinite processing
                processed_issues += 1
                if processed_issues > max_issues:
                    logging.warning(f"Reached maximum number of issues to process: {max_issues}")
                    break
                
                issue_key = issue.get("key", "")
                issue_summary = issue.get("fields", {}).get("summary", "")
                
                if show_info:
                    logging.info(f"Processing issue {i+1}/{total_issues}: {issue_key}")
                
                if show_debug:
                    print(f"DEBUG: Processing issue {issue_key}: {issue_summary}")
                
                # Get detailed worklogs for this issue
                try:
                    if show_info:
                        logging.info(f"Fetching worklogs for issue {issue_key}")
                        
                    worklogs_response = self.client.get(
                        self._get_endpoint(f"issue/{issue_key}/worklog")
                    )
                    
                    # Convert to WorklogList model
                    worklog_list = WorklogList.from_api(worklogs_response)
                    issue_worklogs = worklog_list.worklogs
                    
                    if show_info:
                        logging.info(f"Found {len(issue_worklogs)} worklogs for issue {issue_key}")
                    
                    if show_debug:
                        print(f"DEBUG: Found {len(issue_worklogs)} worklogs for issue {issue_key}")
                    
                    # Filter by date range and username if specified
                    for worklog in issue_worklogs:
                        # Add issue information to each worklog (using the non-API fields)
                        worklog.issue_key = issue_key
                        worklog.issue_summary = issue_summary
                        
                        # Also add these as camelCase versions for compatibility with different consumers
                        setattr(worklog, "issueKey", issue_key)
                        setattr(worklog, "issueSummary", issue_summary)
                        
                        # Apply date filter
                        if hasattr(worklog, 'started'):
                            worklog_date = worklog.started.strftime("%Y-%m-%d")
                            if worklog_date >= start_date and worklog_date <= end_date:
                                # Apply username filter if specified
                                if username:
                                    author_name = worklog.author.display_name.lower()
                                    author_email = getattr(worklog.author, 'email_address', '') or ''
                                    author_id = worklog.author.account_id
                                    
                                    # Check if any author field contains our username
                                    username_lower = username.lower()
                                    if (username_lower in author_name or 
                                        username_lower in author_email.lower() or
                                        username_lower == author_id):
                                        all_worklogs.append(worklog)
                                        if show_debug:
                                            print(f"DEBUG: Added worklog by {author_name} for {issue_key}")
                                else:
                                    all_worklogs.append(worklog)
                                    if show_debug:
                                        author_name = worklog.author.display_name
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