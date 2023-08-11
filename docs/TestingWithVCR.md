# Testing the JiraClient with VCR.py

This document explains how we test the `JiraClient` class and related API services using VCR.py for reliable, repeatable integration tests.

## Overview

Testing API interactions presents several challenges:
- External dependencies on the Jira server
- Authentication requirements
- Network reliability issues
- Rate limiting concerns
- Maintaining test data consistency

To address these challenges, we use VCR.py, which records HTTP interactions and replays them in subsequent test runs, making our tests:
- Fast (no actual HTTP requests after initial recording)
- Reliable (not affected by network or server issues)
- Deterministic (same results every time)
- Offline-capable (tests run without internet access)

## Setup

### 1. Installation

VCR.py is included in our dev dependencies. You can install it with:

```bash
poetry add pytest-vcr --group dev
```

### 2. Configuration

Our VCR configuration is defined in `tests/integration/conftest.py`:

```python
vcr = VCR(
    cassette_library_dir='tests/fixtures/cassettes',  # Where recordings are stored
    filter_headers=['Authorization'],                 # Remove sensitive headers
    record_mode='once'                               # Record once, then replay
)

@pytest.fixture
def vcr_config():
    """VCR configuration."""
    return {
        'filter_headers': ['Authorization'],
        'record_mode': 'once',
    }
```

### 3. Directory Structure

```
tests/
└── fixtures/
    └── cassettes/           # Recorded HTTP interactions
        ├── test_get_issue.yaml
        ├── test_list_projects.yaml
        └── ...
```

## Writing Tests with VCR

### Basic Example

To test the `JiraClient` using VCR:

```python
import pytest

@pytest.mark.vcr()  # This decorator enables VCR for this test
def test_get_issue(mock_env_vars):
    """Test retrieving an issue."""
    from taskra.api.client import get_client
    
    client = get_client()
    response = client.get(f"issue/TEST-1")
    
    assert response["key"] == "TEST-1"
    assert "fields" in response
```

The first time this test runs:
1. It makes a real HTTP request to the Jira API
2. VCR records the request and response
3. The recording is saved to a YAML file in `tests/fixtures/cassettes/`

On subsequent runs:
1. VCR intercepts the HTTP request
2. It matches the request against the recording
3. VCR returns the recorded response without making an actual HTTP request

### Testing Services

When testing services that use the client:

```python
@pytest.mark.vcr()
def test_projects_service(mock_env_vars):
    """Test ProjectsService with VCR."""
    from taskra.api.client import get_client
    from taskra.api.services.projects import ProjectsService
    
    client = get_client()
    service = ProjectsService(client)
    projects = service.list_projects()
    
    assert len(projects) > 0
    assert "key" in projects[0]
```

## Initial Recording Setup

To create the initial recordings, you need valid Jira credentials:

1. Set required environment variables:
   ```bash
   export JIRA_BASE_URL="https://your-domain.atlassian.net"
   export JIRA_EMAIL="your-email@example.com"
   export JIRA_API_TOKEN="your-api-token"
   ```

2. Run the tests to generate cassettes:
   ```bash
   pytest tests/unit/api/test_client.py -v
   ```

3. Commit the generated cassettes to version control (sensitive data is filtered out)

## Best Practices

### 1. Filter Sensitive Information

Always filter out sensitive information from recordings:

```python
vcr = VCR(
    # ...
    filter_headers=['Authorization', 'Cookie'],
    filter_post_data_parameters=['password', 'token'],
)
```

### 2. Use Descriptive Cassette Names

Specify a cassette name to make the recordings more organized:

```python
@pytest.mark.vcr(cassette_name="jira_get_project_details")
def test_get_project():
    # ...
```

### 3. Re-record When Needed

Delete cassettes and re-record when:
- The API changes significantly
- Your test expectations change
- The recorded data is outdated

```bash
# Remove specific cassette
rm tests/fixtures/cassettes/test_get_issue.yaml

# Remove all cassettes
rm tests/fixtures/cassettes/*.yaml
```

### 4. Custom Matchers

For advanced cases where default request matching isn't sufficient:

```python
vcr = VCR(
    # ...
    match_on=['method', 'scheme', 'host', 'path', 'query'],
)
```

### 5. Control When to Record

Use different record modes as needed:

- `once`: Record if no cassette exists (default)
- `new_episodes`: Record new interactions not in the cassette
- `all`: Always re-record
- `none`: Never record, only replay (fails if no cassette)

```python
@pytest.mark.vcr(record_mode='new_episodes')
def test_with_new_episodes():
    # ...
```

## Debugging VCR Issues

### 1. Inspect Cassettes

Cassettes are YAML files you can inspect:

