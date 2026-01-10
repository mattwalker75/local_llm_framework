"""
Tests for tool scaffolding functionality.
"""

import json
import pytest
from pathlib import Path

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
    return ToolScaffolder(temp_tools_dir)


class TestToolScaffolder:
    """Test ToolScaffolder class."""

    def test_create_tool_basic(self, scaffolder, temp_tools_dir):
        """Test creating a basic tool."""
        success, message = scaffolder.create_tool(
            tool_name="test_tool",
            display_name="Test Tool",
            description="A test tool",
            tool_type="llm_invokable",
            category="testing",
            template_type="generic",
            parameters=None
        )

        assert success is True
        assert "test_tool" in message

        # Verify directory was created
        tool_dir = temp_tools_dir / "test_tool"
        assert tool_dir.exists()

    def test_create_tool_with_parameters(self, scaffolder, temp_tools_dir):
        """Test creating a tool with parameters."""
        parameters = [
            {
                "name": "query",
                "type": "string",
                "description": "Search query",
                "required": True
            },
            {
                "name": "limit",
                "type": "integer",
                "description": "Max results",
                "required": False,
                "minimum": 1,
                "maximum": 100
            }
        ]

        success, message = scaffolder.create_tool(
            tool_name="search_tool",
            display_name="Search Tool",
            description="A search tool",
            tool_type="llm_invokable",
            category="internet",
            template_type="http_api",
            parameters=parameters
        )

        assert success is True

        tool_dir = temp_tools_dir / "search_tool"

        # Verify config.json
        config_file = tool_dir / "config.json"
        assert config_file.exists()

        with open(config_file) as f:
            config = json.load(f)

        assert config["name"] == "search_tool"
        assert config["type"] == "llm_invokable"
        assert config["metadata"]["category"] == "internet"
        assert config["enabled"] is False

    def test_create_tool_creates_all_files(self, scaffolder, temp_tools_dir):
        """Test that all required files are created."""
        scaffolder.create_tool(
            tool_name="complete_tool",
            display_name="Complete Tool",
            description="A complete tool",
            tool_type="llm_invokable",
            category="general",
            template_type="generic",
            parameters=None
        )

        tool_dir = temp_tools_dir / "complete_tool"

        # Check all required files exist
        assert (tool_dir / "__init__.py").exists()
        assert (tool_dir / "execute.py").exists()
        assert (tool_dir / "tool_definition.json").exists()
        assert (tool_dir / "config.json").exists()
        assert (tool_dir / "README.md").exists()

        # Check test file was created
        tests_dir = temp_tools_dir.parent / "tests"
        assert (tests_dir / "test_complete_tool.py").exists()

    def test_create_tool_duplicate_fails(self, scaffolder, temp_tools_dir):
        """Test that creating duplicate tool fails."""
        # Create first tool
        scaffolder.create_tool(
            tool_name="duplicate_tool",
            display_name="Duplicate Tool",
            description="A tool",
            tool_type="llm_invokable",
            category="general"
        )

        # Try to create same tool again
        success, message = scaffolder.create_tool(
            tool_name="duplicate_tool",
            display_name="Duplicate Tool",
            description="A tool",
            tool_type="llm_invokable",
            category="general"
        )

        assert success is False
        assert "already exists" in message

    def test_config_json_has_required_fields(self, scaffolder, temp_tools_dir):
        """Test that config.json has all required fields."""
        scaffolder.create_tool(
            tool_name="validated_tool",
            display_name="Validated Tool",
            description="A validated tool",
            tool_type="postprocessor",
            category="formatting"
        )

        config_file = temp_tools_dir / "validated_tool" / "config.json"
        with open(config_file) as f:
            config = json.load(f)

        # Check required top-level fields
        required_fields = [
            "name", "display_name", "description", "type",
            "enabled", "directory", "created_date", "last_modified"
        ]
        for field in required_fields:
            assert field in config, f"Missing field: {field}"

        # Check required metadata fields
        assert "metadata" in config
        required_metadata = ["category", "requires_approval", "dependencies"]
        for field in required_metadata:
            assert field in config["metadata"], f"Missing metadata.{field}"

    def test_postprocessor_type(self, scaffolder, temp_tools_dir):
        """Test creating a postprocessor tool."""
        success, message = scaffolder.create_tool(
            tool_name="post_tool",
            display_name="Post Tool",
            description="A postprocessor",
            tool_type="postprocessor",
            category="processing"
        )

        assert success is True

        # Postprocessors should not have TOOL_DEFINITION
        init_file = temp_tools_dir / "post_tool" / "__init__.py"
        with open(init_file) as f:
            content = f.read()

        # Should have execute function
        assert "def execute(" in content
        # Should not have TOOL_DEFINITION
        assert "TOOL_DEFINITION" not in content

    def test_http_api_template(self, scaffolder, temp_tools_dir):
        """Test HTTP API code template."""
        scaffolder.create_tool(
            tool_name="api_tool",
            display_name="API Tool",
            description="An API tool",
            tool_type="llm_invokable",
            category="internet",
            template_type="http_api"
        )

        init_file = temp_tools_dir / "api_tool" / "__init__.py"
        with open(init_file) as f:
            content = f.read()

        # Should have HTTP-related imports/code
        assert "requests" in content.lower()

    def test_tool_definition_json_structure(self, scaffolder, temp_tools_dir):
        """Test tool_definition.json structure."""
        parameters = [
            {
                "name": "text",
                "type": "string",
                "description": "Input text",
                "required": True
            }
        ]

        scaffolder.create_tool(
            tool_name="def_tool",
            display_name="Def Tool",
            description="Tool with definition",
            tool_type="llm_invokable",
            category="general",
            parameters=parameters
        )

        tool_def_file = temp_tools_dir / "def_tool" / "tool_definition.json"
        with open(tool_def_file) as f:
            tool_def = json.load(f)

        # Check OpenAI function schema structure
        assert tool_def["type"] == "function"
        assert "function" in tool_def
        assert tool_def["function"]["name"] == "def_tool"
        assert "parameters" in tool_def["function"]
        assert "properties" in tool_def["function"]["parameters"]
        assert "text" in tool_def["function"]["parameters"]["properties"]

    def test_readme_generation(self, scaffolder, temp_tools_dir):
        """Test README.md generation."""
        scaffolder.create_tool(
            tool_name="readme_tool",
            display_name="README Tool",
            description="Tool with README",
            tool_type="llm_invokable",
            category="general"
        )

        readme_file = temp_tools_dir / "readme_tool" / "README.md"
        assert readme_file.exists()

        with open(readme_file) as f:
            content = f.read()

        # Check README contains expected sections
        assert "# README Tool" in content
        assert "## Type" in content
        assert "## Installation" in content
        assert "llf tool import readme_tool" in content
        assert "llf tool enable readme_tool" in content
