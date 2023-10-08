"""Report services for generating various Jira reports."""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from .base import BaseService
from .issues import IssuesService
from .projects import ProjectsService
from ...utils.serialization import to_serializable


class ReportService(BaseService):
    """Service for generating Jira reports."""
    
    def project_tickets_report(self, filters: Dict[str, Any], max_results: int = 100, debug: bool = False) -> List[Dict[str, Any]]:
        """
        Generate a report of project tickets based on filters.
        
        Args:
            filters: Dictionary of filters to apply
            max_results: Maximum number of tickets to return (default: 100)
            debug: Enable debug output
            
        Returns:
            List of issue data dictionaries
        """
        jql_parts = []
        
        # Add project filter with proper quoting
        if 'project_key' in filters and filters['project_key']:
            jql_parts.append(f'project = "{filters["project_key"]}"')
        
        # Add date filters if provided
        if 'start_date' in filters and filters['start_date']:
            jql_parts.append(f'created >= "{filters["start_date"]}"')
        
        if 'end_date' in filters and filters['end_date']:
            jql_parts.append(f'created <= "{filters["end_date"]}"')
        
        # Add status filter if provided
        if 'status' in filters and filters['status']:
            statuses = [f'"{status}"' for status in filters['status']]
            jql_parts.append(f'status in ({", ".join(statuses)})')
        
        # Add assignee filter if provided
        if 'assignee' in filters and filters['assignee']:
            jql_parts.append(f'assignee = "{filters["assignee"]}"')
        
        # Add reporter filter if provided
        if 'reporter' in filters and filters['reporter']:
            jql_parts.append(f'reporter = "{filters["reporter"]}"')
        
        # Combine all JQL parts
        jql = " AND ".join(jql_parts) if jql_parts else ""
        
        # Add sorting
        sort_field = filters.get('sort_by', 'created')
        sort_order = filters.get('sort_order', 'desc')
        if jql:
            jql += f" ORDER BY {sort_field} {sort_order}"
        else:
            jql = f"ORDER BY {sort_field} {sort_order}"
        
        if debug:
            print(f"[DEBUG] JQL query: {jql}")
        
        # Get required fields - passing this as a parameter now
        fields_to_retrieve = ["summary", "status", "assignee", "priority", "created", "updated"]
        
        # Call the search_issues method with the fields parameter
        issues_service = IssuesService(self.client)
        results = issues_service.search_issues(
            jql=jql,
            max_results=max_results,
            fields=fields_to_retrieve,
            debug=debug  # Pass debug flag to search_issues
        )
        
        if debug:
            print(f"JQL: {jql}")
            print(f"Issues found: {results.total}")
        
        return self._format_results(results, debug=debug)
    
    def _format_results(self, results: Any, debug: bool = False) -> List[Dict[str, Any]]:
        """
        Format search results for reporting.
        
        Args:
            results: IssueSearchResults from search_issues
            debug: Enable debug output
            
        Returns:
            List of formatted issue dictionaries
        """
        # Check if we got a Pydantic model
        if hasattr(results, 'model_dump'):
            # Debug first issue structure if requested
            if debug and results.issues:
                from ...utils.debug import dump_model_structure, debug_issue_fields
                print("\nDEBUG: First issue model structure:")
                dump_model_structure(results.issues[0])
                debug_issue_fields(results.issues[0])
                
            # Convert to serializable dict first
            formatted_issues = []
            for issue in results.issues:
                # Extract key fields for report
                formatted_issue = {
                    "key": issue.key,
                    "summary": self._extract_summary(issue),
                    "status": self._extract_status_name(issue),
                    "assignee": self._extract_assignee_name(issue),
                    "priority": self._extract_priority_name(issue),
                    "created": self._extract_datetime(issue, "created"),
                    "updated": self._extract_datetime(issue, "updated"),
                }
                if debug and issue == results.issues[0]:  # Only for the first issue
                    print("\nDEBUG: Formatted issue data:")
                    for k, v in formatted_issue.items():
                        print(f"  {k}: {v}")
                    
                formatted_issues.append(formatted_issue)
            return formatted_issues
            
        # Fallback for dictionary results (backward compatibility)
        return self._format_dict_results(results)
    
    def _extract_summary(self, issue: Any) -> str:
        """Extract summary from an issue with fallbacks."""
        if not hasattr(issue, "fields"):
            return "No summary"
            
        fields = issue.fields
        
        # Direct access to summary field
        if hasattr(fields, "summary") and fields.summary:
            return fields.summary
            
        # Try dict-style access
        if isinstance(fields, dict) and "summary" in fields:
            return fields["summary"]
            
        return "No summary"
    
    def _extract_datetime(self, issue: Any, field_name: str) -> Optional[str]:
        """Extract and format a datetime field from an issue."""
        if not hasattr(issue, "fields"):
            return None
            
        fields = issue.fields
        
        # Try direct attribute access
        value = getattr(fields, field_name, None)
        
        if value:
            # Format datetime object
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d %H:%M")
                
            # Handle string datetime
            if isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    return value
                
        return None
    
    def _extract_status_name(self, issue: Any) -> str:
        """Extract status name from an issue."""
        if not hasattr(issue, "fields"):
            return "Unknown"
            
        fields = issue.fields
        
        # Try using the getter method if available
        if hasattr(fields, "get_status_name"):
            return fields.get_status_name()
        
        # Direct access to status object
        if hasattr(fields, "status") and fields.status:
            status = fields.status
            if hasattr(status, "name"):
                return status.name
            # For dict-style status
            if isinstance(status, dict) and "name" in status:
                return status["name"]
                
        return "Unknown"
            
    def _extract_assignee_name(self, issue: Any) -> str:
        """Extract assignee name from an issue."""
        if not hasattr(issue, "fields"):
            return "Unassigned"
            
        fields = issue.fields
        
        # Try using the getter method if available
        if hasattr(fields, "get_assignee_name"):
            return fields.get_assignee_name()
            
        # Direct access to assignee object
        if hasattr(fields, "assignee") and fields.assignee:
            assignee = fields.assignee
            # Try different attribute names
            for attr in ["display_name", "displayName", "name"]:
                if hasattr(assignee, attr):
                    return getattr(assignee, attr)
            
            # For dict-style assignee
            if isinstance(assignee, dict):
                for key in ["displayName", "name", "emailAddress"]:
                    if key in assignee:
                        return assignee[key]
                    
        return "Unassigned"
            
    def _extract_priority_name(self, issue: Any) -> str:
        """Extract priority name from an issue."""
        if not hasattr(issue, "fields"):
            return "Unknown"
            
        fields = issue.fields
        
        # Try using the getter method if available
        if hasattr(fields, "get_priority_name"):
            return fields.get_priority_name()
            
        # Direct access to priority object
        if hasattr(fields, "priority") and fields.priority:
            priority = fields.priority
            if hasattr(priority, "name"):
                return priority.name
            # For dict-style priority
            if isinstance(priority, dict) and "name" in priority:
                return priority["name"]
                
        return "Unknown"
            
    def _format_dict_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Legacy method to format dictionary results."""
        formatted_issues = []
        for issue in results.get("issues", []):
            fields = issue.get("fields", {})
            formatted_issue = {
                "key": issue.get("key", "Unknown"),
                "summary": fields.get("summary", "No summary"),
                "status": fields.get("status", {}).get("name", "Unknown"),
                "assignee": fields.get("assignee", {}).get("displayName", "Unassigned"),
                "created": fields.get("created"),
                "updated": fields.get("updated"),
                # Add other necessary fields
            }
            formatted_issues.append(formatted_issue)
        return formatted_issues
    
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
