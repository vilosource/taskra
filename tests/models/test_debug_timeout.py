"""Debug timeout mechanism for tests to prevent hanging."""

import pytest
import signal
import functools
import logging
import os

# Default timeout in seconds
DEFAULT_TIMEOUT = int(os.environ.get('PYTEST_TIMEOUT', '30'))

def timeout(seconds=DEFAULT_TIMEOUT):
    """Add a timeout to a test function."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Test timed out after {seconds} seconds")
                
            # Set the timeout
            orig_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                # Restore the original handler and cancel the alarm
                signal.signal(signal.SIGALRM, orig_handler)
                signal.alarm(0)
                
            return result
        return wrapper
    return decorator

# Apply timeout to ALL tests, not just those marked with @timeout
@pytest.fixture(autouse=True, scope="function")
def apply_timeout_to_all_tests(request):
    """Apply timeout to all tests automatically."""
    # Get timeout from marker or use default
    marker = request.node.get_closest_marker("timeout")
    seconds = DEFAULT_TIMEOUT
    if marker:
        seconds = marker.kwargs.get("seconds", DEFAULT_TIMEOUT)
    
    # Skip timeout for certain test patterns
    test_name = request.node.name
    if any(pattern in test_name for pattern in ['conftest', 'fixture']):
        return
        
    def timeout_handler(signum, frame):
        test_path = f"{request.module.__name__}::{test_name}"
        logging.error(f"TIMEOUT: Test {test_path} timed out after {seconds} seconds")
        pytest.exit(f"Test {test_path} timed out")
        
    # Set the timeout
    orig_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    def finalizer():
        signal.alarm(0)
        signal.signal(signal.SIGALRM, orig_handler)
        
    request.addfinalizer(finalizer)
