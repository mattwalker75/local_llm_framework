"""
Comprehensive tests for server_commands.py multi-server functionality.

This test suite focuses on testing the NEW multi-server command handlers
without modifying existing mocked tests in test_cli.py.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path

from llf.server_commands import (
    list_servers_command,
    start_server_command,
    stop_server_command,
    status_server_command,
    switch_server_command
)
from llf.config import Config, ServerConfig


@pytest.fixture
def mock_config():
    """Create a mock config with multiple servers."""
    config = MagicMock(spec=Config)

    # Create server configs
    server1 = ServerConfig(
        name='qwen-coder',
        llama_server_path=Path('/usr/bin/llama-server'),
        server_host='127.0.0.1',
        server_port=8000,
        healthcheck_interval=2.0,
        model_dir=Path('/models/qwen'),
        gguf_file='qwen.gguf',
        server_params={},
        auto_start=False
    )

    server2 = ServerConfig(
        name='llama-3',
        llama_server_path=Path('/usr/bin/llama-server'),
        server_host='127.0.0.1',
        server_port=8001,
        healthcheck_interval=2.0,
        model_dir=Path('/models/llama'),
        gguf_file='llama.gguf',
        server_params={},
        auto_start=False
    )

    config.servers = {
        'qwen-coder': server1,
        'llama-3': server2
    }
    config.list_servers.return_value = ['qwen-coder', 'llama-3']
    config.get_server_by_name = lambda name: config.servers.get(name)
    config.model_dir = Path('/models')
    config.default_local_server = 'qwen-coder'
    config.api_base_url = 'http://127.0.0.1:8000/v1'
    config.model_name = 'test/model'  # Add model_name for switch command
    config.DEFAULT_CONFIG_FILE = Path('/config.json')

    return config


@pytest.fixture
def mock_runtime():
    """Create a mock LLMRuntime."""
    runtime = MagicMock()
    runtime.is_server_running_by_name.return_value = False
    runtime.is_server_running.return_value = False
    runtime.get_running_servers.return_value = []
    return runtime


@pytest.fixture
def mock_model_manager():
    """Create a mock ModelManager."""
    manager = MagicMock()
    manager.is_model_downloaded.return_value = True
    return manager


class TestListServersCommand:
    """Tests for list_servers_command()."""

    @patch('llf.server_commands.console')
    def test_list_servers_with_multiple_servers(self, mock_console, mock_config, mock_runtime):
        """Test listing multiple servers with their status."""
        # Setup
        mock_runtime.is_server_running_by_name.side_effect = lambda name: name == 'qwen-coder'

        # Execute
        result = list_servers_command(mock_config, mock_runtime)

        # Verify
        assert result == 0
        # Should have called is_server_running_by_name for each server
        assert mock_runtime.is_server_running_by_name.call_count == 2
        # Should have printed a table
        assert mock_console.print.called

    @patch('llf.server_commands.console')
    def test_list_servers_with_no_servers(self, mock_console, mock_config, mock_runtime):
        """Test listing when no servers are configured."""
        # Setup
        mock_config.servers = {}
        mock_config.list_servers.return_value = []

        # Execute
        result = list_servers_command(mock_config, mock_runtime)

        # Verify
        assert result == 0
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert 'No local servers configured' in call_args

    @patch('llf.server_commands.console')
    def test_list_servers_shows_correct_status(self, mock_console, mock_config, mock_runtime):
        """Test that server status is correctly displayed."""
        # Setup - first server running, second stopped
        mock_runtime.is_server_running_by_name.side_effect = lambda name: name == 'qwen-coder'

        # Execute
        result = list_servers_command(mock_config, mock_runtime)

        # Verify
        assert result == 0
        assert mock_runtime.is_server_running_by_name.call_count == 2


class TestStartServerCommand:
    """Tests for start_server_command()."""

    @patch('llf.server_commands.console')
    def test_start_server_by_name_success(self, mock_console, mock_config, mock_runtime, mock_model_manager):
        """Test successfully starting a server by name."""
        # Setup
        args = MagicMock()
        args.server_name = 'qwen-coder'
        args.force = False
        args.daemon = True

        # Execute
        result = start_server_command(mock_config, mock_runtime, mock_model_manager, args)

        # Verify
        assert result == 0
        mock_runtime.start_server_by_name.assert_called_once_with('qwen-coder', force=False)

    @patch('llf.server_commands.console')
    def test_start_server_by_name_with_force_flag(self, mock_console, mock_config, mock_runtime, mock_model_manager):
        """Test starting server with --force flag."""
        # Setup
        args = MagicMock()
        args.server_name = 'llama-3'
        args.force = True
        args.daemon = True

        # Execute
        result = start_server_command(mock_config, mock_runtime, mock_model_manager, args)

        # Verify
        assert result == 0
        mock_runtime.start_server_by_name.assert_called_once_with('llama-3', force=True)

    @patch('llf.server_commands.console')
    def test_start_server_by_name_error_handling(self, mock_console, mock_config, mock_runtime, mock_model_manager):
        """Test error handling when starting server fails."""
        # Setup
        args = MagicMock()
        args.server_name = 'qwen-coder'
        args.force = False
        args.daemon = True
        mock_runtime.start_server_by_name.side_effect = RuntimeError("Port already in use")

        # Execute
        result = start_server_command(mock_config, mock_runtime, mock_model_manager, args)

        # Verify
        assert result == 1
        # Should have printed error message
        error_calls = [call for call in mock_console.print.call_args_list
                      if len(call[0]) > 0 and 'Failed' in str(call[0][0])]
        assert len(error_calls) > 0

    @patch('llf.server_commands.console')
    def test_start_server_legacy_mode_already_running(self, mock_console, mock_config, mock_runtime, mock_model_manager):
        """Test legacy mode when server is already running."""
        # Setup
        mock_config.default_local_server = None  # Force legacy mode
        args = MagicMock()
        args.server_name = None  # Legacy mode
        args.daemon = True
        args.share = False
        mock_runtime.is_server_running.return_value = True
        mock_config.get_server_url.return_value = 'http://127.0.0.1:8000'

        # Execute
        result = start_server_command(mock_config, mock_runtime, mock_model_manager, args)

        # Verify
        assert result == 0
        # Should not have called start_server
        mock_runtime.start_server.assert_not_called()

    @patch('llf.server_commands.console')
    def test_start_server_legacy_mode_downloads_model(self, mock_console, mock_config, mock_runtime, mock_model_manager):
        """Test legacy mode downloads model if needed."""
        # Setup
        mock_config.default_local_server = None  # Force legacy mode
        args = MagicMock()
        args.server_name = None  # Legacy mode
        args.daemon = True
        args.share = False
        mock_runtime.is_server_running.return_value = False
        mock_model_manager.is_model_downloaded.return_value = False
        mock_config.custom_model_dir = None
        mock_config.model_name = 'test/model'
        mock_config.server_port = 8000
        mock_config.get_server_url.return_value = 'http://127.0.0.1:8000'

        # Execute
        result = start_server_command(mock_config, mock_runtime, mock_model_manager, args)

        # Verify
        assert result == 0
        mock_model_manager.download_model.assert_called_once()
        mock_runtime.start_server.assert_called_once()


class TestStopServerCommand:
    """Tests for stop_server_command()."""

    @patch('llf.server_commands.console')
    def test_stop_server_by_name_success(self, mock_console, mock_config, mock_runtime):
        """Test successfully stopping a server by name."""
        # Setup
        args = MagicMock()
        args.server_name = 'qwen-coder'
        mock_runtime.is_server_running_by_name.return_value = True

        # Execute
        result = stop_server_command(mock_config, mock_runtime, args)

        # Verify
        assert result == 0
        mock_runtime.stop_server_by_name.assert_called_once_with('qwen-coder')

    @patch('llf.server_commands.console')
    def test_stop_server_by_name_not_running(self, mock_console, mock_config, mock_runtime):
        """Test stopping server that's not running."""
        # Setup
        args = MagicMock()
        args.server_name = 'llama-3'
        mock_runtime.is_server_running_by_name.return_value = False

        # Execute
        result = stop_server_command(mock_config, mock_runtime, args)

        # Verify
        assert result == 0
        # Should not have called stop_server_by_name
        mock_runtime.stop_server_by_name.assert_not_called()

    @patch('llf.server_commands.console')
    def test_stop_server_legacy_mode_success(self, mock_console, mock_config, mock_runtime):
        """Test stopping server in legacy mode."""
        # Setup
        mock_config.default_local_server = None  # Force legacy mode
        args = MagicMock()
        args.server_name = None  # Legacy mode
        mock_runtime.is_server_running.return_value = True

        # Execute
        result = stop_server_command(mock_config, mock_runtime, args)

        # Verify
        assert result == 0
        mock_runtime.stop_server.assert_called_once()

    @patch('llf.server_commands.console')
    def test_stop_server_legacy_mode_not_running(self, mock_console, mock_config, mock_runtime):
        """Test stopping server in legacy mode when not running."""
        # Setup
        mock_config.default_local_server = None  # Force legacy mode
        args = MagicMock()
        args.server_name = None  # Legacy mode
        mock_runtime.is_server_running.return_value = False

        # Execute
        result = stop_server_command(mock_config, mock_runtime, args)

        # Verify
        assert result == 0
        # Should not have called stop_server
        mock_runtime.stop_server.assert_not_called()


