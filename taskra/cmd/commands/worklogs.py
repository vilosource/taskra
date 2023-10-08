"""Worklogs command implementation."""

import click
import logging
import datetime
import os
import signal
from rich.console import Console
from rich.table import Table
import threading
import time
import sys
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

# Create console for rich text formatting
console = Console()

@click.command("worklogs")
@click.option("--username", "-u", help="Username to filter worklogs by (defaults to current user)")
@click.option("--start", "-s", help="Start date in format YYYY-MM-DD (defaults to yesterday)")
@click.option("--end", "-e", help="End date in format YYYY-MM-DD (defaults to today)")
@click.option("--json", "-j", is_flag=True, help="Output raw JSON")
@click.option("--refresh-cache", "-r", is_flag=True, help="Force refresh of cached data")
@click.option("--timeout", "-t", type=int, default=30, help="Timeout in seconds (default: 30)")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed progress information")
@click.pass_context
def worklogs_cmd(ctx, username, start, end, json, refresh_cache, timeout, verbose):
    """Get worklogs for a user."""
    # Import here for cleaner testing
    from ...core import get_user_worklogs
    
    # Use the debug level from the global context
    debug_level = ctx.obj.debug_level
    logger = logging.getLogger(__name__)
    
    # Add a timeout to prevent hanging
    result_container = []
    error_container = []
    status_container = {"current_step": "Initializing", "progress": 0}
    
    def fetch_worklogs():
        try:
            status_container["current_step"] = "Preparing request"
            status_container["progress"] = 10
            
            logger.info("Fetching worklogs")
            if username:
                logger.info(f"User: {username}")
            logger.info(f"From: {start or 'yesterday'}")
            logger.info(f"To: {end or 'today'}")
            
            if refresh_cache:
                logger.info("Refreshing cache...")
                status_container["current_step"] = "Refreshing cache"
            else:
                status_container["current_step"] = "Checking cache"
            
            status_container["progress"] = 20
            
            # Capture the result in the container
            status_container["current_step"] = "Fetching data from API"
            status_container["progress"] = 30
            
            data = get_user_worklogs(
                username=username, 
                start_date=start, 
                end_date=end, 
                refresh_cache=refresh_cache,
                timeout=timeout
            )
            
            status_container["current_step"] = "Processing results"
            status_container["progress"] = 80
            
            result_container.append(data)
            status_container["current_step"] = "Complete"
            status_container["progress"] = 100
            
        except Exception as e:
            error_container.append(e)
            status_container["current_step"] = f"Error: {str(e)}"
            status_container["progress"] = 100
    
    # Start fetching in a separate thread
    fetch_thread = threading.Thread(target=fetch_worklogs)
    fetch_thread.daemon = True
    fetch_thread.start()
    
    # Wait for completion with timeout and show progress
    start_time = time.time()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Fetching worklogs...", total=100)
        
        last_step = ""
        while fetch_thread.is_alive() and time.time() - start_time < timeout:
            # Update progress based on status
            current_step = status_container["current_step"]
            current_progress = status_container["progress"]
            
            # Only update description if it changed
            if current_step != last_step:
                progress.update(task, description=f"[bold blue]{current_step}")
                last_step = current_step
                
                # Show more detailed info if verbose
                if verbose:
                    console.print(f"[dim]{datetime.datetime.now().strftime('%H:%M:%S')} - {current_step}[/dim]")
            
            progress.update(task, completed=current_progress)
            
            # Short sleep to prevent CPU spinning
            fetch_thread.join(0.1)
    
    # Check the result
    if fetch_thread.is_alive():
        logger.error(f"Operation timed out after {timeout} seconds")
        console.print(f"\n[bold red]Error:[/bold red] Operation timed out after {timeout} seconds")
        console.print("[yellow]Try increasing the timeout with --timeout option or check your network connection.[/yellow]")
        os._exit(1)
    
    if error_container:
        logger.error(f"Error: {str(error_container[0])}")
        console.print(f"\n[bold red]Error:[/bold red] {str(error_container[0])}")
        if debug_level in ['info', 'verbose']:
            import traceback
            traceback.print_exception(type(error_container[0]), error_container[0], error_container[0].__traceback__)
        return
    
    worklogs_data = result_container[0] if result_container else []
    
    # Process the results as before
    if not worklogs_data:
        logger.info("No worklogs found.")
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
    
    # Show a summary of what we're displaying
    date_range = f"{start or 'yesterday'} to {end or 'today'}"
    user_info = f"for {username}" if username else "for current user"
    console.print(f"[bold]Displaying worklogs {user_info} from {date_range}[/bold]")
    
    # Add a counter to show progress for large result sets
    total_worklogs = len(worklogs_data)
    if total_worklogs > 100 and verbose:
        with Progress() as progress:
            task = progress.add_task("Processing worklogs...", total=total_worklogs)
            
            for i, worklog in enumerate(worklogs_data):
                # ... existing worklog processing code ...
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
                        # Extract time part (remove seconds and timezone if present)
                        if len(parts) > 1:
                            time_part = parts[1].split("+")[0].split(".")[0]  # Remove timezone and milliseconds
                            time_str = time_part[:5]  # Just keep HH:MM
                    else:
                        date_str = str(started)
                
                # Extract issue key
                issue_key = worklog.get("issueKey", "")
                if not issue_key:
                    # Try alternative field names that might contain the issue key
                    issue_key = worklog.get("issue_key", "")
                
                # If we still don't have an issue key, try to get it from nested structures
                if not issue_key and "issue" in worklog and isinstance(worklog["issue"], dict):
                    issue_key = worklog["issue"].get("key", "")
                
                # Add issue summary if available
                issue_display = issue_key
                if "issueSummary" in worklog or "issue_summary" in worklog:
                    summary = worklog.get("issueSummary", "") or worklog.get("issue_summary", "")
                    if summary:
                        issue_display = f"{issue_key}: {summary}"
                
                # Get author name
                author = worklog.get("author", {}).get("displayName", "")
                
                # Get time spent
                time_spent = worklog.get("timeSpent", "")
                
                # Get comment if it exists
                comment = _extract_worklog_comment(worklog)
                
                table.add_row(date_str, time_str, issue_display, author, time_spent, comment)
                progress.update(task, advance=1)
    else:
        # Process without progress bar for smaller result sets
        for worklog in worklogs_data:
            # ... existing worklog processing code ...
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
                    # Extract time part (remove seconds and timezone if present)
                    if len(parts) > 1:
                        time_part = parts[1].split("+")[0].split(".")[0]  # Remove timezone and milliseconds
                        time_str = time_part[:5]  # Just keep HH:MM
                else:
                    date_str = str(started)
            
            # Extract issue key
            issue_key = worklog.get("issueKey", "")
            if not issue_key:
                # Try alternative field names that might contain the issue key
                issue_key = worklog.get("issue_key", "")
            
            # If we still don't have an issue key, try to get it from nested structures
            if not issue_key and "issue" in worklog and isinstance(worklog["issue"], dict):
                issue_key = worklog["issue"].get("key", "")
            
            # Add issue summary if available
            issue_display = issue_key
            if "issueSummary" in worklog or "issue_summary" in worklog:
                summary = worklog.get("issueSummary", "") or worklog.get("issue_summary", "")
                if summary:
                    issue_display = f"{issue_key}: {summary}"
            
            # Get author name
            author = worklog.get("author", {}).get("displayName", "")
            
            # Get time spent
            time_spent = worklog.get("timeSpent", "")
            
            # Get comment if it exists
            comment = _extract_worklog_comment(worklog)
            
            table.add_row(date_str, time_str, issue_display, author, time_spent, comment)
    
    console.print(table)
    
    # Show summary statistics
    total_seconds = sum(worklog.get("timeSpentSeconds", 0) for worklog in worklogs_data)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    time_summary = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    console.print(f"\n[bold]Total worklogs:[/bold] {len(worklogs_data)}")
    console.print(f"[bold]Total time logged:[/bold] {time_summary}")

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