```yaml
interactions:
- request:
    body: null
    headers: 
      Accept: [application/json]
      Content-Type: [application/json]
    method: GET
    uri: https://example.atlassian.net/rest/api/3/issue/TEST-1
  response:
    body: {...}
    headers: {...}
    status: {code: 200, message: OK}
```

### 2. Enable Debug Mode

Add debug logging to see what VCR is doing:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('vcr').setLevel(logging.DEBUG)
```

### 3. Force Re-recording

To force re-recording of cassettes without deleting files:

```bash
VCR_RECORD_MODE=all pytest tests/unit/api/test_client.py
```

## Example Test Cases

### Testing JiraClient Directly

```python
@pytest.mark.vcr()
def test_client_get_request():
    """Test a direct GET request using the client."""
    client = get_client()
    response = client.get("project/search")
    
    assert response["total"] >= 0
    assert "values" in response
```

### Testing Error Handling

```python
@pytest.mark.vcr()
def test_client_error_handling():
    """Test client handles API errors correctly."""
    client = get_client()
    
    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        client.get("invalid/endpoint")
    
    assert excinfo.value.response.status_code == 404
```

### Testing with Query Parameters

```python
@pytest.mark.vcr()
def test_client_with_params():
    """Test client with query parameters."""
    client = get_client()
    response = client.get("project/search", params={"maxResults": 2})
    
    assert len(response["values"]) <= 2
```

## Understanding Test Fixtures in Pytest

### What Are Fixtures?

Fixtures in pytest are functions that provide a fixed baseline for tests. They're designed to:
- Set up test prerequisites (like test data, connections, or state)
- Provide reusable components to multiple tests
- Manage cleanup after tests complete

In Taskra, fixtures handle several important testing concerns:

1. **Environment Setup**: Creating controlled environments for tests
2. **Test Data**: Providing consistent data to test against
3. **Mock Objects**: Creating substitutes for external dependencies
4. **Resource Management**: Managing resources that need cleanup

### How Fixtures Work

Fixtures are declared using the `@pytest.fixture` decorator:

```python
@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing."""
    with patch.dict(os.environ, {
        "JIRA_BASE_URL": "https://example.atlassian.net",
        "JIRA_API_TOKEN": "dummy-token",
        "JIRA_EMAIL": "test@example.com"
    }):
        yield  # This is where tests run
        # Any cleanup happens after the yield
```

Tests can then use these fixtures by including them as function parameters:

```python
def test_client_initialization(mock_env_vars):
    """Test client is properly initialized from environment variables."""
    client = get_client()
    assert client.base_url == "https://example.atlassian.net/rest/api/3/"
```

### Key Fixture Types in Taskra

#### 1. Environment Configuration Fixtures

These fixtures set up the test environment with controlled values:

```python
@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing."""
    with patch.dict(os.environ, {
        "JIRA_BASE_URL": "https://example.atlassian.net",
        "JIRA_API_TOKEN": "dummy-token",
        "JIRA_EMAIL": "test@example.com"
    }):
        yield
```

#### 2. Test Data Fixtures

These provide consistent test data across tests:

```python
@pytest.fixture
def test_issue_key():
    """Returns a test issue key from environment or a default."""
    return os.environ.get('TEST_ISSUE_KEY', 'TEST-1')
```

#### 3. VCR Configuration Fixtures

These configure the VCR library for recording and replaying HTTP interactions:

```python
@pytest.fixture
def vcr_config():
    """VCR configuration."""
    return {
        'filter_headers': ['Authorization'],
        'record_mode': 'once',
    }
```

#### 4. Tool/Helper Fixtures

These provide testing tools to multiple tests:

```python
@pytest.fixture
def runner():
    """Set up CLI test runner."""
    return CliRunner()
```

### Fixture Scopes

Fixtures can have different scopes that determine their lifetime:

- `function`: Created once per test function (default)
- `class`: Created once per test class
- `module`: Created once per test module
- `session`: Created once per test session

```python
@pytest.fixture(scope="module")
def expensive_resource():
    # Setup code
    resource = create_expensive_resource()
    yield resource
    # Teardown code
    resource.cleanup()
```

### Fixture Location and Sharing

Fixtures in Taskra are organized in several locations:

1. **Test-specific fixtures**: Defined in the test file where they're used
2. **Shared fixtures**: In `conftest.py` files at various levels:
   - `/tests/conftest.py`: Global fixtures for all tests
   - `/tests/unit/conftest.py`: Shared by all unit tests
   - `/tests/integration/conftest.py`: Shared by integration tests

Pytest automatically discovers and makes available fixtures from all `conftest.py` files in the parent directories of a test.

### Best Practices for Fixtures

1. **Keep fixtures focused**: Each fixture should do one thing well
2. **Use appropriate scopes**: Don't use wider scopes than necessary
3. **Clean up resources**: Use yield for proper teardown
4. **Document fixtures**: Add docstrings explaining what they do
5. **Parametrize when needed**: Use `@pytest.mark.parametrize` for data-driven tests

### Example: Mock Service Fixture

```python
@pytest.fixture
def mock_issues_service():
    """Create a mock IssuesService for testing."""
    mock_service = MagicMock(spec=IssuesService)
    mock_service.get_issue.return_value = {
        "key": "TEST-1",
        "fields": {"summary": "Test Issue"}
    }
    return mock_service
