# Taskra Code Guide

This document is for developers wishing to understand the layout and architecture of the Taskra codebase.

## Project Directory Structure

```
taskra/
├── api/                    # API interaction layer
│   ├── client.py           # JiraClient base class
│   ├── auth.py             # Authentication providers
│   ├── services/           # Service layer for API endpoints
│   │   ├── __init__.py
│   │   ├── base.py         # Abstract BaseService
│   │   ├── projects.py     # ProjectsService implementation
│   │   ├── issues.py       # IssuesService implementation
│   │   ├── worklogs.py     # WorklogService implementation
│   │   ├── users.py        # UserService for user-related API calls
│   │   └── reports.py      # ReportService for generating reports
│   └── models/             # Data models 
│       ├── __init__.py
│       ├── project.py      # Pydantic models for Projects
│       ├── issue.py        # Pydantic models for Issues
│       ├── worklog.py      # Pydantic models for Worklogs
│       └── user.py         # Pydantic models for Users
├── cmd/                    # CLI commands
│   ├── __init__.py
│   ├── main.py             # Main CLI entry point
│   ├── commands/           # Command implementations
│   │   ├── __init__.py
│   │   ├── projects.py     # Project-related commands
│   │   ├── issues.py       # Issue-related commands
│   │   ├── worklogs.py     # Worklog-related commands
│   │   ├── tickets.py      # Ticket report commands
│   │   └── config.py       # Configuration commands
│   └── utils/              # Command utilities
│       ├── __init__.py
│       └── formatting.py   # Text formatting utilities
├── core/                   # Business logic for all Jira entities
│   ├── __init__.py
│   ├── issues.py           # Uses IssuesService from api.services
│   ├── projects.py         # Uses ProjectsService from api.services
│   ├── worklogs.py         # Uses WorklogService from api.services
│   └── reports.py          # Reporting functionality
├── config/                 # Configuration management
│   ├── __init__.py
│   ├── manager.py          # Configuration file operations
│   └── account.py          # Account management functionality
└── utils/                  # Utility functions and helpers
    ├── __init__.py
    └── cache.py            # Cache utilities
```

## Introduction

The Taskra codebase is designed following SOLID principles to ensure scalability, maintainability, and readability. These principles guide the separation of concerns and the modular structure of the codebase.

### Applying SOLID Design Principles: From Command Line to API Call

The `taskra projects` command demonstrates how Taskra achieves SOLID principles through a layered architecture. Let's trace the execution flow:

#### 1. Command Layer (Entry Point)

The execution starts in `cmd/main.py`, which defines the CLI using Click:

```python
@click.group()
def cli():
    """Taskra - Task and project management from the command line."""
    pass

cli.add_command(projects_cmd)
```

The `projects_cmd` function is imported from `cmd/commands/projects.py`:

```python
@click.command("projects")
@click.option("--json", "-j", "json_output", is_flag=True, help="Output raw JSON")
@click.option("--debug", "-d", is_flag=True, help="Show debug information")
def projects_cmd(json_output, debug):
    """List available projects."""
    from ...core import list_projects
    from ...presentation import render_projects  # Hypothetical presentation service
    
    try:
        # Get projects list - command's responsibility ends with getting data
        projects_list = list_projects()
        
        # Delegate presentation to a separate service
        render_projects(projects_list, format="json" if json_output else "table")
    except Exception as e:
        # Even error handling presentation could be delegated
        render_error(e, debug=debug)
```

**SOLID Principle:** While the current implementation has the command handler handling both argument parsing and result presentation, this actually violates SRP. An improved architecture would separate these responsibilities:

1. **Command Handler**: Should only be responsible for:
   - Parsing command arguments
   - Input validation
   - Delegating to core business logic

2. **Presentation Service**: Should be responsible for:
   - Formatting the data for display
   - Rendering output to the user (tables, JSON, etc.)

This separation would better adhere to SRP by giving each component a single reason to change.

#### 2. Core Layer (Business Logic)

The command calls `list_projects()` from the core module (`core/projects.py`):

```python
def list_projects():
    """List available projects."""
    client = get_client()
    projects_service = ProjectsService(client)
    projects = projects_service.list_all_projects()
    
    return projects
```

**SOLID Principles:**
- **SRP:** The core function is focused only on the business logic of retrieving projects
- **OCP:** You can extend functionality by adding new core functions without modifying existing ones
- **DIP:** The core depends on abstractions (services) rather than concrete implementations

#### 3. Service Layer (API Integration)

The core function uses `ProjectsService` from `api/services/projects.py`:

