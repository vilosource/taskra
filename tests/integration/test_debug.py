"""Debug utilities for integration testing."""

import sys
import importlib


def debug_imports(module_name):
    """Debug imports for a given module."""
    print(f"\nDebugging imports for {module_name}:")
    
    # Try importing the module and print what happens
    try:
        # Remove the module if it's already imported to ensure fresh import
        if module_name in sys.modules:
            del sys.modules[module_name]
            
        module = importlib.import_module(module_name)
        print(f"Successfully imported {module_name}")
        
        # Show module info
        print(f"Module file: {module.__file__}")
        print(f"Module dict keys: {list(module.__dict__.keys())[:10]}...")
        
        # If it's a package, show submodules
        if hasattr(module, "__path__"):
            print(f"Package path: {module.__path__}")
            
    except ImportError as e:
        print(f"Failed to import {module_name}: {e}")
        
    except Exception as e:
        print(f"Other error while importing {module_name}: {e}")
    
    # Show sys.path
    print("\nPython path:")
    for i, path in enumerate(sys.path[:5]):
        print(f"  {i}: {path}")
    if len(sys.path) > 5:
        print(f"  ... and {len(sys.path) - 5} more paths")
    
    # Show loaded modules that match the prefix
    print(f"\nLoaded modules starting with '{module_name.split('.')[0]}':")
    matching_modules = [name for name in sys.modules.keys() 
                       if name.startswith(module_name.split('.')[0])]
    for name in sorted(matching_modules)[:20]:
        print(f"  {name}")
    if len(matching_modules) > 20:
        print(f"  ... and {len(matching_modules) - 20} more modules")
