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

@click.group("worklogs")
def worklogs_cmd():
    """Manage worklogs."""
    pass

@worklogs_cmd.command("list")
@click.option("--username", "-u", help="Username to filter worklogs by (defaults to current user)")
@click.option("--all", is_flag=True, help="Show worklogs for all users, not just the current user")
@click.option("--start", "-s", help="Start date in format YYYY-MM-DD (defaults to yesterday)")
@click.option("--end", "-e", help="End date in format YYYY-MM-DD (defaults to today)")
@click.option("--gaps", "-g", is_flag=True, help="Show gaps between worklogs")
@click.option("--json", "-j", is_flag=True, help="Output raw JSON")
@click.option("--refresh-cache", "-r", is_flag=True, help="Force refresh of cached data")
@click.option("--timeout", "-t", type=int, default=30, help="Timeout in seconds (default: 30)")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed progress information")
@click.pass_context
def list_worklogs_cmd(ctx, username, all, start, end, gaps, json, refresh_cache, timeout, verbose):
    """List worklogs for a user or all users."""
    # Import here for cleaner testing
    from ...core import get_user_worklogs
    from ...api.client import get_jira_client
    
    # Use the debug level from the global context
    debug_level = ctx.obj.debug_level
    logger = logging.getLogger(__name__)
    
    # If --all flag is not set and no specific username is provided,
    # get the current user's email to filter by
    current_user_filter = None
    if not all and not username:
        try:
            # Get the current user's email from the auth details
            from ...api.auth import get_auth_details
            
            auth_details = get_auth_details()
            current_user_filter = auth_details.get('email')
            
            if current_user_filter:
                logger.info(f"Filtering worklogs for current user: {current_user_filter}")
            else:
                logger.warning("Could not determine current user email from auth details")
                console.print("[yellow]Could not determine current user, showing all worklogs.[/yellow]")
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            console.print("[yellow]Could not determine current user, showing all worklogs.[/yellow]")
    
    # Use the provided username if specified, otherwise use the current user filter
    effective_username = username or current_user_filter
    
    # Add a timeout to prevent hanging
    result_container = []
    error_container = []
    status_container = {"current_step": "Initializing", "progress": 0}
    
    def fetch_worklogs():
        try:
            status_container["current_step"] = "Preparing request"
            status_container["progress"] = 10
            
            logger.info("Fetching worklogs")
            if effective_username:
                logger.info(f"User: {effective_username}")
            else:
                logger.info("User: all users")
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
                username=effective_username, 
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
    
    # Calculate gaps if requested
    gap_entries = []
    if gaps:
        gap_entries = _calculate_gaps(worklogs_data)
        logger.info(f"Found {len(gap_entries)} gaps in worklogs")
    
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
    if effective_username:
        user_info = f"for {effective_username}"
    else:
        user_info = "for all users"
    
    if gaps:
        console.print(f"[bold]Displaying worklogs with gaps {user_info} from {date_range}[/bold]")
    else:
        console.print(f"[bold]Displaying worklogs {user_info} from {date_range}[/bold]")
    
    # Combine worklogs and gaps for display if gaps are requested
    display_entries = worklogs_data.copy()
    if gaps:
        # Convert gap entries to a format compatible with the table display
        for gap in gap_entries:
            # Format the gap entry like a worklog
            gap_entry = {
                "started": gap["start_time"],
                "is_gap": True,
                "timeSpent": _format_time_duration(gap["duration_seconds"]),
                "timeSpentSeconds": gap["duration_seconds"]
            }
            display_entries.append(gap_entry)
        
        # Re-sort the combined list
        display_entries = sorted(display_entries, key=_parse_worklog_datetime, reverse=True)
    
    # Add a counter to show progress for large result sets
    total_entries = len(display_entries)
    if total_entries > 100 and verbose:
        with Progress() as progress:
            task = progress.add_task("Processing entries...", total=total_entries)
            
            for i, entry in enumerate(display_entries):
                _add_entry_to_table(table, entry)
                progress.update(task, advance=1)
    else:
        for entry in display_entries:
            _add_entry_to_table(table, entry)
    
    console.print(table)
    
    # Calculate and display statistics
    total_logged_seconds = sum(worklog.get("timeSpentSeconds", 0) for worklog in worklogs_data)
    total_gap_seconds = sum(gap["duration_seconds"] for gap in gap_entries) if gaps else 0
    
    logged_hours = total_logged_seconds // 3600
    logged_minutes = (total_logged_seconds % 3600) // 60
    logged_time_summary = f"{logged_hours}h {logged_minutes}m" if logged_hours > 0 else f"{logged_minutes}m"
    
    console.print(f"\n[bold]Total worklogs:[/bold] {len(worklogs_data)}")
    console.print(f"[bold]Total time logged:[/bold] {logged_time_summary}")
    
    if gaps:
        gap_hours = total_gap_seconds // 3600
        gap_minutes = (total_gap_seconds % 3600) // 60
        gap_time_summary = f"{gap_hours}h {gap_minutes}m" if gap_hours > 0 else f"{gap_minutes}m"
        
        console.print(f"[bold]Total gaps:[/bold] {len(gap_entries)}")
        console.print(f"[bold]Total unlogged time:[/bold] {gap_time_summary}")

