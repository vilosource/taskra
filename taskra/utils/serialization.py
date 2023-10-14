"""
Serialization utilities for Pydantic models.

This module provides helper functions for serializing Pydantic models
and other complex types to JSON-compatible formats, with special handling
for datetime objects, nested models, and other non-serializable types.
"""

import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union, Type, TypeVar, cast

# Type variable for generic model deserialization
T = TypeVar('T')

def to_serializable(obj: Any) -> Any:
    """
    Convert any object to a JSON-serializable format.
    
    Handles Pydantic models, datetime objects, and other complex types.
    
    Args:
        obj: Any Python object
        
    Returns:
        JSON-serializable version of the object
    """
    # Handle None
    if obj is None:
        return None
        
    # Handle Pydantic models (v2 onlyear

    if hasattr(obj, 'model_dump'):
        # Use Pydantic v2 method
        result = obj.model_dump(by_alias=True)
        return to_serializable(result)
        
    # Handle datetime objects
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
        
    # Handle lists
    if isinstance(obj, list):
        return [to_serializable(item) for item in obj]
        
    # Handle dictionaries
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
        
    # Handle sets
    if isinstance(obj, set):
        return [to_serializable(item) for item in obj]
        
    # Return primitive types as-is
    return obj

def serialize_to_json(obj: Any, **kwargs) -> str:
    """
    Convert any object to a JSON string.
    
    Args:
        obj: Any Python object
        **kwargs: Additional arguments to pass to json.dumps
        
    Returns:
        JSON string representation
    """
    return json.dumps(to_serializable(obj), **kwargs)

def deserialize_datetime(value: Optional[str]) -> Optional[datetime]:
    """
    Deserialize an ISO format datetime string.
    
    Args:
        value: ISO format datetime string or None
        
    Returns:
        datetime object or None
    """
    if not value:
        return None
        
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        # Handle different ISO formats
        try:
            # Try with UTC 'Z' format
            if value.endswith('Z'):
                value = value[:-1] + '+00:00'
            return datetime.fromisoformat(value)
        except ValueError:
            # If all else fails, return None rather than crashing
            return None

def deserialize_model(data: Any, model_class: Type[T]) -> T:
    """
    Deserialize data into a Pydantic model.
    
    This function handles common deserialization patterns and edge cases
    when converting data (dict, JSON string, etc.) to Pydantic models.
    
    Args:
        data: Source data (dict, JSON string, or another model)
        model_class: Target Pydantic model class
        
    Returns:
        An instance of the specified model class
    
    Raises:
        ValueError: If data cannot be deserialized to the model
    """
    # Handle None case
    if data is None:
        raise ValueError(f"Cannot deserialize None to {model_class.__name__}")
    
    # If data is already an instance of the target class, return it
    if isinstance(data, model_class):
        return data
    
    # If data is a JSON string, parse it first
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}")
    
    # Only handle Pydantic v2 models
    try:
        return model_class.model_validate(data)
    except Exception as e:
        raise ValueError(f"Failed to deserialize to {model_class.__name__}: {e}")
