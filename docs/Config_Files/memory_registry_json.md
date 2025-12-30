# Memory Registry Guide: memory_registry.json

This document explains how to configure and manage the long-term memory system using the `memory/memory_registry.json` file.

**Last Updated:** 2025-12-28

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Structure](#configuration-structure)
3. [Parameters Reference](#parameters-reference)
4. [Enabled vs Disabled States](#enabled-vs-disabled-states)
5. [Memory Types](#memory-types)
6. [Configuration Examples](#configuration-examples)
7. [CLI Commands](#cli-commands)
8. [Memory Operations](#memory-operations)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Related Documentation](#related-documentation)

---

## Overview

The `memory_registry.json` file manages long-term memory instances that allow the LLM to store and retrieve information across conversations. It allows you to:

- Register multiple memory instances (persistent, session, temporary)
- Enable/disable memory access for the LLM
- Configure storage locations and limits
- Track memory metadata and modification dates
- **Automatically integrate memory tools when enabled**

**Location:** `memory/memory_registry.json`

**Key Concept:** When a memory instance is set to `"enabled": true`, the framework automatically loads memory tool definitions and gives the LLM access to memory functions (`add_memory`, `search_memories`, `get_memory`, `update_memory`, `delete_memory`). No additional configuration needed in `config_prompt.json`.

---

## Configuration Structure

A minimal memory entry looks like this:

```json
{
  "version": "1.0",
  "last_updated": "2025-12-28",
  "memories": [
    {
      "name": "main_memory",
      "display_name": "Main Memory",
      "description": "Long-term memory for persistent information storage",
      "directory": "main_memory",
      "enabled": true,
      "type": "persistent",
      "created_date": null,
      "last_modified": null,
      "metadata": {
        "storage_type": "json",
        "max_entries": 10000,
        "compression": false
      }
    }
  ],
  "metadata": {
    "description": "Registry of all available memory instances for the LLM Framework",
    "schema_version": "1.0"
  }
}
```

---

## Parameters Reference

### Core Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | String | Yes | - | Unique identifier for the memory instance (lowercase, no spaces) |
| `display_name` | String | Yes | - | Human-readable name shown in CLI and UI |
| `description` | String | Yes | - | Brief description of the memory's purpose |
| `directory` | String | Yes | - | Directory path where memory files are stored (relative to `memory/`) |
| `enabled` | Boolean | Yes | `false` | Whether the LLM has access to this memory (true = active, false = inactive) |
| `type` | String | Yes | `"persistent"` | Memory type: `persistent`, `session`, or `temporary` |

### Optional Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `created_date` | String | No | `null` | ISO date when memory instance was created |
| `last_modified` | String | No | `null` | ISO date when memory was last modified |
| `metadata` | Object | No | `{}` | Additional metadata for the memory instance |

### Metadata Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `metadata.storage_type` | String | `"json"` | Storage format: `json`, `sqlite`, etc. |
| `metadata.max_entries` | Integer | `10000` | Maximum number of entries allowed in this memory |
| `metadata.compression` | Boolean | `false` | Whether to compress memory data |

---

## Enabled vs Disabled States

### Enabled (`"enabled": true`)

When a memory instance is **enabled**:
- The LLM gains access to memory tool functions
- Memory tools are automatically added to the LLM's available functions
- The LLM can autonomously decide when to store or retrieve information
- Memory operations are logged and tracked

**Available Memory Functions:**

1. **`add_memory(content, tags, category, importance)`** - Store new information
2. **`search_memories(query, tags, category, limit)`** - Search for relevant memories
3. **`get_memory(memory_id)`** - Retrieve a specific memory by ID
4. **`update_memory(memory_id, content, tags, importance)`** - Update existing memory
5. **`delete_memory(memory_id)`** - Remove a memory entry

**Example LLM Usage:**
```
User: "Remember that I prefer Python over JavaScript"
LLM: I'll remember that for you.
     [Calls add_memory("User prefers Python over JavaScript", ["preferences", "languages"], "user_preferences", 8)]

User: "What programming language do I prefer?"
LLM: [Calls search_memories("programming language preference")]
     Based on what you told me, you prefer Python over JavaScript.
```

### Disabled (`"enabled": false`)

When a memory instance is **disabled**:
- The memory data still exists but the LLM cannot access it
- Memory tools are not loaded
- Useful for temporarily restricting memory access
- Can be re-enabled at any time via CLI or by editing the JSON

**Use Cases for Disabled:**
- Testing conversations without memory influence
- Preventing the LLM from storing sensitive information
- Debugging memory-related issues
- Development and testing

---

## Memory Types

### Persistent Memory (`"type": "persistent"`)

**Purpose:** Long-term storage that persists indefinitely across all sessions

**Characteristics:**
- Survives application restarts
- Shared across all conversations
- Suitable for facts, preferences, and important information
- No automatic cleanup

**Example Use Cases:**
- User preferences and settings
- Important facts about projects or people
- Long-term goals and tasks
- Historical information

**Configuration:**
```json
{
  "name": "persistent_memory",
  "display_name": "Persistent Memory",
  "description": "Long-term persistent storage",
  "type": "persistent",
  "enabled": true,
  "metadata": {
    "max_entries": 10000,
    "compression": false
  }
}
```

---

### Session Memory (`"type": "session"`)

**Purpose:** Storage that lasts for the duration of a session (until application restart)

**Characteristics:**
- Cleared when application stops
- Useful for temporary context within a session
- Lower storage overhead
- Automatic cleanup on session end

**Example Use Cases:**
- Temporary calculations or intermediate results
- Session-specific context
- Draft information not yet finalized
- Working memory for complex tasks

**Configuration:**
```json
{
  "name": "session_memory",
  "display_name": "Session Memory",
  "description": "Temporary storage for current session",
  "type": "session",
  "enabled": true,
  "metadata": {
    "max_entries": 1000,
    "compression": false
  }
}
```

---

### Temporary Memory (`"type": "temporary"`)

**Purpose:** Short-lived storage that expires after a set duration

**Characteristics:**
- Automatically expires and cleans up
- Useful for time-sensitive information
- Configurable expiration period
- Lowest storage overhead

**Example Use Cases:**
- Reminders for near-term events
- Temporary notes
- Cache-like storage
- Time-sensitive context

**Configuration:**
```json
{
  "name": "temp_memory",
  "display_name": "Temporary Memory",
  "description": "Short-lived storage with auto-expiration",
  "type": "temporary",
  "enabled": true,
  "metadata": {
    "max_entries": 500,
    "compression": false,
    "expiration_hours": 24
  }
}
```

---

## Configuration Examples

### Example 1: Standard Persistent Memory

A single persistent memory instance for general use:

```json
{
  "version": "1.0",
  "last_updated": "2025-12-28",
  "memories": [
    {
      "name": "main_memory",
      "display_name": "Main Memory",
      "description": "Long-term memory for persistent information storage",
      "directory": "main_memory",
      "enabled": true,
      "type": "persistent",
      "created_date": "2025-12-28",
      "last_modified": "2025-12-28",
      "metadata": {
        "storage_type": "json",
        "max_entries": 10000,
        "compression": false
      }
    }
  ]
}
```

**Use Case:** Single memory instance for all persistent storage needs.

---

### Example 2: Multi-Tier Memory System

Separate memory instances for different purposes and lifetimes:

```json
{
  "version": "1.0",
  "last_updated": "2025-12-28",
  "memories": [
    {
      "name": "long_term",
      "display_name": "Long-Term Memory",
      "description": "Permanent storage for important facts and preferences",
      "directory": "long_term_memory",
      "enabled": true,
      "type": "persistent",
      "created_date": "2025-12-28",
      "last_modified": "2025-12-28",
      "metadata": {
        "storage_type": "json",
        "max_entries": 5000,
        "compression": false
      }
    },
    {
      "name": "working",
      "display_name": "Working Memory",
      "description": "Session-based working memory for current tasks",
      "directory": "working_memory",
      "enabled": true,
      "type": "session",
      "created_date": "2025-12-28",
      "last_modified": "2025-12-28",
      "metadata": {
        "storage_type": "json",
        "max_entries": 1000,
        "compression": false
      }
    },
    {
      "name": "scratch",
      "display_name": "Scratch Memory",
      "description": "Temporary scratch space for calculations",
      "directory": "scratch_memory",
      "enabled": true,
      "type": "temporary",
      "created_date": "2025-12-28",
      "last_modified": "2025-12-28",
      "metadata": {
        "storage_type": "json",
        "max_entries": 500,
        "compression": false,
        "expiration_hours": 24
      }
    }
  ]
}
```

**Use Case:** Tiered memory system with different retention policies for different types of information.

---

### Example 3: Project-Specific Memory

Separate memory instances for different projects:

```json
{
  "version": "1.0",
  "last_updated": "2025-12-28",
  "memories": [
    {
      "name": "project_a",
      "display_name": "Project A Memory",
      "description": "Memory for Project A context and information",
      "directory": "project_a_memory",
      "enabled": true,
      "type": "persistent",
      "metadata": {
        "storage_type": "json",
        "max_entries": 2000,
        "compression": false,
        "project": "project_a"
      }
    },
    {
      "name": "project_b",
      "display_name": "Project B Memory",
      "description": "Memory for Project B context and information",
      "directory": "project_b_memory",
      "enabled": false,
      "type": "persistent",
      "metadata": {
        "storage_type": "json",
        "max_entries": 2000,
        "compression": false,
        "project": "project_b"
      }
    }
  ]
}
```

**Use Case:** Enable/disable memory instances based on which project you're working on. Only `project_a` is currently active.

---

## CLI Commands

The framework provides convenient CLI commands for managing memory:

### List All Memory Instances

```bash
# List all registered memory instances
llf memory list

# List only enabled memory instances
llf memory list --enabled
```

**Output:**
```
Main Memory                    enabled
Working Memory                 enabled
Scratch Memory                 disabled
```

---

### Enable Memory

```bash
# Enable a specific memory instance by name
llf memory enable main_memory

# Enable by display name
llf memory enable "Main Memory"
```

**Result:** Sets `"enabled": true` in the registry. Memory tools become available to the LLM immediately for new conversations.

---

### Disable Memory

```bash
# Disable a specific memory instance by name
llf memory disable main_memory

# Disable by display name
llf memory disable "Main Memory"
```

**Result:** Sets `"enabled": false` in the registry. Memory tools are removed from the LLM immediately for new conversations.

---

### Show Memory Info

```bash
# Show detailed information about a memory instance
llf memory info main_memory

# Or use display name
llf memory info "Main Memory"
```

**Output:**
```
Main Memory (main_memory)
  ✓ enabled
  Type: persistent
  Description: Long-term memory for persistent information storage
  Location: /path/to/project/memory/main_memory
  Storage Type: json
  Max Entries: 10000
  Compression: No
  Created: 2025-12-28
  Last Modified: 2025-12-28
```

---

## Memory Operations

When memory is enabled, the LLM has access to these operations:

### Add Memory

**Function:** `add_memory(content, tags=[], category="general", importance=5)`

**Purpose:** Store new information in memory

**Parameters:**
- `content` (string, required): The information to store
- `tags` (list, optional): Tags for categorization and search
- `category` (string, optional): Category for organization
- `importance` (integer, optional): Importance level 1-10

**Example LLM Usage:**
```
add_memory("User's birthday is March 15th", ["personal", "dates"], "user_info", 9)
```

---

### Search Memories

**Function:** `search_memories(query, tags=[], category=None, limit=10)`

**Purpose:** Search for relevant memories

**Parameters:**
- `query` (string, required): Search query
- `tags` (list, optional): Filter by tags
- `category` (string, optional): Filter by category
- `limit` (integer, optional): Maximum results to return

**Example LLM Usage:**
```
search_memories("birthday", tags=["personal"], limit=5)
```

---

### Get Memory

**Function:** `get_memory(memory_id)`

**Purpose:** Retrieve a specific memory by ID

**Parameters:**
- `memory_id` (string, required): Unique memory identifier

**Example LLM Usage:**
```
get_memory("mem_12345")
```

---

### Update Memory

**Function:** `update_memory(memory_id, content=None, tags=None, importance=None)`

**Purpose:** Update an existing memory

**Parameters:**
- `memory_id` (string, required): Memory ID to update
- `content` (string, optional): New content
- `tags` (list, optional): New tags
- `importance` (integer, optional): New importance level

**Example LLM Usage:**
```
update_memory("mem_12345", content="User's birthday is March 15th, 1990", importance=10)
```

---

### Delete Memory

**Function:** `delete_memory(memory_id)`

**Purpose:** Remove a memory entry

**Parameters:**
- `memory_id` (string, required): Memory ID to delete

**Example LLM Usage:**
```
delete_memory("mem_12345")
```

---

## Best Practices

### When to Use Memory

**Good Use Cases:**
1. **User Preferences** - Store preferences that should persist
2. **Important Facts** - Store facts about projects, people, or domains
3. **Context Across Sessions** - Information needed in future conversations
4. **Learning** - Store corrections or new information the LLM learns
5. **Tasks and Goals** - Track ongoing tasks and objectives

**Poor Use Cases:**
1. **Conversation History** - Use the built-in conversation tracking instead
2. **Temporary Calculations** - Use session or temporary memory, not persistent
3. **Publicly Available Info** - Don't store what can be searched online
4. **Redundant Information** - Don't duplicate what's in RAG stores

---

### Memory Organization

**Use Categories:**
```
- user_preferences
- project_info
- tasks
- facts
- learning
- corrections
```

**Use Tags Effectively:**
```
- Specific: ["python", "debugging", "logging"]
- Not: ["code", "programming", "tech"]
```

**Set Appropriate Importance:**
- **1-3**: Low priority, can be forgotten
- **4-7**: Medium priority, useful information
- **8-10**: High priority, critical information

---

### Storage Management

**Set Reasonable Limits:**
```json
{
  "metadata": {
    "max_entries": 10000  // Adjust based on needs
  }
}
```

**Monitor Memory Growth:**
- Periodically review memory contents
- Delete outdated or irrelevant entries
- Use appropriate memory types (temporary for short-term needs)

**Use Compression for Large Memories:**
```json
{
  "metadata": {
    "compression": true  // Enable for large memory instances
  }
}
```

---

### Security Considerations

**Avoid Storing:**
- Passwords or API keys
- Personal identification numbers (SSN, credit cards)
- Sensitive personal information
- Confidential business data

**Enable/Disable Strategy:**
- Disable memory when working with sensitive information
- Use separate memory instances for different security levels
- Regularly audit memory contents

---

## Troubleshooting

### Problem: "Memory not found"

**Solution:**
1. Verify the `name` in your command matches the registry
2. Check the registry file exists and is valid JSON
3. Use `llf memory list` to see all available memory instances

---

### Problem: LLM not using memory functions

**Solution:**
1. Verify the memory is enabled: `llf memory list --enabled`
2. Ensure you've started a new conversation after enabling
3. Check that the memory directory exists and is writable
4. Verify the LLM supports function calling (not all models do)

---

### Problem: Memory operations failing

**Solution:**
1. Check directory permissions on `memory/[directory]/`
2. Verify `max_entries` limit hasn't been reached
3. Check disk space availability
4. Look for error messages in logs
5. Ensure memory files aren't corrupted

---

### Problem: Memory growing too large

**Solution:**
1. Reduce `max_entries` limit
2. Enable `compression` in metadata
3. Use `temporary` type for short-lived information
4. Periodically clean up old entries
5. Split into multiple memory instances by category

---

### Problem: "Permission denied" on memory files

**Solution:**
1. Check file permissions on `memory/[directory]/`
2. Ensure the user running LLF has write access
3. Verify directory ownership is correct
4. Check parent directory permissions

---

## Related Documentation

- [Main Configuration](config_json.md) - LLM endpoint and server configuration
- [Prompt Configuration](config_prompt_json.md) - System prompts and message formatting
- [Data Store Registry](data_store_registry_json.md) - RAG vector store configuration
- [Tools Registry](tools_registry_json.md) - Tool system configuration
- [Modules Registry](modules_registry_json.md) - Pluggable module configuration

---

## Additional Resources

### Memory Directory Structure

Each memory instance directory typically contains:
```
memory/
├── memory_registry.json          # This registry file
├── main_memory/                  # Example memory instance
│   ├── memories.json             # Memory entries
│   ├── index.json                # Search index
│   └── metadata.json             # Instance metadata
└── working_memory/               # Another instance
    ├── memories.json
    ├── index.json
    └── metadata.json
```

### Memory Entry Format

Memory entries are stored in JSON format:
```json
{
  "id": "mem_12345",
  "content": "User prefers Python over JavaScript",
  "tags": ["preferences", "languages"],
  "category": "user_preferences",
  "importance": 8,
  "created_at": "2025-12-28T10:30:00Z",
  "updated_at": "2025-12-28T10:30:00Z",
  "access_count": 5,
  "last_accessed": "2025-12-28T15:45:00Z"
}
```

---

For additional help, refer to the main [README.md](../README.md) or open an issue on GitHub.
