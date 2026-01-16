"""
Comprehensive edge case tests for MemoryManager to improve coverage.

Tests cover:
- Registry loading with missing/invalid files
- Path resolution edge cases
- Index and metadata loading/saving errors
- CRUD operations with various error conditions
- Validation failures
- File corruption handling
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from llf.memory_manager import MemoryManager


class TestMemoryManagerInit:
    """Test MemoryManager initialization and registry loading."""

    def test_init_registry_not_found(self, tmp_path):
        """Test initialization when registry file doesn't exist."""
        registry_path = tmp_path / "missing_registry.json"
        manager = MemoryManager(registry_path=registry_path)

        assert len(manager.enabled_memories) == 0
        assert not manager.has_enabled_memories()

    def test_init_registry_invalid_json(self, tmp_path):
        """Test initialization with invalid JSON in registry."""
        registry_path = tmp_path / "bad_registry.json"
        with open(registry_path, 'w') as f:
            f.write("{invalid json{{")

        manager = MemoryManager(registry_path=registry_path)

        assert len(manager.enabled_memories) == 0

    def test_init_registry_with_disabled_memories(self, tmp_path):
        """Test that disabled memories are not loaded."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "enabled_mem", "enabled": True, "directory": "enabled"},
                {"name": "disabled_mem", "enabled": False, "directory": "disabled"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        assert "enabled_mem" in manager.enabled_memories
        assert "disabled_mem" not in manager.enabled_memories
        assert len(manager.enabled_memories) == 1

    def test_reload_clears_memories(self, tmp_path):
        """Test that reload() clears enabled_memories."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)
        assert len(manager.enabled_memories) == 1

        # Manually add an extra memory to test clearing
        manager.enabled_memories["manual_mem"] = {"test": "data"}
        assert len(manager.enabled_memories) == 2

        # Reload should clear and reload from registry
        manager.reload()

        assert len(manager.enabled_memories) == 1
        assert "test_mem" in manager.enabled_memories
        assert "manual_mem" not in manager.enabled_memories


class TestPathResolution:
    """Test path resolution for absolute vs relative paths."""

    def test_resolve_absolute_path(self, tmp_path):
        """Test resolving absolute path."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"memories": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        abs_path = "/absolute/path/to/memory"
        resolved = manager._resolve_path(abs_path)

        assert resolved == Path(abs_path)
        assert resolved.is_absolute()

    def test_resolve_relative_path(self, tmp_path):
        """Test resolving relative path."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"memories": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        rel_path = "memory/test_memory"
        resolved = manager._resolve_path(rel_path)

        assert resolved.is_absolute()
        assert "memory/test_memory" in str(resolved)


class TestGetMemoryPaths:
    """Test _get_memory_paths error handling."""

    def test_get_memory_paths_not_enabled(self, tmp_path):
        """Test getting paths for memory that's not enabled."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"memories": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        with pytest.raises(ValueError, match="not found or not enabled"):
            manager._get_memory_paths("nonexistent_memory")

    def test_get_memory_paths_no_directory(self, tmp_path):
        """Test getting paths when memory has no directory configured."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "bad_mem", "enabled": True}  # No directory field
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        with pytest.raises(ValueError, match="has no directory configured"):
            manager._get_memory_paths("bad_mem")


class TestIndexOperations:
    """Test index loading and saving edge cases."""

    def test_load_index_missing_file(self, tmp_path):
        """Test loading index when file doesn't exist."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"memories": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        missing_index = tmp_path / "missing_index.json"
        index = manager._load_index(missing_index)

        assert index == {}

    def test_load_index_invalid_json(self, tmp_path):
        """Test loading index with invalid JSON."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"memories": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        bad_index = tmp_path / "bad_index.json"
        with open(bad_index, 'w') as f:
            f.write("{bad json}")

        index = manager._load_index(bad_index)

        assert index == {}

    def test_save_index_error(self, tmp_path):
        """Test error handling when saving index fails."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"memories": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        # Try to save to a directory (should fail)
        bad_path = tmp_path

        with pytest.raises(Exception):
            manager._save_index(bad_path, {"test": "data"})


class TestMetadataOperations:
    """Test metadata loading and saving edge cases."""

    def test_load_metadata_missing_file(self, tmp_path):
        """Test loading metadata when file doesn't exist returns default."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"memories": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        missing_metadata = tmp_path / "missing_metadata.json"
        metadata = manager._load_metadata(missing_metadata)

        assert metadata['total_entries'] == 0
        assert 'last_updated' in metadata
        assert 'created_date' in metadata
        assert metadata['entry_types'] == {}

    def test_load_metadata_invalid_json(self, tmp_path):
        """Test loading metadata with invalid JSON."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"memories": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        bad_metadata = tmp_path / "bad_metadata.json"
        with open(bad_metadata, 'w') as f:
            f.write("{invalid json")

        metadata = manager._load_metadata(bad_metadata)

        assert metadata == {}

    def test_save_metadata_error(self, tmp_path):
        """Test error handling when saving metadata fails."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"memories": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        # Try to save to a directory (should fail)
        bad_path = tmp_path

        with pytest.raises(Exception):
            manager._save_metadata(bad_path, {"test": "data"})