def _add_entry_to_table(table, entry):
    """Add a worklog or gap entry to the table."""
    date_str = ""
    time_str = ""
    
    # Extract date and time
    if "started" in entry:
        started = entry["started"]
        if isinstance(started, datetime.datetime):
            date_str = started.strftime("%Y-%m-%d")
            time_str = started.strftime("%H:%M")
        elif isinstance(started, str) and "T" in started:
            parts = started.split("T")
            date_str = parts[0]
            if len(parts) > 1:
                time_part = parts[1].split("+")[0].split(".")[0]
                time_str = time_part[:5]
        else:
            date_str = str(started)
    
    # Check if this is a gap entry
    if entry.get("is_gap", False):
        # For gaps, use a special format
        issue_display = "(Unlogged Time)"
        author = ""
        time_spent = entry.get("timeSpent", "")
        comment = ""
        
        # Use a different style for gap entries
        table.add_row(
            date_str, 
            time_str, 
            f"[bold red]{issue_display}[/bold red]", 
            author, 
            f"[bold red]{time_spent}[/bold red]", 
            comment
        )
    else:
        # For regular worklogs, use the normal format
        issue_key = entry.get("issueKey", "")
        if not issue_key:
            issue_key = entry.get("issue_key", "")
        
        if not issue_key and "issue" in entry and isinstance(entry["issue"], dict):
            issue_key = entry["issue"].get("key", "")
        
        issue_display = issue_key
        if "issueSummary" in entry or "issue_summary" in entry:
            summary = entry.get("issueSummary", "") or entry.get("issue_summary", "")
            if summary:
                issue_display = f"{issue_key}: {summary}"
        
        author = entry.get("author", {}).get("displayName", "")
        time_spent = entry.get("timeSpent", "")
        comment = _extract_worklog_comment(entry)
        
        table.add_row(date_str, time_str, issue_display, author, time_spent, comment)