```python
class ProjectsService(BaseService):
    """Service for interacting with Jira projects API."""
    
    def list_all_projects(self, max_results_per_page: int = 50) -> List[Dict[str, Any]]:
        """Get all projects visible to the user, handling pagination."""
        all_projects = []
        start_at = 0
        is_last_page = False
        
        while not is_last_page:
            # Paginate through results
            response = self.client.get(self._get_endpoint("project/search"), params={...})
            project_list = ProjectList.model_validate(response)

            # Process results
            all_projects.extend([project.model_dump(by_alias=False) for project in project_list.values])
            
            # Check if we need to continue pagination
            # ...
        
        return all_projects
```

**SOLID Principles:**
- **SRP:** The service is responsible only for Jira projects API operations
- **LSP:** All services extend BaseService, ensuring they can be used interchangeably
- **ISP:** The service exposes only methods relevant to project operations

#### 4. Model Layer (Data Validation)

The service uses Pydantic models from `api/models/project.py`:

```python
class ProjectSummary(BaseModel):
    """Basic project information."""
    id: str
    key: str
    name: str
    # ...

class ProjectList(BaseModel):
    """List of projects with pagination info."""
    start_at: int = Field(..., alias="startAt")
    max_results: int = Field(..., alias="maxResults")
    total: int
    is_last: bool = Field(..., alias="isLast")
    values: List[ProjectSummary]
    # ...
```

**SOLID Principles:**
- **SRP:** Models are responsible only for data structure and validation
- **OCP:** New fields can be added without changing existing model behavior

#### 5. Client Layer (HTTP Communication)

The service uses `JiraClient` from `api/client.py`:

```python
class JiraClient:
    def __init__(self, base_url: str, auth: Dict[str, str], debug: bool = False):
        # ...
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Handle HTTP GET requests
        # ...
```

**SOLID Principles:**
- **SRP:** The client is responsible only for HTTP communication
- **DIP:** Services depend on client abstraction, not implementation details

#### Benefits of This Architecture

This layered design provides several advantages:

1. **Separation of Concerns:** Each layer has a specific responsibility
2. **Testability:** Each component can be tested in isolation with mocks
3. **Maintainability:** Changes in one layer don't affect others
4. **Extensibility:** New commands, services, or models can be added without modifying existing code

For example, if we want to add a new command `taskra projects search`, we only need to:
1. Add a new command function in `cmd/commands/projects.py`
2. Add a corresponding core function in `core/projects.py`
3. Add a new method to `ProjectsService` if needed

This demonstrates how the architecture adheres to the Open/Closed Principle by being open for extension but closed for modification.

### Implementing Reports in Taskra

The `taskra reports` command demonstrates how Taskra generates reports using the same layered architecture. Let's trace the execution flow:

#### 1. Command Layer (Entry Point)

The execution starts in `cmd/main.py`, which defines the CLI using Click:

```python
@click.group()
def cli():
    """Taskra - Task and project management from the command line."""
    pass

cli.add_command(reports_cmd)
```

The `reports_cmd` function is imported from `cmd/commands/reports.py`:

```python
@click.command("reports")
@click.option("--type", "-t", type=str, required=True, help="Type of report to generate")
@click.option("--output", "-o", type=str, help="Output file for the report")
def reports_cmd(type, output):
    """Generate reports."""
    from ...core import generate_report
    
    try:
        report_data = generate_report(type)
        if output:
            with open(output, "w") as f:
                f.write(report_data)
        else:
            print(report_data)
    except Exception as e:
        # Error handling
        # ...
```

#### 2. Core Layer (Business Logic)

The command calls `generate_report()` from the core module (`core/reports.py`):

```python
def generate_report(report_type: str) -> str:
    """Generate a report based on the type."""
    client = get_client()
    reports_service = ReportService(client)
    report = reports_service.generate(report_type)
    
    return report
```

#### 3. Service Layer (API Integration)

The core function uses `ReportService` from `api/services/reports.py`:

```python
class ReportService(BaseService):
    """Service for generating reports."""
    
    def generate(self, report_type: str) -> str:
        """Generate a report based on the type."""
        response = self.client.get(self._get_endpoint(f"reports/{report_type}"))
        return response.get("data", "")
```

#### 4. Model Layer (Data Validation)

The service uses Pydantic models from `api/models/report.py`:

```python
class Report(BaseModel):
    """Report data."""
    type: str
    data: str
```

#### 5. Client Layer (HTTP Communication)

The service uses `JiraClient` from `api/client.py`.

#### Benefits of This Architecture

The same benefits apply to the reports functionality, ensuring consistency and adherence to SOLID principles.