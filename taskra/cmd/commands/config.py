"""Configuration command implementation."""

import os
import sys
import traceback
import click
from rich.console import Console
from rich.table import Table
from typing import Optional

# Create console for rich text formatting
console = Console()

@click.group("config")
def config_cmd():
    """Manage Taskra configuration and accounts."""
    pass

@config_cmd.command("list")
def list_config():
    """List all configured accounts."""
    from ...config.account import list_accounts
    
    accounts = list_accounts()
    
    if not accounts:
        console.print("[yellow]No accounts configured.[/yellow]")
        console.print("Use [bold]taskra config add[/bold] to add an account.")
        return
    
    table = Table(title="Configured Accounts")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Email", style="blue")
    table.add_column("Default", justify="center")
    
    for account in accounts:
        default_mark = "[bold green]✓[/bold green]" if account["is_default"] else ""
        table.add_row(
            account["name"],
            account["url"],
            account["email"],
            default_mark
        )
    
    console.print(table)

@config_cmd.command("add")
@click.option("--name", "-n", help="Custom account name (derived from URL if not provided)")
@click.option("--url", "-u", prompt="Jira URL (e.g., https://mycompany.atlassian.net)", 
              help="URL of your Jira instance")
@click.option("--email", "-e", prompt="Email address", help="Your Jira account email")
@click.option("--token", "-t", prompt="API token", hide_input=True, 
              help="Your Jira API token (from https://id.atlassian.com/manage-profile/security/api-tokens)")
@click.option("--debug", "-d", is_flag=True, help="Enable debug output")
def add_account(name: Optional[str], url: str, email: str, token: str, debug: bool):
    """Add a new Jira account."""
    from ...config.account import add_account as add_account_func
    from ...config.manager import enable_debug_mode, config_manager
    
    if debug:
        console.print("[yellow]Debug mode enabled[/yellow]")
        # Enable debug mode in the config manager
        enable_debug_mode()
        
        # Print detailed environment information
        console.print("[bold]Environment Information:[/bold]")
        console.print(f"Python version: {sys.version}")
        console.print(f"Current working directory: {os.getcwd()}")
        console.print(f"User home directory: {os.path.expanduser('~')}")
        
        # Print config paths information
        console.print("[bold]Configuration paths:[/bold]")
        console.print(f"Config directory: {config_manager.config_dir}")
        console.print(f"Config file path: {config_manager.config_path}")
        console.print(f"Config directory exists: {os.path.exists(config_manager.config_dir)}")
        console.print(f"Config file exists: {os.path.exists(config_manager.config_path)}")
        
        # Check write permissions
        config_dir_writable = os.access(os.path.dirname(config_manager.config_dir), os.W_OK)
        console.print(f"Parent directory writable: {config_dir_writable}")
        if os.path.exists(config_manager.config_dir):
            config_dir_writable = os.access(config_manager.config_dir, os.W_OK)
            console.print(f"Config directory writable: {config_dir_writable}")
        
        # Print account parameters
        console.print("[bold]Account parameters:[/bold]")
        console.print(f"URL: {url}")
        console.print(f"Email: {email}")
        console.print(f"Name: {name or '(derived from URL)'}")
        console.print(f"Token length: {len(token)} characters")
    
    try:
        success, message = add_account_func(url, email, token, name, debug)
        if success:
            console.print(f"[bold green]✓[/bold green] {message}")
            
            if debug:
                # Verify config file was created
                console.print("[bold]Post-operation verification:[/bold]")
                console.print(f"Config file exists: {os.path.exists(config_manager.config_path)}")
                if os.path.exists(config_manager.config_path):
                    console.print(f"Config file size: {os.path.getsize(config_manager.config_path)} bytes")
                    try:
                        # Read back and print the config to verify it was written correctly
                        import json
                        with open(config_manager.config_path, "r") as f:
                            saved_config = json.load(f)
                            console.print(f"Saved config content: {saved_config}")
                    except Exception as e:
                        console.print(f"[bold red]Error reading back config:[/bold red] {str(e)}")
        else:
            console.print(f"[bold red]✗[/bold red] {message}")
    
    except Exception as e:
        console.print(f"[bold red]Error during account addition:[/bold red] {str(e)}")
        if debug:
            console.print("[bold red]Traceback:[/bold red]")
            console.print(traceback.format_exc())

@config_cmd.command("remove")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Remove without confirmation")
def remove_account(name: str, force: bool):
    """Remove an account configuration."""
    from ...config.account import remove_account as remove_account_func
    
    if not force:
        if not click.confirm(f"Are you sure you want to remove account '{name}'?"):
            console.print("[yellow]Operation cancelled.[/yellow]")
            return
    
    success, message = remove_account_func(name)
    if success:
        console.print(f"[bold green]✓[/bold green] {message}")
    else:
        console.print(f"[bold red]✗[/bold red] {message}")

@config_cmd.command("default")
@click.argument("name")
def set_default(name: str):
    """Set the default account."""
    from ...config.account import set_default_account
    
    success, message = set_default_account(name)
    
    if success:
        console.print(f"[bold green]✓[/bold green] {message}")
    else:
        console.print(f"[bold red]✗[/bold red] {message}")

@config_cmd.command("current")
def show_current():
    """Show the currently active account."""
    from ...config.account import get_current_account
    
    account = get_current_account()
    if not account:
        console.print("[yellow]No account is currently active.[/yellow]")
        console.print("Use [bold]taskra config add[/bold] to add an account.")
        return
    
    console.print(f"[bold blue]Currently active account:[/bold blue] {account['name']}")
    console.print(f"URL: {account['url']}")
    console.print(f"Email: {account['email']}")
    # Show if this account is from environment variable
    env_account = os.environ.get("TASKRA_ACCOUNT")
    if env_account and env_account == account["name"]:
        console.print("[dim](Set via TASKRA_ACCOUNT environment variable)[/dim]")
