"""Base rendering functionality."""

import json
from rich.console import Console

# Shared console instance for all renderers
console = Console()

class BaseRenderer:
    """Base class for rendering entities to the terminal."""
    
    def __init__(self, console=None):
        """Initialize the renderer with a console."""
        self.console = console or Console()
    
    def render_json(self, data):
        """Render data as JSON."""
        self.console.print(json.dumps(data, indent=2, default=str))
