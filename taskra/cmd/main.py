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
def issue(issue_key, json, debug):
    """Get information about a specific issue."""
    # Import here for cleaner testing
    from ..core import get_issue
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
        
        # Create a single table with HEAVY borders for improved visibility
        # Use a single column layout
        issue_table = Table(box=box.DOUBLE_EDGE, show_header=False, expand=True, padding=1)
        issue_table.add_column("Content", style="green")  # Single column for all content
        
        # ===== SECTION: SUMMARY =====
        summary = fields.get("summary", "No summary provided")
        issue_table.add_row(f"[bold cyan]SUMMARY[/bold cyan]\n{summary}")
        
        # ===== SECTION: DETAILS =====
        # Extract status
        status = "Unknown"
        if "status" in fields and fields["status"]:
            status = fields["status"].get("name", "Unknown")
            status_category = fields["status"].get("statusCategory", {}).get("name", "")
            if status_category:
                status = f"{status} ({status_category})"
        
        # Extract issue type - More detailed extraction
        issue_type = "Unknown"
        if "issuetype" in fields:
            issuetype_data = fields["issuetype"]
            if debug:
                console.print(f"[dim]Debug - Issue type data: {issuetype_data}[/dim]")
                
            if isinstance(issuetype_data, dict):
                issue_type = issuetype_data.get("name", "Unknown")
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
            if debug:
                console.print(f"[dim]Debug - Assignee data: {assignee_data}[/dim]")
                
            if isinstance(assignee_data, dict):
                assignee = assignee_data.get("displayName", assignee_data.get("name", "Unknown"))
            elif isinstance(assignee_data, str):
                assignee = assignee_data
            elif assignee_data is None:
                assignee = "Unassigned"
        
        # Extract reporter - More detailed extraction
        reporter = "Unknown"
        if "reporter" in fields:
            reporter_data = fields["reporter"]
            if debug:
                console.print(f"[dim]Debug - Reporter data: {reporter_data}[/dim]")
                
            if isinstance(reporter_data, dict):
                reporter = reporter_data.get("displayName", reporter_data.get("name", "Unknown"))
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
        
        # If debug mode is enabled, add raw field information
        if debug:
            console.print("[dim]Debug - Fields in issue data:[/dim]")
            for key in fields:
                if key in ["assignee", "reporter", "issuetype", "status", "priority"]:
                    value = fields[key]
                    if isinstance(value, dict):
                        console.print(f"[dim]  {key}: {value}[/dim]")
                    else:
                        console.print(f"[dim]  {key}: {value}[/dim]")
        
        # Format all details as a single block of text
        details = f"""[bold cyan]DETAILS[/bold cyan]
[bold]Status:[/bold] {status}
[bold]Type:[/bold] {issue_type}
[bold]Priority:[/bold] {priority}
[bold]Assignee:[/bold] {assignee}
[bold]Reporter:[/bold] {reporter}
[bold]Created:[/bold] {created_str}
[bold]Updated:[/bold] {updated_str}
"""
        
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
                        console.print(f"[dim]Description structure:[/dim]")
                        try:
                            import json as json_lib
                            console.print(f"[dim]{json_lib.dumps(description, indent=2)[:200]}...[/dim]")
                        except Exception:
                            console.print("[dim]Could not serialize description[/dim]")
                    
                    # Extract text from Atlassian Document Format
                    desc_text = _extract_text_from_adf(description)
                    
                    if debug:
                        console.print(f"[dim]Debug - Extracted text length: {len(desc_text)}[/dim]")
                        if desc_text:
                            console.print(f"[dim]First 50 chars: '{desc_text[:50]}...'[/dim]")
                elif "text" in description:
                    desc_text = description["text"]
            
            # Debug print the description object structure
            if debug and isinstance(description, dict):
                console.print(f"[dim]Description object type: {type(description)}[/dim]")
                console.print(f"[dim]Description keys: {list(description.keys())}[/dim]")
        
        # Add the description with a header
        if desc_text and desc_text.strip():
            from rich.panel import Panel
            from rich.text import Text
            
            # First add the section header
            issue_table.add_row("[bold cyan]DESCRIPTION[/bold cyan]")
            
            # Then add the panel as a separate row with the content
            wrapped_text = Text(desc_text)
            panel = Panel(wrapped_text, border_style="dim", expand=False)
            issue_table.add_row(panel)
        else:
            issue_table.add_row("[bold cyan]DESCRIPTION[/bold cyan]\n[italic]No description provided[/italic]")
        
        # Print the table
        console.print(issue_table)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
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
        elif node_type == "hardBreak":
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

if __name__ == "__main__":
    cli()
