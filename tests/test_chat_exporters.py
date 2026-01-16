"""
Unit tests for chat_exporters module.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from llf.chat_exporters import (
    ChatExporter,
    MarkdownExporter,
    JSONExporter,
    TXTExporter,
    PDFExporter,
    get_exporter
)


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory for tests."""
    output_dir = tmp_path / "exports"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_session_data():
    """Sample session data for export tests."""
    return {
        "session_id": "20260109_120000",
        "timestamp": "2026-01-09T12:00:00",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant.", "timestamp": "2026-01-09T12:00:00"},
            {"role": "user", "content": "Hello", "timestamp": "2026-01-09T12:00:01"},
            {"role": "assistant", "content": "Hi there! How can I help you?", "timestamp": "2026-01-09T12:00:02"},
            {"role": "user", "content": "What is Python?", "timestamp": "2026-01-09T12:00:03"},
            {"role": "assistant", "content": "Python is a high-level programming language.", "timestamp": "2026-01-09T12:00:04"}
        ],
        "metadata": {
            "model": "test-model",
            "server_url": "http://localhost:8000/v1"
        },
        "message_count": 5
    }


class TestMarkdownExporter:
    """Test MarkdownExporter class."""

    def test_export_with_timestamps(self, temp_output_dir, sample_session_data):
        """Test Markdown export with timestamps."""
        exporter = MarkdownExporter(include_timestamps=True, include_system=False)
        output_path = temp_output_dir / "chat.md"

        exporter.export(sample_session_data, output_path)

        assert output_path.exists()

        # Verify content
        content = output_path.read_text()
        assert "# Chat Conversation" in content
        assert "Session ID:" in content
        assert "20260109_120000" in content
        assert "### 👤 User" in content
        assert "### 🤖 Assistant" in content
        assert "Hello" in content
        assert "Python is a high-level programming language" in content
        # System message should not be included
        assert "helpful assistant" not in content

    def test_export_without_timestamps(self, temp_output_dir, sample_session_data):
        """Test Markdown export without timestamps."""
        exporter = MarkdownExporter(include_timestamps=False, include_system=False)
        output_path = temp_output_dir / "chat_no_ts.md"

        exporter.export(sample_session_data, output_path)

        content = output_path.read_text()
        # Should not have timestamp section
        assert "_Timestamp:_" not in content

    def test_export_with_system_messages(self, temp_output_dir, sample_session_data):
        """Test Markdown export including system messages."""
        exporter = MarkdownExporter(include_timestamps=True, include_system=True)
        output_path = temp_output_dir / "chat_with_system.md"

        exporter.export(sample_session_data, output_path)

        content = output_path.read_text()
        assert "### ⚙️ System" in content
        assert "helpful assistant" in content


class TestJSONExporter:
    """Test JSONExporter class."""

    def test_export_json(self, temp_output_dir, sample_session_data):
        """Test JSON export."""
        exporter = JSONExporter(include_timestamps=True, include_system=False)
        output_path = temp_output_dir / "chat.json"

        exporter.export(sample_session_data, output_path)

        assert output_path.exists()

        # Verify content
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'exported_at' in data
        assert 'export_settings' in data
        assert data['session_id'] == "20260109_120000"

        # Should filter out system messages
        messages = data['messages']
        roles = [msg['role'] for msg in messages]
        assert 'system' not in roles

    def test_export_json_with_system(self, temp_output_dir, sample_session_data):
        """Test JSON export with system messages."""
        exporter = JSONExporter(include_timestamps=True, include_system=True)
        output_path = temp_output_dir / "chat_with_system.json"

        exporter.export(sample_session_data, output_path)

        with open(output_path, 'r') as f:
            data = json.load(f)

        messages = data['messages']
        roles = [msg['role'] for msg in messages]
        assert 'system' in roles

    def test_export_json_without_timestamps(self, temp_output_dir, sample_session_data):
        """Test JSON export without timestamps."""
        exporter = JSONExporter(include_timestamps=False, include_system=False)
        output_path = temp_output_dir / "chat_no_ts.json"

        exporter.export(sample_session_data, output_path)

        with open(output_path, 'r') as f:
            data = json.load(f)

        # Messages should not have timestamp field
        for msg in data['messages']:
            assert 'timestamp' not in msg


