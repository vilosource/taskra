"""Main CLI implementation for Taskra."""

import click
from rich.console import Console
from rich.table import Table
from rich import box
from typing import Optional
import os

console = Console()

@click.group()
@click.version_option()
def cli():
    """Taskra - Task and project management from the command line."""
    pass

@cli.command()
def projects():
    """List available projects."""
    # Import inside function to avoid circular imports
    from ..core import list_projects
    
    console.print("[bold blue]Available Projects:[/bold blue]")
    projects_list = list_projects()
    
    console.print(f"\nTotal projects: [bold]{len(projects_list)}[/bold]")

@cli.command()
@click.argument("issue_key")
@click.option("--json", "-j", is_flag=True, help="Output raw JSON")
@click.option("--debug", "-d", is_flag=True, help="Show debug information")
@click.option("--worklogs", "-w", is_flag=True, help="Show worklog entries for the issue")
@click.option("--start-date", "-s", help="Start date for worklogs (YYYY-MM-DD)")
@click.option("--end-date", "-e", help="End date for worklogs (YYYY-MM-DD)")
@click.option("--all-time", "-a", is_flag=True, help="Show all worklogs (no date filtering)")
def issue(issue_key, json, debug, worklogs, start_date, end_date, all_time):
    """Get information about a specific issue."""
    # Import here for cleaner testing
    from ..core import get_issue, get_issue_comments, list_worklogs
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
            # If all-time flag is set, don't filter by date range
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
                
            # Get worklogs for this issue
            issue_worklogs = list_worklogs(issue_key)
            
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
                table = Table(title=f"Worklogs for {issue_key}")
                table.add_column("Date", style="cyan")
                table.add_column("Author", style="yellow")
                table.add_column("Time Spent", style="magenta")
                table.add_column("Comment", style="blue")
                
                total_seconds = 0
                for worklog in filtered_worklogs:
                    # Format the date
                    date_str = ""
                    if "started" in worklog:
                        started = worklog["started"]
                        if isinstance(started, datetime.datetime):
                            date_str = started.strftime("%Y-%m-%d %H:%M")
                        elif isinstance(started, str) and "T" in started:
                            parts = started.split("T")
                            date_str = f"{parts[0]} {parts[1][:5]}"
                    
                    # Get author name
                    author = worklog.get("author", {}).get("displayName", "")
                    
                    # Get time spent
                    time_spent = worklog.get("timeSpent", "")
                    total_seconds += worklog.get("timeSpentSeconds", 0)
                    
                    # Get comment if it exists
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
                    
                    table.add_row(date_str, author, time_spent, comment)
                
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
                    
                console.print(f"\nTotal time logged: [bold]{total_time}[/bold] ({len(filtered_worklogs)} entries)")
            else:
                date_range_msg = f" between {start_date} and {end_date}" if start_date and end_date else ""
                console.print(f"[yellow]No worklogs found for {issue_key}{date_range_msg}.[/yellow]")
            
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
                             issuetype_data.get("value") or 
                             issuetype_data.get("displayName") or 
                             issuetype_data.get("display_name") or 
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
        
        # Add details as a row
        issue_table.add_row(details)
        
        # ===== SECTION: DESCRIPTION =====
        # Process description
        desc_text = ""
        if "description" in fields and fields["description"]:
            description = fields["description"]
            
            # Handle different description formats
            if isinstance(description, str):
                desc_text = description
            elif isinstance(description, dict):
                if "content" in description:
                    # Debug all content if requested
                    if debug:
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
                    
                    # Extract text from Atlassian Document Format
                    desc_text = _extract_text_from_adf(description)
                    
                    if debug and desc_text:
                        console.print(f"[dim yellow]Extracted description length:[/dim yellow] {len(desc_text)} characters")
                        console.print(f"[dim yellow]Preview:[/dim yellow] '{desc_text[:100]}...'")
                elif "text" in description:
                    desc_text = description["text"]
        
        # Add the description section with compact spacing
        if desc_text and desc_text.strip():
            from rich.panel import Panel
            from rich.text import Text
            # Add the description content (if any) with improved spacing
            description_content = f"[bold cyan]DESCRIPTION[/bold cyan]\n{desc_text}"
            issue_table.add_row(description_content)
        else:
            issue_table.add_row("[bold cyan]DESCRIPTION[/bold cyan]\n[italic]No description provided[/italic]")
        
        # ===== SECTION: COMMENTS =====
        # Get comments for the issue
        try:
            comments = get_issue_comments(issue_key)
            
            # Process comments
            if comments:
                from rich.text import Text
                
                # Format all comments into a readable format
                comment_text = "[bold cyan]COMMENTS[/bold cyan]\n\n"
                for i, comment in enumerate(comments):
                    author = comment.get("author", {}).get("displayName", "Unknown")
                    created = comment.get("created", "Unknown date")
                    
                    # Format the date if it's ISO format
                    if isinstance(created, str) and "T" in created:
                        parts = created.split("T")
                        created = f"{parts[0]} {parts[1][:8]}"
                    
                    # Get comment body
                    body = ""
                    if isinstance(comment.get("body"), str):
                        body = comment.get("body")
                    elif isinstance(comment.get("body"), dict) and "content" in comment.get("body", {}):
                        # Extract from Atlassian Document Format if needed
                        body = _extract_text_from_adf(comment.get("body"))
                    
                    # Add a divider between comments except for the first one
                    if i > 0:
                        comment_text += "\n" + "-" * 40 + "\n"
                    # Format the comment with author, date and content
                    comment_text += f"[bold blue]{author}[/bold blue] commented on [italic]{created}[/italic]:\n\n"
                    comment_text += body.strip() + "\n"
                
                # Add comments directly without a panel for more compact display
                issue_table.add_row(comment_text)
            else:
                issue_table.add_row("[bold cyan]COMMENTS[/bold cyan]\n[italic]No comments found[/italic]")
        except Exception as e:
            if debug:
                console.print(f"[bold red]Error fetching comments:[/bold red] {str(e)}")
            issue_table.add_row("[bold cyan]COMMENTS[/bold cyan]\n[italic]Error loading comments[/italic]")
        
        # Print the table
        console.print(issue_table)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if debug:
            import traceback
            console.print("[bold red]Traceback:[/bold red]")
            console.print(traceback.format_exc())
        # Don't propagate the exception during testing
        if os.environ.get("TASKRA_TESTING") != "1":
            raise

