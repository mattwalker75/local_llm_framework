"""
Tests for GUI module.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from llf.gui import LLMFrameworkGUI, start_gui
from llf.config import Config
from llf.prompt_config import PromptConfig


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for tests."""
    return tmp_path


class TestLLMFrameworkGUI:
    """Test LLMFrameworkGUI class."""

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create mock config for testing."""
        config_file = tmp_path / "config.json"
        config_data = {
            "models_dir": str(tmp_path / "models"),
            "external_api": {
                "provider": "openai",
                "api_key": "test-key",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-3.5-turbo"
            }
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file)
        return config

    @pytest.fixture
    def mock_prompt_config(self, tmp_path):
        """Create mock prompt config for testing."""
        config_file = tmp_path / "config_prompt.json"
        config_data = {
            "system_prompt": "Test system prompt",
            "conversation_format": "standard"
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        return PromptConfig(config_file)

    @pytest.fixture
    def gui(self, mock_config, mock_prompt_config):
        """Create GUI instance for testing."""
        return LLMFrameworkGUI(config=mock_config, prompt_config=mock_prompt_config)

    def test_initialization(self, gui):
        """Test GUI initialization."""
        assert gui.config is not None
        assert gui.prompt_config is not None
        assert gui.model_manager is not None
        assert gui.runtime is not None

    def test_initialization_with_defaults(self):
        """Test GUI initialization with default configs."""
        with patch('llf.gui.get_config') as mock_get_config, \
             patch('llf.gui.get_prompt_config') as mock_get_prompt_config:

            mock_get_config.return_value = Mock()
            mock_get_prompt_config.return_value = Mock()

            gui = LLMFrameworkGUI()

            assert gui.config is not None
            assert gui.prompt_config is not None
            mock_get_config.assert_called_once()
            mock_get_prompt_config.assert_called_once()

    def test_initialization_with_auth_key(self):
        """Test GUI initialization with authentication key."""
        with patch('llf.gui.get_config') as mock_get_config, \
             patch('llf.gui.get_prompt_config') as mock_get_prompt_config:

            mock_get_config.return_value = Mock()
            mock_get_prompt_config.return_value = Mock()

            auth_key = "test_secret_key_123"
            gui = LLMFrameworkGUI(auth_key=auth_key)

            assert gui.auth_key == auth_key
            assert gui.config is not None
            assert gui.prompt_config is not None

    def test_initialization_without_auth_key(self):
        """Test GUI initialization without authentication key."""
        with patch('llf.gui.get_config') as mock_get_config, \
             patch('llf.gui.get_prompt_config') as mock_get_prompt_config:

            mock_get_config.return_value = Mock()
            mock_get_prompt_config.return_value = Mock()

            gui = LLMFrameworkGUI()

            assert gui.auth_key is None
            assert gui.config is not None
            assert gui.prompt_config is not None

    def test_started_server_flag_initialization(self, gui):
        """Test that started_server flag is initialized to False."""
        assert gui.started_server == False

    def test_check_server_on_startup_external_api(self, gui):
        """Test check_server_on_startup when using external API."""
        with patch.object(gui.config, 'is_using_external_api', return_value=True):
            needs_start, message = gui.check_server_on_startup()

            assert needs_start == False
            assert "external api" in message.lower()

    def test_check_server_on_startup_no_local_config(self, gui):
        """Test check_server_on_startup when no local server configured."""
        with patch.object(gui.config, 'is_using_external_api', return_value=False), \
             patch.object(gui.config, 'has_local_server_config', return_value=False):

            needs_start, message = gui.check_server_on_startup()

            assert needs_start == False
            assert "not configured" in message.lower()

    def test_check_server_on_startup_already_running(self, gui):
        """Test check_server_on_startup when server is already running."""
        with patch.object(gui.config, 'is_using_external_api', return_value=False), \
             patch.object(gui.config, 'has_local_server_config', return_value=True), \
             patch.object(gui.runtime, 'is_server_running', return_value=True):

            needs_start, message = gui.check_server_on_startup()

            assert needs_start == False
            assert "running" in message.lower()

    def test_check_server_on_startup_needs_start(self, gui):
        """Test check_server_on_startup when server needs to be started."""
        with patch.object(gui.config, 'is_using_external_api', return_value=False), \
             patch.object(gui.config, 'has_local_server_config', return_value=True), \
             patch.object(gui.runtime, 'is_server_running', return_value=False):

            needs_start, message = gui.check_server_on_startup()

            assert needs_start == True
            assert "not running" in message.lower()

    def test_start_server_from_gui_success(self, gui):
        """Test starting server from GUI successfully."""
        with patch.object(gui.runtime, 'start_server') as mock_start:
            result = gui.start_server_from_gui()

            mock_start.assert_called_once()
            assert gui.started_server == True
            assert "success" in result.lower()

    def test_start_server_from_gui_error(self, gui):
        """Test starting server from GUI with error."""
        with patch.object(gui.runtime, 'start_server', side_effect=Exception("Start failed")):
            result = gui.start_server_from_gui()

            assert gui.started_server == False
            assert "failed" in result.lower()
            assert "start failed" in result.lower()

    def test_shutdown_gui_with_started_server(self, gui):
        """Test shutdown stops server if GUI started it."""
        gui.started_server = True

        with patch.object(gui.config, 'has_local_server_config', return_value=True), \
             patch.object(gui.runtime, 'is_server_running', return_value=True), \
             patch.object(gui.runtime, 'stop_server') as mock_stop:

            result = gui.shutdown_gui()

            mock_stop.assert_called_once()
            assert "shutting down" in result.lower()

    def test_shutdown_gui_without_started_server(self, gui):
        """Test shutdown leaves server running if GUI didn't start it."""
        gui.started_server = False

        with patch.object(gui.runtime, 'is_server_running', return_value=True), \
             patch.object(gui.runtime, 'stop_server') as mock_stop:

            result = gui.shutdown_gui()

            mock_stop.assert_not_called()
            assert "shutting down" in result.lower()

    def test_shutdown_gui_no_server_running(self, gui):
        """Test shutdown when no server is running."""
        with patch.object(gui.runtime, 'is_server_running', return_value=False), \
             patch.object(gui.runtime, 'stop_server') as mock_stop:

            result = gui.shutdown_gui()

            mock_stop.assert_not_called()
            assert "shutting down" in result.lower()

    def test_shutdown_gui_error(self, gui):
        """Test shutdown error handling."""
        gui.started_server = True

        with patch.object(gui.config, 'has_local_server_config', return_value=True), \
             patch.object(gui.runtime, 'is_server_running', return_value=True), \
             patch.object(gui.runtime, 'stop_server', side_effect=Exception("Stop error")):

            result = gui.shutdown_gui()

            assert "error" in result.lower()
            assert "stop error" in result.lower()

    def test_get_server_status_no_config(self, gui):
        """Test getting server status when no local server configured."""
        with patch.object(gui.config, 'has_local_server_config', return_value=False):
            status = gui.get_server_status()
            assert "not configured" in status.lower()

    def test_get_server_status_stopped(self, gui, tmp_path):
        """Test getting server status when server is stopped."""
        # Setup config with local server
        gui.config.llama_server_path = tmp_path / "llama-server"
        gui.config.llama_server_path.touch()
        gui.config._has_local_server_section = True

        with patch.object(gui.runtime, 'is_server_running', return_value=False):
            status = gui.get_server_status()
            assert "stopped" in status.lower() or "not running" in status.lower()

    def test_get_server_status_running(self, gui, tmp_path):
        """Test getting server status when server is running."""
        # Setup config with local server
        gui.config.llama_server_path = tmp_path / "llama-server"
        gui.config.llama_server_path.touch()
        gui.config._has_local_server_section = True

        with patch.object(gui.runtime, 'is_server_running', return_value=True):
            status = gui.get_server_status()
            assert "running" in status.lower()

    def test_start_server_no_config(self, gui):
        """Test starting server when no local server configured."""
        with patch.object(gui.config, 'has_local_server_config', return_value=False):
            result = gui.start_server()
            assert "not configured" in result.lower()

    def test_start_server_already_running(self, gui, tmp_path):
        """Test starting server when already running."""
        gui.config.llama_server_path = tmp_path / "llama-server"
        gui.config.llama_server_path.touch()
        gui.config._has_local_server_section = True

        with patch.object(gui.runtime, 'is_server_running', return_value=True):
            result = gui.start_server()
            assert "already running" in result.lower()

    def test_start_server_success(self, gui, tmp_path):
        """Test successfully starting server."""
        gui.config.llama_server_path = tmp_path / "llama-server"
        gui.config.llama_server_path.touch()
        gui.config._has_local_server_section = True
        gui.config.model_name = "test_model.gguf"

        with patch.object(gui.runtime, 'is_server_running', side_effect=[False, True]), \
             patch.object(gui.runtime, 'start_server') as mock_start, \
             patch.object(gui.model_manager, 'is_model_downloaded', return_value=True), \
             patch('time.sleep'):  # Mock sleep to speed up test

            result = gui.start_server()
            mock_start.assert_called_once()
            assert "started successfully" in result.lower() or "success" in result.lower()

    def test_start_server_error(self, gui, tmp_path):
        """Test server start error handling."""
        gui.config.llama_server_path = tmp_path / "llama-server"
        gui.config.llama_server_path.touch()
        gui.config._has_local_server_section = True

        with patch.object(gui.runtime, 'is_server_running', return_value=False), \
             patch.object(gui.runtime, 'start_server', side_effect=Exception("Test error")):

            result = gui.start_server()
            assert "error" in result.lower()
            assert "test error" in result.lower()

    def test_stop_server_no_config(self, gui):
        """Test stopping server when no local server configured."""
        with patch.object(gui.config, 'has_local_server_config', return_value=False):
            result = gui.stop_server()
            assert "not configured" in result.lower()

    def test_stop_server_not_running(self, gui, tmp_path):
        """Test stopping server when not running."""
        gui.config.llama_server_path = tmp_path / "llama-server"
        gui.config.llama_server_path.touch()
        gui.config._has_local_server_section = True

        with patch.object(gui.runtime, 'is_server_running', return_value=False):
            result = gui.stop_server()
            assert "not running" in result.lower()

    def test_stop_server_success(self, gui, tmp_path):
        """Test successfully stopping server."""
        gui.config.llama_server_path = tmp_path / "llama-server"
        gui.config.llama_server_path.touch()
        gui.config._has_local_server_section = True

        with patch.object(gui.runtime, 'is_server_running', side_effect=[True, False]), \
             patch.object(gui.runtime, 'stop_server') as mock_stop, \
             patch('time.sleep'):  # Mock sleep to speed up test

            result = gui.stop_server()
            mock_stop.assert_called_once()
            assert "stopped successfully" in result.lower() or "success" in result.lower()

    def test_stop_server_error(self, gui, tmp_path):
        """Test server stop error handling."""
        gui.config.llama_server_path = tmp_path / "llama-server"
        gui.config.llama_server_path.touch()
        gui.config._has_local_server_section = True

        with patch.object(gui.runtime, 'is_server_running', return_value=True), \
             patch.object(gui.runtime, 'stop_server', side_effect=Exception("Test error")):

            result = gui.stop_server()
            assert "error" in result.lower()
            assert "test error" in result.lower()

    def test_restart_server(self, gui, tmp_path):
        """Test restarting server."""
        gui.config.llama_server_path = tmp_path / "llama-server"
        gui.config.llama_server_path.touch()
        gui.config._has_local_server_section = True

        with patch.object(gui, 'stop_server', return_value="Server stopped") as mock_stop, \
             patch.object(gui, 'start_server', return_value="Server started") as mock_start, \
             patch('time.sleep'):  # Mock sleep to speed up test

            result = gui.restart_server()
            mock_stop.assert_called_once()
            mock_start.assert_called_once()
            assert "restart" in result.lower()

    def test_list_models_empty(self, gui):
        """Test listing models when none available."""
        with patch.object(gui.model_manager, 'list_downloaded_models', return_value=[]):
            result = gui.list_models()
            assert "no models" in result.lower()

    def test_list_models_with_models(self, gui):
        """Test listing models."""
        mock_models = ["model1.gguf", "model2.gguf"]

        with patch.object(gui.model_manager, 'list_downloaded_models', return_value=mock_models):
            result = gui.list_models()
            assert "model1.gguf" in result
            assert "model2.gguf" in result

    def test_download_model_missing_info(self, gui):
        """Test downloading model with missing information."""
        # Generator returns multiple values, get the last one
        results = list(gui.download_model("HuggingFace", "", "", ""))
        result = results[-1] if results else ""
        assert "provide" in result.lower() and "model name" in result.lower()

    def test_download_model_success(self, gui):
        """Test successful model download."""
        with patch.object(gui.model_manager, 'download_model', return_value=None) as mock_download:
            # Generator returns multiple values, get the last one
            results = list(gui.download_model("HuggingFace", "org/model", "", ""))
            result = results[-1] if results else ""
            mock_download.assert_called_once()
            assert "success" in result.lower() or "downloaded" in result.lower()

    def test_download_model_error(self, gui):
        """Test model download error handling."""
        with patch.object(gui.model_manager, 'download_model', side_effect=Exception("Download failed")):
            # Generator returns multiple values, get the last one
            results = list(gui.download_model("HuggingFace", "org/model", "", ""))
            result = results[-1] if results else ""
            assert "error" in result.lower()
            assert "download failed" in result.lower()

    def test_get_model_info_not_found(self, gui):
        """Test getting info for non-existent model."""
        with patch.object(gui.model_manager, 'get_model_info', return_value=None):
            result = gui.get_model_info("nonexistent")
            assert "not found" in result.lower()

    def test_get_model_info_success(self, gui):
        """Test getting model info successfully."""
        mock_info = {
            "downloaded": True,
            "path": "/path/to/test_model.gguf",
            "size": "5.0 GB"
        }

        with patch.object(gui.model_manager, 'get_model_info', return_value=mock_info):
            result = gui.get_model_info("test_model")
            assert "test_model" in result

    def test_load_config(self, gui, tmp_path):
        """Test loading config file."""
        config_file = tmp_path / "config.json"
        config_data = {"test": "data"}
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        with patch('llf.gui.Config.DEFAULT_CONFIG_FILE', config_file):
            result = gui.load_config()
            assert "test" in result
            assert "data" in result

    def test_load_config_missing_file(self, gui, tmp_path):
        """Test loading missing config file."""
        missing_file = tmp_path / "nonexistent.json"

        with patch('llf.gui.Config.DEFAULT_CONFIG_FILE', missing_file):
            result = gui.load_config()
            assert "not found" in result.lower() or "create one" in result.lower()

    def test_save_config_invalid_json(self, gui):
        """Test saving invalid JSON to config."""
        result = gui.save_config("not valid json{")
        assert "invalid json" in result.lower()

    def test_save_config_success(self, gui, tmp_path):
        """Test successfully saving config."""
        config_file = tmp_path / "config.json"

        new_config = {"new": "configuration"}

        with patch('llf.gui.Config.DEFAULT_CONFIG_FILE', config_file), \
             patch('llf.gui.get_config') as mock_get_config:
            mock_get_config.return_value = gui.config
            result = gui.save_config(json.dumps(new_config, indent=2))

            assert "saved" in result.lower() or "success" in result.lower()
            assert config_file.exists()

            # Verify content
            with open(config_file, 'r') as f:
                saved_data = json.load(f)
            assert saved_data["new"] == "configuration"

    def test_load_prompt_config(self, gui, tmp_path):
        """Test loading prompt config file."""
        config_file = tmp_path / "config_prompt.json"
        config_data = {"system_prompt": "Test prompt"}
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        with patch('llf.gui.PromptConfig.DEFAULT_CONFIG_FILE', config_file):
            result = gui.load_prompt_config()
            assert "system_prompt" in result
            assert "Test prompt" in result

    def test_load_prompt_config_missing_file(self, gui, tmp_path):
        """Test loading missing prompt config file."""
        missing_file = tmp_path / "nonexistent_prompt.json"

        with patch('llf.gui.PromptConfig.DEFAULT_CONFIG_FILE', missing_file):
            result = gui.load_prompt_config()
            assert "not found" in result.lower() or "customize" in result.lower()

    def test_save_prompt_config_invalid_json(self, gui):
        """Test saving invalid JSON to prompt config."""
        result = gui.save_prompt_config("not valid json{")
        assert "invalid json" in result.lower()

    def test_save_prompt_config_success(self, gui, tmp_path):
        """Test successfully saving prompt config."""
        config_file = tmp_path / "config_prompt.json"

        new_config = {"system_prompt": "New prompt"}

        with patch('llf.gui.PromptConfig.DEFAULT_CONFIG_FILE', config_file), \
             patch('llf.gui.get_prompt_config') as mock_get_prompt_config:
            mock_get_prompt_config.return_value = gui.prompt_config
            result = gui.save_prompt_config(json.dumps(new_config, indent=2))

            assert "saved" in result.lower() or "success" in result.lower()
            assert config_file.exists()

            # Verify content
            with open(config_file, 'r') as f:
                saved_data = json.load(f)
            assert saved_data["system_prompt"] == "New prompt"

    def test_backup_config_success(self, gui, temp_dir):
        """Test successful config backup via GUI."""
        config_file = temp_dir / "config.json"
        config_file.write_text('{"test": "data"}')

        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(exist_ok=True)

        gui.config.CONFIG_BACKUPS_DIR = backup_dir

        with patch('llf.gui.Config.DEFAULT_CONFIG_FILE', config_file):
            result = gui.backup_config()

            assert "success" in result.lower() or "✅" in result
            # Verify backup file was created
            backups = list(backup_dir.glob("config_*.json"))
            assert len(backups) == 1

    def test_backup_config_file_not_found(self, gui, temp_dir):
        """Test backup fails when config doesn't exist."""
        nonexistent = temp_dir / "nonexistent.json"

        with patch('llf.gui.Config.DEFAULT_CONFIG_FILE', nonexistent):
            result = gui.backup_config()

            assert "❌" in result or "error" in result.lower()

    def test_backup_prompt_config_success(self, gui, temp_dir):
        """Test successful prompt config backup via GUI."""
        config_file = temp_dir / "config_prompt.json"
        config_file.write_text('{"system_prompt": "test"}')

        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(exist_ok=True)

        gui.prompt_config.CONFIG_BACKUPS_DIR = backup_dir

        with patch('llf.gui.PromptConfig.DEFAULT_CONFIG_FILE', config_file):
            result = gui.backup_prompt_config()

            assert "success" in result.lower() or "✅" in result
            # Verify backup file was created
            backups = list(backup_dir.glob("config_prompt_*.json"))
            assert len(backups) == 1

    def test_backup_prompt_config_file_not_found(self, gui, temp_dir):
        """Test prompt config backup fails when file doesn't exist."""
        nonexistent = temp_dir / "nonexistent.json"

        with patch('llf.gui.PromptConfig.DEFAULT_CONFIG_FILE', nonexistent):
            result = gui.backup_prompt_config()

            assert "❌" in result or "error" in result.lower()

    def test_chat_respond(self, gui):
        """Test chat response."""
        def mock_stream():
            yield "Test "
            yield "response"

        with patch.object(gui.runtime, 'chat', return_value=mock_stream()) as mock_chat:
            history = []
            results = list(gui.chat_respond("Hello", history))

            # Get the final result
            cleared_input, new_history = results[-1]

            assert cleared_input == ""
            assert len(new_history) == 2
            assert new_history[0] == {"role": "user", "content": "Hello"}
            assert new_history[1] == {"role": "assistant", "content": "Test response"}
            mock_chat.assert_called_once()

    def test_chat_respond_with_history(self, gui):
        """Test chat response with existing history."""
        def mock_stream():
            yield "Response "
            yield "2"

        with patch.object(gui.runtime, 'chat', return_value=mock_stream()) as mock_chat:
            history = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there"}]
            results = list(gui.chat_respond("How are you?", history))

            # Get the final result
            cleared_input, new_history = results[-1]

            assert cleared_input == ""
            assert len(new_history) == 4
            assert new_history[2] == {"role": "user", "content": "How are you?"}
            assert new_history[3] == {"role": "assistant", "content": "Response 2"}

    def test_chat_respond_error(self, gui):
        """Test chat response error handling."""
        with patch.object(gui.runtime, 'chat', side_effect=Exception("API Error")):
            history = []
            results = list(gui.chat_respond("Hello", history))

            # Get the final result
            cleared_input, new_history = results[-1]

            assert cleared_input == ""
            assert len(new_history) == 2
            assert new_history[0] == {"role": "user", "content": "Hello"}
            error_msg = new_history[1]["content"]
            assert "error" in error_msg.lower()
            assert "api error" in error_msg.lower()

    def test_clear_chat(self, gui):
        """Test clearing chat history."""
        result = gui.clear_chat()

        assert result == []

    def test_create_interface(self, gui):
        """Test creating Gradio interface."""
        # Just test that it creates without error
        # We can't easily mock all Gradio components
        interface = gui.create_interface()
        assert interface is not None

    def test_launch(self, gui):
        """Test launching GUI with default parameters."""
        mock_interface = Mock()

        with patch.object(gui, 'create_interface', return_value=mock_interface):
            gui.launch()

            mock_interface.launch.assert_called_once()
            call_kwargs = mock_interface.launch.call_args[1]
            assert call_kwargs['server_name'] == "127.0.0.1"
            assert call_kwargs['server_port'] == 7860
            assert call_kwargs['inbrowser'] == True

    def test_launch_with_network_access(self, gui):
        """Test launching GUI with network access (server_name='0.0.0.0')."""
        mock_interface = Mock()

        with patch.object(gui, 'create_interface', return_value=mock_interface):
            gui.launch(server_name="0.0.0.0", server_port=8080, inbrowser=False)

            mock_interface.launch.assert_called_once()
            call_kwargs = mock_interface.launch.call_args[1]
            assert call_kwargs['server_name'] == "0.0.0.0"
            assert call_kwargs['server_port'] == 8080
            assert call_kwargs['inbrowser'] == False

    def test_launch_localhost_only(self, gui):
        """Test launching GUI on localhost only."""
        mock_interface = Mock()

        with patch.object(gui, 'create_interface', return_value=mock_interface):
            gui.launch(server_name="127.0.0.1", server_port=7860)

            mock_interface.launch.assert_called_once()
            call_kwargs = mock_interface.launch.call_args[1]
            assert call_kwargs['server_name'] == "127.0.0.1"
            assert call_kwargs['server_port'] == 7860


