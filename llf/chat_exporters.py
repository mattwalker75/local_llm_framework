"""
Chat export formatters for converting conversations to various formats.

Supports:
- Markdown: Human-readable format
- JSON: Programmatic/archival format
- TXT: Plain text format
- PDF: Print-ready format
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class ChatExporter(ABC):
    """Base class for chat exporters."""

    def __init__(self, include_timestamps: bool = True, include_system: bool = False):
        """
        Initialize exporter.

        Args:
            include_timestamps: Whether to include timestamps in export.
            include_system: Whether to include system messages in export.
        """
        self.include_timestamps = include_timestamps
        self.include_system = include_system

    @abstractmethod
    def export(self, session_data: Dict[str, Any], output_path: Path) -> None:
        """Export session data to specified format."""
        pass

    def filter_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter messages based on export settings.

        Args:
            messages: List of message dictionaries.

        Returns:
            Filtered list of messages.
        """
        filtered = messages

        # Filter out system messages if not included
        if not self.include_system:
            filtered = [msg for msg in filtered if msg.get('role') != 'system']

        # Remove timestamps if not included
        if not self.include_timestamps:
            filtered = [
                {k: v for k, v in msg.items() if k != 'timestamp'}
                for msg in filtered
            ]

        return filtered


class MarkdownExporter(ChatExporter):
    """Export chat sessions to Markdown format."""

    def export(self, session_data: Dict[str, Any], output_path: Path) -> None:
        """
        Export session to Markdown.

        Args:
            session_data: Session data dictionary.
            output_path: Path to save the markdown file.
        """
        lines = []

        # Header
        lines.append("# Chat Conversation")
        lines.append("")

        # Metadata
        if session_data.get('metadata'):
            metadata = session_data['metadata']
            lines.append("## Session Information")
            lines.append("")
            if metadata.get('model'):
                lines.append(f"**Model:** {metadata['model']}")
            if metadata.get('timestamp'):
                lines.append(f"**Timestamp:** {metadata['timestamp']}")
            if session_data.get('session_id'):
                lines.append(f"**Session ID:** {session_data['session_id']}")
            lines.append("")

        # Messages
        lines.append("## Conversation")
        lines.append("")

        messages = self.filter_messages(session_data.get('messages', []))

        for i, msg in enumerate(messages, 1):
            role = msg.get('role', 'unknown').title()
            content = msg.get('content', '')

            # Add role header
            if role == 'User':
                lines.append(f"### 👤 User")
            elif role == 'Assistant':
                lines.append(f"### 🤖 Assistant")
            elif role == 'System':
                lines.append(f"### ⚙️ System")
            else:
                lines.append(f"### {role}")

            # Add timestamp if enabled
            if self.include_timestamps and msg.get('timestamp'):
                lines.append(f"*{msg['timestamp']}*")
                lines.append("")

            # Add content
            lines.append(content)
            lines.append("")

        # Footer
        lines.append("---")
        lines.append(f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        # Write to file
        output_path.write_text('\n'.join(lines), encoding='utf-8')


class JSONExporter(ChatExporter):
    """Export chat sessions to JSON format."""

    def export(self, session_data: Dict[str, Any], output_path: Path) -> None:
        """
        Export session to JSON.

        Args:
            session_data: Session data dictionary.
            output_path: Path to save the JSON file.
        """
        # Filter messages if needed
        export_data = session_data.copy()
        export_data['messages'] = self.filter_messages(session_data.get('messages', []))

        # Add export metadata
        export_data['exported_at'] = datetime.now().isoformat()
        export_data['export_settings'] = {
            'include_timestamps': self.include_timestamps,
            'include_system': self.include_system
        }

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)


