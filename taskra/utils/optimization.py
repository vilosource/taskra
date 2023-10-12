"""Performance optimization utilities for Taskra."""

import time
import functools
import logging
from typing import Any, Callable, TypeVar, Dict, cast

T = TypeVar('T')

# Cache for expensive operations
_operation_cache: Dict[str, Any] = {}

def memoize(max_size: int = 128) -> Callable:
    """
    Memoize a function to avoid repeated expensive operations.
    
    Args:
        max_size: Maximum number of results to cache
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key based on args and kwargs
            key = str(args) + str(sorted(kwargs.items()))
            
            # Get from cache or compute
            if key not in cache:
                # If cache is full, remove oldest entry
                if len(cache) >= max_size:
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]
                    
                cache[key] = func(*args, **kwargs)
                
            return cache[key]
            
        # Add cache control methods
        wrapper.clear_cache = lambda: cache.clear()
        wrapper.cache_size = lambda: len(cache)
        
        return wrapper
        
    return decorator

def lazy_property(func: Callable) -> property:
    """
    Create a lazily-evaluated property that caches its value.
    
    Args:
        func: Function to wrap
        
    Returns:
        Property descriptor
    """
    attr_name = '_lazy_' + func.__name__

    @property
    @functools.wraps(func)
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)
    
    return _lazy_property

def benchmark(func: Callable[..., T]) -> Callable[..., T]:
    """
    Benchmark a function's execution time.
    
    Args:
        func: Function to benchmark
        
    Returns:
        Decorated function that logs performance metrics
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        # Log performance information
        logging.debug(f"PERF: {func.__module__}.{func.__name__} took {elapsed*1000:.2f}ms")
        
        return result
    
    return wrapper
