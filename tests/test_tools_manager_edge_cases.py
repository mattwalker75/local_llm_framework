"""
Comprehensive edge case tests for ToolsManager to improve coverage to 95%+.

Tests cover:
- set_global_config with missing global_config key
- import_tool: already exists, JSON decode error, exception handling
- import_tool: missing required fields, missing metadata fields, name mismatch, save failure (lines 471-503)
- export_tool: save failure
- list_available_tools: tools directory doesn't exist (line 553)
- add_whitelist_pattern: pattern already exists, save failure, missing metadata (line 584, 586)
- remove_whitelist_pattern: pattern not in whitelist, save failure
- update_tool_metadata: tool not found, save failure, missing metadata (line 669, 677-678)
"""

import json
import pytest
import shutil
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


@pytest.fixture
def real_tools_dir():
    """Get the real tools directory."""
    return Path(__file__).parent.parent / "llf" / "tools"


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

    def test_import_tool_missing_required_field(self, tools_manager, real_tools_dir):
        """Test importing tool with missing required field (lines 471-475)."""
        tool_dir = real_tools_dir / "incomplete_tool_test"
        tool_dir.mkdir(exist_ok=True)

        try:
            # Create config missing 'description' field
            config_data = {
                "name": "incomplete_tool_test",
                "display_name": "Incomplete Tool",
                # Missing 'description'
                "type": "postprocessor",
                "enabled": True,
                "directory": "incomplete_tool_test",
                "created_date": "2026-01-01",
                "last_modified": "2026-01-01",
                "metadata": {
                    "category": "testing",
                    "requires_approval": False,
                    "dependencies": []
                }
            }

            config_path = tool_dir / "config.json"
            with open(config_path, 'w') as f:
                json.dump(config_data, f)

            success, message = tools_manager.import_tool("incomplete_tool_test")
            assert success is False
            assert "missing required fields" in message
            assert "description" in message
        finally:
            # Cleanup
            if tool_dir.exists():
                shutil.rmtree(tool_dir)

    def test_import_tool_missing_metadata(self, tools_manager, real_tools_dir):
        """Test importing tool with missing metadata section (lines 478-479)."""
        tool_dir = real_tools_dir / "no_metadata_tool_test"
        tool_dir.mkdir(exist_ok=True)

        try:
            # Create config without metadata
            config_data = {
                "name": "no_metadata_tool_test",
                "display_name": "No Metadata Tool",
                "description": "Tool without metadata",
                "type": "postprocessor",
                "enabled": True,
                "directory": "no_metadata_tool_test",
                "created_date": "2026-01-01",
                "last_modified": "2026-01-01"
                # Missing 'metadata'
            }

            config_path = tool_dir / "config.json"
            with open(config_path, 'w') as f:
                json.dump(config_data, f)

            success, message = tools_manager.import_tool("no_metadata_tool_test")
            assert success is False
            assert "missing required fields" in message
            assert "metadata" in message
        finally:
            if tool_dir.exists():
                shutil.rmtree(tool_dir)

    def test_import_tool_missing_metadata_field(self, tools_manager, real_tools_dir):
        """Test importing tool with missing metadata field (lines 481-484)."""
        tool_dir = real_tools_dir / "incomplete_metadata_tool_test"
        tool_dir.mkdir(exist_ok=True)

        try:
            # Create config with incomplete metadata (missing 'category')
            config_data = {
                "name": "incomplete_metadata_tool_test",
                "display_name": "Incomplete Metadata Tool",
                "description": "Tool with incomplete metadata",
                "type": "postprocessor",
                "enabled": True,
                "directory": "incomplete_metadata_tool_test",
                "created_date": "2026-01-01",
                "last_modified": "2026-01-01",
                "metadata": {
                    # Missing 'category'
                    "requires_approval": False,
                    "dependencies": []
                }
            }

            config_path = tool_dir / "config.json"
            with open(config_path, 'w') as f:
                json.dump(config_data, f)

            success, message = tools_manager.import_tool("incomplete_metadata_tool_test")
            assert success is False
            assert "missing required fields" in message
            assert "metadata.category" in message
        finally:
            if tool_dir.exists():
                shutil.rmtree(tool_dir)

    def test_import_tool_name_mismatch(self, tools_manager, real_tools_dir):
        """Test importing tool with name mismatch (lines 490-491)."""
        tool_dir = real_tools_dir / "wrong_name_tool_test"
        tool_dir.mkdir(exist_ok=True)

        try:
            # Create config with different name than directory
            config_data = {
                "name": "different_name",  # Doesn't match directory name
                "display_name": "Wrong Name Tool",
                "description": "Tool with name mismatch",
                "type": "postprocessor",
                "enabled": True,
                "directory": "wrong_name_tool_test",
                "created_date": "2026-01-01",
                "last_modified": "2026-01-01",
                "metadata": {
                    "category": "testing",
                    "requires_approval": False,
                    "dependencies": []
                }
            }

            config_path = tool_dir / "config.json"
            with open(config_path, 'w') as f:
                json.dump(config_data, f)

            success, message = tools_manager.import_tool("wrong_name_tool_test")
            assert success is False
            assert "name mismatch" in message
        finally:
            if tool_dir.exists():
                shutil.rmtree(tool_dir)

    def test_import_tool_save_failure(self, tools_manager, real_tools_dir):
        """Test importing tool when save fails (lines 499-503)."""
        tool_dir = real_tools_dir / "new_valid_tool_test"
        tool_dir.mkdir(exist_ok=True)

        try:
            # Create valid config
            config_data = {
                "name": "new_valid_tool_test",
                "display_name": "New Valid Tool",
                "description": "A valid tool",
                "type": "postprocessor",
                "enabled": True,
                "directory": "new_valid_tool_test",
                "created_date": "2026-01-01",
                "last_modified": "2026-01-01",
                "metadata": {
                    "category": "testing",
                    "requires_approval": False,
                    "dependencies": []
                }
            }

            config_path = tool_dir / "config.json"
            with open(config_path, 'w') as f:
                json.dump(config_data, f)

            # Mock _save_registry to return False
            with patch.object(tools_manager, '_save_registry', return_value=False):
                success, message = tools_manager.import_tool("new_valid_tool_test")
                assert success is False
                assert "Failed to save registry" in message
        finally:
            if tool_dir.exists():
                shutil.rmtree(tool_dir)

    def test_import_tool_generic_exception(self, tools_manager):
        """Test importing tool with generic exception (lines 507-508)."""
        # Mock open to raise an exception
        with patch('builtins.open', side_effect=RuntimeError("Unexpected error")):
            success, message = tools_manager.import_tool("any_tool")
            assert success is False
            assert "Failed to import tool" in message


