"""Projects command implementation."""

import click
from rich.console import Console

# Create console for rich text formatting
console = Console()

@click.command("projects")
def projects_cmd():
    """List available projects."""
    # Import inside function to avoid circular imports
    from ...core import list_projects
    
    console.print("[bold blue]Available Projects:[/bold blue]")
    projects_list = list_projects()
    
    console.print(f"\nTotal projects: [bold]{len(projects_list)}[/bold]")
