"""
Comprehensive tests for export_model_command to improve CLI coverage.

Targets lines 1167-1250 in cli.py (export_model_command function).
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from argparse import Namespace

from llf.cli import export_model_command
from llf.config import Config


@pytest.fixture
def mock_config(tmp_path):
    """Create mock config for testing."""
    config = Config()
    config.config_file = tmp_path / "config.json"
    config.DEFAULT_CONFIG_FILE = tmp_path / "config.json"
    config.model_dir = tmp_path / "models"
    config.model_dir.mkdir(parents=True, exist_ok=True)
    return config


class TestExportModelCommand:
    """Test export_model_command comprehensive coverage (lines 1167-1250)."""

    def test_export_no_multiserver_config(self, mock_config, tmp_path):
        """Test exporting when config has no local_llm_servers (lines 1178-1181)."""
        args = Namespace(model_name="test/model")

        # Create config without local_llm_servers
        config_data = {
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1"
            }
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            result = export_model_command(args)

            # Should return error code
            assert result == 1

    def test_export_model_not_found(self, mock_config, tmp_path):
        """Test exporting model that isn't in config (lines 1201-1204)."""
        args = Namespace(model_name="test/model")

        # Create config with different model
        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    "model_dir": "other--model",
                    "gguf_file": "other.gguf",
                    "server_port": 8000
                }
            ]
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            mock_config.backup_config = Mock(return_value=str(tmp_path / "backup.json"))

            result = export_model_command(args)

            # Should return success (nothing to export)
            assert result == 0

    def test_export_last_model_resets_to_default(self, mock_config, tmp_path):
        """Test exporting last model resets config to default (lines 1213-1227)."""
        args = Namespace(model_name="test/model")

        # Create config with single server
        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    "model_dir": "test--model",
                    "gguf_file": "model.gguf",
                    "server_port": 8001
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1",
                "model_name": "test/model"
            }
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            mock_config.backup_config = Mock(return_value=str(tmp_path / "backup.json"))

            result = export_model_command(args)

            # Should return success
            assert result == 0

            # Check config was reset to default
            with open(mock_config.config_file, 'r') as f:
                updated_config = json.load(f)

            # Should have 1 server reset to default
            assert len(updated_config['local_llm_servers']) == 1
            assert updated_config['local_llm_servers'][0]['name'] == 'default'
            assert updated_config['local_llm_servers'][0]['model_dir'] is None
            assert updated_config['local_llm_servers'][0]['gguf_file'] is None
            assert updated_config['local_llm_servers'][0]['server_port'] == 8000
            # model_name should be cleared
            assert updated_config['llm_endpoint']['model_name'] is None

    def test_export_one_of_multiple_servers(self, mock_config, tmp_path):
        """Test exporting one server when multiple exist (lines 1228-1236)."""
        args = Namespace(model_name="test/model1")

        # Create config with multiple servers
        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    "model_dir": "test--model1",
                    "gguf_file": "model1.gguf",
                    "server_port": 8000
                },
                {
                    "name": "server2",
                    "model_dir": "test--model2",
                    "gguf_file": "model2.gguf",
                    "server_port": 8001
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1",
                "model_name": "test/model2"
            }
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            mock_config.backup_config = Mock(return_value=str(tmp_path / "backup.json"))

            result = export_model_command(args)

            # Should return success
            assert result == 0

            # Check config - should have only server2 left
            with open(mock_config.config_file, 'r') as f:
                updated_config = json.load(f)

            assert len(updated_config['local_llm_servers']) == 1
            assert updated_config['local_llm_servers'][0]['name'] == 'server2'
            # model_name should NOT be cleared (different model)
            assert updated_config['llm_endpoint']['model_name'] == 'test/model2'

    def test_export_multiple_servers_same_model(self, mock_config, tmp_path):
        """Test exporting when multiple servers use same model (lines 1188-1199)."""
        args = Namespace(model_name="test/model")

        # Create config with multiple servers using same model
        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    "model_dir": "test--model",
                    "gguf_file": "model1.gguf",
                    "server_port": 8000
                },
                {
                    "name": "server2",
                    "model_dir": "test--model",
                    "gguf_file": "model2.gguf",
                    "server_port": 8001
                },
                {
                    "name": "server3",
                    "model_dir": "other--model",
                    "gguf_file": "other.gguf",
                    "server_port": 8002
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1",
                "model_name": "test/model"
            }
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            mock_config.backup_config = Mock(return_value=str(tmp_path / "backup.json"))

            result = export_model_command(args)

            # Should return success
            assert result == 0

            # Check config - should have only server3 left
            with open(mock_config.config_file, 'r') as f:
                updated_config = json.load(f)

            assert len(updated_config['local_llm_servers']) == 1
            assert updated_config['local_llm_servers'][0]['name'] == 'server3'
            # model_name should be cleared (matching model)
            assert updated_config['llm_endpoint']['model_name'] is None

    def test_export_clears_matching_model_name(self, mock_config, tmp_path):
        """Test that model_name is cleared when it matches exported model (lines 1239-1241)."""
        args = Namespace(model_name="test/model")

        # Create config where llm_endpoint.model_name matches
        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    "model_dir": "test--model",
                    "gguf_file": "model.gguf",
                    "server_port": 8000
                },
                {
                    "name": "server2",
                    "model_dir": "other--model",
                    "gguf_file": "other.gguf",
                    "server_port": 8001
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1",
                "model_name": "test/model"
            }
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            mock_config.backup_config = Mock(return_value=str(tmp_path / "backup.json"))

            result = export_model_command(args)

            # Should return success
            assert result == 0

            # Check that model_name was cleared
            with open(mock_config.config_file, 'r') as f:
                updated_config = json.load(f)

            assert updated_config['llm_endpoint']['model_name'] is None

    def test_export_model_dir_with_path(self, mock_config, tmp_path):
        """Test export when model_dir contains path separators (lines 1193-1196)."""
        args = Namespace(model_name="test/model")

        # Create config with model_dir as path
        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    "model_dir": "some/path/test--model",
                    "gguf_file": "model.gguf",
                    "server_port": 8000
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1"
            }
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            mock_config.backup_config = Mock(return_value=str(tmp_path / "backup.json"))

            result = export_model_command(args)

            # Should return success
            assert result == 0

            # Check config was reset (last model)
            with open(mock_config.config_file, 'r') as f:
                updated_config = json.load(f)

            # Should be reset to default
            assert updated_config['local_llm_servers'][0]['model_dir'] is None

    def test_export_preserves_backup(self, mock_config, tmp_path):
        """Test that backup is created before export (lines 1206-1208)."""
        args = Namespace(model_name="test/model")

        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    "model_dir": "test--model",
                    "gguf_file": "model.gguf",
                    "server_port": 8000
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1"
            }
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            mock_backup = Mock(return_value=str(tmp_path / "backup.json"))
            mock_config.backup_config = mock_backup

            result = export_model_command(args)

            # Should return success
            assert result == 0
            # Backup should have been called
            mock_backup.assert_called_once_with(mock_config.config_file)