```

## VCR vs. Fixtures: Why We Need Both

While both VCR.py and pytest fixtures help with test data, they serve different purposes and complement each other rather than being redundant:

### Different Responsibilities

1. **VCR.py** is specifically for recording and replaying HTTP interactions. It:
   - Records real API calls and their responses
   - Replays those responses instead of making network requests
   - Focuses solely on HTTP-level interactions

2. **Pytest Fixtures** have a broader scope. They:
   - Set up any kind of test prerequisites (not just HTTP responses)
   - Manage test dependencies and state
   - Create objects needed by tests
   - Handle test teardown and cleanup

### How They Work Together

In the Taskra project, we use both technologies together:

1. **Fixtures provide the test setup**:
   ```python
   @pytest.fixture
   def mock_env_vars():
       """Set up environment variables for testing."""
       with patch.dict(os.environ, {
           "JIRA_BASE_URL": "https://example.atlassian.net",
           "JIRA_API_TOKEN": "dummy-token",
           "JIRA_EMAIL": "test@example.com"
       }):
           yield
   ```

2. **VCR records/replays the HTTP interactions** that occur during the test:
   ```python
   @pytest.mark.vcr()
   def test_get_projects(mock_env_vars):
       client = get_client()
       projects = client.get("project/search")
       assert "values" in projects
   ```

### Key Differences

| Aspect | VCR.py | Pytest Fixtures |
|--------|--------|-----------------|
| **Purpose** | Record/replay HTTP interactions | Set up and tear down test environment |
| **Scope** | Network requests only | Any test prerequisite |
| **Persistence** | Writes to YAML files | In-memory during test run |
| **Configuration** | HTTP-specific (headers, query params) | Any Python object or environment |
| **Usage** | Via decorator `@pytest.mark.vcr()` | As function parameters |

### Examples Where Fixtures Are Essential

1. **Environment Setup**:  
   VCR can't set up environment variables or application configuration.
   ```python
   @pytest.fixture
   def test_config():
       """Provide test configuration."""
       return {"timeout": 5, "retry_attempts": 2}
   ```

2. **Object Creation**:  
   VCR doesn't create application objects.
   ```python
   @pytest.fixture
   def client():
       """Create a pre-configured client."""
       return JiraClient("https://example.com", {"token": "dummy"})
   ```

3. **Mock Services**:  
   For unit tests, we need mocks that aren't based on recorded HTTP.
   ```python
   @pytest.fixture
   def mock_service():
       """Create a mock service with predetermined responses."""
       service = MagicMock(spec=IssuesService)
       service.get_issue.return_value = {"key": "TEST-1"}
       return service
   ```

4. **Custom Test Data**:  
   Programmatically generate test data beyond what's in HTTP responses.
   ```python
   @pytest.fixture
   def sample_issues():
       """Generate sample issue data."""
       return [{"key": f"TEST-{i}", "summary": f"Test {i}"} for i in range(1, 5)]
   ```

5. **Test Resources**:  
   Manage resources that need proper cleanup.
   ```python
   @pytest.fixture
   def temp_directory():
       """Create a temporary directory for test files."""
       dir_path = tempfile.mkdtemp()
       yield dir_path
       shutil.rmtree(dir_path)  # Clean up after test
   ```

### When to Use Each

- **Use VCR.py when**: You need to test code that directly interacts with the API without making real HTTP calls.
- **Use fixtures when**: You need to set up the test environment, create objects, or provide test data.
- **Use both together when**: You're testing code that needs both environment setup and API interaction.

The combination of fixtures and VCR.py creates a powerful testing approach that is:
- Fast (VCR eliminates network latency)
- Flexible (fixtures provide any test setup needed)
- Maintainable (separation of concerns between HTTP recording and test setup)
- Reliable (consistent test environment and responses)

## Conclusion

Using VCR.py provides a robust way to test our JiraClient and service classes without dependency on a live Jira instance. This approach ensures:

- Tests are fast and reliable
- Real HTTP interactions are correctly simulated
- No authentication concerns in CI/CD pipelines
- Tests can be run offline
- We don't hit API rate limits

When making significant changes to the client code or when the Jira API changes, remember to re-record the cassettes to ensure your tests reflect current behavior.
