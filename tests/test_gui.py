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
             patch.object(gui.model_manager, 'is_model_downloaded', return_value=True):

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
             patch.object(gui.runtime, 'stop_server') as mock_stop:

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
             patch.object(gui, 'start_server', return_value="Server started") as mock_start:

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
        result = gui.download_model("", "", "")
        assert "provide" in result.lower() and ("model name" in result.lower() or "url" in result.lower())

    def test_download_model_success(self, gui):
        """Test successful model download."""
        with patch.object(gui.model_manager, 'download_model', return_value=None) as mock_download:
            result = gui.download_model("org/model", "", "")
            mock_download.assert_called_once()
            assert "success" in result.lower() or "downloaded" in result.lower()

    def test_download_model_error(self, gui):
        """Test model download error handling."""
        with patch.object(gui.model_manager, 'download_model', side_effect=Exception("Download failed")):
            result = gui.download_model("org/model", "", "")
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
        """Test launching GUI."""
        mock_interface = Mock()

        with patch.object(gui, 'create_interface', return_value=mock_interface):
            gui.launch(share=True, server_port=8080)

            mock_interface.launch.assert_called_once()
            call_kwargs = mock_interface.launch.call_args[1]
            assert call_kwargs['share'] == True
            assert call_kwargs['server_port'] == 8080


class TestStartGUI:
    """Test start_gui function."""

    def test_start_gui_default_params(self):
        """Test starting GUI with default parameters."""
        with patch('llf.gui.LLMFrameworkGUI') as mock_gui_class:
            mock_gui_instance = Mock()
            mock_gui_class.return_value = mock_gui_instance

            start_gui()

            mock_gui_class.assert_called_once_with(config=None, prompt_config=None)
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
                share=True,
                server_port=8080,
                inbrowser=False
            )

            mock_gui_class.assert_called_once_with(
                config=mock_config,
                prompt_config=mock_prompt_config
            )
            mock_gui_instance.launch.assert_called_once_with(
                share=True,
                server_port=8080,
                inbrowser=False
            )
