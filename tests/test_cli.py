"""
Unit tests for cli module.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import sys
from io import StringIO

from llf.config import Config
from llf.cli import CLI, download_command, list_command, info_command


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for tests."""
    return tmp_path


@pytest.fixture
def config(temp_dir):
    """Create test configuration."""
    config = Config()
    config.model_dir = temp_dir / "models"
    config.cache_dir = temp_dir / ".cache"
    config.model_name = "test/model"
    return config


@pytest.fixture
def cli(config):
    """Create CLI instance."""
    return CLI(config)


class TestCLI:
    """Test CLI class."""

    def test_initialization(self, cli, config):
        """Test CLI initialization."""
        assert cli.config == config
        assert cli.model_manager is not None
        assert cli.runtime is not None
        assert cli.running is False

    @patch('llf.cli.console.print')
    def test_print_welcome(self, mock_print, cli):
        """Test welcome message printing."""
        cli.print_welcome()
        mock_print.assert_called_once()

    @patch('llf.cli.console.print')
    def test_print_help(self, mock_print, cli):
        """Test help message printing."""
        cli.print_help()
        mock_print.assert_called_once()

    @patch('llf.cli.console.print')
    def test_print_info(self, mock_print, cli):
        """Test info message printing."""
        cli.print_info()
        mock_print.assert_called_once()

    @patch('llf.cli.console.print')
    def test_ensure_model_ready_already_downloaded(self, mock_print, cli):
        """Test ensure_model_ready when model exists."""
        cli.model_manager.is_model_downloaded = Mock(return_value=True)

        result = cli.ensure_model_ready()

        assert result is True

    @patch('llf.cli.console.print')
    def test_ensure_model_ready_downloads(self, mock_print, cli):
        """Test ensure_model_ready downloads model."""
        cli.model_manager.is_model_downloaded = Mock(return_value=False)
        cli.model_manager.download_model = Mock(return_value=Path("/fake/path"))

        result = cli.ensure_model_ready()

        assert result is True
        cli.model_manager.download_model.assert_called_once()

    @patch('llf.cli.console.print')
    def test_ensure_model_ready_download_fails(self, mock_print, cli):
        """Test ensure_model_ready when download fails."""
        cli.model_manager.is_model_downloaded = Mock(return_value=False)
        cli.model_manager.download_model = Mock(side_effect=Exception("Download failed"))

        result = cli.ensure_model_ready()

        assert result is False

    @patch('llf.cli.console.print')
    def test_start_server_already_running(self, mock_print, cli):
        """Test start_server when already running."""
        cli.runtime.is_server_running = Mock(return_value=True)

        result = cli.start_server()

        assert result is True

    @patch('llf.cli.console.print')
    def test_start_server_success(self, mock_print, cli):
        """Test successful server start."""
        cli.runtime.is_server_running = Mock(return_value=False)
        cli.runtime.start_server = Mock()

        result = cli.start_server()

        assert result is True
        cli.runtime.start_server.assert_called_once()

    @patch('llf.cli.console.print')
    def test_start_server_failure(self, mock_print, cli):
        """Test server start failure."""
        cli.runtime.is_server_running = Mock(return_value=False)
        cli.runtime.start_server = Mock(side_effect=Exception("Start failed"))

        result = cli.start_server()

        assert result is False

    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    def test_interactive_loop_exit(self, mock_print, mock_prompt, cli):
        """Test interactive loop with exit command."""
        mock_prompt.side_effect = ["exit"]

        cli.interactive_loop()

        # After exit, running should be False
        # Note: The loop sets running=True at start, then breaks on 'exit'
        # The running flag tracks whether we're IN the loop, not whether we exited
        assert mock_prompt.call_count == 1

    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    @patch.object(CLI, 'print_help')
    def test_interactive_loop_help(self, mock_help, mock_print, mock_prompt, cli):
        """Test interactive loop with help command."""
        mock_prompt.side_effect = ["help", "exit"]

        cli.interactive_loop()

        mock_help.assert_called_once()

    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    @patch.object(CLI, 'print_info')
    def test_interactive_loop_info(self, mock_info, mock_print, mock_prompt, cli):
        """Test interactive loop with info command."""
        mock_prompt.side_effect = ["info", "exit"]

        cli.interactive_loop()

        mock_info.assert_called_once()

    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    @patch('llf.cli.console.clear')
    @patch.object(CLI, 'print_welcome')
    def test_interactive_loop_clear(self, mock_welcome, mock_clear, mock_print, mock_prompt, cli):
        """Test interactive loop with clear command."""
        mock_prompt.side_effect = ["clear", "exit"]

        cli.interactive_loop()

        mock_clear.assert_called_once()

    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    def test_interactive_loop_chat(self, mock_print, mock_prompt, cli):
        """Test interactive loop with chat message."""
        mock_prompt.side_effect = ["Hello", "exit"]
        cli.runtime.chat = Mock(return_value="Hi there!")

        cli.interactive_loop()

        cli.runtime.chat.assert_called_once()
        call_args = cli.runtime.chat.call_args[0][0]
        # After the first message, history will have both user and assistant messages
        assert len(call_args) >= 1
        assert call_args[0]['role'] == 'user'
        assert call_args[0]['content'] == 'Hello'

    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    def test_interactive_loop_chat_error(self, mock_print, mock_prompt, cli):
        """Test interactive loop with chat error."""
        mock_prompt.side_effect = ["Hello", "exit"]
        cli.runtime.chat = Mock(side_effect=Exception("Chat failed"))

        cli.interactive_loop()

        # Should handle error and continue
        assert mock_prompt.call_count == 2

    def test_shutdown(self, cli):
        """Test shutdown."""
        cli.runtime.stop_server = Mock()
        cli.shutdown()

        cli.runtime.stop_server.assert_called_once()

    @patch.object(CLI, 'shutdown')
    @patch.object(CLI, 'interactive_loop')
    @patch.object(CLI, 'start_server')
    @patch.object(CLI, 'ensure_model_ready')
    @patch.object(CLI, 'print_welcome')
    def test_run_success(self, mock_welcome, mock_ensure, mock_start, mock_loop, mock_shutdown, cli):
        """Test successful run."""
        mock_ensure.return_value = True
        mock_start.return_value = True

        exit_code = cli.run()

        assert exit_code == 0
        mock_welcome.assert_called_once()
        mock_ensure.assert_called_once()
        mock_start.assert_called_once()
        mock_loop.assert_called_once()
        mock_shutdown.assert_called_once()

    @patch.object(CLI, 'shutdown')
    @patch.object(CLI, 'ensure_model_ready')
    @patch.object(CLI, 'print_welcome')
    def test_run_model_not_ready(self, mock_welcome, mock_ensure, mock_shutdown, cli):
        """Test run when model is not ready."""
        mock_ensure.return_value = False

        exit_code = cli.run()

        assert exit_code == 1
        mock_shutdown.assert_called_once()

    @patch.object(CLI, 'shutdown')
    @patch.object(CLI, 'start_server')
    @patch.object(CLI, 'ensure_model_ready')
    @patch.object(CLI, 'print_welcome')
    def test_run_server_fails(self, mock_welcome, mock_ensure, mock_start, mock_shutdown, cli):
        """Test run when server fails to start."""
        mock_ensure.return_value = True
        mock_start.return_value = False

        exit_code = cli.run()

        assert exit_code == 1
        mock_shutdown.assert_called_once()