@worklogs_cmd.command("add")
@click.argument("issue_key", required=True)
@click.argument("time_spent", required=True)
@click.option("--comment", "-c", help="Comment for the worklog")
@click.option("--date", "-d", help="Date for the worklog (YYYY-MM-DD, defaults to today)")
@click.option("--time", "-t", help="Time for the worklog (HH:MM, defaults to current time)")
@click.option("--json", "-j", is_flag=True, help="Output raw JSON")
@click.option("--debug", is_flag=True, help="Show debug information")
@click.pass_context
def add_worklog_cmd(ctx, issue_key, time_spent, comment, date, time, json, debug):
    """
    Add a worklog to an issue.
    
    ISSUE_KEY: The issue key (e.g., PROJECT-123)
    
    TIME_SPENT: Time spent in format like '1h 30m'
    """
    from ...core import add_worklog
    import json as json_lib
    
    logger = logging.getLogger(__name__)
    
    debug_level = ctx.obj.debug_level
    
    if debug or debug_level in ['info', 'verbose']:
        logger.info(f"Adding worklog to issue {issue_key}")
        logger.info(f"Time spent: {time_spent}")
        if comment:
            logger.info(f"Comment: {comment}")
        if date:
            logger.info(f"Date: {date}")
        if time:
            logger.info(f"Time: {time}")
    
    started = None
    if date or time:
        from datetime import datetime as dt
        
        if not date:
            date = dt.now().strftime("%Y-%m-%d")
            
        if not time:
            time = dt.now().strftime("%H:%M")
            
        try:
            started = dt.fromisoformat(f"{date}T{time}:00")
            if debug or debug_level in ['info', 'verbose']:
                logger.info(f"Using start time: {started.isoformat()}")
        except ValueError as e:
            console.print(f"[bold red]Error:[/bold red] Invalid date or time format: {str(e)}")
            console.print("[yellow]Use YYYY-MM-DD for date and HH:MM for time.[/yellow]")
            return
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Adding worklog..."),
            console=console,
            transient=True
        ) as progress:
            progress.add_task("Adding", total=None)
            
            result = add_worklog(issue_key, time_spent, comment, started)
        
        if json:
            console.print(json_lib.dumps(result, indent=2))
        else:
            time_spent_display = result.get("timeSpent", time_spent)
            
            issue_display = issue_key
            if "issueSummary" in result or "issue_summary" in result:
                summary = result.get("issueSummary", "") or result.get("issue_summary", "")
                if summary:
                    issue_display = f"{issue_key}: {summary}"
            
            console.print(f"[bold green]✓[/bold green] Added worklog to [bold]{issue_display}[/bold]")
            console.print(f"Time logged: [bold]{time_spent_display}[/bold]")
            
            if comment:
                console.print(f"Comment: {comment}")
            
            if "id" in result:
                console.print(f"Worklog ID: {result['id']}")
    
    except Exception as e:
        logger.error(f"Error adding worklog: {str(e)}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if debug_level in ['info', 'verbose']:
            import traceback
            traceback.print_exception(type(e), e, e.__traceback__)

def _extract_worklog_comment(worklog):
    """Extract comment text from a worklog entry."""
    comment = ""
    if "comment" in worklog:
        if isinstance(worklog["comment"], str):
            comment = worklog["comment"]
        elif isinstance(worklog["comment"], dict) and "content" in worklog["comment"]:
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
        try:
            date_part = started.split("+")[0].split(".")[0]
            return datetime.datetime.fromisoformat(date_part)
        except ValueError:
            return datetime.datetime.min
    return datetime.datetime.min

def _calculate_worklog_end_time(worklog):
    """Calculate the end time of a worklog based on its start time and duration."""
    start_time = _parse_worklog_datetime(worklog)
    if start_time == datetime.datetime.min:
        return start_time
    
    # Get the duration in seconds
    seconds = worklog.get("timeSpentSeconds", 0)
    
    # Calculate end time by adding the duration to the start time
    end_time = start_time + datetime.timedelta(seconds=seconds)
    return end_time

def _format_time_duration(seconds):
    """Format a duration in seconds as a human-readable string (e.g., '2h 30m')."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
    else:
        return f"{minutes}m"

def _calculate_gaps(worklogs, work_day_start_hour=9, work_day_hours=7.5):
    """
    Calculate gaps between worklogs.
    
    Args:
        worklogs: List of worklog entries sorted by start time (newest first)
        work_day_start_hour: Hour when the work day starts (default: 9)
        work_day_hours: Length of work day in hours (default: 7.5)
    
    Returns:
        List of gap entries with date, start time, end time, and duration
    """
    if not worklogs:
        return []
    
    # Group worklogs by date
    worklog_by_date = {}
    for worklog in worklogs:
        start_time = _parse_worklog_datetime(worklog)
        if start_time == datetime.datetime.min:
            continue
            
        date_str = start_time.strftime("%Y-%m-%d")
        if date_str not in worklog_by_date:
            worklog_by_date[date_str] = []
        worklog_by_date[date_str].append(worklog)
    
    # Calculate work day boundaries
    work_day_end_hour = work_day_start_hour + work_day_hours
    work_day_end_minutes = int((work_day_end_hour - int(work_day_end_hour)) * 60)
    work_day_end_hour = int(work_day_end_hour)
    
    # Find gaps for each date
    gaps = []
    for date_str, date_worklogs in worklog_by_date.items():
        # Sort worklogs by start time (oldest first)
        date_worklogs.sort(key=_parse_worklog_datetime)
        
        # Create datetime objects for work day start and end
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        work_start = date_obj.replace(hour=work_day_start_hour, minute=0, second=0)
        work_end = date_obj.replace(hour=work_day_end_hour, minute=work_day_end_minutes, second=0)
        
        # Check for gap at the beginning of the day
        first_worklog_start = _parse_worklog_datetime(date_worklogs[0])
        if first_worklog_start > work_start:
            gap_seconds = int((first_worklog_start - work_start).total_seconds())
            if gap_seconds > 0:
                gaps.append({
                    "date": date_str,
                    "start_time": work_start,
                    "end_time": first_worklog_start,
                    "duration_seconds": gap_seconds,
                    "is_gap": True
                })
        
        # Check for gaps between worklogs
        for i in range(len(date_worklogs) - 1):
            current_end = _calculate_worklog_end_time(date_worklogs[i])
            next_start = _parse_worklog_datetime(date_worklogs[i + 1])
            
            if next_start > current_end:
                gap_seconds = int((next_start - current_end).total_seconds())
                if gap_seconds > 0:
                    gaps.append({
                        "date": date_str,
                        "start_time": current_end,
                        "end_time": next_start,
                        "duration_seconds": gap_seconds,
                        "is_gap": True
                    })
        
        # Check for gap at the end of the day
        last_worklog_end = _calculate_worklog_end_time(date_worklogs[-1])
        if last_worklog_end < work_end:
            gap_seconds = int((work_end - last_worklog_end).total_seconds())
            if gap_seconds > 0:
                gaps.append({
                    "date": date_str,
                    "start_time": last_worklog_end,
                    "end_time": work_end,
                    "duration_seconds": gap_seconds,
                    "is_gap": True
                })
    
    # Sort gaps by date and start time (newest first to match worklog display)
    gaps.sort(key=lambda x: x["start_time"], reverse=True)
    return gaps
