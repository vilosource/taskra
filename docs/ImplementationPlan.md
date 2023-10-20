# Taskra: Implementation Plan

This document outlines the comprehensive implementation plan for Taskra, covering configuration management, testing strategy, and development workflow.

## 1. Configuration Management Implementation

### 1.1 Overview

The configuration manager handles reading, writing, and updating configuration data for Taskra, including account management. Our implementation provides:

- Storage and management of multiple Jira account credentials
- Account switching capability
- Environment variable overrides
- Secure credential handling

### 1.2 Core Components

#### ConfigManager Class

A centralized class for handling configuration file operations:

```python
class ConfigManager:
    """Configuration manager for Taskra."""
    
    def __init__(self, config_dir=None, config_file="config.json", debug=False):
        """Initialize with configurable location."""
        # ...existing code...
    
    def read_config(self):
        """Read configuration from file with fallback to default."""
        # ...existing code...
    
    def write_config(self, config):
        """Write configuration to file safely."""
        # ...existing code...
        
    def update_config(self, update_func):
        """Update configuration using a transaction-like function."""
        # ...existing code...
```

#### Account Management Module

Functions for managing Jira accounts:

```python
# Account operations
def list_accounts() -> List[Dict[str, Any]]:
    """List all configured accounts."""
    # ...existing code...

def add_account(url, email, token, name=None, debug=False) -> Tuple[bool, str]:
    """Add a new account, optionally setting as default."""
    # ...existing code...

def remove_account(name) -> Tuple[bool, str]:
    """Remove an account, updating default if needed."""
    # ...existing code...
```

### 1.3 Configuration Data Structure

```json
{
  "default_account": "mycompany",
  "accounts": {
    "mycompany": {
      "url": "https://mycompany.atlassian.net",
      "email": "user@example.com",
      "token": "your-api-token" 
    }
  },
  "settings": {
    "timeout": 30,
    "cache_ttl": 300
  }
}
```

### 1.4 CLI Integration

Configure command group with subcommands:
- `taskra config list`: List all configured accounts
- `taskra config add`: Add a new Jira account
- `taskra config remove`: Remove an account
- `taskra config default`: Set the default account
- `taskra config current`: Show the currently active account

## 2. Testing Strategy

### 2.1 Testing Approach

Taskra follows a comprehensive testing strategy:

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Verify components work correctly together
- **End-to-end tests**: Test complete workflows (optional, using live API)
- **Mock-based testing**: Avoid dependencies on external services

### 2.2 Test Structure

Tests will be organized into two main categories:
1. **ConfigManager Tests**: Testing the low-level configuration file operations
2. **Account Management Tests**: Testing the higher-level account operations

### 2.3 Implementation Plan

#### 2.3.1 Set Up Test Fixtures

```python
@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for test configurations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def test_config_manager(temp_config_dir):
    """Create a ConfigManager instance using a temporary directory."""
    return ConfigManager(config_dir=temp_config_dir)

@pytest.fixture
def mock_jira_client():
    """Create a mock JiraClient for testing."""
    return Mock(spec=JiraClient)

@pytest.fixture
def mock_user_service(mock_jira_client):
    """Create a mock UserService for testing."""
    mock_service = Mock(spec=UserService)
    mock_service.validate_credentials.return_value = True
    return mock_service
```

#### 2.3.2 ConfigManager Tests

##### Creation Tests
- Test that initialization creates correct paths
- Test that default config is created when file doesn't exist

```python
def test_config_manager_initialization(temp_config_dir):
    """Test that ConfigManager initializes correctly."""
    manager = ConfigManager(config_dir=temp_config_dir)
    assert os.path.isdir(temp_config_dir)
    assert manager.config_path == os.path.join(temp_config_dir, "config.json")

def test_create_default_config(test_config_manager):
    """Test that default configuration is created correctly."""
    config = test_config_manager._create_default_config()
    assert config["default_account"] is None
    assert "accounts" in config
    assert "settings" in config
```

##### Read Tests
- Test reading valid config
- Test handling corrupt JSON
- Test reading non-existent file

