"""Projects command implementation."""

import click
import json
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
    
    if debug:
        console.print("[yellow]Debug mode enabled[/yellow]")
    
    try:
        # Get projects list - don't pass debug parameter as it's not supported
        projects_list = list_projects()
        
        # If JSON flag is provided, output raw JSON
        if json_output:
            # Output as JSON format
            console.print(json.dumps(projects_list, indent=2))
            return
        
        # Otherwise, continue with standard output
        console.print("[bold blue]Available Projects:[/bold blue]")
        
        # Display each project
        for project in projects_list:
            key = project.get("key", "Unknown")
            name = project.get("name", "Unnamed")
            console.print(f"{key}: {name}")
        
        console.print(f"\nTotal projects: [bold]{len(projects_list)}[/bold]")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if debug:
            import traceback
            console.print("[bold red]Traceback:[/bold red]")
            console.print(traceback.format_exc())
        # Re-raise exception if not in testing mode
        import os
        if os.environ.get("TASKRA_TESTING") != "1":
            raise
