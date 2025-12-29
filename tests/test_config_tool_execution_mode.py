"""
Unit tests for tool_execution_mode configuration.
"""

import json
import pytest
from pathlib import Path
from llf.config import Config


class TestToolExecutionModeConfig:
    """Test tool_execution_mode configuration loading and validation."""

    def test_default_tool_execution_mode(self):
        """Test that default tool_execution_mode is one of the valid modes."""
        config = Config()
        assert config.tool_execution_mode in Config.VALID_TOOL_EXECUTION_MODES

    def test_load_single_pass_mode(self, tmp_path):
        """Test loading single_pass mode from config."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "llm_endpoint": {
                "tool_execution_mode": "single_pass"
            }
        }))

        config = Config(config_file)
        assert config.tool_execution_mode == "single_pass"

    def test_load_dual_pass_write_only_mode(self, tmp_path):
        """Test loading dual_pass_write_only mode from config."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "llm_endpoint": {
                "tool_execution_mode": "dual_pass_write_only"
            }
        }))

        config = Config(config_file)
        assert config.tool_execution_mode == "dual_pass_write_only"

    def test_load_dual_pass_all_mode(self, tmp_path):
        """Test loading dual_pass_all mode from config."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "llm_endpoint": {
                "tool_execution_mode": "dual_pass_all"
            }
        }))

        config = Config(config_file)
        assert config.tool_execution_mode == "dual_pass_all"

    def test_invalid_mode_raises_error(self, tmp_path):
        """Test that invalid mode raises ValueError."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "llm_endpoint": {
                "tool_execution_mode": "invalid_mode"
            }
        }))

        with pytest.raises(ValueError, match="Invalid tool_execution_mode"):
            Config(config_file)

    def test_missing_mode_uses_default(self, tmp_path):
        """Test that missing mode in config uses default."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1"
            }
        }))

        config = Config(config_file)
        assert config.tool_execution_mode == "single_pass"

    def test_mode_in_to_dict(self, tmp_path):
        """Test that tool_execution_mode is included in to_dict()."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "llm_endpoint": {
                "tool_execution_mode": "dual_pass_write_only"
            }
        }))

        config = Config(config_file)
        config_dict = config.to_dict()

        assert 'llm_endpoint' in config_dict
        assert 'tool_execution_mode' in config_dict['llm_endpoint']
        assert config_dict['llm_endpoint']['tool_execution_mode'] == "dual_pass_write_only"

    def test_valid_modes_constant(self):
        """Test that VALID_TOOL_EXECUTION_MODES constant has expected values."""
        expected_modes = ["single_pass", "dual_pass_write_only", "dual_pass_all"]
        assert Config.VALID_TOOL_EXECUTION_MODES == expected_modes

    def test_backward_compatibility_no_llm_endpoint(self, tmp_path):
        """Test backward compatibility when llm_endpoint section is missing."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "model_name": "test-model",
            "api_base_url": "http://localhost:8000/v1"
        }))

        config = Config(config_file)
        # Should use default mode
        assert config.tool_execution_mode == "single_pass"

    def test_save_and_reload_mode(self, tmp_path):
        """Test that mode is preserved when saving and reloading."""
        config_file = tmp_path / "config.json"

        # Create config with dual_pass_write_only
        config1 = Config()
        config1.tool_execution_mode = "dual_pass_write_only"
        config1.save_to_file(config_file)

        # Reload and verify
        config2 = Config(config_file)
        assert config2.tool_execution_mode == "dual_pass_write_only"
