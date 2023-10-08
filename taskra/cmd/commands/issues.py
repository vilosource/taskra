"""Issue command implementation."""

import os
import click
import requests
from rich.console import Console

# Create console for rich text formatting
console = Console()

@click.command("issue")
@click.argument("issue_key")
@click.option("--json", "-j", is_flag=True, help="Output raw JSON")
@click.option("--debug", "-d", is_flag=True, help="Show debug information")
@click.option("--worklogs", "-w", is_flag=True, help="Show worklog entries for the issue")
@click.option("--comments", "-c", is_flag=True, help="Show comments for the issue")
@click.option("--start-date", "-s", help="Start date for worklogs (YYYY-MM-DD)")
@click.option("--end-date", "-e", help="End date for worklogs (YYYY-MM-DD)")
@click.option("--all-time", "-a", is_flag=True, help="Show all worklogs (no date filtering)")
def issue_cmd(issue_key, json, debug, worklogs, comments, start_date, end_date, all_time):
    """Get information about a specific issue."""
    # Import here for cleaner testing
    from ...core import get_issue, get_issue_comments
    from ...presentation import render_issue, render_issue_comments, render_error, render_worklogs
    
    try:
        # First display the main issue details unless only specific data was requested in JSON format
        show_issue = not (json and (comments or worklogs) and not (comments and worklogs))
        
        if show_issue:
            # Get issue data - this is our core business logic
            issue_data = get_issue(issue_key)
            
            # Delegate presentation to separate service
            render_issue(issue_data, format="json" if json else "table")
        
        # After showing issue details, show comments if requested
        if comments:
            _show_comments(issue_key, debug, json)
            
        # Finally show worklogs if requested
        if worklogs:
            _show_worklogs(issue_key, start_date, end_date, all_time, debug, json)
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[bold red]Error:[/bold red] Issue not found (404)")
        else:
            raise
    except Exception as e:
        # Delegate error handling to presentation layer
        render_error(e, debug)
        # Don't propagate the exception during testing
        if os.environ.get("TASKRA_TESTING") != "1":
            raise

def _show_worklogs(issue_key, start_date, end_date, all_time, debug, json_output):
    """Get and display worklogs for an issue."""
    from ...core import list_worklogs
    from ...presentation import render_worklogs
    import datetime
    
    # If all-time flag is set, don't filter by date range
    if all_time:
        start_date = None
        end_date = None
        if debug:
            console.print("[yellow]Fetching all worklogs (no date filtering)[/yellow]")
    # Set default dates if not provided and not all-time
    elif not all_time:
        if not start_date:
            # Default to 90 days ago
            past_date = datetime.datetime.now() - datetime.timedelta(days=90)
            start_date = past_date.strftime("%Y-%m-%d")
            
        if not end_date:
            # Default to today
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if debug:
            console.print(f"[yellow]Fetching worklogs from {start_date} to {end_date}[/yellow]")
    
    # Get worklogs for this issue - bypass cache to avoid serialization errors with Pydantic models
    worklogs = list_worklogs(issue_key, refresh_cache=True)
    
    # Filter by date range if dates are specified
    if start_date and end_date:
        filtered_worklogs = _filter_worklogs_by_date(worklogs, start_date, end_date)
    else:
        filtered_worklogs = worklogs
    
    # Render worklogs using presentation layer
    render_worklogs(filtered_worklogs, issue_key, format="json" if json_output else "table")

def _filter_worklogs_by_date(worklogs, start_date, end_date):
    """Filter worklogs by date range."""
    import datetime
    
    filtered = []
    for worklog in worklogs:
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
            filtered.append(worklog)
    
    return filtered

def _show_comments(issue_key, debug, json_output):
    """Get and display comments for an issue."""
    from ...core import get_issue_comments
    from ...presentation import render_issue_comments
    
    if debug:
        console.print(f"[yellow]Fetching comments for {issue_key}[/yellow]")
    
    # Get comments for this issue
    comments = get_issue_comments(issue_key)
    
    # Render comments using presentation layer
    render_issue_comments(issue_key, comments, format="json" if json_output else "table")