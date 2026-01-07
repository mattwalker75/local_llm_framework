"""
File Access Tool - Read and write files with whitelist validation.

This tool provides secure file access for the LLM with:
- Read-only (ro) and read-write (rw) modes
- Whitelist pattern validation (glob and fully qualified paths)
- Root directory (chroot-like) support for relative paths
- Dangerous path detection for write operations
- Size limits for file operations
- Comprehensive logging
"""

from typing import Dict, Any
import logging
import os
from pathlib import Path
import fnmatch
import json

logger = logging.getLogger(__name__)

# Tool definition for LLM
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "file_access",
        "description": "Read or write files with whitelist validation. Use 'ro' mode for reading files, 'rw' mode for reading and writing files. Supports glob patterns and fully qualified paths.",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "list"],
                    "description": "Operation to perform: 'read' to read file contents, 'write' to write/create file, 'list' to list directory contents"
                },
                "path": {
                    "type": "string",
                    "description": "File or directory path (can be relative to root_dir or fully qualified)"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (required for write operation)"
                }
            },
            "required": ["operation", "path"]
        }
    }
}


# Dangerous paths that always require approval even if require_approval is false
DANGEROUS_PATHS = [
    '/etc/*',
    '/sys/*',
    '/proc/*',
    '/dev/*',
    '/boot/*',
    '/root/*',
    '~/.ssh/*',
    '~/.aws/*',
    '~/.gnupg/*',
    '*.key',
    '*.pem',
    '*credentials*',
    '*password*',
    '*.env'
]


def _load_tool_config() -> Dict[str, Any]:
    """Load tool configuration from registry."""
    try:
        registry_path = Path(__file__).parent.parent / 'tools_registry.json'
        with open(registry_path, 'r') as f:
            registry = json.load(f)

        # Find file_access tool in registry
        tools = registry.get('tools', [])
        for tool in tools:
            if tool.get('name') == 'file_access':
                return tool

        return {}
    except Exception as e:
        logger.error(f"Failed to load tool config: {e}")
        return {}


def _get_root_dir(config: Dict[str, Any]) -> Path:
    """Get the root directory from config."""
    root_dir_str = config.get('metadata', {}).get('root_dir', os.getcwd())
    root_dir = Path(root_dir_str).resolve()

    # Validate root_dir exists
    if not root_dir.exists():
        logger.warning(f"Root directory does not exist: {root_dir}, using current directory")
        root_dir = Path(os.getcwd())

    return root_dir


def _resolve_path(path_str: str, root_dir: Path) -> Path:
    """
    Resolve a path relative to root_dir or as absolute.

    Args:
        path_str: Path string (can be relative or absolute)
        root_dir: Root directory for relative paths

    Returns:
        Resolved absolute Path
    """
    path = Path(path_str)

    # If path is absolute, use it directly
    if path.is_absolute():
        return path.resolve()

    # Otherwise, resolve relative to root_dir
    return (root_dir / path).resolve()


def _is_path_whitelisted(path: Path, whitelist: list, root_dir: Path) -> bool:
    """
    Check if a path matches any whitelist pattern.

    Args:
        path: Resolved absolute path to check
        whitelist: List of whitelist patterns (globs and fully qualified paths)
        root_dir: Root directory

    Returns:
        True if path is whitelisted
    """
    if not whitelist:
        return False

    path_str = str(path)

    for pattern in whitelist:
        # Handle fully qualified paths
        if '/' in pattern or '\\' in pattern:
            # Resolve pattern relative to root_dir if not absolute
            if not Path(pattern).is_absolute():
                pattern_path = (root_dir / pattern).resolve()
                pattern = str(pattern_path)

            # Check if path matches pattern (exact or glob)
            if fnmatch.fnmatch(path_str, pattern):
                return True
            # Also check if path is under a directory pattern
            if pattern.endswith('/*') or pattern.endswith('\\*'):
                dir_pattern = pattern[:-2]
                if path_str.startswith(dir_pattern):
                    return True
        else:
            # Handle filename glob patterns (e.g., *.txt)
            if fnmatch.fnmatch(path.name, pattern):
                return True

    return False


def _is_dangerous_path(path: Path) -> bool:
    """
    Check if a path matches dangerous path patterns.

    Args:
        path: Path to check

    Returns:
        True if path is dangerous
    """
    path_str = str(path)

    for pattern in DANGEROUS_PATHS:
        # Expand ~ to home directory
        if pattern.startswith('~'):
            pattern = str(Path(pattern).expanduser())

        if fnmatch.fnmatch(path_str, pattern):
            return True

    return False


