# Memory System Setup Guide

This guide explains how to set up and use the Local LLM Framework's long-term memory system, which enables your LLM to remember information across conversations.

---

## Table of Contents

- [What is Memory?](#what-is-memory)
- [How Memory Works](#how-memory-works)
- [Getting Started](#getting-started)
- [Managing Memory Instances](#managing-memory-instances)
- [Creating Custom Memory Instances](#creating-custom-memory-instances)
- [Understanding Memory Structure](#understanding-memory-structure)
- [Memory Types](#memory-types)
- [Best Practices](#best-practices)
- [Advanced Topics](#advanced-topics)
- [Troubleshooting](#troubleshooting)

---

## What is Memory?

The memory system provides **persistent long-term storage** that allows your LLM to:

- **Remember facts** about you across conversations
- **Store preferences** for how you want the LLM to behave
- **Track tasks** and ongoing projects
- **Maintain context** about your work and interests
- **Build knowledge** over time

Think of it as giving your LLM a notebook where it can write down important information and refer back to it later.

### Key Features

- ✅ **Persistent** - Memories survive across chat sessions
- ✅ **Searchable** - LLM can find relevant memories by keywords, tags, or type
- ✅ **Organized** - Categorize memories by type (fact, preference, task, etc.)
- ✅ **Controllable** - Enable/disable memory instances as needed
- ✅ **Multiple instances** - Create separate memory spaces for different purposes

---

## How Memory Works

### Architecture Overview

```
┌─────────────────────┐
│   Your LLM Chat     │  ← You interact here
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Memory Tools       │  ← LLM uses 6 function tools
│  - add_memory       │
│  - search_memories  │
│  - get_memory       │
│  - update_memory    │
│  - delete_memory    │
│  - get_memory_stats │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Memory Manager     │  ← Handles storage operations
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Memory Instance    │  ← Stores data in JSONL format
│  memory/main_memory │
│  ├── memory.jsonl   │  ← All memories stored here
│  ├── index.json     │  ← Fast lookups
│  └── metadata.json  │  ← Statistics
└─────────────────────┘
```

### Conversation Flow

1. **Conversation starts**
   - LLM receives system prompt with memory instructions
   - LLM is instructed to search memories FIRST

2. **LLM searches memories**
   - Uses `search_memories` tool to find relevant information
   - Searches by keywords, tags, or memory type

3. **LLM uses memory context**
   - Incorporates found memories into its understanding
   - Provides personalized, context-aware responses

4. **LLM updates memories**
   - Adds new memories when learning something important
   - Updates existing memories when information changes
   - Deletes outdated or incorrect memories

---

## Getting Started

### Check Memory Status

First, see what memory instances are available:

```bash
llf memory list
```

Output example:
```
Memory Instances:
  ✓ main_memory      (enabled)
```

### Enable Memory

If memory is disabled, enable it:

```bash
llf memory enable main_memory
```

Output:
```
✓ Enabled memory: main_memory
```

### View Memory Information

Get detailed information about a memory instance:

```bash
llf memory info main_memory
```

Output shows:
- Status (enabled/disabled)
- Type (persistent)
- Description
- Storage location
- Configuration settings

### Start Using Memory

Once enabled, your LLM automatically has access to memory. Just chat normally:

```bash
llf chat
```

Example conversation:
```
You: My name is Alex and I prefer concise responses.
LLM: Got it, Alex! I'll keep my responses concise. I've stored that in my memory.
You: I want you to remember that my name is Alex

[Multiple conversation sessions later...]

You: What's my name?
LLM: Your name is Alex.
```

The LLM automatically:
- Searched memories at conversation start
- Found your name
- Responded with personalized information

---

## Managing Memory Instances

### List All Memory Instances

```bash
# Show all instances
llf memory list

# Show only enabled instances
llf memory list --enabled
```

### Create a Memory Instance

```bash
llf memory create <memory_name>
```

This will perform the following:
- Add memory module entry from `memory/memory_registry.json`
- Creates the memory module in the `memory` directory

### Enable a Memory Instance

```bash
llf memory enable <memory_name>
```

**What happens:**
- Sets `enabled: true` in `memory/memory_registry.json`
- LLM gains access to this memory instance
- Memory tools become available to the LLM

### Disable a Memory Instance

```bash
llf memory disable <memory_name>
```

**What happens:**
- Sets `enabled: false` in `memory/memory_registry.json`
- LLM loses access to this memory instance
- Existing memories remain intact but are not accessible

**Use cases:**
- Temporarily disable memory for privacy
- Switch between different memory contexts
- Test LLM behavior without memory

### View Memory Details

```bash
llf memory info <memory_name>
```

Shows:
- Current status (enabled/disabled)
- Memory type (persistent, session, temporary)
- Description
- File locations
- Storage configuration
- Creation and modification dates

### Delete Memory Module

```bash
llf memory delete <memory_name>
```

This will perform the following:
- Delete the memory module entry from `memory/memory_registry.json`
- Delete the memory module in the `memory` directory
- The memory module will NOT be deleted if it is enabled

---

## Creating Custom Memory Instances

You can create multiple memory instances for different purposes (e.g., work, personal, projects).

### Creating The Memory Module

```bash
llf memory create my_memory_module
```

**Examples:**
```bash
# Create a project memory
llf memory create python_project
```

### What Gets Created

The script creates:

1. **Directory:** `memory/<memory_name>/`
2. **Files:**
   - `memory.jsonl` - Empty, ready for memories
   - `index.json` - Empty index (`{}`)
   - `metadata.json` - Initialized with zero counts
   - `README.md` - Documentation placeholder

3. **Registry entry** in `memory/memory_registry.json`:
   ```json
   {
     "name": "my_custom_memory",
     "display_name": "My Custom Memory",
     "description": "Custom memory instance",
     "directory": "my_custom_memory",
     "enabled": false,
     "type": "persistent",
     "metadata": {
       "storage_type": "json",
       "max_entries": 10000,
       "compression": false
     }
   }
   ```

### Customize the Registry Entry

After creation, edit `memory/memory_registry.json` to customize:

```json
{
  "name": "work_context",
  "display_name": "Work Context",
  "description": "Professional work-related memories",  ← Update this
  "enabled": false,                                     ← Change to true when ready
  "metadata": {
    "max_entries": 5000                                 ← Adjust capacity
  }
}
```

### Enable Your Custom Memory

```bash
llf memory enable work_context
```

Now your LLM can use this separate memory space!

---

## Understanding Memory Structure

### Directory Layout

```
memory/
├── memory_registry.json          ← Registry of all memory instances
├── README.md                     ← Overview documentation
│
├── main_memory/                  ← Default memory instance
│   ├── memory.jsonl              ← All memory entries (one per line)
│   ├── index.json                ← Fast ID lookups
│   ├── metadata.json             ← Statistics and info
│   └── README.md                 ← Instance documentation
│
└── work_context/                 ← Your custom memory instance
    ├── memory.jsonl
    ├── index.json
    ├── metadata.json
    └── README.md
```

### Memory Entry Format

Each memory in `memory.jsonl` is a JSON object on one line:

```json
{
  "id": "mem_5e1780260419",
  "timestamp": "2025-12-28T04:32:30.577162+00:00Z",
  "type": "fact",
  "content": "User's name is Alex",
  "tags": ["personal", "name"],
  "importance": 0.8,
  "source": "llm",
  "last_accessed": "2025-12-28T04:32:30.577162+00:00Z",
  "access_count": 0,
  "metadata": {}
}
```

**Field Descriptions:**

| Field | Description |
|-------|-------------|
| `id` | Unique identifier (`mem_` + 12 random characters) |
| `timestamp` | When memory was created (UTC, ISO format) |
| `type` | Memory category: note, fact, preference, task, context |
| `content` | The actual memory text (what to remember) |
| `tags` | Array of keywords for categorization and search |
| `importance` | 0.0-1.0 scale (0.5 = normal, 0.8+ = critical) |
| `source` | Who created it: "llm", "system", or "user" |
| `last_accessed` | Last time this memory was retrieved |
| `access_count` | How many times it's been accessed |
| `metadata` | Custom fields (JSON object) |

### Index File (`index.json`)

Maps memory IDs to line numbers for fast lookups:

```json
{
  "mem_5e1780260419": {
    "line": 1,
    "timestamp": "2025-12-28T04:32:30.577162+00:00Z",
    "type": "fact",
    "tags": ["personal", "name"]
  }
}
```

### Metadata File (`metadata.json`)

Tracks statistics without scanning all memories:

```json
{
  "total_entries": 5,
  "last_updated": "2025-12-28T05:11:01.520670+00:00Z",
  "created_date": "2025-12-27T00:00:00Z",
  "size_bytes": 1529,
  "oldest_entry": "2025-12-27T00:00:00Z",
  "newest_entry": "2025-12-28T05:11:01.520670+00:00Z",
  "entry_types": {
    "note": 1,
    "fact": 4,
    "preference": 0,
    "task": 0,
    "context": 0
  },
  "statistics": {
    "average_importance": 0.5,
    "most_accessed_id": "mem_example_001",
    "total_accesses": 0
  }
}
```

---

## Memory Types

The system supports five memory categories:

### 1. **fact** - Factual Information

**Use for:** Hard facts that don't change often

**Examples:**
- "User's name is Alex"
- "User lives in Seattle"
- "User works as a software engineer"

**Importance:** Usually 0.7-0.9 (facts are important)

**Tags:** `["personal", "identity", "location", "profession"]`

---

### 2. **preference** - User Preferences

**Use for:** How the user wants the LLM to behave

**Examples:**
- "User prefers concise responses"
- "User likes examples in code"
- "User prefers British English spelling"

**Importance:** Usually 0.8-1.0 (preferences guide all responses)

**Tags:** `["behavior", "style", "format", "language"]`

---

### 3. **note** - General Notes

**Use for:** Unstructured observations and comments

**Examples:**
- "User mentioned they like coffee"
- "User is learning Spanish"
- "User is interested in machine learning"

**Importance:** Usually 0.3-0.6 (contextual information)

**Tags:** `["interests", "hobbies", "observations"]`

---

### 4. **task** - Tasks and Projects

**Use for:** Ongoing work, action items, project tracking

**Examples:**
- "User is working on a Python web scraper project"
- "User needs to review the database schema"
- "User wants to learn about Docker"

**Importance:** 0.6-0.8 (varies by task priority)

**Tags:** `["project", "todo", "learning", "goal"]`

---

### 5. **context** - Situational Context

**Use for:** Current conversation or work context

**Examples:**
- "We're discussing REST API design"
- "User is debugging a memory leak issue"
- "Context: building a React application"

**Importance:** 0.4-0.7 (relevant during active work)

**Tags:** `["current", "discussion", "debugging", "topic"]`

---

## Best Practices

### When to Use Memory

✅ **DO remember:**
- User's name and personal details
- Preferences for response style
- Ongoing projects and tasks
- Important decisions made
- Repeated questions or topics
- Skills and expertise level

❌ **DON'T remember:**
- Sensitive personal information (passwords, SSN, etc.)
- Temporary conversation topics
- One-time questions
- Redundant information

### Tagging Strategy

**Use descriptive, searchable tags:**

```json
// Good tags
"tags": ["personal", "name", "identity"]
"tags": ["project", "python", "webscraper"]
"tags": ["preference", "code-style", "concise"]

// Poor tags
"tags": ["stuff", "thing"]
"tags": ["a", "b", "c"]
```

**Tag categories to consider:**
- **Category:** personal, work, project, learning
- **Topic:** python, javascript, database, api
- **Type:** identity, preference, skill, goal
- **Status:** active, completed, archived

### Importance Scoring

**Guidelines:**

| Score | Use For | Examples |
|-------|---------|----------|
| **0.9-1.0** | Critical preferences | "User NEVER wants code comments", "User is colorblind" |
| **0.7-0.8** | Important facts | User's name, profession, key preferences |
| **0.5-0.6** | Normal information | Interests, project details, general notes |
| **0.3-0.4** | Minor observations | Casual mentions, temporary context |
| **0.1-0.2** | Low priority | Rarely used, easily rediscovered |

### Memory Maintenance

**Periodic cleanup:**

1. **Remove duplicates**
   - Search for similar memories
   - Keep the most important/recent one
   - Delete the others

2. **Update outdated information**
   - Use `update_memory` instead of creating new entries
   - Keep memory count manageable

3. **Delete irrelevant memories**
   - Remove completed tasks
   - Clear old context that's no longer relevant

4. **Check statistics**
   ```bash
   llf memory info main_memory
   ```
   - Monitor total entries
   - Watch for unbalanced memory types

---

## Advanced Topics

### Multiple Memory Instances

**Use case:** Separate contexts for different purposes

**Example setup:**

```bash
# Create separate memories
llf memory create work_projects
llf memory create personal_assistant
llf memory create learning_journal

# Enable the one you need
llf memory enable work_projects
llf memory disable personal_assistant
```

**Benefits:**
- Context isolation (work vs. personal)
- Privacy control
- Organized information
- Capacity management

### Memory Registry Structure

**Location:** `memory/memory_registry.json`

**Full structure:**
```json
{
  "version": "1.0",
  "last_updated": "2025-12-30",
  "memories": [
    {
      "name": "main_memory",              // Internal identifier
      "display_name": "Main Memory",      // User-facing name
      "description": "Long-term memory for persistent information storage",
      "directory": "main_memory",         // Directory name
      "enabled": true,                    // Active status
      "type": "persistent",               // Memory type
      "created_date": null,
      "last_modified": null,
      "metadata": {
        "storage_type": "json",           // JSONL format
        "max_entries": 10000,             // Capacity limit
        "compression": false              // Future feature
      }
    }
  ],
  "metadata": {
    "description": "Registry of all available memory instances",
    "schema_version": "1.0"
  }
}
```

### Manual Memory Management

**Editing memory files directly:**

⚠️ **Warning:** Only edit when LLM is not running

1. **Backup first:**
   ```bash
   cp memory/main_memory/memory.jsonl memory/main_memory/memory.jsonl.bak
   ```

2. **Edit memory.jsonl:**
   - Each line must be valid JSON
   - Don't add blank lines
   - Keep ID format: `mem_` + 12 hex chars

3. **Rebuild index and metadata:**
   ```bash
   # The system rebuilds automatically on next access
   # Or manually rebuild using Python:
   python3 << EOF
   from llf.memory_manager import MemoryManager
   mm = MemoryManager()
   mm.reload()
   EOF
   ```

### Capacity Planning

**Default limit:** 10,000 entries per instance

**Estimate storage:**
- Average entry: ~300 bytes
- 1,000 entries: ~300 KB
- 10,000 entries: ~3 MB

**Adjust limit in registry:**
```json
"metadata": {
  "max_entries": 5000  // Reduce or increase as needed
}
```

**When to increase:**
- Large knowledge base
- Many projects tracked
- Long-term historical data

**When to decrease:**
- Limited disk space
- Faster searches needed
- Focused use case

---

## Troubleshooting

### Memory Not Working

**Symptom:** LLM doesn't remember anything

**Solutions:**

1. **Check if memory is enabled:**
   ```bash
   llf memory list
   ```
   Should show `✓ enabled`

2. **Enable memory if disabled:**
   ```bash
   llf memory enable main_memory
   ```

3. **Verify registry file exists:**
   ```bash
   ls -la memory/memory_registry.json
   ```

4. **Check memory directory exists:**
   ```bash
   ls -la memory/main_memory/
   ```
   Should contain: memory.jsonl, index.json, metadata.json

5. **Restart LLF:**
   ```bash
   # Stop any running sessions
   llf server stop

   # Start fresh
   llf chat
   ```

### Memory Registry Errors

**Error:** `Memory registry not found`

**Fix:**
```bash
# Registry should be at memory/memory_registry.json
# If missing, recreate main_memory:
llf memory create main_memory
llf memory enable main_memory
```

**Error:** `Invalid JSON in registry`

**Fix:**
```bash
# Validate JSON syntax
cat memory/memory_registry.json | python3 -m json.tool

# If corrupted, restore from example or rebuild
```

### Memory Files Corrupted

**Symptom:** Errors when accessing memory

**Recovery steps:**

1. **Check file integrity:**
   ```bash
   # Validate JSONL format
   python3 << EOF
   import json
   with open('memory/main_memory/memory.jsonl', 'r') as f:
       for i, line in enumerate(f, 1):
           try:
               json.loads(line.strip())
           except json.JSONDecodeError as e:
               print(f"Error on line {i}: {e}")
   EOF
   ```

2. **Restore from backup:**
   ```bash
   cp memory/main_memory/memory.jsonl.bak memory/main_memory/memory.jsonl
   ```

3. **Rebuild index and metadata:**
   ```bash
   # Delete corrupted files
   rm memory/main_memory/index.json
   rm memory/main_memory/metadata.json

   # System rebuilds on next access
   llf chat
   ```

### Too Many Memories

**Symptom:** Slow searches, large file sizes

**Solutions:**

1. **Check statistics:**
   ```bash
   llf memory info main_memory
   ```

2. **Archive old memories:**
   ```bash
   # Manual approach: copy old entries to archive
   head -1000 memory/main_memory/memory.jsonl > archive.jsonl
   tail -n +1001 memory/main_memory/memory.jsonl > memory.jsonl.new
   mv memory.jsonl.new memory/main_memory/memory.jsonl
   ```

3. **Create new memory instance:**
   ```bash
   # Start fresh with new instance
   llf memory create main_memory_2025
   llf memory enable main_memory_2025
   llf memory disable main_memory
   ```

4. **Reduce max_entries limit in registry**

### Permission Denied

**Error:** `PermissionError: [Errno 13]`

**Fix:**
```bash
# Check permissions
ls -la memory/main_memory/

# Fix if needed
chmod -R u+w memory/
```

---

## Quick Reference

### Common Commands

```bash
# List all memory instances
llf memory list

# Enable memory
llf memory enable main_memory

# Disable memory
llf memory disable main_memory

# View memory info
llf memory info main_memory

# Create new memory instance
llf memory create my_memory

# Check memory directory
ls -la memory/main_memory/

# Validate registry
cat memory/memory_registry.json | python3 -m json.tool
```

### File Locations

| File | Location | Purpose |
|------|----------|---------|
| Registry | `memory/memory_registry.json` | Lists all memory instances |
| Memory data | `memory/main_memory/memory.jsonl` | Stores all memory entries |
| Index | `memory/main_memory/index.json` | Fast ID lookups |
| Metadata | `memory/main_memory/metadata.json` | Statistics |

### Memory Operations (LLM Tools)

| Operation | What It Does |
|-----------|--------------|
| `search_memories` | Find memories by keywords, tags, type |
| `add_memory` | Create a new memory |
| `get_memory` | Retrieve specific memory by ID |
| `update_memory` | Modify existing memory |
| `delete_memory` | Remove a memory |
| `get_memory_stats` | View statistics |

---

## Next Steps

1. **Enable memory:**
   ```bash
   llf memory enable main_memory
   ```

2. **Start chatting:**
   ```bash
   llf chat
   ```

3. **Test memory:**
   ```
   You: Remember that I prefer Python over JavaScript
   LLM: I've stored that preference in my memory!

   [Later...]

   You: What programming language do I prefer?
   LLM: You prefer Python over JavaScript.
   ```

4. **Explore advanced features:**
   - Create custom memory instances for different contexts
   - Organize memories with tags
   - Monitor statistics with `llf memory info`

---

**Last Updated:** 2026-01-01