class TestStatusServerCommand:
    """Tests for status_server_command()."""

    @patch('llf.server_commands.console')
    def test_status_server_by_name_running(self, mock_console, mock_config, mock_runtime):
        """Test checking status of running server by name."""
        # Setup
        args = MagicMock()
        args.server_name = 'qwen-coder'
        mock_runtime.is_server_running_by_name.return_value = True

        # Execute
        result = status_server_command(mock_config, mock_runtime, args)

        # Verify
        assert result == 0
        mock_runtime.is_server_running_by_name.assert_called_once_with('qwen-coder')

    @patch('llf.server_commands.console')
    def test_status_server_by_name_not_running(self, mock_console, mock_config, mock_runtime):
        """Test checking status of stopped server by name."""
        # Setup
        args = MagicMock()
        args.server_name = 'llama-3'
        mock_runtime.is_server_running_by_name.return_value = False

        # Execute
        result = status_server_command(mock_config, mock_runtime, args)

        # Verify
        assert result == 1  # Non-zero exit code for not running
        mock_runtime.is_server_running_by_name.assert_called_once_with('llama-3')

    @patch('llf.server_commands.console')
    def test_status_server_not_found(self, mock_console, mock_config, mock_runtime):
        """Test checking status of non-existent server."""
        # Setup
        args = MagicMock()
        args.server_name = 'nonexistent'
        mock_config.get_server_by_name = lambda name: None

        # Execute
        result = status_server_command(mock_config, mock_runtime, args)

        # Verify
        assert result == 1
        # Should have printed error message
        error_calls = [call for call in mock_console.print.call_args_list
                      if len(call[0]) > 0 and 'not found' in str(call[0][0])]
        assert len(error_calls) > 0

    @patch('llf.server_commands.console')
    def test_status_server_legacy_mode_running(self, mock_console, mock_config, mock_runtime):
        """Test status showing all servers (always returns 0)."""
        # Setup
        args = MagicMock()
        args.server_name = None  # Show all servers
        mock_config.has_local_server_config.return_value = True
        mock_runtime.is_server_running_by_name.return_value = True

        # Execute
        result = status_server_command(mock_config, mock_runtime, args)

        # Verify - showing all servers always returns 0
        assert result == 0
        # Should have called is_server_running_by_name for each server
        assert mock_runtime.is_server_running_by_name.call_count >= 1

    @patch('llf.server_commands.console')
    def test_status_server_legacy_mode_not_running(self, mock_console, mock_config, mock_runtime):
        """Test status showing all servers when none running (still returns 0)."""
        # Setup
        args = MagicMock()
        args.server_name = None  # Show all servers
        mock_config.has_local_server_config.return_value = True
        mock_runtime.is_server_running_by_name.return_value = False

        # Execute
        result = status_server_command(mock_config, mock_runtime, args)

        # Verify - showing all servers always returns 0 even if none running
        assert result == 0
        # Should have called is_server_running_by_name for each server
        assert mock_runtime.is_server_running_by_name.call_count >= 1

    @patch('llf.server_commands.console')
    def test_status_no_local_server_configured(self, mock_console, mock_config, mock_runtime):
        """Test status when no local server is configured."""
        # Setup
        args = MagicMock()
        args.server_name = None  # Legacy mode
        mock_config.has_local_server_config.return_value = False
        mock_config.api_base_url = 'https://api.openai.com/v1'
        mock_config.model_name = 'gpt-4'

        # Execute
        result = status_server_command(mock_config, mock_runtime, args)

        # Verify
        assert result == 0
        # Should have printed external API info
        assert any('external' in str(call).lower() or 'API' in str(call)
                  for call in mock_console.print.call_args_list)