```python
def test_read_valid_config(test_config_manager):
    """Test reading a valid configuration file."""
    # Create a test configuration
    test_config = {"default_account": "test", "accounts": {"test": {}}}
    test_config_manager.write_config(test_config)
    
    # Read it back
    config = test_config_manager.read_config()
    assert config["default_account"] == "test"

def test_read_corrupt_config(test_config_manager):
    """Test reading a corrupt configuration file."""
    # Create a corrupt JSON file
    with open(test_config_manager.config_path, "w") as f:
        f.write("{not valid json")
    
    # Should fall back to default config
    config = test_config_manager.read_config()
    assert "default_account" in config
    assert "accounts" in config
```

##### Write Tests
- Test writing new config
- Test overwriting existing config

```python
def test_write_new_config(test_config_manager):
    """Test writing a new configuration file."""
    test_config = {"test": "value"}
    test_config_manager.write_config(test_config)
    
    # Verify file exists and contains correct data
    assert os.path.exists(test_config_manager.config_path)
    with open(test_config_manager.config_path, "r") as f:
        data = json.load(f)
    assert data == test_config
```

##### Update Tests
- Test updating config with a function
- Test transaction safety (should roll back on error)

```python
def test_update_config(test_config_manager):
    """Test updating configuration with a function."""
    # Start with initial config
    initial_config = {"value": 1}
    test_config_manager.write_config(initial_config)
    
    # Update with function
    def updater(config):
        config["value"] = 2
        config["new_key"] = "new_value"
        return config
    
    updated_config = test_config_manager.update_config(updater)
    
    assert updated_config["value"] == 2
    assert updated_config["new_key"] == "new_value"
```

#### 2.3.3 Account Management Tests

##### List Accounts Tests
- Test empty account list
- Test listing multiple accounts
- Test identifying default account

```python
def test_list_accounts_empty(monkeypatch):
    """Test listing accounts when none exist."""
    # Mock config_manager.read_config to return empty accounts
    monkeypatch.setattr(config_manager, "read_config", 
                        lambda: {"accounts": {}, "default_account": None})
    
    accounts = list_accounts()
    assert len(accounts) == 0

def test_list_accounts_with_default(monkeypatch):
    """Test listing accounts with a default account."""
    # Mock config with accounts including a default
    mock_config = {
        "accounts": {
            "account1": {"url": "https://a1.atlassian.net", "email": "a1@example.com"},
            "account2": {"url": "https://a2.atlassian.net", "email": "a2@example.com"}
        },
        "default_account": "account1"
    }
    monkeypatch.setattr(config_manager, "read_config", lambda: mock_config)
    
    accounts = list_accounts()
    assert len(accounts) == 2
    # Find the default account
    default_account = next(a for a in accounts if a["is_default"])
    assert default_account["name"] == "account1"
```

##### Add Account Tests
- Test adding first account (becomes default)
- Test adding additional accounts
- Test validation of credentials
- Test URL normalization
- Test deriving name from URL

```python
def test_add_first_account(monkeypatch, mock_user_service):
    """Test adding the first account (should become default)."""
    # Mock empty config
    monkeypatch.setattr(config_manager, "read_config", 
                        lambda: {"accounts": {}, "default_account": None})
    
    # Mock update_config to capture the update function
    updated_config = {}
    def mock_update_config(update_func):
        nonlocal updated_config
        updated_config = update_func({"accounts": {}, "default_account": None})
        return updated_config
    monkeypatch.setattr(config_manager, "update_config", mock_update_config)
    
    # Mock JiraClient and UserService
    monkeypatch.setattr("taskra.config.account.JiraClient", lambda *args, **kwargs: None)
    monkeypatch.setattr("taskra.config.account.UserService", lambda *args: mock_user_service)
    
    success, _ = add_account("https://test.atlassian.net", "test@example.com", "api-token")
    
    assert success
    assert "test" in updated_config["accounts"]
    assert updated_config["default_account"] == "test"
```

##### Current Account Tests
- Test getting default account
- Test environment variable override
- Test behavior with no accounts

