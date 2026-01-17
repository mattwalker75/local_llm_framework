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
        with patch.object(LLMFrameworkGUI, '_load_modules'):
            # Prevent loading TTS/STT modules during tests (causes hangs)
            gui_instance = LLMFrameworkGUI(config=mock_config, prompt_config=mock_prompt_config)
            # Ensure tts and stt are None (not loaded)
            gui_instance.tts = None
            gui_instance.stt = None
            return gui_instance

    def test_initialization(self, gui):
        """Test GUI initialization."""
        assert gui.config is not None
        assert gui.prompt_config is not None
        assert gui.model_manager is not None
        assert gui.runtime is not None

    def test_initialization_with_defaults(self, tmp_path):
        """Test GUI initialization with default configs."""
        with patch('llf.gui.get_config') as mock_get_config, \
             patch('llf.gui.get_prompt_config') as mock_get_prompt_config:

            mock_config = Mock()
            mock_config.config_file = tmp_path / "config.json"
            mock_get_config.return_value = mock_config
            mock_get_prompt_config.return_value = Mock()

            gui = LLMFrameworkGUI()

            assert gui.config is not None
            assert gui.prompt_config is not None
            mock_get_config.assert_called_once()
            mock_get_prompt_config.assert_called_once()

    def test_initialization_with_auth_key(self, tmp_path):
        """Test GUI initialization with authentication key."""
        with patch('llf.gui.get_config') as mock_get_config, \
             patch('llf.gui.get_prompt_config') as mock_get_prompt_config:

            mock_config = Mock()
            mock_config.config_file = tmp_path / "config.json"
            mock_get_config.return_value = mock_config
            mock_get_prompt_config.return_value = Mock()

            auth_key = "test_secret_key_123"
            gui = LLMFrameworkGUI(auth_key=auth_key)

            assert gui.auth_key == auth_key
            assert gui.config is not None
            assert gui.prompt_config is not None

    def test_initialization_without_auth_key(self, tmp_path):
        """Test GUI initialization without authentication key."""
        with patch('llf.gui.get_config') as mock_get_config, \
             patch('llf.gui.get_prompt_config') as mock_get_prompt_config:

            mock_config = Mock()
            mock_config.config_file = tmp_path / "config.json"
            mock_get_config.return_value = mock_config
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

            # shutdown_gui no longer takes history/save_enabled args (incremental logging)
            result = gui.shutdown_gui()

            mock_stop.assert_called_once()
            assert "shutting down" in result.lower()

    def test_shutdown_gui_without_started_server(self, gui):
        """Test shutdown leaves server running if GUI didn't start it."""
        gui.started_server = False

        with patch.object(gui.runtime, 'is_server_running', return_value=True), \
             patch.object(gui.runtime, 'stop_server') as mock_stop:

            # shutdown_gui no longer takes history/save_enabled args (incremental logging)
            result = gui.shutdown_gui()

            mock_stop.assert_not_called()
            assert "shutting down" in result.lower()

    def test_shutdown_gui_no_server_running(self, gui):
        """Test shutdown when no server is running."""
        with patch.object(gui.runtime, 'is_server_running', return_value=False), \
             patch.object(gui.runtime, 'stop_server') as mock_stop:

            # shutdown_gui no longer takes history/save_enabled args (incremental logging)
            result = gui.shutdown_gui()

            mock_stop.assert_not_called()
            assert "shutting down" in result.lower()

    def test_shutdown_gui_error(self, gui):
        """Test shutdown error handling."""
        gui.started_server = True

        with patch.object(gui.config, 'has_local_server_config', return_value=True), \
             patch.object(gui.runtime, 'is_server_running', return_value=True), \
             patch.object(gui.runtime, 'stop_server', side_effect=Exception("Stop error")):

            # shutdown_gui no longer takes history/save_enabled args (incremental logging)
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
             patch.object(gui.model_manager, 'is_model_downloaded', return_value=True), \
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

        # Mock prompt_config to have no tools for simpler streaming test
        with patch.object(gui.prompt_config, 'get_all_tools', return_value=None), \
             patch.object(gui.runtime, 'chat', return_value=mock_stream()) as mock_chat:
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

        # Mock prompt_config to have no tools for simpler streaming test
        with patch.object(gui.prompt_config, 'get_all_tools', return_value=None), \
             patch.object(gui.runtime, 'chat', return_value=mock_stream()) as mock_chat:
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

    def test_chat_respond_with_tools_dual_pass(self, gui):
        """Test chat response with tools in dual-pass mode."""
        # Mock prompt_config to have tools
        with patch.object(gui.prompt_config, 'get_memory_tools', return_value=[{'name': 'search_memories'}]):
            # Mock config to use dual_pass_write_only mode
            gui.config.tool_execution_mode = 'dual_pass_write_only'

            def mock_stream():
                yield "Searching "
                yield "memory..."

            # Mock the chat calls
            call_count = [0]
            def mock_chat(messages, stream=False, use_prompt_config=True):
                call_count[0] += 1
                if stream:
                    return mock_stream()
                else:
                    return "Background execution"

            with patch.object(gui.runtime, 'chat', side_effect=mock_chat), \
                 patch('llf.operation_detector.detect_operation_type', return_value='read'), \
                 patch('llf.operation_detector.should_use_dual_pass', return_value=True):

                history = []
                results = list(gui.chat_respond("What is my name?", history))

                # Get the final result
                cleared_input, new_history = results[-1]

                assert cleared_input == ""
                assert len(new_history) == 2
                assert new_history[0] == {"role": "user", "content": "What is my name?"}
                assert new_history[1] == {"role": "assistant", "content": "Searching memory..."}

                # Verify that chat was called for streaming (Pass 1)
                # Pass 2 happens in background thread, so we can't easily verify it here
                assert call_count[0] >= 1

    def test_chat_respond_with_tools_single_pass(self, gui):
        """Test chat response with tools in single-pass mode."""
        # Mock prompt_config to have tools
        with patch.object(gui.prompt_config, 'get_memory_tools', return_value=[{'name': 'search_memories'}]):
            # Mock config to use single_pass mode
            gui.config.tool_execution_mode = 'single_pass'

            # Mock the chat call to return non-streaming response
            with patch.object(gui.runtime, 'chat', return_value="I found your name in memory.") as mock_chat, \
                 patch('llf.operation_detector.detect_operation_type', return_value='read'), \
                 patch('llf.operation_detector.should_use_dual_pass', return_value=False):

                history = []
                results = list(gui.chat_respond("What is my name?", history))

                # Get the final result
                cleared_input, new_history = results[-1]

                assert cleared_input == ""
                assert len(new_history) == 2
                assert new_history[0] == {"role": "user", "content": "What is my name?"}
                assert new_history[1] == {"role": "assistant", "content": "I found your name in memory."}

                # Verify that chat was called with stream=False (single-pass)
                mock_chat.assert_called_once()
                assert mock_chat.call_args[1]['stream'] is False

    def test_chat_respond_no_tools_streaming(self, gui):
        """Test chat response when no tools are available (streaming)."""
        # Mock prompt_config to have no tools
        with patch.object(gui.prompt_config, 'get_all_tools', return_value=None):

            def mock_stream():
                yield "Hello "
                yield "there!"

            with patch.object(gui.runtime, 'chat', return_value=mock_stream()) as mock_chat:
                history = []
                results = list(gui.chat_respond("Hi", history))

                # Get the final result
                cleared_input, new_history = results[-1]

                assert cleared_input == ""
                assert len(new_history) == 2
                assert new_history[0] == {"role": "user", "content": "Hi"}
                assert new_history[1] == {"role": "assistant", "content": "Hello there!"}

                # Verify streaming mode was used
                mock_chat.assert_called_once()
                assert mock_chat.call_args[1]['stream'] is True

    def test_clear_chat(self, gui):
        """Test clearing chat history."""
        result = gui.clear_chat()

        # clear_chat returns empty list for chatbot
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

            mock_gui_class.assert_called_once_with(config=None, prompt_config=None, auth_key=None, share=False)
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
                auth_key="test_key",
                share=False
            )
            mock_gui_instance.launch.assert_called_once_with(
                server_name="0.0.0.0",
                server_port=8080,
                inbrowser=False
            )


