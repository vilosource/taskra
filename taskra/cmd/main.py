"""Main CLI implementation for Taskra."""

import click
from rich.console import Console

console = Console()

@click.group()
@click.version_option()
def cli():
    """Taskra - Task and project management from the command line."""
    pass

@cli.command()
def projects():
    """List available projects."""
    from ..core import list_projects
    
    console.print("[bold blue]Available Projects:[/bold blue]")
    list_projects()

@cli.command()
@click.argument("issue_key")
def issue(issue_key):
    """Get information about a specific issue."""
    from ..core import get_issue
    
    console.print(f"[bold blue]Issue details for {issue_key}:[/bold blue]")
    issue_data = get_issue(issue_key)
    console.print(issue_data)

if __name__ == "__main__":
    cli()
