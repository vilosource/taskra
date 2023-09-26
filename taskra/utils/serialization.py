"""
Serialization utilities for Pydantic models.

This module provides helper functions for serializing Pydantic models
and other complex types to JSON-compatible formats, with special handling
for datetime objects, nested models, and other non-serializable types.
"""

import json
import logging
from datetime import datetime, date, time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set, Union, TypeVar, Type
from pydantic import BaseModel

# Type for anything that might be serializable
SerializableType = Union[Dict, List, Tuple, Set, str, int, float, bool, None]


def to_serializable(obj: Any) -> SerializableType:
    """
    Convert any object to a JSON-serializable format.
    
    This function recursively converts Pydantic models, datetime objects,
    and other complex types into JSON-serializable dictionaries, lists,
    and primitive values.
    
    Args:
        obj: The object to convert
        
    Returns:
        A JSON-serializable version of the object
    """
    # Handle None
    if obj is None:
        return None
    
    # Handle Pydantic models
    if isinstance(obj, BaseModel):
        # For Pydantic models, use the model_dump_api method if available
        if hasattr(obj, 'model_dump_api'):
            result = obj.model_dump_api()
        else:
            # Fall back to model_dump with by_alias=True
            if hasattr(obj, 'model_dump'):
                # Pydantic v2
                result = obj.model_dump(by_alias=True)
            else:
                # Pydantic v1
                result = obj.dict(by_alias=True)
        
        # Process the result to handle any nested objects
        return to_serializable(result)
    
    # Handle datetime objects
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    
    # Handle other objects with isoformat method
    if hasattr(obj, 'isoformat') and callable(obj.isoformat):
        return obj.isoformat()
    
    # Handle enums
    if isinstance(obj, Enum):
        return obj.value
    
    # Handle collections
    if isinstance(obj, dict):
        return {str(k): to_serializable(v) for k, v in obj.items()}
    
    if isinstance(obj, list):
        return [to_serializable(item) for item in obj]
    
    if isinstance(obj, tuple):
        return tuple(to_serializable(item) for item in obj)
    
    if isinstance(obj, set):
        return {to_serializable(item) for item in obj}
    
    # Handle objects with __dict__ attribute
    if hasattr(obj, '__dict__'):
        try:
            return to_serializable(obj.__dict__)
        except Exception as e:
            logging.warning(f"Failed to serialize {type(obj)} using __dict__: {e}")
    
    # Try to directly serialize (for primitive types)
    try:
        json.dumps(obj)
        return obj
    except (TypeError, OverflowError):
        # If this fails, convert to string as fallback
        return str(obj)


def serialize_to_json(obj: Any, **kwargs) -> str:
    """
    Serialize any object to a JSON string.
    
    Args:
        obj: The object to serialize
        **kwargs: Additional arguments to pass to json.dumps
        
    Returns:
        JSON string representation of the object
    """
    serializable_obj = to_serializable(obj)
    return json.dumps(serializable_obj, **kwargs)


def deserialize_datetime(value: str) -> datetime:
    """
    Convert a string to a datetime object.
    
    Args:
        value: ISO-formatted datetime string
        
    Returns:
        datetime object
    
    Raises:
        ValueError: If the string cannot be parsed as a datetime
    """
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        # Handle special cases or alternative formats here
        # For example, try different formats or cleanup the string
        
        # Try without microseconds or timezone
        if 'T' in value:
            date_part, time_part = value.split('T', 1)
            time_part = time_part.split('.')[0]  # Remove microseconds
            cleaned_value = f"{date_part}T{time_part}"
            try:
                return datetime.fromisoformat(cleaned_value)
            except ValueError:
                pass
        
        # Re-raise if all attempts fail
        raise ValueError(f"Cannot parse datetime from string: {value}")


M = TypeVar('M', bound=BaseModel)

def deserialize_model(model_class: Type[M], data: Dict[str, Any]) -> M:
    """
    Deserialize a dictionary into a Pydantic model instance.
    
    This function handles pre-processing of data before passing to
    the Pydantic model constructor, such as converting ISO datetime
    strings to datetime objects for fields that require it.
    
    Args:
        model_class: The Pydantic model class
        data: Dictionary containing data to deserialize
        
    Returns:
        An instance of the model_class
    """
    try:
        return model_class.model_validate(data)
    except Exception as e:
        logging.warning(f"Error deserializing to {model_class.__name__}: {e}")
        
        # Try with more lenient validation
        try:
            return model_class.model_validate(data, mode='lenient')
        except Exception as e2:
            logging.error(f"Failed to deserialize with lenient mode: {e2}")
            raise
