# XML Format Tool

Parse XML-style function calls and convert to OpenAI JSON format.

## Overview

Some LLM models (like Qwen3-Coder) output function calls in XML format instead of the standard OpenAI JSON format. This tool provides automatic detection and conversion.

## Example

**Input (XML from model):**
```xml
<function=search_memories>
<parameter=query>user preferences</parameter>
</function>
```

**Output (Converted to OpenAI JSON):**
```json
{
  "tool_calls": [{
    "id": "call_abc123...",
    "type": "function",
    "function": {
      "name": "search_memories",
      "arguments": "{\"query\": \"user preferences\"}"
    }
  }]
}
```

## Configuration

Set in `configs/config.json`:

```json
{
  "llm_endpoint": {
    "tools": {
      "xml_format": "enable"
    }
  }
}
```

Values: `"enable"` or `"disable"`

## CLI Commands

```bash
# Enable (session override)
llf tool xml_format enable

# Disable (session override)
llf tool xml_format disable

# Reset to config file setting
llf tool xml_format auto

# Check status
llf tool list
```

## Usage in Code

```python
from tools.xml_format import (
    parse_xml_function_call,
    convert_xml_response_to_openai,
    is_xml_function_call
)

# Check if response contains XML
if is_xml_function_call(response_text):
    # Convert to OpenAI format
    openai_format = convert_xml_response_to_openai(response_text)
```

## Supported Models

- **Qwen3-Coder** series (e.g., Qwen3-Coder-30B-A3B-Instruct)
- Some Chinese language models
- Custom fine-tuned models trained on XML function calling

## Files

- `parser.py` - Core parsing logic
- `__init__.py` - Public API exports
- `README.md` - This file

## Tests

Run tests with:
```bash
pytest tests/test_xml_tool_parser.py -v
```

## Integration

The XML parser is automatically integrated into the LLM runtime ([llf/llm_runtime.py:533-554](../../llf/llm_runtime.py#L533-L554)). When enabled, it:

1. Checks if the model response contains XML function calls
2. Converts them to OpenAI JSON format
3. Passes them to the tool execution system

No manual intervention required!
