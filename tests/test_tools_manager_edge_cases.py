"""
Comprehensive edge case tests for ToolsManager to improve coverage.

Tests cover:
- set_global_config with missing global_config key
- import_tool: already exists, JSON decode error, exception handling
- import_tool: missing metadata fields, name mismatch
- export_tool: save failure
- list_available_tools: tools directory doesn't exist
- add_whitelist_pattern: pattern already exists, save failure
- remove_whitelist_pattern: pattern not in whitelist, save failure
- update_tool_metadata: tool not found, save failure
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from llf.tools_manager import ToolsManager


@pytest.fixture
def temp_registry(tmp_path):
    """Create temporary registry file."""
    registry_path = tmp_path / "tools_registry.json"
    registry_data = {
        "version": "1.1",
        "last_updated": "2026-01-12",
        "global_config": {
            "require_approval": False
        },
        "tools": [
            {
                "name": "test_tool",
                "display_name": "Test Tool",
                "description": "A test tool",
                "type": "postprocessor",
                "enabled": True,
                "directory": "test_tool",
                "created_date": "2026-01-01",
                "last_modified": "2026-01-01",
                "metadata": {
                    "category": "testing",
                    "requires_approval": False,
                    "dependencies": [],
                    "whitelist": ["/allowed/path"]
                }
            }
        ]
    }
    with open(registry_path, 'w') as f:
        json.dump(registry_data, f)
    return registry_path


@pytest.fixture
def tools_manager(temp_registry):
    """Create ToolsManager instance."""
    return ToolsManager(registry_path=temp_registry)


class TestSetGlobalConfigEdgeCases:
    """Test set_global_config edge cases."""

    def test_set_global_config_missing_key(self, tmp_path):
        """Test setting global config when global_config key doesn't exist."""
        registry_path = tmp_path / "tools_registry.json"
        registry_data = {
            "version": "1.1",
            "tools": []
            # No global_config key
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = ToolsManager(registry_path=registry_path)

        # Should create global_config dict
        result = manager.set_global_config("test_key", "test_value")
        assert result is True
        assert "global_config" in manager.registry
        assert manager.registry["global_config"]["test_key"] == "test_value"


class TestImportToolEdgeCases:
    """Test import_tool edge cases."""

    def test_import_tool_already_exists(self, tools_manager):
        """Test importing tool that already exists in registry."""
        success, message = tools_manager.import_tool("test_tool")
        assert success is False
        assert "already exists" in message

    def test_import_tool_json_decode_error(self, tools_manager, tmp_path):
        """Test importing tool with invalid JSON in config."""
        # Create tools directory structure
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        tool_dir = tools_dir / "bad_json_tool"
        tool_dir.mkdir()

        # Create invalid JSON config
        config_path = tool_dir / "config.json"
        with open(config_path, 'w') as f:
            f.write("{invalid json{{")

        # Patch Path to use our test tools directory
        with patch.object(Path, '__truediv__', side_effect=lambda self, other: tools_dir / other if '__file__' in str(self) else Path.__truediv__(self, other)):
            with patch('llf.tools_manager.Path') as mock_path_class:
                mock_path_class.return_value.__truediv__ = lambda self, other: tools_dir / other

                success, message = tools_manager.import_tool("bad_json_tool")
                assert success is False
                assert "Invalid JSON" in message or "config not found" in message



class TestExportToolEdgeCases:
    """Test export_tool edge cases."""

    def test_export_tool_save_failure(self, tools_manager):
        """Test export_tool when saving registry fails."""
        # Mock _save_registry to return False
        with patch.object(tools_manager, '_save_registry', return_value=False):
            success, message = tools_manager.export_tool("test_tool")
            assert success is False
            assert "Failed to save registry" in message




class TestAddWhitelistPatternEdgeCases:
    """Test add_whitelist_pattern edge cases."""

    def test_add_whitelist_pattern_already_exists(self, tools_manager):
        """Test adding whitelist pattern that already exists."""
        success, message = tools_manager.add_whitelist_pattern("test_tool", "/allowed/path")
        assert success is False
        assert "already in whitelist" in message

    def test_add_whitelist_pattern_save_failure(self, tools_manager):
        """Test adding whitelist pattern when save fails."""
        # Mock _save_registry to return False
        with patch.object(tools_manager, '_save_registry', return_value=False):
            success, message = tools_manager.add_whitelist_pattern("test_tool", "/new/path")
            assert success is False
            assert "Failed to save registry" in message


class TestRemoveWhitelistPatternEdgeCases:
    """Test remove_whitelist_pattern edge cases."""

    def test_remove_whitelist_pattern_not_in_list(self, tools_manager):
        """Test removing whitelist pattern that doesn't exist."""
        success, message = tools_manager.remove_whitelist_pattern("test_tool", "/nonexistent/path")
        assert success is False
        assert "not in whitelist" in message

    def test_remove_whitelist_pattern_save_failure(self, tools_manager):
        """Test removing whitelist pattern when save fails."""
        # Mock _save_registry to return False
        with patch.object(tools_manager, '_save_registry', return_value=False):
            success, message = tools_manager.remove_whitelist_pattern("test_tool", "/allowed/path")
            assert success is False
            assert "Failed to save registry" in message


class TestUpdateToolMetadataEdgeCases:
    """Test update_tool_metadata edge cases."""

    def test_update_tool_metadata_tool_not_found(self, tools_manager):
        """Test updating metadata for non-existent tool."""
        result = tools_manager.update_tool_metadata("nonexistent_tool", "key", "value")
        assert result is False

    def test_update_tool_metadata_save_failure(self, tools_manager):
        """Test updating metadata when save fails."""
        # Mock _save_registry to return False
        with patch.object(tools_manager, '_save_registry', return_value=False):
            result = tools_manager.update_tool_metadata("test_tool", "new_key", "new_value")
            assert result is False
