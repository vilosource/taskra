"""Enhanced benchmarks for measuring performance differences between models and dictionaries."""

import timeit
import statistics
import json
import sys
from datetime import datetime

from taskra.api.models.worklog import Worklog, Author
from taskra.api.models.issue import Issue, IssueFields, IssueType, IssueStatus
from taskra.api.models.user import User
from taskra.utils.model_adapters import adapt_to_dict
from taskra.utils.serialization import to_serializable

class BenchmarkRunner:
    """Runner for performance benchmarks."""
    
    def __init__(self):
        """Initialize the benchmark runner."""
        self.results = {}
    
    def run_benchmark(self, name, func, setup, number=10000, repeat=5):
        """
        Run a benchmark and store the results.
        
        Args:
            name: Name of the benchmark
            func: Function to benchmark
            setup: Setup code
            number: Number of executions per measurement
            repeat: Number of measurements
        """
        print(f"Running benchmark: {name}...")
        times = timeit.repeat(
            func,
            setup=setup,
            number=number,
            repeat=repeat
        )
        
        result = {
            'min': min(times),
            'max': max(times),
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'number': number
        }
        
        self.results[name] = result
        
        # Print immediate results
        print(f"  Median: {result['median']:.6f} seconds")
        
        return result
    
    def compare(self, base_name, compare_name):
        """
        Compare two benchmark results.
        
        Args:
            base_name: Name of the baseline benchmark
            compare_name: Name of the benchmark to compare
        """
        if base_name not in self.results or compare_name not in self.results:
            print(f"Error: Can't compare {base_name} and {compare_name}")
            return
            
        base = self.results[base_name]['median']
        compare = self.results[compare_name]['median']
        
        diff = compare - base
        percentage = (compare / base - 1) * 100
        
        print(f"\nComparison: {compare_name} vs {base_name}")
        print(f"  {base_name}: {base:.6f} seconds")
        print(f"  {compare_name}: {compare:.6f} seconds")
        print(f"  Absolute difference: {diff:.6f} seconds")
        print(f"  Relative difference: {percentage:.2f}%")
        
        return {
            'base': base,
            'compare': compare,
            'diff': diff,
            'percentage': percentage
        }
    
    def report(self):
        """Generate and print a report of all benchmarks."""
        print("\n===== BENCHMARK RESULTS =====")
        
        for name, result in self.results.items():
            print(f"\n{name}:")
            print(f"  Median: {result['median']:.6f} seconds")
            print(f"  Mean: {result['mean']:.6f} seconds")
            print(f"  Min: {result['min']:.6f} seconds")
            print(f"  Max: {result['max']:.6f} seconds")
        
        # Save results to a JSON file for later analysis
        with open('benchmark_results.json', 'w') as f:
            json.dump({k: {k2: v2 for k2, v2 in v.items() if k2 != 'number'} 
                      for k, v in self.results.items()}, f, indent=2)


# Model creation benchmarks
def create_simple_dict():
    """Create a simple dictionary."""
    return {"key": "value", "number": 123}

def create_simple_model():
    """Create a simple model."""
    from pydantic import BaseModel
    
    class SimpleModel(BaseModel):
        key: str
        number: int
    
    return SimpleModel(key="value", number=123)

def create_worklog_dict():
    """Create a complex worklog using dictionaries."""
    return {
        "id": "123",
        "self": "https://example.com/worklog/123",
        "author": {
            "accountId": "user123",
            "displayName": "Test User",
            "active": True,
            "timeZone": "UTC"
        },
        "timeSpent": "1h",
        "timeSpentSeconds": 3600,
        "started": datetime.now().isoformat(),
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "issueId": "456",
        "comment": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "This is a comment"
                        }
                    ]
                }
            ]
        }
    }

