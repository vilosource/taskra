"""Tests for the ConfigManager class."""

import os
import json
import pytest
from taskra.config.manager import ConfigManager


class TestConfigManager:
    """Tests for the ConfigManager class."""
    
    def test_config_manager_initialization(self, temp_config_dir):
        """Test that ConfigManager initializes correctly."""
        manager = ConfigManager(config_dir=temp_config_dir)
        assert os.path.isdir(temp_config_dir)
        assert manager.config_path == os.path.join(temp_config_dir, "config.json")

    def test_create_default_config(self, test_config_manager):
        """Test that default configuration is created correctly."""
        config = test_config_manager._create_default_config()
        assert config["default_account"] is None
        assert "accounts" in config
        assert "settings" in config
        assert config["settings"]["timeout"] == 30
        assert config["settings"]["cache_ttl"] == 300

    def test_read_valid_config(self, test_config_manager):
        """Test reading a valid configuration file."""
        # Create a test configuration
        test_config = {"default_account": "test", "accounts": {"test": {}}}
        test_config_manager.write_config(test_config)
        
        # Read it back
        config = test_config_manager.read_config()
        assert config["default_account"] == "test"
        assert "test" in config["accounts"]

    def test_read_corrupt_config(self, test_config_manager):
        """Test reading a corrupt configuration file."""
        # Create a corrupt JSON file
        with open(test_config_manager.config_path, "w") as f:
            f.write("{not valid json")
        
        # Should fall back to default config
        config = test_config_manager.read_config()
        assert "default_account" in config
        assert "accounts" in config
        assert config["default_account"] is None

    def test_read_nonexistent_config(self, test_config_manager):
        """Test reading a non-existent configuration file."""
        # Make sure the file doesn't exist
        if os.path.exists(test_config_manager.config_path):
            os.remove(test_config_manager.config_path)
            
        # Should create a default config
        config = test_config_manager.read_config()
        assert "default_account" in config
        assert "accounts" in config
        assert config["settings"]["timeout"] == 30

    def test_write_new_config(self, test_config_manager):
        """Test writing a new configuration file."""
        test_config = {"test": "value"}
        test_config_manager.write_config(test_config)
        
        # Verify file exists and contains correct data
        assert os.path.exists(test_config_manager.config_path)
        with open(test_config_manager.config_path, "r") as f:
            data = json.load(f)
        assert data == test_config

    def test_update_config(self, test_config_manager):
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
        
        # Verify changes were saved to file
        with open(test_config_manager.config_path, "r") as f:
            data = json.load(f)
        assert data["value"] == 2
        assert data["new_key"] == "new_value"

    def test_update_config_preserves_file(self, test_config_manager):
        """Test that update_config preserves the file if updater raises an exception."""
        # Start with initial config
        initial_config = {"key": "initial_value"}
        test_config_manager.write_config(initial_config)
        
        # Define an updater that raises an exception
        def failing_updater(config):
            config["key"] = "modified_value"
            raise ValueError("Test exception")
        
        # Call update_config with the failing updater
        with pytest.raises(ValueError):
            test_config_manager.update_config(failing_updater)
        
        # Verify file still contains original data
        config = test_config_manager.read_config()
        assert config["key"] == "initial_value"
