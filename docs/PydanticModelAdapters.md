# Pydantic Model Adapters

This document describes the adapter pattern implemented for Taskra's Pydantic models to ensure backward compatibility with existing code.

## Overview

As part of our Pydantic model standardization effort, we've implemented adapter functions to ensure that new model-based code can work seamlessly with existing code that expects dictionary structures.

## Adapter Types

### 1. Model-to-Dict Adapters

These adapters convert Pydantic model instances to dictionaries compatible with older code:

```python
# Convert a model to a dictionary
from taskra.utils.model_adapters import adapt_to_dict

worklog_dict = adapt_to_dict(worklog_model)
```

### 2. Dict-to-Model Adapters

These adapters convert dictionaries (potentially from older code) to Pydantic model instances:

```python
# Convert a dictionary to a model
from taskra.utils.model_adapters import adapt_from_dict

worklog_model = adapt_from_dict(worklog_dict, Worklog)
```

### 3. Presentation-Specific Adapters

These adapters ensure that models are compatible with the presentation layer requirements:

```python
# Convert a worklog to a presentation-ready format
from taskra.utils.model_adapters import adapt_worklog_for_presentation

presentation_data = adapt_worklog_for_presentation(worklog)
```

## Key Features

1. **Field Name Preservation**: Maintains both snake_case and camelCase field names as needed
2. **Type Consistency**: Ensures consistent types between old and new code
3. **Missing Field Handling**: Gracefully handles missing or renamed fields
4. **Collection Support**: Works with both individual models and lists of models

## Usage Examples

### Working with Worklogs

```python
from taskra.utils.model_adapters import adapt_worklogs_list
from taskra.core.worklogs import get_user_worklogs

# Get worklogs (returns dictionaries for backward compatibility)
worklogs = get_user_worklogs(username="jsmith")

# If working with the presentation layer, ensure compatibility
presentation_ready = adapt_worklogs_list(worklogs)
```

### Service Layer Example

```python
from taskra.utils.model_adapters import adapt_to_dict
from taskra.api.services.worklogs import WorklogService

service = WorklogService(client)
worklog_model = service.add_worklog("PROJ-123", "2h", "Working on task")

# Convert to dictionary for legacy code
worklog_dict = adapt_to_dict(worklog_model)
```

## Implementation Details

The adapters are implemented in `taskra.utils.model_adapters` and leverage the serialization framework from Phase 2 of the model standardization effort.

## Next Steps

1. Implement adapters for other model types (User, Issue, etc.)
2. Create specialized adapters for more complex presentation requirements
3. Add performance optimization for adapter operations
4. Create comprehensive tests for adapter edge cases
