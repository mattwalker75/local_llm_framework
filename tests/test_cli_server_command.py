"""
Comprehensive tests for server_command to improve CLI coverage.

Targets:
- server_command (lines 1272-1283, 1289-1292, 1300, 1303) - routing and validation
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace

from llf.cli import server_command
from llf.config import Config


@pytest.fixture
def mock_config(tmp_path):
    """Create mock config for testing."""
    config = Config()
    config.config_file = tmp_path / "config.json"
    config.model_dir = tmp_path / "models"
    config.model_dir.mkdir(parents=True, exist_ok=True)
    config.api_base_url = "http://localhost:8000/v1"
    config.server_port = 8000
    config.server_host = "127.0.0.1"
    return config


class TestServerCommandNoLocalConfig:
    """Test server_command when local server is not configured (lines 1272-1283)."""

    def test_start_without_local_server_config(self, mock_config):
        """Test 'start' command without local server config shows error (lines 1272-1283)."""
        args = Namespace(action='start', share=False)

        with patch('llf.cli.get_config', return_value=mock_config):
            # Mock has_local_server_config to return False
            mock_config.has_local_server_config = Mock(return_value=False)

            result = server_command(args)

            # Should return error code
            assert result == 1
            # Should have checked for local config
            mock_config.has_local_server_config.assert_called_once()

    def test_stop_without_local_server_config(self, mock_config):
        """Test 'stop' command without local server config shows error."""
        args = Namespace(action='stop')

        with patch('llf.cli.get_config', return_value=mock_config):
            mock_config.has_local_server_config = Mock(return_value=False)

            result = server_command(args)

            # Should return error code
            assert result == 1

    def test_restart_without_local_server_config(self, mock_config):
        """Test 'restart' command without local server config shows error."""
        args = Namespace(action='restart', share=False)

        with patch('llf.cli.get_config', return_value=mock_config):
            mock_config.has_local_server_config = Mock(return_value=False)

            result = server_command(args)

            # Should return error code
            assert result == 1


class TestServerCommandModelOverrides:
    """Test server_command model override flags (lines 1286-1292)."""

    def test_huggingface_model_override(self, mock_config):
        """Test --huggingface-model flag overrides config (lines 1286-1288)."""
        args = Namespace(
            action='list',
            huggingface_model='override/model'
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                with patch('llf.cli.LLMRuntime') as MockRuntime:
                    # Mock list_servers_command
                    with patch('llf.cli.list_servers_command', return_value=0):
                        mock_manager = Mock()
                        MockModelManager.return_value = mock_manager

                        mock_runtime = Mock()
                        MockRuntime.return_value = mock_runtime

                        result = server_command(args)

                        # Should return success
                        assert result == 0
                        # Config should have been updated
                        assert mock_config.model_name == 'override/model'
                        assert mock_config.custom_model_dir is None

    def test_gguf_dir_and_file_override(self, mock_config):
        """Test --gguf-dir and --gguf-file flags override config (lines 1289-1292)."""
        args = Namespace(
            action='list',
            gguf_dir='custom_dir',
            gguf_file='custom_model.gguf',
            huggingface_model=None
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                with patch('llf.cli.LLMRuntime') as MockRuntime:
                    with patch('llf.cli.list_servers_command', return_value=0):
                        mock_manager = Mock()
                        MockModelManager.return_value = mock_manager

                        mock_runtime = Mock()
                        MockRuntime.return_value = mock_runtime

                        result = server_command(args)

                        # Should return success
                        assert result == 0
                        # Config should have been updated
                        assert mock_config.custom_model_dir == mock_config.model_dir / 'custom_dir'
                        assert mock_config.gguf_file == 'custom_model.gguf'


class TestServerCommandRouting:
    """Test server_command action routing (lines 1299-1303)."""

    def test_list_action_routing(self, mock_config):
        """Test 'list' action routes to list_servers_command (line 1300)."""
        args = Namespace(action='list')

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                with patch('llf.cli.LLMRuntime') as MockRuntime:
                    with patch('llf.cli.list_servers_command') as mock_list_servers:
                        mock_list_servers.return_value = 0

                        mock_manager = Mock()
                        MockModelManager.return_value = mock_manager

                        mock_runtime = Mock()
                        MockRuntime.return_value = mock_runtime

                        result = server_command(args)

                        # Should return success
                        assert result == 0
                        # Should have called list_servers_command
                        mock_list_servers.assert_called_once_with(mock_config, mock_runtime)

    def test_switch_action_routing(self, mock_config):
        """Test 'switch' action routes to switch_server_command (line 1303)."""
        args = Namespace(action='switch', server_name='test_server')

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                with patch('llf.cli.LLMRuntime') as MockRuntime:
                    with patch('llf.cli.switch_server_command') as mock_switch_server:
                        mock_switch_server.return_value = 0

                        mock_manager = Mock()
                        MockModelManager.return_value = mock_manager

                        mock_runtime = Mock()
                        MockRuntime.return_value = mock_runtime

                        result = server_command(args)

                        # Should return success
                        assert result == 0
                        # Should have called switch_server_command
                        mock_switch_server.assert_called_once_with(mock_config, args)

    def test_status_action_routing(self, mock_config):
        """Test 'status' action routes to status_server_command."""
        args = Namespace(action='status', name=None)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                with patch('llf.cli.LLMRuntime') as MockRuntime:
                    with patch('llf.cli.status_server_command') as mock_status_server:
                        mock_status_server.return_value = 0

                        mock_manager = Mock()
                        MockModelManager.return_value = mock_manager

                        mock_runtime = Mock()
                        MockRuntime.return_value = mock_runtime

                        result = server_command(args)

                        # Should return success
                        assert result == 0
                        # Should have called status_server_command
                        mock_status_server.assert_called_once_with(mock_config, mock_runtime, args)

    def test_start_action_routing_with_local_config(self, mock_config):
        """Test 'start' action routes to start_server_command when local config exists."""
        args = Namespace(action='start', share=False, name=None, daemon=False)

        with patch('llf.cli.get_config', return_value=mock_config):
            # Mock has_local_server_config to return True
            mock_config.has_local_server_config = Mock(return_value=True)

            with patch('llf.cli.ModelManager') as MockModelManager:
                with patch('llf.cli.LLMRuntime') as MockRuntime:
                    with patch('llf.cli.start_server_command') as mock_start_server:
                        mock_start_server.return_value = 0

                        mock_manager = Mock()
                        MockModelManager.return_value = mock_manager

                        mock_runtime = Mock()
                        MockRuntime.return_value = mock_runtime

                        result = server_command(args)

                        # Should return success
                        assert result == 0
                        # Should have called start_server_command
                        mock_start_server.assert_called_once_with(
                            mock_config, mock_runtime, mock_manager, args
                        )

    def test_stop_action_routing_with_local_config(self, mock_config):
        """Test 'stop' action routes to stop_server_command when local config exists."""
        args = Namespace(action='stop', name=None)

        with patch('llf.cli.get_config', return_value=mock_config):
            mock_config.has_local_server_config = Mock(return_value=True)

            with patch('llf.cli.ModelManager') as MockModelManager:
                with patch('llf.cli.LLMRuntime') as MockRuntime:
                    with patch('llf.cli.stop_server_command') as mock_stop_server:
                        mock_stop_server.return_value = 0

                        mock_manager = Mock()
                        MockModelManager.return_value = mock_manager

                        mock_runtime = Mock()
                        MockRuntime.return_value = mock_runtime

                        result = server_command(args)

                        # Should return success
                        assert result == 0
                        # Should have called stop_server_command
                        mock_stop_server.assert_called_once_with(mock_config, mock_runtime, args)


class TestServerCommandExceptionHandling:
    """Test server_command exception handling."""

    def test_exception_during_command_execution(self, mock_config):
        """Test that exceptions are caught and return error code (lines 1404-1407)."""
        args = Namespace(action='list')

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                with patch('llf.cli.LLMRuntime') as MockRuntime:
                    with patch('llf.cli.list_servers_command') as mock_list_servers:
                        # Make list_servers_command raise an exception inside try block
                        mock_list_servers.side_effect = Exception("Test error")

                        mock_manager = Mock()
                        MockModelManager.return_value = mock_manager

                        mock_runtime = Mock()
                        MockRuntime.return_value = mock_runtime

                        result = server_command(args)

                        # Should return error code
                        assert result == 1
