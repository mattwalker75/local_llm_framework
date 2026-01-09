# LLM-Invokable Tool Template

This document provides a template and guidelines for creating new LLM-invokable tools.

## Directory Structure

Each tool should be in its own directory under `tools/`:

```
tools/
├── tool_name/
│   ├── __init__.py       # Main entry point, exports TOOL_DEFINITION and execute()
│   ├── config.json       # Tool configuration for import/export
│   ├── tool.py           # Core implementation (optional, can be in __init__.py)
│   └── README.md         # Tool documentation
```

## Required Components

### 1. TOOL_DEFINITION

Every tool module must export a `TOOL_DEFINITION` constant that follows the OpenAI function calling schema:

```python
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "Clear description of what this tool does and when the LLM should use it",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Description of parameter 1"
                },
                "param2": {
                    "type": "integer",
                    "description": "Description of parameter 2",
                    "enum": [1, 2, 3]  # Optional: restrict to specific values
                }
            },
            "required": ["param1"]  # List required parameters
        }
    }
}
```

### 2. execute() Function

Every tool module must export an `execute()` function:

```python
def execute(arguments: dict) -> dict:
    """
    Execute the tool with the given arguments.

    Args:
        arguments: Dictionary of arguments from the LLM's function call

    Returns:
        Dictionary with execution results. Should include:
        - success: bool indicating if execution succeeded
        - result: any relevant return data
        - error: error message if success is False
    """
    try:
        # Your tool implementation here
        param1 = arguments.get('param1')
        param2 = arguments.get('param2', default_value)

        # Perform the tool's operation
        result = do_something(param1, param2)

        return {
            "success": True,
            "result": result
        }

    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

## Tool Configuration (config.json)

Each tool must include a `config.json` file in its directory. This file is used for importing/exporting tools and contains the tool's registry configuration:

### `tools/tool_name/config.json`

```json
{
  "name": "tool_name",
  "display_name": "Human Readable Name",
  "description": "Brief description of the tool",
  "type": "llm_invokable",
  "enabled": false,
  "directory": "tool_name",
  "created_date": "2026-01-06",
  "last_modified": "2026-01-06",
  "metadata": {
    "category": "internet|file_access|command_execution|data_processing",
    "requires_approval": false,
    "use_case": "Detailed explanation of when to use this tool",
    "dependencies": ["library1", "library2"],
    "supported_states": ["false", "true"]
  }
}
```

### Field Descriptions

- **name**: Unique identifier for the tool (used in CLI commands)
- **display_name**: Human-readable name shown in listings
- **description**: Brief description of what the tool does
- **type**: Tool category - `"llm_invokable"`, `"postprocessor"`, or `"preprocessor"`
- **enabled**: Default state - `false`, `true`, or `"auto"`
- **directory**: Directory name under `tools/` (usually same as tool name)
- **created_date**: ISO date when tool was created
- **last_modified**: ISO date of last modification
- **metadata**: Additional configuration
  - **category**: Tool category for organization
  - **requires_approval**: Whether tool requires user approval before execution
  - **use_case**: Detailed explanation of when LLM should use this tool
  - **dependencies**: List of required Python packages
  - **supported_states**: Array of valid enabled states for this tool
  - **whitelist**: (For file_access/command_exec tools) Allowed patterns
  - **permissions**: Additional permission constraints

### Import/Export

Tools can be imported and exported using the CLI:

```bash
# Import a tool (adds to registry from config.json)
llf tool import tool_name

# Export a tool (removes from registry, keeps files)
llf tool export tool_name

# List available tools to import
llf tool list --available
```

The `import` command reads the tool's `config.json` and adds it to `tools_registry.json`. The `export` command removes the tool from the registry but preserves the tool's directory and files, allowing for later re-import.

## Example: Simple Calculator Tool

### `tools/calculator/__init__.py`

```python
"""
Simple Calculator Tool - Perform mathematical operations.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Tool definition for LLM
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Perform basic mathematical operations (add, subtract, multiply, divide)",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The mathematical operation to perform"
                },
                "a": {
                    "type": "number",
                    "description": "First number"
                },
                "b": {
                    "type": "number",
                    "description": "Second number"
                }
            },
            "required": ["operation", "a", "b"]
        }
    }
}


def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute calculator operation.

    Args:
        arguments: Dict with 'operation', 'a', 'b'

    Returns:
        Dict with success status and result
    """
    try:
        operation = arguments.get('operation')
        a = arguments.get('a')
        b = arguments.get('b')

        # Validate inputs
        if not all([operation, a is not None, b is not None]):
            return {
                "success": False,
                "error": "Missing required parameters"
            }

        # Perform operation
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return {
                    "success": False,
                    "error": "Division by zero"
                }
            result = a / b
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}"
            }

        logger.info(f"Calculator: {a} {operation} {b} = {result}")

        return {
            "success": True,
            "result": result,
            "operation": operation,
            "operands": [a, b]
        }

    except Exception as e:
        logger.error(f"Calculator execution failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


__all__ = ['TOOL_DEFINITION', 'execute']
```

## Best Practices

1. **Clear Descriptions**: Write clear, detailed descriptions for both the tool and its parameters. The LLM uses these to decide when to call your tool.

2. **Error Handling**: Always wrap your implementation in try/except and return structured error information.

3. **Return Format**: Always return a dict with at least:
   - `success`: boolean
   - `result`: the actual result (if successful)
   - `error`: error message (if failed)

4. **Logging**: Use the logger to track tool execution for debugging.

5. **Input Validation**: Always validate inputs before processing.

6. **Type Hints**: Use type hints for better code clarity.

7. **Documentation**: Include docstrings for functions and a README.md for the tool.

8. **Security**: For tools that interact with files/commands/network:
   - Validate and sanitize all inputs
   - Check against whitelists/blacklists
   - Respect the `require_approval` global config setting
   - Never trust LLM-provided paths/commands without validation

## Testing Your Tool

1. Add tool to registry with `enabled: true`
2. Test manually:
   ```bash
   bin/llf tool list
   bin/llf tool info tool_name
   ```
3. Write unit tests in `tests/test_tool_name.py`
4. Test with LLM conversation:
   ```bash
   bin/llf chat
   > Use the calculator to add 5 and 3
   ```

## Advanced: Tools with Dependencies

If your tool requires external libraries:

1. Add dependencies to `pyproject.toml` under `[project.optional-dependencies]`:
   ```toml
   [project.optional-dependencies]
   internet_tools = ["requests>=2.31.0", "beautifulsoup4>=4.12.0"]
   ```

2. Import with try/except and provide helpful error messages:
   ```python
   try:
       import requests
   except ImportError:
       raise ImportError(
           "requests library required for internet tools. "
           "Install with: pip install 'llf[internet_tools]'"
       )
   ```

3. Document installation requirements in tool's README.md

## Categories

Use these standard categories in metadata:

- `internet`: Web search, scraping, API calls
- `file_access`: Reading/writing files
- `command_execution`: Running system commands
- `data_processing`: Parsing, transforming data
- `computation`: Mathematical operations
- `integration`: Third-party service integrations

## Security Considerations

For sensitive tools (file_access, command_execution):

1. Set `"requires_approval": true` in metadata
2. Implement validation against global `sensitive_operations` list
3. Use whitelisting, not blacklisting
4. Sanitize all inputs
5. Log all operations for audit trail
6. Never expose system paths or credentials in error messages
