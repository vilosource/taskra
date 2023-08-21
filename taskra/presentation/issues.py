"""Issue rendering functionality."""

from rich.table import Table
from rich.text import Text
from rich import box
from .base import console, BaseRenderer
from ..cmd.utils.formatting import convert_adf_to_rich_text
import datetime

def render_issue(issue_data, format="table"):
    """
    Render issue data to the terminal.
    
    Args:
        issue_data: Issue dictionary with fields
        format: Output format ("table", "json", etc.)
    """
    renderer = IssueRenderer()
    if format == "json":
        renderer.render_json(issue_data)
    else:
        renderer.render_full(issue_data)

def render_issue_comments(issue_key, comments, format="table"):
    """
    Render issue comments to the terminal.
    
    Args:
        issue_key: The issue key
        comments: List of comment dictionaries
        format: Output format ("table", "json", etc.)
    """
    renderer = IssueRenderer()
    if format == "json":
        renderer.render_json(comments)
    else:
        renderer.render_comments(issue_key, comments)

class IssueRenderer(BaseRenderer):
    """Renderer for issues."""
    
    def render_full(self, issue_data):
        """Render a full issue with all fields."""
        issue_key = issue_data.get("key", "Unknown")
        fields = issue_data.get("fields", {})
        
        console.print(f"[bold blue]Issue details for {issue_key}[/bold blue]")
        
        # Create a single table with HEAVY borders
        issue_table = Table(
            box=box.DOUBLE_EDGE, 
            show_header=False, 
            expand=True, 
            padding=(0, 1),
            title=f"[bold cyan]{issue_key}:[/bold cyan] {fields.get('summary', 'No summary')}",
            title_justify="center",
            title_style="bold white"
        )
        issue_table.add_column("Content", style="green")
        
        # Format and add issue details
        details = self._format_issue_details(fields)
        issue_table.add_row(details)
        
        # Add description section
        self._add_description_to_table(issue_table, fields)
        
        # Print the table
        console.print(issue_table)
    
    def _format_issue_details(self, fields):
        """Format issue details as a string."""
        # Extract status
        status = "Unknown"
        if "status" in fields and fields["status"]:
            status = fields["status"].get("name", "Unknown")
            
        # Extract issue type
        issue_type = "Unknown"
        if "issuetype" in fields and fields["issuetype"]:
            issue_type = fields["issuetype"].get("name", "Unknown")
            
        # Extract priority
        priority = "None"
        if "priority" in fields and fields["priority"]:
            priority = fields["priority"].get("name", "None")
            
        # Extract assignee
        assignee = "Unassigned"
        if "assignee" in fields and fields["assignee"]:
            assignee = fields["assignee"].get("displayName", "Unknown")
            
        # Extract dates - handle both string and datetime objects
        created = "Unknown"
        created_value = fields.get("created", "")
        if isinstance(created_value, str) and "T" in created_value:
            created = created_value.split("T")[0]
        elif isinstance(created_value, datetime.datetime):
            created = created_value.strftime("%Y-%m-%d")
        
        updated = "Unknown"
        updated_value = fields.get("updated", "")
        if isinstance(updated_value, str) and "T" in updated_value:
            updated = updated_value.split("T")[0]
        elif isinstance(updated_value, datetime.datetime):
            updated = updated_value.strftime("%Y-%m-%d")
            
        # Format all details
        details = f"[bold]Status:[/bold] {status} | [bold]Type:[/bold] {issue_type} | [bold]Priority:[/bold] {priority} | "
        details += f"[bold]Assignee:[/bold] {assignee} | [bold]Created:[/bold] {created} | [bold]Updated:[/bold] {updated}"
        
        return details
    
    def _add_description_to_table(self, issue_table, fields):
        """Add description section to the issue table."""
        rich_desc = None
        if "description" in fields and fields["description"]:
            description = fields["description"]
            
            # Handle different description formats
            if isinstance(description, str):
                rich_desc = Text(description)
            elif isinstance(description, dict):
                if "content" in description:
                    rich_desc = convert_adf_to_rich_text(description)
                elif "text" in description:
                    rich_desc = Text(description["text"])
        
        # Add the description section
        issue_table.add_row(Text("\nDESCRIPTION", style="bold underline"))
        if rich_desc:
            issue_table.add_row(rich_desc)
        else:
            issue_table.add_row(Text("No description provided", style="italic"))
    
    def render_comments(self, issue_key, comments):
        """Render issue comments."""
        console.print(f"[bold blue]Comments for {issue_key}[/bold blue]")
        
        if not comments:
            console.print("[yellow]No comments found.[/yellow]")
            return
        
        for i, comment in enumerate(comments):
            author = comment.get("author", {}).get("displayName", "Unknown")
            created = comment.get("created", "Unknown date")
            
            # Format the date if it's ISO format
            if isinstance(created, str) and "T" in created:
                parts = created.split("T")
                created = f"{parts[0]} {parts[1][:8]}"
            
            # Add a divider between comments except for the first one
            if i > 0:
                console.print("-" * 40)
            
            # Format the comment header
            console.print(f"[bold blue]{author}[/bold blue] commented on [italic]{created}[/italic]")
            
            # Format the comment body
            if isinstance(comment.get("body"), str):
                console.print(comment.get("body"))
            elif isinstance(comment.get("body"), dict) and "content" in comment.get("body", {}):
                console.print(convert_adf_to_rich_text(comment.get("body")))
            else:
                console.print("[italic]No content[/italic]")
