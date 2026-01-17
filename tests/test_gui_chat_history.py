"""
Unit tests for GUI chat history logging functionality.

Tests the new chat history features added to the GUI:
- ChatHistory manager initialization
- Conversation tracking
- Save/clear operations
- Toggle history saving
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

    def test_current_conversation_initialized(self, gui):
        """Test that current_conversation list is initialized."""
        assert hasattr(gui, 'current_conversation')
        assert isinstance(gui.current_conversation, list)
        assert len(gui.current_conversation) == 0

    def test_history_directory_created(self, gui, tmp_path):
        """Test that history directory is created."""
        history_dir = gui.chat_history_manager.history_dir
        assert history_dir.exists()
        assert history_dir.is_dir()

    def test_initialization_with_mock_config(self):
        """Test initialization handles mock config gracefully."""
        with patch('llf.gui.get_config') as mock_get_config, \
             patch('llf.gui.get_prompt_config') as mock_get_prompt_config:

            mock_config = Mock()
            mock_config.config_file = Mock()  # Mock object, not real path
            mock_get_config.return_value = mock_config
            mock_get_prompt_config.return_value = Mock()

            # Should not raise error
            with patch.object(LLMFrameworkGUI, '_load_modules'):
                gui = LLMFrameworkGUI()
                assert gui.chat_history_manager is not None


class TestSaveCurrentConversation:
    """Test save_current_conversation method."""

    def test_save_empty_conversation(self, gui):
        """Test saving empty conversation returns None."""
        result = gui.save_current_conversation()
        assert result is None

    def test_save_conversation_with_messages(self, gui, tmp_path):
        """Test saving conversation with messages."""
        # Add messages to current conversation
        gui.current_conversation = [
            {'role': 'user', 'content': 'Hello', 'timestamp': '2026-01-16T10:00:00'},
            {'role': 'assistant', 'content': 'Hi there!', 'timestamp': '2026-01-16T10:00:01'}
        ]

        result = gui.save_current_conversation()

        # Should return success message
        assert result is not None
        assert "💾" in result or "saved" in result.lower()

        # Check file was created
        history_files = list(gui.chat_history_manager.history_dir.glob('chat_*.json'))
        assert len(history_files) > 0

        # Verify file content
        with open(history_files[0], 'r') as f:
            data = json.load(f)

        assert data['message_count'] == 2
        assert len(data['messages']) == 2
        assert data['messages'][0]['role'] == 'user'
        assert data['messages'][1]['role'] == 'assistant'
        assert data['metadata']['source'] == 'gui'

    def test_save_with_metadata(self, gui):
        """Test that metadata is included in saved conversation."""
        gui.current_conversation = [
            {'role': 'user', 'content': 'Test', 'timestamp': '2026-01-16T10:00:00'}
        ]

        gui.save_current_conversation()

        history_files = list(gui.chat_history_manager.history_dir.glob('chat_*.json'))
        with open(history_files[0], 'r') as f:
            data = json.load(f)

        metadata = data['metadata']
        assert 'model' in metadata
        assert 'timestamp' in metadata
        assert 'server_url' in metadata
        assert metadata['source'] == 'gui'

    def test_save_when_disabled(self, gui):
        """Test saving does nothing when save_history is False."""
        gui.save_history = False
        gui.current_conversation = [
            {'role': 'user', 'content': 'Test', 'timestamp': '2026-01-16T10:00:00'}
        ]

        result = gui.save_current_conversation()

        assert result is None
        history_files = list(gui.chat_history_manager.history_dir.glob('chat_*.json'))
        assert len(history_files) == 0

    def test_save_handles_exceptions(self, gui):
        """Test save_current_conversation handles exceptions gracefully."""
        gui.current_conversation = [
            {'role': 'user', 'content': 'Test', 'timestamp': '2026-01-16T10:00:00'}
        ]

        # Mock save_session to raise exception
        with patch.object(gui.chat_history_manager, 'save_session', side_effect=Exception("Save failed")):
            result = gui.save_current_conversation()

            # Should return error message
            assert result is not None
            assert "⚠️" in result or "failed" in result.lower()


class TestToggleHistorySaving:
    """Test toggle_history_saving method."""

    def test_toggle_to_disabled(self, gui):
        """Test toggling history saving to disabled."""
        assert gui.save_history is True

        result = gui.toggle_history_saving(False)

        assert gui.save_history is False
        assert "disabled" in result.lower()

    def test_toggle_to_enabled(self, gui):
        """Test toggling history saving to enabled."""
        gui.save_history = False

        result = gui.toggle_history_saving(True)

        assert gui.save_history is True
        assert "enabled" in result.lower()

    def test_toggle_returns_status_message(self, gui):
        """Test that toggle returns status message."""
        result = gui.toggle_history_saving(False)

        assert isinstance(result, str)
        assert "💾" in result

    def test_toggle_logs_state_change(self, gui):
        """Test that toggle logs state change."""
        with patch('llf.gui.logger') as mock_logger:
            gui.toggle_history_saving(False)

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "disabled" in call_args.lower()


class TestClearChat:
    """Test clear_chat method with history saving."""

    def test_clear_returns_tuple(self, gui):
        """Test that clear_chat returns tuple."""
        result = gui.clear_chat()

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_clear_returns_empty_list(self, gui):
        """Test that clear_chat returns empty chat list."""
        chatbot, status = gui.clear_chat()

        assert chatbot == []
        assert isinstance(status, str)

    def test_clear_saves_conversation(self, gui):
        """Test that clear_chat saves conversation before clearing."""
        gui.current_conversation = [
            {'role': 'user', 'content': 'Hello', 'timestamp': '2026-01-16T10:00:00'},
            {'role': 'assistant', 'content': 'Hi!', 'timestamp': '2026-01-16T10:00:01'}
        ]

        chatbot, status = gui.clear_chat()

        # Should have saved conversation
        history_files = list(gui.chat_history_manager.history_dir.glob('chat_*.json'))
        assert len(history_files) > 0

        # Status should indicate save
        assert "💾" in status or "saved" in status.lower()

    def test_clear_empties_current_conversation(self, gui):
        """Test that clear_chat empties current_conversation."""
        gui.current_conversation = [
            {'role': 'user', 'content': 'Test', 'timestamp': '2026-01-16T10:00:00'}
        ]

        gui.clear_chat()

        assert len(gui.current_conversation) == 0

    def test_clear_without_messages(self, gui):
        """Test clearing when no messages exist."""
        chatbot, status = gui.clear_chat()

        assert chatbot == []
        assert status == ""  # No save message when nothing to save

    def test_clear_when_saving_disabled(self, gui):
        """Test clear_chat when history saving is disabled."""
        gui.save_history = False
        gui.current_conversation = [
            {'role': 'user', 'content': 'Test', 'timestamp': '2026-01-16T10:00:00'}
        ]

        chatbot, status = gui.clear_chat()

        # Should not save
        history_files = list(gui.chat_history_manager.history_dir.glob('chat_*.json'))
        assert len(history_files) == 0

        # Current conversation should still be cleared
        assert len(gui.current_conversation) == 0


class TestChatRespondHistoryTracking:
    """Test chat_respond method tracks messages for history."""

    def test_chat_respond_tracks_user_message(self, gui):
        """Test that user messages are tracked."""
        gui.current_conversation = []

        with patch.object(gui.runtime, 'chat', return_value=iter(["Response"])):
            # Process response generator
            for _ in gui.chat_respond("Hello", []):
                pass

        # Should have tracked user message
        assert len(gui.current_conversation) >= 1
        user_msg = gui.current_conversation[0]
        assert user_msg['role'] == 'user'
        assert user_msg['content'] == 'Hello'
        assert 'timestamp' in user_msg

    def test_chat_respond_tracks_assistant_message(self, gui):
        """Test that assistant messages are tracked."""
        gui.current_conversation = []

        with patch.object(gui.runtime, 'chat', return_value=iter(["Hello back!"])):
            # Process response generator
            for _ in gui.chat_respond("Hello", []):
                pass

        # Should have tracked both messages
        assert len(gui.current_conversation) == 2
        assistant_msg = gui.current_conversation[1]
        assert assistant_msg['role'] == 'assistant'
        assert assistant_msg['content'] == 'Hello back!'
        assert 'timestamp' in assistant_msg

    def test_chat_respond_tracks_error(self, gui):
        """Test that error messages are tracked."""
        gui.current_conversation = []

        with patch.object(gui.runtime, 'chat', side_effect=Exception("Test error")):
            # Process response generator
            for _ in gui.chat_respond("Hello", []):
                pass

        # Should have tracked user message and error
        assert len(gui.current_conversation) == 2
        error_msg = gui.current_conversation[1]
        assert error_msg['role'] == 'assistant'
        assert 'Error:' in error_msg['content']

    def test_chat_respond_no_tracking_when_disabled(self, gui):
        """Test that messages are not tracked when save_history is False."""
        gui.save_history = False
        gui.current_conversation = []

        with patch.object(gui.runtime, 'chat', return_value=iter(["Response"])):
            # Process response generator
            for _ in gui.chat_respond("Hello", []):
                pass

        # Should not have tracked anything
        assert len(gui.current_conversation) == 0


class TestShutdownGuiHistorySaving:
    """Test shutdown_gui saves conversation."""

    def test_shutdown_saves_conversation(self, gui):
        """Test that shutdown_gui saves current conversation."""
        gui.current_conversation = [
            {'role': 'user', 'content': 'Test', 'timestamp': '2026-01-16T10:00:00'}
        ]

        with patch.object(gui.runtime, 'is_server_running', return_value=False):
            with patch('llf.gui.threading.Thread'):  # Prevent actual shutdown
                gui.shutdown_gui()

        # Should have saved conversation
        history_files = list(gui.chat_history_manager.history_dir.glob('chat_*.json'))
        assert len(history_files) > 0

    def test_shutdown_logs_save_status(self, gui):
        """Test that shutdown logs save status."""
        gui.current_conversation = [
            {'role': 'user', 'content': 'Test', 'timestamp': '2026-01-16T10:00:00'}
        ]

        with patch.object(gui.runtime, 'is_server_running', return_value=False):
            with patch('llf.gui.threading.Thread'):
                with patch('llf.gui.logger') as mock_logger:
                    gui.shutdown_gui()

                    # Should have logged save status
                    info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                    assert any("saved" in call.lower() for call in info_calls)

    def test_shutdown_handles_no_conversation(self, gui):
        """Test shutdown with no conversation doesn't error."""
        gui.current_conversation = []

        with patch.object(gui.runtime, 'is_server_running', return_value=False):
            with patch('llf.gui.threading.Thread'):
                result = gui.shutdown_gui()

                # Should not raise error
                assert "Shutting down" in result