class TestTXTExporter:
    """Test TXTExporter class."""

    def test_export_txt(self, temp_output_dir, sample_session_data):
        """Test TXT export."""
        exporter = TXTExporter(include_timestamps=True, include_system=False)
        output_path = temp_output_dir / "chat.txt"

        exporter.export(sample_session_data, output_path)

        assert output_path.exists()

        content = output_path.read_text()
        assert "CHAT CONVERSATION" in content
        assert "Session ID: 20260109_120000" in content
        assert "USER" in content
        assert "ASSISTANT" in content
        assert "Hello" in content
        # System message should not be included
        assert "SYSTEM" not in content

    def test_export_txt_without_timestamps(self, temp_output_dir, sample_session_data):
        """Test TXT export without timestamps."""
        exporter = TXTExporter(include_timestamps=False, include_system=False)
        output_path = temp_output_dir / "chat_no_ts.txt"

        exporter.export(sample_session_data, output_path)

        content = output_path.read_text()
        # Should not have timestamp info
        assert "[" not in content  # Timestamps are shown in brackets

    def test_export_txt_with_system(self, temp_output_dir, sample_session_data):
        """Test TXT export with system messages."""
        exporter = TXTExporter(include_timestamps=True, include_system=True)
        output_path = temp_output_dir / "chat_with_system.txt"

        exporter.export(sample_session_data, output_path)

        content = output_path.read_text()
        assert "SYSTEM" in content


class TestPDFExporter:
    """Test PDFExporter class."""

    def test_export_pdf(self, temp_output_dir, sample_session_data):
        """Test PDF export."""
        pytest.importorskip("reportlab")  # Skip if reportlab not installed

        exporter = PDFExporter(include_timestamps=True, include_system=False)
        output_path = temp_output_dir / "chat.pdf"

        exporter.export(sample_session_data, output_path)

        assert output_path.exists()
        # Verify it's a PDF file
        with open(output_path, 'rb') as f:
            header = f.read(4)
            assert header == b'%PDF'

    def test_export_pdf_without_reportlab(self, temp_output_dir, sample_session_data, monkeypatch):
        """Test PDF export fails gracefully without reportlab."""
        # Mock import error
        import sys
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if 'reportlab' in name:
                raise ImportError("No module named 'reportlab'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, '__import__', mock_import)

        with pytest.raises(ImportError, match="reportlab"):
            exporter = PDFExporter(include_timestamps=True, include_system=False)
            output_path = temp_output_dir / "chat.pdf"
            exporter.export(sample_session_data, output_path)


class TestGetExporter:
    """Test get_exporter factory function."""

    def test_get_markdown_exporter(self):
        """Test getting Markdown exporter."""
        exporter = get_exporter('markdown')
        assert isinstance(exporter, MarkdownExporter)

        exporter = get_exporter('md')
        assert isinstance(exporter, MarkdownExporter)

    def test_get_json_exporter(self):
        """Test getting JSON exporter."""
        exporter = get_exporter('json')
        assert isinstance(exporter, JSONExporter)

    def test_get_txt_exporter(self):
        """Test getting TXT exporter."""
        exporter = get_exporter('txt')
        assert isinstance(exporter, TXTExporter)

        exporter = get_exporter('text')
        assert isinstance(exporter, TXTExporter)

    def test_get_pdf_exporter(self):
        """Test getting PDF exporter."""
        pytest.importorskip("reportlab")  # Skip if reportlab not installed
        exporter = get_exporter('pdf')
        assert isinstance(exporter, PDFExporter)

    def test_get_invalid_format(self):
        """Test getting exporter with invalid format."""
        with pytest.raises(ValueError, match="Unsupported format"):
            get_exporter('invalid_format')

    def test_get_exporter_with_options(self):
        """Test getting exporter with custom options."""
        exporter = get_exporter('markdown', include_timestamps=False, include_system=True)
        assert isinstance(exporter, MarkdownExporter)
        assert exporter.include_timestamps is False
        assert exporter.include_system is True


class TestExporterEdgeCases:
    """Test edge cases for exporters."""

    def test_empty_messages(self, temp_output_dir):
        """Test exporting session with no messages."""
        session_data = {
            "session_id": "20260109_120000",
            "timestamp": "2026-01-09T12:00:00",
            "messages": [],
            "metadata": {},
            "message_count": 0
        }

        exporter = MarkdownExporter()
        output_path = temp_output_dir / "empty.md"
        exporter.export(session_data, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Chat Conversation" in content

    def test_messages_without_timestamps(self, temp_output_dir):
        """Test exporting messages that don't have timestamp fields."""
        session_data = {
            "session_id": "20260109_120000",
            "timestamp": "2026-01-09T12:00:00",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"}
            ],
            "metadata": {},
            "message_count": 2
        }

        exporter = MarkdownExporter(include_timestamps=True)
        output_path = temp_output_dir / "no_ts_messages.md"
        exporter.export(session_data, output_path)

        assert output_path.exists()
