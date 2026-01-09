"""
Unit tests for model import/export commands (multi-server only).
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from llf.cli import import_model_command, export_model_command, list_command


class TestModelImport:
    """Test model import command."""

    @pytest.fixture
    def mock_args(self):
        """Mock arguments for model import."""
        args = Mock()
        args.model_name = "Qwen/Qwen2.5-32B-Instruct-GGUF"
        return args

    @pytest.fixture
    def temp_config_multi(self, tmp_path):
        """Create temporary multi-server config."""
        config_data = {
            "local_llm_servers": [
                {
                    "name": "default",
                    "llama_server_path": "/path/to/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "healthcheck_interval": 2.0,
                    "auto_start": False,
                    "model_dir": None,
                    "gguf_file": None
                },
                {
                    "name": "server2",
                    "llama_server_path": "/path/to/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8001,
                    "healthcheck_interval": 2.0,
                    "auto_start": False,
                    "model_dir": None,
                    "gguf_file": None
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://127.0.0.1:8000/v1",
                "api_key": "EMPTY",
                "model_name": None,
                "default_local_server": "default"
            },
            "model_dir": "/path/to/models",
            "cache_dir": "/path/to/.cache"
        }

        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        return config_file, config_data

    def test_import_multi_server_success(self, mock_args, temp_config_multi, tmp_path):
        """Test successful import to multi-server configuration."""
        config_file, _ = temp_config_multi

        # Mock config and model manager
        with patch('llf.cli.get_config') as mock_get_config, \
             patch('llf.cli.ModelManager') as mock_model_manager_class, \
             patch('llf.cli.console'):

            # Setup mock config
            mock_config = Mock()
            mock_config.DEFAULT_CONFIG_FILE = config_file
            mock_config.config_file = config_file
            mock_config.backups_dir = tmp_path / "backups"
            mock_config.backups_dir.mkdir(exist_ok=True)
            mock_get_config.return_value = mock_config

            # Setup mock model manager
            mock_model_manager = Mock()
            mock_model_manager.is_model_downloaded.return_value = True

            model_info = {
                'path': tmp_path / "models" / "Qwen--Qwen2.5-32B-Instruct-GGUF",
                'name': "Qwen/Qwen2.5-32B-Instruct-GGUF"
            }
            model_info['path'].mkdir(parents=True, exist_ok=True)

            # Create a mock GGUF file
            gguf_file_path = model_info['path'] / "Qwen2.5-32B-Instruct-Q5_K_M.gguf"
            gguf_file_path.touch()

            mock_model_manager.get_model_info.return_value = model_info
            mock_model_manager_class.return_value = mock_model_manager

            # Mock backup_config
            mock_config.backup_config.return_value = tmp_path / "backups" / "config_backup.json"

            # Run import
            result = import_model_command(mock_args)

            # Verify success
            assert result == 0

            # Verify config was updated
            with open(config_file, 'r') as f:
                updated_config = json.load(f)

            # The default server should be updated (not adding a new server since default has null model fields)
            assert len(updated_config['local_llm_servers']) == 2

            # Find the default server
            default_server = None
            for server in updated_config['local_llm_servers']:
                if server.get('name') == 'default':
                    default_server = server
                    break

            assert default_server is not None
            assert default_server['model_dir'] == "Qwen--Qwen2.5-32B-Instruct-GGUF"
            assert default_server['gguf_file'] == "Qwen2.5-32B-Instruct-Q5_K_M.gguf"
            assert default_server['server_port'] == 8000  # Should keep the default port

            # Verify that model_name was NOT updated (should only be updated via 'llf server switch')
            assert updated_config['llm_endpoint']['model_name'] is None

    def test_import_model_not_found(self, mock_args, temp_config_multi, tmp_path):
        """Test import when model is not downloaded."""
        config_file, _ = temp_config_multi

        with patch('llf.cli.get_config') as mock_get_config, \
             patch('llf.cli.ModelManager') as mock_model_manager_class, \
             patch('llf.cli.console'):

            mock_config = Mock()
            mock_config.DEFAULT_CONFIG_FILE = config_file
            mock_get_config.return_value = mock_config

            mock_model_manager = Mock()
            mock_model_manager.is_model_downloaded.return_value = False
            mock_model_manager_class.return_value = mock_model_manager

            result = import_model_command(mock_args)

            assert result == 1

    def test_import_no_gguf_file(self, mock_args, temp_config_multi, tmp_path):
        """Test import when no Q5_K_M GGUF file is found."""
        config_file, _ = temp_config_multi

        with patch('llf.cli.get_config') as mock_get_config, \
             patch('llf.cli.ModelManager') as mock_model_manager_class, \
             patch('llf.cli.console'):

            mock_config = Mock()
            mock_config.DEFAULT_CONFIG_FILE = config_file
            mock_get_config.return_value = mock_config

            mock_model_manager = Mock()
            mock_model_manager.is_model_downloaded.return_value = True

            model_info = {
                'path': tmp_path / "models" / "Qwen--Qwen2.5-32B-Instruct-GGUF",
                'name': "Qwen/Qwen2.5-32B-Instruct-GGUF"
            }
            model_info['path'].mkdir(parents=True, exist_ok=True)

            # Don't create any GGUF files

            mock_model_manager.get_model_info.return_value = model_info
            mock_model_manager_class.return_value = mock_model_manager

            result = import_model_command(mock_args)

            assert result == 1

    def test_import_multi_server_update_existing(self, mock_args, temp_config_multi, tmp_path):
        """Test import to multi-server updates existing server if model already exists."""
        config_file, config_data = temp_config_multi

        # Pre-add the Qwen model to one of the servers
        with open(config_file, 'r') as f:
            config_data = json.load(f)

        config_data['local_llm_servers'][0]['model_dir'] = "Qwen--Qwen2.5-32B-Instruct-GGUF"
        config_data['local_llm_servers'][0]['gguf_file'] = "old-file.gguf"

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config') as mock_get_config, \
             patch('llf.cli.ModelManager') as mock_model_manager_class, \
             patch('llf.cli.console'):

            # Setup mock config
            mock_config = Mock()
            mock_config.DEFAULT_CONFIG_FILE = config_file
            mock_config.config_file = config_file
            mock_config.backups_dir = tmp_path / "backups"
            mock_config.backups_dir.mkdir(exist_ok=True)
            mock_get_config.return_value = mock_config

            # Setup mock model manager
            mock_model_manager = Mock()
            mock_model_manager.is_model_downloaded.return_value = True

            model_info = {
                'path': tmp_path / "models" / "Qwen--Qwen2.5-32B-Instruct-GGUF",
                'name': "Qwen/Qwen2.5-32B-Instruct-GGUF"
            }
            model_info['path'].mkdir(parents=True, exist_ok=True)

            # Create a mock GGUF file
            gguf_file_path = model_info['path'] / "Qwen2.5-32B-Instruct-Q5_K_M.gguf"
            gguf_file_path.touch()

            mock_model_manager.get_model_info.return_value = model_info
            mock_model_manager_class.return_value = mock_model_manager

            # Mock backup_config
            mock_config.backup_config.return_value = tmp_path / "backups" / "config_backup.json"

            # Run import
            result = import_model_command(mock_args)

            # Verify success
            assert result == 0

            # Verify config was updated
            with open(config_file, 'r') as f:
                updated_config = json.load(f)

            # Should still have 2 servers (not added a duplicate)
            assert len(updated_config['local_llm_servers']) == 2

            # The first server should have the updated GGUF file
            assert updated_config['local_llm_servers'][0]['model_dir'] == "Qwen--Qwen2.5-32B-Instruct-GGUF"
            assert updated_config['local_llm_servers'][0]['gguf_file'] == "Qwen2.5-32B-Instruct-Q5_K_M.gguf"

    def test_import_multipart_gguf_selects_first(self, mock_args, temp_config_multi, tmp_path):
        """Test import selects first file in multi-part GGUF series."""
        config_file, _ = temp_config_multi

        with patch('llf.cli.get_config') as mock_get_config, \
             patch('llf.cli.ModelManager') as mock_model_manager_class, \
             patch('llf.cli.console'):

            # Setup mock config
            mock_config = Mock()
            mock_config.DEFAULT_CONFIG_FILE = config_file
            mock_config.config_file = config_file
            mock_config.backups_dir = tmp_path / "backups"
            mock_config.backups_dir.mkdir(exist_ok=True)
            mock_get_config.return_value = mock_config

            # Setup mock model manager
            mock_model_manager = Mock()
            mock_model_manager.is_model_downloaded.return_value = True

            model_info = {
                'path': tmp_path / "models" / "Qwen--Qwen2.5-32B-Instruct-GGUF",
                'name': "Qwen/Qwen2.5-32B-Instruct-GGUF"
            }
            model_info['path'].mkdir(parents=True, exist_ok=True)

            # Create multi-part GGUF files (out of order to test sorting)
            (model_info['path'] / "qwen2.5-32b-instruct-q5_k_m-00006-of-00006.gguf").touch()
            (model_info['path'] / "qwen2.5-32b-instruct-q5_k_m-00003-of-00006.gguf").touch()
            (model_info['path'] / "qwen2.5-32b-instruct-q5_k_m-00001-of-00006.gguf").touch()
            (model_info['path'] / "qwen2.5-32b-instruct-q5_k_m-00004-of-00006.gguf").touch()

            mock_model_manager.get_model_info.return_value = model_info
            mock_model_manager_class.return_value = mock_model_manager

            # Mock backup_config
            mock_config.backup_config.return_value = tmp_path / "backups" / "config_backup.json"

            # Run import
            result = import_model_command(mock_args)

            # Verify success
            assert result == 0

            # Verify the first file in the series was selected
            with open(config_file, 'r') as f:
                updated_config = json.load(f)

            # Find the new server with our model
            new_server = None
            for server in updated_config['local_llm_servers']:
                if server.get('model_dir') == "Qwen--Qwen2.5-32B-Instruct-GGUF":
                    new_server = server
                    break

            # Should select 00001, not 00003, 00004, or 00006
            assert new_server['gguf_file'] == "qwen2.5-32b-instruct-q5_k_m-00001-of-00006.gguf"

    def test_import_adds_new_server_when_default_has_model(self, mock_args, tmp_path):
        """Test that import adds a new server when default server already has a model."""
        # Create config with default server that already has a model
        config_data = {
            "local_llm_servers": [
                {
                    "name": "default",
                    "llama_server_path": "/path/to/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "healthcheck_interval": 2.0,
                    "auto_start": False,
                    "model_dir": "ExistingModel--GGUF",
                    "gguf_file": "existing-model.gguf"
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://127.0.0.1:8000/v1",
                "api_key": "EMPTY",
                "model_name": None,
                "default_local_server": "default"
            },
            "model_dir": "/path/to/models",
            "cache_dir": "/path/to/.cache"
        }

        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        with patch('llf.cli.get_config') as mock_get_config, \
             patch('llf.cli.ModelManager') as mock_model_manager_class, \
             patch('llf.cli.console'):

            mock_config = Mock()
            mock_config.DEFAULT_CONFIG_FILE = config_file
            mock_config.config_file = config_file
            mock_config.backups_dir = tmp_path / "backups"
            mock_config.backups_dir.mkdir(exist_ok=True)
            mock_get_config.return_value = mock_config

            mock_model_manager = Mock()
            mock_model_manager.is_model_downloaded.return_value = True

            model_info = {
                'path': tmp_path / "Qwen--Qwen2.5-32B-Instruct-GGUF",
                'size_gb': 21.66
            }
            model_info['path'].mkdir(parents=True, exist_ok=True)
            (model_info['path'] / "Qwen2.5-32B-Instruct-Q5_K_M.gguf").touch()

            mock_model_manager.get_model_info.return_value = model_info
            mock_model_manager_class.return_value = mock_model_manager

            mock_config.backup_config.return_value = tmp_path / "backups" / "config_backup.json"

            result = import_model_command(mock_args)

            assert result == 0

            with open(config_file, 'r') as f:
                updated_config = json.load(f)

            # Should add a new server instead of updating default
            assert len(updated_config['local_llm_servers']) == 2

            # Default server should still have its original model
            default_server = updated_config['local_llm_servers'][0]
            assert default_server['name'] == 'default'
            assert default_server['model_dir'] == "ExistingModel--GGUF"
            assert default_server['gguf_file'] == "existing-model.gguf"

            # New server should be added
            new_server = updated_config['local_llm_servers'][1]
            assert new_server['model_dir'] == "Qwen--Qwen2.5-32B-Instruct-GGUF"
            assert new_server['gguf_file'] == "Qwen2.5-32B-Instruct-Q5_K_M.gguf"
            assert new_server['server_port'] == 8001  # Next available port


class TestModelExport:
    """Test model export command."""

    @pytest.fixture
    def mock_args(self):
        """Mock arguments for model export."""
        args = Mock()
        args.model_name = "Qwen/Qwen2.5-32B-Instruct-GGUF"
        return args

    @pytest.fixture
    def temp_config_multi_with_model(self, tmp_path):
        """Create temporary multi-server config with multiple models configured."""
        config_data = {
            "local_llm_servers": [
                {
                    "name": "default",
                    "llama_server_path": "/path/to/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "healthcheck_interval": 2.0,
                    "auto_start": False,
                    "model_dir": "Qwen--Qwen2.5-32B-Instruct-GGUF",
                    "gguf_file": "Qwen2.5-32B-Instruct-Q5_K_M.gguf"
                },
                {
                    "name": "server2",
                    "llama_server_path": "/path/to/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8001,
                    "healthcheck_interval": 2.0,
                    "auto_start": False,
                    "model_dir": None,
                    "gguf_file": None
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://127.0.0.1:8000/v1",
                "api_key": "EMPTY",
                "model_name": "Qwen/Qwen2.5-32B-Instruct-GGUF",
                "default_local_server": "default"
            },
            "model_dir": "/path/to/models",
            "cache_dir": "/path/to/.cache"
        }

        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        return config_file, config_data

    @pytest.fixture
    def temp_config_multi_no_model(self, tmp_path):
        """Create temporary multi-server config without a model."""
        config_data = {
            "local_llm_servers": [
                {
                    "name": "default",
                    "llama_server_path": "/path/to/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "healthcheck_interval": 2.0,
                    "auto_start": False,
                    "model_dir": None,
                    "gguf_file": None
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://127.0.0.1:8000/v1",
                "api_key": "EMPTY",
                "model_name": None,
                "default_local_server": "default"
            },
            "model_dir": "/path/to/models",
            "cache_dir": "/path/to/.cache"
        }

        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        return config_file, config_data

    def test_export_multi_server_success(self, mock_args, temp_config_multi_with_model, tmp_path):
        """Test successful export from multi-server configuration with multiple servers."""
        config_file, _ = temp_config_multi_with_model

        with patch('llf.cli.get_config') as mock_get_config, \
             patch('llf.cli.console'):

            mock_config = Mock()
            mock_config.DEFAULT_CONFIG_FILE = config_file
            mock_config.config_file = config_file
            mock_config.backups_dir = tmp_path / "backups"
            mock_config.backups_dir.mkdir(exist_ok=True)
            mock_get_config.return_value = mock_config

            # Mock backup_config
            mock_config.backup_config.return_value = tmp_path / "backups" / "config_backup.json"

            result = export_model_command(mock_args)

            assert result == 0

            # Verify config was updated
            with open(config_file, 'r') as f:
                updated_config = json.load(f)

            # The server with the model should be removed (only 1 server remaining)
            assert len(updated_config['local_llm_servers']) == 1
            assert updated_config['local_llm_servers'][0]['name'] == 'server2'
            assert updated_config['llm_endpoint']['model_name'] is None

    def test_export_model_name_mismatch(self, temp_config_multi_with_model, tmp_path):
        """Test export returns 0 when model name doesn't match any configured servers."""
        config_file, _ = temp_config_multi_with_model

        with patch('llf.cli.get_config') as mock_get_config, \
             patch('llf.cli.console'):

            mock_config = Mock()
            mock_config.DEFAULT_CONFIG_FILE = config_file
            mock_config.config_file = config_file
            mock_config.backups_dir = tmp_path / "backups"
            mock_config.backups_dir.mkdir(exist_ok=True)
            mock_get_config.return_value = mock_config

            # Create args with wrong model name
            args = Mock()
            args.model_name = "WrongModel/Name"

            result = export_model_command(args)

            assert result == 0  # Should succeed with "nothing to export" message

    def test_export_no_model_configured(self, temp_config_multi_no_model, tmp_path):
        """Test export when no model is configured (returns 0, nothing to do)."""
        config_file, _ = temp_config_multi_no_model

        with patch('llf.cli.get_config') as mock_get_config, \
             patch('llf.cli.console'):

            mock_config = Mock()
            mock_config.DEFAULT_CONFIG_FILE = config_file
            mock_config.config_file = config_file
            mock_config.backups_dir = tmp_path / "backups"
            mock_config.backups_dir.mkdir(exist_ok=True)
            mock_get_config.return_value = mock_config

            # Create args
            args = Mock()
            args.model_name = "Qwen/Qwen2.5-32B-Instruct-GGUF"

            result = export_model_command(args)

            assert result == 0  # Should succeed with "nothing to export" message

    @pytest.fixture
    def temp_config_multi_single_server_with_model(self, tmp_path):
        """Create temporary multi-server config with only ONE server configured with a model."""
        config_data = {
            "local_llm_servers": [
                {
                    "name": "default",
                    "llama_server_path": "/path/to/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8001,
                    "healthcheck_interval": 2.0,
                    "auto_start": False,
                    "model_dir": "Qwen--Qwen2.5-32B-Instruct-GGUF",
                    "gguf_file": "Qwen2.5-32B-Instruct-Q5_K_M.gguf"
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://127.0.0.1:8000/v1",
                "api_key": "EMPTY",
                "model_name": "Qwen/Qwen2.5-32B-Instruct-GGUF",
                "default_local_server": "default"
            },
            "model_dir": "/path/to/models",
            "cache_dir": "/path/to/.cache"
        }

        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        return config_file, config_data

    def test_export_multi_server_single_remaining(self, mock_args, temp_config_multi_single_server_with_model, tmp_path):
        """Test export with only 1 server left - should null out model fields and reset port to 8000."""
        config_file, _ = temp_config_multi_single_server_with_model

        with patch('llf.cli.get_config') as mock_get_config, \
             patch('llf.cli.console'):

            mock_config = Mock()
            mock_config.DEFAULT_CONFIG_FILE = config_file
            mock_config.config_file = config_file
            mock_config.backups_dir = tmp_path / "backups"
            mock_config.backups_dir.mkdir(exist_ok=True)
            mock_get_config.return_value = mock_config

            # Mock backup_config
            mock_config.backup_config.return_value = tmp_path / "backups" / "config_backup.json"

            result = export_model_command(mock_args)

            assert result == 0

            # Verify the config still has multi-server structure with nulled out model
            with open(config_file, 'r') as f:
                updated_config = json.load(f)

            assert 'local_llm_servers' in updated_config
            assert len(updated_config['local_llm_servers']) == 1
            assert updated_config['local_llm_servers'][0]['model_dir'] is None
            assert updated_config['local_llm_servers'][0]['gguf_file'] is None
            assert updated_config['local_llm_servers'][0]['name'] == 'default'  # Reset to default
            assert updated_config['local_llm_servers'][0]['server_port'] == 8000  # Reset to 8000
            assert updated_config['llm_endpoint']['model_name'] is None


class TestModelList:
    """Test model list command with --imported flag."""

    @pytest.fixture
    def temp_config_multi_with_model(self, tmp_path):
        """Create temporary multi-server config with a model configured."""
        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    "llama_server_path": "/path/to/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "healthcheck_interval": 2.0,
                    "auto_start": False,
                    "model_dir": "Qwen--Qwen2.5-32B-Instruct-GGUF",
                    "gguf_file": "Qwen2.5-32B-Instruct-Q5_K_M.gguf"
                },
                {
                    "name": "server2",
                    "llama_server_path": "/path/to/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8001,
                    "healthcheck_interval": 2.0,
                    "auto_start": False,
                    "model_dir": "Qwen--Qwen2.5-32B-Instruct-GGUF",
                    "gguf_file": "Qwen2.5-32B-Instruct-Q5_K_M.gguf"
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://127.0.0.1:8000/v1",
                "api_key": "EMPTY",
                "model_name": "Qwen/Qwen2.5-32B-Instruct-GGUF"
            },
            "model_dir": "/path/to/models",
            "cache_dir": "/path/to/.cache"
        }

        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        return config_file, config_data

    @pytest.fixture
    def temp_config_multi_no_model(self, tmp_path):
        """Create temporary multi-server config without a model."""
        config_data = {
            "local_llm_servers": [
                {
                    "name": "default",
                    "llama_server_path": "../llama.cpp/build/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "healthcheck_interval": 2.0,
                    "model_dir": None,
                    "gguf_file": None
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://127.0.0.1:8000/v1",
                "api_key": "EMPTY",
                "model_name": None
            },
            "model_dir": "models",
            "cache_dir": ".cache"
        }

        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        return config_file, config_data

    def test_list_imported_multi_server(self, temp_config_multi_with_model, tmp_path):
        """Test list --imported with multi-server configuration."""
        config_file, _ = temp_config_multi_with_model

        with patch('llf.cli.get_config') as mock_get_config, \
             patch('llf.cli.ModelManager') as mock_model_manager_class, \
             patch('llf.cli.console'):

            mock_config = Mock()
            mock_config.DEFAULT_CONFIG_FILE = config_file
            mock_config.config_file = config_file
            mock_get_config.return_value = mock_config

            mock_model_manager = Mock()
            mock_model_manager.is_model_downloaded.return_value = True
            mock_model_manager.get_model_info.return_value = {'size_gb': 21.66}
            mock_model_manager_class.return_value = mock_model_manager

            # Create args with imported flag
            args = Mock()
            args.imported = True

            result = list_command(args)

            assert result == 0
            # Verify the ModelManager methods were called
            assert mock_model_manager.is_model_downloaded.called
            assert mock_model_manager.get_model_info.called

    def test_list_imported_no_model(self, temp_config_multi_no_model, tmp_path):
        """Test list --imported when no model is configured."""
        config_file, _ = temp_config_multi_no_model

        with patch('llf.cli.get_config') as mock_get_config, \
             patch('llf.cli.ModelManager') as mock_model_manager_class, \
             patch('llf.cli.console'):

            mock_config = Mock()
            mock_config.DEFAULT_CONFIG_FILE = config_file
            mock_config.config_file = config_file
            mock_get_config.return_value = mock_config

            mock_model_manager = Mock()
            mock_model_manager_class.return_value = mock_model_manager

            # Create args with imported flag
            args = Mock()
            args.imported = True

            result = list_command(args)

            assert result == 0
            # Verify model manager methods were NOT called since no model configured
            assert not mock_model_manager.is_model_downloaded.called