class TestStartGUI:
    """Test start_gui function."""

    def test_start_gui_default_params(self):
        """Test starting GUI with default parameters."""
        with patch('llf.gui.LLMFrameworkGUI') as mock_gui_class:
            mock_gui_instance = Mock()
            mock_gui_class.return_value = mock_gui_instance

            start_gui()

            mock_gui_class.assert_called_once_with(config=None, prompt_config=None, auth_key=None)
            # Check that launch was called (with no kwargs by default)
            mock_gui_instance.launch.assert_called_once()

    def test_start_gui_custom_params(self):
        """Test starting GUI with custom parameters."""
        mock_config = Mock()
        mock_prompt_config = Mock()

        with patch('llf.gui.LLMFrameworkGUI') as mock_gui_class:
            mock_gui_instance = Mock()
            mock_gui_class.return_value = mock_gui_instance

            start_gui(
                config=mock_config,
                prompt_config=mock_prompt_config,
                server_name="0.0.0.0",
                server_port=8080,
                auth_key="test_key",
                inbrowser=False
            )

            mock_gui_class.assert_called_once_with(
                config=mock_config,
                prompt_config=mock_prompt_config,
                auth_key="test_key"
            )
            mock_gui_instance.launch.assert_called_once_with(
                server_name="0.0.0.0",
                server_port=8080,
                inbrowser=False
            )


