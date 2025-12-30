# Tools Registry Guide: tools_registry.json

This document explains how to configure and manage the tool system using the `tools/tools_registry.json` file.

**Last Updated:** 2025-12-28

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Structure](#configuration-structure)
3. [Parameters Reference](#parameters-reference)
4. [Three-State System](#three-state-system)
5. [Tool Types](#tool-types)
6. [Configuration Examples](#configuration-examples)
7. [CLI Commands](#cli-commands)
8. [Built-in Tools](#built-in-tools)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Related Documentation](#related-documentation)

---

## Overview

The `tools_registry.json` file manages compatibility layers and tool features that extend the LLM's capabilities. It allows you to:

- Register compatibility layers for different LLM formats
- Enable/disable/auto-enable tools based on needs
- Configure tool-specific behavior and activation patterns
- Track tool metadata and usage information
- **Automatically integrate tools when enabled or set to auto**

**Location:** `tools/tools_registry.json`

**Key Concept:** The tools system uses a three-state model (`false`, `'auto'`, `true`) to provide flexible control over when tools are active. Most tools support the `'auto'` mode for automatic activation when needed.

---

## Configuration Structure

A minimal tool entry looks like this:

```json
{
  "version": "1.0",
  "last_updated": "2025-12-28",
  "tools": [
    {
      "name": "xml_format",
      "display_name": "XML Format Parser",
      "description": "Parse XML-style function calls and convert to OpenAI JSON format",
      "type": "compatibility_layer",
      "enabled": "auto",
      "directory": "xml_format",
      "created_date": null,
      "last_modified": "2025-12-28",
      "metadata": {
        "input_format": "XML",
        "output_format": "JSON",
        "use_case": "Model outputs XML instead of JSON tool calls",
        "behavior": "compatibility_layer",
        "activation": "automatic_on_pattern",
        "supported_states": ["false", "auto"]
      }
    }
  ],
  "metadata": {
    "description": "Registry of all available tools for the LLM Framework",
    "schema_version": "1.0"
  }
}
```

---

## Parameters Reference

### Core Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | String | Yes | - | Unique identifier for the tool (lowercase, no spaces) |
| `display_name` | String | Yes | - | Human-readable name shown in CLI and UI |
| `description` | String | Yes | - | Brief description of the tool's functionality |
| `type` | String | Yes | - | Tool type: `compatibility_layer`, `function_calling`, `preprocessor`, `postprocessor` |
| `enabled` | Boolean/String | Yes | `false` | Activation state: `false`, `"auto"`, or `true` |
| `directory` | String | Yes | - | Directory path where tool code is stored (relative to `tools/`) |

### Optional Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `created_date` | String | No | `null` | ISO date when tool was created |
| `last_modified` | String | No | `null` | ISO date when tool was last modified |
| `metadata` | Object | No | `{}` | Additional metadata for the tool |

### Metadata Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `metadata.input_format` | String | - | Format the tool expects as input |
| `metadata.output_format` | String | - | Format the tool produces as output |
| `metadata.use_case` | String | - | When this tool should be used |
| `metadata.behavior` | String | - | How tool integrates: `compatibility_layer`, `llm_invoked`, `preprocessor`, `postprocessor` |
| `metadata.activation` | String | - | When tool activates: `automatic_on_pattern`, `on_demand`, `always` |
| `metadata.supported_states` | Array | `["false", "auto", "true"]` | Array of enabled states this tool supports |
| `metadata.example_input` | String | - | Example of tool input format |
| `metadata.example_output` | String | - | Example of tool output format |

---

## Three-State System

The tools registry uses a unique three-state system for flexible control:

### State 1: Disabled (`false`)

**Behavior:**
- Tool is completely disabled
- Not loaded into memory
- No processing occurs
- Lowest overhead

**When to Use:**
- Tool not needed for your use case
- Want to minimize memory usage
- Testing without the tool
- Tool incompatible with current setup

**Example:**
```json
{
  "name": "xml_format",
  "enabled": false
}
```

---

### State 2: Auto (`"auto"`) - Recommended

**Behavior:**
- Tool is loaded at initialization
- Activates automatically when needed
- Pattern-based or conditional activation
- Balance of convenience and efficiency

**When to Use:**
- Default recommended state for most tools
- Want tool available but not always active
- Tool has smart activation logic
- Production environments

**Example:**
```json
{
  "name": "xml_format",
  "enabled": "auto"
}
```

**How It Works:**
```
1. Tool loads at startup (minimal overhead)
2. Monitors LLM output for activation patterns
3. Activates when pattern detected
4. Processes output when needed
5. Stays dormant otherwise
```

---

### State 3: Force Active (`true`)

**Behavior:**
- Tool is always loaded and active
- Processes every interaction
- No conditional logic
- Highest overhead but guaranteed activation

**When to Use:**
- Debugging tool behavior
- Testing tool functionality
- Tool must always be active
- Overriding auto detection

**Example:**
```json
{
  "name": "xml_format",
  "enabled": true
}
```

**Note:** Most tools don't support `true` state - they only support `false` and `"auto"`. Check `metadata.supported_states` to see what a tool supports.

---

## Tool Types

### Compatibility Layer (`"type": "compatibility_layer"`)

**Purpose:** Convert between different format standards to ensure compatibility

**Characteristics:**
- Bridges format differences
- Typically runs in auto mode
- Activates on pattern detection
- Transparent to user

**Example Use Cases:**
- Convert XML function calls to JSON
- Translate between different tool call formats
- Normalize output formats

**Example:**
```json
{
  "name": "xml_format",
  "type": "compatibility_layer",
  "enabled": "auto"
}
```

---

### Function Calling (`"type": "function_calling"`)

**Purpose:** Enable or enhance LLM function calling capabilities

**Characteristics:**
- Adds function calling to LLMs that lack it
- Enhances existing function calling
- May modify function definitions
- Activates during tool execution

**Example Use Cases:**
- Add function calling to local models
- Improve function call parsing
- Format function responses

---

### Preprocessor (`"type": "preprocessor"`)

**Purpose:** Process or transform data before LLM interaction

**Characteristics:**
- Runs before LLM receives input
- Can modify user messages
- Can inject additional context
- Transparent preprocessing

**Example Use Cases:**
- Format sanitization
- Context injection
- Input validation
- Data transformation

---

### Postprocessor (`"type": "postprocessor"`)

**Purpose:** Process or transform LLM output after generation

**Characteristics:**
- Runs after LLM generates response
- Can modify output format
- Can add additional formatting
- Transparent postprocessing

**Example Use Cases:**
- Format conversion
- Output validation
- Response enhancement
- Error correction

---

## Configuration Examples

### Example 1: XML Format Tool (Recommended)

Standard configuration with auto mode:

```json
{
  "name": "xml_format",
  "display_name": "XML Format Parser",
  "description": "Parse XML-style function calls and convert to OpenAI JSON format",
  "type": "compatibility_layer",
  "enabled": "auto",
  "directory": "xml_format",
  "created_date": null,
  "last_modified": "2025-12-28",
  "metadata": {
    "input_format": "XML",
    "output_format": "JSON",
    "use_case": "Model outputs XML instead of JSON tool calls",
    "example_input": "<function=search_memories><parameter=query>value</parameter></function>",
    "example_output": "{\"name\": \"search_memories\", \"parameters\": {\"query\": \"value\"}}",
    "behavior": "compatibility_layer",
    "activation": "automatic_on_pattern",
    "supported_states": ["false", "auto"]
  }
}
```

**Use Case:** Automatically convert XML function calls from local LLMs to standard JSON format. Recommended for local models that use XML instead of JSON for tool calling.

---

### Example 2: Disabled Tool

Tool disabled when not needed:

```json
{
  "name": "xml_format",
  "display_name": "XML Format Parser",
  "description": "Parse XML-style function calls and convert to OpenAI JSON format",
  "type": "compatibility_layer",
  "enabled": false,
  "directory": "xml_format",
  "metadata": {
    "input_format": "XML",
    "output_format": "JSON",
    "use_case": "Model outputs XML instead of JSON tool calls",
    "supported_states": ["false", "auto"]
  }
}
```

**Use Case:** When using an LLM that natively supports JSON tool calling (like OpenAI, Anthropic), disable XML conversion.

---

## CLI Commands

The framework provides convenient CLI commands for managing tools:

### List All Tools

```bash
# List all registered tools
llf tool list

# List only enabled tools (auto or true)
llf tool list --enabled
```

**Output:**
```
xml_format                     auto
```

---

### Enable a Tool (Auto Mode)

```bash
# Enable tool in auto mode (recommended)
llf tool enable xml_format

# Or explicitly use --auto flag
llf tool enable xml_format --auto
```

**Result:** Sets `"enabled": "auto"` in the registry. Tool loads at next startup and activates when needed.

---

### Enable a Tool (Force Active)

```bash
# Force tool to always be active
llf tool enable xml_format

# Note: Most tools don't support this; check supported_states first
```

**Result:** Sets `"enabled": true` if supported. Otherwise shows error message.

---

### Disable a Tool

```bash
# Disable a tool
llf tool disable xml_format
```

**Result:** Sets `"enabled": false` in the registry. Tool is not loaded on next startup.

---

### Show Tool Info

```bash
# Show detailed information about a tool
llf tool info xml_format
```

**Output:**
```
Feature: xml_format
Status: auto (recommended)
Description: Parse XML-style function calls and convert to OpenAI JSON format
Type: compatibility_layer
Directory: /path/to/project/tools/xml_format
Input Format: XML
Output Format: JSON
Use Case: Model outputs XML instead of JSON tool calls
Activation: automatic_on_pattern
```

---

## Built-in Tools

### XML Format Parser (xml_format)

**Type:** Compatibility Layer
**Purpose:** Convert XML-style function calls to JSON format
**Recommended State:** `"auto"`

**Problem It Solves:**
Many local LLMs (especially smaller models) output function calls in XML format instead of the standard JSON format. This creates incompatibility with the OpenAI-style function calling API.

**XML Format Example:**
```xml
<function=search_memories>
  <parameter=query>Python debugging tips</parameter>
  <parameter=limit>5</parameter>
</function>
```

**Converted JSON Format:**
```json
{
  "name": "search_memories",
  "parameters": {
    "query": "Python debugging tips",
    "limit": 5
  }
}
```

**When It Activates (Auto Mode):**
- Detects XML function call pattern in LLM output
- Automatically parses and converts to JSON
- Passes converted JSON to function executor
- Completely transparent to the user

**Configuration:**
```json
{
  "name": "xml_format",
  "enabled": "auto",
  "metadata": {
    "supported_states": ["false", "auto"]
  }
}
```

**Supported States:** `false`, `"auto"` (does not support `true`)

**When to Use:**
- ✅ Using local LLMs that output XML function calls
- ✅ Models without native JSON function calling support
- ✅ Want automatic format conversion
- ❌ Using OpenAI/Anthropic (already use JSON)
- ❌ Model already outputs valid JSON

**CLI Commands:**
```bash
# Enable auto mode (recommended for local LLMs)
llf tool enable xml_format --auto

# Disable (for cloud APIs with native JSON support)
llf tool disable xml_format

# Check status
llf tool info xml_format
```

---

## Best Practices

### Choosing the Right State

**Use `false` when:**
- Tool not needed for your use case
- Using cloud APIs that don't need compatibility layers
- Want to minimize overhead
- Debugging without tool interference

**Use `"auto"` when (Recommended):**
- Tool provides compatibility for some scenarios
- Want tool available but not always active
- Production environments
- **This is the recommended default for most tools**

**Use `true` when:**
- Debugging tool behavior specifically
- Tool must always be active
- Overriding auto-detection
- **Check if tool supports this state first**

---

### Local LLM Setup

For local LLMs that may use XML function calls:

```bash
# Enable XML format parser in auto mode
llf tool enable xml_format --auto
```

This allows the framework to automatically detect and convert XML function calls to JSON when needed.

---

### Cloud API Setup

For cloud APIs (OpenAI, Anthropic, etc.) that use native JSON:

```bash
# Disable XML format parser (not needed)
llf tool disable xml_format
```

This reduces overhead since cloud APIs already output proper JSON.

---

### Checking Tool Compatibility

Before enabling a tool, check what states it supports:

```bash
llf tool info xml_format
```

Look for `supported_states` in the output. Attempting to use an unsupported state will show an error.

---

### Session vs Persistent Changes

**Persistent Changes (Default):**
```bash
# Changes saved to registry file
llf tool enable xml_format
```

**Session-Only Changes:**
Some tools may support session-only mode (check tool documentation):
```bash
# Would only last for current session (if supported)
# Check tool-specific documentation
```

---

## Troubleshooting

### Problem: Tool not activating in auto mode

**Solution:**
1. Verify tool is set to `"auto"`: `llf tool list`
2. Check that activation pattern is being triggered
3. Look for errors in logs
4. Ensure LLM output matches expected pattern
5. Try force-enabling if supported: `llf tool enable [name]`

---

### Problem: "Tool does not support enabled state: true"

**Solution:**
This tool only supports `false` and `"auto"` states. Use auto mode instead:
```bash
llf tool enable xml_format --auto
```

---

### Problem: Function calls not being converted

**Solution:**
1. Verify xml_format tool is enabled: `llf tool list --enabled`
2. Check LLM is actually outputting XML format
3. Look for parsing errors in logs
4. Verify XML format matches expected pattern
5. Try force-enabling the tool

---

### Problem: Tool causing errors or unexpected behavior

**Solution:**
1. Check tool logs for specific error messages
2. Verify tool directory exists: `tools/[tool_name]/`
3. Ensure all tool dependencies are installed
4. Try disabling and re-enabling the tool
5. Check for tool version compatibility

---

### Problem: Can't find a tool

**Solution:**
1. List all tools: `llf tool list`
2. Check registry file: `tools/tools_registry.json`
3. Verify tool is registered in the registry
4. Check tool name spelling

---

## Related Documentation

- [Main Configuration](config_json.md) - LLM endpoint and server configuration
- [Prompt Configuration](config_prompt_json.md) - System prompts and message formatting
- [Data Store Registry](data_store_registry_json.md) - RAG vector store configuration
- [Memory Registry](memory_registry_json.md) - Long-term memory configuration
- [Modules Registry](modules_registry_json.md) - Pluggable module configuration

---

## Additional Resources

### Tool Directory Structure

Each tool directory typically contains:
```
tools/
├── tools_registry.json           # This registry file
└── xml_format/                   # Example tool
    ├── __init__.py               # Tool entry point
    ├── xml_parser.py             # Main implementation
    ├── patterns.py               # Pattern detection
    └── README.md                 # Tool documentation
```

### Understanding supported_states

The `metadata.supported_states` array indicates which activation states a tool supports:

**`["false", "auto"]`** - Most common
- Can be disabled or auto-enabled
- Does not support force-active mode
- Best for compatibility layers

**`["false", "auto", "true"]`** - Full support
- Supports all three states
- Can be disabled, auto, or force-active
- Rare; most tools don't need force-active

**`["false", "true"]`** - Binary only
- Can only be disabled or force-active
- No auto mode
- Uncommon; typically preprocessors/postprocessors

### Creating Custom Tools

To create a custom tool:

1. Create directory in `tools/[your_tool_name]/`
2. Add `__init__.py` with tool class
3. Implement required methods
4. Register in `tools_registry.json`
5. Set `supported_states` in metadata
6. Enable via CLI

**Example tool class structure:**
```python
class MyTool:
    def __init__(self):
        self.name = "my_tool"

    def should_activate(self, context):
        """Return True if tool should activate (for auto mode)"""
        return self._detect_pattern(context)

    def process(self, input_data):
        """Process the data"""
        return processed_data
```

---

For additional help, refer to the main [README.md](../README.md) or open an issue on GitHub.
