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
            "version": "1.0",
            "last_updated": datetime.now().strftime('%Y-%m-%d'),
            "tools": [
                {
                    "name": "xml_format",
                    "display_name": "XML Format Parser",
                    "description": "Parse XML-style function calls and convert to OpenAI JSON format",
                    "type": "compatibility_layer",
                    "enabled": False,
                    "directory": "xml_format",
                    "created_date": None,
                    "last_modified": None,
                    "metadata": {
                        "input_format": "XML",
                        "output_format": "JSON",
                        "use_case": "Model outputs XML instead of JSON tool calls"
                    }
                }
            ],
            "metadata": {
                "description": "Registry of all available tools for the LLM Framework",
                "schema_version": "1.0"
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
