"""
Comprehensive edge case tests for chat_exporters to improve coverage.

Tests cover:
- Metadata edge cases (with/without timestamp in metadata)
- Unknown role handling in exporters
- PDF export functionality with reportlab
- Error cases for unsupported formats
- Message filtering edge cases
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

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


class TestMarkdownExporterEdgeCases:
    """Test MarkdownExporter edge cases."""

    def test_export_with_metadata_timestamp(self, temp_output_dir):
        """Test Markdown export with timestamp in metadata."""
        exporter = MarkdownExporter(include_timestamps=True, include_system=False)
        output_path = temp_output_dir / "chat.md"

        session_data = {
            "session_id": "test_session",
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "metadata": {
                "model": "test-model",
                "timestamp": "2026-01-12T10:00:00"  # Timestamp in metadata
            }
        }

        exporter.export(session_data, output_path)

        content = output_path.read_text()
        # Should include metadata timestamp
        assert "**Timestamp:** 2026-01-12T10:00:00" in content

    def test_export_with_unknown_role(self, temp_output_dir):
        """Test Markdown export with unknown message role."""
        exporter = MarkdownExporter(include_timestamps=False, include_system=True)
        output_path = temp_output_dir / "chat_unknown.md"

        session_data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "custom_role", "content": "Custom message"},  # Unknown role
                {"role": "assistant", "content": "Hi"}
            ]
        }

        exporter.export(session_data, output_path)

        content = output_path.read_text()
        # Should handle unknown role gracefully
        assert "### Custom_Role" in content
        assert "Custom message" in content

    def test_export_without_metadata(self, temp_output_dir):
        """Test Markdown export without metadata section."""
        exporter = MarkdownExporter(include_timestamps=False, include_system=False)
        output_path = temp_output_dir / "chat_no_meta.md"

        session_data = {
            "messages": [
                {"role": "user", "content": "Test"}
            ]
        }

        exporter.export(session_data, output_path)

        content = output_path.read_text()
        # Should not have Session Information section
        assert "## Session Information" not in content
        assert "## Conversation" in content


class TestTXTExporterEdgeCases:
    """Test TXTExporter edge cases."""

    def test_export_with_metadata_timestamp(self, temp_output_dir):
        """Test TXT export with timestamp in metadata."""
        exporter = TXTExporter(include_timestamps=True, include_system=False)
        output_path = temp_output_dir / "chat.txt"

        session_data = {
            "session_id": "test_session",
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "metadata": {
                "model": "test-model",
                "timestamp": "2026-01-12T10:00:00"  # Timestamp in metadata
            }
        }

        exporter.export(session_data, output_path)

        content = output_path.read_text()
        # Should include metadata timestamp
        assert "Timestamp: 2026-01-12T10:00:00" in content

    def test_export_without_metadata(self, temp_output_dir):
        """Test TXT export without metadata."""
        exporter = TXTExporter(include_timestamps=False, include_system=False)
        output_path = temp_output_dir / "chat_no_meta.txt"

        session_data = {
            "messages": [
                {"role": "user", "content": "Test"}
            ]
        }

        exporter.export(session_data, output_path)

        content = output_path.read_text()
        # Should not have metadata lines
        assert "Model:" not in content
        assert "Timestamp:" not in content


# Check if reportlab is available
try:
    import reportlab
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class TestPDFExporterEdgeCases:
    """Test PDFExporter edge cases."""

    def test_export_without_reportlab(self, temp_output_dir):
        """Test PDF export when reportlab is not installed."""
        exporter = PDFExporter(include_timestamps=True, include_system=False)
        output_path = temp_output_dir / "chat.pdf"

        session_data = {
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }

        # Mock reportlab import to raise ImportError
        with patch.dict('sys.modules', {'reportlab': None, 'reportlab.lib': None, 'reportlab.lib.pagesizes': None}):
            with pytest.raises(ImportError, match="PDF export requires reportlab"):
                exporter.export(session_data, output_path)

    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="reportlab not installed")
    @patch('reportlab.platypus.Spacer')
    @patch('reportlab.platypus.Paragraph')
    @patch('reportlab.lib.styles.ParagraphStyle')
    @patch('reportlab.lib.styles.getSampleStyleSheet')
    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_export_pdf_success(self, mock_doc, mock_styles, mock_style, mock_paragraph, mock_spacer, temp_output_dir):
        """Test successful PDF export with reportlab available."""
        exporter = PDFExporter(include_timestamps=True, include_system=False)
        output_path = temp_output_dir / "chat.pdf"

        session_data = {
            "session_id": "test_session",
            "messages": [
                {"role": "user", "content": "Hello", "timestamp": "2026-01-12T10:00:00"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "metadata": {
                "model": "test-model",
                "timestamp": "2026-01-12T09:00:00"
            }
        }

        # Mock the styles
        mock_styles_dict = {
            'Heading1': Mock(),
            'Heading2': Mock(),
            'Normal': Mock()
        }
        mock_styles.return_value = mock_styles_dict

        # Mock document build
        mock_doc_instance = Mock()
        mock_doc.return_value = mock_doc_instance

        # Export
        exporter.export(session_data, output_path)

        # Verify document was created and built
        mock_doc.assert_called_once()
        mock_doc_instance.build.assert_called_once()

    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="reportlab not installed")
    @patch('reportlab.platypus.Spacer')
    @patch('reportlab.platypus.Paragraph')
    @patch('reportlab.lib.styles.ParagraphStyle')
    @patch('reportlab.lib.styles.getSampleStyleSheet')
    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_export_pdf_with_special_characters(self, mock_doc, mock_styles, mock_style, mock_paragraph, mock_spacer, temp_output_dir):
        """Test PDF export with special HTML characters that need escaping."""
        exporter = PDFExporter(include_timestamps=False, include_system=False)
        output_path = temp_output_dir / "chat_special.pdf"

        session_data = {
            "messages": [
                {"role": "user", "content": "Test with <tags> & special chars > <"}
            ]
        }

        # Mock the styles
        mock_styles_dict = {
            'Heading1': Mock(),
            'Heading2': Mock(),
            'Normal': Mock()
        }
        mock_styles.return_value = mock_styles_dict

        # Mock document
        mock_doc_instance = Mock()
        mock_doc.return_value = mock_doc_instance

        # Export
        exporter.export(session_data, output_path)

        # Verify document was created
        mock_doc_instance.build.assert_called_once()

    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="reportlab not installed")
    @patch('reportlab.platypus.Spacer')
    @patch('reportlab.platypus.Paragraph')
    @patch('reportlab.lib.styles.ParagraphStyle')
    @patch('reportlab.lib.styles.getSampleStyleSheet')
    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_export_pdf_with_newlines(self, mock_doc, mock_styles, mock_style, mock_paragraph, mock_spacer, temp_output_dir):
        """Test PDF export with newlines in content."""
        exporter = PDFExporter(include_timestamps=False, include_system=False)
        output_path = temp_output_dir / "chat_newlines.pdf"

        session_data = {
            "messages": [
                {"role": "user", "content": "Line 1\nLine 2\nLine 3"}
            ]
        }

        # Mock the styles
        mock_styles_dict = {
            'Heading1': Mock(),
            'Heading2': Mock(),
            'Normal': Mock()
        }
        mock_styles.return_value = mock_styles_dict

        # Mock document
        mock_doc_instance = Mock()
        mock_doc.return_value = mock_doc_instance

        # Export
        exporter.export(session_data, output_path)

        # Verify document was created
        mock_doc_instance.build.assert_called_once()

    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="reportlab not installed")
    @patch('reportlab.platypus.Spacer')
    @patch('reportlab.platypus.Paragraph')
    @patch('reportlab.lib.styles.ParagraphStyle')
    @patch('reportlab.lib.styles.getSampleStyleSheet')
    @patch('reportlab.platypus.SimpleDocTemplate')
    def test_export_pdf_with_all_metadata(self, mock_doc, mock_styles, mock_style, mock_paragraph, mock_spacer, temp_output_dir):
        """Test PDF export with complete metadata."""
        exporter = PDFExporter(include_timestamps=True, include_system=False)
        output_path = temp_output_dir / "chat_full_meta.pdf"

        session_data = {
            "session_id": "test_session_123",
            "messages": [
                {"role": "user", "content": "Hello", "timestamp": "2026-01-12T10:00:00"}
            ],
            "metadata": {
                "model": "test-model-v1",
                "timestamp": "2026-01-12T09:00:00"
            }
        }

        # Mock the styles
        mock_styles_dict = {
            'Heading1': Mock(),
            'Heading2': Mock(),
            'Normal': Mock()
        }
        mock_styles.return_value = mock_styles_dict

        # Mock document
        mock_doc_instance = Mock()
        mock_doc.return_value = mock_doc_instance

        # Export
        exporter.export(session_data, output_path)

        # Verify document was created
        mock_doc_instance.build.assert_called_once()



class TestGetExporter:
    """Test get_exporter factory function."""

    def test_get_exporter_markdown(self):
        """Test getting markdown exporter."""
        exporter = get_exporter('markdown', include_timestamps=True, include_system=False)
        assert isinstance(exporter, MarkdownExporter)
        assert exporter.include_timestamps is True
        assert exporter.include_system is False

    def test_get_exporter_md_alias(self):
        """Test getting markdown exporter with 'md' alias."""
        exporter = get_exporter('md')
        assert isinstance(exporter, MarkdownExporter)

    def test_get_exporter_json(self):
        """Test getting JSON exporter."""
        exporter = get_exporter('json', include_timestamps=False, include_system=True)
        assert isinstance(exporter, JSONExporter)
        assert exporter.include_timestamps is False
        assert exporter.include_system is True

    def test_get_exporter_txt(self):
        """Test getting TXT exporter."""
        exporter = get_exporter('txt')
        assert isinstance(exporter, TXTExporter)

    def test_get_exporter_text_alias(self):
        """Test getting TXT exporter with 'text' alias."""
        exporter = get_exporter('text')
        assert isinstance(exporter, TXTExporter)

    def test_get_exporter_pdf(self):
        """Test getting PDF exporter."""
        exporter = get_exporter('pdf')
        assert isinstance(exporter, PDFExporter)

    def test_get_exporter_case_insensitive(self):
        """Test that format is case-insensitive."""
        exporter1 = get_exporter('MARKDOWN')
        exporter2 = get_exporter('Markdown')
        exporter3 = get_exporter('markdown')

        assert isinstance(exporter1, MarkdownExporter)
        assert isinstance(exporter2, MarkdownExporter)
        assert isinstance(exporter3, MarkdownExporter)

    def test_get_exporter_unsupported_format(self):
        """Test getting exporter with unsupported format."""
        with pytest.raises(ValueError, match="Unsupported format: xml"):
            get_exporter('xml')

    def test_get_exporter_empty_format(self):
        """Test getting exporter with empty format string."""
        with pytest.raises(ValueError, match="Unsupported format"):
            get_exporter('')


class TestFilterMessages:
    """Test message filtering functionality."""

    def test_filter_messages_remove_system(self):
        """Test filtering out system messages."""
        exporter = MarkdownExporter(include_timestamps=True, include_system=False)

        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant message"}
        ]

        filtered = exporter.filter_messages(messages)

        assert len(filtered) == 2
        assert all(msg['role'] != 'system' for msg in filtered)

    def test_filter_messages_keep_system(self):
        """Test keeping system messages."""
        exporter = MarkdownExporter(include_timestamps=True, include_system=True)

        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User message"}
        ]

        filtered = exporter.filter_messages(messages)

        assert len(filtered) == 2
        assert any(msg['role'] == 'system' for msg in filtered)

    def test_filter_messages_remove_timestamps(self):
        """Test removing timestamps from messages."""
        exporter = MarkdownExporter(include_timestamps=False, include_system=True)

        messages = [
            {"role": "user", "content": "Message 1", "timestamp": "2026-01-12T10:00:00"},
            {"role": "assistant", "content": "Message 2", "timestamp": "2026-01-12T10:00:01"}
        ]

        filtered = exporter.filter_messages(messages)

        assert len(filtered) == 2
        assert all('timestamp' not in msg for msg in filtered)

    def test_filter_messages_keep_timestamps(self):
        """Test keeping timestamps in messages."""
        exporter = MarkdownExporter(include_timestamps=True, include_system=True)

        messages = [
            {"role": "user", "content": "Message 1", "timestamp": "2026-01-12T10:00:00"}
        ]

        filtered = exporter.filter_messages(messages)

        assert len(filtered) == 1
        assert 'timestamp' in filtered[0]
        assert filtered[0]['timestamp'] == "2026-01-12T10:00:00"

    def test_filter_messages_both_filters(self):
        """Test filtering both system messages and timestamps."""
        exporter = MarkdownExporter(include_timestamps=False, include_system=False)

        messages = [
            {"role": "system", "content": "System", "timestamp": "2026-01-12T10:00:00"},
            {"role": "user", "content": "User", "timestamp": "2026-01-12T10:00:01"},
            {"role": "assistant", "content": "Assistant", "timestamp": "2026-01-12T10:00:02"}
        ]

        filtered = exporter.filter_messages(messages)

        assert len(filtered) == 2  # No system
        assert all('timestamp' not in msg for msg in filtered)  # No timestamps
        assert all(msg['role'] != 'system' for msg in filtered)
