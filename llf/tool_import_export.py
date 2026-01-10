"""
Tool import and export functionality for managing tools in the registry.
"""

import json
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, Any, Optional
from llf.logging_config import get_logger

logger = get_logger(__name__)


class ToolImportExport:
    """Manages importing and exporting tools to/from the registry."""

    REQUIRED_CONFIG_FIELDS = [
        "name",
        "display_name",
        "description",
        "type",
        "enabled",
        "directory",
        "created_date",
        "last_modified"
    ]

    REQUIRED_METADATA_FIELDS = [
        "category",
        "requires_approval",
        "dependencies"
    ]

    def __init__(self, tools_dir: Path, registry_file: Path):
        """
        Initialize the import/export manager.

        Args:
            tools_dir: Path to the tools directory
            registry_file: Path to the tools_registry.json file
        """
        self.tools_dir = Path(tools_dir)
        self.registry_file = Path(registry_file)
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load the tools registry from file."""
        if not self.registry_file.exists():
            logger.error(f"Registry file not found: {self.registry_file}")
            return {"version": "1.1", "tools": [], "global_config": {}}

        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse registry file: {e}")
            return {"version": "1.1", "tools": [], "global_config": {}}

    def _save_registry(self) -> bool:
        """Save the tools registry to file."""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.registry, f, indent=2)
            logger.info(f"Registry saved to {self.registry_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
            return False

    def _validate_config(self, config: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate that a config.json has all required fields.

        Args:
            config: The config dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_missing_fields)
        """
        missing_fields = []

        # Check top-level required fields
        for field in self.REQUIRED_CONFIG_FIELDS:
            if field not in config:
                missing_fields.append(field)

        # Check metadata required fields
        if "metadata" not in config:
            missing_fields.append("metadata")
        else:
            for field in self.REQUIRED_METADATA_FIELDS:
                if field not in config["metadata"]:
                    missing_fields.append(f"metadata.{field}")

        return (len(missing_fields) == 0, missing_fields)

    def _tool_exists_in_registry(self, tool_name: str) -> bool:
        """Check if a tool already exists in the registry."""
        return any(tool["name"] == tool_name for tool in self.registry.get("tools", []))

    def import_tool(self, tool_name: str) -> tuple[bool, str]:
        """
        Import a tool from the tools directory into the registry.

        Args:
            tool_name: Name of the tool to import

        Returns:
            Tuple of (success, message)
        """
        # Check if tool already exists in registry
        if self._tool_exists_in_registry(tool_name):
            msg = f"Tool '{tool_name}' already exists in registry. Cannot import."
            logger.warning(msg)
            return (False, msg)

        # Check if tool directory exists
        tool_dir = self.tools_dir / tool_name
        if not tool_dir.exists() or not tool_dir.is_dir():
            msg = f"Tool directory not found: {tool_dir}"
            logger.error(msg)
            return (False, msg)

        # Check if config.json exists
        config_file = tool_dir / "config.json"
        if not config_file.exists():
            msg = f"config.json not found in {tool_dir}"
            logger.error(msg)
            return (False, msg)

        # Load and validate config.json
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in config.json: {e}"
            logger.error(msg)
            return (False, msg)

        # Validate required fields
        is_valid, missing_fields = self._validate_config(config)
        if not is_valid:
            msg = f"config.json is missing required fields: {', '.join(missing_fields)}"
            logger.error(msg)
            return (False, msg)

        # Verify tool name matches
        if config.get("name") != tool_name:
            msg = f"Tool name mismatch: directory='{tool_name}', config.name='{config.get('name')}'"
            logger.error(msg)
            return (False, msg)

        # Add to registry
        registry_entry = {
            "name": config["name"],
            "display_name": config["display_name"],
            "description": config["description"],
            "type": config["type"],
            "enabled": config["enabled"],
            "directory": config["directory"],
            "created_date": config["created_date"],
            "last_modified": config["last_modified"],
            "metadata": config["metadata"]
        }

        self.registry["tools"].append(registry_entry)

        if not self._save_registry():
            msg = "Failed to save registry after import"
            return (False, msg)

        msg = f"Successfully imported tool '{tool_name}' into registry"
        logger.info(msg)
        return (True, msg)

    def export_tool(self, tool_name: str, confirm: bool = False) -> tuple[bool, str]:
        """
        Export a tool from the registry (remove from registry, keep files).

        Args:
            tool_name: Name of the tool to export
            confirm: Whether user has confirmed the operation

        Returns:
            Tuple of (success, message)
        """
        # Check if tool exists in registry
        if not self._tool_exists_in_registry(tool_name):
            msg = f"Tool '{tool_name}' not found in registry"
            logger.warning(msg)
            return (False, msg)

        # If not confirmed, return message asking for confirmation
        if not confirm:
            msg = (f"This will remove '{tool_name}' from the registry but keep the tool files. "
                   "The tool will no longer be available until re-imported.")
            return (False, msg)

        # Remove from registry
        original_count = len(self.registry["tools"])
        self.registry["tools"] = [
            tool for tool in self.registry["tools"]
            if tool["name"] != tool_name
        ]

        if len(self.registry["tools"]) == original_count:
            msg = f"Failed to remove tool '{tool_name}' from registry"
            logger.error(msg)
            return (False, msg)

        if not self._save_registry():
            msg = "Failed to save registry after export"
            return (False, msg)

        msg = f"Successfully exported tool '{tool_name}' from registry (files preserved)"
        logger.info(msg)
        return (True, msg)

    def list_importable_tools(self) -> list[str]:
        """
        List all tools in the tools directory that are not in the registry.

        Returns:
            List of tool names that can be imported
        """
        if not self.tools_dir.exists():
            return []

        registry_tools = {tool["name"] for tool in self.registry.get("tools", [])}

        importable = []
        for item in self.tools_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it has a config.json
                config_file = item / "config.json"
                if config_file.exists() and item.name not in registry_tools:
                    importable.append(item.name)

        return sorted(importable)