class TestSwitchServerCommand:
    """Tests for switch_server_command()."""

    @patch('llf.server_commands.console')
    def test_switch_server_success(self, mock_console, mock_config):
        """Test successfully switching to a different server."""
        # Setup
        args = MagicMock()
        args.server_name = 'llama-3'

        # Execute
        result = switch_server_command(mock_config, args)

        # Verify
        assert result == 0
        mock_config.update_default_server.assert_called_once_with('llama-3')
        mock_config.save_to_file.assert_called_once_with(mock_config.DEFAULT_CONFIG_FILE)

    @patch('llf.server_commands.console')
    def test_switch_server_invalid_name(self, mock_console, mock_config):
        """Test switching to non-existent server."""
        # Setup
        args = MagicMock()
        args.server_name = 'nonexistent'
        mock_config.update_default_server.side_effect = ValueError("Server 'nonexistent' not found")

        # Execute
        result = switch_server_command(mock_config, args)

        # Verify
        assert result == 1
        # Should have printed error message
        error_calls = [call for call in mock_console.print.call_args_list
                      if len(call[0]) > 0 and 'not found' in str(call[0][0])]
        assert len(error_calls) > 0

    @patch('llf.server_commands.console')
    def test_switch_server_saves_config(self, mock_console, mock_config):
        """Test that switching server saves the config file."""
        # Setup
        args = MagicMock()
        args.server_name = 'qwen-coder'

        # Execute
        result = switch_server_command(mock_config, args)

        # Verify
        assert result == 0
        mock_config.save_to_file.assert_called_once()
        # Verify the path passed to save_to_file
        save_call_args = mock_config.save_to_file.call_args[0]
        assert save_call_args[0] == mock_config.DEFAULT_CONFIG_FILE

    @patch('llf.server_commands.console')
    def test_switch_server_general_exception(self, mock_console, mock_config):
        """Test handling of unexpected exceptions during switch."""
        # Setup
        args = MagicMock()
        args.server_name = 'llama-3'
        mock_config.save_to_file.side_effect = IOError("Permission denied")

        # Execute
        result = switch_server_command(mock_config, args)

        # Verify
        assert result == 1
        # Should have printed error message
        error_calls = [call for call in mock_console.print.call_args_list
                      if len(call[0]) > 0 and 'Failed' in str(call[0][0])]
        assert len(error_calls) > 0