class TXTExporter(ChatExporter):
    """Export chat sessions to plain text format."""

    def export(self, session_data: Dict[str, Any], output_path: Path) -> None:
        """
        Export session to plain text.

        Args:
            session_data: Session data dictionary.
            output_path: Path to save the text file.
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("CHAT CONVERSATION")
        lines.append("=" * 80)
        lines.append("")

        # Metadata
        if session_data.get('metadata'):
            metadata = session_data['metadata']
            if metadata.get('model'):
                lines.append(f"Model: {metadata['model']}")
            if metadata.get('timestamp'):
                lines.append(f"Timestamp: {metadata['timestamp']}")
            if session_data.get('session_id'):
                lines.append(f"Session ID: {session_data['session_id']}")
            lines.append("")

        # Messages
        messages = self.filter_messages(session_data.get('messages', []))

        for i, msg in enumerate(messages, 1):
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')

            lines.append("-" * 80)
            lines.append(f"{role}")

            if self.include_timestamps and msg.get('timestamp'):
                lines.append(f"Time: {msg['timestamp']}")

            lines.append("-" * 80)
            lines.append(content)
            lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append(f"Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)

        # Write to file
        output_path.write_text('\n'.join(lines), encoding='utf-8')


class PDFExporter(ChatExporter):
    """Export chat sessions to PDF format."""

    def export(self, session_data: Dict[str, Any], output_path: Path) -> None:
        """
        Export session to PDF.

        Args:
            session_data: Session data dictionary.
            output_path: Path to save the PDF file.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_LEFT, TA_CENTER
        except ImportError:
            raise ImportError(
                "PDF export requires reportlab. Install with: pip install reportlab"
            )

        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )

        # Build story (content)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#333333',
            spaceAfter=30,
            alignment=TA_CENTER
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='#666666',
            spaceAfter=12,
            spaceBefore=12
        )

        # Title
        story.append(Paragraph("Chat Conversation", title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Metadata
        if session_data.get('metadata'):
            metadata = session_data['metadata']
            meta_text = []
            if metadata.get('model'):
                meta_text.append(f"<b>Model:</b> {metadata['model']}")
            if metadata.get('timestamp'):
                meta_text.append(f"<b>Timestamp:</b> {metadata['timestamp']}")
            if session_data.get('session_id'):
                meta_text.append(f"<b>Session ID:</b> {session_data['session_id']}")

            if meta_text:
                story.append(Paragraph("<br/>".join(meta_text), styles['Normal']))
                story.append(Spacer(1, 0.3 * inch))

        # Messages
        messages = self.filter_messages(session_data.get('messages', []))

        for msg in messages:
            role = msg.get('role', 'unknown').title()
            content = msg.get('content', '')

            # Role header
            role_emoji = {'User': '👤', 'Assistant': '🤖', 'System': '⚙️'}.get(role, '')
            story.append(Paragraph(f"{role_emoji} <b>{role}</b>", heading_style))

            # Timestamp
            if self.include_timestamps and msg.get('timestamp'):
                story.append(Paragraph(f"<i>{msg['timestamp']}</i>", styles['Normal']))
                story.append(Spacer(1, 0.1 * inch))

            # Content - escape HTML and preserve line breaks
            safe_content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            safe_content = safe_content.replace('\n', '<br/>')
            story.append(Paragraph(safe_content, styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))

        # Footer
        footer_text = f"<i>Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph(footer_text, styles['Normal']))

        # Build PDF
        doc.build(story)


def get_exporter(format: str, include_timestamps: bool = True, include_system: bool = False) -> ChatExporter:
    """
    Get appropriate exporter for specified format.

    Args:
        format: Export format (markdown, json, txt, pdf).
        include_timestamps: Whether to include timestamps.
        include_system: Whether to include system messages.

    Returns:
        ChatExporter instance for the specified format.

    Raises:
        ValueError: If format is not supported.
    """
    exporters = {
        'markdown': MarkdownExporter,
        'md': MarkdownExporter,
        'json': JSONExporter,
        'txt': TXTExporter,
        'text': TXTExporter,
        'pdf': PDFExporter
    }

    exporter_class = exporters.get(format.lower())
    if not exporter_class:
        raise ValueError(
            f"Unsupported format: {format}. "
            f"Supported formats: {', '.join(set(exporters.keys()))}"
        )

    return exporter_class(include_timestamps=include_timestamps, include_system=include_system)
