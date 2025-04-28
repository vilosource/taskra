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

@config_cmd.command("validate")
@click.option("--config-name", "-n", help="Account config name to validate (default if omitted)")
def validate_config(config_name: Optional[str]):
    """Validate Jira credentials and permissions for an account."""
    from ...config.account import list_accounts, get_current_account, validate_credentials
    from ...api.client import JiraClient
    from ...api.services.users import UserService
    from ...api.services.permissions import PermissionsService

    # Load account info
    account = None
    if config_name:
        accounts = list_accounts()
        for acc in accounts:
            if acc["name"] == config_name:
                account = acc
                break
        if not account:
            console.print(f"[bold red]Account '{config_name}' not found.[/bold red]")
            return
    else:
        account = get_current_account()
        if not account:
            console.print("[bold red]No default account configured.[/bold red]")
            return

    url = account.get("url")
    email = account.get("email")
    token = account.get("token")

    if not token:
        # token may not be included in list_accounts(), so reload full config
        from ...config.manager import config_manager
        config = config_manager.read_config()
        acc_data = config.get("accounts", {}).get(account["name"], {})
        token = acc_data.get("token")

    console.print(f"Validating account: [bold]{account['name']}[/bold] ({email})")

    # Step 1: Validate credentials
    auth_ok = validate_credentials(url, email, token)
    if not auth_ok:
        console.print("[bold red]✗ Authentication failed. Invalid credentials.[/bold red]")
        return
    console.print("[bold green]✓ Authentication successful[/bold green]")

    # Step 2: Check permissions
    try:
        client = JiraClient(base_url=url, email=email, api_token=token)
        perm_service = PermissionsService(client)
        ok, missing = perm_service.has_required_permissions()
        if ok:
            console.print("[bold green]✓ Required Jira permissions granted[/bold green]")
        else:
            console.print("[bold yellow]⚠ Missing permissions:[/bold yellow] " + ", ".join(missing))
    except Exception as e:
        console.print(f"[bold red]Error checking permissions:[/bold red] {str(e)}")

@config_cmd.command("update")
@click.option("--config-name", "-n", help="Account config name to update (default if omitted)")
def update_account(config_name: Optional[str]):
    """Update an existing Jira account configuration."""
    from ...config.account import list_accounts, get_current_account, validate_credentials
    from ...config.manager import config_manager

    # Load account info
    account = None
    if config_name:
        accounts = list_accounts()
        for acc in accounts:
            if acc["name"] == config_name:
                account = acc
                break
        if not account:
            console.print(f"[bold red]Account '{config_name}' not found.[/bold red]")
            return
    else:
        account = get_current_account()
        if not account:
            console.print("[bold red]No default account configured.[/bold red]")
            return

    # Load full config to get token
    config = config_manager.read_config()
    acc_data = config.get("accounts", {}).get(account["name"], {})

    # Prompt user for new values, defaulting to current
    console.print(f"Updating account: [bold]{account['name']}[/bold]")
    new_url = click.prompt("Jira URL", default=acc_data.get("url", ""), show_default=True)
    new_email = click.prompt("Email", default=acc_data.get("email", ""), show_default=True)
    new_token = click.prompt("API token (leave blank to keep existing)", default="", hide_input=True, show_default=False)

    # If token left blank, keep existing
    if not new_token:
        new_token = acc_data.get("token", "")

    # Validate new credentials
    console.print("Validating updated credentials...")
    if not validate_credentials(new_url, new_email, new_token):
        console.print("[bold red]✗ Invalid credentials. Update aborted.[/bold red]")
        return

    # Save updated account info
    def update_func(cfg):
        accounts = cfg.get("accounts", {})
        if account["name"] not in accounts:
            console.print(f"[bold red]Account '{account['name']}' not found during update.[/bold red]")
            return cfg
        accounts[account["name"]]["url"] = new_url
        accounts[account["name"]]["email"] = new_email
        accounts[account["name"]]["token"] = new_token
        cfg["accounts"] = accounts
        return cfg

    config_manager.update_config(update_func)
    console.print(f"[bold green]✓ Account '{account['name']}' updated successfully.[/bold green]")

