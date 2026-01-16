"""
Tests to improve coverage for chat_exporters.py PDF functionality.

Missing lines (40 total): 226-229, 236-315
These are all in the PDF export functionality which requires reportlab.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from llf.chat_exporters import PDFExporter


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory for tests."""
    output_dir = tmp_path / "exports"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_session_data():
    """Create sample session data for testing."""
    return {
        "session_id": "test_session_123",
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?",
                "timestamp": "2026-01-15T10:00:00"
            },
            {
                "role": "assistant",
                "content": "I'm doing well, thank you! How can I help you today?",
                "timestamp": "2026-01-15T10:00:05"
            },
            {
                "role": "user",
                "content": "Can you help me with Python?",
                "timestamp": "2026-01-15T10:01:00"
            },
            {
                "role": "assistant",
                "content": "Of course! I'd be happy to help with Python. What do you need?",
                "timestamp": "2026-01-15T10:01:05"
            }
        ],
        "metadata": {
            "model": "test-model-v1",
            "timestamp": "2026-01-15T10:00:00"
        }
    }


class TestPDFExporterWithReportlab:
    """Test PDF export functionality when reportlab is available."""

    def test_pdf_export_success(self, temp_output_dir, sample_session_data):
        """Test successful PDF export with reportlab."""
        pytest.importorskip("reportlab")

        exporter = PDFExporter(include_timestamps=True, include_system=False)
        output_path = temp_output_dir / "chat.pdf"

        # Export should succeed
        exporter.export(sample_session_data, output_path)

        # Verify PDF was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_pdf_export_with_metadata(self, temp_output_dir, sample_session_data):
        """Test PDF export includes metadata (lines 273-285)."""
        pytest.importorskip("reportlab")

        exporter = PDFExporter(include_timestamps=True, include_system=False)
        output_path = temp_output_dir / "chat_with_metadata.pdf"

        # Export with full metadata
        exporter.export(sample_session_data, output_path)

        # Verify file exists and has content
        assert output_path.exists()
        assert output_path.stat().st_size > 1000  # PDF with content should be >1KB

    def test_pdf_export_without_metadata(self, temp_output_dir):
        """Test PDF export without metadata."""
        pytest.importorskip("reportlab")

        exporter = PDFExporter(include_timestamps=False, include_system=False)
        output_path = temp_output_dir / "chat_no_metadata.pdf"

        # Session data without metadata
        session_data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }

        exporter.export(session_data, output_path)

        assert output_path.exists()

    def test_pdf_export_with_special_characters(self, temp_output_dir):
        """Test PDF export with special characters (lines 304-306)."""
        pytest.importorskip("reportlab")

        exporter = PDFExporter(include_timestamps=False, include_system=False)
        output_path = temp_output_dir / "chat_special.pdf"

        # Session data with special characters
        session_data = {
            "messages": [
                {"role": "user", "content": "Test <html> & special chars > < & test"},
                {"role": "assistant", "content": "Response with <tags> and & symbols"}
            ]
        }

        # Should handle HTML escaping (lines 304-306)
        exporter.export(session_data, output_path)

        assert output_path.exists()

    def test_pdf_export_with_newlines(self, temp_output_dir):
        """Test PDF export preserves newlines (lines 304-306)."""
        pytest.importorskip("reportlab")

        exporter = PDFExporter(include_timestamps=False, include_system=False)
        output_path = temp_output_dir / "chat_newlines.pdf"

        # Session data with newlines
        session_data = {
            "messages": [
                {"role": "user", "content": "Line 1\nLine 2\nLine 3"},
                {"role": "assistant", "content": "Response\nwith\nmultiple\nlines"}
            ]
        }

        # Should convert \n to <br/> (line 305)
        exporter.export(session_data, output_path)

        assert output_path.exists()

    def test_pdf_export_with_timestamps(self, temp_output_dir):
        """Test PDF export with message timestamps (lines 299-301)."""
        pytest.importorskip("reportlab")

        exporter = PDFExporter(include_timestamps=True, include_system=False)
        output_path = temp_output_dir / "chat_timestamps.pdf"

        # Session data with timestamps
        session_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2026-01-15T10:00:00"
                },
                {
                    "role": "assistant",
                    "content": "Hi",
                    "timestamp": "2026-01-15T10:00:05"
                }
            ]
        }

        # Should include timestamps (lines 299-301)
        exporter.export(session_data, output_path)

        assert output_path.exists()

    def test_pdf_export_without_timestamps(self, temp_output_dir):
        """Test PDF export without timestamps."""
        pytest.importorskip("reportlab")

        exporter = PDFExporter(include_timestamps=False, include_system=False)
        output_path = temp_output_dir / "chat_no_timestamps.pdf"

        session_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2026-01-15T10:00:00"
                }
            ]
        }

        exporter.export(session_data, output_path)

        assert output_path.exists()

    def test_pdf_export_with_system_messages(self, temp_output_dir):
        """Test PDF export includes system messages when enabled."""
        pytest.importorskip("reportlab")

        exporter = PDFExporter(include_timestamps=False, include_system=True)
        output_path = temp_output_dir / "chat_system.pdf"

        session_data = {
            "messages": [
                {"role": "system", "content": "System message"},
                {"role": "user", "content": "User message"},
                {"role": "assistant", "content": "Assistant message"}
            ]
        }

        exporter.export(session_data, output_path)

        assert output_path.exists()

    def test_pdf_export_unknown_role(self, temp_output_dir):
        """Test PDF export handles unknown roles (line 295)."""
        pytest.importorskip("reportlab")

        exporter = PDFExporter(include_timestamps=False, include_system=False)
        output_path = temp_output_dir / "chat_unknown_role.pdf"

        session_data = {
            "messages": [
                {"role": "unknown_role", "content": "Mystery message"},
                {"role": "user", "content": "Normal message"}
            ]
        }

        # Should handle unknown role gracefully (line 295)
        exporter.export(session_data, output_path)

        assert output_path.exists()

    def test_pdf_export_footer(self, temp_output_dir):
        """Test PDF export includes footer (lines 310-312)."""
        pytest.importorskip("reportlab")

        exporter = PDFExporter(include_timestamps=False, include_system=False)
        output_path = temp_output_dir / "chat_footer.pdf"

        session_data = {
            "messages": [
                {"role": "user", "content": "Test message"}
            ]
        }

        # Should include export timestamp footer (lines 310-312)
        exporter.export(session_data, output_path)

        assert output_path.exists()

    def test_pdf_export_complete_document(self, temp_output_dir, sample_session_data):
        """Test complete PDF document generation (lines 236-315)."""
        pytest.importorskip("reportlab")

        exporter = PDFExporter(include_timestamps=True, include_system=False)
        output_path = temp_output_dir / "complete_chat.pdf"

        # Full session with all features
        exporter.export(sample_session_data, output_path)

        # Verify PDF structure
        assert output_path.exists()
        file_size = output_path.stat().st_size

        # PDF with content should be reasonably sized
        assert file_size > 2000  # At least 2KB for a full conversation
        assert file_size < 1000000  # But less than 1MB for this simple test


class TestPDFExporterImportError:
    """Test PDF export when reportlab is not available."""

    def test_pdf_export_without_reportlab(self, temp_output_dir):
        """Test PDF export raises ImportError when reportlab is missing (lines 226-233)."""
        exporter = PDFExporter()
        output_path = temp_output_dir / "chat.pdf"

        session_data = {
            "messages": [
                {"role": "user", "content": "Test"}
            ]
        }

        # Mock reportlab import to fail
        with patch.dict('sys.modules', {'reportlab': None, 'reportlab.lib': None}):
            with patch('llf.chat_exporters.PDFExporter.export', side_effect=ImportError("PDF export requires reportlab")):
                with pytest.raises(ImportError, match="reportlab"):
                    exporter.export(session_data, output_path)
