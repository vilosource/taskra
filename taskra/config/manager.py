"""Configuration manager for Taskra."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Configuration manager for Taskra.

    This class is responsible for managing the configuration files used by Taskra. It provides methods to read, write, and update configuration files, ensuring that the configuration directory and files are properly handled. The configuration files store settings such as user accounts, application preferences, and other customizable options.
    """
    
    def __init__(self, config_dir: Optional[str] = None, config_file: str = "config.json", debug: bool = False):
        """
        Initialize the configuration manager.

        Args:
            config_dir: Directory to store configuration (default: ~/.taskra)
            config_file: Name of the configuration file
            debug: Enable debug output for troubleshooting and development purposes
        """
        self.debug = debug
        
        if config_dir is None:
            self.config_dir = os.path.expanduser("~/.taskra")
        else:
            self.config_dir = config_dir
            
        self.config_path = os.path.join(self.config_dir, config_file)
        
        if self.debug:
            print(f"DEBUG: ConfigManager initialized with dir: {self.config_dir}, file: {self.config_path}")
            
        self._ensure_config_dir()
    
    def _ensure_config_dir(self) -> None:
        """Create the configuration directory if it doesn't exist."""
        if not os.path.exists(self.config_dir):
            if self.debug:
                print(f"DEBUG: Creating config directory: {self.config_dir}")
            os.makedirs(self.config_dir, exist_ok=True)
        elif self.debug:
            print(f"DEBUG: Config directory already exists: {self.config_dir}")
    
    def read_config(self) -> Dict[str, Any]:
        """
        Read configuration from file.

        This method reads the configuration file and returns its contents as a dictionary. If the file does not exist or is corrupted, a default configuration is created and returned.

        Returns:
            Configuration dictionary
        """
        if not os.path.exists(self.config_path):
            if self.debug:
                print(f"DEBUG: Config file does not exist: {self.config_path}. Creating default config.")
            return self._create_default_config()
            
        try:
            if self.debug:
                print(f"DEBUG: Reading config from: {self.config_path}")
            with open(self.config_path, "r") as f:
                config = json.load(f)
                if self.debug:
                    print(f"DEBUG: Successfully read config: {config}")
                return config
        except (json.JSONDecodeError, FileNotFoundError) as e:
            if self.debug:
                print(f"DEBUG: Error reading config: {str(e)}. Creating default config.")
            # If the file is corrupted or missing, create a new default config
            return self._create_default_config()
    
    def write_config(self, config: Dict[str, Any]) -> None:
        """
        Write configuration to file.

        This method writes the given configuration dictionary to the configuration file. It ensures that the configuration directory exists before writing and uses a temporary file to avoid partial writes.

        Args:
            config: Configuration dictionary
        """
        # Ensure directory exists before writing
        self._ensure_config_dir()
        
        if self.debug:
            print(f"DEBUG: Writing config to: {self.config_path}")
            print(f"DEBUG: Config content: {config}")
        
        try:
            # First write to a temporary file, then move it to avoid partial writes
            temp_path = f"{self.config_path}.tmp"
            with open(temp_path, "w") as f:
                json.dump(config, f, indent=2)
            
            # Replace the original file with the new one
            os.replace(temp_path, self.config_path)
            
            if self.debug:
                print(f"DEBUG: Successfully wrote config to: {self.config_path}")
                print(f"DEBUG: File exists after write: {os.path.exists(self.config_path)}")
                print(f"DEBUG: File size: {os.path.getsize(self.config_path)} bytes")
        except Exception as e:
            if self.debug:
                print(f"DEBUG: Error writing config: {str(e)}")
            raise
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create a default configuration.

        This method generates a default configuration dictionary with predefined settings and writes it to the configuration file.

        Returns:
            Default configuration dictionary
        """
        default_config = {
            "default_account": None,
            "accounts": {},
            "settings": {
                "timeout": 30,
                "cache_ttl": 300,
            }
        }
        
        self.write_config(default_config)
        return default_config
    
    def update_config(self, update_func) -> Dict[str, Any]:
        """
        Update configuration using a function.

        This method allows updating the configuration by applying a user-provided function to the current configuration. The function should take the current configuration as input and return the updated configuration.

        Args:
            update_func: Function that takes the current config and returns the updated config
            
        Returns:
            Updated configuration dictionary
        """
        if self.debug:
            print(f"DEBUG: Updating config using function: {update_func.__name__ if hasattr(update_func, '__name__') else 'anonymous'}")
        
        config = self.read_config()
        updated_config = update_func(config)
        
        if self.debug:
            print(f"DEBUG: Original config: {config}")
            print(f"DEBUG: Updated config: {updated_config}")
        
        self.write_config(updated_config)
        return updated_config


# Global instance
config_manager = ConfigManager()

# Function to enable debug mode for the global instance
def enable_debug_mode():
    """
    Enable debug mode for the global ConfigManager instance.

    This function sets the debug flag to True for the global instance of ConfigManager, allowing detailed debug output to be printed to the console. Useful for troubleshooting configuration-related issues.
    """
    global config_manager
    config_manager.debug = True
    print("DEBUG: Enabled debug mode for global ConfigManager")

def get_auth_details():
    """
    Get authentication details from environment or config.

    This function retrieves authentication details such as the base URL, email, and API token from environment variables. These details are typically used for connecting to external services like JIRA.

    Returns:
        A dictionary containing the authentication details.
    """
    import os
    return {
        'base_url': os.environ.get('JIRA_BASE_URL'),
        'email': os.environ.get('JIRA_EMAIL'),
        'token': os.environ.get('JIRA_API_TOKEN')
    }