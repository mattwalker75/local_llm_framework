"""
Trash management system for soft-delete functionality.

Provides 30-day recovery for deleted items including:
- Memory instances and individual memories
- Datastores
- Chat history sessions
- Prompt templates
"""

import json
import shutil
from pathlib import Path
from datetime import datetime, UTC, timedelta
from typing import List, Dict, Any, Optional
from llf.logging_config import get_logger

logger = get_logger(__name__)


class TrashManager:
    """Manages soft-delete trash operations with 30-day retention."""

    # Supported item types and their subdirectories
    ITEM_TYPES = {
        "memory": "memories",
        "datastore": "datastores",
        "chat_history": "chat_history",
        "template": "templates"
    }

    def __init__(self, trash_dir: Path):
        """
        Initialize trash manager.

        Args:
            trash_dir: Path to centralized trash directory
        """
        self.trash_dir = Path(trash_dir)
        self._ensure_trash_structure()

    def _ensure_trash_structure(self):
        """Create trash directory structure if it doesn't exist."""
        self.trash_dir.mkdir(exist_ok=True)

        for subdir in self.ITEM_TYPES.values():
            (self.trash_dir / subdir).mkdir(exist_ok=True)

    def _generate_trash_id(self, item_type: str, item_name: str) -> str:
        """
        Generate unique trash ID with timestamp.

        Args:
            item_type: Type of item (memory, datastore, etc.)
            item_name: Original name of the item (not used in ID, stored in metadata)

        Returns:
            Trash ID in format: YYYYMMDD_HHMMSS
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return timestamp

    def _get_trash_path(self, item_type: str, trash_id: str) -> Path:
        """
        Get path to trash item directory.

        Args:
            item_type: Type of item
            trash_id: Unique trash identifier

        Returns:
            Path to trash item directory
        """
        if item_type not in self.ITEM_TYPES:
            raise ValueError(f"Invalid item type: {item_type}")

        subdir = self.ITEM_TYPES[item_type]
        return self.trash_dir / subdir / trash_id

    def move_to_trash(
        self,
        item_type: str,
        item_name: str,
        paths: List[Path],
        original_metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, str]:
        """
        Move item to trash with metadata preservation.

        Args:
            item_type: Type of item (memory, datastore, chat_history, template)
            item_name: Original name of the item
            paths: List of file/directory paths to move to trash
            original_metadata: Optional metadata to preserve

        Returns:
            Tuple of (success, trash_id or error_message)
        """
        if item_type not in self.ITEM_TYPES:
            msg = f"Invalid item type: {item_type}"
            logger.error(msg)
            return (False, msg)

        # Generate unique trash ID
        trash_id = self._generate_trash_id(item_type, item_name)
        trash_path = self._get_trash_path(item_type, trash_id)

        try:
            # Create trash item directory
            trash_path.mkdir(parents=True, exist_ok=True)

            # Move all paths to trash
            moved_items = []
            for path in paths:
                if not path.exists():
                    logger.warning(f"Path does not exist, skipping: {path}")
                    continue

                dest = trash_path / path.name

                if path.is_dir():
                    shutil.copytree(path, dest)
                    shutil.rmtree(path)
                else:
                    shutil.copy2(path, dest)
                    path.unlink()

                moved_items.append({
                    "original_path": str(path.resolve()),
                    "trash_path": str(dest),
                    "is_directory": path.is_dir() if path.exists() else dest.is_dir()
                })

            # Create metadata file
            metadata = {
                "trash_id": trash_id,
                "item_type": item_type,
                "item_name": item_name,
                "deleted_date": datetime.now(UTC).isoformat(),
                "moved_items": moved_items,
                "original_metadata": original_metadata or {}
            }

            metadata_file = trash_path / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Moved {item_type} '{item_name}' to trash: {trash_id}")
            return (True, trash_id)

        except Exception as e:
            msg = f"Failed to move {item_type} '{item_name}' to trash: {e}"
            logger.error(msg)

            # Attempt cleanup of partial trash
            if trash_path.exists():
                try:
                    shutil.rmtree(trash_path)
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup partial trash: {cleanup_error}")

            return (False, str(e))

    def restore_from_trash(self, trash_id: str) -> tuple[bool, str]:
        """
        Restore item from trash to original location.

        NOTE: This does NOT update any registries. User must manually
        run the appropriate import command after restore.

        Args:
            trash_id: Unique trash identifier

        Returns:
            Tuple of (success, message)
        """
        # Find the trash item
        trash_path = None
        item_type = None

        for type_key, subdir in self.ITEM_TYPES.items():
            potential_path = self.trash_dir / subdir / trash_id
            if potential_path.exists():
                trash_path = potential_path
                item_type = type_key
                break

        if not trash_path:
            msg = f"Trash item not found: {trash_id}"
            logger.error(msg)
            return (False, msg)

        # Load metadata
        metadata_file = trash_path / "metadata.json"
        if not metadata_file.exists():
            msg = f"Metadata file missing for trash item: {trash_id}"
            logger.error(msg)
            return (False, msg)

        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except json.JSONDecodeError as e:
            msg = f"Failed to parse metadata for {trash_id}: {e}"
            logger.error(msg)
            return (False, msg)

        # Restore all moved items
        restored_items = []
        try:
            for item in metadata.get("moved_items", []):
                original_path = Path(item["original_path"])
                trash_item_path = Path(item["trash_path"])

                if not trash_item_path.exists():
                    logger.warning(f"Trash item missing: {trash_item_path}")
                    continue

                # Check if original location already exists
                if original_path.exists():
                    msg = f"Cannot restore: Original path already exists: {original_path}"
                    logger.error(msg)
                    return (False, msg)

                # Ensure parent directory exists
                original_path.parent.mkdir(parents=True, exist_ok=True)

                # Restore the item
                if item["is_directory"]:
                    shutil.copytree(trash_item_path, original_path)
                else:
                    shutil.copy2(trash_item_path, original_path)

                restored_items.append(str(original_path))

            # Remove from trash
            shutil.rmtree(trash_path)

            item_name = metadata.get("item_name", trash_id)
            msg = f"Restored {item_type} '{item_name}' from trash. Files restored to original locations. Note: You must manually import to update registries."
            logger.info(msg)
            return (True, msg)

        except Exception as e:
            msg = f"Failed to restore {trash_id}: {e}"
            logger.error(msg)
            return (False, str(e))

    def list_trash_items(
        self,
        item_type: Optional[str] = None,
        older_than_days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List items in trash with optional filtering.

        Args:
            item_type: Filter by item type (memory, datastore, etc.)
            older_than_days: Only show items older than N days

        Returns:
            List of trash item metadata dictionaries
        """
        items = []
        cutoff_date = None

        if older_than_days is not None:
            cutoff_date = datetime.now(UTC) - timedelta(days=older_than_days)

        # Determine which subdirectories to search
        search_types = {}
        if item_type:
            if item_type not in self.ITEM_TYPES:
                logger.error(f"Invalid item type: {item_type}")
                return []
            search_types[item_type] = self.ITEM_TYPES[item_type]
        else:
            search_types = self.ITEM_TYPES

        # Scan trash directories
        for type_key, subdir in search_types.items():
            type_dir = self.trash_dir / subdir

            if not type_dir.exists():
                continue

            for trash_item_dir in type_dir.iterdir():
                if not trash_item_dir.is_dir():
                    continue

                metadata_file = trash_item_dir / "metadata.json"
                if not metadata_file.exists():
                    logger.warning(f"Metadata missing for: {trash_item_dir.name}")
                    continue

                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)

                    # Parse deletion date
                    deleted_date_str = metadata.get("deleted_date")
                    if deleted_date_str:
                        deleted_date = datetime.fromisoformat(deleted_date_str)

                        # Apply age filter
                        if cutoff_date and deleted_date > cutoff_date:
                            continue

                        # Calculate age in days
                        age_days = (datetime.now(UTC) - deleted_date).days
                        metadata["age_days"] = age_days

                    items.append(metadata)

                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Failed to parse metadata for {trash_item_dir.name}: {e}")
                    continue

        # Sort by deletion date (newest first)
        items.sort(key=lambda x: x.get("deleted_date", ""), reverse=True)

        return items

    def get_trash_info(self, trash_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific trash item.

        Args:
            trash_id: Unique trash identifier

        Returns:
            Metadata dictionary or None if not found
        """
        # Find the trash item
        for type_key, subdir in self.ITEM_TYPES.items():
            trash_path = self.trash_dir / subdir / trash_id
            metadata_file = trash_path / "metadata.json"

            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)

                    # Add age calculation
                    deleted_date_str = metadata.get("deleted_date")
                    if deleted_date_str:
                        deleted_date = datetime.fromisoformat(deleted_date_str)
                        age_days = (datetime.now(UTC) - deleted_date).days
                        metadata["age_days"] = age_days

                    return metadata
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse metadata for {trash_id}: {e}")
                    return None

        return None

    def empty_trash(
        self,
        older_than_days: int = 30,
        force: bool = False,
        dry_run: bool = False
    ) -> tuple[int, List[str]]:
        """
        Permanently delete items from trash.

        Args:
            older_than_days: Delete items older than N days (default: 30)
            force: Delete all items regardless of age
            dry_run: Show what would be deleted without actually deleting

        Returns:
            Tuple of (count_deleted, list_of_deleted_ids)
        """
        if force:
            older_than_days = 0

        cutoff_date = datetime.now(UTC) - timedelta(days=older_than_days)
        deleted_count = 0
        deleted_ids = []

        for type_key, subdir in self.ITEM_TYPES.items():
            type_dir = self.trash_dir / subdir

            if not type_dir.exists():
                continue

            for trash_item_dir in type_dir.iterdir():
                if not trash_item_dir.is_dir():
                    continue

                metadata_file = trash_item_dir / "metadata.json"

                # Check deletion date
                should_delete = False
                if force:
                    should_delete = True
                elif metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)

                        deleted_date_str = metadata.get("deleted_date")
                        if deleted_date_str:
                            deleted_date = datetime.fromisoformat(deleted_date_str)
                            if deleted_date <= cutoff_date:
                                should_delete = True
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"Failed to parse metadata for {trash_item_dir.name}: {e}")

                if should_delete:
                    trash_id = trash_item_dir.name

                    if not dry_run:
                        try:
                            shutil.rmtree(trash_item_dir)
                            logger.info(f"Permanently deleted trash item: {trash_id}")
                        except Exception as e:
                            logger.error(f"Failed to delete {trash_id}: {e}")
                            continue

                    deleted_count += 1
                    deleted_ids.append(trash_id)

        return (deleted_count, deleted_ids)

    def get_trash_stats(self) -> Dict[str, Any]:
        """
        Get statistics about trash contents.

        Returns:
            Dictionary with trash statistics
        """
        stats = {
            "total_items": 0,
            "by_type": {},
            "oldest_item_days": 0,
            "items_over_30_days": 0
        }

        cutoff_30_days = datetime.now(UTC) - timedelta(days=30)

        for type_key, subdir in self.ITEM_TYPES.items():
            type_dir = self.trash_dir / subdir
            type_count = 0

            if type_dir.exists():
                for trash_item_dir in type_dir.iterdir():
                    if not trash_item_dir.is_dir():
                        continue

                    type_count += 1
                    stats["total_items"] += 1

                    # Check age
                    metadata_file = trash_item_dir / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)

                            deleted_date_str = metadata.get("deleted_date")
                            if deleted_date_str:
                                deleted_date = datetime.fromisoformat(deleted_date_str)
                                age_days = (datetime.now(UTC) - deleted_date).days

                                stats["oldest_item_days"] = max(stats["oldest_item_days"], age_days)

                                if deleted_date <= cutoff_30_days:
                                    stats["items_over_30_days"] += 1
                        except (json.JSONDecodeError, ValueError):
                            pass

            stats["by_type"][type_key] = type_count

        return stats
