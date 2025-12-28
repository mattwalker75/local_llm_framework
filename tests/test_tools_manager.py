"""
Unit tests for ToolsManager.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from llf.tools_manager import ToolsManager


class TestToolsManager:
    """Test ToolsManager functionality."""

    def test_initialization_with_defaults(self):
        """Test initialization with default paths."""
        manager = ToolsManager()

        assert manager.main_config_path.name == 'config.json'
        assert manager.config_path.name == 'tools_config.json'
        assert isinstance(manager.session_overrides, dict)
        assert len(manager.session_overrides) == 0

    def test_initialization_with_custom_paths(self, tmp_path):
        """Test initialization with custom paths."""
        main_config = tmp_path / "custom_main.json"
        tools_config = tmp_path / "custom_tools.json"

        manager = ToolsManager(config_path=tools_config, main_config_path=main_config)

        assert manager.main_config_path == main_config
        assert manager.config_path == tools_config

    def test_load_config_from_main_config(self, tmp_path):
        """Test loading config from main config.json."""
        main_config = tmp_path / "config.json"
        main_config.write_text(json.dumps({
            "llm_endpoint": {
                "tools": {
                    "xml_format": "enable"
                }
            }
        }))

        manager = ToolsManager(main_config_path=main_config)

        assert manager.config['source'] == 'main_config'
        assert manager.config['features']['xml_format']['enabled'] is True

    def test_load_config_from_legacy_config(self, tmp_path):
        """Test loading config from legacy tools_config.json."""
        main_config = tmp_path / "config.json"
        main_config.write_text(json.dumps({"llm_endpoint": {}}))

        tools_config = tmp_path / "tools_config.json"
        tools_config.write_text(json.dumps({
            "version": "1.0",
            "features": {
                "xml_format": {
                    "enabled": True,
                    "description": "Test description"
                }
            }
        }))

        manager = ToolsManager(config_path=tools_config, main_config_path=main_config)

        assert manager.config['features']['xml_format']['enabled'] is True

    def test_load_config_with_missing_files(self, tmp_path):
        """Test loading config when both files are missing."""
        main_config = tmp_path / "missing_main.json"
        tools_config = tmp_path / "missing_tools.json"

        manager = ToolsManager(config_path=tools_config, main_config_path=main_config)

        # Should use defaults
        assert manager.config['version'] == '1.0'
        assert 'xml_format' in manager.config['features']
        assert manager.config['features']['xml_format']['enabled'] is False

    def test_convert_main_config(self):
        """Test conversion from main config format to internal format."""
        manager = ToolsManager()

        tools_config = {
            "xml_format": "enable",
            "other_feature": "disable"
        }

        result = manager._convert_main_config(tools_config)

        assert result['version'] == '1.0'
        assert result['source'] == 'main_config'
        assert result['features']['xml_format']['enabled'] is True
        assert result['features']['other_feature']['enabled'] is False

    def test_get_feature_description(self):
        """Test getting feature descriptions."""
        manager = ToolsManager()

        # Known feature
        desc = manager._get_feature_description('xml_format')
        assert 'XML' in desc
        assert 'OpenAI JSON format' in desc

        # Unknown feature
        desc = manager._get_feature_description('unknown_feature')
        assert 'unknown_feature' in desc

    def test_is_feature_enabled_from_config(self, tmp_path):
        """Test checking if feature is enabled from config."""
        main_config = tmp_path / "config.json"
        main_config.write_text(json.dumps({
            "llm_endpoint": {
                "tools": {
                    "xml_format": "enable"
                }
            }
        }))

        manager = ToolsManager(main_config_path=main_config)

        assert manager.is_feature_enabled('xml_format') is True
        assert manager.is_feature_enabled('nonexistent') is False

    def test_is_feature_enabled_with_session_override(self, tmp_path):
        """Test that session overrides take precedence over config."""
        main_config = tmp_path / "config.json"
        main_config.write_text(json.dumps({
            "llm_endpoint": {
                "tools": {
                    "xml_format": "enable"
                }
            }
        }))

        manager = ToolsManager(main_config_path=main_config)

        # Config says enabled
        assert manager.is_feature_enabled('xml_format') is True

        # Session override to disable
        manager.session_overrides['xml_format'] = False
        assert manager.is_feature_enabled('xml_format') is False

    def test_enable_feature_session_only(self, tmp_path):
        """Test enabling feature as session override."""
        main_config = tmp_path / "config.json"
        main_config.write_text(json.dumps({
            "llm_endpoint": {
                "tools": {
                    "xml_format": "disable"
                }
            }
        }))

        manager = ToolsManager(main_config_path=main_config)

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
        main_config = tmp_path / "config.json"
        main_config.write_text(json.dumps({
            "llm_endpoint": {
                "tools": {
                    "xml_format": "enable"
                }
            }
        }))

        manager = ToolsManager(main_config_path=main_config)

        # Initially enabled from config
        assert manager.is_feature_enabled('xml_format') is True

        # Disable as session override
        result = manager.disable_feature('xml_format', session_only=True)

        assert result is True
        assert manager.is_feature_enabled('xml_format') is False
        assert 'xml_format' in manager.session_overrides
        assert manager.session_overrides['xml_format'] is False

    def test_reset_to_config(self, tmp_path):
        """Test resetting feature to config file setting."""
        main_config = tmp_path / "config.json"
        main_config.write_text(json.dumps({
            "llm_endpoint": {
                "tools": {
                    "xml_format": "enable"
                }
            }
        }))

        manager = ToolsManager(main_config_path=main_config)

        # Add session override
        manager.session_overrides['xml_format'] = False
        assert manager.is_feature_enabled('xml_format') is False

        # Reset to config
        result = manager.reset_to_config('xml_format')

        assert result is True
        assert 'xml_format' not in manager.session_overrides
        assert manager.is_feature_enabled('xml_format') is True  # Back to config value

    def test_reset_to_config_no_override(self):
        """Test resetting when there's no session override."""
        manager = ToolsManager()

        # No override exists
        result = manager.reset_to_config('xml_format')

        assert result is True
        assert 'xml_format' not in manager.session_overrides

    def test_list_features(self, tmp_path):
        """Test listing all features."""
        main_config = tmp_path / "config.json"
        main_config.write_text(json.dumps({
            "llm_endpoint": {
                "tools": {
                    "xml_format": "enable",
                    "other_feature": "disable"
                }
            }
        }))

        manager = ToolsManager(main_config_path=main_config)

        features = manager.list_features()

        assert isinstance(features, dict)
        assert 'xml_format' in features
        assert 'other_feature' in features
        assert features['xml_format']['enabled'] is True
        assert features['other_feature']['enabled'] is False

    def test_enable_feature_persistent_new_feature(self, tmp_path):
        """Test enabling a new feature persistently."""
        tools_config = tmp_path / "tools_config.json"
        tools_config.write_text(json.dumps({
            "version": "1.0",
            "features": {}
        }))

        manager = ToolsManager(config_path=tools_config)

        # Enable persistently
        result = manager.enable_feature('new_feature', session_only=False)

        assert result is True

        # Check it was written to file
        with open(tools_config) as f:
            saved_config = json.load(f)

        assert saved_config['features']['new_feature']['enabled'] is True

    def test_enable_feature_persistent_existing_feature(self, tmp_path):
        """Test enabling an existing feature persistently."""
        tools_config = tmp_path / "tools_config.json"
        tools_config.write_text(json.dumps({
            "version": "1.0",
            "features": {
                "xml_format": {
                    "enabled": False,
                    "description": "Test"
                }
            }
        }))

        manager = ToolsManager(config_path=tools_config)

        # Enable persistently
        result = manager.enable_feature('xml_format', session_only=False)

        assert result is True

        # Check it was updated in file
        with open(tools_config) as f:
            saved_config = json.load(f)

        assert saved_config['features']['xml_format']['enabled'] is True

    def test_disable_feature_persistent(self, tmp_path):
        """Test disabling a feature persistently."""
        tools_config = tmp_path / "tools_config.json"
        tools_config.write_text(json.dumps({
            "version": "1.0",
            "features": {
                "xml_format": {
                    "enabled": True,
                    "description": "Test"
                }
            }
        }))

        manager = ToolsManager(config_path=tools_config)

        # Disable persistently
        result = manager.disable_feature('xml_format', session_only=False)

        assert result is True

        # Check it was updated in file
        with open(tools_config) as f:
            saved_config = json.load(f)

        assert saved_config['features']['xml_format']['enabled'] is False

    def test_disable_feature_persistent_unknown_feature(self, tmp_path):
        """Test disabling an unknown feature persistently fails."""
        tools_config = tmp_path / "tools_config.json"
        tools_config.write_text(json.dumps({
            "version": "1.0",
            "features": {}
        }))

        manager = ToolsManager(config_path=tools_config)

        # Try to disable unknown feature
        result = manager.disable_feature('unknown', session_only=False)

        assert result is False

    def test_disable_feature_persistent_no_features_section(self, tmp_path):
        """Test disabling when features section doesn't exist."""
        tools_config = tmp_path / "tools_config.json"
        tools_config.write_text(json.dumps({
            "version": "1.0"
        }))

        manager = ToolsManager(config_path=tools_config)

        # Should succeed (no-op)
        result = manager.disable_feature('xml_format', session_only=False)

        assert result is True

    def test_load_config_with_invalid_main_config(self, tmp_path):
        """Test handling of invalid JSON in main config."""
        main_config = tmp_path / "config.json"
        main_config.write_text("invalid json{")

        tools_config = tmp_path / "tools_config.json"
        tools_config.write_text(json.dumps({
            "version": "1.0",
            "features": {
                "xml_format": {"enabled": True}
            }
        }))

        manager = ToolsManager(config_path=tools_config, main_config_path=main_config)

        # Should fall back to legacy config
        assert manager.config['features']['xml_format']['enabled'] is True

    def test_load_config_with_invalid_legacy_config(self, tmp_path):
        """Test handling of invalid JSON in legacy config."""
        main_config = tmp_path / "config.json"
        main_config.write_text(json.dumps({"llm_endpoint": {}}))

        tools_config = tmp_path / "tools_config.json"
        tools_config.write_text("invalid json{")

        manager = ToolsManager(config_path=tools_config, main_config_path=main_config)

        # Should use defaults
        assert manager.config['version'] == '1.0'
        assert 'xml_format' in manager.config['features']

    def test_save_config_creates_directory(self, tmp_path):
        """Test that save_config creates parent directories if needed."""
        tools_config = tmp_path / "subdir" / "tools_config.json"

        # Directory doesn't exist yet
        assert not tools_config.parent.exists()

        manager = ToolsManager(config_path=tools_config)
        manager.config = {"version": "1.0", "features": {}}

        # Save should create directory
        result = manager._save_config()

        assert result is True
        assert tools_config.parent.exists()
        assert tools_config.exists()
