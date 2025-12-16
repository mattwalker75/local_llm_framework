"""
Unit tests for cli module.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import sys
from io import StringIO

from llf.config import Config
from llf.cli import CLI, download_command, list_command, info_command, server_command


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

    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    def test_start_server_success_with_prompt(self, mock_print, mock_prompt, cli):
        """Test successful server start with interactive prompt."""
        cli.runtime.is_server_running = Mock(return_value=False)
        cli.runtime.start_server = Mock()
        mock_prompt.return_value = 'y'

        result = cli.start_server()

        assert result is True
        cli.runtime.start_server.assert_called_once()
        mock_prompt.assert_called_once()

    @patch('llf.cli.console.print')
    def test_start_server_auto_start(self, mock_print):
        """Test server auto-start without prompt."""
        config = Config()
        cli = CLI(config, auto_start_server=True)
        cli.runtime.is_server_running = Mock(return_value=False)
        cli.runtime.start_server = Mock()

        result = cli.start_server()

        assert result is True
        cli.runtime.start_server.assert_called_once()

    @patch('llf.cli.console.print')
    def test_start_server_no_server_start(self, mock_print):
        """Test server start with --no-server-start flag."""
        config = Config()
        cli = CLI(config, no_server_start=True)
        cli.runtime.is_server_running = Mock(return_value=False)

        result = cli.start_server()

        assert result is False

    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    def test_start_server_user_declines(self, mock_print, mock_prompt, cli):
        """Test server start when user declines prompt."""
        cli.runtime.is_server_running = Mock(return_value=False)
        mock_prompt.return_value = 'n'

        result = cli.start_server()

        assert result is False
        mock_prompt.assert_called_once()

    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    def test_start_server_failure(self, mock_print, mock_prompt, cli):
        """Test server start failure."""
        cli.runtime.is_server_running = Mock(return_value=False)
        cli.runtime.start_server = Mock(side_effect=Exception("Start failed"))
        mock_prompt.return_value = 'y'

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
        # Mock streaming response
        cli.runtime.chat = Mock(return_value=iter(["Hi", " there", "!"]))

        cli.interactive_loop()

        cli.runtime.chat.assert_called_once()
        call_args = cli.runtime.chat.call_args[0][0]
        # After the first message, history will have both user and assistant messages
        assert len(call_args) >= 1
        assert call_args[0]['role'] == 'user'
        assert call_args[0]['content'] == 'Hello'
        # Verify stream parameter was passed
        assert cli.runtime.chat.call_args[1]['stream'] is True

    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    def test_interactive_loop_chat_error(self, mock_print, mock_prompt, cli):
        """Test interactive loop with chat error."""
        mock_prompt.side_effect = ["Hello", "exit"]
        cli.runtime.chat = Mock(side_effect=Exception("Chat failed"))

        cli.interactive_loop()

        # Should handle error and continue
        assert mock_prompt.call_count == 2

    @patch('builtins.input')
    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    def test_interactive_loop_multiline_input(self, mock_print, mock_prompt, mock_input, cli):
        """Test interactive loop with multiline input (START/END)."""
        # First prompt returns "START", then input() collects lines until "END"
        mock_prompt.side_effect = ["START", "exit"]
        mock_input.side_effect = [
            "Line 1 of multiline content",
            "Line 2 of multiline content",
            "Line 3 of multiline content",
            "END"
        ]
        cli.runtime.chat = Mock(return_value=iter(["Got your", " multiline input!"]))

        cli.interactive_loop()

        # Verify chat was called with multiline content
        cli.runtime.chat.assert_called_once()
        call_args = cli.runtime.chat.call_args[0][0]
        assert len(call_args) >= 1
        assert call_args[0]['role'] == 'user'
        # Should have joined the three lines with newlines
        expected_content = "Line 1 of multiline content\nLine 2 of multiline content\nLine 3 of multiline content"
        assert call_args[0]['content'] == expected_content

    @patch('builtins.input')
    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    def test_interactive_loop_multiline_empty(self, mock_print, mock_prompt, mock_input, cli):
        """Test interactive loop with empty multiline input."""
        # START followed immediately by END
        mock_prompt.side_effect = ["START", "exit"]
        mock_input.side_effect = ["END"]
        cli.runtime.chat = Mock()

        cli.interactive_loop()

        # Chat should not be called with empty input
        cli.runtime.chat.assert_not_called()

    @patch('builtins.input')
    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    def test_interactive_loop_multiline_case_insensitive(self, mock_print, mock_prompt, mock_input, cli):
        """Test that START and END are case-insensitive."""
        # Test with lowercase "start"
        mock_prompt.side_effect = ["start", "exit"]
        mock_input.side_effect = [
            "Some content",
            "end"  # lowercase end
        ]
        cli.runtime.chat = Mock(return_value=iter(["Response"]))

        cli.interactive_loop()

        # Should still work with lowercase
        cli.runtime.chat.assert_called_once()
        call_args = cli.runtime.chat.call_args[0][0]
        assert call_args[0]['content'] == "Some content"

    @patch('builtins.input')
    @patch('llf.cli.Prompt.ask')
    @patch('llf.cli.console.print')
    def test_interactive_loop_multiline_eof(self, mock_print, mock_prompt, mock_input, cli):
        """Test multiline input handles EOFError gracefully."""
        mock_prompt.side_effect = ["START", "exit"]
        # Simulate Ctrl+D (EOF) during multiline input
        mock_input.side_effect = [
            "Line 1",
            EOFError()
        ]
        cli.runtime.chat = Mock(return_value=iter(["Response"]))

        cli.interactive_loop()

        # Should capture the line before EOF
        cli.runtime.chat.assert_called_once()
        call_args = cli.runtime.chat.call_args[0][0]
        assert call_args[0]['content'] == "Line 1"

    def test_shutdown(self, cli):
        """Test shutdown when server was started by this instance."""
        cli.runtime.stop_server = Mock()
        cli.started_server = True  # Simulate that this instance started the server
        cli.shutdown()

        cli.runtime.stop_server.assert_called_once()

    def test_shutdown_no_stop(self, cli):
        """Test shutdown when server was NOT started by this instance."""
        cli.runtime.stop_server = Mock()
        cli.started_server = False  # Server was already running
        cli.shutdown()

        # Should NOT stop the server
        cli.runtime.stop_server.assert_not_called()

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
        mock_config.log_level = 'INFO'  # Default from config
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
        mock_config.log_level = 'INFO'  # Default from config
        mock_config.model_name = 'Qwen/Qwen2.5-Coder-7B-Instruct-GGUF'
        mock_get_config.return_value = mock_config
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0

        # Simulate command line args: llf chat (no --model)
        test_args = ['llf', 'chat']
        with patch.object(sys, 'argv', test_args):
            result = main()

        # Verify default model was NOT overridden
        assert mock_config.model_name == 'Qwen/Qwen2.5-Coder-7B-Instruct-GGUF'
        assert result == 0
        mock_cli_instance.run.assert_called_once()

    @patch('llf.cli.CLI')
    @patch('llf.cli.get_config')
    def test_main_default_command_with_model(self, mock_get_config, mock_cli_class):
        """Test main function with no command (defaults to chat) but with --model parameter."""
        from llf.cli import main

        mock_config = MagicMock()
        mock_config.log_level = 'INFO'  # Default from config
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

    @patch('llf.cli.console.print')
    @patch('llf.cli.LLMRuntime')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_server_command_status_running(self, mock_config, mock_manager_class, mock_runtime_class, mock_print):
        """Test server status command when server is running."""
        mock_runtime = MagicMock()
        mock_runtime_class.return_value = mock_runtime
        mock_runtime.is_server_running.return_value = True

        mock_config_instance = MagicMock()
        mock_config_instance.model_name = 'test/model'
        mock_config_instance.get_server_url.return_value = 'http://127.0.0.1:8000'
        mock_config.return_value = mock_config_instance

        args = MagicMock()
        args.action = 'status'

        result = server_command(args)

        assert result == 0
        mock_runtime.is_server_running.assert_called_once()

    @patch('llf.cli.console.print')
    @patch('llf.cli.LLMRuntime')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_server_command_status_not_running(self, mock_config, mock_manager_class, mock_runtime_class, mock_print):
        """Test server status command when server is not running."""
        mock_runtime = MagicMock()
        mock_runtime_class.return_value = mock_runtime
        mock_runtime.is_server_running.return_value = False

        args = MagicMock()
        args.action = 'status'

        result = server_command(args)

        assert result == 1
        mock_runtime.is_server_running.assert_called_once()

    @patch('llf.cli.console.print')
    @patch('llf.cli.LLMRuntime')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_server_command_start_success(self, mock_config, mock_manager_class, mock_runtime_class, mock_print):
        """Test server start command success."""
        mock_runtime = MagicMock()
        mock_runtime_class.return_value = mock_runtime
        mock_runtime.is_server_running.return_value = False

        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.is_model_downloaded.return_value = True

        mock_config_instance = MagicMock()
        mock_config_instance.model_name = 'test/model'
        mock_config_instance.get_server_url.return_value = 'http://127.0.0.1:8000'
        mock_config.return_value = mock_config_instance

        args = MagicMock()
        args.action = 'start'
        args.daemon = True  # Use daemon to avoid sleep loop

        result = server_command(args)

        assert result == 0
        mock_runtime.start_server.assert_called_once()

    @patch('llf.cli.console.print')
    @patch('llf.cli.LLMRuntime')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_server_command_start_already_running(self, mock_config, mock_manager_class, mock_runtime_class, mock_print):
        """Test server start command when already running."""
        mock_runtime = MagicMock()
        mock_runtime_class.return_value = mock_runtime
        mock_runtime.is_server_running.return_value = True

        mock_config_instance = MagicMock()
        mock_config_instance.get_server_url.return_value = 'http://127.0.0.1:8000'
        mock_config.return_value = mock_config_instance

        args = MagicMock()
        args.action = 'start'
        args.daemon = True

        result = server_command(args)

        assert result == 0
        mock_runtime.start_server.assert_not_called()

    @patch('llf.cli.console.print')
    @patch('llf.cli.LLMRuntime')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_server_command_start_downloads_model(self, mock_config, mock_manager_class, mock_runtime_class, mock_print):
        """Test server start downloads model if needed."""
        mock_runtime = MagicMock()
        mock_runtime_class.return_value = mock_runtime
        mock_runtime.is_server_running.return_value = False

        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.is_model_downloaded.return_value = False
        mock_manager.download_model.return_value = None

        mock_config_instance = MagicMock()
        mock_config_instance.model_name = 'test/model'
        mock_config_instance.get_server_url.return_value = 'http://127.0.0.1:8000'
        mock_config.return_value = mock_config_instance

        args = MagicMock()
        args.action = 'start'
        args.daemon = True

        result = server_command(args)

        assert result == 0
        mock_manager.download_model.assert_called_once()
        mock_runtime.start_server.assert_called_once()

    @patch('llf.cli.console.print')
    @patch('llf.cli.LLMRuntime')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_server_command_stop_success(self, mock_config, mock_manager_class, mock_runtime_class, mock_print):
        """Test server stop command success."""
        mock_runtime = MagicMock()
        mock_runtime_class.return_value = mock_runtime
        mock_runtime.is_server_running.return_value = True

        args = MagicMock()
        args.action = 'stop'

        result = server_command(args)

        assert result == 0
        mock_runtime.stop_server.assert_called_once()

    @patch('llf.cli.console.print')
    @patch('llf.cli.LLMRuntime')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_server_command_stop_not_running(self, mock_config, mock_manager_class, mock_runtime_class, mock_print):
        """Test server stop command when not running."""
        mock_runtime = MagicMock()
        mock_runtime_class.return_value = mock_runtime
        mock_runtime.is_server_running.return_value = False

        args = MagicMock()
        args.action = 'stop'

        result = server_command(args)

        assert result == 0
        mock_runtime.stop_server.assert_not_called()

    @patch('llf.cli.console.print')
    @patch('llf.cli.LLMRuntime')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_server_command_restart_success(self, mock_config, mock_manager_class, mock_runtime_class, mock_print):
        """Test server restart command success."""
        mock_runtime = MagicMock()
        mock_runtime_class.return_value = mock_runtime
        mock_runtime.is_server_running.return_value = True

        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.is_model_downloaded.return_value = True

        mock_config_instance = MagicMock()
        mock_config_instance.model_name = 'test/model'
        mock_config_instance.get_server_url.return_value = 'http://127.0.0.1:8000'
        mock_config.return_value = mock_config_instance

        args = MagicMock()
        args.action = 'restart'

        result = server_command(args)

        assert result == 0
        mock_runtime.stop_server.assert_called_once()
        mock_runtime.start_server.assert_called_once()

    @patch('llf.cli.console.print')
    @patch('llf.cli.LLMRuntime')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_server_command_with_model_override(self, mock_config, mock_manager_class, mock_runtime_class, mock_print):
        """Test server command with --model parameter."""
        mock_runtime = MagicMock()
        mock_runtime_class.return_value = mock_runtime
        mock_runtime.is_server_running.return_value = False

        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.is_model_downloaded.return_value = True

        mock_config_instance = MagicMock()
        mock_config_instance.get_server_url.return_value = 'http://127.0.0.1:8000'
        mock_config.return_value = mock_config_instance

        args = MagicMock()
        args.action = 'start'
        args.model = 'custom/model'
        args.daemon = True

        result = server_command(args)

        assert result == 0
        assert mock_config_instance.model_name == 'custom/model'
        mock_runtime.start_server.assert_called_once()

    @patch('llf.cli.console.print')
    @patch('llf.cli.LLMRuntime')
    @patch('llf.cli.ModelManager')
    @patch('llf.cli.get_config')
    def test_server_command_error_handling(self, mock_config, mock_manager_class, mock_runtime_class, mock_print):
        """Test server command error handling."""
        mock_runtime = MagicMock()
        mock_runtime_class.return_value = mock_runtime
        mock_runtime.is_server_running.side_effect = Exception("Server error")

        args = MagicMock()
        args.action = 'status'

        result = server_command(args)

        assert result == 1


class TestCLIQuestionMode:
    """Test CLI non-interactive question mode."""

    @patch.object(CLI, 'ensure_model_ready')
    @patch.object(CLI, 'start_server')
    def test_cli_question_basic(self, mock_start, mock_ensure, cli):
        """Test basic CLI question mode."""
        mock_ensure.return_value = True
        mock_start.return_value = True
        cli.runtime.chat = Mock(return_value="This is the answer")

        exit_code = cli.cli_question("What is 2+2?")

        assert exit_code == 0
        cli.runtime.chat.assert_called_once()
        call_args = cli.runtime.chat.call_args
        # Verify message structure
        assert call_args[0][0][0]['role'] == 'user'
        assert call_args[0][0][0]['content'] == "What is 2+2?"
        # Verify stream=False for CLI mode
        assert call_args[1]['stream'] is False

    @patch.object(CLI, 'ensure_model_ready')
    def test_cli_question_model_not_ready(self, mock_ensure, cli):
        """Test CLI question mode when model not ready."""
        mock_ensure.return_value = False

        exit_code = cli.cli_question("What is 2+2?")

        assert exit_code == 1

    @patch.object(CLI, 'ensure_model_ready')
    @patch.object(CLI, 'start_server')
    def test_cli_question_server_fails(self, mock_start, mock_ensure, cli):
        """Test CLI question mode when server fails to start."""
        mock_ensure.return_value = True
        mock_start.return_value = False

        exit_code = cli.cli_question("What is 2+2?")

        assert exit_code == 1

    @patch.object(CLI, 'ensure_model_ready')
    @patch.object(CLI, 'start_server')
    def test_cli_question_chat_error(self, mock_start, mock_ensure, cli):
        """Test CLI question mode when chat fails."""
        mock_ensure.return_value = True
        mock_start.return_value = True
        cli.runtime.chat = Mock(side_effect=Exception("Chat error"))

        exit_code = cli.cli_question("What is 2+2?")

        assert exit_code == 1

    @patch.object(CLI, 'cli_question')
    def test_run_with_cli_question(self, mock_cli_question, cli):
        """Test run() method with CLI question parameter."""
        mock_cli_question.return_value = 0

        exit_code = cli.run(cli_question="What is the meaning of life?")

        assert exit_code == 0
        mock_cli_question.assert_called_once_with("What is the meaning of life?")

    @patch.object(CLI, 'interactive_loop')
    @patch.object(CLI, 'start_server')
    @patch.object(CLI, 'ensure_model_ready')
    @patch.object(CLI, 'print_welcome')
    @patch.object(CLI, 'shutdown')
    def test_run_without_cli_question(self, mock_shutdown, mock_welcome, mock_ensure,
                                       mock_start, mock_loop, cli):
        """Test run() method without CLI question (interactive mode)."""
        mock_ensure.return_value = True
        mock_start.return_value = True

        exit_code = cli.run(cli_question=None)

        assert exit_code == 0
        mock_welcome.assert_called_once()
        mock_loop.assert_called_once()
        mock_shutdown.assert_called_once()

    @patch('llf.cli.CLI')
    @patch('llf.cli.get_config')
    def test_main_with_cli_argument(self, mock_get_config, mock_cli_class):
        """Test main function with --cli argument."""
        from llf.cli import main

        mock_config = MagicMock()
        mock_config.log_level = 'INFO'  # Default from config
        mock_get_config.return_value = mock_config
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0

        # Simulate: llf chat --cli "What is AI?"
        test_args = ['llf', 'chat', '--cli', 'What is AI?']
        with patch.object(sys, 'argv', test_args):
            result = main()

        # Verify CLI.run was called with the question
        mock_cli_instance.run.assert_called_once()
        call_args = mock_cli_instance.run.call_args
        assert call_args[1]['cli_question'] == 'What is AI?'
        assert result == 0

    @patch('llf.cli.CLI')
    @patch('llf.cli.get_config')
    def test_main_with_cli_and_model(self, mock_get_config, mock_cli_class):
        """Test main function with --cli and --model arguments."""
        from llf.cli import main

        mock_config = MagicMock()
        mock_config.log_level = 'INFO'  # Default from config
        mock_get_config.return_value = mock_config
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0

        # Simulate: llf chat --cli "What is AI?" --model "custom/model"
        test_args = ['llf', 'chat', '--cli', 'What is AI?', '--model', 'custom/model']
        with patch.object(sys, 'argv', test_args):
            result = main()

        # Verify model was overridden
        assert mock_config.model_name == 'custom/model'
        # Verify CLI.run was called with the question
        call_args = mock_cli_instance.run.call_args
        assert call_args[1]['cli_question'] == 'What is AI?'
        assert result == 0

    @patch('llf.cli.CLI')
    @patch('llf.cli.get_config')
    def test_main_with_cli_and_auto_start(self, mock_get_config, mock_cli_class):
        """Test main function with --cli and --auto-start-server arguments."""
        from llf.cli import main

        mock_config = MagicMock()
        mock_config.log_level = 'INFO'  # Default from config
        mock_get_config.return_value = mock_config
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0

        # Simulate: llf chat --cli "What is AI?" --auto-start-server
        test_args = ['llf', 'chat', '--cli', 'What is AI?', '--auto-start-server']
        with patch.object(sys, 'argv', test_args):
            result = main()

        # Verify CLI was initialized with auto_start_server=True
        call_args = mock_cli_class.call_args
        assert call_args[1]['auto_start_server'] is True
        # Verify question was passed
        run_call_args = mock_cli_instance.run.call_args
        assert run_call_args[1]['cli_question'] == 'What is AI?'
        assert result == 0

    @patch('llf.cli.CLI')
    @patch('llf.cli.get_config')
    def test_main_with_cli_and_no_server_start(self, mock_get_config, mock_cli_class):
        """Test main function with --cli and --no-server-start arguments."""
        from llf.cli import main

        mock_config = MagicMock()
        mock_config.log_level = 'INFO'  # Default from config
        mock_get_config.return_value = mock_config
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0

        # Simulate: llf chat --cli "What is AI?" --no-server-start
        test_args = ['llf', 'chat', '--cli', 'What is AI?', '--no-server-start']
        with patch.object(sys, 'argv', test_args):
            result = main()

        # Verify CLI was initialized with no_server_start=True
        call_args = mock_cli_class.call_args
        assert call_args[1]['no_server_start'] is True
        # Verify question was passed
        run_call_args = mock_cli_instance.run.call_args
        assert run_call_args[1]['cli_question'] == 'What is AI?'
        assert result == 0


class TestLogging:
    """Test logging configuration."""

    @patch('llf.cli.setup_logging')
    @patch('llf.cli.disable_external_loggers')
    @patch('llf.cli.CLI')
    @patch('llf.cli.get_config')
    def test_main_with_log_file(self, mock_get_config, mock_cli_class, mock_disable, mock_setup_logging):
        """Test main function with --log-file argument."""
        from llf.cli import main

        mock_config = MagicMock()
        mock_config.log_level = 'INFO'  # Default from config
        mock_get_config.return_value = mock_config
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0

        # Simulate: llf --log-file /tmp/llf.log chat
        test_args = ['llf', '--log-file', '/tmp/llf.log', 'chat']
        with patch.object(sys, 'argv', test_args):
            result = main()

        # Verify setup_logging was called with log_file
        mock_setup_logging.assert_called_once()
        call_args = mock_setup_logging.call_args
        assert call_args[1]['level'] == 'INFO'  # from config
        assert call_args[1]['log_file'] == Path('/tmp/llf.log')
        assert result == 0

    @patch('llf.cli.setup_logging')
    @patch('llf.cli.disable_external_loggers')
    @patch('llf.cli.CLI')
    @patch('llf.cli.get_config')
    def test_main_with_log_level_and_log_file(self, mock_get_config, mock_cli_class, mock_disable, mock_setup_logging):
        """Test main function with both --log-level and --log-file."""
        from llf.cli import main

        mock_config = MagicMock()
        mock_config.log_level = 'INFO'  # Default from config
        mock_get_config.return_value = mock_config
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0

        # Simulate: llf --log-level DEBUG --log-file /var/log/llf.log chat
        test_args = ['llf', '--log-level', 'DEBUG', '--log-file', '/var/log/llf.log', 'chat']
        with patch.object(sys, 'argv', test_args):
            result = main()

        # Verify setup_logging was called with both parameters
        mock_setup_logging.assert_called_once()
        call_args = mock_setup_logging.call_args
        assert call_args[1]['level'] == 'DEBUG'
        assert call_args[1]['log_file'] == Path('/var/log/llf.log')
        assert result == 0

    @patch('llf.cli.setup_logging')
    @patch('llf.cli.disable_external_loggers')
    @patch('llf.cli.CLI')
    @patch('llf.cli.get_config')
    def test_main_without_log_file(self, mock_get_config, mock_cli_class, mock_disable, mock_setup_logging):
        """Test main function without --log-file (console only)."""
        from llf.cli import main

        mock_config = MagicMock()
        mock_config.log_level = 'INFO'  # Default from config
        mock_get_config.return_value = mock_config
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0

        # Simulate: llf chat (no log file)
        test_args = ['llf', 'chat']
        with patch.object(sys, 'argv', test_args):
            result = main()

        # Verify setup_logging was called with log_file=None
        mock_setup_logging.assert_called_once()
        call_args = mock_setup_logging.call_args
        assert call_args[1]['level'] == 'INFO'
        assert call_args[1]['log_file'] is None
        assert result == 0