def create_worklog_model():
    """Create a complex worklog using models."""
    author = Author(
        accountId="user123",
        displayName="Test User", 
        active=True,
        timeZone="UTC"
    )
    
    comment = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "This is a comment"
                    }
                ]
            }
        ]
    }
    
    return Worklog(
        id="123",
        self_url="https://example.com/worklog/123",
        author=author,
        timeSpent="1h",
        timeSpentSeconds=3600,
        started=datetime.now(),
        created=datetime.now(),
        updated=datetime.now(),
        issue_id="456",
        comment=comment
    )

# Field access benchmarks
def access_dict_simple(obj):
    """Access a simple dictionary field."""
    return obj["key"]

def access_model_simple(obj):
    """Access a simple model field."""
    return obj.key

def access_dict_nested(obj):
    """Access a nested field in a dictionary."""
    return obj["author"]["displayName"]

def access_model_nested(obj):
    """Access a nested field in a model."""
    return obj.author.display_name

# Serialization benchmarks
def serialize_dict_to_json(obj):
    """Serialize a dictionary to JSON."""
    return json.dumps(obj)

def serialize_model_to_json(obj):
    """Serialize a model to JSON."""
    return obj.model_dump_json()

def dict_to_dict_adapter(obj):
    """Adapt a dictionary using the same path as model adaptation."""
    # Create a copy to simulate the same kind of work
    result = dict(obj)
    # Apply the same kinds of modifications the adapter might
    if "author" in result and isinstance(result["author"], dict):
        result["author"] = dict(result["author"])
    return result

def model_to_dict_adapter(obj):
    """Convert model to dictionary using the adapter function."""
    return adapt_to_dict(obj)

# Validation benchmarks
def validate_dict_manual(data):
    """Manually validate a dictionary."""
    errors = []
    
    if "id" not in data:
        errors.append("Missing id field")
    elif not isinstance(data["id"], str):
        errors.append("id must be a string")
        
    if "timeSpentSeconds" not in data:
        errors.append("Missing timeSpentSeconds field")
    elif not isinstance(data["timeSpentSeconds"], int):
        errors.append("timeSpentSeconds must be an integer")
    elif data["timeSpentSeconds"] <= 0:
        errors.append("timeSpentSeconds must be positive")
        
    if "author" not in data:
        errors.append("Missing author field")
    elif not isinstance(data["author"], dict):
        errors.append("author must be a dictionary")
    elif "displayName" not in data["author"]:
        errors.append("author.displayName is required")
        
    return len(errors) == 0, errors

def validate_model_pydantic(data):
    """Validate data using Pydantic."""
    try:
        Worklog.model_validate(data)
        return True, []
    except Exception as e:
        return False, [str(e)]

