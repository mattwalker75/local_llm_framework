"""
Tests for trash management functionality.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, UTC, timedelta

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
    (test_dir / "subdir").mkdir()
    (test_dir / "subdir" / "file3.txt").write_text("File 3 content")

    return test_dir


class TestTrashManager:
    """Test TrashManager class."""

    def test_initialization_creates_structure(self, temp_trash_dir):
        """Test that initialization creates trash directory structure."""
        manager = TrashManager(temp_trash_dir)

        assert temp_trash_dir.exists()
        assert (temp_trash_dir / "memories").exists()
        assert (temp_trash_dir / "datastores").exists()
        assert (temp_trash_dir / "chat_history").exists()
        assert (temp_trash_dir / "templates").exists()

    def test_move_to_trash_single_file(self, trash_manager, sample_file):
        """Test moving a single file to trash."""
        original_path = sample_file

        success, trash_id = trash_manager.move_to_trash(
            item_type='datastore',
            item_name='test_datastore',
            paths=[original_path]
        )

        assert success is True
        # Trash ID should be in format YYYYMMDD_HHMMSS
        assert len(trash_id) == 15  # 8 digits + underscore + 6 digits
        assert '_' in trash_id
        assert not original_path.exists()

        # Verify metadata was created
        trash_path = trash_manager._get_trash_path('datastore', trash_id)
        metadata_file = trash_path / "metadata.json"
        assert metadata_file.exists()

        with open(metadata_file) as f:
            metadata = json.load(f)

        assert metadata['trash_id'] == trash_id
        assert metadata['item_type'] == 'datastore'
        assert metadata['item_name'] == 'test_datastore'
        assert len(metadata['moved_items']) == 1

    def test_move_to_trash_directory(self, trash_manager, sample_directory):
        """Test moving a directory to trash."""
        original_path = sample_directory

        success, trash_id = trash_manager.move_to_trash(
            item_type='memory',
            item_name='test_memory',
            paths=[original_path]
        )

        assert success is True
        assert not original_path.exists()

        # Verify directory was preserved in trash
        trash_path = trash_manager._get_trash_path('memory', trash_id)
        trashed_dir = trash_path / sample_directory.name

        assert trashed_dir.exists()
        assert (trashed_dir / "file1.txt").exists()
        assert (trashed_dir / "subdir" / "file3.txt").exists()

    def test_move_to_trash_invalid_type(self, trash_manager, sample_file):
        """Test moving with invalid item type."""
        success, message = trash_manager.move_to_trash(
            item_type='invalid_type',
            item_name='test',
            paths=[sample_file]
        )

        assert success is False
        assert 'Invalid item type' in message

    def test_move_to_trash_with_metadata(self, trash_manager, sample_file):
        """Test moving item with additional metadata."""
        original_metadata = {
            'display_name': 'Test Display',
            'category': 'testing',
            'custom_field': 'custom_value'
        }

        success, trash_id = trash_manager.move_to_trash(
            item_type='template',
            item_name='test_template',
            paths=[sample_file],
            original_metadata=original_metadata
        )

        assert success is True

        # Verify metadata includes original_metadata
        metadata = trash_manager.get_trash_info(trash_id)
        assert metadata['original_metadata'] == original_metadata

    def test_restore_from_trash(self, trash_manager, sample_file):
        """Test restoring an item from trash."""
        original_path = sample_file
        original_content = original_path.read_text()

        # Move to trash
        success, trash_id = trash_manager.move_to_trash(
            item_type='chat_history',
            item_name='test_session',
            paths=[original_path]
        )

        assert not original_path.exists()

        # Restore from trash
        success, message = trash_manager.restore_from_trash(trash_id)

        assert success is True
        assert original_path.exists()
        assert original_path.read_text() == original_content

    def test_restore_nonexistent_item(self, trash_manager):
        """Test restoring an item that doesn't exist."""
        success, message = trash_manager.restore_from_trash('nonexistent_id')

        assert success is False
        assert 'not found' in message

    def test_restore_when_original_exists(self, trash_manager, sample_file, tmp_path):
        """Test restore fails when original location already exists."""
        original_path = sample_file

        # Move to trash
        success, trash_id = trash_manager.move_to_trash(
            item_type='datastore',
            item_name='test',
            paths=[original_path]
        )

        # Recreate file at original location
        original_path.parent.mkdir(parents=True, exist_ok=True)
        original_path.write_text("New file")

        # Try to restore
        success, message = trash_manager.restore_from_trash(trash_id)

        assert success is False
        assert 'already exists' in message

    def test_list_trash_items_empty(self, trash_manager):
        """Test listing trash when empty."""
        items = trash_manager.list_trash_items()
        assert items == []

    def test_list_trash_items(self, trash_manager, sample_file, tmp_path):
        """Test listing trash items."""
        # Add multiple items to trash
        file1 = sample_file
        file2 = tmp_path / "test_data" / "file2.txt"
        file2.parent.mkdir(parents=True, exist_ok=True)
        file2.write_text("File 2")

        trash_manager.move_to_trash('memory', 'memory1', [file1])
        trash_manager.move_to_trash('datastore', 'datastore1', [file2])

        items = trash_manager.list_trash_items()

        assert len(items) == 2
        assert any(item['item_type'] == 'memory' for item in items)
        assert any(item['item_type'] == 'datastore' for item in items)

    def test_list_trash_items_filtered_by_type(self, trash_manager, sample_file, tmp_path):
        """Test filtering trash items by type."""
        file1 = sample_file
        file2 = tmp_path / "test_data" / "file2.txt"
        file2.parent.mkdir(parents=True, exist_ok=True)
        file2.write_text("File 2")

        trash_manager.move_to_trash('memory', 'memory1', [file1])
        trash_manager.move_to_trash('datastore', 'datastore1', [file2])

        memory_items = trash_manager.list_trash_items(item_type='memory')

        assert len(memory_items) == 1
        assert memory_items[0]['item_type'] == 'memory'

    def test_list_trash_items_filtered_by_age(self, trash_manager, sample_file, temp_trash_dir):
        """Test filtering trash items by age."""
        # Add item to trash
        success, trash_id = trash_manager.move_to_trash(
            'memory',
            'old_memory',
            [sample_file]
        )

        # Manually modify deletion date to make it old
        trash_path = trash_manager._get_trash_path('memory', trash_id)
        metadata_file = trash_path / "metadata.json"

        with open(metadata_file) as f:
            metadata = json.load(f)

        # Set deletion date to 40 days ago
        old_date = datetime.now(UTC) - timedelta(days=40)
        metadata['deleted_date'] = old_date.isoformat()

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        # Test filtering
        old_items = trash_manager.list_trash_items(older_than_days=30)
        recent_items = trash_manager.list_trash_items(older_than_days=50)

        assert len(old_items) == 1
        assert len(recent_items) == 0

    def test_get_trash_info(self, trash_manager, sample_file):
        """Test getting detailed trash item info."""
        success, trash_id = trash_manager.move_to_trash(
            'template',
            'test_template',
            [sample_file],
            original_metadata={'category': 'testing'}
        )

        info = trash_manager.get_trash_info(trash_id)

        assert info is not None
        assert info['trash_id'] == trash_id
        assert info['item_type'] == 'template'
        assert info['item_name'] == 'test_template'
        assert 'age_days' in info
        assert info['original_metadata']['category'] == 'testing'

    def test_get_trash_info_nonexistent(self, trash_manager):
        """Test getting info for nonexistent item."""
        info = trash_manager.get_trash_info('nonexistent_id')
        assert info is None

    def test_empty_trash_default(self, trash_manager, sample_file, temp_trash_dir):
        """Test emptying trash with default 30-day threshold."""
        # Add item to trash
        success, trash_id = trash_manager.move_to_trash(
            'memory',
            'old_memory',
            [sample_file]
        )

        # Manually set old deletion date
        trash_path = trash_manager._get_trash_path('memory', trash_id)
        metadata_file = trash_path / "metadata.json"

        with open(metadata_file) as f:
            metadata = json.load(f)

        old_date = datetime.now(UTC) - timedelta(days=35)
        metadata['deleted_date'] = old_date.isoformat()

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        # Empty trash
        deleted_count, deleted_ids = trash_manager.empty_trash()

        assert deleted_count == 1
        assert trash_id in deleted_ids
        assert not trash_path.exists()

    def test_empty_trash_custom_days(self, trash_manager, sample_file, temp_trash_dir):
        """Test emptying trash with custom day threshold."""
        success, trash_id = trash_manager.move_to_trash(
            'datastore',
            'test_datastore',
            [sample_file]
        )

        # Modify deletion date to 10 days ago
        trash_path = trash_manager._get_trash_path('datastore', trash_id)
        metadata_file = trash_path / "metadata.json"

        with open(metadata_file) as f:
            metadata = json.load(f)

        old_date = datetime.now(UTC) - timedelta(days=10)
        metadata['deleted_date'] = old_date.isoformat()

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        # Empty with 7-day threshold
        deleted_count, _ = trash_manager.empty_trash(older_than_days=7)

        assert deleted_count == 1
        assert not trash_path.exists()

    def test_empty_trash_force(self, trash_manager, sample_file):
        """Test force emptying all trash regardless of age."""
        # Add recent item
        success, trash_id = trash_manager.move_to_trash(
            'chat_history',
            'recent_session',
            [sample_file]
        )

        # Force delete
        deleted_count, deleted_ids = trash_manager.empty_trash(force=True)

        assert deleted_count == 1
        assert trash_id in deleted_ids

    def test_empty_trash_dry_run(self, trash_manager, sample_file):
        """Test dry run mode for emptying trash."""
        success, trash_id = trash_manager.move_to_trash(
            'template',
            'test_template',
            [sample_file]
        )

        # Dry run
        deleted_count, deleted_ids = trash_manager.empty_trash(force=True, dry_run=True)

        assert deleted_count == 1
        assert trash_id in deleted_ids

        # Verify item still exists
        trash_path = trash_manager._get_trash_path('template', trash_id)
        assert trash_path.exists()

    def test_get_trash_stats(self, trash_manager, sample_file, tmp_path):
        """Test getting trash statistics."""
        # Add items of different types
        file1 = sample_file
        file2 = tmp_path / "test_data" / "file2.txt"
        file2.parent.mkdir(parents=True, exist_ok=True)
        file2.write_text("File 2")

        trash_manager.move_to_trash('memory', 'memory1', [file1])
        trash_manager.move_to_trash('datastore', 'datastore1', [file2])

        stats = trash_manager.get_trash_stats()

        assert stats['total_items'] == 2
        assert stats['by_type']['memory'] == 1
        assert stats['by_type']['datastore'] == 1
        assert stats['oldest_item_days'] >= 0

    def test_trash_id_format(self, trash_manager, sample_file):
        """Test that trash IDs have correct format."""
        success, trash_id = trash_manager.move_to_trash(
            'memory',
            'test_memory',
            [sample_file]
        )

        # Should be in format: YYYYMMDD_HHMMSS
        parts = trash_id.split('_')
        assert len(parts) == 2

        # First part should be date
        date_part = parts[0]
        assert len(date_part) == 8
        assert date_part.isdigit()

        # Second part should be time
        time_part = parts[1]
        assert len(time_part) == 6
        assert time_part.isdigit()

    def test_multiple_files_in_single_trash_item(self, trash_manager, tmp_path):
        """Test trashing multiple files as a single item."""
        file1 = tmp_path / "test_data" / "file1.txt"
        file2 = tmp_path / "test_data" / "file2.txt"
        file1.parent.mkdir(parents=True, exist_ok=True)
        file1.write_text("File 1")
        file2.write_text("File 2")

        success, trash_id = trash_manager.move_to_trash(
            'datastore',
            'multi_file_datastore',
            paths=[file1, file2]
        )

        assert success is True
        assert not file1.exists()
        assert not file2.exists()

        # Verify both files are in metadata
        metadata = trash_manager.get_trash_info(trash_id)
        assert len(metadata['moved_items']) == 2

    def test_restore_directory_structure(self, trash_manager, sample_directory):
        """Test that directory structure is preserved during trash and restore."""
        original_subfile = sample_directory / "subdir" / "file3.txt"
        original_content = original_subfile.read_text()

        # Move to trash
        success, trash_id = trash_manager.move_to_trash(
            'memory',
            'structured_memory',
            [sample_directory]
        )

        # Restore
        success, _ = trash_manager.restore_from_trash(trash_id)

        assert success is True
        assert original_subfile.exists()
        assert original_subfile.read_text() == original_content
