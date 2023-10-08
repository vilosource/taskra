"""Project rendering functionality."""

from rich.table import Table
from .base import console, BaseRenderer

def render_projects(projects_list, format="table"):
    """
    Render a list of projects to the terminal.
    
    Args:
        projects_list: List of project dictionaries
        format: Output format ("table" or "json")
    """
    renderer = ProjectsRenderer()
    if format == "json":
        renderer.render_json(projects_list)
    else:
        renderer.render_table(projects_list)

class ProjectsRenderer(BaseRenderer):
    """Renderer for project listings."""
    
    def render_table(self, projects):
        """Render projects as a formatted table."""
        self.console.print("[bold blue]Available Projects:[/bold blue]")
        
        if not projects:
            self.console.print("[yellow]No projects found.[/yellow]")
            return
        
        # Create a table
        table = Table()
        table.add_column("Key", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="yellow")
        
        # Add rows
        for project in projects:
            key = project.get("key", "Unknown")
            name = project.get("name", "Unnamed")
            project_type = project.get("projectTypeKey", "Unknown")
            table.add_row(key, name, project_type)
            
        self.console.print(table)
        self.console.print(f"\nTotal projects: [bold]{len(projects)}[/bold]")
