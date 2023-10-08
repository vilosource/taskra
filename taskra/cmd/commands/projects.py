"""Projects command implementation."""

import click
import os
from rich.console import Console

# Create console for rich text formatting
console = Console()

@click.command("projects")
@click.option("--json", "-j", "json_output", is_flag=True, help="Output raw JSON")
@click.option("--debug", "-d", is_flag=True, help="Show debug information")
def projects_cmd(json_output, debug):
    """List available projects."""
    # Import inside function to avoid circular imports
    from ...core import list_projects
    from ...presentation import render_projects, render_error
    
    if debug:
        console.print("[yellow]Debug mode enabled[/yellow]")
    
    try:
        # Get projects list - don't pass debug parameter as it's not supported
        projects_list = list_projects()
        
        # Delegate presentation to separate service
        render_projects(projects_list, format="json" if json_output else "table")
    
    except Exception as e:
        # Delegate error handling to presentation layer
        render_error(e, debug)
        # Re-raise exception if not in testing mode
        if os.environ.get("TASKRA_TESTING") != "1":
            raise
