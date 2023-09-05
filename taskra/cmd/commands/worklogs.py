"""Worklogs command implementation."""

import click
import logging
import datetime
import os
from rich.console import Console
from rich.table import Table

# Create console for rich text formatting
console = Console()

@click.command("worklogs")
@click.option("--username", "-u", help="Username to filter worklogs by (defaults to current user)")
@click.option("--start", "-s", help="Start date in format YYYY-MM-DD (defaults to yesterday)")
@click.option("--end", "-e", help="End date in format YYYY-MM-DD (defaults to today)")
@click.option("--json", "-j", is_flag=True, help="Output raw JSON")
@click.option("--debug", "-d", type=click.Choice(['none', 'error', 'info', 'verbose']), 
              default='none', help="Set debug output level")
@click.option("--refresh-cache", "-r", is_flag=True, help="Force refresh of cached data")
def worklogs_cmd(username, start, end, json, debug, refresh_cache):
    """Get worklogs for a user."""
    # Import here for cleaner testing
    from ...core import get_user_worklogs
    
    # Configure logging based on debug level
    if debug == 'verbose':
        logging.basicConfig(level=logging.DEBUG)
        console.print("[yellow]Debug mode: VERBOSE[/yellow]")
    elif debug == 'info':
        logging.basicConfig(level=logging.INFO)
        console.print("[blue]Debug mode: INFO[/blue]")
    elif debug == 'error':
        logging.basicConfig(level=logging.ERROR)
        console.print("[red]Debug mode: ERROR[/red]")
    else:
        # Only show critical errors by default
        logging.basicConfig(level=logging.CRITICAL)
    
    try:
        console.print(f"[bold blue]Fetching worklogs{'': ^10}[/bold blue]")
        if username:
            console.print(f"User: {username}")
        console.print(f"From: {start or 'yesterday'}")
        console.print(f"To: {end or 'today'}")
        
        if refresh_cache:
            console.print("[yellow]Refreshing cache...[/yellow]")
        
        worklogs_data = get_user_worklogs(
            username=username, 
            start_date=start, 
            end_date=end, 
            debug_level=debug,
            refresh_cache=refresh_cache
        )
        
        if not worklogs_data:
            console.print("[yellow]No worklogs found.[/yellow]")
            return
        
        # If JSON output requested, print raw data
        if json:
            import json as json_lib
            console.print(json_lib.dumps(worklogs_data, indent=2))
            return
        
        # Sort worklogs by date and time (newest first)
        worklogs_data = sorted(worklogs_data, key=_parse_worklog_datetime, reverse=True)
        
        # Otherwise, create a nicely formatted table
        table = Table(title="Worklogs")
        table.add_column("Work Date", style="cyan")
        table.add_column("Work Start Time", style="cyan")  # Added column for start time
        table.add_column("Issue", style="green")
        table.add_column("Author", style="yellow")
        table.add_column("Time Spent", style="magenta")
        table.add_column("Comment", style="blue")
        
        for worklog in worklogs_data:
            # Format the date from the 'started' field - this represents when the work was performed
            date_str = ""
            time_str = ""  # New variable to store the time component
            if "started" in worklog:
                started = worklog["started"]
                if isinstance(started, datetime.datetime):
                    date_str = started.strftime("%Y-%m-%d")
                    time_str = started.strftime("%H:%M")
                elif isinstance(started, str) and "T" in started:
                    parts = started.split("T")
                    date_str = parts[0]
                    # Extract time part (remove seconds and timezone if present)
                    if len(parts) > 1:
                        time_part = parts[1].split("+")[0].split(".")[0]  # Remove timezone and milliseconds
                        time_str = time_part[:5]  # Just keep HH:MM
                else:
                    date_str = str(started)
            
            # Extract issue key
            issue_key = worklog.get("issueKey", "")
            
            # Get author name
            author = worklog.get("author", {}).get("displayName", "")
            
            # Get time spent
            time_spent = worklog.get("timeSpent", "")
            
            # Get comment if it exists
            comment = _extract_worklog_comment(worklog)
            
            table.add_row(date_str, time_str, issue_key, author, time_spent, comment)
        
        console.print(table)
        console.print(f"\nTotal worklogs: [bold]{len(worklogs_data)}[/bold]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if os.environ.get("TASKRA_TESTING") != "1":
            raise

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
                comment = " ".join(text_parts) if text_parts else "Complex comment"
            except Exception:
                comment = "Complex comment format"
    return comment

def _parse_worklog_datetime(worklog):
    """Parse the 'started' field from a worklog into a datetime object for sorting."""
    started = worklog.get("started")
    if not started:
        return datetime.datetime.min
    
    if isinstance(started, datetime.datetime):
        return started
    elif isinstance(started, str) and "T" in started:
        # Handle ISO format like "2023-05-22T14:30:00.000+0000"
        try:
            date_part = started.split("+")[0].split(".")[0]
            return datetime.datetime.fromisoformat(date_part)
        except ValueError:
            return datetime.datetime.min
    return datetime.datetime.min
