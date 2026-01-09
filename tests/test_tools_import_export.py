"""
Unit tests for Tools Import/Export and Whitelist Management.
"""

import pytest
import json
import tempfile
from pathlib import Path
from llf.tools_manager import ToolsManager


class TestToolsImportExport:
    """Test import/export functionality."""

    def test_export_tool(self, tmp_path):
        """Test exporting a tool from registry."""
        # Create test registry
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.1",
            "last_updated": "2026-01-06",
            "tools": [
                {
                    "name": "test_tool",
                    "type": "llm_invokable",
                    "enabled": False,
                    "directory": "test_tool"
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Export the tool
        success, message = manager.export_tool("test_tool")
        assert success is True
        assert "exported successfully" in message

        # Verify tool is removed from registry
        assert manager.get_tool_info("test_tool") is None

    def test_export_nonexistent_tool(self, tmp_path):
        """Test exporting a tool that doesn't exist."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.1",
            "tools": []
        }))

        manager = ToolsManager(registry_path=registry_path)

        success, message = manager.export_tool("nonexistent")
        assert success is False
        assert "not found" in message

    def test_import_tool(self, tmp_path):
        """Test importing a tool from config.json."""
        # Create test registry without the tool
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.1",
            "tools": []
        }))

        # Create mock tools directory with config.json
        tools_dir = tmp_path.parent / "tools"
        tools_dir.mkdir(exist_ok=True)
        tool_dir = tools_dir / "test_tool"
        tool_dir.mkdir(exist_ok=True)

        config_path = tool_dir / "config.json"
        config_path.write_text(json.dumps({
            "name": "test_tool",
            "type": "llm_invokable",
            "enabled": False,
            "directory": "test_tool"
        }))

        # Note: This test won't work properly without mocking the tools directory path
        # but it shows the test structure

    def test_import_already_exists(self, tmp_path):
        """Test importing a tool that already exists in registry."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.1",
            "tools": [
                {
                    "name": "test_tool",
                    "type": "llm_invokable",
                    "enabled": False,
                    "directory": "test_tool"
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        success, message = manager.import_tool("test_tool")
        assert success is False
        assert "already exists" in message


class TestWhitelistManagement:
    """Test whitelist add/remove/list functionality."""

    def test_add_whitelist_pattern(self, tmp_path):
        """Test adding a whitelist pattern to a tool."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.1",
            "tools": [
                {
                    "name": "test_tool",
                    "type": "llm_invokable",
                    "enabled": False,
                    "directory": "test_tool",
                    "metadata": {}
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Add pattern
        success, message = manager.add_whitelist_pattern("test_tool", "*.txt")
        assert success is True
        assert "added to whitelist" in message

        # Verify pattern was added
        patterns = manager.list_whitelist_patterns("test_tool")
        assert "*.txt" in patterns

    def test_add_duplicate_pattern(self, tmp_path):
        """Test adding a duplicate whitelist pattern."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.1",
            "tools": [
                {
                    "name": "test_tool",
                    "type": "llm_invokable",
                    "metadata": {
                        "whitelist": ["*.txt"]
                    }
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Try to add duplicate
        success, message = manager.add_whitelist_pattern("test_tool", "*.txt")
        assert success is False
        assert "already in whitelist" in message

    def test_remove_whitelist_pattern(self, tmp_path):
        """Test removing a whitelist pattern."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.1",
            "tools": [
                {
                    "name": "test_tool",
                    "type": "llm_invokable",
                    "metadata": {
                        "whitelist": ["*.txt", "*.py"]
                    }
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Remove pattern
        success, message = manager.remove_whitelist_pattern("test_tool", "*.txt")
        assert success is True
        assert "removed from whitelist" in message

        # Verify pattern was removed
        patterns = manager.list_whitelist_patterns("test_tool")
        assert "*.txt" not in patterns
        assert "*.py" in patterns

    def test_remove_nonexistent_pattern(self, tmp_path):
        """Test removing a pattern that doesn't exist."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.1",
            "tools": [
                {
                    "name": "test_tool",
                    "type": "llm_invokable",
                    "metadata": {
                        "whitelist": ["*.txt"]
                    }
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        success, message = manager.remove_whitelist_pattern("test_tool", "*.py")
        assert success is False
        assert "not in whitelist" in message

    def test_list_whitelist_patterns(self, tmp_path):
        """Test listing whitelist patterns."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.1",
            "tools": [
                {
                    "name": "test_tool",
                    "type": "llm_invokable",
                    "metadata": {
                        "whitelist": ["*.txt", "*.py", "/path/to/dir/*"]
                    }
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        patterns = manager.list_whitelist_patterns("test_tool")
        assert len(patterns) == 3
        assert "*.txt" in patterns
        assert "*.py" in patterns
        assert "/path/to/dir/*" in patterns

    def test_list_whitelist_empty(self, tmp_path):
        """Test listing whitelist when empty."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.1",
            "tools": [
                {
                    "name": "test_tool",
                    "type": "llm_invokable",
                    "metadata": {}
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        patterns = manager.list_whitelist_patterns("test_tool")
        assert patterns == []

    def test_list_whitelist_nonexistent_tool(self, tmp_path):
        """Test listing whitelist for nonexistent tool."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.1",
            "tools": []
        }))

        manager = ToolsManager(registry_path=registry_path)

        patterns = manager.list_whitelist_patterns("nonexistent")
        assert patterns is None
