"""
Comprehensive edge case tests for TrashManager to improve coverage.

Tests cover:
- Invalid item type handling in _get_trash_path
- Path not existing in move_to_trash
- Exception handling during move_to_trash (cleanup)
- Metadata file missing/corrupted during restore
- Trash item path missing during restore
- Exception during restore operations
- Invalid item type in list_trash_items
- Non-directory items in trash scan
- Missing/corrupted metadata files during listing
- JSON decode errors in get_trash_info
- Non-directory items during empty_trash
- Metadata parsing errors during empty_trash
- Deletion errors during empty_trash
- JSON errors during stats collection
- Items over 30 days in stats
"""

import json
import pytest
import shutil
from pathlib import Path
from datetime import datetime, UTC, timedelta
from unittest.mock import Mock, patch, MagicMock

from llf.trash_manager import TrashManager


@pytest.fixture
def temp_trash_dir(tmp_path):
    """Create temporary trash directory."""
    trash_dir = tmp_path / "trash"
    return trash_dir


@pytest.fixture
def trash_manager(temp_trash_dir):
    """Create TrashManager instance."""
    return TrashManager(temp_trash_dir)


@pytest.fixture
def sample_file(tmp_path):
    """Create a sample file for testing."""
    test_file = tmp_path / "test_data" / "sample.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("This is a test file")
    return test_file


@pytest.fixture
def sample_directory(tmp_path):
    """Create a sample directory with files for testing."""
    test_dir = tmp_path / "test_data" / "sample_dir"
    test_dir.mkdir(parents=True, exist_ok=True)

    (test_dir / "file1.txt").write_text("File 1 content")
    (test_dir / "file2.txt").write_text("File 2 content")

    return test_dir


class TestGetTrashPathEdgeCases:
    """Test _get_trash_path edge cases."""

    def test_get_trash_path_invalid_type(self, trash_manager):
        """Test _get_trash_path with invalid item type."""
        with pytest.raises(ValueError, match="Invalid item type: invalid"):
            trash_manager._get_trash_path("invalid", "test_id")


class TestMoveToTrashEdgeCases:
    """Test move_to_trash edge cases."""

    def test_move_to_trash_path_not_exists(self, trash_manager, tmp_path):
        """Test moving path that doesn't exist (should skip with warning)."""
        nonexistent = tmp_path / "nonexistent" / "file.txt"

        success, trash_id = trash_manager.move_to_trash(
            item_type="memory",
            item_name="test_mem",
            paths=[nonexistent]
        )

        # Should succeed but skip the non-existent path
        assert success is True

        # Verify metadata shows no moved items
        metadata = trash_manager.get_trash_info(trash_id)
        assert len(metadata["moved_items"]) == 0

    def test_move_to_trash_exception_during_move(self, trash_manager, sample_file):
        """Test exception handling during move operation."""
        # Mock shutil.copy2 to raise exception
        with patch('shutil.copy2', side_effect=PermissionError("Copy denied")):
            success, error_msg = trash_manager.move_to_trash(
                item_type="datastore",
                item_name="test_store",
                paths=[sample_file]
            )

            assert success is False
            assert "Copy denied" in error_msg

    def test_move_to_trash_cleanup_on_error(self, trash_manager, sample_file):
        """Test that partial trash is cleaned up on error."""
        # Mock to fail during metadata write
        original_open = open
        def selective_open(path, *args, **kwargs):
            if 'metadata.json' in str(path) and 'w' in args:
                raise IOError("Write failed")
            return original_open(path, *args, **kwargs)

        with patch('builtins.open', side_effect=selective_open):
            success, error_msg = trash_manager.move_to_trash(
                item_type="template",
                item_name="test_template",
                paths=[sample_file]
            )

            assert success is False

    def test_move_to_trash_cleanup_error(self, trash_manager, sample_file):
        """Test when cleanup itself fails after main operation error."""
        # First, cause main operation to fail
        with patch('shutil.copy2', side_effect=Exception("Main error")):
            # Also make cleanup fail
            with patch('shutil.rmtree', side_effect=Exception("Cleanup error")):
                success, error_msg = trash_manager.move_to_trash(
                    item_type="memory",
                    item_name="test",
                    paths=[sample_file]
                )

                assert success is False
                assert "Main error" in error_msg


