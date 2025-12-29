# XML Function Call Format Support

## Overview

Some LLM models output function calls in XML format instead of the standard OpenAI JSON format. This framework now supports both formats automatically!

## The Problem

**Your model outputs this (XML format):**
```xml
<function=search_memories>
<parameter=query>user name</parameter>
```

**But your framework expects this (OpenAI JSON format):**
```json
{
  "tool_calls": [{
    "function": {
      "name": "search_memories",
      "arguments": "{\"query\": \"user name\"}"
    }
  }]
}
```

## The Solution

Configure XML format parsing in your config file or via CLI:

### Option 1: Config File (Recommended)

Edit `configs/config.json` and set the xml_format tool:

```json
{
  "llm_endpoint": {
    "model_name": "Qwen/Qwen3-Coder-30B-A3B-Instruct-GGUF",
    "tools": {
      "xml_format": "enable"
    }
  }
}
```

Valid values: `"enable"` or `"disable"`

### Option 2: CLI Override (Temporary)

```bash
llf tool xml_format enable   # Enable for this session
llf tool xml_format disable  # Disable for this session
llf tool xml_format auto     # Reset to config file setting
```

Now your framework will automatically:
1. Detect XML-style function calls in model responses
2. Parse the XML format
3. Convert it to OpenAI JSON format
4. Execute the tools normally

## Quick Start

### 1. Check Current Status
```bash
llf tool list
```

Output:
```
Tool Features

xml_format                     disabled
  Parse XML-style function calls and convert to OpenAI JSON format
```

### 2. Enable XML Parsing
```bash
llf tool xml_format enable
```

Output:
```
✓ Feature 'xml_format' enabled

This feature will parse XML-style function calls like:
  <function=search_memories><parameter=query>value</parameter>
and convert them to OpenAI JSON format.
```

### 3. Test With Your Model
```bash
# Enable memory
llf memory enable main_memory

# Start chat (XML parsing is now active)
llf chat
```

Ask the LLM:
```
> Remember that my name is Matt
> What is my name?
```

If your model outputs XML function calls, they'll be automatically converted and executed!

### 4. Disable When Not Needed
```bash
llf tool xml_format disable
```

## Supported XML Formats

### Single Parameter
```xml
<function=search_memories>
<parameter=query>Matt</parameter>
```

### Multiple Parameters
```xml
<function=add_memory>
<parameter=content>User's name is Matt</parameter>
<parameter=memory_type>fact</parameter>
<parameter=importance>0.9</parameter>
```

### With Closing Tags
```xml
<function=search_memories>
<parameter=query>preferences</parameter>
</function>
```

## Which Models Need This?

### Models That Output XML Format
- **Qwen3-Coder** series (e.g., Qwen3-Coder-30B-A3B-Instruct)
- Some Chinese language models
- Custom fine-tuned models trained on XML function calling

### Models That Use JSON Format (Don't Need This)
- **GPT-4, GPT-3.5** (OpenAI)
- **Claude 3+** (Anthropic)
- **Llama-3.1+** (Meta)
- **Qwen2.5-Coder** (newer than Qwen3)
- **Hermes-2-Pro** series
- **Mistral Large**

## CLI Commands

```bash
# List all tool features
llf tool list

# Show only enabled features
llf tool list --enabled

# Enable XML parsing (session override)
llf tool xml_format enable

# Disable XML parsing (session override)
llf tool xml_format disable

# Reset to config file setting
llf tool xml_format auto

# Show feature details
llf tool info xml_format
```

## How It Works

1. **Configuration**: Framework reads xml_format setting from `configs/config.json`
2. **Detection**: After the LLM responds, the system checks if XML function calls are present
3. **Parsing**: XML is parsed using regex to extract function name and parameters
4. **Conversion**: Creates OpenAI-compatible tool call structure
5. **Execution**: Tools execute normally using the converted format

## Configuration

### Primary Configuration (Recommended)

The xml_format setting is stored in `configs/config.json`:

```json
{
  "llm_endpoint": {
    "model_name": "Qwen/Qwen3-Coder-30B-A3B-Instruct-GGUF",
    "tools": {
      "xml_format": "enable"
    }
  }
}
```

This is model-specific configuration - different models may need different settings.

### Legacy Configuration (Fallback)

For backwards compatibility, the framework also checks `tools/tools_config.json`:

```json
{
  "version": "1.0",
  "features": {
    "xml_format": {
      "enabled": false,
      "description": "Parse XML-style function calls and convert to OpenAI JSON format"
    }
  }
}
```

## Testing

The framework includes comprehensive tests for XML parsing:

```bash
# Run XML parser tests
source llf_venv/bin/activate
python -m pytest tests/test_xml_tool_parser.py -v
```

## Troubleshooting

### XML Detection Not Working

**Symptom**: Model outputs XML but it's not being parsed

**Check**:
1. Is xml_format enabled? `llf tool list`
2. Are tools enabled? `llf memory list --enabled`
3. Check logs for "XML Parser: Detected XML-style function calls"

**Solution**:
```bash
llf tool xml_format enable
llf memory enable main_memory
```

### Still Getting Plain XML in Output

**Cause**: The model might be outputting XML but not in the expected format

**Solution**: Check the exact format your model uses and adjust if needed. The parser supports:
- `<function=name>`
- `<parameter=key>value</parameter>`

## Performance Impact

Minimal - XML parsing only occurs when:
1. xml_format feature is enabled
2. Tools are available (memory enabled)
3. LLM response contains XML function tags
4. No native JSON tool calls are present

## Future Extensions

This feature can be extended to support:
- Custom XML schemas
- Other function calling formats
- Model-specific parsing rules

Add new parsers to `llf/xml_tool_parser.py` as needed!

## Summary

The XML format feature makes your framework **model-agnostic**:
- ✅ Works with JSON-based models (default)
- ✅ Works with XML-based models (with xml_format enabled)
- ✅ Automatic detection and conversion
- ✅ Zero performance impact when disabled
- ✅ Easy to enable/disable per session

Enable it once, and your framework adapts to whatever format your model outputs!
