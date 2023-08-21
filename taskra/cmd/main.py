"""Main CLI implementation for Taskra."""

import click
from rich.console import Console

from .commands.projects import projects_cmd
from .commands.issues import issue_cmd
from .commands.worklogs import worklogs_cmd
from .commands.tickets import tickets_cmd
from .commands.config import config_cmd
from .commands.reports import report_cmd  # Import the new report command
from .utils.formatting import convert_adf_to_rich_text, map_atlassian_color_to_rich

# Create console for rich text formatting
console = Console()

@click.group()
@click.version_option()
def cli():
    """Taskra - Task and project management from the command line."""
    pass

# Register command groups
cli.add_command(projects_cmd)
cli.add_command(issue_cmd)
cli.add_command(worklogs_cmd)
cli.add_command(config_cmd)
cli.add_command(tickets_cmd)
cli.add_command(report_cmd)  # Register the new report command

if __name__ == "__main__":
    cli()