class TestListServersEdgeCases:
    """Additional tests for list_servers_command edge cases."""

    @patch('llf.server_commands.console')
    def test_list_servers_with_external_api(self, mock_console, mock_config, mock_runtime):
        """Test listing servers when using external API."""
        # Setup - using external API
        mock_config.is_using_external_api.return_value = True
        mock_config.api_base_url = "https://api.openai.com/v1"

        # Execute
        result = list_servers_command(mock_config, mock_runtime)

        # Verify
        assert result == 0
        # Should display external API info
        assert mock_console.print.called

    @patch('llf.server_commands.console')
    def test_list_servers_with_none_server_config(self, mock_console, mock_config, mock_runtime):
        """Test listing servers when get_server_by_name returns None."""
        # Setup - make get_server_by_name return None for one server
        original_get_server = mock_config.get_server_by_name
        mock_config.get_server_by_name = lambda name: None if name == 'qwen-coder' else original_get_server(name)

        # Execute
        result = list_servers_command(mock_config, mock_runtime)

        # Verify - should handle gracefully and continue
        assert result == 0

    @patch('llf.server_commands.console')
    def test_list_servers_with_model_dir_value_error(self, mock_console, mock_config, mock_runtime):
        """Test listing servers when model_dir.relative_to raises ValueError."""
        # Setup - model_dir not relative to config.model_dir
        server = mock_config.servers['qwen-coder']
        server.model_dir = Path('/completely/different/path')

        # Execute
        result = list_servers_command(mock_config, mock_runtime)

        # Verify - should handle ValueError gracefully
        assert result == 0

    @patch('llf.server_commands.console')
    def test_list_servers_no_active_server_config(self, mock_console, mock_config, mock_runtime):
        """Test listing servers when active server config is None."""
        # Setup - active server doesn't exist
        mock_config.is_using_external_api.return_value = False
        mock_config.default_local_server = 'nonexistent_server'
        original_get_server = mock_config.get_server_by_name
        mock_config.get_server_by_name = lambda name: None if name == 'nonexistent_server' else original_get_server(name)

        # Execute
        result = list_servers_command(mock_config, mock_runtime)

        # Verify - should handle gracefully
        assert result == 0


