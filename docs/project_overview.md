# Taskra Project Documentation

Welcome to the Taskra Project documentation. This is the central repository for all documentation related to the Taskra CLI tool.

## Project Overview

Taskra is a command-line interface (CLI) tool designed to streamline task and worklog management. The project provides functionalities for tracking issues, managing projects, generating reports, and logging work time.

## Current Status: In Development (April 2025)

All major components are currently in active development with significant progress made on core modules.

## Project Architecture

Taskra follows a modular architecture with the following key components:

### 1. Core Module (TASKRA-1) - In Progress
- Issues management (core/issues.py)
- Projects management (core/projects.py)
- Reports generation (core/reports.py)
- Tickets management (core/tickets.py)
- Users management (core/users.py)
- Worklogs tracking (core/worklogs.py)
- Comments handling (core/comments.py)

### 2. API Implementation (TASKRA-2) - In Progress
- Authentication (api/auth.py)
- Client functionality (api/client.py)
- API models and data structures
- API services for external communication
- API utilities

### 3. Command Line Interface (TASKRA-3) - In Progress
- Main CLI entrypoint (cmd/main.py)
- Command structure and handling
- CLI utilities and helpers
- Command-specific implementations

### 4. Configuration Management (TASKRA-4) - In Progress
- Account configuration (config/account.py)
- Configuration commands (config/config_cmd.py)
- Configuration manager (config/manager.py)
- Core configuration functionality (config/config.py)

### 5. Presentation Layer (TASKRA-5) - In Progress
- Base presentation components (presentation/base.py)
- Error handling and display (presentation/errors.py)
- Issue presentation (presentation/issues.py)
- Project presentation (presentation/projects.py)
- Report presentation (presentation/reports.py)
- Worklog presentation (presentation/worklogs.py)

### 6. Utilities and Helpers (TASKRA-6) - In Progress
- Caching mechanisms (utils/cache.py)
- Debugging tools (utils/debug.py)
- Model adapters (utils/model_adapters.py)
- Model caching (utils/model_cache.py)
- Performance optimization (utils/optimization.py)
- Serialization utilities (utils/serialization.py)

## Jira Tickets and Epics

The Taskra project is organized into 6 main epics, each representing a key component of the system, with various tasks that implement specific features.

### Epics

#### TASKRA-1: Core Module Implementation
This epic covers the essential components that manage various aspects of the application, including issues management, projects management, reports generation, tickets management, users management, worklogs tracking, and comments handling.

**Status:** In Progress

#### TASKRA-2: API Implementation
This epic includes authentication, client functionality, API models and data structures, API services for external communication, and API utilities. It handles all external service integration and data exchange.

**Status:** In Progress

#### TASKRA-3: Command Line Interface
This epic covers the main CLI entrypoint, command structure and handling, CLI utilities and helpers, and command-specific implementations. It provides the user-facing interface for the application.

**Status:** In Progress

#### TASKRA-4: Configuration Management
This epic manages application settings, user preferences, and persistent configuration, including account configuration, configuration commands, configuration manager, and core configuration functionality.

**Status:** In Progress

#### TASKRA-5: Presentation Layer
This epic handles formatting and displaying information to users, including base presentation components, error handling and display, issue presentation, project presentation, report presentation, and worklog presentation.

**Status:** In Progress

#### TASKRA-6: Utilities and Helpers
This epic provides cross-cutting concerns and helper functionality used throughout the application, including caching mechanisms, debugging tools, model adapters, model caching, performance optimization, and serialization utilities.

**Status:** In Progress

### Completed Tasks

#### TASKRA-7: Implement Worklog Tracking Functionality
This task implemented worklog tracking functionality in core/worklogs.py, including creating, reading, updating, and deleting worklog entries, searching and filtering worklogs, calculating time spent on issues, and tracking worklog history.

**Status:** Done

#### TASKRA-8: Implement Issues Management Functionality
This task implemented the core issues management functionality in core/issues.py, including creating, reading, updating, and deleting issues, searching and filtering issues, tracking issue status changes, and handling issue relationships.

**Status:** Done

#### TASKRA-9: Implement Projects Management Functionality
This task implemented the core projects management functionality in core/projects.py, including listing and retrieving projects, filtering projects by criteria, handling project metadata, and project status tracking.

**Status:** Done

#### TASKRA-10: Implement Jira Authentication
This task implemented Jira authentication functionality in api/auth.py, including handling Jira API token-based authentication, managing authentication sessions, implementing credential storage and retrieval, and error handling for authentication failures.

**Status:** Done

### Ticket Relationships and Dependencies

The epics represent the main components of the system, while the tasks implement specific features within those components. The completed tasks (TASKRA-7 through TASKRA-10) have provided the foundation for the ongoing epic implementations. As more tasks are completed, the epics will move toward completion.

## Completed Tasks

The following components have been fully implemented:

- ✅ Worklog tracking functionality (TASKRA-7)
- ✅ Issues management functionality (TASKRA-8)
- ✅ Projects management functionality (TASKRA-9)
- ✅ Jira authentication (TASKRA-10)

## Development Guidelines

### Project Structure
The project follows a modular architecture with clear separation of concerns:
```
taskra/
├── api/           # API layer for external services
├── cmd/           # Command-line interface
├── config/        # Configuration management
├── core/          # Core business logic
├── presentation/  # User interface components
└── utils/         # Utilities and helpers
```

### Testing
- Unit tests are located in the tests/ directory
- Integration tests ensure components work together correctly
- Test fixtures provide consistent test data

### Development Workflow
1. Pick an issue from the backlog
2. Develop the feature or fix
3. Write tests to validate functionality
4. Submit for review
5. Integrate into main branch

## Getting Started

To get started with Taskra development:

1. Clone the repository
2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```
3. Run the tests:
   ```bash
   poetry run pytest
   ```
4. Explore the codebase to understand the structure

## Resources

- [GitHub Repository](#) (Link to be added)
- [Jira Board](https://viloforge.atlassian.net/browse/TASKRA)
- [Development Guidelines](#) (Link to be added)

## Contact

For questions about this project, please contact the project maintainer.

---

*Last updated: April 6, 2025*