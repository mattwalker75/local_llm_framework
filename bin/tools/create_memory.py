#!/usr/bin/env python3
"""
Create a new memory instance directory structure.

This script creates a blank memory directory with the required file structure
that can be enabled/disabled via the 'llf memory' command.

Usage:
    # Create a new memory instance
    ./create_memory.py my_custom_memory

    # Create another memory instance
    ./create_memory.py project_notes

The script will:
1. Create a new directory in memory/<name>/
2. Initialize required files: index.json, memory.jsonl, metadata.json, README.md
3. Add an entry to memory/memory_registry.json (with enabled=false)

Author: Local LLM Framework
License: MIT

THIS IS LEGACY CODE...  Use "llf memory create NAME" instead

"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, UTC


def create_directory_name_to_display_name(directory_name: str) -> str:
    """
    Convert directory name to display name.

    Examples:
        my_custom_memory -> My Custom Memory
        project_notes -> Project Notes

    Args:
        directory_name: The directory name

    Returns:
        Display name with title case
    """
    return directory_name.replace('_', ' ').replace('-', ' ').title()


def create_memory_structure(memory_name: str, project_root: Path) -> bool:
    """
    Create the memory directory structure and files.

    Args:
        memory_name: Name of the memory instance (directory name)
        project_root: Path to project root directory

    Returns:
        True if successful, False otherwise
    """
    memory_dir = project_root / 'memory' / memory_name

    # Check if directory already exists
    if memory_dir.exists():
        print(f"Error: Memory directory already exists: {memory_dir}", file=sys.stderr)
        print(f"Please choose a different name or remove the existing directory.", file=sys.stderr)
        return False

    # Create directory
    try:
        memory_dir.mkdir(parents=True, exist_ok=False)
        print(f"✓ Created directory: {memory_dir}")
    except Exception as e:
        print(f"Error: Failed to create directory {memory_dir}: {e}", file=sys.stderr)
        return False

    # Create index.json (empty object)
    index_file = memory_dir / 'index.json'
    try:
        with open(index_file, 'w') as f:
            json.dump({}, f, indent=2)
        print(f"✓ Created: {index_file.name}")
    except Exception as e:
        print(f"Error: Failed to create index.json: {e}", file=sys.stderr)
        return False

    # Create memory.jsonl (empty file)
    memory_file = memory_dir / 'memory.jsonl'
    try:
        memory_file.touch()
        print(f"✓ Created: {memory_file.name}")
    except Exception as e:
        print(f"Error: Failed to create memory.jsonl: {e}", file=sys.stderr)
        return False

    # Create metadata.json (initialized with defaults)
    metadata_file = memory_dir / 'metadata.json'
    current_time = datetime.now(UTC).isoformat() + "Z"

    metadata = {
        "total_entries": 0,
        "last_updated": current_time,
        "created_date": current_time,
        "size_bytes": 0,
        "oldest_entry": None,
        "newest_entry": None,
        "entry_types": {
            "note": 0,
            "fact": 0,
            "preference": 0,
            "task": 0,
            "context": 0
        },
        "statistics": {
            "average_importance": 0.0,
            "most_accessed_id": None,
            "total_accesses": 0
        }
    }

    try:
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ Created: {metadata_file.name}")
    except Exception as e:
        print(f"Error: Failed to create metadata.json: {e}", file=sys.stderr)
        return False

    # Create README.md
    readme_file = memory_dir / 'README.md'
    readme_content = """
Contains the memory data files

"""

    try:
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        print(f"✓ Created: {readme_file.name}")
    except Exception as e:
        print(f"Error: Failed to create README.md: {e}", file=sys.stderr)
        return False

    return True


def add_to_registry(memory_name: str, project_root: Path) -> bool:
    """
    Add the new memory instance to memory_registry.json.

    Args:
        memory_name: Name of the memory instance
        project_root: Path to project root directory

    Returns:
        True if successful, False otherwise
    """
    registry_file = project_root / 'memory' / 'memory_registry.json'

    if not registry_file.exists():
        print(f"Error: Registry file not found: {registry_file}", file=sys.stderr)
        return False

    # Load current registry
    try:
        with open(registry_file, 'r') as f:
            registry = json.load(f)
    except Exception as e:
        print(f"Error: Failed to read registry file: {e}", file=sys.stderr)
        return False

    # Check if memory name already exists in registry
    memories = registry.get('memories', [])
    for memory in memories:
        if memory.get('name') == memory_name:
            print(f"Error: Memory '{memory_name}' already exists in registry", file=sys.stderr)
            return False

    # Create new registry entry
    display_name = create_directory_name_to_display_name(memory_name)
    current_date = datetime.now().strftime('%Y-%m-%d')

    new_entry = {
        "name": memory_name,
        "display_name": display_name,
        "description": "Custom memory instance",
        "directory": memory_name,
        "enabled": False,
        "type": "persistent",
        "created_date": current_date,
        "last_modified": None,
        "metadata": {
            "storage_type": "json",
            "max_entries": 10000,
            "compression": False
        }
    }

    # Add to registry
    memories.append(new_entry)
    registry['memories'] = memories
    registry['last_updated'] = current_date

    # Save registry
    try:
        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
        print(f"\n✓ Added entry to memory_registry.json")
    except Exception as e:
        print(f"Error: Failed to update registry file: {e}", file=sys.stderr)
        return False

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create a new memory instance directory structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./create_memory.py my_custom_memory
  ./create_memory.py project_notes
  ./create_memory.py work_context

The script will create a new memory instance that can be enabled via 'llf memory enable <name>'.
"""
    )

    parser.add_argument(
        'memory_name',
        help='Name of the memory instance to create (will be used as directory name)'
    )

    args = parser.parse_args()
    memory_name = args.memory_name

    # Validate memory name
    if not memory_name:
        print("Error: Memory name cannot be empty", file=sys.stderr)
        sys.exit(1)

    if not memory_name.replace('_', '').replace('-', '').isalnum():
        print("Error: Memory name must contain only alphanumeric characters, underscores, and hyphens", file=sys.stderr)
        sys.exit(1)

    # Determine project root (script is in bin/tools/, so go up 2 levels)
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent.parent

    print(f"Creating new memory instance: '{memory_name}'")
    print(f"Project root: {project_root}")
    print()

    # Create memory structure
    if not create_memory_structure(memory_name, project_root):
        sys.exit(1)

    # Add to registry
    if not add_to_registry(memory_name, project_root):
        sys.exit(1)

    print()
    print("=" * 70)
    print("SUCCESS! Memory instance created successfully.")
    print("=" * 70)
    print()
    print("Registry entry added with default values:")
    print(f"  - enabled: false (use 'llf memory enable {memory_name}' to activate)")
    print(f"  - display_name: {create_directory_name_to_display_name(memory_name)}")
    print(f"  - description: Custom memory instance")
    print(f"  - type: persistent")
    print(f"  - max_entries: 10000")
    print()
    print("IMPORTANT: Please review and edit the following fields in memory_registry.json:")
    print(f"  - description: Update to describe the purpose of this memory instance")
    print(f"  - display_name: Customize if desired")
    print(f"  - metadata.max_entries: Adjust based on your needs")
    print(f"  - enabled: Set to true when ready to use (or use 'llf memory enable {memory_name}')")
    print()
    print(f"Memory location: memory/{memory_name}/")
    print()


if __name__ == '__main__':
    main()
