"""Error rendering functionality."""

from .base import console

def render_error(error, debug=False):
    """
    Render an error to the terminal.
    
    Args:
        error: Exception or error message
        debug: Whether to show debug information
    """
    console.print(f"[bold red]Error:[/bold red] {str(error)}")
    
    if debug:
        import traceback
        console.print("[bold red]Traceback:[/bold red]")
        console.print(traceback.format_exc())