class TestReadMemoryLine:
    """Test _read_memory_line error handling."""

    def test_read_memory_line_missing_file(self, tmp_path):
        """Test reading from non-existent memory file."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"memories": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        missing_file = tmp_path / "missing_memory.jsonl"
        result = manager._read_memory_line(missing_file, 0)

        assert result is None

    def test_read_memory_line_invalid_json(self, tmp_path):
        """Test reading line with invalid JSON."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"memories": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        bad_memory = tmp_path / "bad_memory.jsonl"
        with open(bad_memory, 'w') as f:
            f.write("{invalid json}\n")

        result = manager._read_memory_line(bad_memory, 0)

        assert result is None


class TestAddMemoryValidation:
    """Test add_memory validation and error cases."""

    def test_add_memory_empty_content(self, tmp_path):
        """Test adding memory with empty content."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        with pytest.raises(ValueError, match="content cannot be empty"):
            manager.add_memory("", memory_name="test_mem")

    def test_add_memory_whitespace_only_content(self, tmp_path):
        """Test adding memory with whitespace-only content."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        with pytest.raises(ValueError, match="content cannot be empty"):
            manager.add_memory("   \n\t  ", memory_name="test_mem")

    def test_add_memory_invalid_importance_low(self, tmp_path):
        """Test adding memory with importance < 0.0."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        with pytest.raises(ValueError, match="Importance must be between 0.0 and 1.0"):
            manager.add_memory("test content", importance=-0.1, memory_name="test_mem")

    def test_add_memory_invalid_importance_high(self, tmp_path):
        """Test adding memory with importance > 1.0."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        with pytest.raises(ValueError, match="Importance must be between 0.0 and 1.0"):
            manager.add_memory("test content", importance=1.5, memory_name="test_mem")


class TestGetMemoryEdgeCases:
    """Test get_memory edge cases."""

    def test_get_memory_not_found_in_index(self, tmp_path):
        """Test getting memory with ID not in index."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        # Create memory directory with empty index
        mem_dir = tmp_path.parent / "memory" / "test"
        mem_dir.mkdir(parents=True, exist_ok=True)
        with open(mem_dir / "index.json", 'w') as f:
            json.dump({}, f)

        result = manager.get_memory("nonexistent_id", memory_name="test_mem")

        assert result is None

    def test_get_memory_file_read_error(self, tmp_path):
        """Test get_memory when reading memory file fails."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        # Create memory directory with index pointing to non-existent line
        mem_dir = tmp_path.parent / "memory" / "test"
        mem_dir.mkdir(parents=True, exist_ok=True)

        index = {"test_id": {"line": 999, "timestamp": "2026-01-01", "type": "note", "tags": []}}
        with open(mem_dir / "index.json", 'w') as f:
            json.dump(index, f)

        # Create empty memory file
        (mem_dir / "memory.jsonl").touch()

        result = manager.get_memory("test_id", memory_name="test_mem")

        assert result is None


