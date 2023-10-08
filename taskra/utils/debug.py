"""
Debug utilities for Taskra.

This module contains useful debug functions to help diagnose issues,
especially with API responses and model structures.
"""

import json
import pprint
from typing import Any, Optional
import inspect
import sys
from datetime import datetime

def dump_model_structure(
    obj: Any, 
    name: str = "object", 
    max_depth: int = 3, 
    current_depth: int = 0,
    file=None
) -> None:
    """
    Print the structure of an object (especially useful for Pydantic models).
    
    Args:
        obj: Object to examine
        name: Name of the object
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth (used internally)
        file: File to write to (default: sys.stdout)
    """
    indent = "  " * current_depth
    
    if file is None:
        file = sys.stdout
        
    if current_depth >= max_depth:
        print(f"{indent}{name}: [Max depth reached]", file=file)
        return
        
    if obj is None:
        print(f"{indent}{name}: None", file=file)
        return
        
    # Handle Pydantic models
    if hasattr(obj, "model_fields") and hasattr(obj, "model_dump"):
        print(f"{indent}{name} ({obj.__class__.__name__}):", file=file)
        
        # Get all attributes (including dynamic ones)
        fields_and_values = {}
        for key, value in obj.__dict__.items():
            if key.startswith("_"):
                continue
            fields_and_values[key] = value
            
        # Process each field
        for field_name, value in fields_and_values.items():
            dump_model_structure(value, field_name, max_depth, current_depth + 1, file)
            
    # Handle dictionaries
    elif isinstance(obj, dict):
        if len(obj) == 0:
            print(f"{indent}{name}: {{}}", file=file)
        else:
            print(f"{indent}{name}: {{", file=file)
            for key, value in obj.items():
                dump_model_structure(value, str(key), max_depth, current_depth + 1, file)
            print(f"{indent}}}", file=file)
            
    # Handle lists and tuples
    elif isinstance(obj, (list, tuple)):
        if len(obj) == 0:
            print(f"{indent}{name}: []", file=file)
        else:
            print(f"{indent}{name}: [", file=file)
            if len(obj) > 5:
                # For long lists, just show first and last items
                for i, item in enumerate(obj[:2]):
                    dump_model_structure(item, f"[{i}]", max_depth, current_depth + 1, file)
                print(f"{indent}  ... {len(obj) - 4} more items ...", file=file)
                for i, item in enumerate(obj[-2:]):
                    dump_model_structure(item, f"[{len(obj) - 2 + i}]", max_depth, current_depth + 1, file)
            else:
                for i, item in enumerate(obj):
                    dump_model_structure(item, f"[{i}]", max_depth, current_depth + 1, file)
            print(f"{indent}]", file=file)
            
    # Simple types
    else:
        type_name = type(obj).__name__
        value_str = str(obj)
        if len(value_str) > 100:
            value_str = value_str[:97] + "..."
        print(f"{indent}{name}: {value_str} ({type_name})", file=file)

def debug_issue_fields(issue: Any) -> None:
    """
    Debug helper specifically for issue fields extraction.
    
    This function helps identify how fields are structured 
    in the issue object, which is useful for troubleshooting.
    
    Args:
        issue: Issue object to analyze
    """
    print("\n=== DEBUG ISSUE FIELDS ===")
    
    # Check if issue has fields attribute
    if hasattr(issue, "fields"):
        fields = issue.fields
        
        # Print field attributes
        print(f"Fields object type: {type(fields).__name__}")
        
        if hasattr(fields, "__dict__"):
            print("\nFields attributes:")
            for key, value in fields.__dict__.items():
                if key.startswith("_"):
                    continue
                print(f"  {key}: {type(value).__name__}")
                # Show value for simple types
                if isinstance(value, (str, int, float, bool)) or value is None:
                    print(f"    Value: {value}")
                    
        # Try to access common fields
        print("\nCommon field access tests:")
        
        # Summary field
        try:
            summary = getattr(fields, "summary", "[Not found as attribute]")
            print(f"  summary (attr): {summary}")
        except Exception as e:
            print(f"  summary (attr) error: {str(e)}")
            
        # Status field
        try:
            status = getattr(fields, "status", "[Not found as attribute]")
            print(f"  status: {type(status).__name__}")
            if status:
                if hasattr(status, "name"):
                    print(f"    status.name: {status.name}")
                elif isinstance(status, dict) and "name" in status:
                    print(f"    status['name']: {status['name']}")
        except Exception as e:
            print(f"  status error: {str(e)}")
            
        # Assignee field
        try:
            assignee = getattr(fields, "assignee", "[Not found as attribute]")
            print(f"  assignee: {type(assignee).__name__}")
            if assignee:
                for attr in ["display_name", "displayName", "name", "emailAddress"]:
                    if hasattr(assignee, attr):
                        print(f"    assignee.{attr}: {getattr(assignee, attr)}")
                if isinstance(assignee, dict):
                    for key in ["displayName", "name", "emailAddress"]:
                        if key in assignee:
                            print(f"    assignee['{key}']: {assignee[key]}")
        except Exception as e:
            print(f"  assignee error: {str(e)}")
            
        # Priority field
        try:
            priority = getattr(fields, "priority", "[Not found as attribute]")
            print(f"  priority: {type(priority).__name__}")
            if priority:
                if hasattr(priority, "name"):
                    print(f"    priority.name: {priority.name}")
                elif isinstance(priority, dict) and "name" in priority:
                    print(f"    priority['name']: {priority['name']}")
        except Exception as e:
            print(f"  priority error: {str(e)}")
            
        # Date fields
        for date_field in ["created", "updated"]:
            try:
                value = getattr(fields, date_field, "[Not found as attribute]")
                print(f"  {date_field}: {type(value).__name__}")
                if value:
                    print(f"    Value: {value}")
                    if isinstance(value, datetime):
                        print(f"    Formatted: {value.strftime('%Y-%m-%d %H:%M')}")
            except Exception as e:
                print(f"  {date_field} error: {str(e)}")
                
    else:
        print("Issue has no 'fields' attribute!")
        
    print("==========================\n")
