"""
Memory Manager for Long-Term LLM Memory

This module provides functionality for the LLM to manage long-term memory storage.
It handles:
- Loading enabled memory instances from the registry
- CRUD operations on memory entries (Create, Read, Update, Delete)
- Index and metadata management for performance
- Search functionality by keywords, tags, and filters

Author: Local LLM Framework
License: MIT
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, UTC
import uuid

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages long-term memory for the LLM.

    This class handles loading memory instances, performing CRUD operations,
    and maintaining index/metadata files for performance.
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize the memory manager.

        Args:
            registry_path: Path to memory_registry.json. If None, uses default location.
        """
        # Set registry path
        if registry_path is None:
            self.registry_path = Path(__file__).parent.parent / 'memory' / 'memory_registry.json'
        else:
            self.registry_path = Path(registry_path)

        # Project root for resolving relative paths
        self.project_root = Path(__file__).parent.parent

        # Enabled memories configuration
        self.enabled_memories: Dict[str, Dict[str, Any]] = {}

        # Load enabled memories from registry
        self._load_registry()

    def _load_registry(self):
        """Load the memory registry and identify enabled memories."""
        try:
            if not self.registry_path.exists():
                logger.warning(f"Memory registry not found at {self.registry_path}")
                return

            with open(self.registry_path, 'r') as f:
                registry = json.load(f)

            # Filter enabled memories
            memories = registry.get('memories', [])
            for memory in memories:
                if memory.get('enabled', False):
                    name = memory.get('name')
                    if name:
                        self.enabled_memories[name] = memory
                        logger.info(f"Loaded enabled memory: {name}")

        except Exception as e:
            logger.error(f"Error loading memory registry: {e}")
            self.enabled_memories = {}

    def has_enabled_memories(self) -> bool:
        """Check if any memories are enabled."""
        return len(self.enabled_memories) > 0

    def reload(self):
        """Reload the registry."""
        logger.info("Reloading memory manager configuration")
        self.enabled_memories.clear()
        self._load_registry()

    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a path that may be relative or absolute.

        Args:
            path: Path string from registry

        Returns:
            Resolved absolute Path object
        """
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        else:
            return (self.project_root / path).resolve()

    def _get_memory_paths(self, memory_name: str) -> Dict[str, Path]:
        """
        Get file paths for a memory instance.

        Args:
            memory_name: Name of the memory instance

        Returns:
            Dict with keys: base_dir, memory_file, index_file, metadata_file

        Raises:
            ValueError: If memory not found or not enabled
        """
        if memory_name not in self.enabled_memories:
            raise ValueError(f"Memory '{memory_name}' not found or not enabled")

        memory_config = self.enabled_memories[memory_name]
        memory_dir = memory_config.get('directory')

        if not memory_dir:
            raise ValueError(f"Memory '{memory_name}' has no directory configured")

        # Resolve base directory (relative to memory/)
        base_dir = self.project_root / 'memory' / memory_dir

        return {
            'base_dir': base_dir,
            'memory_file': base_dir / 'memory.jsonl',
            'index_file': base_dir / 'index.json',
            'metadata_file': base_dir / 'metadata.json'
        }

    def _load_index(self, index_path: Path) -> Dict[str, Any]:
        """Load the index file."""
        if not index_path.exists():
            return {}

        try:
            with open(index_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading index from {index_path}: {e}")
            return {}

    def _save_index(self, index_path: Path, index: Dict[str, Any]):
        """Save the index file."""
        try:
            with open(index_path, 'w') as f:
                json.dump(index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving index to {index_path}: {e}")
            raise

    def _load_metadata(self, metadata_path: Path) -> Dict[str, Any]:
        """Load the metadata file."""
        if not metadata_path.exists():
            # Return default metadata structure
            return {
                "total_entries": 0,
                "last_updated": datetime.now(UTC).isoformat() + "Z",
                "created_date": datetime.now(UTC).isoformat() + "Z",
                "size_bytes": 0,
                "oldest_entry": None,
                "newest_entry": None,
                "entry_types": {},
                "statistics": {
                    "average_importance": 0.0,
                    "most_accessed_id": None,
                    "total_accesses": 0
                }
            }

        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata from {metadata_path}: {e}")
            return {}

    def _save_metadata(self, metadata_path: Path, metadata: Dict[str, Any]):
        """Save the metadata file."""
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata to {metadata_path}: {e}")
            raise

    def _generate_id(self) -> str:
        """Generate a unique memory ID."""
        return f"mem_{uuid.uuid4().hex[:12]}"

    def _read_memory_line(self, memory_path: Path, line_number: int) -> Optional[Dict[str, Any]]:
        """
        Read a specific line from the memory file.

        Args:
            memory_path: Path to memory.jsonl
            line_number: Line number (0-indexed)

        Returns:
            Memory entry dict, or None if not found
        """
        try:
            with open(memory_path, 'r') as f:
                for i, line in enumerate(f):
                    if i == line_number:
                        return json.loads(line.strip())
            return None
        except Exception as e:
            logger.error(f"Error reading line {line_number} from {memory_path}: {e}")
            return None

    def add_memory(
        self,
        content: str,
        memory_type: str = "note",
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        source: str = "llm",
        metadata: Optional[Dict[str, Any]] = None,
        memory_name: str = "main_memory"
    ) -> Dict[str, Any]:
        """
        Add a new memory entry.

        Args:
            content: The memory content text
            memory_type: Type of memory (note, fact, preference, task, context)
            tags: List of tags for categorization
            importance: Importance score 0.0-1.0
            source: Source of memory (user, llm, system)
            metadata: Additional metadata dict
            memory_name: Name of memory instance to use

        Returns:
            The created memory entry dict

        Raises:
            ValueError: If memory not found/enabled or validation fails
        """
        # Validate inputs
        if not content or not content.strip():
            raise ValueError("Memory content cannot be empty")

        if importance < 0.0 or importance > 1.0:
            raise ValueError("Importance must be between 0.0 and 1.0")

        # Get paths
        paths = self._get_memory_paths(memory_name)
        memory_path = paths['memory_file']
        index_path = paths['index_file']
        metadata_path = paths['metadata_file']

        # Ensure directory exists
        paths['base_dir'].mkdir(parents=True, exist_ok=True)

        # Load current index and metadata
        index = self._load_index(index_path)
        meta = self._load_metadata(metadata_path)

        # Generate new entry
        memory_id = self._generate_id()
        timestamp = datetime.now(UTC).isoformat() + "Z"

        entry = {
            "id": memory_id,
            "timestamp": timestamp,
            "type": memory_type,
            "content": content.strip(),
            "tags": tags or [],
            "importance": importance,
            "source": source,
            "last_accessed": timestamp,
            "access_count": 0,
            "metadata": metadata or {}
        }

        # Append to memory file
        try:
            # Get current line count
            line_number = 0
            if memory_path.exists():
                with open(memory_path, 'r') as f:
                    line_number = sum(1 for _ in f)

            # Append new entry
            with open(memory_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')

            # Update index
            index[memory_id] = {
                "line": line_number,
                "timestamp": timestamp,
                "type": memory_type,
                "tags": tags or []
            }
            self._save_index(index_path, index)

            # Update metadata
            meta['total_entries'] = meta.get('total_entries', 0) + 1
            meta['last_updated'] = timestamp
            meta['newest_entry'] = timestamp

            if meta.get('oldest_entry') is None:
                meta['oldest_entry'] = timestamp

            # Update entry type counts
            entry_types = meta.get('entry_types', {})
            entry_types[memory_type] = entry_types.get(memory_type, 0) + 1
            meta['entry_types'] = entry_types

            # Update file size
            if memory_path.exists():
                meta['size_bytes'] = memory_path.stat().st_size

            self._save_metadata(metadata_path, meta)

            logger.info(f"Added memory {memory_id} to {memory_name}")
            return entry

        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise

    def get_memory(self, memory_id: str, memory_name: str = "main_memory") -> Optional[Dict[str, Any]]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: The memory ID
            memory_name: Name of memory instance

        Returns:
            Memory entry dict, or None if not found
        """
        try:
            paths = self._get_memory_paths(memory_name)
            index = self._load_index(paths['index_file'])

            if memory_id not in index:
                return None

            line_number = index[memory_id]['line']
            entry = self._read_memory_line(paths['memory_file'], line_number)

            if entry:
                # Update access tracking
                entry['access_count'] = entry.get('access_count', 0) + 1
                entry['last_accessed'] = datetime.now(UTC).isoformat() + "Z"
                # Note: We don't update the file here to avoid rewriting on every read
                # Access counts are tracked in memory but not immediately persisted

            return entry

        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {e}")
            return None

    def search_memories(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[str] = None,
        min_importance: Optional[float] = None,
        limit: int = 10,
        memory_name: str = "main_memory"
    ) -> List[Dict[str, Any]]:
        """
        Search memories by keywords, tags, and filters.

        Args:
            query: Keyword search in content (case-insensitive)
            tags: Filter by tags (matches if any tag matches)
            memory_type: Filter by type
            min_importance: Minimum importance score
            limit: Maximum number of results
            memory_name: Name of memory instance

        Returns:
            List of matching memory entries, sorted by importance (descending)
        """
        try:
            paths = self._get_memory_paths(memory_name)

            if not paths['memory_file'].exists():
                return []

            results = []

            # Read and filter memories
            with open(paths['memory_file'], 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())

                        # Apply filters
                        if memory_type and entry.get('type') != memory_type:
                            continue

                        if min_importance is not None and entry.get('importance', 0) < min_importance:
                            continue

                        if tags:
                            entry_tags = entry.get('tags', [])
                            if not any(tag in entry_tags for tag in tags):
                                continue

                        if query:
                            content = entry.get('content', '').lower()
                            if query.lower() not in content:
                                continue

                        results.append(entry)

                    except json.JSONDecodeError:
                        continue

            # Sort by importance (descending)
            results.sort(key=lambda x: x.get('importance', 0), reverse=True)

            # Limit results
            return results[:limit]

        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []

    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        importance: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        memory_name: str = "main_memory"
    ) -> bool:
        """
        Update an existing memory entry.

        Note: This requires rewriting the entire memory file, which is acceptable
        for occasional updates but not for frequent operations.

        Args:
            memory_id: The memory ID to update
            content: New content (if provided)
            tags: New tags (if provided)
            importance: New importance (if provided)
            metadata: New metadata (if provided)
            memory_name: Name of memory instance

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            paths = self._get_memory_paths(memory_name)
            index = self._load_index(paths['index_file'])

            if memory_id not in index:
                logger.warning(f"Memory {memory_id} not found in index")
                return False

            # Read all memories
            memories = []
            with open(paths['memory_file'], 'r') as f:
                for line in f:
                    try:
                        memories.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue

            # Find and update the target memory
            updated = False
            for entry in memories:
                if entry.get('id') == memory_id:
                    if content is not None:
                        entry['content'] = content.strip()
                    if tags is not None:
                        entry['tags'] = tags
                    if importance is not None:
                        if importance < 0.0 or importance > 1.0:
                            raise ValueError("Importance must be between 0.0 and 1.0")
                        entry['importance'] = importance
                    if metadata is not None:
                        entry['metadata'].update(metadata)

                    entry['last_accessed'] = datetime.now(UTC).isoformat() + "Z"
                    updated = True
                    break

            if not updated:
                return False

            # Rewrite memory file
            with open(paths['memory_file'], 'w') as f:
                for entry in memories:
                    f.write(json.dumps(entry) + '\n')

            # Update index if tags changed
            if tags is not None:
                index[memory_id]['tags'] = tags
                self._save_index(paths['index_file'], index)

            # Update metadata timestamp
            meta = self._load_metadata(paths['metadata_file'])
            meta['last_updated'] = datetime.now(UTC).isoformat() + "Z"
            if paths['memory_file'].exists():
                meta['size_bytes'] = paths['memory_file'].stat().st_size
            self._save_metadata(paths['metadata_file'], meta)

            logger.info(f"Updated memory {memory_id} in {memory_name}")
            return True

        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            return False

    def delete_memory(self, memory_id: str, memory_name: str = "main_memory") -> bool:
        """
        Delete a memory entry.

        Note: This requires rewriting the entire memory file and rebuilding the index.

        Args:
            memory_id: The memory ID to delete
            memory_name: Name of memory instance

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            paths = self._get_memory_paths(memory_name)
            index = self._load_index(paths['index_file'])

            if memory_id not in index:
                logger.warning(f"Memory {memory_id} not found in index")
                return False

            # Read all memories except the one to delete
            memories = []
            deleted_type = None

            with open(paths['memory_file'], 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('id') == memory_id:
                            deleted_type = entry.get('type')
                        else:
                            memories.append(entry)
                    except json.JSONDecodeError:
                        continue

            # Rewrite memory file
            with open(paths['memory_file'], 'w') as f:
                for entry in memories:
                    f.write(json.dumps(entry) + '\n')

            # Rebuild index with new line numbers
            new_index = {}
            for i, entry in enumerate(memories):
                entry_id = entry.get('id')
                if entry_id:
                    new_index[entry_id] = {
                        "line": i,
                        "timestamp": entry.get('timestamp'),
                        "type": entry.get('type'),
                        "tags": entry.get('tags', [])
                    }

            self._save_index(paths['index_file'], new_index)

            # Update metadata
            meta = self._load_metadata(paths['metadata_file'])
            meta['total_entries'] = max(0, meta.get('total_entries', 0) - 1)
            meta['last_updated'] = datetime.now(UTC).isoformat() + "Z"

            if deleted_type:
                entry_types = meta.get('entry_types', {})
                if deleted_type in entry_types:
                    entry_types[deleted_type] = max(0, entry_types[deleted_type] - 1)
                meta['entry_types'] = entry_types

            if paths['memory_file'].exists():
                meta['size_bytes'] = paths['memory_file'].stat().st_size

            self._save_metadata(paths['metadata_file'], meta)

            logger.info(f"Deleted memory {memory_id} from {memory_name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return False

    def get_stats(self, memory_name: str = "main_memory") -> Dict[str, Any]:
        """
        Get statistics about a memory instance.

        Args:
            memory_name: Name of memory instance

        Returns:
            Dict with memory statistics
        """
        try:
            paths = self._get_memory_paths(memory_name)
            meta = self._load_metadata(paths['metadata_file'])

            return {
                'memory_name': memory_name,
                'enabled': True,
                'total_entries': meta.get('total_entries', 0),
                'last_updated': meta.get('last_updated'),
                'size_bytes': meta.get('size_bytes', 0),
                'entry_types': meta.get('entry_types', {}),
                'statistics': meta.get('statistics', {})
            }

        except Exception as e:
            logger.error(f"Error getting stats for {memory_name}: {e}")
            return {'memory_name': memory_name, 'error': str(e)}
