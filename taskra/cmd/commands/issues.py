"""Issue command implementation."""

import os
import click
import datetime
from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text
from typing import Dict, Any
import requests

from ..utils.formatting import convert_adf_to_rich_text

# Create console for rich text formatting
console = Console()

@click.command("issue")
@click.argument("issue_key")
@click.option("--json", "-j", is_flag=True, help="Output raw JSON")
@click.option("--debug", "-d", is_flag=True, help="Show debug information")
@click.option("--worklogs", "-w", is_flag=True, help="Show worklog entries for the issue")
@click.option("--start-date", "-s", help="Start date for worklogs (YYYY-MM-DD)")
@click.option("--end-date", "-e", help="End date for worklogs (YYYY-MM-DD)")
@click.option("--all-time", "-a", is_flag=True, help="Show all worklogs (no date filtering)")
def issue_cmd(issue_key, json, debug, worklogs, start_date, end_date, all_time):
    """Get information about a specific issue."""
    # Import here for cleaner testing
    from ...core import get_issue, get_issue_comments, list_worklogs
    import datetime
    
    try:
        if json:
            # If JSON flag is provided, output raw JSON
            import json as json_lib
            issue_data = get_issue(issue_key)
            console.print(json_lib.dumps(issue_data, indent=2, default=str))
            return
            
        console.print(f"[bold blue]Issue details for {issue_key}[/bold blue]")
        issue_data = get_issue(issue_key)
        fields = issue_data.get("fields", {})
        
        # If debug mode is enabled, add raw field information at the beginning
        if debug:
            console.print("[bold yellow]Debug Information:[/bold yellow]")
            
            # Show fields that are most important for debugging - improved logging
            debug_fields = ["issuetype", "assignee", "reporter", "status", "priority"]
            for key in debug_fields:
                if key in fields:
                    value = fields[key]
                    console.print(f"[dim yellow]- {key}:[/dim yellow] {value}")
                else:
                    console.print(f"[dim red]- {key}: Not found in response[/dim red]")
        
        # Handle worklog display if the flag is set
        if worklogs:
            _display_worklogs(issue_key, start_date, end_date, all_time, debug)
            
            # If only worklogs are requested, return now
            if json or not worklogs:
                return
        
        # Get the summary for the title
        summary = fields.get("summary", "No summary provided")
        
        # Create a single table with HEAVY borders for improved visibility but reduced padding
        # Use a single column layout with a title that includes the issue key and summary
        issue_table = Table(
            box=box.DOUBLE_EDGE, 
            show_header=False, 
            expand=True, 
            padding=(0, 1),  # Reduce vertical padding to 0 to make it more compact
            title=f"[bold cyan]{issue_key}:[/bold cyan] {summary}",
            title_justify="center",
            title_style="bold white"
        )
        issue_table.add_column("Content", style="green")  # Single column for all content
        
        # ===== SECTION: DETAILS =====
        details = _format_issue_details(fields, debug)
        issue_table.add_row(details)
        
        # ===== SECTION: DESCRIPTION =====
        _add_description_to_table(issue_table, fields, debug)
        
        # ===== SECTION: COMMENTS =====
        _add_comments_to_table(issue_table, issue_key, debug)
        
        # Print the table
        console.print(issue_table)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[bold red]Error:[/bold red] Issue not found (404)")
        else:
            raise
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if debug:
            import traceback
            console.print("[bold red]Traceback:[/bold red]")
            console.print(traceback.format_exc())
        # Don't propagate the exception during testing
        if os.environ.get("TASKRA_TESTING") != "1":
            raise

@click.command("issues")
@click.argument("issue_key", required=True)
@click.option("--json", "-j", is_flag=True, help="Output raw JSON")
@click.option("--worklogs", "-w", is_flag=True, help="Include worklogs")
@click.option("--start", "-s", help="Start date for worklogs in format YYYY-MM-DD")
@click.option("--end", "-e", help="End date for worklogs in format YYYY-MM-DD")
@click.option("--all-time", "-a", is_flag=True, help="Show all worklogs (no date filtering)")
@click.option("--debug", "-d", is_flag=True, help="Show debug information")
@click.option("--refresh-cache", "-r", is_flag=True, help="Force refresh of cached worklog data")
def issues_cmd(issue_key, json, worklogs, start, end, all_time, debug, refresh_cache):
    """Get details for a specific issue by key."""
    # Import here for cleaner testing
    from ...core import get_issue, list_worklogs
    import datetime
    
    try:
        if json:
            # If JSON flag is provided, output raw JSON
            import json as json_lib
            issue_data = get_issue(issue_key)
            console.print(json_lib.dumps(issue_data, indent=2, default=str))
            return
            
        console.print(f"[bold blue]Issue {issue_key}[/bold blue]")
        issue_data = get_issue(issue_key)
        fields = issue_data.get("fields", {})
        
        # Handle worklog display if the flag is set
        if worklogs:
            _display_worklogs(issue_key, start, end, all_time, debug, refresh_cache)
            
            # If only worklogs are requested, return now
            if json or not worklogs:
                return
        
        # Get the summary for the title
        summary = fields.get("summary", "No summary provided")
        
        # Print the summary
        console.print(f"[bold cyan]Summary:[/bold cyan] {summary}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[bold red]Error:[/bold red] Issue not found (404)")
        else:
            raise
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if debug:
            import traceback
            console.print("[bold red]Traceback:[/bold red]")
            console.print(traceback.format_exc())
        # Don't propagate the exception during testing
        if os.environ.get("TASKRA_TESTING") != "1":
            raise

