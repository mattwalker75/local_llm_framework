# LLM Long-Term Memory System

## Overview

The Local LLM Framework now includes a long-term memory system that allows the LLM to persistently store and retrieve information across conversations. When enabled, the LLM can use function calling (tool use) to manage its own memory.

## Quick Start

### 1. Enable Memory

```bash
# Enable the main memory instance
llf memory enable main_memory

# Verify it's enabled
llf memory list --enabled
```

### 2. Start Chatting

Once memory is enabled, the LLM will automatically:
- See memory instructions in its system prompt
- Have access to 6 memory tools (add, search, get, update, delete, stats)
- Use these tools autonomously during conversations

```bash
# CLI chat with memory
llf chat

# GUI chat with memory
llf gui
```

### 3. Test Memory

```
User: Remember that I prefer Python over JavaScript
LLM: [Uses add_memory tool to store this preference]

User: What programming language do I prefer?
LLM: [Uses search_memories tool to find the preference]
```

## Architecture

### Directory Structure

```
local_llm_framework/
├── memory/
│   ├── memory_registry.json          # Configuration file
│   └── main_memory/                   # Memory instance directory
│       ├── memory.jsonl               # Memory entries (one JSON per line)
│       ├── index.json                 # Fast lookup index
│       └── metadata.json              # Statistics and metadata
```

### Storage Format

Memory is stored in **JSONL** (JSON Lines) format - human-readable and editable:

```jsonl
{"id": "mem_abc123", "timestamp": "2025-12-27T12:00:00Z", "type": "preference", "content": "User prefers Python", "tags": ["programming"], "importance": 0.9, ...}
{"id": "mem_def456", "timestamp": "2025-12-27T13:00:00Z", "type": "fact", "content": "User lives in San Francisco", "tags": ["personal"], "importance": 0.7, ...}
```

## Memory Tools

The LLM has access to 6 memory management tools:

### 1. add_memory
Store new information in memory.

**Parameters:**
- `content` (required): The information to remember
- `memory_type` (required): Type - "note", "fact", "preference", "task", or "context"
- `tags` (optional): Array of tags for categorization
- `importance` (optional): Score from 0.0-1.0 (default: 0.5)

**Example:**
```json
{
  "content": "User prefers dark mode in applications",
  "memory_type": "preference",
  "tags": ["ui", "preferences"],
  "importance": 0.8
}
```

### 2. search_memories
Search for relevant memories.

**Parameters:**
- `query` (optional): Keyword to search for
- `tags` (optional): Filter by tags
- `memory_type` (optional): Filter by type
- `min_importance` (optional): Minimum importance score
- `limit` (optional): Max results (default: 10)

### 3. get_memory
Retrieve a specific memory by ID.

**Parameters:**
- `memory_id` (required): The unique memory ID

### 4. update_memory
Update an existing memory.

**Parameters:**
- `memory_id` (required): Memory to update
- `content` (optional): New content
- `tags` (optional): New tags
- `importance` (optional): New importance score

### 5. delete_memory
Delete a memory (permanent).

**Parameters:**
- `memory_id` (required): Memory to delete

### 6. get_memory_stats
Get statistics about the memory system.

**Parameters:** None

## CLI Commands

### List Memories

```bash
# List all memory instances
llf memory list

# List only enabled memories
llf memory list --enabled
```

### Enable/Disable Memory

```bash
# Enable a memory instance
llf memory enable main_memory

# Disable a memory instance
llf memory disable main_memory
```

### Get Memory Info

```bash
# View detailed information about a memory instance
llf memory info main_memory
```

## Configuration

Edit `memory/memory_registry.json` to configure memory instances:

```json
{
  "version": "1.0",
  "memories": [
    {
      "name": "main_memory",
      "display_name": "Main Memory",
      "description": "Long-term memory for persistent information storage",
      "directory": "main_memory",
      "enabled": true,
      "type": "persistent",
      "metadata": {
        "storage_type": "json",
        "max_entries": 10000,
        "compression": false
      }
    }
  ]
}
```

### Registry Fields

- **name**: Internal identifier (used in CLI commands)
- **display_name**: Human-readable name
- **description**: What this memory is for
- **directory**: Where memory files are stored (relative to `memory/`)
- **enabled**: `true` = LLM has access, `false` = disabled
- **type**: "persistent", "session", or "temporary"
- **metadata.max_entries**: Maximum number of memory entries
- **metadata.storage_type**: Storage format (currently "json")

