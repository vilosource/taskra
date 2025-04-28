"""Projects command implementation."""

import click
import os
import logging
from rich.console import Console

# Create console for rich text formatting
console = Console()

@click.command("projects")
@click.option("--json", "-j", "json_output", is_flag=True, help="Output raw JSON")
@click.pass_context
def projects_cmd(ctx, json_output):
    """List available projects."""
    # Import inside function to avoid circular imports
    from ...core import list_projects
    from ...presentation import render_projects, render_error
    
    # Access the debug level from the parent context
    debug_level = ctx.obj.debug_level if ctx.obj else "none"
    debug = debug_level.lower() != "none"
    
    if debug:
        console.print(f"[yellow]Debug level: {debug_level}[/yellow]")
        logging.info(f"Running projects command with debug level: {debug_level}")
    
    try:
        # Get projects list with logging
        if debug:
            logging.info("Fetching projects list...")
        
        projects_list = list_projects()
        
        if debug:
            logging.info(f"Found {len(projects_list)} projects")
        
        # Delegate presentation to separate service
        render_projects(projects_list, format="json" if json_output else "table")
    
    except Exception as e:
        # Delegate error handling to presentation layer
        if debug:
            logging.error(f"Error fetching projects: {str(e)}", exc_info=True)
        render_error(e, debug)
        # Re-raise exception if not in testing mode
        if os.environ.get("TASKRA_TESTING") != "1":
            raise