def _check_permissions(operation: str, path: Path, config: Dict[str, Any]) -> tuple[bool, str]:
    """
    Check if operation is permitted on path.

    Args:
        operation: Operation to perform ('read', 'write', 'list')
        path: Resolved path
        config: Tool configuration

    Returns:
        Tuple of (allowed, error_message)
    """
    # Get mode from config
    mode = config.get('metadata', {}).get('mode', 'ro')
    whitelist = config.get('metadata', {}).get('whitelist', [])
    root_dir = _get_root_dir(config)

    # Check if path is whitelisted
    if not _is_path_whitelisted(path, whitelist, root_dir):
        return False, f"Path '{path}' is not whitelisted. Check tool whitelist configuration."

    # Check mode permissions
    if operation == 'read' or operation == 'list':
        # Read operations allowed in both ro and rw modes
        return True, ""

    elif operation == 'write':
        # Write operations only allowed in rw mode
        if mode != 'rw':
            return False, f"Write operation not permitted. Tool is in '{mode}' mode, requires 'rw' mode."

        # Check for dangerous paths
        if _is_dangerous_path(path):
            # Check global config for require_approval
            require_approval = config.get('metadata', {}).get('requires_approval', False)
            if not require_approval:
                # Even if approval is disabled globally, dangerous paths always require approval
                return False, f"Write to dangerous path '{path}' requires approval. This path matches sensitive system files/directories."

        return True, ""

    return False, f"Unknown operation: {operation}"


def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute file access operation.

    Args:
        arguments: Dict with 'operation', 'path', and optional 'content'

    Returns:
        Dict with success status and result
    """
    try:
        # Load configuration
        config = _load_tool_config()
        root_dir = _get_root_dir(config)

        # Validate inputs
        operation = arguments.get('operation')
        path_str = arguments.get('path')

        if not operation or not path_str:
            return {
                "success": False,
                "error": "Missing required parameters: operation and path are required"
            }

        # Resolve path
        path = _resolve_path(path_str, root_dir)

        # Log operation
        logger.info(f"File access: operation={operation}, path={path}")

        # Check permissions
        allowed, error_msg = _check_permissions(operation, path, config)
        if not allowed:
            logger.warning(f"Permission denied: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }

        # Execute operation
        if operation == 'read':
            return _execute_read(path)
        elif operation == 'write':
            content = arguments.get('content')
            if content is None:
                return {
                    "success": False,
                    "error": "Content parameter required for write operation"
                }
            return _execute_write(path, content)
        elif operation == 'list':
            return _execute_list(path)
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}"
            }

    except Exception as e:
        logger.error(f"File access failed: {e}")
        return {
            "success": False,
            "error": f"Operation failed: {str(e)}"
        }


def _execute_read(path: Path) -> Dict[str, Any]:
    """Read file contents."""
    try:
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {path}"
            }

        if not path.is_file():
            return {
                "success": False,
                "error": f"Path is not a file: {path}"
            }

        # Check file size (limit to 10MB)
        size = path.stat().st_size
        max_size = 10 * 1024 * 1024  # 10MB
        if size > max_size:
            return {
                "success": False,
                "error": f"File too large: {size} bytes (max {max_size} bytes)"
            }

        # Read file
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.info(f"Read file: {path} ({size} bytes)")

        return {
            "success": True,
            "operation": "read",
            "path": str(path),
            "content": content,
            "size": size
        }

    except UnicodeDecodeError:
        return {
            "success": False,
            "error": f"File is not a text file or has unsupported encoding: {path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Read failed: {str(e)}"
        }


def _execute_write(path: Path, content: str) -> Dict[str, Any]:
    """Write content to file."""
    try:
        # Check content size (limit to 10MB)
        size = len(content.encode('utf-8'))
        max_size = 10 * 1024 * 1024  # 10MB
        if size > max_size:
            return {
                "success": False,
                "error": f"Content too large: {size} bytes (max {max_size} bytes)"
            }

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Wrote file: {path} ({size} bytes)")

        return {
            "success": True,
            "operation": "write",
            "path": str(path),
            "size": size,
            "message": f"Successfully wrote {size} bytes to {path}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Write failed: {str(e)}"
        }


def _execute_list(path: Path) -> Dict[str, Any]:
    """List directory contents."""
    try:
        if not path.exists():
            return {
                "success": False,
                "error": f"Path not found: {path}"
            }

        if not path.is_dir():
            return {
                "success": False,
                "error": f"Path is not a directory: {path}"
            }

        # List contents
        items = []
        for item in path.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })

        logger.info(f"Listed directory: {path} ({len(items)} items)")

        return {
            "success": True,
            "operation": "list",
            "path": str(path),
            "items": items,
            "count": len(items)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"List failed: {str(e)}"
        }


__all__ = ['TOOL_DEFINITION', 'execute']
