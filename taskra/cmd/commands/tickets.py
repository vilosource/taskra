"""Tickets command implementation."""

import os
import click
import traceback
import datetime
from rich.console import Console
from rich.table import Table
from itertools import groupby

# Create console for rich text formatting
console = Console()

@click.command("tickets")
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
@click.option("--reverse/--no-reverse", "-r", default=True, 
              help="Reverse the sort order")
@click.option("--format", "-f", default="table", type=click.Choice(["table", "json", "csv"]), 
              help="Output format")
@click.option("--debug", "-d", is_flag=True, help="Show debug information")
def tickets_cmd(project_key, start_date=None, end_date=None, status=None, assignee=None, 
                reporter=None, worklog_user=None, num_tickets=100, group_by="none", 
                sort_by="created", reverse=True, format="table", debug=False):
    """Display tickets for a project."""
    from ...core.reports import generate_project_tickets_report
    
    try:
        # Convert filter options to a filter dict
        filters = {
            'project_key': project_key,
            'sort_by': sort_by,
            'sort_order': 'desc' if reverse else 'asc',
            'status': list(status) if status else None,
            'start_date': start_date,
            'end_date': end_date,
            'assignee': assignee,
            'reporter': reporter,
            'worklog_user': worklog_user
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        if debug:
            console.print(f"[yellow]Filters: {filters}[/yellow]")
            console.print(f"[yellow]Max tickets: {num_tickets}[/yellow]")
            console.print(f"[yellow]Group by: {group_by}[/yellow]")
            console.print(f"[yellow]Sort by: {sort_by} ({'desc' if reverse else 'asc'})[/yellow]")
            
        # Generate the report
        report_data = generate_project_tickets_report(filters, max_results=num_tickets, debug=debug)
        
        # Ensure report_data is used directly for display
        if not report_data:
            console.print(f"[yellow]No tickets found for project {project_key} with the specified filters.[/yellow]")
            return
            
        # If debugging, print the first report item to verify data
        if debug and report_data:
            console.print("\nDEBUG: First report item being sent to display:")
            first_item = report_data[0] if report_data else {}
            for key, value in first_item.items():
                console.print(f"  {key}: {value}")

        # Display the report
        display_tickets_report(project_key, report_data, group_by, sort_by, reverse)
        console.print(f"\nTotal tickets: [bold]{len(report_data)}[/bold]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if debug:
            console.print("[bold red]Traceback:[/bold red]")
            console.print(traceback.format_exc())
        # Don't propagate the exception during testing
        if os.environ.get("TASKRA_TESTING") != "1":
            raise

def display_tickets_report(project_key, tickets, group_by=None, sort_by='created', reverse=False):
    """Display a formatted ticket report."""
    
    # Check if tickets is in the right format
    if not isinstance(tickets, list):
        raise click.ClickException(f"Invalid report data format: {type(tickets).__name__}")
        
    # Define the headers for the table
    headers = ['Key', 'Summary', 'Status', 'Assignee', 'Priority', 'Created', 'Updated']
    
    # Create rows from ticket data - ensure proper field extraction
    rows = []
    for ticket in tickets:
        # Make sure we extract the right fields
        row = [
            ticket.get('key', 'Unknown'),  
            ticket.get('summary', 'No summary'),
            ticket.get('status', 'Unknown'),
            ticket.get('assignee', 'Unassigned'),
            ticket.get('priority', 'Unknown'),
            ticket.get('created', ''),
            ticket.get('updated', '')
        ]
        rows.append(row)
    
    # Display the tickets in a table
    title = f"Tickets for Project {project_key}"
    print_table(headers, rows, title)

def print_table(headers, rows, title):
    """Print a table using rich."""
    table = Table(title=title)
    
    for header in headers:
        table.add_column(header)
    
    for row in rows:
        table.add_row(*row)
    
    console.print(table)
