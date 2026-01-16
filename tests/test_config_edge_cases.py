"""
Comprehensive edge case tests for Config to improve coverage.

Tests cover:
- Legacy configuration support (lines 268-273)
- is_using_external_api: empty api_base_url (line 352)
- has_local_server_config: using external API (line 384)
- get_active_server: exception handling, single server fallback (lines 444-445, 449)
- update_default_server: model_dir with string format (lines 484-485)
- save_to_file: model_dir relative path exception (lines 539-540)
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from llf.config import Config, ServerConfig


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def temp_config_file(temp_config_dir):
    """Create temporary config file."""
    config_file = temp_config_dir / "config.json"

    config_data = {
        "llm_endpoint": {
            "model_name": "test-model",
            "api_base_url": "http://localhost:8080/v1"
        }
    }

    with open(config_file, 'w') as f:
        json.dump(config_data, f)

    return config_file


class TestLegacyConfigSupport:
    """Test legacy configuration format support."""

    def test_legacy_default_llm_model_name(self, temp_config_dir):
        """Test loading legacy 'default_llm' config with model_name."""
        config_file = temp_config_dir / "legacy_config.json"

        # Create config with legacy format (no 'llm_endpoint')
        legacy_config = {
            "default_llm": {
                "model_name": "legacy-model",
                "gguf_file": "legacy-model.gguf"
            }
        }

        with open(config_file, 'w') as f:
            json.dump(legacy_config, f)

        config = Config(config_file=config_file)

        # Should load model_name from legacy config
        assert config.model_name == "legacy-model"
        assert config.gguf_file == "legacy-model.gguf"

    def test_legacy_config_with_new_structure(self, temp_config_dir):
        """Test that new structure takes precedence over legacy."""
        config_file = temp_config_dir / "mixed_config.json"

        # Create config with both legacy and new formats
        mixed_config = {
            "default_llm": {
                "model_name": "legacy-model"
            },
            "llm_endpoint": {  # This should prevent legacy model_name
                "model_name": "new-model"
            }
        }

        with open(config_file, 'w') as f:
            json.dump(mixed_config, f)

        config = Config(config_file=config_file)

        # Should use new model_name, not legacy
        assert config.model_name == "new-model"


class TestIsUsingExternalApiEdgeCases:
    """Test is_using_external_api edge cases."""

    def test_is_using_external_api_empty_url(self, temp_config_file):
        """Test when api_base_url is empty string."""
        config = Config(config_file=temp_config_file)
        config.api_base_url = ""

        # Empty URL means not using external API
        assert config.is_using_external_api() is False

    def test_is_using_external_api_none_url(self, temp_config_file):
        """Test when api_base_url is None."""
        config = Config(config_file=temp_config_file)
        config.api_base_url = None

        # None URL means not using external API
        assert config.is_using_external_api() is False


class TestHasLocalServerConfigEdgeCases:
    """Test has_local_server_config edge cases."""

    def test_has_local_server_config_using_external_api(self, temp_config_file):
        """Test has_local_server_config when using external API."""
        config = Config(config_file=temp_config_file)
        config.api_base_url = "https://api.openai.com/v1"
        config._has_local_server_section = True

        # Should return False when using external API
        assert config.has_local_server_config() is False


class TestGetActiveServerEdgeCases:
    """Test get_active_server edge cases."""

    def test_get_active_server_exception_handling(self, temp_config_file):
        """Test exception handling during URL parsing."""
        config = Config(config_file=temp_config_file)

        # Set api_base_url to invalid URL that will cause exception
        config.api_base_url = "not a valid url at all"

        # Add a server
        config.servers = {
            "test_server": Mock(server_port=8080, server_host="localhost")
        }

        # Should handle exception gracefully
        result = config.get_active_server()

        # Should return None or single server (line 449 fallback)
        assert result is None or result == list(config.servers.values())[0]

    def test_get_active_server_single_server_fallback(self, temp_config_file):
        """Test fallback to single server when only one configured."""
        config = Config(config_file=temp_config_file)

        # Configure exactly one server
        mock_server = Mock(server_port=8080, server_host="localhost")
        config.servers = {"only_server": mock_server}

        # Set api_base_url that doesn't match
        config.api_base_url = "http://different-host:9999/v1"

        # Should return the single configured server (line 449)
        result = config.get_active_server()
        assert result == mock_server


class TestUpdateDefaultServerEdgeCases:
    """Test update_default_server edge cases."""

    def test_update_default_server_with_string_model_dir(self, temp_config_dir):
        """Test update_default_server when model_dir is a string."""
        config_file = temp_config_dir / "config.json"

        config_data = {
            "llm_endpoint": {
                "model_name": "test-model"
            },
            "local_llm_servers": [
                {
                    "name": "test_server",
                    "server_host": "localhost",
                    "server_port": 8080,
                    "llama_server_path": "/path/to/llama-server",
                    "model_dir": "bartowski--Llama-3.3-70B-Instruct-GGUF"
                }
            ]
        }

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file=config_file)

        # Update default server - should convert model_dir format
        config.update_default_server("test_server")

        # Model name should be converted from -- to /
        assert config.model_name == "bartowski/Llama-3.3-70B-Instruct-GGUF"


class TestSaveToFileEdgeCases:
    """Test save_to_file edge cases."""

    def test_save_to_file_model_dir_relative_path_exception(self, temp_config_dir):
        """Test save_to_file when model_dir relative path conversion fails."""
        config_file = temp_config_dir / "config.json"

        # Create initial config
        config_data = {
            "llm_endpoint": {
                "model_name": "test-model"
            }
        }

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file=config_file)

        # Add server with model_dir outside of config.model_dir
        # This will cause ValueError when trying to compute relative path
        external_model_dir = Path("/completely/different/path/models")
        test_server = ServerConfig(
            name="test_server",
            server_host="localhost",
            server_port=8080,
            llama_server_path=Path("/path/to/server"),
            healthcheck_interval=30,
            model_dir=external_model_dir,
            gguf_file=None,
            server_params={}
        )

        config.servers = {"test_server": test_server}
        config.model_dir = temp_config_dir / "models"

        # Save config - should handle ValueError and use absolute path
        config.save_to_file(config_file)

        # Verify config was saved with absolute path
        with open(config_file, 'r') as f:
            saved_config = json.load(f)

        assert 'local_llm_servers' in saved_config
        assert saved_config['local_llm_servers'][0]['model_dir'] == str(external_model_dir)
