"""
Operation type detector for determining user intent.

This module helps classify user messages into different operation types:
- READ: User is asking for information from memory
- WRITE: User is requesting to store information in memory
- GENERAL: General conversation that doesn't require memory access
"""

import re
from typing import Literal
from enum import Enum


class OperationType(str, Enum):
    """Types of operations based on user intent."""
    READ = "READ"       # Retrieve information from memory
    WRITE = "WRITE"     # Store information in memory
    GENERAL = "GENERAL" # General conversation


# Patterns that indicate READ operations (retrieving from memory)
READ_PATTERNS = [
    r'\b(what|whats|what\'s)\b.*\b(my|your|their|our)\b',
    r'\b(do you (know|remember))\b',
    r'\b(can you (recall|tell me|remind me))\b',
    r'\b(what did i (say|tell|mention))\b',
    r'\b(retrieve|recall|find|search|look up|get)\b',
    r'\b(show me|tell me about)\b',
]

# Patterns that indicate WRITE operations (storing to memory)
WRITE_PATTERNS = [
    r'\b(remember|memorize|store|save|keep track|note that)\b',
    r'\b(my .* is)\b',
    r'\b(i (am|like|prefer|want|need))\b',
    r'\b(add (this|that|to)|put in|write down)\b',
]


def detect_operation_type(user_message: str) -> OperationType:
    """
    Detect the type of operation based on user message content.

    This uses simple pattern matching to classify the user's intent.
    The classification helps determine the best execution strategy:
    - READ operations should use single-pass (accurate results needed)
    - WRITE operations can use dual-pass (streaming acknowledgment)
    - GENERAL operations can stream freely

    Args:
        user_message: The user's input message.

    Returns:
        OperationType indicating READ, WRITE, or GENERAL.

    Examples:
        >>> detect_operation_type("What's my name?")
        OperationType.READ

        >>> detect_operation_type("Remember that I like pizza")
        OperationType.WRITE

        >>> detect_operation_type("Tell me a joke")
        OperationType.GENERAL
    """
    # Normalize message for matching
    msg_lower = user_message.lower().strip()

    # Check for READ patterns first (more specific)
    for pattern in READ_PATTERNS:
        if re.search(pattern, msg_lower):
            return OperationType.READ

    # Check for WRITE patterns
    for pattern in WRITE_PATTERNS:
        if re.search(pattern, msg_lower):
            return OperationType.WRITE

    # Default to GENERAL if no patterns match
    return OperationType.GENERAL


def should_use_dual_pass(
    operation_type: OperationType,
    tool_execution_mode: str,
    tools_available: bool
) -> bool:
    """
    Determine if dual-pass execution should be used.

    Args:
        operation_type: The detected operation type.
        tool_execution_mode: Configuration setting ("single_pass", "dual_pass_write_only", "dual_pass_all").
        tools_available: Whether memory tools are available.

    Returns:
        True if dual-pass execution should be used, False otherwise.
    """
    # If no tools available, no point in dual-pass
    if not tools_available:
        return False

    # single_pass mode: Never use dual-pass
    if tool_execution_mode == "single_pass":
        return False

    # dual_pass_all mode: Always use dual-pass when tools available
    if tool_execution_mode == "dual_pass_all":
        return True

    # dual_pass_write_only mode: Only for WRITE operations
    if tool_execution_mode == "dual_pass_write_only":
        return operation_type == OperationType.WRITE

    # Unknown mode, default to safe single-pass
    return False
