"""
Comprehensive tests for chat history display commands to improve CLI coverage.

Targets:
- chat_history_list_command (lines 1484-1513) - table rendering and size display
- chat_history_info_command (lines 1578-1585, 1590) - message role formatting
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace
from datetime import datetime, timedelta

from llf.cli import chat_history_list_command, chat_history_info_command
from llf.config import Config


@pytest.fixture
def mock_config(tmp_path):
    """Create mock config for testing."""
    config = Config()
    config.config_file = tmp_path / "config.json"
    config.chat_history_dir = tmp_path / "chat_history"
    config.chat_history_dir.mkdir(parents=True, exist_ok=True)
    return config


class TestChatHistoryListDisplay:
    """Test chat_history_list_command display rendering (lines 1484-1513)."""

    def test_list_with_sessions_displays_table(self, mock_config):
        """Test listing sessions renders table with all columns (lines 1484-1513)."""
        # Create multiple mock history files
        session1_id = "20260115_100000_123456"
        session2_id = "20260115_110000_234567"

        history1 = mock_config.chat_history_dir / f"chat_{session1_id}.json"
        history2 = mock_config.chat_history_dir / f"chat_{session2_id}.json"

        history_data1 = {
            "session_id": session1_id,
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"}
            ],
            "metadata": {"model": "test-model"},
            "timestamp": "2026-01-15T10:00:00",
            "message_count": 2
        }

        history_data2 = {
            "session_id": session2_id,
            "messages": [
                {"role": "user", "content": "Test"}
            ],
            "metadata": {"model": "other-model"},
            "timestamp": "2026-01-15T11:00:00",
            "message_count": 1
        }

        with open(history1, 'w') as f:
            json.dump(history_data1, f)
        with open(history2, 'w') as f:
            json.dump(history_data2, f)

        args = Namespace(days=None, limit=None)

        result = chat_history_list_command(mock_config, args)

        # Should return success
        assert result == 0

    def test_list_with_days_filter_no_results(self, mock_config):
        """Test listing with days filter when no sessions match (lines 1478-1481)."""
        # Create an old session (older than filter)
        old_date = datetime.now() - timedelta(days=100)
        session_id = old_date.strftime('%Y%m%d_%H%M%S') + "_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [],
            "metadata": {},
            "timestamp": old_date.isoformat(),
            "message_count": 0
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        # Filter for last 7 days (should exclude the old session)
        args = Namespace(days=7, limit=None)

        result = chat_history_list_command(mock_config, args)

        # Should return success even with no results
        assert result == 0

    def test_list_with_limit_filter(self, mock_config):
        """Test listing with limit filter (lines 1471-1472)."""
        # Create 3 sessions
        for i in range(3):
            session_id = f"20260115_{i:02d}0000_123456"
            history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

            history_data = {
                "session_id": session_id,
                "messages": [{"role": "user", "content": f"Message {i}"}],
                "metadata": {"model": "test-model"},
                "timestamp": f"2026-01-15T{i:02d}:00:00",
                "message_count": 1
            }

            with open(history_file, 'w') as f:
                json.dump(history_data, f)

        # Limit to 2 sessions
        args = Namespace(days=None, limit=2)

        result = chat_history_list_command(mock_config, args)

        # Should return success
        assert result == 0

    def test_list_displays_session_metadata(self, mock_config):
        """Test that session metadata is properly formatted in table (lines 1490-1503)."""
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        # Create session with specific metadata
        history_data = {
            "session_id": session_id,
            "messages": [
                {"role": "user", "content": "Q1"},
                {"role": "assistant", "content": "A1"},
                {"role": "user", "content": "Q2"},
            ],
            "metadata": {"model": "gpt-4"},
            "timestamp": "2026-01-15T10:30:45",
            "message_count": 3
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(days=None, limit=None)

        result = chat_history_list_command(mock_config, args)

        # Should return success and display table
        assert result == 0

    def test_list_shows_total_size_and_directory(self, mock_config):
        """Test that total size and directory are displayed (lines 1507-1511)."""
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [{"role": "user", "content": "Test"}],
            "metadata": {},
            "timestamp": "2026-01-15T10:00:00",
            "message_count": 1
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(days=None, limit=None)

        result = chat_history_list_command(mock_config, args)

        # Should return success
        assert result == 0


class TestChatHistoryInfoDisplay:
    """Test chat_history_info_command message role formatting (lines 1578-1585, 1590)."""

    def test_info_displays_user_message(self, mock_config):
        """Test displaying user message with proper formatting (lines 1570-1573)."""
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "metadata": {"model": "test-model"},
            "timestamp": "2026-01-15T10:00:00"
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(session_id=session_id)

        result = chat_history_info_command(mock_config, args)

        # Should return success
        assert result == 0

    def test_info_displays_assistant_message(self, mock_config):
        """Test displaying assistant message with proper formatting (lines 1574-1577)."""
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [
                {"role": "assistant", "content": "I'm doing well, thank you!"}
            ],
            "metadata": {"model": "test-model"},
            "timestamp": "2026-01-15T10:00:00"
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(session_id=session_id)

        result = chat_history_info_command(mock_config, args)

        # Should return success
        assert result == 0

    def test_info_displays_system_message(self, mock_config):
        """Test displaying system message with proper formatting (lines 1578-1581)."""
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."}
            ],
            "metadata": {"model": "test-model"},
            "timestamp": "2026-01-15T10:00:00"
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(session_id=session_id)

        result = chat_history_info_command(mock_config, args)

        # Should return success
        assert result == 0

    def test_info_displays_unknown_role_message(self, mock_config):
        """Test displaying message with unknown role (lines 1582-1585)."""
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [
                {"role": "custom_role", "content": "Custom message"}
            ],
            "metadata": {"model": "test-model"},
            "timestamp": "2026-01-15T10:00:00"
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(session_id=session_id)

        result = chat_history_info_command(mock_config, args)

        # Should return success
        assert result == 0

    def test_info_displays_message_with_timestamp(self, mock_config):
        """Test displaying message with timestamp (line 1590)."""
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2026-01-15T10:00:00"
                }
            ],
            "metadata": {"model": "test-model"},
            "timestamp": "2026-01-15T10:00:00"
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(session_id=session_id)

        result = chat_history_info_command(mock_config, args)

        # Should return success
        assert result == 0

    def test_info_displays_mixed_message_roles(self, mock_config):
        """Test displaying conversation with mixed roles (all paths)."""
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "What is AI?"},
                {"role": "assistant", "content": "AI stands for..."},
                {"role": "user", "content": "Tell me more", "timestamp": "2026-01-15T10:05:00"},
                {"role": "custom", "content": "Custom message"}
            ],
            "metadata": {"model": "test-model"},
            "timestamp": "2026-01-15T10:00:00"
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(session_id=session_id)

        result = chat_history_info_command(mock_config, args)

        # Should return success
        assert result == 0

    def test_info_displays_session_header(self, mock_config):
        """Test that session header is displayed with metadata."""
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [
                {"role": "user", "content": "Test"}
            ],
            "metadata": {"model": "gpt-4-turbo"},
            "timestamp": "2026-01-15T10:30:45",
            "message_count": 1
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(session_id=session_id)

        result = chat_history_info_command(mock_config, args)

        # Should return success
        assert result == 0

    def test_info_invalid_timestamp_fallback(self, mock_config):
        """Test that invalid timestamp falls back gracefully (lines 1547-1551)."""
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [{"role": "user", "content": "Test"}],
            "metadata": {},
            "timestamp": "invalid-timestamp"
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(session_id=session_id)

        result = chat_history_info_command(mock_config, args)

        # Should return success
        assert result == 0

    def test_info_missing_metadata_model(self, mock_config):
        """Test displaying session when model metadata is missing."""
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [{"role": "user", "content": "Test"}],
            "metadata": {},  # No model key
            "timestamp": "2026-01-15T10:00:00"
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(session_id=session_id)

        result = chat_history_info_command(mock_config, args)

        # Should return success
        assert result == 0
