"""
Chat history management for storing and retrieving conversation sessions.

This module handles:
- Saving chat sessions to disk in JSON format
- Loading and listing saved chat sessions
- Purging old chat history
- Exporting chat sessions to various formats (Markdown, JSON, PDF, TXT)
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from rich.console import Console

console = Console()


class ChatHistory:
    """Manages chat history storage and retrieval."""

    def __init__(self, history_dir: Path):
        """
        Initialize ChatHistory manager.

        Args:
            history_dir: Directory path for storing chat history files.
        """
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, messages: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> Path:
        """
        Save a chat session to disk.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            metadata: Optional metadata about the session (model, timestamp, etc.).

        Returns:
            Path to the saved session file.
        """
        timestamp = datetime.now()
        # Include microseconds to ensure uniqueness when saving multiple sessions rapidly
        session_id = timestamp.strftime("%Y%m%d_%H%M%S_%f")
        filename = f"chat_{session_id}.json"
        filepath = self.history_dir / filename

        session_data = {
            "session_id": session_id,
            "timestamp": timestamp.isoformat(),
            "messages": messages,
            "metadata": metadata or {},
            "message_count": len(messages)
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        return filepath

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a chat session from disk.

        Args:
            session_id: Session ID or filename to load.

        Returns:
            Session data dictionary or None if not found.
        """
        # Try exact filename match first
        if not session_id.endswith('.json'):
            session_id = f"chat_{session_id}.json"

        filepath = self.history_dir / session_id

        if not filepath.exists():
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[red]Error loading session {session_id}: {e}[/red]")
            return None

    def list_sessions(self, limit: Optional[int] = None, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all chat sessions.

        Args:
            limit: Optional maximum number of sessions to return.
            days: Optional filter to only show sessions from last N days.

        Returns:
            List of session metadata dictionaries.
        """
        sessions = []
        cutoff_date = None

        if days:
            cutoff_date = datetime.now() - timedelta(days=days)

        for filepath in sorted(self.history_dir.glob("chat_*.json"), reverse=True):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                session_date = datetime.fromisoformat(data['timestamp'])

                # Apply date filter
                if cutoff_date and session_date < cutoff_date:
                    continue

                sessions.append({
                    'session_id': data['session_id'],
                    'filename': filepath.name,
                    'timestamp': data['timestamp'],
                    'message_count': data['message_count'],
                    'metadata': data.get('metadata', {})
                })

                if limit and len(sessions) >= limit:
                    break

            except Exception as e:
                console.print(f"[yellow]Warning: Could not load {filepath.name}: {e}[/yellow]")
                continue

        return sessions

    def purge_old_sessions(self, days: int, dry_run: bool = False) -> int:
        """
        Delete chat sessions older than specified days.

        Args:
            days: Delete sessions older than this many days.
            dry_run: If True, only show what would be deleted without actually deleting.

        Returns:
            Number of sessions deleted (or that would be deleted in dry run).
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for filepath in self.history_dir.glob("chat_*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                session_date = datetime.fromisoformat(data['timestamp'])

                if session_date < cutoff_date:
                    if dry_run:
                        console.print(f"[yellow]Would delete:[/yellow] {filepath.name} ({data['timestamp']})")
                    else:
                        filepath.unlink()
                        console.print(f"[dim]Deleted:[/dim] {filepath.name}")
                    deleted_count += 1

            except Exception as e:
                console.print(f"[yellow]Warning: Could not process {filepath.name}: {e}[/yellow]")
                continue

        return deleted_count

    def get_total_size(self) -> int:
        """
        Get total size of all chat history files in bytes.

        Returns:
            Total size in bytes.
        """
        total = 0
        for filepath in self.history_dir.glob("chat_*.json"):
            total += filepath.stat().st_size
        return total

    def import_session(self, session_path: Path) -> Optional[Dict[str, Any]]:
        """
        Import a chat session from an external file.

        Supports multiple formats:
        - JSON (.json): Full session data with metadata
        - Markdown (.md): Human-readable format with role headers
        - Text (.txt): Plain text format with role markers

        Args:
            session_path: Path to the session file to import.

        Returns:
            Session data dictionary or None if import failed.
        """
        try:
            session_path = Path(session_path)
            file_extension = session_path.suffix.lower()

            if file_extension == '.json':
                return self._import_json(session_path)
            elif file_extension in ['.md', '.markdown']:
                return self._import_markdown(session_path)
            elif file_extension == '.txt':
                return self._import_txt(session_path)
            else:
                console.print(f"[red]Unsupported file format: {file_extension}[/red]")
                console.print("[yellow]Supported formats: .json, .md, .txt[/yellow]")
                return None

        except Exception as e:
            console.print(f"[red]Error importing session: {e}[/red]")
            return None

    def _import_json(self, session_path: Path) -> Optional[Dict[str, Any]]:
        """Import session from JSON format."""
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate that it has required fields
            if 'messages' not in data:
                console.print(f"[red]Invalid session file: missing 'messages' field[/red]")
                return None

            # Ensure it has proper structure
            if not isinstance(data['messages'], list):
                console.print(f"[red]Invalid session file: 'messages' must be a list[/red]")
                return None

            return data

        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing JSON file: {e}[/red]")
            return None

    def _import_markdown(self, session_path: Path) -> Optional[Dict[str, Any]]:
        """Import session from Markdown format."""
        import re

        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                content = f.read()

            messages = []

            # Split by role headers (### 👤 User, ### 🤖 Assistant, ### ⚙️ System)
            # Pattern matches: ### emoji Role OR ### Role
            pattern = r'###\s*(?:👤|🤖|⚙️)?\s*(User|Assistant|System)'

            parts = re.split(pattern, content, flags=re.IGNORECASE)

            # parts[0] is the header before first message (skip it)
            # Then alternates: role, content, role, content...
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    role = parts[i].strip().lower()
                    message_content = parts[i + 1].strip()

                    # Remove timestamp line if present (format: *YYYY-MM-DD HH:MM:SS*)
                    lines = message_content.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        # Skip timestamp lines and footer
                        if line.startswith('*') and line.endswith('*'):
                            continue
                        if line.startswith('---'):
                            break
                        cleaned_lines.append(line)

                    message_content = '\n'.join(cleaned_lines).strip()

                    if message_content:
                        messages.append({
                            'role': role,
                            'content': message_content
                        })

            if not messages:
                console.print(f"[red]No messages found in markdown file[/red]")
                return None

            return {
                'messages': messages,
                'metadata': {
                    'imported_from': str(session_path),
                    'import_format': 'markdown',
                    'imported_at': datetime.now().isoformat()
                }
            }

        except Exception as e:
            console.print(f"[red]Error parsing markdown file: {e}[/red]")
            return None

    def _import_txt(self, session_path: Path) -> Optional[Dict[str, Any]]:
        """Import session from plain text format."""
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                content = f.read()

            messages = []

            # Split by role markers (lines of dashes followed by role in uppercase)
            lines = content.split('\n')

            current_role = None
            current_content = []
            in_message = False

            for line in lines:
                # Check for role marker (line of dashes)
                if line.strip() == '-' * 80:
                    # If we were collecting a message, save it
                    if in_message and current_role and current_content:
                        message_text = '\n'.join(current_content).strip()
                        if message_text:
                            messages.append({
                                'role': current_role.lower(),
                                'content': message_text
                            })
                        current_content = []
                        in_message = False
                    continue

                # Check for role line (USER, ASSISTANT, SYSTEM)
                if line.strip() in ['USER', 'ASSISTANT', 'SYSTEM']:
                    current_role = line.strip()
                    in_message = True
                    continue

                # Check for timestamp line
                if line.startswith('Time: '):
                    continue

                # Check for header/footer separators
                if line.strip() == '=' * 80:
                    continue

                # Skip header lines
                if line.strip() in ['CHAT CONVERSATION', ''] and not in_message:
                    continue

                # Check for footer
                if line.startswith('Exported on '):
                    break

                # Collect message content
                if in_message:
                    current_content.append(line)

            # Save last message if exists
            if current_role and current_content:
                message_text = '\n'.join(current_content).strip()
                if message_text:
                    messages.append({
                        'role': current_role.lower(),
                        'content': message_text
                    })

            if not messages:
                console.print(f"[red]No messages found in text file[/red]")
                return None

            return {
                'messages': messages,
                'metadata': {
                    'imported_from': str(session_path),
                    'import_format': 'text',
                    'imported_at': datetime.now().isoformat()
                }
            }

        except Exception as e:
            console.print(f"[red]Error parsing text file: {e}[/red]")
            return None