class TestNewGUIMethods:
    """Test new GUI methods added for enhanced functionality."""

    @pytest.fixture
    def gui(self):
        """Create GUI instance for testing."""
        with patch('llf.gui.get_config') as mock_get_config, \
             patch('llf.gui.get_prompt_config') as mock_get_prompt_config:

            mock_config = Mock()
            mock_config.model_dir = Path("/tmp/models")
            mock_config.cache_dir = Path("/tmp/cache")
            mock_config.model_name = "test-model"
            mock_config.is_using_external_api.return_value = False
            mock_config.has_local_server_config.return_value = True

            mock_prompt_config = Mock()

            mock_get_config.return_value = mock_config
            mock_get_prompt_config.return_value = mock_prompt_config

            return LLMFrameworkGUI()

    def test_toggle_download_sections_huggingface(self):
        """Test toggle_download_sections with HuggingFace selection."""
        hf_update, url_update = LLMFrameworkGUI.toggle_download_sections("HuggingFace")
        assert hf_update['visible'] is True
        assert url_update['visible'] is False

    def test_toggle_download_sections_url(self):
        """Test toggle_download_sections with URL selection."""
        hf_update, url_update = LLMFrameworkGUI.toggle_download_sections("URL")
        assert hf_update['visible'] is False
        assert url_update['visible'] is True

    def test_list_models_for_radio_empty(self, gui):
        """Test list_models_for_radio with no models."""
        with patch.object(gui.model_manager, 'list_downloaded_models', return_value=[]):
            result = gui.list_models_for_radio()
            assert result == ["Default"]

    def test_list_models_for_radio_with_models(self, gui):
        """Test list_models_for_radio with multiple models."""
        mock_models = ["model1", "model2", "model3"]
        with patch.object(gui.model_manager, 'list_downloaded_models', return_value=mock_models):
            result = gui.list_models_for_radio()
            assert result == ["Default", "model1", "model2", "model3"]
            assert result[0] == "Default"  # Default should always be first

    def test_list_models_for_radio_error(self, gui):
        """Test list_models_for_radio handles errors gracefully."""
        with patch.object(gui.model_manager, 'list_downloaded_models', side_effect=Exception("Error")):
            result = gui.list_models_for_radio()
            assert result == ["Default"]  # Should return Default on error

    def test_get_selected_model_info_default(self, gui):
        """Test get_selected_model_info with Default selection."""
        with patch.object(gui, 'get_model_info', return_value="Model info") as mock_info:
            result = gui.get_selected_model_info("Default")
            mock_info.assert_called_once_with("test-model")  # Should use config.model_name
            assert result == "Model info"

    def test_get_selected_model_info_custom(self, gui):
        """Test get_selected_model_info with custom model."""
        with patch.object(gui, 'get_model_info', return_value="Custom model info") as mock_info:
            result = gui.get_selected_model_info("custom-model")
            mock_info.assert_called_once_with("custom-model")
            assert result == "Custom model info"

    def test_get_selected_model_info_empty(self, gui):
        """Test get_selected_model_info with empty selection."""
        result = gui.get_selected_model_info("")
        assert result == ""

    def test_get_selected_model_info_error(self, gui):
        """Test get_selected_model_info handles errors."""
        with patch.object(gui, 'get_model_info', side_effect=Exception("Error")):
            result = gui.get_selected_model_info("model")
            assert "error" in result.lower()

    def test_refresh_models_list_success(self, gui):
        """Test refresh_models_list successfully refreshes."""
        mock_models = ["model1", "model2"]
        with patch.object(gui, 'list_models_for_radio', return_value=["Default"] + mock_models), \
             patch.object(gui, 'get_selected_model_info', return_value="Default model info"):

            radio_update, info = gui.refresh_models_list()

            # Radio component returns tuples (label, value) for choices
            expected_choices = [("Default", "Default"), ("model1", "model1"), ("model2", "model2")]
            assert radio_update.choices == expected_choices
            assert radio_update.value == "Default"
            assert info == "Default model info"

    def test_refresh_models_list_error(self, gui):
        """Test refresh_models_list handles errors."""
        with patch.object(gui, 'list_models_for_radio', side_effect=Exception("Error")):
            radio_update, info = gui.refresh_models_list()
            # Radio component returns tuples (label, value) for choices
            assert radio_update.choices == [("Default", "Default")]
            assert "error" in info.lower()

    def test_reload_config_with_status_success(self, gui, temp_dir):
        """Test reload_config_with_status successfully reloads."""
        config_file = temp_dir / "config.json"
        config_content = '{"test": "data"}'
        config_file.write_text(config_content)

        with patch('llf.gui.Config.DEFAULT_CONFIG_FILE', config_file):
            content, status = gui.reload_config_with_status()
            assert content == config_content
            assert "✅" in status
            assert "successfully" in status.lower()

    def test_reload_config_with_status_file_not_found(self, gui, temp_dir):
        """Test reload_config_with_status when file doesn't exist."""
        nonexistent = temp_dir / "nonexistent.json"

        with patch('llf.gui.Config.DEFAULT_CONFIG_FILE', nonexistent):
            content, status = gui.reload_config_with_status()
            assert "not found" in content.lower()
            assert "❌" in status

    def test_reload_config_with_status_error(self, gui, temp_dir):
        """Test reload_config_with_status handles read errors."""
        config_file = temp_dir / "config.json"
        config_file.write_text("test")

        with patch('llf.gui.Config.DEFAULT_CONFIG_FILE', config_file), \
             patch('builtins.open', side_effect=PermissionError("No permission")):
            content, status = gui.reload_config_with_status()
            assert "error" in content.lower()
            assert "❌" in status

    def test_reload_prompt_config_with_status_success(self, gui, temp_dir):
        """Test reload_prompt_config_with_status successfully reloads."""
        config_file = temp_dir / "config_prompt.json"
        config_content = '{"system_prompt": "test"}'
        config_file.write_text(config_content)

        with patch('llf.gui.PromptConfig.DEFAULT_CONFIG_FILE', config_file):
            content, status = gui.reload_prompt_config_with_status()
            assert content == config_content
            assert "✅" in status
            assert "successfully" in status.lower()

    def test_reload_prompt_config_with_status_file_not_found(self, gui, temp_dir):
        """Test reload_prompt_config_with_status when file doesn't exist."""
        nonexistent = temp_dir / "nonexistent.json"

        with patch('llf.gui.PromptConfig.DEFAULT_CONFIG_FILE', nonexistent):
            content, status = gui.reload_prompt_config_with_status()
            assert "not found" in content.lower()
            assert "❌" in status

    def test_reload_prompt_config_with_status_error(self, gui, temp_dir):
        """Test reload_prompt_config_with_status handles read errors."""
        config_file = temp_dir / "config_prompt.json"
        config_file.write_text("test")

        with patch('llf.gui.PromptConfig.DEFAULT_CONFIG_FILE', config_file), \
             patch('builtins.open', side_effect=PermissionError("No permission")):
            content, status = gui.reload_prompt_config_with_status()
            assert "error" in content.lower()
            assert "❌" in status

    def test_download_model_url_missing_url(self, gui):
        """Test download_model with URL type but missing URL."""
        results = list(gui.download_model("URL", "", "", ""))
        result = results[-1] if results else ""
        assert "url" in result.lower()

    def test_download_model_url_missing_name(self, gui):
        """Test download_model with URL type but missing custom name."""
        results = list(gui.download_model("URL", "", "http://example.com/model.gguf", ""))
        result = results[-1] if results else ""
        assert "name" in result.lower()

    def test_download_model_url_success(self, gui):
        """Test successful URL download."""
        with patch.object(gui.model_manager, 'download_from_url', return_value=None) as mock_download:
            results = list(gui.download_model("URL", "", "http://example.com/model.gguf", "my-model"))
            result = results[-1] if results else ""

            mock_download.assert_called_once_with(
                url="http://example.com/model.gguf",
                name="my-model"
            )
            assert "success" in result.lower()

    def test_download_model_url_error(self, gui):
        """Test URL download error handling."""
        with patch.object(gui.model_manager, 'download_from_url', side_effect=Exception("Download failed")):
            results = list(gui.download_model("URL", "", "http://example.com/model.gguf", "my-model"))
            result = results[-1] if results else ""
            assert "error" in result.lower()
            assert "download failed" in result.lower()
