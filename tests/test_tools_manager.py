"""
Unit tests for ToolsManager.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
from llf.tools_manager import ToolsManager


class TestToolsManager:
    """Test ToolsManager functionality."""

    def test_initialization_with_defaults(self):
        """Test initialization with default paths."""
        manager = ToolsManager()

        assert manager.registry_path.name == 'tools_registry.json'
        assert isinstance(manager.session_overrides, dict)
        assert len(manager.session_overrides) == 0

    def test_initialization_with_custom_path(self, tmp_path):
        """Test initialization with custom path."""
        registry_path = tmp_path / "custom_registry.json"

        manager = ToolsManager(registry_path=registry_path)

        assert manager.registry_path == registry_path

    def test_load_registry_from_file(self, tmp_path):
        """Test loading registry from file."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "last_updated": "2025-12-28",
            "tools": [
                {
                    "name": "xml_format",
                    "display_name": "XML Format Parser",
                    "description": "Parse XML-style function calls",
                    "type": "compatibility_layer",
                    "enabled": True,
                    "directory": "xml_format",
                    "metadata": {}
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        assert manager.registry['version'] == '1.0'
        assert len(manager.registry['tools']) == 1
        assert manager.registry['tools'][0]['name'] == 'xml_format'
        assert manager.registry['tools'][0]['enabled'] is True

    def test_load_registry_with_missing_file(self, tmp_path):
        """Test loading registry when file is missing."""
        registry_path = tmp_path / "missing_registry.json"

        manager = ToolsManager(registry_path=registry_path)

        # Should use defaults
        assert manager.registry['version'] == '1.0'
        assert len(manager.registry['tools']) >= 1
        assert any(tool['name'] == 'xml_format' for tool in manager.registry['tools'])

    def test_get_default_registry(self):
        """Test default registry structure."""
        manager = ToolsManager()

        default_registry = manager._get_default_registry()

        assert default_registry['version'] == '1.0'
        assert 'tools' in default_registry
        assert 'metadata' in default_registry
        assert len(default_registry['tools']) >= 1

        # Check xml_format is in defaults
        xml_tool = next((t for t in default_registry['tools'] if t['name'] == 'xml_format'), None)
        assert xml_tool is not None
        assert xml_tool['display_name'] == 'XML Format Parser'

    def test_is_feature_enabled_from_registry(self, tmp_path):
        """Test checking if feature is enabled from registry."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": True
                },
                {
                    "name": "other_tool",
                    "enabled": False
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        assert manager.is_feature_enabled('xml_format') is True
        assert manager.is_feature_enabled('other_tool') is False
        assert manager.is_feature_enabled('nonexistent') is False

    def test_is_feature_enabled_with_session_override(self, tmp_path):
        """Test that session overrides take precedence over registry."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": True
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Registry says enabled
        assert manager.is_feature_enabled('xml_format') is True

        # Session override to disable
        manager.session_overrides['xml_format'] = False
        assert manager.is_feature_enabled('xml_format') is False

    def test_enable_feature_session_only(self, tmp_path):
        """Test enabling feature as session override."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": False
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Initially disabled
        assert manager.is_feature_enabled('xml_format') is False

        # Enable as session override
        result = manager.enable_feature('xml_format', session_only=True)

        assert result is True
        assert manager.is_feature_enabled('xml_format') is True
        assert 'xml_format' in manager.session_overrides
        assert manager.session_overrides['xml_format'] is True

    def test_disable_feature_session_only(self, tmp_path):
        """Test disabling feature as session override."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": True
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Initially enabled from registry
        assert manager.is_feature_enabled('xml_format') is True

        # Disable as session override
        result = manager.disable_feature('xml_format', session_only=True)

        assert result is True
        assert manager.is_feature_enabled('xml_format') is False
        assert 'xml_format' in manager.session_overrides
        assert manager.session_overrides['xml_format'] is False

    def test_enable_feature_persistent(self, tmp_path):
        """Test enabling a feature persistently."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "last_updated": "2025-12-27",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": False,
                    "last_modified": None
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Enable persistently
        result = manager.enable_feature('xml_format', session_only=False)

        assert result is True

        # Check it was written to file
        with open(registry_path) as f:
            saved_registry = json.load(f)

        assert saved_registry['tools'][0]['enabled'] is True
        assert saved_registry['tools'][0]['last_modified'] is not None
        assert saved_registry['last_updated'] is not None

    def test_disable_feature_persistent(self, tmp_path):
        """Test disabling a feature persistently."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "last_updated": "2025-12-27",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": True,
                    "last_modified": None
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Disable persistently
        result = manager.disable_feature('xml_format', session_only=False)

        assert result is True

        # Check it was updated in file
        with open(registry_path) as f:
            saved_registry = json.load(f)

        assert saved_registry['tools'][0]['enabled'] is False
        assert saved_registry['tools'][0]['last_modified'] is not None

    def test_enable_feature_persistent_unknown_tool(self, tmp_path):
        """Test enabling an unknown tool persistently fails."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": []
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Try to enable unknown tool
        result = manager.enable_feature('unknown', session_only=False)

        assert result is False

    def test_disable_feature_persistent_unknown_tool(self, tmp_path):
        """Test disabling an unknown tool persistently fails."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": []
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Try to disable unknown tool
        result = manager.disable_feature('unknown', session_only=False)

        assert result is False

    def test_reset_to_config(self, tmp_path):
        """Test resetting feature to registry file setting."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": True
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Add session override
        manager.session_overrides['xml_format'] = False
        assert manager.is_feature_enabled('xml_format') is False

        # Reset to registry
        result = manager.reset_to_config('xml_format')

        assert result is True
        assert 'xml_format' not in manager.session_overrides
        assert manager.is_feature_enabled('xml_format') is True  # Back to registry value

    def test_reset_to_config_no_override(self):
        """Test resetting when there's no session override."""
        manager = ToolsManager()

        # No override exists
        result = manager.reset_to_config('xml_format')

        assert result is True
        assert 'xml_format' not in manager.session_overrides

    def test_list_features(self, tmp_path):
        """Test listing all features (backward compatibility)."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": True,
                    "description": "Parse XML",
                    "metadata": {
                        "use_case": "Model outputs XML"
                    }
                },
                {
                    "name": "other_tool",
                    "enabled": False,
                    "description": "Other tool",
                    "metadata": {}
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        features = manager.list_features()

        assert isinstance(features, dict)
        assert 'xml_format' in features
        assert 'other_tool' in features
        assert features['xml_format']['enabled'] is True
        assert features['xml_format']['description'] == 'Parse XML'
        assert features['xml_format']['note'] == 'Model outputs XML'
        assert features['other_tool']['enabled'] is False

    def test_list_tools(self, tmp_path):
        """Test listing all tools."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "display_name": "XML Format Parser",
                    "enabled": True
                },
                {
                    "name": "other_tool",
                    "display_name": "Other Tool",
                    "enabled": False
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        tools = manager.list_tools()

        assert isinstance(tools, list)
        assert len(tools) == 2
        assert tools[0]['name'] == 'xml_format'
        assert tools[0]['display_name'] == 'XML Format Parser'
        assert tools[1]['name'] == 'other_tool'

    def test_get_tool_info(self, tmp_path):
        """Test getting detailed tool information."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "display_name": "XML Format Parser",
                    "description": "Parse XML-style function calls",
                    "type": "compatibility_layer",
                    "enabled": True,
                    "directory": "xml_format",
                    "metadata": {
                        "input_format": "XML",
                        "output_format": "JSON"
                    }
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        tool_info = manager.get_tool_info('xml_format')

        assert tool_info is not None
        assert tool_info['name'] == 'xml_format'
        assert tool_info['display_name'] == 'XML Format Parser'
        assert tool_info['type'] == 'compatibility_layer'
        assert tool_info['metadata']['input_format'] == 'XML'

    def test_get_tool_info_not_found(self, tmp_path):
        """Test getting info for non-existent tool."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": []
        }))

        manager = ToolsManager(registry_path=registry_path)

        tool_info = manager.get_tool_info('nonexistent')

        assert tool_info is None

    def test_save_registry_creates_directory(self, tmp_path):
        """Test that save_registry creates parent directories if needed."""
        registry_path = tmp_path / "subdir" / "tools_registry.json"

        # Directory doesn't exist yet
        assert not registry_path.parent.exists()

        manager = ToolsManager(registry_path=registry_path)
        manager.registry = {
            "version": "1.0",
            "last_updated": "2025-12-28",
            "tools": []
        }

        # Save should create directory
        result = manager._save_registry()

        assert result is True
        assert registry_path.parent.exists()
        assert registry_path.exists()

    def test_save_registry_updates_timestamp(self, tmp_path):
        """Test that save_registry updates last_updated timestamp."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "last_updated": "2025-01-01",
            "tools": []
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Save registry
        manager._save_registry()

        # Check timestamp was updated
        with open(registry_path) as f:
            saved_registry = json.load(f)

        assert saved_registry['last_updated'] != "2025-01-01"
        # Should be today's date
        today = datetime.now().strftime('%Y-%m-%d')
        assert saved_registry['last_updated'] == today

    def test_load_registry_with_invalid_json(self, tmp_path):
        """Test handling of invalid JSON in registry."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text("invalid json{")

        manager = ToolsManager(registry_path=registry_path)

        # Should use defaults
        assert manager.registry['version'] == '1.0'
        assert 'tools' in manager.registry
        assert len(manager.registry['tools']) >= 1

    # ===== Three-State Support Tests =====

    def test_normalize_enabled_value_with_bool(self):
        """Test _normalize_enabled_value with boolean values."""
        manager = ToolsManager()

        assert manager._normalize_enabled_value(True) is True
        assert manager._normalize_enabled_value(False) is False

    def test_normalize_enabled_value_with_strings(self):
        """Test _normalize_enabled_value with string values."""
        manager = ToolsManager()

        assert manager._normalize_enabled_value('true') is True
        assert manager._normalize_enabled_value('True') is True
        assert manager._normalize_enabled_value('auto') is True
        assert manager._normalize_enabled_value('Auto') is True
        assert manager._normalize_enabled_value('false') is False
        assert manager._normalize_enabled_value('False') is False

    def test_is_feature_enabled_with_auto_state(self, tmp_path):
        """Test that 'auto' state is treated as enabled."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": "auto"
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Auto should be treated as enabled
        assert manager.is_feature_enabled('xml_format') is True

    def test_get_enabled_state_returns_raw_value(self, tmp_path):
        """Test get_enabled_state returns the raw three-state value."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": "auto"
                },
                {
                    "name": "tool_enabled",
                    "enabled": True
                },
                {
                    "name": "tool_disabled",
                    "enabled": False
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        assert manager.get_enabled_state('xml_format') == 'auto'
        assert manager.get_enabled_state('tool_enabled') is True
        assert manager.get_enabled_state('tool_disabled') is False
        assert manager.get_enabled_state('nonexistent') is False

    def test_get_enabled_state_with_session_override(self, tmp_path):
        """Test that get_enabled_state returns session override value."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": False
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Registry says disabled
        assert manager.get_enabled_state('xml_format') is False

        # Session override to auto
        manager.session_overrides['xml_format'] = 'auto'
        assert manager.get_enabled_state('xml_format') == 'auto'

    def test_should_load_at_init_with_auto(self, tmp_path):
        """Test should_load_at_init returns True for 'auto' state."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": "auto"
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        assert manager.should_load_at_init('xml_format') is True

    def test_should_load_at_init_with_true(self, tmp_path):
        """Test should_load_at_init returns True for enabled state."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": True
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        assert manager.should_load_at_init('xml_format') is True

    def test_should_load_at_init_with_false(self, tmp_path):
        """Test should_load_at_init returns False for disabled state."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": False
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        assert manager.should_load_at_init('xml_format') is False

    def test_auto_feature_session_only(self, tmp_path):
        """Test setting feature to auto as session override."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": False
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Initially disabled
        assert manager.is_feature_enabled('xml_format') is False
        assert manager.get_enabled_state('xml_format') is False

        # Set to auto as session override
        result = manager.auto_feature('xml_format', session_only=True)

        assert result is True
        assert manager.is_feature_enabled('xml_format') is True  # Auto is treated as enabled
        assert manager.get_enabled_state('xml_format') == 'auto'
        assert 'xml_format' in manager.session_overrides
        assert manager.session_overrides['xml_format'] == 'auto'

    def test_auto_feature_persistent(self, tmp_path):
        """Test setting feature to auto persistently."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "last_updated": "2025-12-27",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": True,
                    "last_modified": None
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Set to auto persistently
        result = manager.auto_feature('xml_format', session_only=False)

        assert result is True

        # Check it was written to file
        with open(registry_path) as f:
            saved_registry = json.load(f)

        assert saved_registry['tools'][0]['enabled'] == 'auto'
        assert saved_registry['tools'][0]['last_modified'] is not None
        assert saved_registry['last_updated'] is not None

    def test_auto_feature_persistent_unknown_tool(self, tmp_path):
        """Test setting unknown tool to auto persistently fails."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": []
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Try to set unknown tool to auto
        result = manager.auto_feature('unknown', session_only=False)

        assert result is False

    def test_list_features_with_auto_state(self, tmp_path):
        """Test listing features with 'auto' state."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": "auto",
                    "description": "Parse XML",
                    "metadata": {}
                },
                {
                    "name": "enabled_tool",
                    "enabled": True,
                    "description": "Enabled tool",
                    "metadata": {}
                },
                {
                    "name": "disabled_tool",
                    "enabled": False,
                    "description": "Disabled tool",
                    "metadata": {}
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        features = manager.list_features()

        assert isinstance(features, dict)
        assert features['xml_format']['enabled'] == 'auto'
        assert features['enabled_tool']['enabled'] is True
        assert features['disabled_tool']['enabled'] is False

    def test_backward_compatibility_with_boolean_enabled(self, tmp_path):
        """Test that boolean enabled values still work."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "tool_true",
                    "enabled": True
                },
                {
                    "name": "tool_false",
                    "enabled": False
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Boolean values should still work
        assert manager.is_feature_enabled('tool_true') is True
        assert manager.is_feature_enabled('tool_false') is False
        assert manager.get_enabled_state('tool_true') is True
        assert manager.get_enabled_state('tool_false') is False

    def test_session_override_with_auto_string(self, tmp_path):
        """Test session override can use 'auto' string."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": False
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Manually set session override to auto
        manager.session_overrides['xml_format'] = 'auto'

        assert manager.is_feature_enabled('xml_format') is True
        assert manager.get_enabled_state('xml_format') == 'auto'

    def test_reset_to_config_with_auto_state(self, tmp_path):
        """Test resetting to registry value when registry has 'auto'."""
        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.0",
            "tools": [
                {
                    "name": "xml_format",
                    "enabled": "auto"
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Add session override to disable
        manager.session_overrides['xml_format'] = False
        assert manager.get_enabled_state('xml_format') is False

        # Reset to registry
        result = manager.reset_to_config('xml_format')

        assert result is True
        assert 'xml_format' not in manager.session_overrides
        assert manager.get_enabled_state('xml_format') == 'auto'  # Back to registry value
        assert manager.is_feature_enabled('xml_format') is True  # Auto is treated as enabled
