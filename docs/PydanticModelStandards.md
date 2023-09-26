# Taskra Pydantic Model Standards

This document defines the standardized approach for implementing Pydantic models in Taskra. These standards aim to ensure consistency, improve maintainability, and solve the serialization challenges identified in the [Pydantic Model Audit](./PydanticModelAudit.md).

## Base Models

### BaseJiraModel

All Jira API models should inherit from the `BaseJiraModel` class:

```python
from pydantic import BaseModel, ConfigDict

def to_camel(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

class BaseJiraModel(BaseModel):
    """Base class for all Jira API models."""
    
    model_config = ConfigDict(
        populate_by_name=True,  # Allow populating by attribute name or alias
        extra="ignore",         # Ignore extra fields in API responses
        alias_generator=to_camel # Auto-convert snake_case to camelCase
    )
    
    def model_dump_api(self, **kwargs):
        """
        Serialize model to API-compatible format.
        
        Returns:
            Dict with camelCase keys suitable for Jira API.
        """
        # Ensure by_alias=True to get camelCase field names
        return self.model_dump(by_alias=True, **kwargs)
    
    def model_dump_json_api(self, **kwargs):
        """
        Serialize model to API-compatible JSON.
        
        Returns:
            JSON string with camelCase keys suitable for Jira API.
        """
        # Ensure by_alias=True to get camelCase field names
        return self.model_dump_json(by_alias=True, **kwargs)
```

## Naming Conventions

### Field Names

- **Python Fields**: Use `snake_case` for all model fields
- **API Fields**: Use `camelCase` for all API field aliases
- **Field Declaration**: Always use explicit type hints

```python
# Good
summary: str
description: Optional[str] = None
time_spent_seconds: int = Field(..., alias="timeSpentSeconds")

# Avoid
summary = ""  # Missing type hint
TimeSpent: int  # Not snake_case
```

### Model Names

- **Model Classes**: Use `PascalCase` for all model class names
- **Model Naming Pattern**: `{Entity}[Purpose]`
  - Examples: `Project`, `IssueCreate`, `UserDetail`, `WorklogList`

## Field Definition Standards

### Required vs Optional Fields

- **Required Fields**: Use ellipsis (`...`) as field default
- **Optional Fields**: Mark with `Optional[Type]` and provide default
- **Default Values**: Use `None` for optional fields unless another default is appropriate

```python
# Required field
id: str = Field(...)

# Optional field with None default
description: Optional[str] = None

# Optional field with non-None default
active: bool = True
```

### Common Field Patterns

#### ID Fields

```python
id: str = Field(...)  # Primary identifier
key: Optional[str] = None  # Business key (like PROJ-123)
```

#### URL Fields

```python
self: HttpUrl = Field(..., description="API URL for this resource")
```

#### Timestamp Fields

```python
created: datetime = Field(...)
updated: Optional[datetime] = None
```

## Validation

### Field Validators

Use consistent validation patterns:

```python
from pydantic import field_validator

class MyModel(BaseJiraModel):
    url: str
    
    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v
```

### Custom Types

Create custom types for common patterns:

```python
# For JQL strings
class JqlQuery(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        # Validate JQL syntax
        return v
```

## Serialization Standards

### To/From API

- Always use `by_alias=True` when serializing for API
- Use `exclude_unset=True` for partial updates
- Use `exclude_none=True` when sending to API

### To/From Cache

- Serialize models with `model_dump_api()` before caching
- Deserialize from cache with `Model.model_validate(cached_data)`

### Datetime Handling

- Use ISO format for datetime serialization
- Parse ISO datetime strings with consistent approach

## Documentation Standards

### Model Docstrings

```python
class Issue(BaseJiraModel):
    """
    Represents a Jira issue.
    
    API Endpoint: /rest/api/3/issue/{issueIdOrKey}
    
    Attributes:
        id: Unique identifier
        key: Issue key (e.g., PROJ-123)
        fields: Issue fields including summary, description, etc.
    """
    id: str
    key: str
    fields: "IssueFields"
```

### Field Descriptions

Use Field's description parameter for important notes:

```python
summary: str = Field(
    ...,
    description="Issue summary text, maximum 255 characters"
)
```

## Implementation Examples

### Complete Model Example

```python
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, field_validator

class WorklogCreate(BaseJiraModel):
    """
    Model for creating a new worklog entry.
    
    API Endpoint: POST /rest/api/3/issue/{issueIdOrKey}/worklog
    """
    time_spent_seconds: int = Field(..., alias="timeSpentSeconds", ge=1)
    comment: Optional[str] = None
    started: Optional[datetime] = None
    
    @field_validator("time_spent_seconds")
    @classmethod
    def validate_time_spent(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Time spent must be positive")
        return v
```

## Migration Strategy

1. Create the base model classes first
2. Update one module at a time, starting with core models
3. Use IDE refactoring tools to update references
4. Add thorough tests for each updated model
5. Update service classes to use new model methods

## Testing Guidelines

- Test serialization/deserialization roundtrips
- Test validation with both valid and invalid inputs
- Test compatibility with actual API responses