## How It Works

### 1. Memory Manager (`llf/memory_manager.py`)

Core engine that handles:
- Loading enabled memories from registry
- CRUD operations on memory entries
- Index and metadata maintenance
- Search functionality

### 2. Memory Tools (`llf/memory_tools.py`)

Defines the function calling interface:
- 6 tool definitions in OpenAI format
- `execute_memory_tool()` function for tool execution
- System prompt with memory guidelines

### 3. Prompt Config Integration (`llf/prompt_config.py`)

Automatically injects memory when enabled:
- Lazy-loads memory manager
- Adds memory instructions to system prompt
- Provides tools via `get_memory_tools()`

### 4. Runtime Tool Calling (`llf/llm_runtime.py`)

Executes LLM tool requests:
- Gets tools from prompt_config
- Passes tools to OpenAI API
- Handles tool call responses from LLM
- Executes tools and returns results
- Supports multi-turn tool calling

## Performance

The memory system is designed for local use:

- **Supported entries**: 10,000-50,000 entries
- **Lookup speed**: O(1) via index.json
- **File format**: Human-readable JSONL
- **Search method**: Linear scan with filters (fast for 10k-50k entries)

## Memory Guidelines

The LLM is instructed to remember:
- User preferences and settings
- Important facts about the user
- Ongoing projects or tasks
- Significant decisions or conclusions
- Information the user explicitly says to remember

The LLM is instructed NOT to remember:
- Temporary/ephemeral information
- Sensitive data (passwords, API keys, PII)
- Every minor detail
- Information the user asks not to remember

## Tool Calling Requirements

### Server Support

Your LLM server must support function calling (tool use). This includes:
- **llama-server**: Supports tools via OpenAI-compatible API
- **OpenAI API**: Full tool support
- **Compatible servers**: Any server implementing OpenAI function calling spec

### Model Support

The loaded model must support function calling:
- Most modern LLMs (Llama 3+, Mistral, etc.) support this
- Check your model's documentation for function calling capabilities

## Troubleshooting

### Memory tools not working?

1. **Check if memory is enabled:**
   ```bash
   llf memory list --enabled
   ```

2. **Check server logs for tool calling errors:**
   ```bash
   llf chat  # Look for tool-related errors in output
   ```

3. **Verify your model supports function calling**

4. **Check the registry file exists:**
   ```bash
   cat memory/memory_registry.json
   ```

### Memory not persisting?

1. **Check file permissions on memory directory:**
   ```bash
   ls -la memory/main_memory/
   ```

2. **Verify memory.jsonl is being written:**
   ```bash
   cat memory/main_memory/memory.jsonl
   ```

3. **Check for errors in application logs**

## Examples

### Example 1: User Preferences

```
User: I prefer concise responses without too much explanation
LLM: I'll remember that you prefer concise responses.
[Calls add_memory with content="User prefers concise responses", type="preference"]

User: How should you respond to me?
LLM: [Calls search_memories with query="prefer"]
Based on your preferences, I should provide concise responses without too much explanation.
```

### Example 2: Project Context

```
User: I'm working on a Python web app using FastAPI and PostgreSQL
LLM: [Calls add_memory with content="Working on Python web app with FastAPI and PostgreSQL", type="context", tags=["project", "python", "fastapi", "postgresql"]]

User: What database am I using in my current project?
LLM: [Calls search_memories with tags=["project"]]
You're using PostgreSQL for your Python web app project with FastAPI.
```

### Example 3: Task Tracking

```
User: Remember to implement user authentication next
LLM: [Calls add_memory with content="TODO: Implement user authentication", type="task", importance=0.8]

User: What tasks do I have pending?
LLM: [Calls search_memories with memory_type="task"]
You have a pending task to implement user authentication.
```

## Testing

Comprehensive test coverage includes:

- **Unit tests**: `tests/test_memory_manager.py`
- **Integration tests**: `tests/test_memory_integration.py`
- **Tool calling tests**: `tests/test_memory_tool_calling.py`

Run all tests:
```bash
source llf_venv/bin/activate
python -m pytest tests/ -v
```

## Future Enhancements

Potential improvements:
- Vector embeddings for semantic search
- Multiple memory instances (personal, work, project-specific)
- Automatic memory importance calculation
- Memory summarization and compression
- Memory export/import functionality
- Memory statistics dashboard in GUI