class TestChatHistoryIntegration:
    """Integration tests for chat history functionality."""

    def test_full_conversation_flow(self, gui):
        """Test complete conversation flow with history."""
        # Start with empty conversation
        assert len(gui.current_conversation) == 0

        # Have a conversation
        with patch.object(gui.runtime, 'chat', return_value=iter(["Response 1"])):
            for _ in gui.chat_respond("Message 1", []):
                pass

        assert len(gui.current_conversation) == 2

        with patch.object(gui.runtime, 'chat', return_value=iter(["Response 2"])):
            for _ in gui.chat_respond("Message 2", [{"role": "user", "content": "Message 1"}, {"role": "assistant", "content": "Response 1"}]):
                pass

        assert len(gui.current_conversation) == 4

        # Clear and save
        chatbot, status = gui.clear_chat()

        # Should have saved
        history_files = list(gui.chat_history_manager.history_dir.glob('chat_*.json'))
        assert len(history_files) > 0

        # Verify saved content
        with open(history_files[0], 'r') as f:
            data = json.load(f)

        assert data['message_count'] == 4
        assert len(data['messages']) == 4

    def test_multiple_conversations(self, gui):
        """Test multiple separate conversations."""
        # First conversation
        gui.current_conversation = [
            {'role': 'user', 'content': 'Test 1', 'timestamp': '2026-01-16T10:00:00'}
        ]
        gui.clear_chat()

        # Second conversation
        gui.current_conversation = [
            {'role': 'user', 'content': 'Test 2', 'timestamp': '2026-01-16T10:01:00'}
        ]
        gui.clear_chat()

        # Should have two saved files
        history_files = list(gui.chat_history_manager.history_dir.glob('chat_*.json'))
        assert len(history_files) == 2