class TestRestoreFromTrashEdgeCases:
    """Test restore_from_trash edge cases."""

    def test_restore_metadata_file_missing(self, trash_manager, sample_file, temp_trash_dir):
        """Test restore when metadata file is missing."""
        # Move to trash first
        success, trash_id = trash_manager.move_to_trash(
            item_type="datastore",
            item_name="test",
            paths=[sample_file]
        )

        # Delete metadata file
        trash_path = trash_manager._get_trash_path("datastore", trash_id)
        metadata_file = trash_path / "metadata.json"
        metadata_file.unlink()

        # Try to restore
        success, error_msg = trash_manager.restore_from_trash(trash_id)

        assert success is False
        assert "Metadata file missing" in error_msg

    def test_restore_metadata_json_decode_error(self, trash_manager, sample_file):
        """Test restore when metadata file has invalid JSON."""
        # Move to trash first
        success, trash_id = trash_manager.move_to_trash(
            item_type="memory",
            item_name="test",
            paths=[sample_file]
        )

        # Corrupt metadata file
        trash_path = trash_manager._get_trash_path("memory", trash_id)
        metadata_file = trash_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            f.write("{invalid json{{")

        # Try to restore
        success, error_msg = trash_manager.restore_from_trash(trash_id)

        assert success is False
        assert "Failed to parse metadata" in error_msg

    def test_restore_trash_item_path_missing(self, trash_manager, sample_file, temp_trash_dir):
        """Test restore when trash item file is missing (should skip with warning)."""
        # Move to trash
        success, trash_id = trash_manager.move_to_trash(
            item_type="chat_history",
            item_name="test_session",
            paths=[sample_file]
        )

        # Delete the actual trashed file (but keep metadata)
        trash_path = trash_manager._get_trash_path("chat_history", trash_id)
        trashed_file = trash_path / sample_file.name
        trashed_file.unlink()

        # Try to restore - should succeed but skip missing file
        success, message = trash_manager.restore_from_trash(trash_id)

        # Should succeed (skips missing items)
        assert success is True

    def test_restore_exception_during_restore(self, trash_manager, sample_file):
        """Test exception handling during restore operation."""
        original_path = sample_file

        # Move to trash
        success, trash_id = trash_manager.move_to_trash(
            item_type="template",
            item_name="test",
            paths=[original_path]
        )

        # Mock shutil.copy2 to raise exception
        with patch('shutil.copy2', side_effect=PermissionError("Restore denied")):
            success, error_msg = trash_manager.restore_from_trash(trash_id)

            assert success is False
            assert "Restore denied" in error_msg or "Failed to restore" in error_msg


class TestListTrashItemsEdgeCases:
    """Test list_trash_items edge cases."""

    def test_list_trash_items_invalid_type(self, trash_manager):
        """Test listing with invalid item type."""
        items = trash_manager.list_trash_items(item_type="invalid_type")
        assert items == []

    def test_list_trash_items_non_directory_in_trash(self, trash_manager, sample_file, temp_trash_dir):
        """Test listing skips non-directory items in trash."""
        # Move item to trash
        trash_manager.move_to_trash("memory", "test", [sample_file])

        # Create a file (not directory) in trash subdirectory
        memory_dir = temp_trash_dir / "memories"
        (memory_dir / "random_file.txt").write_text("Not a trash item")

        # List should skip the file
        items = trash_manager.list_trash_items(item_type="memory")
        assert len(items) == 1  # Only the valid trash item

    def test_list_trash_items_missing_metadata(self, trash_manager, sample_file, temp_trash_dir):
        """Test listing skips items with missing metadata."""
        # Move item to trash
        success, trash_id = trash_manager.move_to_trash("datastore", "test", [sample_file])

        # Delete metadata file
        trash_path = trash_manager._get_trash_path("datastore", trash_id)
        metadata_file = trash_path / "metadata.json"
        metadata_file.unlink()

        # List should skip this item
        items = trash_manager.list_trash_items(item_type="datastore")
        assert len(items) == 0

    def test_list_trash_items_corrupted_metadata(self, trash_manager, sample_file):
        """Test listing skips items with corrupted metadata."""
        # Move item to trash
        success, trash_id = trash_manager.move_to_trash("template", "test", [sample_file])

        # Corrupt metadata
        trash_path = trash_manager._get_trash_path("template", trash_id)
        metadata_file = trash_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            f.write("{invalid json{{")

        # List should skip this item
        items = trash_manager.list_trash_items(item_type="template")
        assert len(items) == 0

    def test_list_trash_items_type_dir_not_exists(self, trash_manager, temp_trash_dir):
        """Test listing when type directory doesn't exist."""
        # Remove a type directory
        (temp_trash_dir / "memories").rmdir()

        # Should handle gracefully
        items = trash_manager.list_trash_items(item_type="memory")
        assert items == []