def _display_worklogs(issue_key, start_date, end_date, all_time, debug, refresh_cache=False):
    """Display worklogs for an issue."""
    from ...core import list_worklogs
    import datetime
    
    # If all-time flag is set, don't filter by date range (no date filtering)
    if all_time:
        start_date = None
        end_date = None
        if debug:
            console.print("[yellow]Fetching all worklogs (no date filtering)[/yellow]")
    # Set default dates if not provided and not all-time
    elif not all_time:
        if not start_date:
            # Default to 90 days ago instead of just 1
            past_date = datetime.datetime.now() - datetime.timedelta(days=90)
            start_date = past_date.strftime("%Y-%m-%d")
            
        if not end_date:
            # Default to today
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if debug:
            console.print(f"[yellow]Fetching worklogs from {start_date} to {end_date}[/yellow]")
        
    if refresh_cache and debug:
        console.print("[yellow]Refreshing worklog cache...[/yellow]")
        
    # Get worklogs for this issue
    issue_worklogs = list_worklogs(issue_key, refresh_cache=refresh_cache)
    
    # Filter by date range if dates are specified
    filtered_worklogs = []
    if start_date and end_date:
        for worklog in issue_worklogs:
            # Get the date from the worklog
            worklog_date = None
            if "started" in worklog:
                started = worklog["started"]
                if isinstance(started, datetime.datetime):
                    worklog_date = started.strftime("%Y-%m-%d")
                elif isinstance(started, str) and "T" in started:
                    worklog_date = started.split("T")[0]
            
            # Only include if within the date range
            if worklog_date and start_date <= worklog_date <= end_date:
                filtered_worklogs.append(worklog)
    else:
        # No date filtering
        filtered_worklogs = issue_worklogs
    
    # Display the worklogs
    if filtered_worklogs:
        _display_worklog_table(filtered_worklogs, issue_key)
    else:
        date_range_msg = f" between {start_date} and {end_date}" if start_date and end_date else ""
        console.print(f"[yellow]No worklogs found for {issue_key}{date_range_msg}.[/yellow]")

def _display_worklog_table(worklogs, issue_key):
    """Display worklogs in a table format."""
    import datetime
    
    table = Table(title=f"Worklogs for {issue_key}")
    table.add_column("Date", style="cyan")
    table.add_column("Time", style="cyan")  # New column for time
    table.add_column("Author", style="yellow")
    table.add_column("Time Spent", style="magenta")
    table.add_column("Comment", style="blue")
    
    total_seconds = 0
    for worklog in worklogs:
        # Format the date and time separately
        date_str = ""
        time_str = ""
        if "started" in worklog:
            started = worklog["started"]
            if isinstance(started, datetime.datetime):
                date_str = started.strftime("%Y-%m-%d")
                time_str = started.strftime("%H:%M")
            elif isinstance(started, str) and "T" in started:
                parts = started.split("T")
                date_str = parts[0]
                # Extract time portion (remove timezone if present)
                time_part = parts[1].split("+")[0].split(".")[0]
                time_str = time_part[:5]  # Just take HH:MM
        
        # Get author name
        author = worklog.get("author", {}).get("displayName", "")
        
        # Get time spent
        time_spent = worklog.get("timeSpent", "")
        total_seconds += worklog.get("timeSpentSeconds", 0)
        
        # Get comment if it exists
        comment = _extract_worklog_comment(worklog)
        
        table.add_row(date_str, time_str, author, time_spent, comment)
    
    console.print(table)
    
    # Show total time spent
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    if hours > 0 and minutes > 0:
        total_time = f"{hours}h {minutes}m"
    elif hours > 0:
        total_time = f"{hours}h"
    else:
        total_time = f"{minutes}m"
        
    console.print(f"\nTotal time logged: [bold]{total_time}[/bold] ({len(worklogs)} entries)")