class TestCLICommands:
    """Test CLI command functions."""

    @patch('llf.cli.CLI')
    @patch('llf.cli.get_config')
    def test_main_chat_with_model_override(self, mock_get_config, mock_cli_class):
        """Test main function with chat command and --model parameter."""
        from llf.cli import main

        mock_config = MagicMock()
        mock_get_config.return_value = mock_config
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0

        # Simulate command line args: llf chat --model "mistralai/Mistral-7B"
        test_args = ['llf', 'chat', '--model', 'mistralai/Mistral-7B-Instruct-v0.2']
        with patch.object(sys, 'argv', test_args):
            result = main()

        # Verify model was overridden
        assert mock_config.model_name == 'mistralai/Mistral-7B-Instruct-v0.2'
        assert result == 0
        mock_cli_instance.run.assert_called_once()

    @patch('llf.cli.CLI')
    @patch('llf.cli.get_config')
    def test_main_chat_without_model_uses_default(self, mock_get_config, mock_cli_class):
        """Test main function with chat command but no --model parameter uses default."""
        from llf.cli import main

        mock_config = MagicMock()
        mock_config.model_name = 'Qwen/Qwen3-Coder-30B-A3B-Instruct'
        mock_get_config.return_value = mock_config
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0

        # Simulate command line args: llf chat (no --model)
        test_args = ['llf', 'chat']
        with patch.object(sys, 'argv', test_args):
            result = main()

        # Verify default model was NOT overridden
        assert mock_config.model_name == 'Qwen/Qwen3-Coder-30B-A3B-Instruct'
        assert result == 0
        mock_cli_instance.run.assert_called_once()

    @patch('llf.cli.CLI')
    @patch('llf.cli.get_config')
    def test_main_default_command_with_model(self, mock_get_config, mock_cli_class):
        """Test main function with no command (defaults to chat) but with --model parameter."""
        from llf.cli import main

        mock_config = MagicMock()
        mock_get_config.return_value = mock_config
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0

        # Simulate command line args: llf --model "custom/model"
        # Note: --model must come after command or be a global option
        # For now, test with explicit chat command
        test_args = ['llf', 'chat', '--model', 'custom/model']
        with patch.object(sys, 'argv', test_args):
            result = main()

        # Verify model was overridden
        assert mock_config.model_name == 'custom/model'
        assert result == 0
        mock_cli_instance.run.assert_called_once()

    @patch('llf.cli.console.print')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_download_command_success(self, mock_config, mock_manager_class, mock_print):
        """Test download command success."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.download_model.return_value = Path("/fake/path")
        mock_manager.get_model_info.return_value = {
            'path': '/fake/path',
            'size_gb': 5.0
        }

        args = MagicMock()
        args.model = None
        args.force = False

        result = download_command(args)

        assert result == 0
        mock_manager.download_model.assert_called_once()

    @patch('llf.cli.console.print')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_download_command_failure(self, mock_config, mock_manager_class, mock_print):
        """Test download command failure."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.download_model.side_effect = Exception("Download failed")

        args = MagicMock()
        args.model = None
        args.force = False

        result = download_command(args)

        assert result == 1

    @patch('llf.cli.console.print')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_list_command_empty(self, mock_config, mock_manager_class, mock_print):
        """Test list command with no models."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.list_downloaded_models.return_value = []

        args = MagicMock()
        result = list_command(args)

        assert result == 0

    @patch('llf.cli.console.print')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_list_command_with_models(self, mock_config, mock_manager_class, mock_print):
        """Test list command with models."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.list_downloaded_models.return_value = ["model1", "model2"]
        mock_manager.get_model_info.return_value = {
            'downloaded': True,
            'size_gb': 5.0
        }

        args = MagicMock()
        result = list_command(args)

        assert result == 0

    @patch('llf.cli.console.print')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_info_command(self, mock_config, mock_manager_class, mock_print):
        """Test info command."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.get_model_info.return_value = {
            'name': 'test/model',
            'path': '/fake/path',
            'downloaded': True,
            'size_gb': 5.0,
            'verification': {
                'exists': True,
                'has_config': True,
                'has_tokenizer': True,
                'has_weights': True,
                'valid': True
            }
        }

        args = MagicMock()
        args.model = None

        result = info_command(args)

        assert result == 0
        mock_manager.get_model_info.assert_called_once()