@config_cmd.command("check")
@click.option("--name", "-n", help="Account name to check (uses default if not specified)")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed permission information")
def check_account(name: Optional[str], detailed: bool):
    """
    Check if an account is valid and what permissions it has.
    
    This command verifies that the account can connect to Jira,
    checks the validity of the API token, and lists the permissions
    the account has on the Jira instance.
    """
    from ...config.account import get_current_account, list_accounts
    from ...api.client import JiraClient
    import requests
    from requests.auth import HTTPBasicAuth
    from rich.table import Table
    
    # Get the account to check
    account = None
    if name:
        accounts = list_accounts()
        for acc in accounts:
            if acc["name"] == name:
                account = acc
                break
        if not account:
            console.print(f"[bold red]Error:[/bold red] Account '{name}' not found.")
            return
    else:
        account = get_current_account()
        if not account:
            console.print("[bold red]Error:[/bold red] No default account configured.")
            console.print("Use [bold]taskra config add[/bold] to add an account or specify an account with --name.")
            return
    
    # Extract account details
    url = account.get("url")
    email = account.get("email")
    
    # Token is not included in the account info from list_accounts, so we need to get it from the config
    from ...config.manager import config_manager
    config = config_manager.read_config()
    token = config.get("accounts", {}).get(account["name"], {}).get("token")
    
    if not token:
        console.print(f"[bold red]Error:[/bold red] Could not retrieve token for account '{account['name']}'.")
        return
    
    console.print(f"Checking account: [bold]{account['name']}[/bold] ({email})")
    console.print(f"Jira URL: {url}")
    
    # Ensure the URL doesn't end with a slash
    if url.endswith('/'):
        url = url[:-1]
    
    # Create auth object for API requests
    auth = HTTPBasicAuth(email, token)
    
    # Headers for API requests
    headers = {
        "Accept": "application/json"
    }
    
    # Step 1: Verify user identity
    console.print("\n[bold]Verifying account authentication...[/bold]")
    try:
        myself_endpoint = f"{url}/rest/api/3/myself"
        response = requests.get(
            myself_endpoint,
            auth=auth,
            headers=headers
        )
        
        if response.status_code == 200:
            user_data = response.json()
            console.print(f"[bold green]✓ Authentication successful[/bold green]")
            console.print(f"Authenticated as: {user_data.get('displayName')} ({user_data.get('emailAddress')})")
            console.print(f"Account ID: {user_data.get('accountId')}")
            console.print(f"Account active: {'Yes' if user_data.get('active', False) else 'No'}")
            
            # Display groups if available and detailed flag is set
            if detailed and "groups" in user_data and "items" in user_data["groups"]:
                groups = user_data["groups"]["items"]
                if groups:
                    console.print("\n[bold]Group Memberships:[/bold]")
                    for group in groups:
                        console.print(f"- {group.get('name', 'Unknown group')}")
                else:
                    console.print("\n[bold]Group Memberships:[/bold] None")
            
            # Display application roles if available and detailed flag is set
            if detailed and "applicationRoles" in user_data and "items" in user_data["applicationRoles"]:
                roles = user_data["applicationRoles"]["items"]
                if roles:
                    console.print("\n[bold]Application Roles:[/bold]")
                    for role in roles:
                        console.print(f"- {role.get('name', 'Unknown role')}")
                else:
                    console.print("\n[bold]Application Roles:[/bold] None")
        else:
            console.print(f"[bold red]✗ Authentication failed[/bold red] (Status code: {response.status_code})")
            if response.status_code == 401:
                console.print("Invalid credentials. Please check your email and API token.")
            elif response.status_code == 403:
                console.print("Permission denied. Your account may not have sufficient permissions.")
            return
    except Exception as e:
        console.print(f"[bold red]✗ Connection error:[/bold red] {str(e)}")
        return
    
    # Step 2: Check permissions by testing different endpoints
    console.print("\n[bold]Checking API permissions...[/bold]")
    
    # Define the endpoints to check with friendly names
    endpoints_to_check = [
        {"name": "View Projects", "endpoint": "/rest/api/3/project/search", "method": "GET", 
         "description": "List and view projects"},
        {"name": "View Issues", "endpoint": "/rest/api/3/search", "method": "GET", 
         "params": {"maxResults": 1}, "description": "Search and view issues"},
        {"name": "Create Issue", "endpoint": "/rest/api/3/issue", "method": "POST", 
         "check_only": True, "description": "Create new issues"},
        {"name": "Edit Issue", "endpoint": "/rest/api/3/issue/{issueIdOrKey}", "method": "PUT", 
         "check_only": True, "description": "Edit existing issues"},
        {"name": "Add Comment", "endpoint": "/rest/api/3/issue/{issueIdOrKey}/comment", "method": "POST", 
         "check_only": True, "description": "Add comments to issues"},
        {"name": "View Worklogs", "endpoint": "/rest/api/3/issue/{issueIdOrKey}/worklog", "method": "GET", 
         "check_only": True, "description": "View time tracking information"},
        {"name": "Add Worklog", "endpoint": "/rest/api/3/issue/{issueIdOrKey}/worklog", "method": "POST", 
         "check_only": True, "description": "Log work on issues"},
    ]
    
    # Create a table for permissions
    table = Table(title="Jira API Permissions")
    table.add_column("Permission", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Description", style="dim")
    
    # Find a sample issue key if needed
    sample_issue_key = None
    try:
        search_response = requests.get(
            f"{url}/rest/api/3/search",
            auth=auth,
            headers=headers,
            params={"maxResults": 1}
        )
        if search_response.status_code == 200:
            issues = search_response.json().get("issues", [])
            if issues:
                sample_issue_key = issues[0].get("key")
    except:
        pass
    
    # Check each endpoint
    for check in endpoints_to_check:
        endpoint = check["endpoint"]
        method = check["method"]
        
        # Replace placeholders with actual values if we have them
        if "{issueIdOrKey}" in endpoint and sample_issue_key:
            endpoint = endpoint.replace("{issueIdOrKey}", sample_issue_key)
        elif "{issueIdOrKey}" in endpoint and not sample_issue_key:
            # Skip checks that require an issue key if we couldn't find one
            table.add_row(
                check["name"],
                "[yellow]⚠ Skipped[/yellow]",
                f"{check['description']} (No sample issue found)"
            )
            continue
        
        # For endpoints marked as check_only, we don't actually make the request
        # as it might modify data - we just check if we could make the request
        if check.get("check_only", False):
            # For these, we check permission via options request
            try:
                options_response = requests.options(
                    f"{url}{endpoint}",
                    auth=auth,
                    headers=headers
                )
                
                # If we get a successful response or are specifically unauthorized
                # (rather than a general server error), we can determine the permission
                if options_response.status_code in [200, 204, 401, 403]:
                    allowed_methods = options_response.headers.get("Allow", "").split(", ")
                    if method in allowed_methods:
                        table.add_row(
                            check["name"],
                            "[bold green]✓ Allowed[/bold green]",
                            check["description"]
                        )
                    else:
                        table.add_row(
                            check["name"],
                            "[bold red]✗ Not allowed[/bold red]",
                            check["description"]
                        )
                else:
                    table.add_row(
                        check["name"],
                        f"[yellow]⚠ Unknown ({options_response.status_code})[/yellow]",
                        check["description"]
                    )
            except Exception as e:
                table.add_row(
                    check["name"],
                    "[yellow]⚠ Error[/yellow]",
                    f"{check['description']} (Error: {str(e)})"
                )
        else:
            # For GET endpoints, make the actual request
            try:
                params = check.get("params", {})
                response = requests.get(
                    f"{url}{endpoint}",
                    auth=auth,
                    headers=headers,
                    params=params
                )
                
                if response.status_code in [200, 201, 204]:
                    table.add_row(
                        check["name"],
                        "[bold green]✓ Allowed[/bold green]",
                        check["description"]
                    )
                elif response.status_code in [401, 403]:
                    table.add_row(
                        check["name"],
                        "[bold red]✗ Not allowed[/bold red]",
                        check["description"]
                    )
                else:
                    table.add_row(
                        check["name"],
                        f"[yellow]⚠ Error ({response.status_code})[/yellow]",
                        check["description"]
                    )
            except Exception as e:
                table.add_row(
                    check["name"],
                    "[yellow]⚠ Error[/yellow]",
                    f"{check['description']} (Error: {str(e)})"
                )
    
    # Display the permissions table
    console.print(table)
    
    # Step 3: Check projects (since this is what you were having trouble with)
    console.print("\n[bold]Checking project access...[/bold]")
    try:
        projects_response = requests.get(
            f"{url}/rest/api/3/project/search",
            auth=auth,
            headers=headers,
            params={"maxResults": 50}
        )
        
        if projects_response.status_code == 200:
            projects_data = projects_response.json()
            projects = projects_data.get("values", [])
            project_count = len(projects)
            
            if project_count > 0:
                console.print(f"[bold green]✓ Found {project_count} projects[/bold green]")
                
                if detailed and project_count > 0:
                    projects_table = Table(title="Available Projects")
                    projects_table.add_column("Key", style="cyan")
                    projects_table.add_column("Name")
                    projects_table.add_column("Type", style="dim")
                    
                    for project in projects[:10]:  # Limit to first 10 projects
                        projects_table.add_row(
                            project.get("key", "Unknown"),
                            project.get("name", "Unknown"),
                            project.get("projectTypeKey", "Unknown")
                        )
                    
                    if project_count > 10:
                        console.print(projects_table)
                        console.print(f"[dim]...and {project_count - 10} more projects[/dim]")
                    else:
                        console.print(projects_table)
            else:
                console.print("[bold yellow]⚠ No projects found[/bold yellow]")
                console.print("Your account may not have permission to view any projects, or there might not be any projects in this Jira instance.")
                console.print("Possible solutions:")
                console.print("1. Ask a Jira administrator to grant you access to at least one project")
                console.print("2. Create a new project if you have permission to do so")
        else:
            console.print(f"[bold red]✗ Failed to retrieve projects[/bold red] (Status code: {projects_response.status_code})")
    except Exception as e:
        console.print(f"[bold red]✗ Error checking projects:[/bold red] {str(e)}")
    
    # Final summary
    console.print("\n[bold]Summary:[/bold]")
    if user_data.get("active", False):
        console.print("[bold green]✓ Your account is active and authenticated successfully.[/bold green]")
        if sample_issue_key:
            console.print("[bold green]✓ You have access to at least one issue.[/bold green]")
        else:
            console.print("[bold yellow]⚠ You don't appear to have access to any issues.[/bold yellow]")
        
        project_count = len(projects) if 'projects' in locals() else 0
        if project_count > 0:
            console.print(f"[bold green]✓ You have access to {project_count} projects.[/bold green]")
        else:
            console.print("[bold yellow]⚠ You don't have access to any projects.[/bold yellow]")
            console.print("This is likely why 'taskra projects' is not showing any results.")
    else:
        console.print("[bold red]✗ Your account appears to be inactive.[/bold red]")
        console.print("Please contact your Jira administrator to resolve this issue.")