def _extract_worklog_comment(worklog):
    """Extract comment text from a worklog entry."""
    comment = ""
    if "comment" in worklog:
        if isinstance(worklog["comment"], str):
            comment = worklog["comment"]
        elif isinstance(worklog["comment"], dict) and "content" in worklog["comment"]:
            # Extract text from Atlassian Document Format if possible
            try:
                comment_content = worklog["comment"].get("content", [])
                text_parts = []
                for paragraph in comment_content:
                    for text_node in paragraph.get("content", []):
                        if "text" in text_node:
                            text_parts.append(text_node["text"])
                comment = " ".join(text_parts) if text_parts else ""
            except Exception:
                comment = "Complex comment format"
    return comment

def _format_issue_details(fields: Dict[str, Any], debug: bool = False) -> str:
    """Format issue details as a string."""
    import datetime
    
    # Extract status
    status = "Unknown"
    if "status" in fields and fields["status"]:
        status = fields["status"].get("name", "Unknown")
        status_category = fields["status"].get("statusCategory", {}).get("name", "")
        if status_category:
            status = f"{status} ({status_category})"
    
    # Extract issue type - Significantly improved extraction with better fallbacks
    issue_type = "Unknown"
    if "issuetype" in fields:
        issuetype_data = fields["issuetype"]
        if debug:
            console.print(f"[dim yellow]Debug - Issue type data:[/dim yellow] {issuetype_data}")
            
        if isinstance(issuetype_data, dict):
            # Try all possible field names for the name of the issue type
            issue_type = (issuetype_data.get("name") or 
                         issuetype_data.get("displayName") or 
                         issuetype_data.get("display_name") or 
                         issuetype_data.get("value") or 
                         "Unknown")
        elif isinstance(issuetype_data, str):
            issue_type = issuetype_data
    
    # Additional check for alternative field names
    if issue_type == "Unknown" and "issueType" in fields:  # Try camel case variant
        issuetype_data = fields["issueType"]
        if isinstance(issuetype_data, dict):
            issue_type = (issuetype_data.get("name") or 
                         issuetype_data.get("value") or 
                         "Unknown")
        elif isinstance(issuetype_data, str):
            issue_type = issuetype_data
    
    # If all else fails, check for issue_type (snake case)
    if issue_type == "Unknown" and "issue_type" in fields:
        issuetype_data = fields["issue_type"]
        if isinstance(issuetype_data, dict):
            issue_type = (issuetype_data.get("name") or 
                         issuetype_data.get("value") or 
                         "Unknown")
        elif isinstance(issuetype_data, str):
            issue_type = issuetype_data
    
    # Extract priority
    priority = "None"
    if "priority" in fields and fields["priority"]:
        priority = fields["priority"].get("name", "None")
    
    # Extract assignee - More detailed extraction
    assignee = "Unassigned"
    if "assignee" in fields:
        assignee_data = fields["assignee"]
        if isinstance(assignee_data, dict):
            # Check for both camel case and snake case field names
            assignee = (assignee_data.get("displayName") or 
                       assignee_data.get("display_name") or 
                       assignee_data.get("name", "Unknown"))
        elif isinstance(assignee_data, str):
            assignee = assignee_data
        elif assignee_data is None:
            assignee = "Unassigned"
    
    # Extract reporter - More detailed extraction
    reporter = "Unknown"
    if "reporter" in fields:
        reporter_data = fields["reporter"]
        if isinstance(reporter_data, dict):
            # Check for both camel case and snake case field names
            reporter = (reporter_data.get("displayName") or 
                       reporter_data.get("display_name") or 
                       reporter_data.get("name", "Unknown"))
        elif isinstance(reporter_data, str):
            reporter = reporter_data
    
    # Format dates
    created_str = "Unknown"
    updated_str = "Unknown"
    if "created" in fields and fields["created"]:
        created_date = fields["created"]
        # Handle datetime object
        if isinstance(created_date, datetime.datetime):
            created_str = created_date.strftime("%Y-%m-%d %H:%M:%S")
        # Handle string in ISO format
        elif isinstance(created_date, str) and "T" in created_date:
            parts = created_date.split("T")
            created_str = f"{parts[0]} {parts[1][:8]}"
        else:
            created_str = str(created_date)
    if "updated" in fields and fields["updated"]:
        updated_date = fields["updated"]
        # Handle datetime object
        if isinstance(updated_date, datetime.datetime):
            updated_str = updated_date.strftime("%Y-%m-%d %H:%M:%S")
        # Handle string in ISO format
        elif isinstance(updated_date, str) and "T" in updated_date:
            parts = updated_date.split("T")
            updated_str = f"{parts[0]} {parts[1][:8]}"
        else:
            updated_str = str(updated_date)
    
    # If debug is enabled, print what values we're actually using
    if debug:
        console.print("[dim yellow]Using the following values:[/dim yellow]")
        console.print(f"[dim yellow]- Status:[/dim yellow] {status}")
        console.print(f"[dim yellow]- Type:[/dim yellow] {issue_type} (from field: {'issuetype' if 'issuetype' in fields else 'issueType' if 'issueType' in fields else 'issue_type' if 'issue_type' in fields else 'Not found'})")
        console.print(f"[dim yellow]- Priority:[/dim yellow] {priority}")
        console.print(f"[dim yellow]- Assignee:[/dim yellow] {assignee}")
        console.print(f"[dim yellow]- Reporter:[/dim yellow] {reporter}")
    
    # Format all details as a single line with key-value pairs
    details = f"[bold]Status:[/bold] {status} | [bold]Type:[/bold] {issue_type} | [bold]Priority:[/bold] {priority} | "
    details += f"[bold]Assignee:[/bold] {assignee} | [bold]Reporter:[/bold] {reporter} | "
    details += f"[bold]Created:[/bold] {created_str} | [bold]Updated:[/bold] {updated_str}"
    
    return details

