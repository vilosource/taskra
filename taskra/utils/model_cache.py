"""
Caching utilities for Pydantic models.

This module provides functions for caching Pydantic models
and retrieving them from cache, handling serialization and
deserialization appropriately.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast
from hashlib import md5

from pydantic import BaseModel

from .serialization import to_serializable, deserialize_model

# Type variable for model classes
M = TypeVar('M', bound=BaseModel)

# Default cache directory
DEFAULT_CACHE_DIR = os.path.expanduser("~/.taskra/cache")


def get_cache_path() -> str:
    """
    Get the path to the cache directory.
    
    Returns:
        Path to the cache directory
    """
    cache_dir = os.environ.get("TASKRA_CACHE_DIR", DEFAULT_CACHE_DIR)
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def generate_cache_key(**kwargs) -> str:
    """
    Generate a cache key based on parameters.
    
    Args:
        **kwargs: Key-value pairs to use in generating the cache key
        
    Returns:
        A unique cache key string
    """
    # Convert all values to strings
    key_parts = []
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")
    
    # Create a string representation for hashing
    key_string = "|".join(key_parts)
    
    # Generate MD5 hash for the key string
    return md5(key_string.encode()).hexdigest()


def save_model_to_cache(
    key: str, model: Union[BaseModel, List[BaseModel]], ttl: Optional[int] = None
) -> bool:
    """
    Save a model or list of models to cache.
    
    Args:
        key: Cache key
        model: Model or list of models to cache
        ttl: Time-to-live in seconds (not implemented yet)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cache_path = Path(get_cache_path()) / f"{key}.json"
        
        # Convert model to serializable format
        serializable_data = to_serializable(model)
        
        # Add metadata for model type
        if isinstance(model, list) and model and isinstance(model[0], BaseModel):
            model_type = model[0].__class__.__module__ + "." + model[0].__class__.__name__
            cache_data = {
                "model_type": model_type,
                "is_list": True,
                "data": serializable_data
            }
        elif isinstance(model, BaseModel):
            model_type = model.__class__.__module__ + "." + model.__class__.__name__
            cache_data = {
                "model_type": model_type,
                "is_list": False,
                "data": serializable_data
            }
        else:
            # Fallback for raw data
            cache_data = {
                "model_type": None,
                "is_list": isinstance(model, list),
                "data": serializable_data
            }
        
        # Save to file
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
        
        return True
    except Exception as e:
        logging.error(f"Failed to save model to cache: {e}")
        return False


def get_model_from_cache(
    key: str,
    model_class: Optional[Type[M]] = None
) -> Optional[Union[M, List[M], Dict, List[Dict]]]:
    """
    Retrieve a model or list of models from cache.
    
    Args:
        key: Cache key
        model_class: Optional model class for deserialization
        
    Returns:
        Model instance, list of model instances, or None if not found
    """
    try:
        cache_path = Path(get_cache_path()) / f"{key}.json"
        
        if not cache_path.exists():
            return None
        
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
        
        data = cache_data.get("data")
        is_list = cache_data.get("is_list", False)
        
        # If model_class is provided, deserialize to that class
        if model_class is not None:
            if is_list and isinstance(data, list):
                return [deserialize_model(model_class, item) for item in data]
            else:
                return deserialize_model(model_class, data)
        
        # Otherwise return raw data
        return data
    except Exception as e:
        logging.error(f"Failed to get model from cache: {e}")
        return None
