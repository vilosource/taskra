import timeit
import statistics
from datetime import datetime

from taskra.api.models.worklog import Worklog, Author

def create_worklog_dict():
    """Create a worklog using dictionaries."""
    return {
        "id": "123",
        "self": "https://example.com/worklog/123",
        "author": {
            "accountId": "user123",
            "displayName": "Test User"
        },
        "timeSpent": "1h",
        "timeSpentSeconds": 3600,
        "started": datetime.now(),
        "created": datetime.now(),
        "updated": datetime.now()
    }

def create_worklog_model():
    """Create a worklog using models."""
    author = Author(
        accountId="user123",
        displayName="Test User"
    )
    return Worklog(
        id="123",
        self_url="https://example.com/worklog/123",
        author=author,
        timeSpent="1h",
        timeSpentSeconds=3600,
        started=datetime.now(),
        created=datetime.now(),
        updated=datetime.now()
    )

def access_dict(worklog):
    """Access worklog fields using dictionary syntax."""
    _ = worklog["id"]
    _ = worklog["timeSpent"]
    _ = worklog["author"]["displayName"]
    return _

def access_model(worklog):
    """Access worklog fields using model attributes."""
    _ = worklog.id
    _ = worklog.time_spent
    _ = worklog.author.display_name
    return _

def run_benchmark(func, setup, number=10000):
    """Run a benchmark for the given function."""
    times = timeit.repeat(
        func,
        setup=setup,
        number=number,
        repeat=5
    )
    return {
        'min': min(times),
        'max': max(times),
        'mean': statistics.mean(times),
        'median': statistics.median(times)
    }

if __name__ == "__main__":
    # Benchmark creation
    dict_create_results = run_benchmark(
        "create_worklog_dict()",
        "from __main__ import create_worklog_dict"
    )
    model_create_results = run_benchmark(
        "create_worklog_model()",
        "from __main__ import create_worklog_model"
    )
    
    # Benchmark field access
    dict_access_results = run_benchmark(
        "access_dict(worklog)",
        "from __main__ import create_worklog_dict, access_dict; worklog = create_worklog_dict()"
    )
    model_access_results = run_benchmark(
        "access_model(worklog)",
        "from __main__ import create_worklog_model, access_model; worklog = create_worklog_model()"
    )
    
    print("Creation benchmarks (lower is better):")
    print(f"Dictionary: {dict_create_results['median']:.6f} seconds")
    print(f"Model:      {model_create_results['median']:.6f} seconds")
    print(f"Overhead:   {(model_create_results['median'] / dict_create_results['median'] - 1) * 100:.2f}%")
    
    print("\nAccess benchmarks (lower is better):")
    print(f"Dictionary: {dict_access_results['median']:.6f} seconds")
    print(f"Model:      {model_access_results['median']:.6f} seconds")
    print(f"Overhead:   {(model_access_results['median'] / dict_access_results['median'] - 1) * 100:.2f}%")