def _extract_text_from_adf(doc):
    """Extract plain text from Atlassian Document Format."""
    if not doc or not isinstance(doc, dict):
        return ""
    
    # Handle the ADF document structure
    def _process_node(node):
        if not isinstance(node, dict):
            return ""
        
        node_type = node.get("type", "")
        
        # Direct text node
        if node_type == "text":
            return node.get("text", "")
        
        # Process content array if it exists
        result = []
        if "content" in node and isinstance(node.get("content"), list):
            for child in node.get("content", []):
                child_text = _process_node(child)
                if child_text:
                    result.append(child_text)
        # Join text within this node based on the node type
        if node_type in ["paragraph", "heading"]:
            # Add newline after paragraphs or headings
            return " ".join(result) + "\n"
        elif node_type == "list-item":
            # Add bullet point for list items
            return "• " + " ".join(result) + "\n"
        elif node_type in ["bulletList", "orderedList"]:
            # Just join list items
            return "".join(result)
        elif node_type in ["hardBreak"]:
            # Hard break gets converted to newline
            return "\n"
        else:
            # Default: just join the text
            return " ".join(result)
    
    # Process the document from the top level
    return _process_node(doc).strip()

@cli.command()
@click.option("--username", "-u", help="Username to filter worklogs by (defaults to current user)")
@click.option("--start", "-s", help="Start date in format YYYY-MM-DD (defaults to yesterday)")
@click.option("--end", "-e", help="End date in format YYYY-MM-DD (defaults to today)")
@click.option("--json", "-j", is_flag=True, help="Output raw JSON")
@click.option("--debug", "-d", type=click.Choice(['none', 'error', 'info', 'verbose']), 
              default='none', help="Set debug output level")
