"""Reports command implementation."""

import click
from rich.console import Console

# Create console for rich text formatting
console = Console()

@click.group("report")
def report_cmd():
    """Generate various reports."""
    pass

@report_cmd.command("cross-project")
@click.argument("project_keys", nargs=-1, required=True)
@click.option("--start-date", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", "-e", help="End date (YYYY-MM-DD)")
@click.option("--status", multiple=True, help="Filter by status (can be used multiple times)")
@click.option("--assignee", help="Filter by assignee")
@click.option("--format", "-f", default="table", type=click.Choice(["table", "json"]), 
              help="Output format")
@click.option("--debug", "-d", is_flag=True, help="Show debug information")
def cross_project_cmd(project_keys, start_date, end_date, status, assignee, format, debug):
    """Generate a report across multiple projects."""
    # Import inside function to avoid circular imports
    from ...core.reports import generate_cross_project_report
    from ...presentation import render_cross_project_report, render_error
    
    try:
        # Prepare filters
        filters = {
            "status": list(status) if status else None,
            "assignee": assignee
        }
        
        # Only add date filters if explicitly provided
        if start_date:
            filters["start_date"] = start_date
        
        if end_date:
            filters["end_date"] = end_date
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        if debug:
            console.print(f"[yellow]Generating cross-project report for:[/yellow] {', '.join(project_keys)}")
            console.print(f"[yellow]Using filters:[/yellow] {filters}")
        
        # Generate the report - this is our core business logic
        report_data = generate_cross_project_report(list(project_keys), filters, debug)
        
        # Delegate presentation to the presentation layer
        render_cross_project_report(report_data, format=format)
            
    except Exception as e:
        # Delegate error handling to the presentation layer
        render_error(e, debug)
