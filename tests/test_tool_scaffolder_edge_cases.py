"""
Comprehensive edge case tests for ToolScaffolder to improve coverage.

Tests cover:
- Exception during tool creation with cleanup (lines 114-120)
- Parameters with enum values (line 154 and 504 - same code path)
- Template types: web_scraping (line 244), file_operations (286),
  command_execution (331), database_query (382)
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from llf.tool_scaffolder import ToolScaffolder


@pytest.fixture
def temp_tools_dir(tmp_path):
    """Create temporary tools directory."""
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    return tools_dir


@pytest.fixture
def scaffolder(temp_tools_dir):
    """Create ToolScaffolder instance."""
    return ToolScaffolder(tools_dir=temp_tools_dir)


class TestCreateToolEdgeCases:
    """Test create_tool edge cases."""

    def test_create_tool_exception_with_cleanup(self, scaffolder, temp_tools_dir):
        """Test exception during creation triggers cleanup."""
        tool_name = "test_tool"
        display_name = "Test Tool"
        tool_type = "postprocessor"
        description = "Test tool"
        category = "testing"

        # Mock _write_init_py to raise exception after tool_dir is created
        with patch.object(scaffolder, '_write_init_py', side_effect=IOError("Write failed")):
            success, message = scaffolder.create_tool(
                tool_name=tool_name,
                display_name=display_name,
                description=description,
                tool_type=tool_type,
                category=category
            )

        assert success is False
        assert "Failed to create tool" in message

        # Verify cleanup occurred - tool directory should not exist
        tool_dir = temp_tools_dir / tool_name
        assert not tool_dir.exists()


class TestGetCodeTemplateTypes:
    """Test _get_code_template with different template types."""

    def test_template_web_scraping(self, scaffolder):
        """Test web_scraping template generation."""
        template = scaffolder._get_code_template('web_scraping', 'llm_invokable')
        assert 'web scraping' in template.lower()
        assert 'BeautifulSoup' in template
        assert 'execute' in template

    def test_template_file_operations(self, scaffolder):
        """Test file_operations template generation."""
        template = scaffolder._get_code_template('file_operations', 'llm_invokable')
        assert 'file operation' in template.lower()
        assert 'Path' in template
        assert 'execute' in template

    def test_template_command_execution(self, scaffolder):
        """Test command_execution template generation."""
        template = scaffolder._get_code_template('command_execution', 'llm_invokable')
        assert 'command' in template.lower()
        assert 'execute' in template

    def test_template_database_query(self, scaffolder):
        """Test database_query template generation."""
        template = scaffolder._get_code_template('database_query', 'llm_invokable')
        assert 'database' in template.lower()
        assert 'execute' in template


class TestParameterEdgeCases:
    """Test parameter handling with special attributes."""

    def test_create_tool_with_enum_parameter(self, scaffolder, temp_tools_dir):
        """Test creating tool with enum parameter."""
        tool_name = "enum_test_tool"
        display_name = "Enum Test Tool"
        description = "Tool with enum parameter"
        tool_type = "llm_invokable"
        category = "testing"
        parameters = [
            {
                'name': 'format',
                'type': 'string',
                'description': 'Output format',
                'required': True,
                'enum': ['json', 'xml', 'csv']
            }
        ]

        success, message = scaffolder.create_tool(
            tool_name=tool_name,
            display_name=display_name,
            description=description,
            tool_type=tool_type,
            category=category,
            template_type='generic',
            parameters=parameters
        )

        assert success is True

        # Verify tool_definition.json was created with enum
        tool_def_file = temp_tools_dir / tool_name / "tool_definition.json"
        assert tool_def_file.exists()

        with open(tool_def_file) as f:
            tool_def = json.load(f)

        # Check that enum is in the parameter schema
        assert 'function' in tool_def
        assert 'parameters' in tool_def['function']
        assert 'properties' in tool_def['function']['parameters']
        assert 'format' in tool_def['function']['parameters']['properties']
        assert 'enum' in tool_def['function']['parameters']['properties']['format']
        assert tool_def['function']['parameters']['properties']['format']['enum'] == ['json', 'xml', 'csv']