class TestNewGUIMethods:
    """Test new GUI methods added for enhanced functionality."""

    @pytest.fixture
    def gui(self, tmp_path):
        """Create GUI instance for testing."""
        with patch('llf.gui.get_config') as mock_get_config, \
             patch('llf.gui.get_prompt_config') as mock_get_prompt_config:

            mock_config = Mock()
            mock_config.model_dir = Path("/tmp/models")
            mock_config.cache_dir = Path("/tmp/cache")
            mock_config.model_name = "test-model"
            mock_config.config_file = tmp_path / "config.json"  # Required for chat history init
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


class TestShareModeTTS:
    """Test share mode TTS functionality."""

    @pytest.fixture
    def temp_config(self, tmp_path):
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

        return Config(config_file)

    @pytest.fixture
    def temp_prompt_config(self, tmp_path):
        """Create mock prompt config for testing."""
        config_file = tmp_path / "config_prompt.json"
        config_data = {
            "system_prompt": "Test system prompt",
            "conversation_format": "standard"
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        return PromptConfig(config_file)

    def test_initialization_with_share_mode(self, temp_config, temp_prompt_config):
        """Test GUI initialization with share mode enabled."""
        with patch.object(LLMFrameworkGUI, '_load_modules'):
            gui = LLMFrameworkGUI(config=temp_config, prompt_config=temp_prompt_config, share=True)
            gui.tts = None
            gui.stt = None
            assert gui.is_share_mode is True

    def test_initialization_without_share_mode(self, temp_config, temp_prompt_config):
        """Test GUI initialization without share mode (default)."""
        with patch.object(LLMFrameworkGUI, '_load_modules'):
            gui = LLMFrameworkGUI(config=temp_config, prompt_config=temp_prompt_config)
            gui.tts = None
            gui.stt = None
            assert gui.is_share_mode is False

    def test_chat_respond_share_mode_no_tts(self, temp_config, temp_prompt_config):
        """Test chat_respond in share mode without TTS enabled."""
        with patch.object(LLMFrameworkGUI, '_load_modules'):
            gui = LLMFrameworkGUI(config=temp_config, prompt_config=temp_prompt_config, share=True)
            gui.tts = None  # No TTS module
            gui.stt = None

            with patch.object(gui.runtime, 'chat', return_value=iter(["Hello", " world"])):
                results = list(gui.chat_respond("test", []))
                # Should complete without errors
                assert len(results) > 0
                final_result = results[-1]
                assert final_result[0] == ""  # Message cleared
                assert len(final_result[1]) == 2  # User + assistant messages

    def test_chat_respond_share_mode_with_tts(self, temp_config, temp_prompt_config):
        """Test chat_respond in share mode with TTS enabled (should not call pyttsx3)."""
        with patch.object(LLMFrameworkGUI, '_load_modules'):
            gui = LLMFrameworkGUI(config=temp_config, prompt_config=temp_prompt_config, share=True)
            gui.stt = None

            # Mock TTS module
            mock_tts = Mock()
            gui.tts = mock_tts

            with patch.object(gui.runtime, 'chat', return_value=iter(["Hello", " world"])):
                results = list(gui.chat_respond("test", []))

                # Should complete without errors
                assert len(results) > 0

                # In share mode, pyttsx3.speak should NOT be called (browser handles TTS)
                mock_tts.speak.assert_not_called()

    def test_chat_respond_local_mode_with_tts(self, temp_config, temp_prompt_config):
        """Test chat_respond in local mode with TTS enabled (should call pyttsx3)."""
        with patch.object(LLMFrameworkGUI, '_load_modules'):
            gui = LLMFrameworkGUI(config=temp_config, prompt_config=temp_prompt_config, share=False)
            gui.stt = None

            # Mock TTS module
            mock_tts = Mock()
            mock_tts.speak.return_value = None
            gui.tts = mock_tts

            def mock_stream():
                yield "Hello"
                yield " world"

            # Mock prompt_config to have no tools for simpler streaming test
            with patch.object(gui.prompt_config, 'get_all_tools', return_value=None), \
                 patch.object(gui.runtime, 'chat', return_value=mock_stream()):
                results = list(gui.chat_respond("test", []))

                # Should complete without errors
                assert len(results) > 0

                # In local mode, pyttsx3.speak SHOULD be called
                mock_tts.speak.assert_called_once_with("Hello world")

    def test_start_gui_with_share_true(self, temp_config, temp_prompt_config):
        """Test that start_gui correctly passes share=True to GUI constructor."""
        with patch('llf.gui.get_config', return_value=temp_config), \
             patch('llf.gui.get_prompt_config', return_value=temp_prompt_config), \
             patch.object(LLMFrameworkGUI, '_load_modules'), \
             patch.object(LLMFrameworkGUI, 'launch') as mock_launch:

            start_gui(share=True)

            # Verify launch was called
            mock_launch.assert_called_once()

    def test_create_interface_share_mode(self, temp_config, temp_prompt_config):
        """Test that create_interface adds JavaScript TTS handlers in share mode."""
        with patch.object(LLMFrameworkGUI, '_load_modules'):
            gui = LLMFrameworkGUI(config=temp_config, prompt_config=temp_prompt_config, share=True)
            gui.stt = None

            # Mock TTS module
            mock_tts = Mock()
            gui.tts = mock_tts

            # Create interface should not raise errors
            interface = gui.create_interface()
            assert interface is not None

    def test_create_interface_local_mode(self, temp_config, temp_prompt_config):
        """Test that create_interface works in local mode without JavaScript handlers."""
        with patch.object(LLMFrameworkGUI, '_load_modules'):
            gui = LLMFrameworkGUI(config=temp_config, prompt_config=temp_prompt_config, share=False)
            gui.tts = None
            gui.stt = None

            # Create interface should not raise errors
            interface = gui.create_interface()
            assert interface is not None


class TestMultiServerGUI:
    """Test multi-server GUI functionality."""

    @pytest.fixture
    def multi_server_config(self, tmp_path):
        """Create multi-server config for testing."""
        from llf.config import ServerConfig
        config = Config()

        # Create server configs
        server1 = ServerConfig(
            name='server1',
            llama_server_path=tmp_path / 'llama-server',
            server_host='127.0.0.1',
            server_port=8000,
            healthcheck_interval=2.0,
            model_dir=tmp_path / 'models' / 'server1',
            gguf_file='model1.gguf',
            server_params={},
            auto_start=False
        )

        server2 = ServerConfig(
            name='server2',
            llama_server_path=tmp_path / 'llama-server',
            server_host='127.0.0.1',
            server_port=8001,
            healthcheck_interval=2.0,
            model_dir=tmp_path / 'models' / 'server2',
            gguf_file='model2.gguf',
            server_params={},
            auto_start=False
        )

        config.servers = {
            'server1': server1,
            'server2': server2
        }
        config.default_local_server = 'server1'
        config.model_dir = tmp_path / 'models'

        return config

    @pytest.fixture
    def gui(self, multi_server_config, tmp_path):
        """Create GUI instance with multi-server config."""
        prompt_config_file = tmp_path / "config_prompt.json"
        prompt_config_data = {
            "system_prompt": "Test prompt",
            "conversation_format": "standard"
        }
        with open(prompt_config_file, 'w') as f:
            json.dump(prompt_config_data, f)

        prompt_config = PromptConfig(prompt_config_file)

        with patch.object(LLMFrameworkGUI, '_load_modules'):
            gui_instance = LLMFrameworkGUI(config=multi_server_config, prompt_config=prompt_config)
            gui_instance.tts = None
            gui_instance.stt = None
            return gui_instance

    def test_get_available_servers(self, gui):
        """Test getting available servers list."""
        servers = gui.get_available_servers()
        assert servers == ['server1', 'server2']

    def test_get_available_servers_empty(self, gui):
        """Test getting available servers when none configured."""
        gui.config.servers = {}
        servers = gui.get_available_servers()
        assert servers == ["No servers configured"]

    def test_get_available_servers_error(self, gui):
        """Test get_available_servers error handling."""
        with patch.object(gui.config, 'list_servers', side_effect=Exception("Error")):
            servers = gui.get_available_servers()
            assert servers == ["Error loading servers"]

    def test_get_server_info(self, gui):
        """Test getting server info."""
        info = gui.get_server_info('server1')

        assert 'server1' in info
        assert '127.0.0.1' in info
        assert '8000' in info
        assert 'model1.gguf' in info
        assert '⭐ ACTIVE' in info  # server1 is the active server

    def test_get_server_info_not_active(self, gui):
        """Test getting info for non-active server."""
        info = gui.get_server_info('server2')

        assert 'server2' in info
        assert '8001' in info
        assert '⭐ ACTIVE' not in info  # server2 is not active

    def test_get_server_info_running(self, gui):
        """Test server info shows running status."""
        with patch.object(gui.runtime, 'is_server_running_by_name', return_value=True):
            info = gui.get_server_info('server1')
            assert '🟢 Running' in info

    def test_get_server_info_stopped(self, gui):
        """Test server info shows stopped status."""
        with patch.object(gui.runtime, 'is_server_running_by_name', return_value=False):
            info = gui.get_server_info('server1')
            assert '⭕ Stopped' in info

    def test_get_server_info_not_found(self, gui):
        """Test getting info for non-existent server."""
        info = gui.get_server_info('nonexistent')
        assert "not found" in info.lower()

    def test_get_server_info_no_selection(self, gui):
        """Test getting info with no server selected."""
        info = gui.get_server_info('')
        assert "no server selected" in info.lower()

    def test_start_server_by_name_success(self, gui):
        """Test successfully starting a server by name."""
        with patch.object(gui.runtime, 'is_server_running_by_name', side_effect=[False, True]), \
             patch.object(gui.runtime, 'start_server_by_name') as mock_start, \
             patch.object(gui, 'get_server_info', return_value="Server info") as mock_info, \
             patch('llf.gui.time.sleep'):

            status, info = gui.start_server_by_name('server1')

            mock_start.assert_called_once_with('server1', force=True)
            assert "started successfully" in status.lower()
            assert info == "Server info"

    def test_start_server_by_name_already_running(self, gui):
        """Test starting server that's already running."""
        with patch.object(gui.runtime, 'is_server_running_by_name', return_value=True):
            status, info = gui.start_server_by_name('server1')
            assert "already running" in status.lower()

    def test_start_server_by_name_not_found(self, gui):
        """Test starting non-existent server."""
        status, info = gui.start_server_by_name('nonexistent')
        assert "not found" in status.lower()

    def test_start_server_by_name_no_selection(self, gui):
        """Test starting with no server selected."""
        status, info = gui.start_server_by_name('')
        assert "no server selected" in status.lower()

    def test_start_server_by_name_failed(self, gui):
        """Test server start failure."""
        with patch.object(gui.runtime, 'is_server_running_by_name', side_effect=[False, False]), \
             patch.object(gui.runtime, 'start_server_by_name'), \
             patch.object(gui, 'get_server_info', return_value="Server info"), \
             patch('llf.gui.time.sleep'):

            status, info = gui.start_server_by_name('server1')
            assert "failed to start" in status.lower()

    def test_start_server_by_name_error(self, gui):
        """Test server start error handling."""
        with patch.object(gui.runtime, 'is_server_running_by_name', return_value=False), \
             patch.object(gui.runtime, 'start_server_by_name', side_effect=Exception("Start error")):

            status, info = gui.start_server_by_name('server1')
            assert "error" in status.lower()
            assert "start error" in status.lower()

    def test_stop_server_by_name_success(self, gui):
        """Test successfully stopping a server by name."""
        with patch.object(gui.runtime, 'is_server_running_by_name', side_effect=[True, False]), \
             patch.object(gui.runtime, 'stop_server_by_name') as mock_stop, \
             patch.object(gui, 'get_server_info', return_value="Server info"), \
             patch('llf.gui.time.sleep'):

            status, info = gui.stop_server_by_name('server1')

            mock_stop.assert_called_once_with('server1')
            assert "stopped successfully" in status.lower()

    def test_stop_server_by_name_not_running(self, gui):
        """Test stopping server that's not running."""
        with patch.object(gui.runtime, 'is_server_running_by_name', return_value=False):
            status, info = gui.stop_server_by_name('server1')
            assert "not running" in status.lower()

    def test_stop_server_by_name_not_found(self, gui):
        """Test stopping non-existent server."""
        status, info = gui.stop_server_by_name('nonexistent')
        assert "not found" in status.lower()

    def test_stop_server_by_name_error(self, gui):
        """Test server stop error handling."""
        with patch.object(gui.runtime, 'is_server_running_by_name', return_value=True), \
             patch.object(gui.runtime, 'stop_server_by_name', side_effect=Exception("Stop error")):

            status, info = gui.stop_server_by_name('server1')
            assert "error" in status.lower()
            assert "stop error" in status.lower()

    def test_restart_server_by_name_success(self, gui):
        """Test successfully restarting a server by name."""
        with patch.object(gui, 'stop_server_by_name', return_value=("Stopped", "info")), \
             patch.object(gui, 'start_server_by_name', return_value=("Started", "updated_info")), \
             patch('llf.gui.time.sleep'):

            status, info = gui.restart_server_by_name('server1')

            assert "restart" in status.lower()
            assert "stopped" in status.lower()
            assert "started" in status.lower()
            assert info == "updated_info"

    def test_restart_server_by_name_error(self, gui):
        """Test server restart error handling."""
        with patch.object(gui, 'stop_server_by_name', side_effect=Exception("Restart error")):
            status, info = gui.restart_server_by_name('server1')
            assert "error" in status.lower()
            assert "restart error" in status.lower()

    def test_refresh_server_info(self, gui):
        """Test refreshing server information."""
        # First get initial info
        info1 = gui.get_server_info('server1')
        assert 'server1' in info1

        # Mock server as running
        with patch.object(gui.runtime, 'is_server_running_by_name', return_value=True):
            info2 = gui.get_server_info('server1')
            assert '🟢 Running' in info2

        # Mock server as stopped
        with patch.object(gui.runtime, 'is_server_running_by_name', return_value=False):
            info3 = gui.get_server_info('server1')
            assert '⭕ Stopped' in info3

    # ===== Memory Management Tests =====

    def test_get_available_memories(self, gui, temp_dir):
        """Test getting list of available memory instances."""
        # Create memory registry
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(exist_ok=True)
        registry = {
            "version": "1.0",
            "last_updated": "2025-12-27",
            "memories": [
                {"name": "main_memory", "display_name": "Main Memory", "enabled": False},
                {"name": "test_memory", "display_name": "Test Memory", "enabled": True}
            ]
        }
        registry_path = memory_dir / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        # Patch the registry path
        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = temp_dir
            memories = gui.get_available_memories()

            assert len(memories) == 2
            assert "Main Memory" in memories
            assert "Test Memory" in memories

    def test_get_available_memories_no_registry(self, gui):
        """Test getting memories when registry doesn't exist."""
        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = Path("/nonexistent")
            memories = gui.get_available_memories()
            assert memories == []

    def test_get_memory_info(self, gui, temp_dir):
        """Test getting information about a specific memory."""
        # Create memory registry
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(exist_ok=True)
        registry = {
            "version": "1.0",
            "memories": [
                {
                    "name": "main_memory",
                    "display_name": "Main Memory",
                    "description": "Long-term memory for persistent information",
                    "enabled": True,
                    "type": "persistent",
                    "directory": "main_memory",
                    "created_date": "2025-01-01",
                    "last_modified": "2025-01-15",
                    "metadata": {
                        "storage_type": "json",
                        "max_entries": 10000
                    }
                }
            ]
        }
        registry_path = memory_dir / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        # Patch the registry path
        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = temp_dir
            info = gui.get_memory_info("Main Memory")

            assert "Main Memory" in info
            assert "🟢 Enabled" in info
            assert "Long-term memory" in info
            assert "persistent" in info
            assert "main_memory" in info
            assert "storage_type" in info
            assert "json" in info

    def test_get_memory_info_disabled(self, gui, temp_dir):
        """Test getting info for disabled memory."""
        # Create memory registry
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(exist_ok=True)
        registry = {
            "version": "1.0",
            "memories": [
                {
                    "name": "test_memory",
                    "display_name": "Test Memory",
                    "description": "Test memory instance",
                    "enabled": False,
                    "type": "temporary",
                    "directory": "test_memory"
                }
            ]
        }
        registry_path = memory_dir / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = temp_dir
            info = gui.get_memory_info("Test Memory")

            assert "Test Memory" in info
            assert "⭕ Disabled" in info

    def test_get_memory_info_not_found(self, gui, temp_dir):
        """Test getting info for non-existent memory."""
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(exist_ok=True)
        registry = {"version": "1.0", "memories": []}
        registry_path = memory_dir / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = temp_dir
            info = gui.get_memory_info("Nonexistent Memory")

            assert "not found" in info.lower()

    def test_get_memory_info_no_selection(self, gui):
        """Test getting info with no memory selected."""
        info = gui.get_memory_info("")
        assert info == "No memory selected"

    def test_enable_memory(self, gui, temp_dir):
        """Test enabling a memory instance."""
        # Create memory registry
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(exist_ok=True)
        registry = {
            "version": "1.0",
            "last_updated": "2025-12-27",
            "memories": [
                {
                    "name": "main_memory",
                    "display_name": "Main Memory",
                    "description": "Test memory",
                    "enabled": False,
                    "type": "persistent"
                }
            ]
        }
        registry_path = memory_dir / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = temp_dir
            status, info = gui.enable_memory("Main Memory")

            assert "enabled successfully" in status.lower()
            assert "✅" in status

            # Verify registry was updated
            with open(registry_path, 'r') as f:
                updated_registry = json.load(f)
            assert updated_registry['memories'][0]['enabled'] is True

    def test_enable_memory_already_enabled(self, gui, temp_dir):
        """Test enabling already enabled memory."""
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(exist_ok=True)
        registry = {
            "version": "1.0",
            "memories": [
                {"name": "main_memory", "display_name": "Main Memory", "enabled": True}
            ]
        }
        registry_path = memory_dir / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = temp_dir
            status, info = gui.enable_memory("Main Memory")

            assert "already enabled" in status.lower()
            assert "⚠️" in status

    def test_enable_memory_not_found(self, gui, temp_dir):
        """Test enabling non-existent memory."""
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(exist_ok=True)
        registry = {"version": "1.0", "memories": []}
        registry_path = memory_dir / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = temp_dir
            status, info = gui.enable_memory("Nonexistent Memory")

            assert "not found" in status.lower()
            assert "❌" in status

    def test_enable_memory_no_selection(self, gui):
        """Test enabling with no memory selected."""
        status, info = gui.enable_memory("")
        assert "no memory selected" in status.lower()
        assert "⚠️" in status

    def test_disable_memory(self, gui, temp_dir):
        """Test disabling a memory instance."""
        # Create memory registry
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(exist_ok=True)
        registry = {
            "version": "1.0",
            "last_updated": "2025-12-27",
            "memories": [
                {
                    "name": "main_memory",
                    "display_name": "Main Memory",
                    "description": "Test memory",
                    "enabled": True,
                    "type": "persistent"
                }
            ]
        }
        registry_path = memory_dir / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = temp_dir
            status, info = gui.disable_memory("Main Memory")

            assert "disabled successfully" in status.lower()
            assert "✅" in status

            # Verify registry was updated
            with open(registry_path, 'r') as f:
                updated_registry = json.load(f)
            assert updated_registry['memories'][0]['enabled'] is False

    def test_disable_memory_already_disabled(self, gui, temp_dir):
        """Test disabling already disabled memory."""
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(exist_ok=True)
        registry = {
            "version": "1.0",
            "memories": [
                {"name": "main_memory", "display_name": "Main Memory", "enabled": False}
            ]
        }
        registry_path = memory_dir / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = temp_dir
            status, info = gui.disable_memory("Main Memory")

            assert "already disabled" in status.lower()
            assert "⚠️" in status

    def test_disable_memory_not_found(self, gui, temp_dir):
        """Test disabling non-existent memory."""
        memory_dir = temp_dir / "memory"
        memory_dir.mkdir(exist_ok=True)
        registry = {"version": "1.0", "memories": []}
        registry_path = memory_dir / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = temp_dir
            status, info = gui.disable_memory("Nonexistent Memory")

            assert "not found" in status.lower()
            assert "❌" in status

    def test_disable_memory_no_selection(self, gui):
        """Test disabling with no memory selected."""
        status, info = gui.disable_memory("")
        assert "no memory selected" in status.lower()
        assert "⚠️" in status
