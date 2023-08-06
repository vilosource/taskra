# Taskra Project Design

Taskra is a command-line tool for task and project management that integrates with Jira. It follows SOLID design principles to ensure a maintainable, extensible codebase.

## Architecture

### 1. Package Structure

#### Current Structure
```
taskra/
├── api/
│   ├── client.py           # JiraClient base class
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base.py         # Abstract BaseService
│   │   ├── projects.py     # ProjectsService implementation
│   │   ├── issues.py       # IssuesService implementation
│   │   └── worklogs.py     # WorklogService implementation
│   └── models/
│       ├── __init__.py
│       ├── project.py      # Pydantic models for Projects
│       ├── issue.py        # Pydantic models for Issues
│       └── worklog.py      # Pydantic models for Worklogs
├── cmd/                    # CLI commands
│   ├── __init__.py
│   └── main.py
├── core/                   # Business logic for all Jira entities
│   ├── __init__.py
│   ├── issues.py           # Uses IssuesService from api.services
│   ├── projects.py         # Uses ProjectsService from api.services
│   └── worklogs.py         # Uses WorklogService from api.services
```

#### Updated Structure with Account Management and Tests
```
taskra/
├── api/                    # API interaction layer
│   ├── client.py           # JiraClient base class
│   ├── services/           # Service layer for API endpoints
│   │   ├── __init__.py
│   │   ├── base.py         # Abstract BaseService
│   │   ├── projects.py     # ProjectsService implementation
│   │   ├── issues.py       # IssuesService implementation
│   │   ├── worklogs.py     # WorklogService implementation
│   │   └── users.py        # UserService for user-related API calls
│   └── models/             # Data models 
│       ├── __init__.py
│       ├── project.py      # Pydantic models for Projects
│       ├── issue.py        # Pydantic models for Issues
│       ├── worklog.py      # Pydantic models for Worklogs
│       └── user.py         # Pydantic models for Users
├── cmd/                    # CLI commands
│   ├── __init__.py
│   ├── main.py
│   └── config_cmd.py       # Configuration management commands
├── config/                 # Configuration management
│   ├── __init__.py
│   ├── manager.py          # Configuration file operations
│   ├── account.py          # Account management functionality
│   └── credentials.py      # Secure credential storage
├── core/                   # Business logic for all Jira entities
│   ├── __init__.py
│   ├── issues.py           # Uses IssuesService from api.services
│   ├── projects.py         # Uses ProjectsService from api.services
│   ├── worklogs.py         # Uses WorklogService from api.services
│   └── users.py            # User-related business logic
└── tests/                  # Test suite
    ├── unit/               # Unit tests
    │   ├── api/            # Tests for API layer
    │   │   ├── test_client.py
    │   │   ├── services/
    │   │   │   ├── test_projects.py
    │   │   │   ├── test_issues.py
    │   │   │   ├── test_worklogs.py
    │   │   │   └── test_users.py
    │   │   └── models/
    │   │       ├── test_project.py
    │   │       ├── test_issue.py
    │   │       ├── test_worklog.py
    │   │       └── test_user.py
    │   ├── config/         # Tests for configuration module
    │   │   ├── test_manager.py
    │   │   ├── test_account.py
    │   │   └── test_credentials.py
    │   ├── core/           # Tests for core business logic
    │   │   ├── test_projects.py
    │   │   ├── test_issues.py
    │   │   ├── test_worklogs.py
    │   │   └── test_users.py
    │   └── cmd/            # Tests for CLI commands
    │       ├── test_main.py
    │       └── test_config_cmd.py
    ├── integration/        # Integration tests
    │   ├── test_api_integration.py
    │   ├── test_cli_integration.py
    │   └── test_account_integration.py
    └── fixtures/           # Test fixtures and mock data
        ├── projects.py
        ├── issues.py
        ├── worklogs.py
        └── accounts.py
```

### 2. SOLID Principles Implementation

#### Single Responsibility Principle
Each component has a single responsibility:
- `JiraClient`: Handles authentication and HTTP communication
- Service classes: Interface with specific Jira endpoints (projects, issues, worklogs)
- Model classes: Define data structures and validation rules
- Command modules: Handle CLI interaction

#### Open/Closed Principle
- The system is designed to be extended without modifying existing code
- New services can be added by creating new service classes
- CLI commands can be added without changing the core framework

#### Liskov Substitution Principle
- Service classes implement a common interface
- Different implementations (like mock services for testing) can be substituted

#### Interface Segregation Principle
- Each service exposes only methods relevant to its domain
- Clients depend only on the interfaces they use

#### Dependency Inversion Principle
- High-level modules depend on abstractions
- Services depend on abstract client interfaces
- Dependency injection is used where appropriate

### 3. Core Components

#### JiraClient
- Responsible for authentication and HTTP operations
- Handles base URL configuration
- Provides error handling and retries
- Manages API rate limiting

```python
class JiraClient:
    def __init__(self, base_url, auth):
        self.base_url = base_url
        self.auth = auth
        
    def get(self, endpoint, params=None):
        # Implementation
        
    def post(self, endpoint, data=None, json=None):
        # Implementation
        
    # Additional HTTP methods
```

#### BaseService
- Abstract base class for all services
- Defines common service interface
- Enforces consistent patterns across services

```python
class BaseService:
    def __init__(self, client):
        self.client = client
```

#### Service Implementations
- Each service focuses on a specific domain (projects, issues, worklogs)
- Maps to corresponding Jira API endpoints
- Transforms API responses into domain objects

#### Data Models
- Pydantic models for data validation
- Type annotations for better IDE support
- Consistent representation of API resources

#### Flow Architecture
```
CLI Commands → Core Functions → API Services → JiraClient → Jira REST API
```

