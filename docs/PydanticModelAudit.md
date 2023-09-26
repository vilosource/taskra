# Pydantic Model Audit

This document catalogs the existing Pydantic models in Taskra, identifies inconsistencies, and documents current naming conventions and alias usage.

## Model Catalog

### API Models

#### Worklog Models
- **Location**: `taskra/api/models/worklog.py`
- **Models**:
  - `Author`: Represents worklog author information
  - `Visibility`: Represents worklog visibility settings
  - `Worklog`: Detailed worklog model
  - `WorklogCreate`: Model for creating a new worklog
  - `WorklogList`: List of worklogs with pagination info

#### Project Models
- **Location**: `taskra/api/models/project.py`
- **Models**:
  - `ProjectAvatar`: Represents project avatar URLs
  - `ProjectCategory`: Project category information
  - `Project`: Core project model with details
  - `ProjectList`: Paginated list of projects
- **Key Fields**:
  - `id`: Project identifier
  - `key`: Project key (e.g., "PROJ")
  - `name`: Project name
  - `avatar_urls`: Dictionary or nested model for avatar images
  - `project_type_key`: Type of project
- **Notable Features**:
  - Multiple URL fields requiring validation
  - Optional fields for project configuration
  - Relations to issue types and components

#### Issue Models
- **Location**: `taskra/api/models/issue.py`
- **Models**:
  - `IssueType`: Represents issue type (Bug, Task, etc.)
  - `IssuePriority`: Priority information
  - `IssueStatus`: Status information
  - `IssueFields`: Contains all issue fields
  - `Issue`: Core issue model with all details
  - `IssueCreate`: Model for creating a new issue
  - `IssueUpdate`: Model for updating existing issues
  - `IssueList`: Paginated list of issues
- **Key Fields**:
  - `id`: Issue identifier
  - `key`: Issue key (e.g., "PROJ-123")
  - `summary`: Issue title/summary
  - `description`: Issue description
  - `status`: Current status
  - `assignee`: User assignment information
  - `reporter`: User who created the issue
  - `created`, `updated`: Timestamp fields
  - `priority`: Issue priority information
- **Notable Features**:
  - Extensive nesting of related models
  - Complex custom field handling
  - Many optional fields
  - DateTime fields requiring serialization
  - Multiple relationships to other models

#### User Models
- **Location**: `taskra/api/models/user.py`
- **Models**:
  - `UserAvatar`: Avatar URL information
  - `User`: Core user information
  - `CurrentUser`: Extended model for authenticated user
- **Key Fields**:
  - `account_id`: User's account identifier
  - `display_name`: User's display name
  - `email_address`: User's email
  - `active`: Boolean indicating active status
  - `avatar_urls`: Dictionary or nested model for avatar images
  - `time_zone`: User's timezone information
- **Notable Features**:
  - Email validation requirements
  - Optional fields for permissions
  - Integration with authentication system

## Field Naming Conventions

### Current State
- **API Field Names**: camelCase (e.g., `displayName`, `timeSpent`, `timeSpentSeconds`)
- **Model Field Names**: snake_case (e.g., `display_name`, `time_spent`, `time_spent_seconds`)
- **Alias Usage**: Inconsistent use of field aliases

### Examples
From `worklog.py`:
```python
class Author(BaseModel):
    account_id: str = Field(..., alias="accountId")
    display_name: str = Field(..., alias="displayName")
```

## Inconsistencies

### Alias Usage
- Some models use explicit aliases for all fields
- Other models rely on default model_config settings
- Inconsistent handling of optional vs required fields

### Validation
- Inconsistent validation rules across similar fields
- Some models use field validators, others don't
- Varying approaches to handling null/None values

### Serialization
- No consistent approach to model serialization
- Manual handling of datetime serialization
- Custom serialization functions instead of model methods

## Field Mapping Issues

### Currently Observed Issues
- Field name inconsistencies between API and models cause rendering failures
- Custom serialization is needed for cache storage
- Special handling for critical fields like `author.displayName` and `timeSpent`

## Field Analysis

### Common Fields Across Models

| Field Pattern | Models Using | Type Consistency | Alias Consistency |
|---------------|--------------|-----------------|-------------------|
| `id` | Worklog, Project, Issue, User | Mostly string | Consistent |
| `self` (URL) | Worklog, Project, Issue | String URL | Consistent |
| `*_id` fields | Various | Mix of int/string | Inconsistent |
| Timestamps | Worklog, Issue | datetime | Consistent |
| `name`/`display_name` | Project, User | string | Consistent |
| `avatar_urls` | Project, User | dict/model | Inconsistent structure |

### Validation Patterns

- **URL Fields**: No consistent validation
- **Required vs Optional**: Inconsistent approach to marking fields as required
- **Default Values**: Mix of explicit defaults and None
- **Custom Validators**: Sporadic usage with no standard pattern

## Model Relationships

```
User ─────┐
          ├──► Issue ◄─┐
Project ──┘            │
                       │
User ◄──── Worklog ────┘
```

- **Worklogs** reference Issues and Users (author)
- **Issues** reference Projects and Users (assignee, reporter)
- **Projects** contain minimal external references

## Missing Models

- **Comment** models for issue comments
- **Attachment** models for file attachments
- **Dashboard** models
- **Filter** models for JQL filters
- **Board** models for Agile boards
- **Sprint** models for Agile sprints

## Recommendations

1. Standardize alias usage across all models
2. Create base models with common configuration
3. Implement consistent validation approach
4. Develop standardized serialization utilities
5. Document field mapping standards

## Extended Recommendations

1. Create a `BaseJiraModel` with common configuration:
   ```python
   class BaseJiraModel(BaseModel):
       model_config = ConfigDict(
           populate_by_name=True, 
           extra="ignore", 
           alias_generator=to_camel
       )
   ```

2. Implement consistent datetime field handling:
   ```python
   created: datetime = Field(default_factory=datetime.now)
   updated: Optional[datetime] = None
   ```

3. Standardize URL validation:
   ```python
   @field_validator("self", "url", mode="before")
   @classmethod
   def validate_url(cls, v: str) -> str:
       # Standardized URL validation logic
       return v
   ```

4. Create consistent nested model handling:
   ```python
   @field_validator("fields", mode="before")
   @classmethod
   def ensure_fields_model(cls, v: Union[Dict, "IssueFields"]) -> "IssueFields":
       if isinstance(v, dict):
           return IssueFields.model_validate(v)
       return v
   ```

5. Develop a model documentation system using docstrings and Sphinx

## Next Steps

- Complete model inventory with detailed field analysis
- Document validation rules for each model type
- Map dependencies between models
- Identify models missing for complete API coverage
