"""
Tests for 'llf model list --imported' command to improve CLI coverage.

Targets lines 822-902 in cli.py (list_command with --imported flag).
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace

from llf.cli import list_command
from llf.config import Config


@pytest.fixture
def mock_config(tmp_path):
    """Create mock config for testing."""
    config = Config()
    config.config_file = tmp_path / "config.json"
    config.model_dir = tmp_path / "models"
    config.cache_dir = tmp_path / ".cache"
    return config


class TestModelListImported:
    """Test 'llf model list --imported' command (lines 822-902)."""

    def test_list_imported_multiserver_config(self, mock_config, tmp_path):
        """Test listing imported models with multi-server config (lines 827-881)."""
        # Create config with multi-server setup
        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    "model_dir": "bartowski--Llama-3.3-70B-Instruct-GGUF",
                    "gguf_file": "model-Q5_K_M.gguf"
                },
                {
                    "name": "server2",
                    "model_dir": "Qwen--Qwen2.5-Coder-7B-Instruct-GGUF",
                    "gguf_file": "model-Q4_K_M.gguf"
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1",
                "model_name": "bartowski/Llama-3.3-70B-Instruct-GGUF"
            }
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        args = Namespace(
            action='list',
            imported=True,
            model=None,
            info=False
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True
                mock_manager.get_model_info.return_value = {'size_gb': '5.2'}
                MockModelManager.return_value = mock_manager

                result = list_command(args)

                # Should return success
                assert result == 0
                # Should check if models are downloaded
                assert mock_manager.is_model_downloaded.called

    def test_list_imported_multiserver_same_model(self, mock_config, tmp_path):
        """Test listing when same model used across multiple servers (lines 838-880)."""
        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    "model_dir": "bartowski--Llama-3.3-70B-Instruct-GGUF",
                    "gguf_file": "model-Q5_K_M.gguf"
                },
                {
                    "name": "server2",
                    "model_dir": "bartowski--Llama-3.3-70B-Instruct-GGUF",
                    "gguf_file": "model-Q4_K_M.gguf"
                }
            ]
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        args = Namespace(
            action='list',
            imported=True,
            model=None,
            info=False
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = False
                MockModelManager.return_value = mock_manager

                result = list_command(args)

                # Should return success and show model used by 2 servers
                assert result == 0

    def test_list_imported_empty_servers(self, mock_config, tmp_path):
        """Test listing with empty servers list (lines 830-833)."""
        config_data = {
            "local_llm_servers": []
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        args = Namespace(
            action='list',
            imported=True,
            model=None,
            info=False
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                MockModelManager.return_value = mock_manager

                result = list_command(args)

                # Should return success with message about no models
                assert result == 0

    def test_list_imported_servers_no_model_dir(self, mock_config, tmp_path):
        """Test listing when servers have no model_dir (lines 851-854)."""
        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    # No model_dir field
                    "gguf_file": "model.gguf"
                }
            ]
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        args = Namespace(
            action='list',
            imported=True,
            model=None,
            info=False
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                MockModelManager.return_value = mock_manager

                result = list_command(args)

                # Should return success with no models message
                assert result == 0

    def test_list_imported_legacy_config(self, mock_config, tmp_path):
        """Test listing with legacy single-server config (lines 882-902)."""
        # Legacy config without local_llm_servers
        config_data = {
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1",
                "model_name": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
            }
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        args = Namespace(
            action='list',
            imported=True,
            model=None,
            info=False
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True
                mock_manager.get_model_info.return_value = {'size_gb': '3.8'}
                MockModelManager.return_value = mock_manager

                result = list_command(args)

                # Should return success
                assert result == 0
                # Should check if model is downloaded
                mock_manager.is_model_downloaded.assert_called_with("Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")

    def test_list_imported_legacy_no_model(self, mock_config, tmp_path):
        """Test legacy config with no model_name (lines 886-889)."""
        config_data = {
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1"
                # No model_name field
            }
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        args = Namespace(
            action='list',
            imported=True,
            model=None,
            info=False
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                MockModelManager.return_value = mock_manager

                result = list_command(args)

                # Should return success with no models message
                assert result == 0

    def test_list_imported_model_not_downloaded(self, mock_config, tmp_path):
        """Test listing when model is imported but not downloaded (lines 862-866)."""
        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    "model_dir": "bartowski--Llama-3.3-70B-Instruct-GGUF",
                    "gguf_file": "model-Q5_K_M.gguf"
                }
            ]
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        args = Namespace(
            action='list',
            imported=True,
            model=None,
            info=False
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                # Model not downloaded - is_model_downloaded returns False
                mock_manager.is_model_downloaded.return_value = False
                MockModelManager.return_value = mock_manager

                result = list_command(args)

                # Should return success (shows model without size)
                assert result == 0
