"""
Comprehensive edge case tests for ChatHistory to improve coverage.

Tests cover:
- load_session: Exception during load (lines 85-87)
- list_sessions: Exception during session parsing (lines 128-130)
- purge_old_sessions: Exception during purge (lines 163-165)
- import_session: Invalid JSON structure (lines 228-229)
- _import_markdown: Timestamp filtering, no messages found (lines 266, 280-281)
- _import_markdown: Exception during parsing (lines 292-294)
- _import_txt: Footer detection, no messages found (lines 334, 362-363)
- _import_txt: Exception during parsing (lines 374-376)
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

from llf.chat_history import ChatHistory


@pytest.fixture
def temp_history_dir(tmp_path):
    """Create temporary history directory."""
    history_dir = tmp_path / "chat_history"
    history_dir.mkdir()
    return history_dir


@pytest.fixture
def chat_history(temp_history_dir):
    """Create ChatHistory instance."""
    return ChatHistory(history_dir=temp_history_dir)


@pytest.fixture
def sample_session(temp_history_dir):
    """Create a sample session file."""
    session_id = "test_session_20260101_120000"
    session_file = temp_history_dir / f"chat_{session_id}.json"

    session_data = {
        "session_id": session_id,
        "timestamp": "2026-01-01T12:00:00",
        "message_count": 2,
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ],
        "metadata": {}
    }

    with open(session_file, 'w') as f:
        json.dump(session_data, f)

    return session_id


class TestLoadSessionEdgeCases:
    """Test load_session edge cases."""

    def test_load_session_exception(self, chat_history, temp_history_dir):
        """Test load_session when file is corrupted."""
        session_id = "corrupt_session"
        session_file = temp_history_dir / f"chat_{session_id}.json"

        # Create corrupted JSON file
        with open(session_file, 'w') as f:
            f.write("{invalid json{{")

        # Should return None and print error
        result = chat_history.load_session(session_id)
        assert result is None


class TestListSessionsEdgeCases:
    """Test list_sessions edge cases."""

    def test_list_sessions_with_corrupted_file(self, chat_history, temp_history_dir, sample_session):
        """Test listing sessions when one file is corrupted."""
        # Create a corrupted session file
        corrupt_file = temp_history_dir / "chat_corrupt_20260102_120000.json"
        with open(corrupt_file, 'w') as f:
            f.write("{invalid json{{")

        # Should skip corrupted file and return valid session
        sessions = chat_history.list_sessions()

        # Should have only the valid session
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == sample_session


class TestPurgeOldSessionsEdgeCases:
    """Test purge_old_sessions edge cases."""

    def test_purge_old_sessions_with_corrupted_file(self, chat_history, temp_history_dir):
        """Test purging when a session file is corrupted."""
        # Create an old valid session
        old_date = datetime.now() - timedelta(days=40)
        old_session_file = temp_history_dir / "chat_old_session.json"
        with open(old_session_file, 'w') as f:
            json.dump({
                "session_id": "old_session",
                "timestamp": old_date.isoformat(),
                "messages": []
            }, f)

        # Create a corrupted session file
        corrupt_file = temp_history_dir / "chat_corrupt_session.json"
        with open(corrupt_file, 'w') as f:
            f.write("{invalid json{{")

        # Should skip corrupted file and delete old valid session
        deleted_count = chat_history.purge_old_sessions(days=30, dry_run=False)

        # Should have deleted only the valid old session
        assert deleted_count == 1
        assert not old_session_file.exists()
        assert corrupt_file.exists()  # Corrupted file should remain


class TestImportSessionEdgeCases:
    """Test import_session edge cases."""

    def test_import_session_invalid_messages_structure(self, chat_history, temp_history_dir):
        """Test importing JSON with invalid messages structure."""
        import_file = temp_history_dir / "invalid_structure.json"

        # Create JSON with messages as string instead of list
        with open(import_file, 'w') as f:
            json.dump({
                "messages": "not a list",
                "metadata": {}
            }, f)

        # Should return None and print error
        result = chat_history.import_session(import_file)
        assert result is None


class TestImportMarkdownEdgeCases:
    """Test _import_markdown edge cases."""

    def test_import_markdown_with_timestamp_filtering(self, chat_history, temp_history_dir):
        """Test markdown import filters out timestamp lines."""
        import_file = temp_history_dir / "with_timestamps.md"

        markdown_content = """# Chat Session

