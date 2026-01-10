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

        Args:
            session_path: Path to the session file to import.

        Returns:
            Session data dictionary or None if import failed.
        """
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
            console.print(f"[red]Error parsing session file: {e}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]Error importing session: {e}[/red]")
            return None