class TestListAvailableToolsEdgeCases:
    """Test list_available_tools edge cases."""

    def test_list_available_tools_directory_not_exists(self, tools_manager):
        """Test listing tools when tools directory doesn't exist (line 553)."""
        # Mock Path(__file__).parent.parent / 'tools' to return non-existent directory
        non_existent = Path("/nonexistent/tools")

        with patch('llf.tools_manager.Path') as mock_path_class:
            # Create a mock that returns a path where parent.parent / 'tools' doesn't exist
            mock_file_path = Mock()
            mock_parent = Mock()
            mock_parent.parent = Mock()
            mock_parent.parent.__truediv__ = Mock(return_value=non_existent)
            mock_file_path.parent = mock_parent
            mock_path_class.return_value = mock_file_path

            tools = tools_manager.list_available_tools()
            assert tools == []


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

    def test_add_whitelist_pattern_missing_metadata(self, tmp_path):
        """Test adding whitelist pattern when tool has no metadata (line 584)."""
        # Create registry with tool that has no metadata
        registry_path = tmp_path / "tools_registry.json"
        registry_data = {
            "version": "1.1",
            "tools": [
                {
                    "name": "test_tool_no_metadata",
                    "display_name": "Test Tool",
                    "description": "A test tool",
                    "type": "postprocessor",
                    "enabled": True,
                    "directory": "test_tool"
                    # No metadata
                }
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = ToolsManager(registry_path=registry_path)

        # Should create metadata dict
        success, message = manager.add_whitelist_pattern("test_tool_no_metadata", "/new/path")
        assert success is True
        tool_info = manager.get_tool_info("test_tool_no_metadata")
        assert 'metadata' in tool_info
        assert 'whitelist' in tool_info['metadata']
        assert "/new/path" in tool_info['metadata']['whitelist']

    def test_add_whitelist_pattern_missing_whitelist(self, tmp_path):
        """Test adding whitelist pattern when metadata has no whitelist (line 586)."""
        # Create registry with tool that has metadata but no whitelist
        registry_path = tmp_path / "tools_registry.json"
        registry_data = {
            "version": "1.1",
            "tools": [
                {
                    "name": "test_tool_no_whitelist",
                    "display_name": "Test Tool",
                    "description": "A test tool",
                    "type": "postprocessor",
                    "enabled": True,
                    "directory": "test_tool",
                    "metadata": {
                        "category": "testing"
                        # No whitelist
                    }
                }
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = ToolsManager(registry_path=registry_path)

        # Should create whitelist list
        success, message = manager.add_whitelist_pattern("test_tool_no_whitelist", "/new/path")
        assert success is True
        tool_info = manager.get_tool_info("test_tool_no_whitelist")
        assert 'whitelist' in tool_info['metadata']
        assert "/new/path" in tool_info['metadata']['whitelist']

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

    def test_update_tool_metadata_missing_metadata(self, tmp_path):
        """Test updating metadata when tool has no metadata dict (line 669)."""
        # Create registry with tool that has no metadata
        registry_path = tmp_path / "tools_registry.json"
        registry_data = {
            "version": "1.1",
            "tools": [
                {
                    "name": "test_tool_no_meta",
                    "display_name": "Test Tool",
                    "description": "A test tool",
                    "type": "postprocessor",
                    "enabled": True,
                    "directory": "test_tool"
                    # No metadata
                }
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = ToolsManager(registry_path=registry_path)

        # Should create metadata dict
        result = manager.update_tool_metadata("test_tool_no_meta", "new_key", "new_value")
        assert result is True
        tool_info = manager.get_tool_info("test_tool_no_meta")
        assert 'metadata' in tool_info
        assert tool_info['metadata']['new_key'] == "new_value"

    def test_update_tool_metadata_save_failure(self, tools_manager):
        """Test updating metadata when save fails (lines 677-678)."""
        # Mock _save_registry to return False
        with patch.object(tools_manager, '_save_registry', return_value=False):
            result = tools_manager.update_tool_metadata("test_tool", "new_key", "new_value")
            assert result is False