### 👤 User
*2026-01-01 12:00:00*

Hello, how are you?

### 🤖 Assistant
*2026-01-01 12:00:05*

I'm doing well, thank you!

---
Exported on 2026-01-01
"""

        with open(import_file, 'w') as f:
            f.write(markdown_content)

        result = chat_history._import_markdown(import_file)

        assert result is not None
        assert len(result['messages']) == 2
        # Verify timestamps were filtered out
        assert '*2026-01-01' not in result['messages'][0]['content']
        assert '*2026-01-01' not in result['messages'][1]['content']

    def test_import_markdown_no_messages_found(self, chat_history, temp_history_dir):
        """Test markdown import with no valid messages."""
        import_file = temp_history_dir / "no_messages.md"

        # Create markdown with no message content
        markdown_content = """# Chat Session

Some header content but no actual messages in the right format.
"""

        with open(import_file, 'w') as f:
            f.write(markdown_content)

        # Should return None
        result = chat_history._import_markdown(import_file)
        assert result is None

    def test_import_markdown_exception(self, chat_history, temp_history_dir):
        """Test markdown import with exception during parsing."""
        import_file = temp_history_dir / "error.md"

        # Mock open to raise exception
        with patch('builtins.open', side_effect=IOError("Read error")):
            result = chat_history._import_markdown(import_file)
            assert result is None


class TestImportTextEdgeCases:
    """Test _import_txt edge cases."""

    def test_import_txt_with_footer_detection(self, chat_history, temp_history_dir):
        """Test text import stops at footer."""
        import_file = temp_history_dir / "with_footer.txt"

        text_content = """CHAT CONVERSATION
================================================================================

--------------------------------------------------------------------------------
USER
Hello, how are you?
--------------------------------------------------------------------------------
ASSISTANT
I'm doing well!

Exported on 2026-01-01 12:00:00
This should not be included
"""

        with open(import_file, 'w') as f:
            f.write(text_content)

        result = chat_history._import_txt(import_file)

        assert result is not None
        assert len(result['messages']) == 2
        # Verify footer content was not included
        for msg in result['messages']:
            assert 'should not be included' not in msg['content'].lower()

    def test_import_txt_with_timestamp_line(self, chat_history, temp_history_dir):
        """Test text import filters out timestamp lines."""
        import_file = temp_history_dir / "with_timestamp.txt"

        text_content = """CHAT CONVERSATION
================================================================================

--------------------------------------------------------------------------------
USER
Time: 2026-01-01 12:00:00
Hello, how are you?
--------------------------------------------------------------------------------
ASSISTANT
Time: 2026-01-01 12:00:05
I'm doing well!
"""

        with open(import_file, 'w') as f:
            f.write(text_content)

        result = chat_history._import_txt(import_file)

        assert result is not None
        assert len(result['messages']) == 2
        # Verify timestamp lines were filtered out
        assert 'Time:' not in result['messages'][0]['content']
        assert 'Time:' not in result['messages'][1]['content']

    def test_import_txt_no_messages_found(self, chat_history, temp_history_dir):
        """Test text import with no valid messages."""
        import_file = temp_history_dir / "no_messages.txt"

        # Create text file with no message markers
        text_content = """CHAT CONVERSATION
================================================================================

Just some header content with no messages.
"""

        with open(import_file, 'w') as f:
            f.write(text_content)

        # Should return None
        result = chat_history._import_txt(import_file)
        assert result is None

    def test_import_txt_exception(self, chat_history, temp_history_dir):
        """Test text import with exception during parsing."""
        import_file = temp_history_dir / "error.txt"

        # Mock open to raise exception
        with patch('builtins.open', side_effect=IOError("Read error")):
            result = chat_history._import_txt(import_file)
            assert result is None
