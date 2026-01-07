"""
Execute function for command execution tool.
"""

from typing import Dict, Any, List
import logging
import subprocess
import fnmatch
import json
from pathlib import Path
import shlex

logger = logging.getLogger(__name__)


def _load_tool_config() -> Dict[str, Any]:
    """Load tool configuration from registry."""
    try:
        registry_path = Path(__file__).parent.parent / 'tools_registry.json'
        with open(registry_path, 'r') as f:
            registry = json.load(f)

        # Find command_exec tool in registry
        tools = registry.get('tools', [])
        for tool in tools:
            if tool.get('name') == 'command_exec':
                return tool

        return {}
    except Exception as e:
        logger.error(f"Failed to load tool config: {e}")
        return {}


def _is_command_whitelisted(command: str, whitelist: List[str]) -> bool:
    """
    Check if a command matches any whitelist pattern.

    Args:
        command: Command to check
        whitelist: List of whitelisted commands/patterns

    Returns:
        True if command is whitelisted
    """
    if not whitelist:
        return False

    for pattern in whitelist:
        # Exact match
        if command == pattern:
            return True

        # Pattern match (e.g., 'git*' matches 'git', 'git-log', etc.)
        if fnmatch.fnmatch(command, pattern):
            return True

    return False


def _validate_command(command: str, arguments: List[str], config: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate command against whitelist.

    Args:
        command: Command to execute
        arguments: Command arguments
        config: Tool configuration

    Returns:
        Tuple of (allowed, error_message)
    """
    # Get whitelist from config
    whitelist = config.get('metadata', {}).get('whitelist', [])

    # Check if command is whitelisted
    if not _is_command_whitelisted(command, whitelist):
        return False, f"Command '{command}' is not whitelisted. Check tool whitelist configuration."

    # Additional safety check: prevent dangerous commands
    dangerous_commands = ['rm', 'del', 'format', 'mkfs', 'dd']
    for dangerous in dangerous_commands:
        if command == dangerous or command.startswith(dangerous + ' '):
            # Check if require_approval is set
            require_approval = config.get('metadata', {}).get('requires_approval', False)
            if not require_approval:
                return False, f"Dangerous command '{command}' requires approval to be enabled."

    return True, ""


def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute shell command.

    Args:
        arguments: Dict with 'command', optional 'arguments', and optional 'timeout'

    Returns:
        Dict with success status and result
    """
    try:
        # Load configuration
        config = _load_tool_config()

        # Validate inputs
        command = arguments.get('command')
        cmd_arguments = arguments.get('arguments', [])
        timeout = arguments.get('timeout', 30)

        if not command:
            return {
                "success": False,
                "error": "Missing required parameter: command"
            }

        # Ensure arguments is a list
        if not isinstance(cmd_arguments, list):
            cmd_arguments = [str(cmd_arguments)]

        # Clamp timeout to reasonable range
        timeout = max(1, min(300, int(timeout)))

        # Validate command
        allowed, error_msg = _validate_command(command, cmd_arguments, config)
        if not allowed:
            logger.warning(f"Command execution denied: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }

        # Build command list
        cmd_list = [command] + [str(arg) for arg in cmd_arguments]
        cmd_str = ' '.join(shlex.quote(part) for part in cmd_list)

        # Log command execution
        logger.info(f"Executing command: {cmd_str}")

        # Execute command
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False  # Never use shell=True for security
        )

        # Log result
        logger.info(f"Command completed: return_code={result.returncode}")

        return {
            "success": True,
            "command": cmd_str,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": False
        }

    except subprocess.TimeoutExpired as e:
        logger.warning(f"Command timed out after {timeout}s")
        return {
            "success": False,
            "error": f"Command timed out after {timeout} seconds",
            "timed_out": True,
            "timeout": timeout
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": f"Command not found: {command}. Check that the command exists on the system."
        }

    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return {
            "success": False,
            "error": f"Execution failed: {str(e)}"
        }
