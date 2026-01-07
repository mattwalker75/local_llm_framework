# Tool Logic Flow

This document explains the complete logic flow when a tool is enabled in the Local LLM Framework (LLF), including detailed examples and internal processing.

## Table of Contents

1. [What is a Tool?](#what-is-a-tool)
2. [Function Calling Overview](#function-calling-overview)
3. [High-Level Flow](#high-level-flow)
4. [Detailed Logic Flow](#detailed-logic-flow)
5. [Examples](#examples)
6. [Internal Processing](#internal-processing)

## What is a Tool?

A **tool** in LLF is a function that the LLM can invoke to perform specific actions or retrieve information. Tools enable the LLM to:
- Execute commands
- Access files
- Search the internet
- Query databases
- Call external APIs
- Perform calculations

**Key Characteristics**:
- Defined with OpenAI-compatible schema
- Invoked by the LLM (not directly by user)
- Security-controlled (whitelists, approvals)
- Return structured results

**Tool vs Module**:
| Feature | Tool | Module |
|---------|------|--------|
| **Invocation** | LLM decides when to call | Automatic on every message |
| **Purpose** | Specific actions | Transform input/output |
| **Control** | LLM-controlled | Pipeline-controlled |
| **Examples** | Search web, run command | Translate, format |

## Function Calling Overview

The LLM uses **function calling** (tool calling) to determine when and how to use tools:

```
User: "What's the weather in Paris?"
    ↓
LLM thinks: "I need to search for weather information"
    ↓
LLM calls: search_internet(query="weather Paris")
    ↓
Tool executes and returns: "Weather in Paris: 15°C, cloudy"
    ↓
LLM responds: "The weather in Paris is 15°C and cloudy."
```

The LLM receives tool definitions and decides autonomously which tools to call and with what parameters.

## High-Level Flow

```
┌──────────────┐
│ User Message │
└──────┬───────┘
       │
       ↓
┌────────────────────────────────────────────────────────┐
│ 1. Tool Registration                                   │
│    - Load enabled tools from registry                 │
│    - Parse tool definitions                            │
│    - Validate configurations                           │
│    - Send tool schemas to LLM                          │
└────────────────┬───────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────┐
│ 2. LLM Analysis                                        │
│    - Analyze user request                             │
│    - Determine if tools are needed                    │
│    - Select appropriate tool(s)                       │
│    - Generate tool call parameters                    │
└────────────────┬───────────────────────────────────────┘
                 │
                 ↓
        ┌────────┴────────┐
        │                 │
        ↓                 ↓
┌──────────────┐  ┌──────────────────┐
│ No Tool Call │  │ Tool Call(s)     │
│ Regular LLM  │  │ Generated        │
│ Response     │  │                  │
└──────┬───────┘  └────────┬─────────┘
       │                   │
       │                   ↓
       │          ┌────────────────────────────┐
       │          │ 3. Tool Execution          │
       │          │    - Validate parameters   │
       │          │    - Check security        │
       │          │    - Request approval      │
       │          │    - Execute tool          │
       │          │    - Return results        │
       │          └────────┬───────────────────┘
       │                   │
       │                   ↓
       │          ┌────────────────────────────┐
       │          │ 4. LLM Processing Results  │
       │          │    - Receive tool results  │
       │          │    - Analyze data          │
       │          │    - Generate response     │
       │          └────────┬───────────────────┘
       │                   │
       └───────────┬───────┘
                   │
                   ↓
         ┌─────────────────────┐
         │ 5. Response to User │
         └─────────────────────┘
```

## Detailed Logic Flow

### Phase 1: Tool Registration and Initialization

```
┌─────────────────────────────────────────────────────────────┐
│ LLMClient.__init__()                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │ ToolsManager()         │
        │ - Load registry        │
        │ - Get enabled tools    │
        └────────┬───────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ For each enabled tool:         │
        │                                │
        │ 1. Read config.json            │
        │ {                              │
        │   "name": "file_access",       │
        │   "type": "llm_invokable",     │
        │   "directory": "file_access",  │
        │   "metadata": {                │
        │     "mode": "ro",              │
        │     "whitelist": [...]         │
        │   }                            │
        │ }                              │
        │                                │
        │ 2. Load tool_definition.json   │
        │ {                              │
        │   "type": "function",          │
        │   "function": {                │
        │     "name": "file_access",     │
        │     "description": "Read...",  │
        │     "parameters": {            │
        │       "type": "object",        │
        │       "properties": {...}      │
        │     }                          │
        │   }                            │
        │ }                              │
        │                                │
        │ 3. Import execute.py module    │
        │ 4. Validate tool interface     │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Build Tools Schema for LLM     │
        │                                │
        │ tools = [                      │
        │   {                            │
        │     "type": "function",        │
        │     "function": {              │
        │       "name": "file_access",   │
        │       "description": "...",    │
        │       "parameters": {...}      │
        │     }                          │
        │   },                           │
        │   {                            │
        │     "type": "function",        │
        │     "function": {              │
        │       "name": "search_web",    │
        │       ...                      │
        │     }                          │
        │   }                            │
        │ ]                              │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Send Tools to LLM              │
        │                                │
        │ llm.configure(                 │
        │   tools=tools,                 │
        │   tool_choice="auto"           │
        │ )                              │
        └────────────────────────────────┘
```

### Phase 2: LLM Decision Making

```
┌─────────────────────────────────────────────────────────────┐
│ User: "Show me the contents of config.json"                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────┐
        │ LLM Receives:                  │
        │                                │
        │ 1. User message                │
        │ 2. Conversation history        │
        │ 3. Available tools:            │
        │    - file_access               │
        │    - command_exec              │
        │    - search_internet           │
        │    - xml_format                │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ LLM Analysis                   │
        │                                │
        │ Question: "Show contents of    │
        │           config.json"         │
        │                                │
        │ Intent: Read file              │
        │ File: config.json              │
        │                                │
        │ Available tools:               │
        │ ✓ file_access - CAN read files │
        │ ✗ command_exec - Not needed    │
        │ ✗ search_internet - Not needed │
        │                                │
        │ Decision: Call file_access     │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Generate Tool Call             │
        │                                │
        │ {                              │
        │   "id": "call_abc123",         │
        │   "type": "function",          │
        │   "function": {                │
        │     "name": "file_access",     │
        │     "arguments": {             │
        │       "operation": "read",     │
        │       "path": "config.json"    │
        │     }                          │
        │   }                            │
        │ }                              │
        └────────────────────────────────┘
```

### Phase 3: Tool Execution

```
┌─────────────────────────────────────────────────────────────┐
│ Tool Call Received                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────┐
        │ Step 1: Validate Tool Call     │
        │                                │
        │ ✓ Tool exists: file_access     │
        │ ✓ Tool enabled: true           │
        │ ✓ Parameters present           │
        │ ✓ Parameters valid JSON        │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Step 2: Security Checks        │
        │                                │
        │ Check 1: Whitelist             │
        │ - Path: config.json            │
        │ - Whitelist: ["**/*.json"]     │
        │ - Result: ✓ MATCH              │
        │                                │
        │ Check 2: Dangerous Path        │
        │ - Path: config.json            │
        │ - Dangerous: [/etc/, ~/.ssh/]  │
        │ - Result: ✓ SAFE               │
        │                                │
        │ Check 3: Mode                  │
        │ - Operation: read              │
        │ - Mode: ro (read-only)         │
        │ - Result: ✓ ALLOWED            │
        │                                │
        │ Check 4: Approval Required     │
        │ - requires_approval: false     │
        │ - Result: ✓ NO APPROVAL NEEDED │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Step 3: Execute Tool           │
        │                                │
        │ import tools.file_access       │
        │                                │
        │ result = execute({             │
        │   "operation": "read",         │
        │   "path": "config.json"        │
        │ })                             │
        │                                │
        │ # Tool reads file and returns  │
        │ {                              │
        │   "success": true,             │
        │   "content": "{...json...}",   │
        │   "size": 1024,                │
        │   "encoding": "utf-8"          │
        │ }                              │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Step 4: Format Result          │
        │                                │
        │ {                              │
        │   "tool_call_id": "call_abc123"│
        │   "role": "tool",              │
        │   "name": "file_access",       │
        │   "content": "{               │
        │     'success': true,           │
        │     'content': '{...}',        │
        │     'size': 1024               │
        │   }"                           │
        │ }                              │
        └────────────────────────────────┘
```

### Phase 4: LLM Processing Tool Results

```
┌─────────────────────────────────────────────────────────────┐
│ LLM Receives Tool Result                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────┐
        │ Conversation History:          │
        │                                │
        │ [User]                         │
        │ "Show me the contents of       │
        │  config.json"                  │
        │                                │
        │ [Assistant - Tool Call]        │
        │ Called: file_access(           │
        │   operation="read",            │
        │   path="config.json"           │
        │ )                              │
        │                                │
        │ [Tool Result]                  │
        │ {                              │
        │   success: true,               │
        │   content: "{               │
        │     'database': 'postgres',    │
        │     'port': 5432               │
        │   }",                          │
        │   size: 1024                   │
        │ }                              │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ LLM Analysis                   │
        │                                │
        │ "The tool successfully read    │
        │ config.json. The file contains │
        │ database configuration. I      │
        │ should present this clearly    │
        │ to the user."                  │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Generate Response              │
        │                                │
        │ "Here are the contents of      │
        │ config.json:                   │
        │                                │
        │ ```json                        │
        │ {                              │
        │   'database': 'postgres',      │
        │   'port': 5432                 │
        │ }                              │
        │ ```                            │
        │                                │
        │ The file contains database     │
        │ configuration with PostgreSQL  │
        │ on port 5432."                 │
        └────────────────────────────────┘
```

### Phase 5: Multi-Tool Calls

```
User: "Search for Python tutorials and save the results to tutorials.txt"
    ↓
┌────────────────────────────────────┐
│ LLM Analysis                       │
│                                    │
│ Tasks:                             │
│ 1. Search for Python tutorials     │
│ 2. Save results to file            │
│                                    │
│ Tools needed:                      │
│ 1. search_internet                 │
│ 2. file_access                     │
│                                    │
│ Strategy: Sequential execution     │
└────────┬───────────────────────────┘
         │
         ↓
┌────────────────────────────────────┐
│ Tool Call 1: search_internet       │
│ {                                  │
│   "function": "search_internet",   │
│   "arguments": {                   │
│     "query": "Python tutorials"    │
│   }                                │
│ }                                  │
└────────┬───────────────────────────┘
         │
         ↓
┌────────────────────────────────────┐
│ Tool Result 1                      │
│ [                                  │
│   "Tutorial 1: Learn Python...",   │
│   "Tutorial 2: Python Basics...",  │
│   ...                              │
│ ]                                  │
└────────┬───────────────────────────┘
         │
         ↓
┌────────────────────────────────────┐
│ LLM: "Now I have search results.   │
│       Need to save to file."       │
│                                    │
│ Tool Call 2: file_access           │
│ {                                  │
│   "function": "file_access",       │
│   "arguments": {                   │
│     "operation": "write",          │
│     "path": "tutorials.txt",       │
│     "content": "[results...]"      │
│   }                                │
│ }                                  │
└────────┬───────────────────────────┘
         │
         ↓
┌────────────────────────────────────┐
│ Tool Result 2                      │
│ {                                  │
│   "success": true,                 │
│   "bytes_written": 2048            │
│ }                                  │
└────────┬───────────────────────────┘
         │
         ↓
┌────────────────────────────────────┐
│ LLM Response                       │
│ "I've searched for Python tutorials│
│ and saved the results to           │
│ tutorials.txt. Found 5 great       │
│ tutorials covering basics to       │
│ advanced topics."                  │
└────────────────────────────────────┘
```

## Examples

### Example 1: Simple File Read

**User Request**:
```
User: "What's in my README.md file?"
```

**Tool Flow**:

```python
# 1. LLM generates tool call
tool_call = {
    "id": "call_001",
    "function": {
        "name": "file_access",
        "arguments": {
            "operation": "read",
            "path": "README.md"
        }
    }
}

# 2. Tool execution
from tools.file_access import execute

result = execute({
    "operation": "read",
    "path": "README.md"
})
# Returns:
# {
#   "success": true,
#   "content": "# My Project\n\nThis is a sample project...",
#   "size": 512
# }

# 3. LLM receives result and responds
response = """
Your README.md contains:

# My Project

This is a sample project...

The file is 512 bytes.
"""
```

### Example 2: Command Execution with Security

**User Request**:
```
User: "List all Python files in the current directory"
```

**Tool Flow**:

```python
# 1. LLM generates tool call
tool_call = {
    "function": {
        "name": "command_exec",
        "arguments": {
            "command": "ls",
            "arguments": ["-l", "*.py"]
        }
    }
}

# 2. Security checks
tool_info = manager.get_tool("command_exec")

# Check whitelist
whitelist = tool_info["metadata"]["whitelist"]
# ["ls", "pwd", "echo", "cat"]

command = "ls"
if command not in whitelist:
    return {"success": false, "error": "Command not whitelisted"}

# Check if dangerous
dangerous_commands = ["rm", "dd", "mkfs", ...]
if command in dangerous_commands:
    if not requires_approval:
        return {"success": false, "error": "Requires approval"}

# 3. Execute command
import subprocess

result = subprocess.run(
    ["ls", "-l", "*.py"],
    capture_output=True,
    text=True,
    timeout=60
)

# 4. Return result
return {
    "success": True,
    "stdout": result.stdout,
    "stderr": result.stderr,
    "return_code": result.returncode
}
```

### Example 3: Internet Search

**User Request**:
```
User: "What's the latest news about AI?"
```

**Tool Flow**:

```python
# 1. LLM generates tool call
tool_call = {
    "function": {
        "name": "internet_duckduckgo",
        "arguments": {
            "query": "latest AI news 2025",
            "max_results": 5
        }
    }
}

# 2. Execute search
from tools.internet_duckduckgo import execute

result = execute({
    "query": "latest AI news 2025",
    "max_results": 5
})

# Returns:
# {
#   "success": true,
#   "results": [
#     {
#       "title": "New AI Model Released...",
#       "snippet": "A groundbreaking AI model...",
#       "url": "https://example.com/news1"
#     },
#     # ... more results
#   ],
#   "count": 5
# }

# 3. LLM synthesizes response
response = """
Here's the latest news about AI:

1. **New AI Model Released**
   A groundbreaking AI model was announced...
   [Read more](https://example.com/news1)

2. **AI in Healthcare**
   ...

[Based on 5 recent search results]
"""
```

### Example 4: Complex Multi-Step Task

**User Request**:
```
User: "Search for FastAPI tutorials, summarize the top 3, and save the summary to fastapi_summary.md"
```

**Complete Flow**:

```python
# Step 1: Search
tool_call_1 = {
    "function": {
        "name": "internet_duckduckgo",
        "arguments": {
            "query": "FastAPI tutorials",
            "max_results": 3
        }
    }
}

result_1 = execute_tool(tool_call_1)
# Returns: [tutorial1, tutorial2, tutorial3]

# LLM receives results and analyzes
# "I have 3 tutorials. Now I need to create a summary."

# Step 2: LLM generates summary internally
summary = """
# FastAPI Tutorials Summary

## 1. Getting Started with FastAPI
- Introduction to FastAPI framework
- Setting up your first API
- ...

## 2. Advanced FastAPI Features
...

## 3. FastAPI Best Practices
...
"""

# Step 3: Save to file
tool_call_2 = {
    "function": {
        "name": "file_access",
        "arguments": {
            "operation": "write",
            "path": "fastapi_summary.md",
            "content": summary
        }
    }
}

result_2 = execute_tool(tool_call_2)
# Returns: {"success": true, "bytes_written": 1024}

# Final response
response = """
I've completed your request:

1. ✓ Searched for FastAPI tutorials
2. ✓ Found and analyzed top 3 tutorials
3. ✓ Created summary and saved to fastapi_summary.md

The summary (1024 bytes) covers:
- Getting Started with FastAPI
- Advanced Features
- Best Practices

You can now read fastapi_summary.md for the full summary.
"""
```

## Internal Processing

### Tool Definition Schema

Each tool must provide an OpenAI-compatible definition:

```json
{
  "type": "function",
  "function": {
    "name": "file_access",
    "description": "Read, write, list, or delete files. Supports text and binary files with security controls.",
    "parameters": {
      "type": "object",
      "properties": {
        "operation": {
          "type": "string",
          "enum": ["read", "write", "list", "delete"],
          "description": "The file operation to perform"
        },
        "path": {
          "type": "string",
          "description": "Path to the file or directory"
        },
        "content": {
          "type": "string",
          "description": "Content to write (for write operation)"
        }
      },
      "required": ["operation", "path"]
    }
  }
}
```

### Tool Execution Pipeline

```python
def execute_tool_call(tool_call: dict, manager: ToolsManager) -> dict:
    """Execute a tool call with full security checks."""

    # 1. Extract tool information
    tool_name = tool_call["function"]["name"]
    arguments = json.loads(tool_call["function"]["arguments"])

    # 2. Get tool info from registry
    tool_info = manager.get_tool(tool_name)
    if not tool_info:
        return {"success": False, "error": f"Tool {tool_name} not found"}

    # 3. Check if enabled
    if not tool_info.get("enabled", False):
        return {"success": False, "error": f"Tool {tool_name} is disabled"}

    # 4. Security checks
    security_result = perform_security_checks(
        tool_name,
        arguments,
        tool_info
    )
    if not security_result["passed"]:
        return {
            "success": False,
            "error": security_result["error"]
        }

    # 5. Check if approval required
    if tool_info["metadata"].get("requires_approval", False):
        approved = request_user_approval(
            tool_name,
            arguments
        )
        if not approved:
            return {
                "success": False,
                "error": "User denied approval"
            }

    # 6. Load and execute tool
    try:
        tool_module = manager.load_tool_module(tool_name)
        result = tool_module.execute(arguments)
        return result
    except Exception as e:
        logger.exception(f"Tool execution error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def perform_security_checks(
    tool_name: str,
    arguments: dict,
    tool_info: dict
) -> dict:
    """Perform security checks before tool execution."""

    # Whitelist check (if applicable)
    if "path" in arguments or "command" in arguments:
        target = arguments.get("path") or arguments.get("command")

        if not check_whitelist(tool_name, target, tool_info):
            return {
                "passed": False,
                "error": f"Not whitelisted: {target}"
            }

    # Dangerous operation check
    if is_dangerous_operation(tool_name, arguments, tool_info):
        if not tool_info["metadata"].get("requires_approval"):
            return {
                "passed": False,
                "error": "Dangerous operation requires approval"
            }

    # Mode check (for file_access)
    if tool_name == "file_access":
        mode = tool_info["metadata"].get("mode", "ro")
        operation = arguments.get("operation")

        if mode == "ro" and operation in ["write", "delete"]:
            return {
                "passed": False,
                "error": f"Operation {operation} not allowed in read-only mode"
            }

    return {"passed": True}
```

### Tool Result Handling

```python
def handle_tool_result(
    tool_call_id: str,
    tool_name: str,
    result: dict
) -> dict:
    """Format tool result for LLM."""

    # Standard format for LLM
    return {
        "tool_call_id": tool_call_id,
        "role": "tool",
        "name": tool_name,
        "content": json.dumps(result)
    }


# Example in conversation
conversation = [
    {
        "role": "user",
        "content": "Read config.json"
    },
    {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_abc",
                "type": "function",
                "function": {
                    "name": "file_access",
                    "arguments": '{"operation":"read","path":"config.json"}'
                }
            }
        ]
    },
    {
        "tool_call_id": "call_abc",
        "role": "tool",
        "name": "file_access",
        "content": '{"success":true,"content":"...","size":1024}'
    },
    {
        "role": "assistant",
        "content": "Here are the contents of config.json: ..."
    }
]
```

### Error Handling

```python
# Tool execution with comprehensive error handling

try:
    result = execute_tool(tool_call)

except ToolNotFoundError as e:
    result = {
        "success": False,
        "error": f"Tool not found: {e.tool_name}",
        "error_type": "ToolNotFoundError"
    }

except ToolDisabledError as e:
    result = {
        "success": False,
        "error": f"Tool is disabled: {e.tool_name}",
        "error_type": "ToolDisabledError"
    }

except SecurityViolationError as e:
    result = {
        "success": False,
        "error": f"Security violation: {e.message}",
        "error_type": "SecurityViolationError",
        "details": e.details
    }

except ApprovalDeniedError as e:
    result = {
        "success": False,
        "error": "User denied approval",
        "error_type": "ApprovalDeniedError"
    }

except TimeoutError as e:
    result = {
        "success": False,
        "error": "Tool execution timed out",
        "error_type": "TimeoutError",
        "timeout": e.timeout
    }

except Exception as e:
    logger.exception("Unexpected tool error")
    result = {
        "success": False,
        "error": f"Unexpected error: {str(e)}",
        "error_type": type(e).__name__
    }

# Return error to LLM
return format_tool_result(tool_call_id, tool_name, result)
```

## Summary

When a tool is enabled:

1. **Registration**: Tool definition sent to LLM at initialization
2. **Decision**: LLM autonomously decides when to use the tool
3. **Invocation**: LLM generates function call with parameters
4. **Security**: Multiple security layers validate the call
5. **Execution**: Tool executes and returns structured result
6. **Processing**: LLM receives result and generates response
7. **Response**: User receives natural language response based on tool output

Tools provide the LLM with:
- **Action Capability**: Perform operations beyond text generation
- **Information Access**: Retrieve real-time data and files
- **External Integration**: Connect to APIs and services
- **Controlled Execution**: Security-enforced system access
- **Autonomous Operation**: LLM decides when and how to use tools

The tool system enables LLF to be a powerful agent capable of complex multi-step tasks while maintaining security and user control.

---

**Last Updated**: 2025-01-06
