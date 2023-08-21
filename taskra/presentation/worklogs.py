"""Worklog rendering functionality."""

from rich.table import Table
from .base import console, BaseRenderer

def render_worklogs(worklogs, issue_key=None, format="table"):
    """
    Render worklogs to the terminal.
    
    Args:
        worklogs: List of worklog dictionaries
        issue_key: Optional issue key for context
        format: Output format ("table" or "json")
    """
    renderer = WorklogsRenderer()
    if format == "json":
        renderer.render_json(worklogs)
    else:
        renderer.render_table(worklogs, issue_key)

class WorklogsRenderer(BaseRenderer):
    """Renderer for worklogs."""
    
    def render_table(self, worklogs, issue_key=None):
        """Render worklogs as a table."""
        # Prepare title based on whether we're showing for a specific issue
        title = f"Worklogs for {issue_key}" if issue_key else "Worklogs"
        
        if not worklogs:
            date_range_msg = ""
            self.console.print(f"[yellow]No worklogs found{' for ' + issue_key if issue_key else ''}{date_range_msg}.[/yellow]")
            return
            
        # Create table
        table = Table(title=title)
        table.add_column("Date", style="cyan")
        table.add_column("Time", style="cyan")
        if not issue_key:
            table.add_column("Issue", style="green")  # Only show issue column if not filtering by issue
        table.add_column("Author", style="yellow")
        table.add_column("Time Spent", style="magenta")
        table.add_column("Comment", style="blue")
        
        # Calculate total time spent
        total_seconds = 0
        
        # Add rows
        for worklog in worklogs:
            # Format date and time
            date_str, time_str = self._format_date_time(worklog.get("started", ""))
            
            # Get author
            author = worklog.get("author", {}).get("displayName", "")
            
            # Get time spent
            time_spent = worklog.get("timeSpent", "")
            total_seconds += worklog.get("timeSpentSeconds", 0)
            
            # Get issue key if not filtering by issue
            issue_column = []
            if not issue_key and "issueKey" in worklog:
                issue_column = [worklog["issueKey"]]
            
            # Get comment
            comment = self._extract_comment(worklog)
            
            # Add the row with or without issue column
            row_data = [date_str, time_str] + issue_column + [author, time_spent, comment]
            table.add_row(*row_data)
        
        self.console.print(table)
        
        # Show total time spent
        total_time = self._format_total_time(total_seconds)
        self.console.print(f"\nTotal time logged: [bold]{total_time}[/bold] ({len(worklogs)} entries)")
    
    def _format_date_time(self, started):
        """Format the started field into date and time components."""
        import datetime
        
        date_str = ""
        time_str = ""
        
        if not started:
            return date_str, time_str
            
        if isinstance(started, datetime.datetime):
            date_str = started.strftime("%Y-%m-%d")
            time_str = started.strftime("%H:%M")
        elif isinstance(started, str) and "T" in started:
            parts = started.split("T")
            date_str = parts[0]
            # Extract time part (remove seconds and timezone if present)
            if len(parts) > 1:
                time_part = parts[1].split("+")[0].split(".")[0]  # Remove timezone and milliseconds
                time_str = time_part[:5]  # Just keep HH:MM
        
        return date_str, time_str
    
    def _extract_comment(self, worklog):
        """Extract comment text from a worklog entry."""
        comment = ""
        if "comment" in worklog:
            if isinstance(worklog["comment"], str):
                comment = worklog["comment"]
            elif isinstance(worklog["comment"], dict) and "content" in worklog["comment"]:
                # Extract text from Atlassian Document Format if possible
                try:
                    comment_content = worklog["comment"].get("content", [])
                    text_parts = []
                    for paragraph in comment_content:
                        for text_node in paragraph.get("content", []):
                            if "text" in text_node:
                                text_parts.append(text_node["text"])
                    comment = " ".join(text_parts) if text_parts else "Complex comment"
                except Exception:
                    comment = "Complex comment format"
        return comment
    
    def _format_total_time(self, seconds):
        """Format total time spent."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"