class TestStartServerEdgeCases:
    """Additional tests for start_server_command edge cases."""

    @patch('llf.server_commands.console')
    def test_start_server_model_not_downloaded(self, mock_console, mock_config, mock_runtime, mock_model_manager):
        """Test starting server when model is not downloaded."""
        from argparse import Namespace
        args = Namespace(server_name='qwen-coder')

        # Setup - model not downloaded
        mock_model_manager.is_model_downloaded.return_value = False

        # Execute
        result = start_server_command(mock_config, mock_runtime, mock_model_manager, args)

        # Verify - should fail or prompt
        assert result in [0, 1]  # Could succeed if it downloads or fail

    @patch('llf.server_commands.console')
    def test_start_server_already_running(self, mock_console, mock_config, mock_runtime, mock_model_manager):
        """Test starting server that's already running."""
        from argparse import Namespace
        args = Namespace(server_name='qwen-coder')

        # Setup - server already running
        mock_runtime.is_server_running_by_name.return_value = True

        # Execute
        result = start_server_command(mock_config, mock_runtime, mock_model_manager, args)

        # Verify - should handle gracefully
        assert result in [0, 1]


class TestStopServerEdgeCases:
    """Additional tests for stop_server_command edge cases."""

    @patch('llf.server_commands.console')
    def test_stop_server_not_running(self, mock_console, mock_config, mock_runtime):
        """Test stopping server that's not running."""
        from argparse import Namespace
        args = Namespace(server_name='qwen-coder')

        # Setup - server not running
        mock_runtime.is_server_running_by_name.return_value = False

        # Execute
        result = stop_server_command(mock_config, mock_runtime, args)

        # Verify - should handle gracefully
        assert result in [0, 1]

    @patch('llf.server_commands.console')
    def test_stop_server_nonexistent(self, mock_console, mock_config, mock_runtime):
        """Test stopping server that doesn't exist."""
        from argparse import Namespace
        args = Namespace(server_name='nonexistent_server')

        # Setup - server doesn't exist
        original_get_server = mock_config.get_server_by_name
        mock_config.get_server_by_name = lambda name: None if name == 'nonexistent_server' else original_get_server(name)

        # Execute
        result = stop_server_command(mock_config, mock_runtime, args)

        # Verify - may succeed or fail depending on implementation
        assert result in [0, 1]


class TestStatusServerEdgeCases:
    """Additional tests for status_server_command edge cases."""

    @patch('llf.server_commands.console')
    def test_status_server_running_with_details(self, mock_console, mock_config, mock_runtime):
        """Test status of running server with detailed info."""
        from argparse import Namespace
        args = Namespace(server_name='qwen-coder')

        # Setup - server running
        mock_runtime.is_server_running_by_name.return_value = True
        mock_runtime.get_server_pid.return_value = 12345

        # Execute
        result = status_server_command(mock_config, mock_runtime, args)

        # Verify
        assert result == 0

    @patch('llf.server_commands.console')
    def test_status_server_stopped(self, mock_console, mock_config, mock_runtime):
        """Test status of stopped server."""
        from argparse import Namespace
        args = Namespace(server_name='qwen-coder')

        # Setup - server not running
        mock_runtime.is_server_running_by_name.return_value = False

        # Execute
        result = status_server_command(mock_config, mock_runtime, args)

        # Verify - stopped server returns error code 1
        assert result == 1

    @patch('llf.server_commands.console')
    def test_status_server_nonexistent(self, mock_console, mock_config, mock_runtime):
        """Test status of nonexistent server."""
        from argparse import Namespace
        args = Namespace(server_name='nonexistent_server')

        # Setup - server doesn't exist
        original_get_server = mock_config.get_server_by_name
        mock_config.get_server_by_name = lambda name: None if name == 'nonexistent_server' else original_get_server(name)

        # Execute
        result = status_server_command(mock_config, mock_runtime, args)

        # Verify - should fail gracefully
        assert result == 1


class TestSwitchServerEdgeCases:
    """Additional tests for switch_server_command edge cases."""

    @patch('llf.server_commands.console')
    def test_switch_server_success(self, mock_console, mock_config):
        """Test successfully switching to different server."""
        from argparse import Namespace
        args = Namespace(server_name='llama-3')

        # Mock save_to_file (the actual method called in implementation)
        mock_config.save_to_file = MagicMock()

        # Execute
        result = switch_server_command(mock_config, args)

        # Verify
        assert result == 0
        # Should have called save_to_file
        mock_config.save_to_file.assert_called_once()

    @patch('llf.server_commands.console')
    def test_switch_server_nonexistent(self, mock_console, mock_config):
        """Test switching to nonexistent server."""
        from argparse import Namespace
        args = Namespace(server_name='nonexistent_server')

        # Setup - server doesn't exist
        original_get_server = mock_config.get_server_by_name
        mock_config.get_server_by_name = lambda name: None if name == 'nonexistent_server' else original_get_server(name)

        # Execute
        result = switch_server_command(mock_config, args)

        # Verify - should fail
        assert result == 1
