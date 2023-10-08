"""Main CLI implementation for Taskra."""

import click
import logging
from rich.console import Console
from rich.logging import RichHandler

from .commands.projects import projects_cmd
from .commands.issues import issue_cmd
from .commands.worklogs import worklogs_cmd
from .commands.tickets import tickets_cmd
from .commands.config import config_cmd
from .commands.reports import report_cmd  # Import the new report command
from .utils.formatting import convert_adf_to_rich_text, map_atlassian_color_to_rich

# Create console for rich text formatting
console = Console()

# Create a class to hold shared context
class TaskraContext:
    def __init__(self):
        self.debug_level = "none"

# Setup logging with Rich handler
def setup_logging(level_name):
    """Configure logging based on debug level."""
    # Map level names to logging levels
    level_map = {
        "none": logging.WARNING,
        "error": logging.ERROR,
        "info": logging.INFO,
        "verbose": logging.DEBUG
    }
    level = level_map.get(level_name.lower(), logging.WARNING)
    
    # Only reset logging if it hasn't been configured
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Configure logging with Rich handler for pretty output
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)]
    )
    
    # Set specific logger levels
    logging.getLogger("taskra").setLevel(level)
    
    # Log the debug level
    if level_name.lower() != "none":
        logging.debug(f"Debug mode: {level_name.upper()}")
    
    return level

@click.group()
@click.version_option()
@click.option("--debug", "-d", 
              type=click.Choice(['none', 'error', 'info', 'verbose'], case_sensitive=False), 
              default='none', 
              help="Set debug output level")
@click.pass_context
def cli(ctx, debug):
    """Taskra - Task and project management from the command line."""
    # Initialize our context object
    ctx.obj = TaskraContext()
    ctx.obj.debug_level = debug
    
    # Setup logging based on debug level
    setup_logging(debug)

# Register command groups
cli.add_command(projects_cmd)
cli.add_command(issue_cmd)
cli.add_command(worklogs_cmd)
cli.add_command(config_cmd)
cli.add_command(tickets_cmd)
cli.add_command(report_cmd)  # Register the new report command

if __name__ == "__main__":
    cli()
