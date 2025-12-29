"""
XML Tool Call Parser for Local LLM Framework.

This module provides functionality to parse XML-style function calls from models
that don't natively support OpenAI-style JSON function calling format.

Example XML format:
    <function=search_memories>
    <parameter=query>user name</parameter>
    </function>

Converts to OpenAI format:
    {
        "tool_calls": [{
            "id": "call_...",
            "type": "function",
            "function": {
                "name": "search_memories",
                "arguments": "{\"query\": \"user name\"}"
            }
        }]
    }
"""

import re
import json
import uuid
from typing import Dict, List, Optional, Any
from llf.logging_config import get_logger

logger = get_logger(__name__)


def parse_xml_function_call(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse XML-style function call from text.

    Supports formats:
    - <function=name><parameter=key>value</parameter></function>
    - <function=name><parameter=key>value</parameter>
    - Multiple parameters

    Args:
        text: Text potentially containing XML function calls

    Returns:
        Dict with parsed function call in OpenAI format, or None if no valid call found
    """
    # Pattern to match: <function=name>
    function_pattern = r'<function=([^>]+)>'
    function_match = re.search(function_pattern, text)

    if not function_match:
        return None

    function_name = function_match.group(1).strip()
    logger.debug(f"Found XML function call: {function_name}")

    # Pattern to match: <parameter=key>value</parameter>
    param_pattern = r'<parameter=([^>]+)>([^<]*)</parameter>'
    param_matches = re.findall(param_pattern, text)

    # Build arguments dict
    arguments = {}
    for param_name, param_value in param_matches:
        param_name = param_name.strip()
        param_value = param_value.strip()
        arguments[param_name] = param_value
        logger.debug(f"  Parameter: {param_name} = {param_value}")

    # Create OpenAI-style tool call
    tool_call = {
        "id": f"call_{uuid.uuid4().hex[:24]}",
        "type": "function",
        "function": {
            "name": function_name,
            "arguments": json.dumps(arguments)
        }
    }

    return tool_call


def parse_xml_function_calls(text: str) -> List[Dict[str, Any]]:
    """
    Parse multiple XML-style function calls from text.

    Args:
        text: Text potentially containing multiple XML function calls

    Returns:
        List of parsed function calls in OpenAI format
    """
    tool_calls = []

    # Find all function blocks
    function_pattern = r'<function=([^>]+)>.*?(?:</function>|$)'
    function_blocks = re.finditer(function_pattern, text, re.DOTALL)

    for block_match in function_blocks:
        block_text = block_match.group(0)
        tool_call = parse_xml_function_call(block_text)
        if tool_call:
            tool_calls.append(tool_call)

    return tool_calls


def convert_xml_response_to_openai(content: str) -> Optional[Dict[str, Any]]:
    """
    Convert XML-style function call response to OpenAI format.

    This function checks if the response contains XML function calls and converts them
    to the OpenAI tool_calls format that the runtime expects.

    Args:
        content: The response content from the LLM

    Returns:
        Dict with OpenAI-style message structure if XML calls found, None otherwise
    """
    tool_calls = parse_xml_function_calls(content)

    if not tool_calls:
        return None

    logger.info(f"XML Parser: Converted {len(tool_calls)} XML function call(s) to OpenAI format")

    # Create a mock message object similar to what OpenAI API returns
    return {
        "tool_calls": tool_calls,
        "content": None  # When using tools, content is typically None
    }


def is_xml_function_call(text: str) -> bool:
    """
    Check if text contains XML-style function calls.

    Args:
        text: Text to check

    Returns:
        True if XML function calls detected
    """
    return bool(re.search(r'<function=([^>]+)>', text))
