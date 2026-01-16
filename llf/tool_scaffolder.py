"""
Tool scaffolding system for creating new tool skeletons.
"""

import json
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
from llf.logging_config import get_logger

logger = get_logger(__name__)


class ToolScaffolder:
    """Creates tool skeleton files and directories."""

    TOOL_TYPES = {
        'llm_invokable': {
            'display': 'LLM Invokable',
            'description': 'Tool that the LLM can call directly as a function during conversation'
        },
        'postprocessor': {
            'display': 'Postprocessor',
            'description': 'Tool that processes and modifies the LLM output before sending to user'
        },
        'preprocessor': {
            'display': 'Preprocessor',
            'description': 'Tool that processes and modifies user input before sending to LLM'
        }
    }

    CODE_TEMPLATES = {
        'http_api': {
            'display': 'HTTP API Call',
            'description': 'Template for calling external HTTP/REST APIs'
        },
        'web_scraping': {
            'display': 'Web Scraping',
            'description': 'Template for fetching and parsing web pages'
        },
        'file_operations': {
            'display': 'File Operations',
            'description': 'Template for reading/writing local files'
        },
        'command_execution': {
            'display': 'Command Execution',
            'description': 'Template for executing shell commands with security checks'
        },
        'database_query': {
            'display': 'Database Query',
            'description': 'Template for querying databases (SQL/NoSQL)'
        },
        'generic': {
            'display': 'Generic/Custom',
            'description': 'Empty template with TODO comments for custom implementation'
        }
    }

    def __init__(self, tools_dir: Path):
        """
        Initialize the tool scaffolder.

        Args:
            tools_dir: Path to the tools directory where new tools will be created
        """
        self.tools_dir = Path(tools_dir)

    def create_tool(
        self,
        tool_name: str,
        display_name: str,
        description: str,
        tool_type: str,
        category: str,
        template_type: str = 'generic',
        parameters: Optional[List[Dict[str, Any]]] = None
    ) -> tuple[bool, str]:
        """
        Create a new tool with all required files.

        Args:
            tool_name: Tool identifier (lowercase, underscores)
            display_name: Human-readable name
            description: Tool description for LLM understanding
            tool_type: Type of tool (llm_invokable, postprocessor, preprocessor)
            category: Tool category (e.g., internet, file_access, command_execution)
            template_type: Code template to use (http_api, web_scraping, etc.)
            parameters: List of parameter definitions (for llm_invokable only)

        Returns:
            Tuple of (success, message)
        """
        # Create tool directory
        tool_dir = self.tools_dir / tool_name
        if tool_dir.exists():
            return False, f"Tool directory already exists: {tool_dir}"

        try:
            tool_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created tool directory: {tool_dir}")

            # Generate and write all files
            self._write_init_py(tool_dir, tool_name, description, tool_type, template_type, parameters)
            self._write_execute_py(tool_dir)
            self._write_tool_definition_json(tool_dir, tool_name, description, parameters)
            self._write_config_json(tool_dir, tool_name, display_name, description, tool_type, category)
            self._write_readme_md(tool_dir, tool_name, display_name, description, tool_type, parameters)
            self._write_test_file(tool_dir, tool_name)

            msg = f"Successfully created tool scaffold for '{tool_name}' in {tool_dir}"
            logger.info(msg)
            return True, msg

        except Exception as e:
            logger.error(f"Failed to create tool: {e}")
            # Clean up partial creation
            if tool_dir.exists():
                import shutil
                shutil.rmtree(tool_dir)
            return False, f"Failed to create tool: {e}"

    def _write_init_py(
        self,
        tool_dir: Path,
        tool_name: str,
        description: str,
        tool_type: str,
        template_type: str,
        parameters: Optional[List[Dict[str, Any]]]
    ):
        """Generate and write __init__.py file."""
        # Build parameters schema for llm_invokable tools
        params_schema = {}
        required_params = []

        if tool_type == 'llm_invokable' and parameters:
            for param in parameters:
                param_name = param['name']
                param_type = param['type']
                param_desc = param.get('description', '')
                param_required = param.get('required', False)

                params_schema[param_name] = {
                    "type": param_type,
                    "description": param_desc
                }

                # Add constraints if present
                if 'minimum' in param:
                    params_schema[param_name]['minimum'] = param['minimum']
                if 'maximum' in param:
                    params_schema[param_name]['maximum'] = param['maximum']
                if 'enum' in param:
                    params_schema[param_name]['enum'] = param['enum']

                if param_required:
                    required_params.append(param_name)

        # Generate code template
        execute_code = self._get_code_template(template_type, tool_type)

        content = f'''"""
{description}
"""

from llf.logging_config import get_logger
from typing import Dict, Any

logger = get_logger(__name__)

'''

        # Add TOOL_DEFINITION only for llm_invokable
        if tool_type == 'llm_invokable':
            params_json = json.dumps({
                "type": "object",
                "properties": params_schema,
                "required": required_params
            }, indent=8).replace('\n', '\n        ')

            content += f'''TOOL_DEFINITION = {{
    "type": "function",
    "function": {{
        "name": "{tool_name}",
        "description": "{description}",
        "parameters": {params_json}
    }}
}}

'''

        content += execute_code

        # Add exports
        if tool_type == 'llm_invokable':
            content += "\n__all__ = ['TOOL_DEFINITION', 'execute']\n"
        else:
            content += "\n__all__ = ['execute']\n"

        with open(tool_dir / '__init__.py', 'w') as f:
            f.write(content)

    def _get_code_template(self, template_type: str, tool_type: str) -> str:
        """Get the code template based on type."""
        if template_type == 'http_api':
            return '''
def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute HTTP API call.

    Args:
        arguments: Dictionary of function arguments

    Returns:
        Dictionary with success status and data/error
    """
    try:
        import requests

        # TODO: Extract arguments
        # url = arguments.get('url')
        # method = arguments.get('method', 'GET')

        # TODO: Make HTTP request
        # response = requests.request(method, url)
        # response.raise_for_status()

        # TODO: Process response
        # data = response.json()

        logger.info(f"API call executed successfully")
        return {
            "success": True,
            "data": {}  # TODO: Return actual data
        }

    except Exception as e:
        logger.error(f"API call failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
'''
        elif template_type == 'web_scraping':
            return '''
def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute web scraping operation.

    Args:
        arguments: Dictionary of function arguments

    Returns:
        Dictionary with success status and data/error
    """
    try:
        import requests
        from bs4 import BeautifulSoup

        # TODO: Extract arguments
        # url = arguments.get('url')

        # TODO: Fetch webpage
        # response = requests.get(url, timeout=30)
        # response.raise_for_status()

        # TODO: Parse HTML
        # soup = BeautifulSoup(response.text, 'html.parser')

        # TODO: Extract data
        # data = soup.find_all('tag', class_='classname')

        logger.info(f"Web scraping completed successfully")
        return {
            "success": True,
            "data": {}  # TODO: Return extracted data
        }

    except Exception as e:
        logger.error(f"Web scraping failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
'''
        elif template_type == 'file_operations':
            return '''
def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute file operation.

    Args:
        arguments: Dictionary of function arguments

    Returns:
        Dictionary with success status and data/error
    """
    try:
        from pathlib import Path

        # TODO: Extract arguments
        # file_path = arguments.get('file_path')
        # operation = arguments.get('operation', 'read')  # read, write, append

        # TODO: Validate file path (security check)
        # if not self._is_safe_path(file_path):
        #     return {"success": False, "error": "Invalid file path"}

        # TODO: Perform file operation
        # if operation == 'read':
        #     with open(file_path, 'r') as f:
        #         content = f.read()
        # elif operation == 'write':
        #     content = arguments.get('content', '')
        #     with open(file_path, 'w') as f:
        #         f.write(content)

        logger.info(f"File operation completed successfully")
        return {
            "success": True,
            "data": {}  # TODO: Return operation result
        }

    except Exception as e:
        logger.error(f"File operation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
'''
        elif template_type == 'command_execution':
            return '''
def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute shell command with security checks.

    Args:
        arguments: Dictionary of function arguments

    Returns:
        Dictionary with success status and data/error
    """
    try:
        import subprocess

        # TODO: Extract arguments
        # command = arguments.get('command')

        # TODO: Implement whitelist validation
        # ALLOWED_COMMANDS = ['ls', 'git', 'cat']  # Example whitelist
        # cmd_name = command.split()[0]
        # if cmd_name not in ALLOWED_COMMANDS:
        #     return {"success": False, "error": f"Command '{cmd_name}' not allowed"}

        # TODO: Check for dangerous patterns
        # DANGEROUS_PATTERNS = ['rm -rf', '>', '|', ';', '&&']
        # if any(pattern in command for pattern in DANGEROUS_PATTERNS):
        #     return {"success": False, "error": "Dangerous command pattern detected"}

        # TODO: Execute command with timeout
        # result = subprocess.run(
        #     command,
        #     shell=True,
        #     capture_output=True,
        #     text=True,
        #     timeout=30
        # )

        logger.info(f"Command executed successfully")
        return {
            "success": True,
            "data": {}  # TODO: Return command output
        }

    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
'''
        elif template_type == 'database_query':
            return '''
def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute database query.

    Args:
        arguments: Dictionary of function arguments

    Returns:
        Dictionary with success status and data/error
    """
    try:
        # TODO: Import database library
        # import sqlite3  # For SQLite
        # import psycopg2  # For PostgreSQL
        # from pymongo import MongoClient  # For MongoDB

        # TODO: Extract arguments
        # query = arguments.get('query')
        # database = arguments.get('database')

        # TODO: Connect to database
        # conn = sqlite3.connect(database)
        # cursor = conn.cursor()

        # TODO: Execute query
        # cursor.execute(query)
        # results = cursor.fetchall()

        # TODO: Close connection
        # conn.close()

        logger.info(f"Database query executed successfully")
        return {
            "success": True,
            "data": {}  # TODO: Return query results
        }

    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
'''
        else:  # generic
            return '''
def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute tool operation.

    Args:
        arguments: Dictionary of function arguments

    Returns:
        Dictionary with success status and data/error
    """
    try:
        # TODO: Extract arguments
        # arg1 = arguments.get('arg1')

        # TODO: Implement your tool logic here
        # result = your_custom_logic(arg1)

        logger.info(f"Tool executed successfully")
        return {
            "success": True,
            "data": {}  # TODO: Return actual data
        }

    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
'''

    def _write_execute_py(self, tool_dir: Path):
        """Generate and write execute.py file."""
        content = '''"""
Re-export execute function for compatibility.
"""

from . import execute as _execute

execute = _execute
'''
        with open(tool_dir / 'execute.py', 'w') as f:
            f.write(content)

    def _write_tool_definition_json(
        self,
        tool_dir: Path,
        tool_name: str,
        description: str,
        parameters: Optional[List[Dict[str, Any]]]
    ):
        """Generate and write tool_definition.json file."""
        # Build parameters schema
        params_schema = {}
        required_params = []

        if parameters:
            for param in parameters:
                param_name = param['name']
                param_type = param['type']
                param_desc = param.get('description', '')
                param_required = param.get('required', False)

                params_schema[param_name] = {
                    "type": param_type,
                    "description": param_desc
                }

                # Add constraints if present
                if 'minimum' in param:
                    params_schema[param_name]['minimum'] = param['minimum']
                if 'maximum' in param:
                    params_schema[param_name]['maximum'] = param['maximum']
                if 'enum' in param:
                    params_schema[param_name]['enum'] = param['enum']

                if param_required:
                    required_params.append(param_name)

        tool_def = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": params_schema,
                    "required": required_params
                }
            }
        }

        with open(tool_dir / 'tool_definition.json', 'w') as f:
            json.dump(tool_def, f, indent=2)

    def _write_config_json(
        self,
        tool_dir: Path,
        tool_name: str,
        display_name: str,
        description: str,
        tool_type: str,
        category: str
    ):
        """Generate and write config.json file."""
        now = datetime.now(UTC).strftime("%Y-%m-%d")

        config = {
            "name": tool_name,
            "display_name": display_name,
            "description": description,
            "type": tool_type,
            "enabled": False,
            "directory": tool_name,
            "created_date": now,
            "last_modified": now,
            "metadata": {
                "category": category,
                "requires_approval": False,
                "dependencies": [],
                "use_case": f"TODO: Describe the use case for {tool_name}",
                "supported_states": ["false", "true"]
            }
        }

        with open(tool_dir / 'config.json', 'w') as f:
            json.dump(config, f, indent=2)

    def _write_readme_md(
        self,
        tool_dir: Path,
        tool_name: str,
        display_name: str,
        description: str,
        tool_type: str,
        parameters: Optional[List[Dict[str, Any]]]
    ):
        """Generate and write README.md file."""
        content = f'''# {display_name}

{description}

## Type

**{tool_type}** - {self.TOOL_TYPES[tool_type]['description']}

## Installation

This tool is located in the tools directory but is not yet registered.

To add it to the registry:
```bash
llf tool import {tool_name}
```

To enable it:
```bash
llf tool enable {tool_name}
```

## Configuration

Edit `config.json` to customize:
- `enabled`: Set to `true` to enable the tool
- `metadata.requires_approval`: Set to `true` if tool requires user approval
- `metadata.dependencies`: List any Python package dependencies

'''

        if tool_type == 'llm_invokable' and parameters:
            content += '''## Parameters

'''
            for param in parameters:
                param_name = param['name']
                param_type = param['type']
                param_desc = param.get('description', '')
                param_required = "Required" if param.get('required', False) else "Optional"

                content += f'''### `{param_name}` ({param_type}, {param_required})

{param_desc}

'''

        content += '''## Usage

### From Command Line (Testing)

```python
from llf.tools_manager import ToolsManager
from tools.''' + tool_name + ''' import execute

# Test the tool directly
result = execute({
    # TODO: Add your test arguments here
})

print(result)
```

### Expected Response

```python
{
    "success": True,
    "data": {
        # TODO: Document expected response structure
    }
}
```

## Development

1. Implement the `execute()` function in `__init__.py`
2. Add any required dependencies to `requirements.txt` and `config.json`
3. Write unit tests in `test_''' + tool_name + '''.py`
4. Run tests: `pytest tests/test_''' + tool_name + '''.py`
5. Update this README with actual usage examples

## Error Handling

The tool returns errors in this format:

```python
{
    "success": False,
    "error": "Error description"
}
```

## TODO

- [ ] Implement core functionality in `execute()` function
- [ ] Add comprehensive error handling
- [ ] Write unit tests
- [ ] Update configuration as needed
- [ ] Document actual usage examples
- [ ] Test with LLM integration
'''

        with open(tool_dir / 'README.md', 'w') as f:
            f.write(content)

    def _write_test_file(self, tool_dir: Path, tool_name: str):
        """Generate and write test file."""
        content = f'''"""
Tests for {tool_name} tool.
"""

import pytest
from tools.{tool_name} import execute

class TestToolDefinition:
    """Test tool definition structure."""

    def test_execute_function_exists(self):
        """Test that execute function exists."""
        assert callable(execute)

class TestExecute:
    """Test execute function."""

    def test_execute_returns_dict(self):
        """Test that execute returns a dictionary."""
        result = execute({{}})
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_with_empty_args(self):
        """Test execute with empty arguments."""
        result = execute({{}})
        # TODO: Update this based on expected behavior
        assert result["success"] in [True, False]

    # TODO: Add more comprehensive tests
    # def test_execute_with_valid_args(self):
    #     """Test execute with valid arguments."""
    #     result = execute({{"arg_name": "value"}})
    #     assert result["success"] is True
    #     assert "data" in result

    # def test_execute_with_invalid_args(self):
    #     """Test execute with invalid arguments."""
    #     result = execute({{"invalid": "arg"}})
    #     assert result["success"] is False
    #     assert "error" in result
'''

        # Create tests directory if it doesn't exist
        tests_dir = self.tools_dir.parent / 'tests'
        tests_dir.mkdir(exist_ok=True)

        with open(tests_dir / f'test_{tool_name}.py', 'w') as f:
            f.write(content)
