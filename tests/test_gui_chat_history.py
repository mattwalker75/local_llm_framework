"""
Unit tests for GUI chat history logging functionality.

Tests the incremental chat history features:
- ChatHistory manager initialization
- Session file management
- Incremental message appending
- Clear chat starting new sessions
- Shutdown behavior
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from llf.gui import LLMFrameworkGUI
from llf.config import Config
from llf.prompt_config import PromptConfig


@pytest.fixture
def mock_config(tmp_path):
    """Create mock config for testing."""
    config_file = tmp_path / "config.json"
    config_data = {
        "models_dir": str(tmp_path / "models"),
        "model_name": "test-model",
        "api_base_url": "http://localhost:8000/v1",
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
def mock_prompt_config(tmp_path):
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
def gui(mock_config, mock_prompt_config):
    """Create GUI instance for testing."""
    with patch.object(LLMFrameworkGUI, '_load_modules'):
        gui_instance = LLMFrameworkGUI(config=mock_config, prompt_config=mock_prompt_config)
        gui_instance.tts = None
        gui_instance.stt = None
        return gui_instance


class TestChatHistoryInitialization:
    """Test chat history manager initialization."""

    def test_chat_history_manager_initialized(self, gui):
        """Test that ChatHistory manager is initialized."""
        assert hasattr(gui, 'chat_history_manager')
        assert gui.chat_history_manager is not None

    def test_save_history_enabled_by_default(self, gui):
        """Test that save_history is enabled by default."""
        assert hasattr(gui, 'save_history')
        assert gui.save_history is True

    def test_current_session_file_initialized(self, gui):
        """Test that current_session_file is initialized to None."""
        assert hasattr(gui, 'current_session_file')
        assert gui.current_session_file is None

    def test_history_directory_created(self, gui, tmp_path):
        """Test that history directory is created."""
        history_dir = gui.chat_history_manager.history_dir
        assert history_dir.exists()
        assert history_dir.is_dir()

    def test_initialization_with_mock_config(self, tmp_path):
        """Test initialization handles mock config gracefully."""
        with patch('llf.gui.get_config') as mock_get_config, \
             patch('llf.gui.get_prompt_config') as mock_get_prompt_config:

            mock_config = Mock()
            mock_config.config_file = tmp_path / "config.json"  # Use real path
            mock_get_config.return_value = mock_config
            mock_get_prompt_config.return_value = Mock()

            # Should not raise error
            with patch.object(LLMFrameworkGUI, '_load_modules'):
                gui = LLMFrameworkGUI()
                assert gui.chat_history_manager is not None


class TestIncrementalLogging:
    """Test incremental logging methods."""

    def test_ensure_session_started_creates_file(self, gui):
        """Test _ensure_session_started creates a session file."""
        assert gui.current_session_file is None

        result = gui._ensure_session_started()

        assert result is not None
        assert result.exists()
        assert gui.current_session_file == result

    def test_ensure_session_started_reuses_existing(self, gui):
        """Test _ensure_session_started reuses existing session."""
        first_session = gui._ensure_session_started()
        second_session = gui._ensure_session_started()

        assert first_session == second_session

    def test_ensure_session_started_returns_none_when_disabled(self, gui):
        """Test _ensure_session_started returns None when save_history is False."""
        gui.save_history = False

        result = gui._ensure_session_started()

        assert result is None
        assert gui.current_session_file is None

    def test_append_to_chat_history(self, gui):
        """Test _append_to_chat_history adds messages to session file."""
        gui._append_to_chat_history("Hello", "Hi there!")

        # Load the session file and check messages
        with open(gui.current_session_file, 'r') as f:
            data = json.load(f)

        assert len(data['messages']) == 2
        assert data['messages'][0]['role'] == 'user'
        assert data['messages'][0]['content'] == 'Hello'
        assert data['messages'][1]['role'] == 'assistant'
        assert data['messages'][1]['content'] == 'Hi there!'

    def test_append_to_chat_history_multiple_exchanges(self, gui):
        """Test multiple exchanges are appended correctly."""
        gui._append_to_chat_history("Hello", "Hi!")
        gui._append_to_chat_history("How are you?", "I'm fine, thanks!")

        with open(gui.current_session_file, 'r') as f:
            data = json.load(f)

        assert len(data['messages']) == 4
        assert data['messages'][2]['content'] == 'How are you?'
        assert data['messages'][3]['content'] == "I'm fine, thanks!"

    def test_append_to_chat_history_returns_false_when_disabled(self, gui):
        """Test _append_to_chat_history returns False when save_history is False."""
        gui.save_history = False

        result = gui._append_to_chat_history("Hello", "Hi!")

        assert result is False
        assert gui.current_session_file is None

    def test_start_new_session_creates_new_file(self, gui):
        """Test _start_new_session creates a new session file."""
        first_session = gui._ensure_session_started()
        second_session = gui._start_new_session()

        assert second_session != first_session
        assert second_session.exists()


class TestClearChat:
    """Test clear_chat method with incremental logging."""

    def test_clear_returns_empty_list(self, gui):
        """Test that clear_chat returns empty list."""
        result = gui.clear_chat()

        assert result == []

    def test_clear_starts_new_session(self, gui):
        """Test that clear_chat starts a new session."""
        # Start a session and add some messages
        gui._append_to_chat_history("Hello", "Hi!")
        first_session = gui.current_session_file

        # Clear chat
        gui.clear_chat()

        # Should have a new session file
        assert gui.current_session_file != first_session
        assert gui.current_session_file.exists()

    def test_clear_when_saving_disabled(self, gui):
        """Test clear_chat when history saving is disabled."""
        gui.save_history = False

        result = gui.clear_chat()

        assert result == []
        assert gui.current_session_file is None


class TestChatRespondHistoryTracking:
    """Test chat_respond method saves messages incrementally."""

    def test_chat_respond_saves_incrementally(self, gui):
        """Test that chat_respond saves messages after each exchange."""
        with patch.object(gui.runtime, 'chat', return_value=iter(["Response"])):
            with patch.object(gui.prompt_config, 'get_all_tools', return_value=None):
                # Process response generator
                for _ in gui.chat_respond("Hello", [], save_enabled=True):
                    pass

        # Should have created a session and saved messages
        assert gui.current_session_file is not None

        with open(gui.current_session_file, 'r') as f:
            data = json.load(f)

        assert len(data['messages']) == 2
        assert data['messages'][0]['role'] == 'user'
        assert data['messages'][0]['content'] == 'Hello'
        assert data['messages'][1]['role'] == 'assistant'
        assert data['messages'][1]['content'] == 'Response'

    def test_chat_respond_no_save_when_disabled(self, gui):
        """Test that messages are not saved when save_enabled is False."""
        with patch.object(gui.runtime, 'chat', return_value=iter(["Response"])):
            with patch.object(gui.prompt_config, 'get_all_tools', return_value=None):
                for _ in gui.chat_respond("Hello", [], save_enabled=False):
                    pass

        # Should not have created a session
        assert gui.current_session_file is None

    def test_chat_respond_no_save_when_global_disabled(self, gui):
        """Test that messages are not saved when save_history is False."""
        gui.save_history = False

        with patch.object(gui.runtime, 'chat', return_value=iter(["Response"])):
            with patch.object(gui.prompt_config, 'get_all_tools', return_value=None):
                for _ in gui.chat_respond("Hello", [], save_enabled=True):
                    pass

        # Should not have created a session
        assert gui.current_session_file is None

    def test_chat_respond_saves_multiple_exchanges(self, gui):
        """Test that multiple exchanges are saved to the same session."""
        with patch.object(gui.runtime, 'chat', return_value=iter(["Response 1"])):
            with patch.object(gui.prompt_config, 'get_all_tools', return_value=None):
                for _ in gui.chat_respond("Message 1", [], save_enabled=True):
                    pass

        first_session = gui.current_session_file

        with patch.object(gui.runtime, 'chat', return_value=iter(["Response 2"])):
            with patch.object(gui.prompt_config, 'get_all_tools', return_value=None):
                for _ in gui.chat_respond("Message 2", [{"role": "user", "content": "Message 1"}, {"role": "assistant", "content": "Response 1"}], save_enabled=True):
                    pass

        # Should use the same session
        assert gui.current_session_file == first_session

        with open(gui.current_session_file, 'r') as f:
            data = json.load(f)

        assert len(data['messages']) == 4


class TestShutdownGUI:
    """Test shutdown_gui behavior with incremental logging."""

    def test_shutdown_does_not_save(self, gui):
        """Test that shutdown_gui does not save (incremental logging saves after each exchange)."""
        # Add some messages
        gui._append_to_chat_history("Hello", "Hi!")
        initial_files = list(gui.chat_history_manager.history_dir.glob('chat_*.json'))

        with patch.object(gui.runtime, 'is_server_running', return_value=False):
            with patch('llf.gui.threading.Thread'):  # Prevent actual shutdown
                gui.shutdown_gui()

        # Should have the same number of files (no additional save)
        final_files = list(gui.chat_history_manager.history_dir.glob('chat_*.json'))
        assert len(final_files) == len(initial_files)

    def test_shutdown_handles_no_session(self, gui):
        """Test shutdown with no session doesn't error."""
        assert gui.current_session_file is None

        with patch.object(gui.runtime, 'is_server_running', return_value=False):
            with patch('llf.gui.threading.Thread'):
                result = gui.shutdown_gui()

                # Should not raise error
                assert "Shutting down" in result


