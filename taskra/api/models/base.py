"""Base model classes for Taskra's Pydantic models."""

from datetime import datetime
from typing import Any, Dict, Optional, TypeVar, Type, cast
from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationError

# Type variable for generic model methods
T = TypeVar('T', bound='BaseJiraModel')

def to_camel(snake_str: str) -> str:
    """
    Convert snake_case to camelCase.
    
    Args:
        snake_str: A string in snake_case format
        
    Returns:
        The equivalent string in camelCase format
    """
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class BaseJiraModel(BaseModel):
    """
    Base class for all Jira API models.
    
    This class provides common configuration and utility methods
    for all Jira API models to ensure consistent behavior.
    """
    
    model_config = ConfigDict(
        populate_by_name=True,  # Allow populating by attribute name or alias
        extra="ignore",         # Ignore extra fields in API responses
        alias_generator=to_camel # Auto-convert snake_case to camelCase
    )
    
    def model_dump_api(self, **kwargs) -> Dict[str, Any]:
        """
        Serialize model to API-compatible format.
        
        Returns:
            Dict with camelCase keys suitable for Jira API.
        """
        # Ensure by_alias=True to get camelCase field names
        kwargs["by_alias"] = True
        return self.model_dump(**kwargs)
    
    def model_dump_json_api(self, **kwargs) -> str:
        """
        Serialize model to API-compatible JSON.
        
        Returns:
            JSON string with camelCase keys suitable for Jira API.
        """
        # Ensure by_alias=True to get camelCase field names
        kwargs["by_alias"] = True
        return self.model_dump_json(**kwargs)
        
    @classmethod
    def from_api(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create a model instance from API data.
        
        Args:
            data: Dictionary from API response
        
        Returns:
            An instance of this model
        """
        try:
            return cls.model_validate(data)
        except ValidationError as e:
            # Log validation errors but try to continue with partial data
            import logging
            logging.warning(f"Validation error in {cls.__name__}: {e}")
            
            # Create a model with only the valid fields, using default values for the rest
            # First, extract field names that have validation errors
            error_fields = {err["loc"][0] for err in e.errors()}
            
            # Create a clean dict without the problematic fields
            clean_data = {k: v for k, v in data.items() if k not in error_fields}
            
            # Create default values dictionary for all fields
            default_values = {}
            model_fields = cls.model_fields
            
            # Prepare default values for all fields
            for field_name, field_info in model_fields.items():
                # Only provide defaults for fields not already in clean_data
                if field_name not in clean_data and field_name not in default_values:
                    # Use type-appropriate defaults based on annotation
                    annotation_str = str(field_info.annotation)
                    if "str" in annotation_str:
                        default_values[field_name] = ""
                    elif "int" in annotation_str:
                        default_values[field_name] = 0
                    elif "float" in annotation_str:
                        default_values[field_name] = 0.0
                    elif "bool" in annotation_str:
                        default_values[field_name] = False
                    elif "List" in annotation_str or "list" in annotation_str:
                        default_values[field_name] = []
                    elif "Dict" in annotation_str or "dict" in annotation_str:
                        default_values[field_name] = {}
                    # For other types, no default (will be None)
            
            # Combine clean data with defaults (clean data takes precedence)
            complete_data = {**default_values, **clean_data}
            
            try:
                # Try to create the model with complete data including defaults
                return cls(**complete_data)
            except Exception as ex:
                logging.error(f"Failed to create model with defaults: {ex}")
                # As an absolute last resort, create with minimal data
                return cls()

class BaseJiraListModel(BaseJiraModel):
    """Base class for paginated list responses from Jira."""
    
    start_at: int = Field(..., description="Index of the first item")
    max_results: int = Field(..., description="Maximum results per page")
    total: Optional[int] = Field(None, description="Total number of items available")
    

class ApiResource(BaseJiraModel):
    """Base class for API resources with standard fields."""
    
    # Change from 'self' to 'self_url' to avoid Python keyword conflict
    self_url: str = Field(..., alias="self", description="URL to this resource")
    
    @field_validator("self_url")
    @classmethod
    def validate_self_url(cls, v: str) -> str:
        """Validate that self_url is a valid URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("self_url must start with http:// or https://")
        return v
        
    @property
    def self(self) -> str:
        """Property getter to maintain backward compatibility with tests and existing code."""
        return self.self_url


class TimestampedResource(ApiResource):
    """
    Base class for resources with creation and update timestamps.
    
    Many Jira resources include created and updated timestamps.
    """
    
    created: datetime = Field(..., description="When this resource was created")
    updated: datetime = Field(..., description="When this resource was last updated")