- **CLI Commands**: Handle user input, display output
- **Core Functions**: Implement business logic, orchestrate operations
- **API Services**: Translate business operations to API calls
- **JiraClient**: Handles HTTP communication, authentication, error handling

This architecture ensures:
1. Separation of concerns
2. Testability (services can be mocked)
3. Reusability (services can be used by different core functions)
4. Maintainability (changes to API don't affect core business logic)

## Implementation Details

### Account Management

Account management should be implemented in a dedicated `config` module. This separation of concerns follows the SOLID principles and keeps the configuration and account management functionality isolated from API and core business logic.

#### Key Files for Account Management:

1. **config/manager.py**: Handles reading/writing configuration files
   - Responsible for managing the `config.json` file
   - Provides methods to read, update, and write configuration

2. **config/account.py**: Implements account management logic
   - Add/remove/update account profiles
   - Set default account
   - Validate account information

3. **cmd/config_cmd.py**: CLI commands for configuration
   - Implements the commands for account management
   - Maps user input to configuration operations

4. **api/services/users.py**: User-related API calls
   - Validates API tokens and credentials
   - Retrieves user information from Jira

#### Flow for Account Operations:

CLI Command → config/account.py → config/manager.py → api/client.py

The account management functionality should:
1. Support multiple accounts with distinct configurations
2. Store all data in a simple plain text configuration file
3. Allow easy switching between accounts
4. Support environment variable overrides for CI/CD
5. Validate credentials before saving

The `config.json` file uses the following structure:  
```json
{
  "default_account": "mycompany",
  "accounts": {
    "mycompany": {
      "url": "https://mycompany.atlassian.net",
      "auth_type": "token",
      "email": "user@example.com",
      "token": "your-api-token"
    },
    "personal": {
      "url": "https://personal.atlassian.net",
      "auth_type": "token",
      "email": "me@example.com",
      "token": "your-personal-api-token"
    }
  },
  "settings": {
    "timeout": 30,
    "cache_ttl": 300
  }
}
```

### Authentication

Taskra supports multiple authentication methods:
- Personal Access Token
- Basic Authentication (username/password)
- OAuth (planned)

### Error Handling

- Network errors are caught and presented with clear messages
- API errors include relevant details for troubleshooting
- Validation errors prevent invalid data from being sent

## Future Enhancements  
// ...existing code...  

## Development Workflow  
// ...existing code...  

## Testing Strategy  
// ...existing code...  

### Extension Points  
// ...existing code...  

### Command Line Interface  
// ...existing code...  

### Error Handling  
- `JIRA_EMAIL`: Direct email override  
- `JIRA_API_TOKEN`: Direct token override  
- `JIRA_BASE_URL`: Direct URL override  
- `TASKRA_ACCOUNT`: Use a specific account from the config  

For CI/CD and scripting use cases, environment variables can override configuration:  

#### Environment Variables  
1. On first run, Taskra creates a default configuration file.  
2. Users add account details via the CLI.  
3. Taskra uses the default account unless specified otherwise.  
4. Commands accept an optional `--account` parameter to use a non-default account.  

#### Configuration Flow  
The account name is typically derived from the Atlassian Cloud subdomain (e.g., `mycompany` from `mycompany.atlassian.net`).  

- `taskra config list`: List all configured accounts  
- `taskra config add`: Add a new Jira account  
- `taskra config set-default`: Set the default account  
- `taskra config remove`: Remove an account  

Users can manage their Jira accounts through CLI commands:  

#### Account Management  
The tokens themselves are stored in environment variables or a secure credential store, not in the configuration file.  

#### Configuration Format  
The `config.json` file uses the following structure:  
```json
{
  "default_account": "mycompany",
  "accounts": {
    "mycompany": {
      "url": "https://mycompany.atlassian.net",
      "auth_type": "token",
      "email": "user@example.com"
    },
    "personal": {
      "url": "https://personal.atlassian.net",
      "auth_type": "token",
      "email": "me@example.com"
    }
  },
  "settings": {
    "timeout": 30,
    "cache_ttl": 300
  }
}



### Authentication

Taskra supports multiple authentication methods:
- Personal Access Token
- Basic Authentication (username/password)
- OAuth (planned)

### Error Handling

- Network errors are caught and presented with clear messages
- API errors include relevant details for troubleshooting
- Validation errors prevent invalid data from being sent

### Command Line Interface

Built with Click framework:
- Nested command structure
- Help text and documentation
- Input validation
- Rich terminal output

### Extension Points

Taskra is designed to be extended in the following ways:
- Adding new API services
- Implementing custom data transformations
- Creating new CLI commands
- Supporting additional authentication methods

## Testing Strategy

### Unit Tests

Unit tests focus on testing individual components in isolation:
- API client tests with mocked HTTP responses
- Service tests with mocked client
- Model validation tests
- Core function tests with mocked services

### Integration Tests

Integration tests verify that components work together correctly:
- API services with actual HTTP requests (using a test instance or mocked server)
- CLI commands with input/output testing
- End-to-end workflows

### Test Fixtures

Common test fixtures provide reusable test data:
- Mock HTTP responses
- Sample model instances
- Test configuration

### Testing Best Practices

- Use pytest as the testing framework
- Mock external dependencies
- Use parametrized tests for comprehensive coverage
- Aim for high test coverage (>80%)
- Include both positive and negative test cases

## Development Workflow

1. Add new functionality by extending existing components
2. Follow SOLID principles for all new code
3. Write tests before implementing features
4. Document public APIs and CLI commands

## Future Enhancements

- Offline mode with local caching
- Custom report generation
- Integration with additional task management systems
- Workflow automation capabilities
