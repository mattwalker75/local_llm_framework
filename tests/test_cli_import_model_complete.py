"""
Comprehensive tests for import_model_command to improve CLI coverage.

Targets lines 1047-1154 in cli.py (import_model_command function).
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from argparse import Namespace

from llf.cli import import_model_command
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


class TestImportModelCommand:
    """Test import_model_command comprehensive coverage (lines 1016-1154)."""

    def test_import_single_q5km_file(self, mock_config, tmp_path):
        """Test importing model with single Q5_K_M GGUF file (lines 1047-1055)."""
        args = Namespace(model_name="test/model")

        # Create model directory with Q5_K_M GGUF file
        model_path = mock_config.model_dir / "test--model"
        model_path.mkdir(parents=True, exist_ok=True)
        (model_path / "model-q5_k_m.gguf").write_text("fake model")

        # Create config with multi-server setup
        config_data = {
            "local_llm_servers": [
                {
                    "name": "default",
                    "llama_server_path": "../llama.cpp/build/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "model_dir": None,
                    "gguf_file": None
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1",
                "model_name": "default/model"
            }
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True
                mock_manager.get_model_info.return_value = {'path': str(model_path)}
                MockModelManager.return_value = mock_manager

                result = import_model_command(args)

                # Should return success
                assert result == 0

                # Check config was updated
                with open(mock_config.config_file, 'r') as f:
                    updated_config = json.load(f)

                # Default server should be updated
                assert updated_config['local_llm_servers'][0]['model_dir'] == 'test--model'
                assert updated_config['local_llm_servers'][0]['gguf_file'] == 'model-q5_k_m.gguf'

    def test_import_multiple_q5km_files(self, mock_config, tmp_path):
        """Test importing with multiple Q5_K_M files (lines 1049-1053)."""
        args = Namespace(model_name="test/model")

        # Create model directory with multiple Q5_K_M GGUF files
        model_path = mock_config.model_dir / "test--model"
        model_path.mkdir(parents=True, exist_ok=True)
        (model_path / "model-q5_k_m-00001-of-00003.gguf").write_text("fake model part 1")
        (model_path / "model-q5_k_m-00002-of-00003.gguf").write_text("fake model part 2")
        (model_path / "model-q5_k_m-00003-of-00003.gguf").write_text("fake model part 3")

        # Create config with multi-server setup
        config_data = {
            "local_llm_servers": [
                {
                    "name": "default",
                    "llama_server_path": "../llama.cpp/build/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "model_dir": None,
                    "gguf_file": None
                }
            ]
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True
                mock_manager.get_model_info.return_value = {'path': str(model_path)}
                MockModelManager.return_value = mock_manager

                result = import_model_command(args)

                # Should return success and select first file
                assert result == 0

                # Check config was updated with first file
                with open(mock_config.config_file, 'r') as f:
                    updated_config = json.load(f)

                assert updated_config['local_llm_servers'][0]['gguf_file'] == 'model-q5_k_m-00001-of-00003.gguf'

    def test_import_no_multiserver_config(self, mock_config, tmp_path):
        """Test importing when config has no local_llm_servers (lines 1068-1071)."""
        args = Namespace(model_name="test/model")

        # Create model directory with Q5_K_M GGUF file
        model_path = mock_config.model_dir / "test--model"
        model_path.mkdir(parents=True, exist_ok=True)
        (model_path / "model-q5_k_m.gguf").write_text("fake model")

        # Create config without local_llm_servers
        config_data = {
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1"
            }
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True
                mock_manager.get_model_info.return_value = {'path': str(model_path)}
                MockModelManager.return_value = mock_manager

                result = import_model_command(args)

                # Should return error code
                assert result == 1

    def test_import_update_existing_server(self, mock_config, tmp_path):
        """Test updating existing server with new GGUF file (lines 1093-1098)."""
        args = Namespace(model_name="test/model")

        # Create model directory with Q5_K_M GGUF file
        model_path = mock_config.model_dir / "test--model"
        model_path.mkdir(parents=True, exist_ok=True)
        (model_path / "model-q5_k_m.gguf").write_text("fake model")

        # Create config with existing server for this model
        config_data = {
            "local_llm_servers": [
                {
                    "name": "existing_server",
                    "llama_server_path": "../llama.cpp/build/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "model_dir": "test--model",
                    "gguf_file": "old-file.gguf"
                }
            ]
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True
                mock_manager.get_model_info.return_value = {'path': str(model_path)}
                MockModelManager.return_value = mock_manager

                result = import_model_command(args)

                # Should return success
                assert result == 0

                # Check config was updated
                with open(mock_config.config_file, 'r') as f:
                    updated_config = json.load(f)

                # Existing server should have updated GGUF file
                assert updated_config['local_llm_servers'][0]['gguf_file'] == 'model-q5_k_m.gguf'

    def test_import_first_model_to_default_server(self, mock_config, tmp_path):
        """Test first import updates default server (lines 1099-1107)."""
        args = Namespace(model_name="test/model")

        # Create model directory with Q5_K_M GGUF file
        model_path = mock_config.model_dir / "test--model"
        model_path.mkdir(parents=True, exist_ok=True)
        (model_path / "model-q5_k_m.gguf").write_text("fake model")

        # Create config with default server with null model fields
        config_data = {
            "local_llm_servers": [
                {
                    "name": "default",
                    "llama_server_path": "../llama.cpp/build/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "model_dir": None,
                    "gguf_file": None
                }
            ]
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True
                mock_manager.get_model_info.return_value = {'path': str(model_path)}
                MockModelManager.return_value = mock_manager

                result = import_model_command(args)

                # Should return success
                assert result == 0

                # Check config was updated
                with open(mock_config.config_file, 'r') as f:
                    updated_config = json.load(f)

                # Default server should be updated
                assert updated_config['local_llm_servers'][0]['model_dir'] == 'test--model'
                assert updated_config['local_llm_servers'][0]['gguf_file'] == 'model-q5_k_m.gguf'

    def test_import_add_new_server(self, mock_config, tmp_path):
        """Test adding new server for model (lines 1108-1142)."""
        args = Namespace(model_name="test/newmodel")

        # Create model directory with Q5_K_M GGUF file
        model_path = mock_config.model_dir / "test--newmodel"
        model_path.mkdir(parents=True, exist_ok=True)
        (model_path / "model-q5_k_m.gguf").write_text("fake model")

        # Create config with existing server (not default, not matching)
        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    "llama_server_path": "../llama.cpp/build/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "model_dir": "other--model",
                    "gguf_file": "other.gguf"
                }
            ]
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True
                mock_manager.get_model_info.return_value = {'path': str(model_path)}
                MockModelManager.return_value = mock_manager

                result = import_model_command(args)

                # Should return success
                assert result == 0

                # Check config was updated
                with open(mock_config.config_file, 'r') as f:
                    updated_config = json.load(f)

                # Should have 2 servers now
                assert len(updated_config['local_llm_servers']) == 2

                # New server should be added
                new_server = updated_config['local_llm_servers'][1]
                assert new_server['model_dir'] == 'test--newmodel'
                assert new_server['gguf_file'] == 'model-q5_k_m.gguf'
                assert new_server['server_port'] == 8001  # Next available port

    def test_import_unique_server_name_collision(self, mock_config, tmp_path):
        """Test server name uniqueness when collision occurs (lines 1117-1122)."""
        args = Namespace(model_name="test/newmodel")

        # Create model directory with Q5_K_M GGUF file
        model_path = mock_config.model_dir / "test--newmodel"
        model_path.mkdir(parents=True, exist_ok=True)
        (model_path / "model-q5_k_m.gguf").write_text("fake model")

        # Create config with server that would have same name
        config_data = {
            "local_llm_servers": [
                {
                    "name": "newmodel",  # Will conflict with generated name
                    "llama_server_path": "../llama.cpp/build/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "model_dir": "other--model",
                    "gguf_file": "other.gguf"
                }
            ]
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True
                mock_manager.get_model_info.return_value = {'path': str(model_path)}
                MockModelManager.return_value = mock_manager

                result = import_model_command(args)

                # Should return success
                assert result == 0

                # Check config was updated
                with open(mock_config.config_file, 'r') as f:
                    updated_config = json.load(f)

                # Should have 2 servers now
                assert len(updated_config['local_llm_servers']) == 2

                # New server should have unique name (newmodel-1)
                new_server = updated_config['local_llm_servers'][1]
                assert new_server['name'] == 'newmodel-1'

    def test_import_next_available_port(self, mock_config, tmp_path):
        """Test finding next available port (lines 1111-1114)."""
        args = Namespace(model_name="test/newmodel")

        # Create model directory with Q5_K_M GGUF file
        model_path = mock_config.model_dir / "test--newmodel"
        model_path.mkdir(parents=True, exist_ok=True)
        (model_path / "model-q5_k_m.gguf").write_text("fake model")

        # Create config with servers using ports 8000 and 8001
        config_data = {
            "local_llm_servers": [
                {
                    "name": "server1",
                    "llama_server_path": "../llama.cpp/build/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "model_dir": "model1",
                    "gguf_file": "model1.gguf"
                },
                {
                    "name": "server2",
                    "llama_server_path": "../llama.cpp/build/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8001,
                    "model_dir": "model2",
                    "gguf_file": "model2.gguf"
                }
            ]
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True
                mock_manager.get_model_info.return_value = {'path': str(model_path)}
                MockModelManager.return_value = mock_manager

                result = import_model_command(args)

                # Should return success
                assert result == 0

                # Check config was updated
                with open(mock_config.config_file, 'r') as f:
                    updated_config = json.load(f)

                # New server should have port 8002
                new_server = updated_config['local_llm_servers'][2]
                assert new_server['server_port'] == 8002

    def test_import_case_insensitive_q5km_match(self, mock_config, tmp_path):
        """Test case-insensitive Q5_K_M matching (lines 1036-1038)."""
        args = Namespace(model_name="test/model")

        # Create model directory with uppercase Q5_K_M in filename (lowercase extension)
        model_path = mock_config.model_dir / "test--model"
        model_path.mkdir(parents=True, exist_ok=True)
        (model_path / "MODEL-Q5_K_M.gguf").write_text("fake model")

        # Create config with multi-server setup
        config_data = {
            "local_llm_servers": [
                {
                    "name": "default",
                    "llama_server_path": "../llama.cpp/build/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "model_dir": None,
                    "gguf_file": None
                }
            ]
        }

        with open(mock_config.config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True
                mock_manager.get_model_info.return_value = {'path': str(model_path)}
                MockModelManager.return_value = mock_manager

                result = import_model_command(args)

                # Should return success
                assert result == 0

                # Check config was updated
                with open(mock_config.config_file, 'r') as f:
                    updated_config = json.load(f)

                # Should find uppercase Q5_K_M in filename
                assert updated_config['local_llm_servers'][0]['gguf_file'] == 'MODEL-Q5_K_M.gguf'
