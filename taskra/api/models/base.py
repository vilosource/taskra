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
    
    This class provides common configuration and utility methods for all Jira API models 
    to ensure consistent behavior across the application. It handles serialization to and 
    from the Jira API format, including automatic conversion between snake_case (Python standard)
    and camelCase (Jira API standard) field names. It also provides robust error handling
    and graceful degradation when dealing with incomplete or invalid API responses.
    
    Features:
    - Automatic field name conversion between snake_case and camelCase
    - Graceful handling of missing or invalid API data
    - Consistent serialization of datetime objects
    - Utility methods for API-compatible JSON output
    """
    
    model_config = ConfigDict(
        populate_by_name=True,  # Allow populating by attribute name or alias
        extra="ignore",         # Ignore extra fields in API responses
        alias_generator=to_camel # Auto-convert snake_case to camelCase
    )
    
    def model_dump_api(self, **kwargs) -> Dict[str, Any]:
        """
        Serialize model to API-compatible format.
        
        This method converts the model to a dictionary suitable for sending to the Jira API,
        ensuring that field names are in camelCase and datetime objects are properly serialized
        to ISO format strings.
        
        Args:
            **kwargs: Additional arguments to pass to model_dump
            
        Returns:
            Dict with camelCase keys suitable for Jira API.
        """
        # Ensure by_alias=True to get camelCase field names
        kwargs["by_alias"] = True
        
        # Add datetime serialization
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
            
        # Get the model as a dict
        data = self.model_dump(**kwargs)
        
        # Handle datetime serialization
        for key, value in list(data.items()):
            if isinstance(value, datetime):
                # Convert datetime to ISO format string for API compatibility
                data[key] = value.isoformat()
        
        return data
    
    def model_dump_json_api(self, **kwargs) -> str:
        """
        Serialize model to API-compatible JSON.
        
        This method converts the model to a JSON string suitable for sending to the Jira API,
        ensuring that field names are in camelCase.
        
        Args:
            **kwargs: Additional arguments to pass to model_dump_json
            
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
        
        This method provides robust handling of API responses, attempting to create a valid
        model instance even if some fields have validation errors. It will:
        1. Try to validate the full data
        2. If validation fails, remove problematic fields
        3. Apply sensible defaults for missing fields
        4. Create a model with as much valid data as possible
        
        Args:
            data: Dictionary from API response
        
        Returns:
            An instance of this model, potentially with default values for invalid fields
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
    """
    Base class for paginated list responses from Jira.
    
    This class represents paginated list responses commonly returned by the Jira API.
    It provides standard fields for handling pagination, including the starting index,
    maximum results per page, and total items available. This allows for consistent
    handling of paginated responses throughout the application and simplifies
    iterating through multiple pages of results.
    """
    
    start_at: int = Field(..., description="Index of the first item")
    max_results: int = Field(..., description="Maximum results per page")
    total: Optional[int] = Field(None, description="Total number of items available")
    

class ApiResource(BaseJiraModel):
    """
    Base class for API resources with standard fields.
    
    This class provides a foundation for all Jira API resources that have a self URL,
    which is nearly all resources in the Jira REST API. It handles the field name conflict
    between Python's 'self' keyword and Jira's 'self' field by mapping it to 'self_url',
    while maintaining compatibility through a property getter.
    
    The class also provides URL validation to ensure the self URL is properly formatted.
    """
    
    # Change from 'self' to 'self_url' to avoid Python keyword conflict
    self_url: str = Field(..., alias="self", description="URL to this resource")
    
    @field_validator("self_url")
    @classmethod
    def validate_self_url(cls, v: str) -> str:
        """
        Validate that self_url is a valid URL.
        
        Args:
            v: The URL string to validate
            
        Returns:
            The validated URL string
            
        Raises:
            ValueError: If the URL doesn't start with http:// or https://
        """
        if not v.startswith(("http://", "https://")):
            raise ValueError("self_url must start with http:// or https://")
        return v
        
    @property
    def self(self) -> str:
        """
        Property getter to maintain backward compatibility with tests and existing code.
        
        Returns:
            The self URL as a string
        """
        return self.self_url


class TimestampedResource(ApiResource):
    """
    Base class for resources with creation and update timestamps.
    
    This class extends ApiResource to add timestamp fields that are common to many
    Jira resources. It standardizes the handling of creation and update timestamps,
    ensuring consistent datetime handling across the application. This is particularly
    useful for resources like issues, comments, and worklogs that track when they were
    created and last modified.
    """
    
    created: datetime = Field(..., description="When this resource was created")
    updated: datetime = Field(..., description="When this resource was last updated")
