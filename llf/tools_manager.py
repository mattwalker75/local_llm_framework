"""
Tools Configuration Manager for Local LLM Framework.

This module manages tool system features and compatibility layers.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from llf.logging_config import get_logger

logger = get_logger(__name__)


class ToolsManager:
    """Manager for tool system configuration and features."""

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize ToolsManager.

        Args:
            registry_path: Path to tools_registry.json. If None, uses default location.
        """
        # Tools registry
        if registry_path is None:
            self.registry_path = Path(__file__).parent.parent / 'tools' / 'tools_registry.json'
        else:
            self.registry_path = Path(registry_path)

        self.registry = self._load_registry()
        self.session_overrides = {}  # Store CLI session overrides

    def _load_registry(self) -> Dict[str, Any]:
        """
        Load tools registry from tools_registry.json.

        Returns:
            Registry dictionary
        """
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    registry = json.load(f)
                    logger.info(f"Loaded tools registry from {self.registry_path}")
                    return registry
            except Exception as e:
                logger.error(f"Failed to load tools registry: {e}")
                return self._get_default_registry()
        else:
            logger.warning(f"Tools registry not found at {self.registry_path}, using defaults")
            return self._get_default_registry()

    def _get_default_registry(self) -> Dict[str, Any]:
        """Get default registry structure."""
        return {
            "version": "1.1",
            "last_updated": datetime.now().strftime('%Y-%m-%d'),
            "global_config": {
                "require_approval": False,
                "sensitive_operations": ["file_write", "file_delete", "command_exec"]
            },
            "tools": [
                {
                    "name": "xml_format",
                    "display_name": "XML Format Parser",
                    "description": "Parse XML-style function calls and convert to OpenAI JSON format",
                    "type": "postprocessor",
                    "enabled": False,
                    "directory": "xml_format",
                    "created_date": None,
                    "last_modified": None,
                    "metadata": {
                        "input_format": "XML",
                        "output_format": "JSON",
                        "use_case": "Model outputs XML instead of JSON tool calls",
                        "behavior": "postprocessor",
                        "activation": "automatic_on_pattern"
                    }
                }
            ],
            "metadata": {
                "description": "Registry of all available tools for the LLM Framework",
                "schema_version": "1.1"
            }
        }

    def _save_registry(self) -> bool:
        """Save registry to file."""
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

            # Update last_updated timestamp
            self.registry['last_updated'] = datetime.now().strftime('%Y-%m-%d')

            with open(self.registry_path, 'w') as f:
                json.dump(self.registry, f, indent=2)
            logger.info(f"Saved tools registry to {self.registry_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save tools registry: {e}")
            return False

    def _normalize_enabled_value(self, value) -> bool:
        """
        Normalize enabled value to boolean.

        Args:
            value: Can be bool, 'auto', 'true', 'false', True, False

        Returns:
            True if enabled or auto, False otherwise
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', 'auto']
        return False

    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a tool feature is enabled (loaded and available).

        This returns True for both 'auto' and true states.
        Checks session override first, then registry file.

        Args:
            feature_name: Name of the tool (e.g., 'xml_format')

        Returns:
            True if tool is enabled or auto (available for use)
        """
        # Check session override first
        if feature_name in self.session_overrides:
            return self._normalize_enabled_value(self.session_overrides[feature_name])

        # Fall back to registry
        tools = self.registry.get('tools', [])
        for tool in tools:
            if tool.get('name') == feature_name:
                return self._normalize_enabled_value(tool.get('enabled', False))

        return False

    def get_enabled_state(self, feature_name: str):
        """
        Get the raw enabled state (false, 'auto', or true).

        Args:
            feature_name: Name of the tool

        Returns:
            The enabled value: False, 'auto', or True
        """
        # Check session override first
        if feature_name in self.session_overrides:
            return self.session_overrides[feature_name]

        # Fall back to registry
        tools = self.registry.get('tools', [])
        for tool in tools:
            if tool.get('name') == feature_name:
                return tool.get('enabled', False)

        return False

    def should_load_at_init(self, feature_name: str) -> bool:
        """
        Check if tool should be loaded at initialization.

        Returns True for 'auto' and true states.

        Args:
            feature_name: Name of the tool

        Returns:
            True if tool should be loaded at runtime initialization
        """
        return self.is_feature_enabled(feature_name)

    def enable_feature(self, feature_name: str, session_only: bool = True) -> bool:
        """
        Enable a tool feature.

        Args:
            feature_name: Name of the tool to enable
            session_only: If True, only affects current session (override).
                         If False, saves to registry file.

        Returns:
            True if successful
        """
        if session_only:
            # Session override - doesn't modify registry file
            self.session_overrides[feature_name] = True
            logger.info(f"Session override: {feature_name} enabled (temporary)")
            return True
        else:
            # Persistent change to registry
            tools = self.registry.get('tools', [])
            tool_found = False

            for tool in tools:
                if tool.get('name') == feature_name:
                    tool['enabled'] = True
                    tool['last_modified'] = datetime.now().strftime('%Y-%m-%d')
                    tool_found = True
                    break

            if not tool_found:
                logger.error(f"Unknown tool: {feature_name}")
                return False

            return self._save_registry()

    def disable_feature(self, feature_name: str, session_only: bool = True) -> bool:
        """
        Disable a tool feature.

        Args:
            feature_name: Name of the tool to disable
            session_only: If True, only affects current session (override).
                         If False, saves to registry file.

        Returns:
            True if successful
        """
        if session_only:
            # Session override - doesn't modify registry file
            self.session_overrides[feature_name] = False
            logger.info(f"Session override: {feature_name} disabled (temporary)")
            return True
        else:
            # Persistent change to registry
            tools = self.registry.get('tools', [])
            tool_found = False

            for tool in tools:
                if tool.get('name') == feature_name:
                    tool['enabled'] = False
                    tool['last_modified'] = datetime.now().strftime('%Y-%m-%d')
                    tool_found = True
                    break

            if not tool_found:
                logger.error(f"Unknown tool: {feature_name}")
                return False

            return self._save_registry()

    def auto_feature(self, feature_name: str, session_only: bool = True) -> bool:
        """
        Set a tool feature to 'auto' mode (load at init, use when needed).

        Args:
            feature_name: Name of the tool to set to auto
            session_only: If True, only affects current session (override).
                         If False, saves to registry file.

        Returns:
            True if successful
        """
        if session_only:
            # Session override - doesn't modify registry file
            self.session_overrides[feature_name] = 'auto'
            logger.info(f"Session override: {feature_name} set to auto (temporary)")
            return True
        else:
            # Persistent change to registry
            tools = self.registry.get('tools', [])
            tool_found = False

            for tool in tools:
                if tool.get('name') == feature_name:
                    tool['enabled'] = 'auto'
                    tool['last_modified'] = datetime.now().strftime('%Y-%m-%d')
                    tool_found = True
                    break

            if not tool_found:
                logger.error(f"Unknown tool: {feature_name}")
                return False

            return self._save_registry()

    def reset_to_config(self, feature_name: str) -> bool:
        """
        Reset a tool to use the registry file setting (remove session override).

        This is what 'auto' means in CLI - use whatever is in registry.

        Args:
            feature_name: Name of the tool to reset

        Returns:
            True if successful
        """
        if feature_name in self.session_overrides:
            del self.session_overrides[feature_name]
            logger.info(f"Reset {feature_name} to registry file setting")

        return True

    def list_features(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all tools and their status (for backward compatibility with CLI).

        Returns:
            Dict of tool names to tool info in legacy format
        """
        features = {}
        tools = self.registry.get('tools', [])

        for tool in tools:
            name = tool.get('name')
            features[name] = {
                'enabled': tool.get('enabled', False),
                'description': tool.get('description', 'No description'),
                'note': tool.get('metadata', {}).get('use_case', ''),
                'supported_states': tool.get('metadata', {}).get('supported_states', [])
            }

        return features

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Get all tools from registry.

        Returns:
            List of tool dictionaries
        """
        return self.registry.get('tools', [])

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool info dictionary or None if not found
        """
        tools = self.registry.get('tools', [])
        for tool in tools:
            if tool.get('name') == tool_name:
                return tool
        return None

    def get_global_config(self, key: Optional[str] = None) -> Any:
        """
        Get global tool configuration.

        Args:
            key: Specific config key to retrieve. If None, returns entire config.

        Returns:
            Config value or entire config dict
        """
        global_config = self.registry.get('global_config', {})
        if key:
            return global_config.get(key)
        return global_config

    def set_global_config(self, key: str, value: Any) -> bool:
        """
        Set a global tool configuration value.

        Args:
            key: Config key to set
            value: Value to set

        Returns:
            True if successful
        """
        if 'global_config' not in self.registry:
            self.registry['global_config'] = {}

        self.registry['global_config'][key] = value
        return self._save_registry()

    def list_tools_by_type(self, tool_type: str) -> List[Dict[str, Any]]:
        """
        Get all tools of a specific type.

        Args:
            tool_type: Type of tools to list ('postprocessor', 'preprocessor', 'llm_invokable')

        Returns:
            List of tool dictionaries matching the type
        """
        tools = self.registry.get('tools', [])
        return [tool for tool in tools if tool.get('type') == tool_type]

    def get_enabled_llm_invokable_tools(self) -> List[Dict[str, Any]]:
        """
        Get all enabled LLM-invokable tools.

        Returns:
            List of enabled llm_invokable tool definitions
        """
        tools = self.list_tools_by_type('llm_invokable')
        enabled_tools = []

        for tool in tools:
            if self.is_feature_enabled(tool.get('name')):
                enabled_tools.append(tool)

        return enabled_tools

    def load_tool_module(self, tool_name: str):
        """
        Dynamically load a tool module.

        Args:
            tool_name: Name of the tool to load

        Returns:
            Loaded module or None if failed
        """
        tool_info = self.get_tool_info(tool_name)
        if not tool_info:
            logger.error(f"Tool '{tool_name}' not found in registry")
            return None

        directory = tool_info.get('directory')
        if not directory:
            logger.error(f"Tool '{tool_name}' has no directory specified")
            return None

        try:
            # Import the tool module dynamically
            import importlib
            module_path = f"tools.{directory}"
            module = importlib.import_module(module_path)
            logger.debug(f"Loaded tool module: {module_path}")
            return module
        except Exception as e:
            logger.error(f"Failed to load tool module '{tool_name}': {e}")
            return None

    def import_tool(self, tool_name: str) -> tuple[bool, str]:
        """
        Import a tool from its config.json into the registry.

        Args:
            tool_name: Name/directory of the tool to import

        Returns:
            Tuple of (success, message)
        """
        # Check if tool already exists in registry
        if self.get_tool_info(tool_name):
            return False, f"Tool '{tool_name}' already exists in registry. Use 'llf tool export' first if you want to re-import."

        # Look for config.json in tool directory
        tools_dir = Path(__file__).parent.parent / 'tools'
        tool_dir = tools_dir / tool_name
        config_path = tool_dir / 'config.json'

        if not config_path.exists():
            return False, f"Tool config not found at {config_path}"

        try:
            # Load tool config
            with open(config_path, 'r') as f:
                tool_config = json.load(f)

            # Validate required fields
            required_fields = ['name', 'type', 'directory']
            for field in required_fields:
                if field not in tool_config:
                    return False, f"Tool config missing required field: {field}"

            # Verify the tool name matches
            if tool_config['name'] != tool_name:
                return False, f"Tool config name '{tool_config['name']}' doesn't match directory '{tool_name}'"

            # Add to registry
            tools = self.registry.get('tools', [])
            tools.append(tool_config)
            self.registry['tools'] = tools

            # Save registry
            if self._save_registry():
                logger.info(f"Imported tool '{tool_name}' into registry")
                return True, f"Tool '{tool_name}' imported successfully"
            else:
                return False, "Failed to save registry"

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in config file: {e}"
        except Exception as e:
            return False, f"Failed to import tool: {e}"

    def export_tool(self, tool_name: str) -> tuple[bool, str]:
        """
        Export a tool from the registry (removes from registry but keeps files).

        Args:
            tool_name: Name of the tool to export

        Returns:
            Tuple of (success, message)
        """
        # Find tool in registry
        tools = self.registry.get('tools', [])
        tool_found = False
        tool_config = None

        for i, tool in enumerate(tools):
            if tool.get('name') == tool_name:
                tool_config = tool
                tools.pop(i)
                tool_found = True
                break

        if not tool_found:
            return False, f"Tool '{tool_name}' not found in registry"

        # Update registry (remove the tool)
        self.registry['tools'] = tools

        # Save registry
        if self._save_registry():
            logger.info(f"Exported tool '{tool_name}' from registry")
            return True, f"Tool '{tool_name}' exported successfully (files preserved for re-import)"
        else:
            return False, "Failed to save registry"

    def list_available_tools(self) -> List[str]:
        """
        List all tools that have config.json but are not in registry.

        Returns:
            List of tool directory names available for import
        """
        tools_dir = Path(__file__).parent.parent / 'tools'
        available = []

        if not tools_dir.exists():
            return available

        # Get all tools currently in registry
        registered_tools = {tool.get('name') for tool in self.registry.get('tools', [])}

        # Scan tools directory for subdirectories with config.json
        for item in tools_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                config_path = item / 'config.json'
                if config_path.exists() and item.name not in registered_tools:
                    available.append(item.name)

        return available

    def add_whitelist_pattern(self, tool_name: str, pattern: str) -> tuple[bool, str]:
        """
        Add a whitelist pattern to a tool's configuration.

        Args:
            tool_name: Name of the tool
            pattern: Whitelist pattern to add (glob or fully qualified path)

        Returns:
            Tuple of (success, message)
        """
        tool_info = self.get_tool_info(tool_name)
        if not tool_info:
            return False, f"Tool '{tool_name}' not found"

        # Ensure metadata and whitelist exist
        if 'metadata' not in tool_info:
            tool_info['metadata'] = {}
        if 'whitelist' not in tool_info['metadata']:
            tool_info['metadata']['whitelist'] = []

        # Check if pattern already exists
        if pattern in tool_info['metadata']['whitelist']:
            return False, f"Pattern '{pattern}' already in whitelist"

        # Add pattern
        tool_info['metadata']['whitelist'].append(pattern)
        tool_info['last_modified'] = datetime.now().strftime('%Y-%m-%d')

        # Save registry
        if self._save_registry():
            logger.info(f"Added whitelist pattern '{pattern}' to tool '{tool_name}'")
            return True, f"Pattern '{pattern}' added to whitelist"
        else:
            return False, "Failed to save registry"

    def remove_whitelist_pattern(self, tool_name: str, pattern: str) -> tuple[bool, str]:
        """
        Remove a whitelist pattern from a tool's configuration.

        Args:
            tool_name: Name of the tool
            pattern: Whitelist pattern to remove

        Returns:
            Tuple of (success, message)
        """
        tool_info = self.get_tool_info(tool_name)
        if not tool_info:
            return False, f"Tool '{tool_name}' not found"

        # Check if whitelist exists
        whitelist = tool_info.get('metadata', {}).get('whitelist', [])
        if pattern not in whitelist:
            return False, f"Pattern '{pattern}' not in whitelist"

        # Remove pattern
        whitelist.remove(pattern)
        tool_info['last_modified'] = datetime.now().strftime('%Y-%m-%d')

        # Save registry
        if self._save_registry():
            logger.info(f"Removed whitelist pattern '{pattern}' from tool '{tool_name}'")
            return True, f"Pattern '{pattern}' removed from whitelist"
        else:
            return False, "Failed to save registry"

    def list_whitelist_patterns(self, tool_name: str) -> Optional[List[str]]:
        """
        Get all whitelist patterns for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            List of whitelist patterns or None if tool not found
        """
        tool_info = self.get_tool_info(tool_name)
        if not tool_info:
            return None

        return tool_info.get('metadata', {}).get('whitelist', [])