class TestSearchMemoriesEdgeCases:
    """Test search_memories edge cases."""

    def test_search_memories_file_not_exists(self, tmp_path):
        """Test searching when memory file doesn't exist."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        # Don't create memory file
        mem_dir = tmp_path.parent / "memory" / "test"
        mem_dir.mkdir(parents=True, exist_ok=True)

        results = manager.search_memories(query="test", memory_name="test_mem")

        assert results == []

    def test_search_memories_invalid_json_line(self, tmp_path):
        """Test searching with invalid JSON line (should skip it)."""
        # Use manager's project_root for correct path resolution
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        # Create memory file at correct location based on manager's project_root
        mem_dir = manager.project_root / "memory" / "test"
        mem_dir.mkdir(parents=True, exist_ok=True)

        with open(mem_dir / "memory.jsonl", 'w') as f:
            f.write("{invalid json}\n")
            f.write(json.dumps({"id": "valid_id", "content": "valid content", "importance": 0.8, "type": "note", "tags": []}) + "\n")

        results = manager.search_memories(memory_name="test_mem")

        # Should return only valid entry
        assert len(results) == 1
        assert results[0]['id'] == 'valid_id'


class TestUpdateMemoryEdgeCases:
    """Test update_memory edge cases."""

    def test_update_memory_not_in_index(self, tmp_path):
        """Test updating memory that's not in index."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        # Create memory directory with empty index
        mem_dir = tmp_path.parent / "memory" / "test"
        mem_dir.mkdir(parents=True, exist_ok=True)
        with open(mem_dir / "index.json", 'w') as f:
            json.dump({}, f)
        (mem_dir / "memory.jsonl").touch()

        result = manager.update_memory("nonexistent_id", content="new content", memory_name="test_mem")

        assert result is False

    def test_update_memory_invalid_importance(self, tmp_path):
        """Test updating memory with invalid importance value."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        # Create memory with one entry at correct location
        mem_dir = manager.project_root / "memory" / "test"
        mem_dir.mkdir(parents=True, exist_ok=True)

        entry = {"id": "test_id", "content": "test content", "importance": 0.5, "type": "note", "tags": [], "metadata": {}}
        with open(mem_dir / "memory.jsonl", 'w') as f:
            f.write(json.dumps(entry) + "\n")

        index = {"test_id": {"line": 0, "timestamp": "2026-01-01", "type": "note", "tags": []}}
        with open(mem_dir / "index.json", 'w') as f:
            json.dump(index, f)

        # Try to update with invalid importance - should return False (error is logged, not raised)
        result = manager.update_memory("test_id", importance=2.0, memory_name="test_mem")
        assert result is False

    def test_update_memory_json_decode_error(self, tmp_path):
        """Test updating when memory file has corrupted JSON."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        # Create memory file with mix of valid and invalid JSON at correct location
        mem_dir = manager.project_root / "memory" / "test"
        mem_dir.mkdir(parents=True, exist_ok=True)

        entry = {"id": "test_id", "content": "test content", "type": "note", "tags": [], "metadata": {}}

        with open(mem_dir / "memory.jsonl", 'w') as f:
            f.write("{invalid json}\n")  # Bad line
            f.write(json.dumps(entry) + "\n")  # Valid entry

        # Index points to line 1 (the valid entry)
        index = {"test_id": {"line": 1, "timestamp": "2026-01-01", "type": "note", "tags": []}}
        with open(mem_dir / "index.json", 'w') as f:
            json.dump(index, f)

        result = manager.update_memory("test_id", content="new content", memory_name="test_mem")

        # Should succeed - corrupted line is skipped during file read
        assert result is True


class TestDeleteMemoryEdgeCases:
    """Test delete_memory edge cases."""

    def test_delete_memory_not_in_index(self, tmp_path):
        """Test deleting memory that's not in index."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        # Create memory directory with empty index
        mem_dir = tmp_path.parent / "memory" / "test"
        mem_dir.mkdir(parents=True, exist_ok=True)
        with open(mem_dir / "index.json", 'w') as f:
            json.dump({}, f)
        (mem_dir / "memory.jsonl").touch()

        result = manager.delete_memory("nonexistent_id", memory_name="test_mem")

        assert result is False

    def test_delete_memory_json_decode_error(self, tmp_path):
        """Test deleting when memory file has corrupted JSON (should skip bad lines)."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "memories": [
                {"name": "test_mem", "enabled": True, "directory": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        # Create memory file at correct location
        mem_dir = manager.project_root / "memory" / "test"
        mem_dir.mkdir(parents=True, exist_ok=True)

        entry1 = {"id": "test_id", "content": "test content", "type": "note", "tags": []}
        entry2 = {"id": "keep_id", "content": "keep this", "type": "note", "tags": []}

        with open(mem_dir / "memory.jsonl", 'w') as f:
            f.write(json.dumps(entry1) + "\n")
            f.write("{invalid json}\n")
            f.write(json.dumps(entry2) + "\n")

        index = {"test_id": {"line": 0, "timestamp": "2026-01-01", "type": "note", "tags": []}}
        with open(mem_dir / "index.json", 'w') as f:
            json.dump(index, f)

        with open(mem_dir / "metadata.json", 'w') as f:
            json.dump({"total_entries": 3, "entry_types": {"note": 3}}, f)

        result = manager.delete_memory("test_id", memory_name="test_mem")

        # Should successfully delete despite corrupted line
        assert result is True


class TestGetStatsEdgeCases:
    """Test get_stats edge cases."""

    def test_get_stats_memory_not_found(self, tmp_path):
        """Test get_stats for non-existent memory."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"memories": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)

        stats = manager.get_stats("nonexistent_mem")

        assert 'error' in stats
        assert stats['memory_name'] == "nonexistent_mem"