class TestGetTrashInfoEdgeCases:
    """Test get_trash_info edge cases."""

    def test_get_trash_info_json_decode_error(self, trash_manager, sample_file):
        """Test get_trash_info with corrupted metadata."""
        # Move to trash
        success, trash_id = trash_manager.move_to_trash("memory", "test", [sample_file])

        # Corrupt metadata
        trash_path = trash_manager._get_trash_path("memory", trash_id)
        metadata_file = trash_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            f.write("{invalid json{{")

        # Should return None
        info = trash_manager.get_trash_info(trash_id)
        assert info is None


class TestEmptyTrashEdgeCases:
    """Test empty_trash edge cases."""

    def test_empty_trash_type_dir_not_exists(self, trash_manager, temp_trash_dir):
        """Test emptying trash when type directory doesn't exist."""
        # Remove a type directory
        (temp_trash_dir / "templates").rmdir()

        # Should handle gracefully
        count, ids = trash_manager.empty_trash(force=True)
        assert count >= 0  # No error

    def test_empty_trash_non_directory_item(self, trash_manager, sample_file, temp_trash_dir):
        """Test empty_trash skips non-directory items."""
        # Add item to trash
        trash_manager.move_to_trash("chat_history", "test", [sample_file])

        # Create a file in trash subdirectory
        chat_dir = temp_trash_dir / "chat_history"
        (chat_dir / "random_file.txt").write_text("Not a trash item")

        # Empty should skip the file
        count, ids = trash_manager.empty_trash(force=True)
        assert count == 1  # Only the valid trash item

    def test_empty_trash_metadata_parse_error(self, trash_manager, sample_file):
        """Test empty_trash with metadata parsing error."""
        # Add old item
        success, trash_id = trash_manager.move_to_trash("datastore", "test", [sample_file])

        # Corrupt metadata
        trash_path = trash_manager._get_trash_path("datastore", trash_id)
        metadata_file = trash_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            f.write("{invalid json{{")

        # Should skip this item (no date to check)
        count, ids = trash_manager.empty_trash(older_than_days=0)
        assert trash_id not in ids

    def test_empty_trash_deletion_error(self, trash_manager, sample_file):
        """Test empty_trash when deletion fails."""
        # Add item
        success, trash_id = trash_manager.move_to_trash("memory", "test", [sample_file])

        # Mock shutil.rmtree to raise exception
        with patch('shutil.rmtree', side_effect=PermissionError("Delete denied")):
            count, ids = trash_manager.empty_trash(force=True)

            # Should handle error and continue
            assert trash_id not in ids


class TestGetTrashStatsEdgeCases:
    """Test get_trash_stats edge cases."""

    def test_get_trash_stats_non_directory_item(self, trash_manager, sample_file, temp_trash_dir):
        """Test stats skips non-directory items."""
        # Add item
        trash_manager.move_to_trash("template", "test", [sample_file])

        # Create a file in trash subdirectory
        template_dir = temp_trash_dir / "templates"
        (template_dir / "random_file.txt").write_text("Not a trash item")

        # Stats should only count directory
        stats = trash_manager.get_trash_stats()
        assert stats["by_type"]["template"] == 1

    def test_get_trash_stats_metadata_json_error(self, trash_manager, sample_file):
        """Test stats with JSON decode error in metadata."""
        # Add item
        success, trash_id = trash_manager.move_to_trash("memory", "test", [sample_file])

        # Corrupt metadata
        trash_path = trash_manager._get_trash_path("memory", trash_id)
        metadata_file = trash_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            f.write("{invalid json{{")

        # Should handle error and continue
        stats = trash_manager.get_trash_stats()
        assert stats["total_items"] == 1  # Item still counted
        assert stats["oldest_item_days"] == 0  # No age data available

    def test_get_trash_stats_items_over_30_days(self, trash_manager, sample_file):
        """Test stats correctly counts items over 30 days old."""
        # Add item
        success, trash_id = trash_manager.move_to_trash("datastore", "test", [sample_file])

        # Set deletion date to 35 days ago
        trash_path = trash_manager._get_trash_path("datastore", trash_id)
        metadata_file = trash_path / "metadata.json"

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        old_date = datetime.now(UTC) - timedelta(days=35)
        metadata["deleted_date"] = old_date.isoformat()

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        # Check stats
        stats = trash_manager.get_trash_stats()
        assert stats["items_over_30_days"] == 1
        assert stats["oldest_item_days"] >= 35
