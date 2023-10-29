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
def worklogs_cmd(username, start, end, json, debug):
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
        
        worklogs_data = get_user_worklogs(
            username=username, 
            start_date=start, 
            end_date=end, 
            debug_level=debug
        )
        
        if not worklogs_data:
            console.print("[yellow]No worklogs found.[/yellow]")
            return
        
        # If JSON output requested, print raw data
        if json:
            import json as json_lib
            console.print(json_lib.dumps(worklogs_data, indent=2))
            return
        
        # Otherwise, create a nicely formatted table
        table = Table(title="Worklogs")
        table.add_column("Date", style="cyan")
        table.add_column("Issue", style="green")
        table.add_column("Author", style="yellow")
        table.add_column("Time Spent", style="magenta")
        table.add_column("Comment", style="blue")
        
        for worklog in worklogs_data:
            # Format the date from the 'started' field - handling both string and datetime objects
            date_str = ""
            if "started" in worklog:
                started = worklog["started"]
                if isinstance(started, datetime.datetime):
                    date_str = started.strftime("%Y-%m-%d")
                elif isinstance(started, str) and "T" in started:
                    date_str = started.split("T")[0]
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
            
            table.add_row(date_str, issue_key, author, time_spent, comment)
        
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