def _add_description_to_table(issue_table, fields, debug):
    """Add description section to the issue table."""
    rich_desc = None
    if "description" in fields and fields["description"]:
        description = fields["description"]
        
        # Debug all content if requested
        if debug and isinstance(description, dict):
            console.print("[dim yellow]Description structure preview:[/dim yellow]")
            try:
                import json as json_lib
                desc_preview = json_lib.dumps(description, indent=2)
                # Only show first few lines to avoid overwhelming output
                preview_lines = desc_preview.split("\n")[:10]
                if len(preview_lines) < len(desc_preview.split("\n")):
                    preview_lines.append("  ... (truncated)")
                console.print("\n".join(preview_lines))
            except Exception:
                console.print("[dim]Could not serialize description[/dim]")
        
        # Handle different description formats
        if isinstance(description, str):
            rich_desc = Text(description)
        elif isinstance(description, dict):
            if "content" in description:
                # Convert from Atlassian Document Format to Rich Text
                rich_desc = convert_adf_to_rich_text(description)
            elif "text" in description:
                rich_desc = Text(description["text"])
                
                if debug and rich_desc:
                    console.print(f"[dim yellow]Extracted rich description[/dim yellow]")
    
    # Add the description section
    # Use bold and underlined text for the section header instead of a panel
    issue_table.add_row(Text("\nDESCRIPTION", style="bold underline"))
    if rich_desc:
        issue_table.add_row(rich_desc)
    else:
        issue_table.add_row(Text("No description provided", style="italic"))

def _add_comments_to_table(issue_table, issue_key, debug):
    """Add comments section to the issue table."""
    from ...core import get_issue_comments
    try:
        comments = get_issue_comments(issue_key)
        
        # Use bold and underlined text for the section header
        issue_table.add_row(Text("\nCOMMENTS", style="bold underline"))
        
        # Process comments
        if comments:
            # Format all comments into a readable format
            for i, comment in enumerate(comments):
                author = comment.get("author", {}).get("displayName", "Unknown")
                created = comment.get("created", "Unknown date")
                
                # Format the date if it's ISO format
                if isinstance(created, str) and "T" in created:
                    parts = created.split("T")
                    created = f"{parts[0]} {parts[1][:8]}"
                
                # Get comment body
                comment_content = None
                if isinstance(comment.get("body"), str):
                    comment_content = Text(comment.get("body"))
                elif isinstance(comment.get("body"), dict) and "content" in comment.get("body", {}):
                    # Convert from Atlassian Document Format to Rich Text
                    comment_content = convert_adf_to_rich_text(comment.get("body"))
                
                # Add a divider between comments except for the first one
                if i > 0:
                    issue_table.add_row(Text("-" * 40))
                
                # Format the comment with author, date and content
                comment_header = Text()
                comment_header.append(author, style="bold blue")
                comment_header.append(" commented on ", style="default")
                comment_header.append(created, style="italic")
                issue_table.add_row(comment_header)
                if comment_content:
                    issue_table.add_row(comment_content)
                else:
                    issue_table.add_row(Text("No content", style="italic"))
        else:
            issue_table.add_row(Text("No comments found", style="italic"))
    except Exception as e:
        issue_table.add_row(Text("Error loading comments", style="italic"))
        if debug:
            console.print(f"[bold red]Error fetching comments:[/bold red] {str(e)}")