def run_core_benchmarks():
    """Run the core set of benchmarks."""
    runner = BenchmarkRunner()
    
    # Simple creation
    runner.run_benchmark(
        "Simple Dict Creation",
        "create_simple_dict()",
        "from __main__ import create_simple_dict"
    )
    
    runner.run_benchmark(
        "Simple Model Creation",
        "create_simple_model()",
        "from __main__ import create_simple_model"
    )
    
    # Compare
    runner.compare("Simple Dict Creation", "Simple Model Creation")
    
    # Complex creation
    runner.run_benchmark(
        "Complex Dict Creation",
        "create_worklog_dict()",
        "from __main__ import create_worklog_dict"
    )
    
    runner.run_benchmark(
        "Complex Model Creation",
        "create_worklog_model()",
        "from __main__ import create_worklog_model"
    )
    
    # Compare
    runner.compare("Complex Dict Creation", "Complex Model Creation")
    
    # Simple field access
    runner.run_benchmark(
        "Dict Simple Field Access",
        "access_dict_simple(d)",
        "from __main__ import create_simple_dict, access_dict_simple; d = create_simple_dict()"
    )
    
    runner.run_benchmark(
        "Model Simple Field Access",
        "access_model_simple(m)",
        "from __main__ import create_simple_model, access_model_simple; m = create_simple_model()"
    )
    
    # Compare
    runner.compare("Dict Simple Field Access", "Model Simple Field Access")
    
    # Nested field access
    runner.run_benchmark(
        "Dict Nested Field Access",
        "access_dict_nested(d)",
        "from __main__ import create_worklog_dict, access_dict_nested; d = create_worklog_dict()"
    )
    
    runner.run_benchmark(
        "Model Nested Field Access",
        "access_model_nested(m)",
        "from __main__ import create_worklog_model, access_model_nested; m = create_worklog_model()"
    )
    
    # Compare
    runner.compare("Dict Nested Field Access", "Model Nested Field Access")
    
    # Serialization
    runner.run_benchmark(
        "Dict to JSON",
        "serialize_dict_to_json(d)",
        "from __main__ import create_worklog_dict, serialize_dict_to_json; d = create_worklog_dict()",
        number=5000  # Fewer iterations for slower operations
    )
    
    runner.run_benchmark(
        "Model to JSON",
        "serialize_model_to_json(m)",
        "from __main__ import create_worklog_model, serialize_model_to_json; m = create_worklog_model()",
        number=5000  # Fewer iterations for slower operations
    )
    
    # Compare
    runner.compare("Dict to JSON", "Model to JSON")
    
    # Adapter conversions
    runner.run_benchmark(
        "Dict Adapter",
        "dict_to_dict_adapter(d)",
        "from __main__ import create_worklog_dict, dict_to_dict_adapter; d = create_worklog_dict()",
        number=5000
    )
    
    runner.run_benchmark(
        "Model Adapter",
        "model_to_dict_adapter(m)",
        "from __main__ import create_worklog_model, model_to_dict_adapter; m = create_worklog_model()",
        number=5000
    )
    
    # Compare
    runner.compare("Dict Adapter", "Model Adapter")
    
    # Validation
    runner.run_benchmark(
        "Dict Validation",
        "validate_dict_manual(d)",
        "from __main__ import create_worklog_dict, validate_dict_manual; d = create_worklog_dict()",
        number=5000
    )
    
    runner.run_benchmark(
        "Model Validation",
        "validate_model_pydantic(d)",
        "from __main__ import create_worklog_dict, validate_model_pydantic; d = create_worklog_dict()",
        number=5000
    )
    
    # Compare
    runner.compare("Dict Validation", "Model Validation")
    
    # Print the final report
    runner.report()
    
    return runner

def run_memory_benchmark():
    """Run memory usage benchmarks."""
    import os
    import resource
    import gc
    
    print("\n===== MEMORY USAGE BENCHMARKS =====")
    
    def get_memory():
        """Get current memory usage in MB."""
        # Force garbage collection
        gc.collect()
        # Get memory info
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024  # Convert from KB to MB on Linux
    
    baseline = get_memory()
    print(f"Baseline memory usage: {baseline:.2f} MB")
    
    # Test with dictionaries
    dict_objects = []
    dict_start = get_memory()
    for _ in range(10000):
        dict_objects.append(create_worklog_dict())
    dict_end = get_memory()
    dict_usage = dict_end - dict_start
    print(f"Memory for 10,000 dictionaries: {dict_usage:.2f} MB")
    
    # Clear and force garbage collection
    dict_objects = None
    gc.collect()
    
    # Test with models
    model_objects = []
    model_start = get_memory()
    for _ in range(10000):
        model_objects.append(create_worklog_model())
    model_end = get_memory()
    model_usage = model_end - model_start
    print(f"Memory for 10,000 models: {model_usage:.2f} MB")
    
    # Compare
    print(f"\nDifference: {model_usage - dict_usage:.2f} MB")
    print(f"Relative increase: {(model_usage / dict_usage - 1) * 100:.2f}%")
    
    return {
        'dict_usage': dict_usage,
        'model_usage': model_usage,
        'difference': model_usage - dict_usage,
        'percentage': (model_usage / dict_usage - 1) * 100
    }

if __name__ == "__main__":
    # Run the benchmarks
    print("Starting Taskra model performance benchmarks...")
    runner = run_core_benchmarks()
    
    # Only run memory benchmark if explicitly requested
    if len(sys.argv) > 1 and sys.argv[1] == '--with-memory':
        mem_results = run_memory_benchmark()
