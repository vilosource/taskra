"""Cache utilities for Taskra."""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional
import logging

# Default TTL of 15 minutes (in seconds)
DEFAULT_TTL = 15 * 60

def get_cache_dir():
    """Get the cache directory path."""
    cache_dir = os.path.join(str(Path.home()), ".taskra", "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def generate_cache_key(**params) -> str:
    """Generate a cache key from the provided parameters."""
    # Sort parameters to ensure consistent key generation
    sorted_items = sorted((k, str(v)) for k, v in params.items() if v is not None)
    return "_".join(f"{k}-{v}" for k, v in sorted_items)

def save_to_cache(key: str, data: Any) -> None:
    """Save data to cache with timestamp."""
    cache_path = os.path.join(get_cache_dir(), f"{key}.json")
    
    cache_data = {
        "timestamp": time.time(),
        "data": data
    }
    
    with open(cache_path, "w") as f:
        json.dump(cache_data, f)
    
    logging.debug(f"Saved data to cache: {cache_path}")

def get_from_cache(key: str, ttl: int = DEFAULT_TTL) -> Optional[Any]:
    """
    Retrieve data from cache if available and not expired.
    
    Args:
        key: The cache key
        ttl: Time to live in seconds (default: 15 minutes)
        
    Returns:
        The cached data or None if no valid cache exists
    """
    cache_path = os.path.join(get_cache_dir(), f"{key}.json")
    
    if not os.path.exists(cache_path):
        logging.debug(f"Cache miss: {cache_path} (file not found)")
        return None
    
    try:
        with open(cache_path, "r") as f:
            cache_data = json.load(f)
        
        timestamp = cache_data.get("timestamp", 0)
        current_time = time.time()
        
        # Check if cache has expired
        if current_time - timestamp > ttl:
            logging.debug(f"Cache expired: {cache_path} (age: {current_time - timestamp:.1f}s, ttl: {ttl}s)")
            return None
        
        logging.debug(f"Cache hit: {cache_path} (age: {current_time - timestamp:.1f}s)")
        return cache_data.get("data")
        
    except (json.JSONDecodeError, KeyError, IOError) as e:
        logging.debug(f"Cache error: {cache_path} - {str(e)}")
        return None
