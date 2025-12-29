"""
Unit tests for XML tool call parser.
"""

import pytest
from tools.xml_format import (
    parse_xml_function_call,
    parse_xml_function_calls,
    convert_xml_response_to_openai,
    is_xml_function_call
)


class TestXMLToolParser:
    """Test XML tool call parsing functionality."""

    def test_parse_single_parameter(self):
        """Test parsing XML with single parameter."""
        xml = "<function=search_memories><parameter=query>user name</parameter>"
        result = parse_xml_function_call(xml)

        assert result is not None
        assert result['type'] == 'function'
        assert result['function']['name'] == 'search_memories'

        import json
        args = json.loads(result['function']['arguments'])
        assert args['query'] == 'user name'

    def test_parse_multiple_parameters(self):
        """Test parsing XML with multiple parameters."""
        xml = """<function=add_memory>
        <parameter=content>User's name is Matt</parameter>
        <parameter=memory_type>fact</parameter>
        <parameter=importance>0.9</parameter>
        """
        result = parse_xml_function_call(xml)

        assert result is not None
        assert result['function']['name'] == 'add_memory'

        import json
        args = json.loads(result['function']['arguments'])
        assert args['content'] == "User's name is Matt"
        assert args['memory_type'] == 'fact'
        assert args['importance'] == '0.9'

    def test_parse_no_function(self):
        """Test parsing text with no function call."""
        text = "This is just regular text without any function calls."
        result = parse_xml_function_call(text)

        assert result is None

    def test_parse_multiple_functions(self):
        """Test parsing multiple function calls."""
        xml = """
        <function=search_memories>
        <parameter=query>name</parameter>
        </function>

        <function=add_memory>
        <parameter=content>test</parameter>
        </function>
        """
        results = parse_xml_function_calls(xml)

        assert len(results) == 2
        assert results[0]['function']['name'] == 'search_memories'
        assert results[1]['function']['name'] == 'add_memory'

    def test_convert_to_openai_format(self):
        """Test full conversion to OpenAI format."""
        xml = "<function=search_memories><parameter=query>Matt</parameter>"
        result = convert_xml_response_to_openai(xml)

        assert result is not None
        assert 'tool_calls' in result
        assert len(result['tool_calls']) == 1
        assert result['content'] is None

    def test_is_xml_function_call_positive(self):
        """Test detection of XML function calls."""
        xml = "<function=search_memories><parameter=query>test</parameter>"
        assert is_xml_function_call(xml) is True

    def test_is_xml_function_call_negative(self):
        """Test detection returns False for non-XML text."""
        text = "Regular response without any XML tags"
        assert is_xml_function_call(text) is False

    def test_parse_with_special_characters(self):
        """Test parsing with special characters in values."""
        xml = '<function=add_memory><parameter=content>User prefers "concise" answers</parameter>'
        result = parse_xml_function_call(xml)

        assert result is not None
        import json
        args = json.loads(result['function']['arguments'])
        assert 'concise' in args['content']

    def test_parse_empty_parameter(self):
        """Test parsing with empty parameter value."""
        xml = "<function=search_memories><parameter=query></parameter>"
        result = parse_xml_function_call(xml)

        assert result is not None
        import json
        args = json.loads(result['function']['arguments'])
        assert args['query'] == ''

    def test_unique_call_ids(self):
        """Test that each parsed call gets a unique ID."""
        xml = """
        <function=test1><parameter=a>1</parameter></function>
        <function=test2><parameter=b>2</parameter></function>
        """
        results = parse_xml_function_calls(xml)

        assert len(results) == 2
        assert results[0]['id'] != results[1]['id']
