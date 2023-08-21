"""Report services for generating various Jira reports."""

from typing import Dict, List, Any, Optional
import logging

from .base import BaseService
from .issues import IssuesService
from .projects import ProjectsService


class ReportService(BaseService):
    """Service for generating Jira reports."""
    
    def project_tickets_report(self, filters: Dict[str, Any], max_results: int = 100, debug: bool = False) -> List[Dict[str, Any]]:
        """
        Generate a report of tickets for a project with filters.
        
        Args:
            filters: Dictionary of filters to apply
            max_results: Maximum number of tickets to return (default: 100)
            debug: Enable debug output
            
        Returns:
            List of issue data dictionaries
        """
        # Build JQL query from filters
        jql = self._build_jql_for_project_tickets(filters)
        
        if debug:
            print(f"[DEBUG] Using JQL query: {jql}")
            print(f"[DEBUG] Max results: {max_results}")
            print(f"[DEBUG] Test this JQL query at: {self.client.base_url.replace('rest/api/3/', '')}issues/?jql={jql.replace(' ', '+')}")
        
        # Define fields to retrieve
        fields = [
            "summary", 
            "status", 
            "assignee", 
            "reporter", 
            "created", 
            "updated",
            "priority"
        ]
        
        # Add worklog field if filtering by worklog user
        if "worklog_user" in filters:
            fields.append("worklog")
        
        # Use IssuesService to search for issues
        issues_service = IssuesService(self.client)
        try:
            results = issues_service.search_issues(
                jql=jql,
                fields=fields,
                max_results=max_results
            )
            
            return results.get("issues", [])
        except Exception as e:
            if debug:
                print(f"[DEBUG] Error executing JQL query: {str(e)}")
                # If we got response content in the exception, print it
                if hasattr(e, 'response') and hasattr(e.response, 'content'):
                    print(f"[DEBUG] Response content: {e.response.content.decode('utf-8')}")
            raise
    
    def _build_jql_for_project_tickets(self, filters: Dict[str, Any]) -> str:
        """Build a JQL query from filter options."""
        jql_parts = []
        
        # Project is required
        if "project" in filters:
            jql_parts.append(f'project = "{filters["project"]}"')
        else:
            raise ValueError("Project key is required")
            
        # Date filters - only apply if explicitly provided
        if "start_date" in filters and filters.get("start_date_explicit", False):
            jql_parts.append(f'created >= "{filters["start_date"]}"')
            
        if "end_date" in filters and filters.get("end_date_explicit", False):
            jql_parts.append(f'created <= "{filters["end_date"]}"')
            
        # Status filter (can be multiple)
        if "status" in filters and filters["status"]:
            statuses = ', '.join(f'"{s}"' for s in filters["status"])
            jql_parts.append(f'status in ({statuses})')
            
        # Assignee filter
        if "assignee" in filters:
            jql_parts.append(f'assignee = "{filters["assignee"]}"')
            
        # Reporter filter
        if "reporter" in filters:
            jql_parts.append(f'reporter = "{filters["reporter"]}"')
        
        # Build JQL query
        jql = " AND ".join(jql_parts)
        
        # Add sorting
        sort_field = filters.get("sort_by", "created")
        sort_order = filters.get("sort_order", "DESC").upper()
        jql += f" ORDER BY {sort_field} {sort_order}"
            
        return jql
    
    def cross_project_report(self, project_keys: List[str], filters: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
        """
        Generate a report spanning multiple projects.
        
        Args:
            project_keys: List of project keys to include in the report
            filters: Dictionary of filters to apply
            debug: Enable debug output
            
        Returns:
            Report data dictionary with combined results
        """
        if debug:
            self.logger.debug(f"Generating cross-project report for projects: {project_keys}")
            
        # Access other services as needed
        projects_service = ProjectsService(self.client)
        issues_service = IssuesService(self.client)
        
        # Collect data from multiple sources
        result = {
            "projects": {},
            "summary": {
                "total_issues": 0,
                "projects_count": len(project_keys)
            }
        }
        
        # Process each project
        for project_key in project_keys:
            if debug:
                self.logger.debug(f"Processing project: {project_key}")
                
            # Get project details
            project_data = projects_service.get_project(project_key)
            
            # Create JQL for this project's issues
            jql = self._build_jql_for_project_tickets({**filters, "project": project_key})
            
            # Get issues for this project
            issues = issues_service.search_all_issues(jql)
            
            # Store in results
            result["projects"][project_key] = {
                "name": project_data.get("name", "Unknown"),
                "issues_count": len(issues),
                "issues": issues
            }
            
            result["summary"]["total_issues"] += len(issues)
        
        return result
