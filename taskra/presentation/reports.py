"""Report rendering functionality."""

from rich.table import Table
from .base import console, BaseRenderer

def render_cross_project_report(report_data, format="table"):
    """
    Render a cross-project report to the terminal.
    
    Args:
        report_data: Report dictionary with project data
        format: Output format ("table" or "json")
    """
    renderer = CrossProjectReportRenderer()
    if format == "json":
        renderer.render_json(report_data)
    else:
        renderer.render_table(report_data)

class CrossProjectReportRenderer(BaseRenderer):
    """Renderer for cross-project reports."""
    
    def render_table(self, report_data):
        """Render a cross-project report as tables."""
        total_issues = report_data["summary"]["total_issues"]
        projects_count = report_data["summary"]["projects_count"]
        
        self.console.print(f"[bold blue]Cross-Project Report[/bold blue]")
        self.console.print(f"Projects: [bold]{projects_count}[/bold], Total Issues: [bold]{total_issues}[/bold]")
        self.console.print("")
        
        # For each project, create a table
        for project_key, project_data in report_data["projects"].items():
            project_name = project_data["name"]
            issues = project_data["issues"]
            
            if not issues:
                self.console.print(f"[yellow]Project {project_key} ({project_name}): No issues found[/yellow]")
                continue
                
            # Create a table for this project
            table = Table(title=f"Project: {project_key} - {project_name}")
            
            # Add columns
            table.add_column("Key", style="cyan")
            table.add_column("Summary", style="green")
            table.add_column("Status", style="magenta")
            table.add_column("Assignee", style="yellow")
            table.add_column("Created", style="blue")
            
            # Add rows
            for issue in issues:
                table.add_row(
                    issue["key"],
                    issue["summary"],
                    issue["status"],
                    issue["assignee"],
                    issue["created"]
                )
            
            self.console.print(table)
            self.console.print("")  # Add spacing between tables