class TestChatHistoryIntegration:
    """Integration tests for chat history functionality."""

    def test_full_conversation_flow(self, gui):
        """Test complete conversation flow with incremental history."""
        # Start with no session
        assert gui.current_session_file is None

        # Have a conversation
        with patch.object(gui.runtime, 'chat', return_value=iter(["Response 1"])):
            with patch.object(gui.prompt_config, 'get_all_tools', return_value=None):
                for _ in gui.chat_respond("Message 1", [], save_enabled=True):
                    pass

        # Should have created a session
        assert gui.current_session_file is not None
        first_session = gui.current_session_file

        with patch.object(gui.runtime, 'chat', return_value=iter(["Response 2"])):
            with patch.object(gui.prompt_config, 'get_all_tools', return_value=None):
                for _ in gui.chat_respond("Message 2", [{"role": "user", "content": "Message 1"}, {"role": "assistant", "content": "Response 1"}], save_enabled=True):
                    pass

        # Should still use same session
        assert gui.current_session_file == first_session

        # Verify saved content
        with open(gui.current_session_file, 'r') as f:
            data = json.load(f)

        assert len(data['messages']) == 4
        assert data['metadata']['interface'] == 'gui'

    def test_multiple_sessions(self, gui):
        """Test multiple separate sessions after clearing."""
        # First session
        gui._append_to_chat_history("Test 1", "Response 1")
        first_session = gui.current_session_file

        # Clear to start new session
        gui.clear_chat()
        second_session = gui.current_session_file

        # Add to second session
        gui._append_to_chat_history("Test 2", "Response 2")

        # Should have two different sessions
        assert first_session != second_session
        history_files = list(gui.chat_history_manager.history_dir.glob('chat_*.json'))
        assert len(history_files) == 2

    def test_toggle_save_during_conversation(self, gui):
        """Test toggling save_enabled during conversation."""
        # First exchange - save enabled
        with patch.object(gui.runtime, 'chat', return_value=iter(["Response 1"])):
            with patch.object(gui.prompt_config, 'get_all_tools', return_value=None):
                for _ in gui.chat_respond("Message 1", [], save_enabled=True):
                    pass

        # Second exchange - save disabled
        with patch.object(gui.runtime, 'chat', return_value=iter(["Response 2"])):
            with patch.object(gui.prompt_config, 'get_all_tools', return_value=None):
                for _ in gui.chat_respond("Message 2", [{"role": "user", "content": "Message 1"}, {"role": "assistant", "content": "Response 1"}], save_enabled=False):
                    pass

        # Third exchange - save enabled again
        with patch.object(gui.runtime, 'chat', return_value=iter(["Response 3"])):
            with patch.object(gui.prompt_config, 'get_all_tools', return_value=None):
                for _ in gui.chat_respond("Message 3", [{"role": "user", "content": "Message 1"}, {"role": "assistant", "content": "Response 1"}, {"role": "user", "content": "Message 2"}, {"role": "assistant", "content": "Response 2"}], save_enabled=True):
                    pass

        # Should only have messages 1, 3 saved (2 was skipped)
        with open(gui.current_session_file, 'r') as f:
            data = json.load(f)

        assert len(data['messages']) == 4  # 2 from first + 2 from third
        assert data['messages'][0]['content'] == 'Message 1'
        assert data['messages'][2]['content'] == 'Message 3'