```python
def test_get_current_account_default(monkeypatch):
    """Test getting the default account."""
    # Mock config with default account
    mock_config = {
        "accounts": {
            "account1": {"url": "https://a1.atlassian.net", "email": "a1@example.com"},
            "account2": {"url": "https://a2.atlassian.net", "email": "a2@example.com"}
        },
        "default_account": "account1"
    }
    monkeypatch.setattr(config_manager, "read_config", lambda: mock_config)
    monkeypatch.delenv("TASKRA_ACCOUNT", raising=False)  # Ensure env var is not set
    
    account = get_current_account()
    assert account["name"] == "account1"
    assert account["url"] == "https://a1.atlassian.net"

def test_get_current_account_env_override(monkeypatch):
    """Test getting account from environment variable override."""
    # Mock config with default account
    mock_config = {
        "accounts": {
            "account1": {"url": "https://a1.atlassian.net", "email": "a1@example.com"},
            "account2": {"url": "https://a2.atlassian.net", "email": "a2@example.com"}
        },
        "default_account": "account1"
    }
    monkeypatch.setattr(config_manager, "read_config", lambda: mock_config)
    monkeypatch.setenv("TASKRA_ACCOUNT", "account2")
    
    account = get_current_account()
    assert account["name"] == "account2"  # Should use account2 from env var
```

##### Remove Account Tests
- Test removing existing account
- Test removing default account (should pick new default)
- Test removing last account

```python
def test_remove_account_standard(monkeypatch):
    """Test removing a non-default account."""
    # Mock config with multiple accounts
    mock_config = {
        "accounts": {
            "account1": {"url": "https://a1.atlassian.net"},
            "account2": {"url": "https://a2.atlassian.net"}
        },
        "default_account": "account1"
    }
    
    # Capture the updated configuration
    updated_config = {}
    def mock_update_config(update_func):
        nonlocal updated_config
        updated_config = update_func(mock_config)
        return updated_config
    
    monkeypatch.setattr(config_manager, "update_config", mock_update_config)
    
    remove_account("account2")
    
    assert "account2" not in updated_config["accounts"]
    assert "account1" in updated_config["accounts"]
    assert updated_config["default_account"] == "account1"  # Unchanged
```

##### Default Account Tests
- Test setting default account
- Test error when setting non-existent account

```python
def test_set_default_account(monkeypatch):
    """Test setting the default account."""
    # Mock config with multiple accounts
    mock_config = {
        "accounts": {
            "account1": {"url": "https://a1.atlassian.net"},
            "account2": {"url": "https://a2.atlassian.net"}
        },
        "default_account": "account1"
    }
    
    monkeypatch.setattr(config_manager, "read_config", lambda: mock_config)
    
    # Capture the updated configuration
    updated_config = {}
    def mock_update_config(update_func):
        nonlocal updated_config
        updated_config = update_func(mock_config)
        return updated_config
    
    monkeypatch.setattr(config_manager, "update_config", mock_update_config)
    
    success, _ = set_default_account("account2")
    
    assert success
    assert updated_config["default_account"] == "account2"
```

#### 2.3.4 Integration Tests

Create integration tests that verify the entire flow:

```python
def test_account_management_workflow(temp_config_dir, monkeypatch):
    """Test the entire account management workflow."""
    # Set up a config manager with the temp directory
    manager = ConfigManager(config_dir=temp_config_dir)
    monkeypatch.setattr("taskra.config.account.config_manager", manager)
    
    # Mock JiraClient and UserService for validation
    monkeypatch.setattr("taskra.config.account.JiraClient", lambda *args, **kwargs: None)
    mock_user_service = Mock(spec=UserService)
    mock_user_service.validate_credentials.return_value = True
    monkeypatch.setattr("taskra.config.account.UserService", lambda *args: mock_user_service)
    
    # 1. Add first account
    add_account("https://first.atlassian.net", "first@example.com", "token1")
    
    # 2. Add second account
    add_account("https://second.atlassian.net", "second@example.com", "token2")
    
    # 3. List accounts and verify both exist
    accounts = list_accounts()
    assert len(accounts) == 2
    assert any(a["name"] == "first" for a in accounts)
    assert any(a["name"] == "second" for a in accounts)
    
    # 4. Check default account is the first one added
    account = get_current_account()
    assert account["name"] == "first"
    
    # 5. Change default account
    set_default_account("second")
    account = get_current_account()
    assert account["name"] == "second"
    
    # 6. Remove an account
    remove_account("first")
    accounts = list_accounts()
    assert len(accounts) == 1
    assert accounts[0]["name"] == "second"
```

