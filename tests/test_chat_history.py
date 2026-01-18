"""
Unit tests for chat_history module.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from llf.chat_history import ChatHistory


@pytest.fixture
def temp_history_dir(tmp_path):
    """Create temporary history directory for tests."""
    history_dir = tmp_path / "chat_history"
    history_dir.mkdir()
    return history_dir


@pytest.fixture
def chat_history(temp_history_dir):
    """Create ChatHistory instance."""
    return ChatHistory(temp_history_dir)


@pytest.fixture
def sample_messages():
    """Sample conversation messages."""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I'm doing well, thanks!"}
    ]


@pytest.fixture
def sample_metadata():
    """Sample session metadata."""
    return {
        "model": "test-model",
        "server_url": "http://localhost:8000/v1"
    }


class TestChatHistory:
    """Test ChatHistory class."""

    def test_initialization(self, chat_history, temp_history_dir):
        """Test ChatHistory initialization."""
        assert chat_history.history_dir == temp_history_dir
        assert temp_history_dir.exists()

    def test_save_session(self, chat_history, sample_messages, sample_metadata):
        """Test saving a chat session."""
        filepath = chat_history.save_session(sample_messages, sample_metadata)

        assert filepath.exists()
        assert filepath.name.startswith("chat_")
        assert filepath.name.endswith(".json")

        # Verify saved content
        with open(filepath, 'r') as f:
            data = json.load(f)

        assert data['messages'] == sample_messages
        assert data['metadata'] == sample_metadata
        # message_count is no longer stored in file (computed from messages array length)
        assert 'session_id' in data
        assert 'timestamp' in data

    def test_save_session_without_metadata(self, chat_history, sample_messages):
        """Test saving session without metadata."""
        filepath = chat_history.save_session(sample_messages)

        with open(filepath, 'r') as f:
            data = json.load(f)

        assert data['metadata'] == {}
        assert data['messages'] == sample_messages

    def test_load_session(self, chat_history, sample_messages, sample_metadata):
        """Test loading a saved session."""
        # Save a session first
        filepath = chat_history.save_session(sample_messages, sample_metadata)
        session_id = filepath.stem.replace("chat_", "")

        # Load it back
        loaded_data = chat_history.load_session(session_id)

        assert loaded_data is not None
        assert loaded_data['messages'] == sample_messages
        assert loaded_data['metadata'] == sample_metadata

    def test_load_session_with_filename(self, chat_history, sample_messages):
        """Test loading session using full filename."""
        filepath = chat_history.save_session(sample_messages)

        # Load using full filename
        loaded_data = chat_history.load_session(filepath.name)

        assert loaded_data is not None
        assert loaded_data['messages'] == sample_messages

    def test_load_nonexistent_session(self, chat_history):
        """Test loading a session that doesn't exist."""
        result = chat_history.load_session("nonexistent_session")
        assert result is None

    def test_list_sessions(self, chat_history, sample_messages):
        """Test listing saved sessions."""
        import time
        # Save multiple sessions
        for i in range(3):
            chat_history.save_session(sample_messages, {"index": i})
            time.sleep(0.01)  # Small delay to ensure different timestamps

        sessions = chat_history.list_sessions()

        assert len(sessions) == 3
        # Verify sessions are sorted by timestamp (most recent first)
        for session in sessions:
            assert 'session_id' in session
            assert 'timestamp' in session
            assert 'message_count' in session
            assert session['message_count'] == len(sample_messages)

    def test_list_sessions_with_limit(self, chat_history, sample_messages):
        """Test listing sessions with a limit."""
        import time
        # Save 5 sessions
        for i in range(5):
            chat_history.save_session(sample_messages)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        sessions = chat_history.list_sessions(limit=3)
        assert len(sessions) == 3

    def test_list_sessions_with_days_filter(self, chat_history, sample_messages, temp_history_dir):
        """Test listing sessions filtered by days."""
        # Create a session with old timestamp
        old_timestamp = datetime.now() - timedelta(days=10)
        session_data = {
            "session_id": old_timestamp.strftime("%Y%m%d_%H%M%S"),
            "timestamp": old_timestamp.isoformat(),
            "messages": sample_messages,
            "metadata": {},
            "message_count": len(sample_messages)
        }

        old_file = temp_history_dir / f"chat_{session_data['session_id']}.json"
        with open(old_file, 'w') as f:
            json.dump(session_data, f)

        # Create a recent session
        chat_history.save_session(sample_messages)

        # List sessions from last 7 days
        recent_sessions = chat_history.list_sessions(days=7)

        # Should only return the recent session
        assert len(recent_sessions) == 1

    def test_purge_old_sessions(self, chat_history, sample_messages, temp_history_dir):
        """Test purging old sessions."""
        # Create sessions with different ages
        old_timestamp = datetime.now() - timedelta(days=40)

        # Old session
        old_session_data = {
            "session_id": old_timestamp.strftime("%Y%m%d_%H%M%S"),
            "timestamp": old_timestamp.isoformat(),
            "messages": sample_messages,
            "metadata": {},
            "message_count": len(sample_messages)
        }
        old_file = temp_history_dir / f"chat_{old_session_data['session_id']}.json"
        with open(old_file, 'w') as f:
            json.dump(old_session_data, f)

        # Recent session
        chat_history.save_session(sample_messages)

        # Purge sessions older than 30 days
        deleted_count = chat_history.purge_old_sessions(days=30, dry_run=False)

        assert deleted_count == 1
        assert not old_file.exists()

        # Recent session should still exist
        sessions = chat_history.list_sessions()
        assert len(sessions) == 1

    def test_purge_old_sessions_dry_run(self, chat_history, sample_messages, temp_history_dir):
        """Test purging with dry run (no actual deletion)."""
        # Create old session
        old_timestamp = datetime.now() - timedelta(days=40)
        old_session_data = {
            "session_id": old_timestamp.strftime("%Y%m%d_%H%M%S"),
            "timestamp": old_timestamp.isoformat(),
            "messages": sample_messages,
            "metadata": {},
            "message_count": len(sample_messages)
        }
        old_file = temp_history_dir / f"chat_{old_session_data['session_id']}.json"
        with open(old_file, 'w') as f:
            json.dump(old_session_data, f)

        # Dry run
        deleted_count = chat_history.purge_old_sessions(days=30, dry_run=True)

        assert deleted_count == 1
        # File should still exist
        assert old_file.exists()

    def test_get_total_size(self, chat_history, sample_messages):
        """Test getting total size of history files."""
        # Save some sessions
        for i in range(3):
            chat_history.save_session(sample_messages)

        total_size = chat_history.get_total_size()
        assert total_size > 0

    def test_empty_history_dir(self, chat_history):
        """Test operations on empty history directory."""
        sessions = chat_history.list_sessions()
        assert len(sessions) == 0

        total_size = chat_history.get_total_size()
        assert total_size == 0

        deleted_count = chat_history.purge_old_sessions(days=30)
        assert deleted_count == 0

    def test_import_session(self, chat_history, sample_messages, sample_metadata, temp_history_dir):
        """Test importing a session from an external file."""
        # Create an external session file
        external_session = {
            "session_id": "external_20260109_120000_000000",
            "timestamp": datetime.now().isoformat(),
            "messages": sample_messages,
            "metadata": sample_metadata,
            "message_count": len(sample_messages)
        }

        external_file = temp_history_dir / "external_session.json"
        with open(external_file, 'w') as f:
            json.dump(external_session, f)

        # Import the session
        imported = chat_history.import_session(external_file)

        assert imported is not None
        assert imported['messages'] == sample_messages
        assert imported['metadata'] == sample_metadata

    def test_import_session_invalid_json(self, chat_history, temp_history_dir):
        """Test importing a session with invalid JSON."""
        invalid_file = temp_history_dir / "invalid.json"
        invalid_file.write_text("not valid json {{{")

        imported = chat_history.import_session(invalid_file)
        assert imported is None

    def test_import_session_missing_messages(self, chat_history, temp_history_dir):
        """Test importing a session without messages field."""
        invalid_session = {
            "session_id": "test",
            "timestamp": datetime.now().isoformat()
            # Missing 'messages' field
        }

        invalid_file = temp_history_dir / "no_messages.json"
        with open(invalid_file, 'w') as f:
            json.dump(invalid_session, f)

        imported = chat_history.import_session(invalid_file)
        assert imported is None

    def test_import_session_nonexistent_file(self, chat_history, temp_history_dir):
        """Test importing from a file that doesn't exist."""
        nonexistent = temp_history_dir / "does_not_exist.json"

        imported = chat_history.import_session(nonexistent)
        assert imported is None

    def test_import_session_markdown(self, chat_history, temp_history_dir):
        """Test importing a session from Markdown format."""
        # Create a markdown file in the format exported by MarkdownExporter
        markdown_content = """# Chat Conversation

## Session Information

**Model:** test-model
**Session ID:** test_session

## Conversation

### 👤 User

Hello, how are you?

### 🤖 Assistant

I'm doing well, thank you! How can I help you today?

### 👤 User

Can you explain Python?

### 🤖 Assistant

Python is a high-level programming language known for its readability and versatility.

---
*Exported on 2026-01-10 10:00:00*
"""

        md_file = temp_history_dir / "chat.md"
        md_file.write_text(markdown_content)

        # Import the session
        imported = chat_history.import_session(md_file)

        assert imported is not None
        assert 'messages' in imported
        assert len(imported['messages']) == 4

        # Check first message
        assert imported['messages'][0]['role'] == 'user'
        assert 'Hello, how are you?' in imported['messages'][0]['content']

        # Check second message
        assert imported['messages'][1]['role'] == 'assistant'
        assert "I'm doing well" in imported['messages'][1]['content']

    def test_import_session_txt(self, chat_history, temp_history_dir):
        """Test importing a session from plain text format."""
        # Create a text file in the format exported by TXTExporter
        txt_content = """================================================================================
CHAT CONVERSATION
================================================================================

Model: test-model
Session ID: test_session

--------------------------------------------------------------------------------
USER
--------------------------------------------------------------------------------
What is Python?

--------------------------------------------------------------------------------
ASSISTANT
--------------------------------------------------------------------------------
Python is a programming language.

--------------------------------------------------------------------------------
USER
--------------------------------------------------------------------------------
Thanks!

================================================================================
Exported on 2026-01-10 10:00:00
================================================================================
"""

        txt_file = temp_history_dir / "chat.txt"
        txt_file.write_text(txt_content)

        # Import the session
        imported = chat_history.import_session(txt_file)

        assert imported is not None
        assert 'messages' in imported
        assert len(imported['messages']) == 3

        # Check messages
        assert imported['messages'][0]['role'] == 'user'
        assert 'What is Python?' in imported['messages'][0]['content']

        assert imported['messages'][1]['role'] == 'assistant'
        assert 'Python is a programming language' in imported['messages'][1]['content']

        assert imported['messages'][2]['role'] == 'user'
        assert 'Thanks!' in imported['messages'][2]['content']

    def test_import_session_unsupported_format(self, chat_history, temp_history_dir):
        """Test importing from an unsupported file format."""
        pdf_file = temp_history_dir / "chat.pdf"
        pdf_file.write_text("fake pdf content")

        imported = chat_history.import_session(pdf_file)
        assert imported is None
