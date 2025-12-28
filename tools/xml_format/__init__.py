"""
XML Format Tool - Parse XML-style function calls and convert to OpenAI JSON format.

This tool provides compatibility for LLM models that output function calls in XML format
instead of the standard OpenAI JSON format.

Usage:
    from tools.xml_format import parse_xml_function_call, convert_xml_response_to_openai, is_xml_function_call

Supported Models:
    - Qwen3-Coder series
    - Some Chinese language models
    - Custom fine-tuned models trained on XML function calling
"""

from tools.xml_format.parser import (
    parse_xml_function_call,
    parse_xml_function_calls,
    convert_xml_response_to_openai,
    is_xml_function_call
)

__all__ = [
    'parse_xml_function_call',
    'parse_xml_function_calls',
    'convert_xml_response_to_openai',
    'is_xml_function_call'
]

__version__ = '1.0.0'