def worklogs(username, start, end, json, debug):
    """Get worklogs for a user."""
    # Import here for cleaner testing
    from ..core import get_user_worklogs
    import logging
    import datetime
    
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
            
            table.add_row(date_str, issue_key, author, time_spent, comment)
        
        console.print(table)
        console.print(f"\nTotal worklogs: [bold]{len(worklogs_data)}[/bold]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if os.environ.get("TASKRA_TESTING") != "1":
            raise

# Add config group
@cli.group()
def config():
    """Manage Taskra configuration and accounts."""
    pass

@config.command("list")
def list_config():
    """List all configured accounts."""
    from ..config.account import list_accounts
    
    accounts = list_accounts()
    
    if not accounts:
        console.print("[yellow]No accounts configured.[/yellow]")
        console.print("Use [bold]taskra config add[/bold] to add an account.")
        return
    
    table = Table(title="Configured Accounts")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Email", style="blue")
    table.add_column("Default", justify="center")
    
    for account in accounts:
        default_mark = "[bold green]✓[/bold green]" if account["is_default"] else ""
        table.add_row(
            account["name"],
            account["url"],
            account["email"],
            default_mark
        )
    
    console.print(table)

@config.command("add")
@click.option("--name", "-n", help="Custom account name (derived from URL if not provided)")
@click.option("--url", "-u", prompt="Jira URL (e.g., https://mycompany.atlassian.net)", 
              help="URL of your Jira instance")
@click.option("--email", "-e", prompt="Email address", help="Your Jira account email")
@click.option("--token", "-t", prompt="API token", hide_input=True, 
              help="Your Jira API token (from https://id.atlassian.com/manage-profile/security/api-tokens)")
@click.option("--debug", "-d", is_flag=True, help="Enable debug output")
def add_account(name: Optional[str], url: str, email: str, token: str, debug: bool):
    """Add a new Jira account."""
    from ..config.account import add_account as add_account_func
    from ..config.manager import enable_debug_mode, config_manager
    import sys
    import traceback
    
    if debug:
        console.print("[yellow]Debug mode enabled[/yellow]")
        # Enable debug mode in the config manager
        enable_debug_mode()
        
        # Print detailed environment information
        console.print("[bold]Environment Information:[/bold]")
        console.print(f"Python version: {sys.version}")
        console.print(f"Current working directory: {os.getcwd()}")
        console.print(f"User home directory: {os.path.expanduser('~')}")
        
        # Print config paths information
        console.print("[bold]Configuration paths:[/bold]")
        console.print(f"Config directory: {config_manager.config_dir}")
        console.print(f"Config file path: {config_manager.config_path}")
        console.print(f"Config directory exists: {os.path.exists(config_manager.config_dir)}")
        console.print(f"Config file exists: {os.path.exists(config_manager.config_path)}")
        
        # Check write permissions
        config_dir_writable = os.access(os.path.dirname(config_manager.config_dir), os.W_OK)
        console.print(f"Parent directory writable: {config_dir_writable}")
        if os.path.exists(config_manager.config_dir):
            config_dir_writable = os.access(config_manager.config_dir, os.W_OK)
            console.print(f"Config directory writable: {config_dir_writable}")
        
        # Print account parameters
        console.print("[bold]Account parameters:[/bold]")
        console.print(f"URL: {url}")
        console.print(f"Email: {email}")
        console.print(f"Name: {name or '(derived from URL)'}")
        console.print(f"Token length: {len(token)} characters")
    
    try:
        success, message = add_account_func(url, email, token, name, debug)
        if success:
            console.print(f"[bold green]✓[/bold green] {message}")
            
            if debug:
                # Verify config file was created
                console.print("[bold]Post-operation verification:[/bold]")
                console.print(f"Config file exists: {os.path.exists(config_manager.config_path)}")
                if os.path.exists(config_manager.config_path):
                    console.print(f"Config file size: {os.path.getsize(config_manager.config_path)} bytes")
                    try:
                        # Read back and print the config to verify it was written correctly
                        import json
                        with open(config_manager.config_path, "r") as f:
                            saved_config = json.load(f)
                            console.print(f"Saved config content: {saved_config}")
                    except Exception as e:
                        console.print(f"[bold red]Error reading back config:[/bold red] {str(e)}")
        else:
            console.print(f"[bold red]✗[/bold red] {message}")
    
    except Exception as e:
        console.print(f"[bold red]Error during account addition:[/bold red] {str(e)}")
        if debug:
            console.print("[bold red]Traceback:[/bold red]")
            console.print(traceback.format_exc())

@config.command("remove")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Remove without confirmation")
def remove_account(name: str, force: bool):
    """Remove an account configuration."""
    from ..config.account import remove_account as remove_account_func
    
    if not force:
        if not click.confirm(f"Are you sure you want to remove account '{name}'?"):
            console.print("[yellow]Operation cancelled.[/yellow]")
            return
    
    success, message = remove_account_func(name)
    if success:
        console.print(f"[bold green]✓[/bold green] {message}")
    else:
        console.print(f"[bold red]✗[/bold red] {message}")

@config.command("default")
@click.argument("name")
def set_default(name: str):
    """Set the default account."""
    from ..config.account import set_default_account
    
    success, message = set_default_account(name)
    
    if success:
        console.print(f"[bold green]✓[/bold green] {message}")
    else:
        console.print(f"[bold red]✗[/bold red] {message}")

@config.command("current")
def show_current():
    """Show the currently active account."""
    from ..config.account import get_current_account
    
    account = get_current_account()
    if not account:
        console.print("[yellow]No account is currently active.[/yellow]")
        console.print("Use [bold]taskra config add[/bold] to add an account.")
        return
    
    console.print(f"[bold blue]Currently active account:[/bold blue] {account['name']}")
    console.print(f"URL: {account['url']}")
    console.print(f"Email: {account['email']}")
    # Show if this account is from environment variable
    env_account = os.environ.get("TASKRA_ACCOUNT")
    if env_account and env_account == account["name"]:
        console.print("[dim](Set via TASKRA_ACCOUNT environment variable)[/dim]")

@cli.command()
@click.argument("project_key")
@click.option("--start-date", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", "-e", help="End date (YYYY-MM-DD)")
@click.option("--status", multiple=True, help="Filter by status (can be used multiple times)")
@click.option("--assignee", help="Filter by assignee")
@click.option("--reporter", help="Filter by reporter")
@click.option("--worklog-user", help="Filter by user who logged work")
@click.option("--num-tickets", "-n", type=int, default=100, help="Maximum number of tickets to return")
@click.option("--group-by", "-g", type=click.Choice(["status", "assignee", "none"]), default="none", 
              help="Group results by field")
@click.option("--sort-by", "-b", type=click.Choice(["created", "updated", "status", "assignee", "priority"]), 
              default="created", help="Sort results by field")
@click.option("--sort-order", "-o", type=click.Choice(["asc", "desc"]), default="desc", 
              help="Sort order (ascending or descending)")
@click.option("--format", "-f", default="table", type=click.Choice(["table", "json", "csv"]), 
              help="Output format")
@click.option("--debug", "-d", is_flag=True, help="Show debug information")
def tickets(project_key, start_date, end_date, status, assignee, reporter, worklog_user, 
           num_tickets, group_by, sort_by, sort_order, format, debug):
    """List tickets for a specific project with optional filters."""
    from ..core.reports import generate_project_tickets_report
    import datetime
    import json as json_lib
    from itertools import groupby
    from operator import itemgetter
    
    try:
        # Convert filter options to a filter dict
        filters = {
            "project": project_key,
            "status": list(status) if status else None,
            "assignee": assignee,
            "reporter": reporter,
            "worklog_user": worklog_user,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        # Only add date filters if explicitly provided
        if start_date:
            filters["start_date"] = start_date
        
        if end_date:
            filters["end_date"] = end_date
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        if debug:
            console.print(f"[yellow]Filters: {filters}[/yellow]")
            console.print(f"[yellow]Max tickets: {num_tickets}[/yellow]")
            console.print(f"[yellow]Group by: {group_by}[/yellow]")
            console.print(f"[yellow]Sort by: {sort_by} ({sort_order})[/yellow]")
            
        # Generate the report
        report_data = generate_project_tickets_report(filters, max_results=num_tickets, debug=debug)
        
        if not report_data:
            console.print(f"[yellow]No tickets found for project {project_key} with the specified filters.[/yellow]")
            return
        
        # Sort the data if requested
        if group_by != "none":
            # For grouping, we first need to ensure it's sorted by the group field
            report_data = sorted(report_data, key=lambda x: x.get(group_by, ""))
        
        # Output in the requested format
        if format == "json":
            console.print(json_lib.dumps(report_data, indent=2, default=str))
            return
        elif format == "csv":
            # Output as CSV
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=report_data[0].keys())
            writer.writeheader()
            writer.writerows(report_data)
            
            console.print(output.getvalue())
            return
        else:  # Default to table format
            if group_by == "none":
                # Regular table display
                table = Table(title=f"Tickets for Project {project_key}")
                
                # Add columns based on the keys in the first result
                if report_data:
                    keys = report_data[0].keys()
                    for key in keys:
                        column_name = key.replace("_", " ").title()
                        table.add_column(column_name)
                    
                    # Add rows
                    for item in report_data:
                        table.add_row(*[str(item.get(key, "")) for key in keys])
                    
                console.print(table)
                console.print(f"\nTotal tickets: [bold]{len(report_data)}[/bold]")
            else:
                # Grouped display
                grouped_count = 0
                
                # Group by the selected field
                for group_value, items in groupby(report_data, key=lambda x: x.get(group_by, "")):
                    # Convert to list because groupby returns an iterator that can only be consumed once
                    group_items = list(items)
                    grouped_count += len(group_items)
                    
                    # Create a table for this group
                    group_title = f"{group_by.title()}: {group_value}" if group_value else f"{group_by.title()}: Unassigned/Unknown"
                    group_table = Table(title=group_title)
                    
                    # Add columns (excluding the group-by column to avoid redundancy)
                    if group_items:
                        keys = [k for k in group_items[0].keys() if k != group_by]
                        for key in keys:
                            column_name = key.replace("_", " ").title()
                            group_table.add_column(column_name)
                        
                        # Add rows for this group
                        for item in group_items:
                            group_table.add_row(*[str(item.get(key, "")) for key in keys])
                    
                    console.print(group_table)
                    console.print("")  # Add spacing between groups
                
                console.print(f"Total tickets: [bold]{grouped_count}[/bold]")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if debug:
            import traceback
            console.print("[bold red]Traceback:[/bold red]")
            console.print(traceback.format_exc())
        # Don't propagate the exception during testing
        if os.environ.get("TASKRA_TESTING") != "1":
            raise

if __name__ == "__main__":
    cli()
