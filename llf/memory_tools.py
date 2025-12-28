"""
Memory Tools for LLM Function Calling

This module defines the tool/function calling interface for memory operations.
These tools allow the LLM to interact with long-term memory through structured
function calls.

Author: Local LLM Framework
License: MIT
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# Tool definitions for OpenAI-style function calling
MEMORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_memory",
            "description": "Store a new piece of information in long-term memory. Use this to remember important facts, preferences, tasks, or context that should be recalled in future conversations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The information to remember. Be specific and clear."
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["note", "fact", "preference", "task", "context"],
                        "description": "Type of memory: 'note' for general notes, 'fact' for factual information, 'preference' for user preferences, 'task' for ongoing tasks, 'context' for conversation context"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorizing and finding this memory later (e.g., ['python', 'coding'], ['personal', 'hobbies'])"
                    },
                    "importance": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Importance score from 0.0 (trivial) to 1.0 (critical). Use 0.5 for normal importance."
                    }
                },
                "required": ["content", "memory_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_memories",
            "description": "Search for relevant memories. Use this to recall information from previous conversations or to check if something is already remembered.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keyword to search for in memory content (case-insensitive)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by specific tags"
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["note", "fact", "preference", "task", "context"],
                        "description": "Filter by memory type"
                    },
                    "min_importance": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Only return memories with importance >= this value"
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "description": "Maximum number of results to return (default: 10)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_memory",
            "description": "Retrieve a specific memory by its ID. Use this when you have a memory ID from a previous search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "The unique ID of the memory to retrieve"
                    }
                },
                "required": ["memory_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_memory",
            "description": "Update an existing memory. Use this to correct outdated information or add details to existing memories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "The unique ID of the memory to update"
                    },
                    "content": {
                        "type": "string",
                        "description": "New content (replaces existing content if provided)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New tags (replaces existing tags if provided)"
                    },
                    "importance": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "New importance score (replaces existing if provided)"
                    }
                },
                "required": ["memory_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_memory",
            "description": "Delete a memory that is no longer needed or is incorrect. Use this carefully as deletion is permanent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "The unique ID of the memory to delete"
                    }
                },
                "required": ["memory_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_memory_stats",
            "description": "Get statistics about the memory system (total entries, types, etc.). Useful for understanding what's stored.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


def execute_memory_tool(tool_name: str, arguments: Dict[str, Any], memory_manager) -> Dict[str, Any]:
    """
    Execute a memory tool function.

    Args:
        tool_name: Name of the tool function to execute
        arguments: Arguments for the function
        memory_manager: MemoryManager instance

    Returns:
        Dict with result or error information
    """
    try:
        # Get the first enabled memory name (usually "main_memory")
        memory_name = list(memory_manager.enabled_memories.keys())[0] if memory_manager.enabled_memories else "main_memory"

        if tool_name == "add_memory":
            result = memory_manager.add_memory(
                content=arguments.get('content'),
                memory_type=arguments.get('memory_type', 'note'),
                tags=arguments.get('tags'),
                importance=arguments.get('importance', 0.5),
                source='llm',
                memory_name=memory_name
            )
            return {
                "success": True,
                "memory_id": result.get('id'),
                "message": f"Memory stored successfully with ID: {result.get('id')}"
            }

        elif tool_name == "search_memories":
            results = memory_manager.search_memories(
                query=arguments.get('query'),
                tags=arguments.get('tags'),
                memory_type=arguments.get('memory_type'),
                min_importance=arguments.get('min_importance'),
                limit=arguments.get('limit', 10),
                memory_name=memory_name
            )
            return {
                "success": True,
                "count": len(results),
                "memories": results
            }

        elif tool_name == "get_memory":
            memory_id = arguments.get('memory_id')
            result = memory_manager.get_memory(memory_id, memory_name=memory_name)

            if result:
                return {
                    "success": True,
                    "memory": result
                }
            else:
                return {
                    "success": False,
                    "error": f"Memory with ID '{memory_id}' not found"
                }

        elif tool_name == "update_memory":
            memory_id = arguments.get('memory_id')
            success = memory_manager.update_memory(
                memory_id=memory_id,
                content=arguments.get('content'),
                tags=arguments.get('tags'),
                importance=arguments.get('importance'),
                memory_name=memory_name
            )

            if success:
                return {
                    "success": True,
                    "message": f"Memory '{memory_id}' updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to update memory '{memory_id}' (not found or error)"
                }

        elif tool_name == "delete_memory":
            memory_id = arguments.get('memory_id')
            success = memory_manager.delete_memory(memory_id, memory_name=memory_name)

            if success:
                return {
                    "success": True,
                    "message": f"Memory '{memory_id}' deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to delete memory '{memory_id}' (not found or error)"
                }

        elif tool_name == "get_memory_stats":
            stats = memory_manager.get_stats(memory_name=memory_name)
            return {
                "success": True,
                "stats": stats
            }

        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }

    except Exception as e:
        logger.error(f"Error executing memory tool '{tool_name}': {e}")
        return {
            "success": False,
            "error": str(e)
        }


# System prompt addition for memory awareness
MEMORY_SYSTEM_PROMPT = """
---

# Long-Term Memory

You have access to a long-term memory system that persists across conversations. Use this to remember important information, user preferences, ongoing tasks, and context.

## CRITICAL: Always Search Memory First

**IMPORTANT:** At the start of EVERY conversation or when the user asks a question, you MUST:
1. Use `search_memories` to check if you have relevant stored information about the user or topic
2. Use those memories to personalize your response and maintain continuity across conversations

Even if the user doesn't explicitly mention past conversations, check your memory for context!

## Memory Guidelines

**When to Remember:**
- User explicitly says "remember this" or "don't forget"
- Important facts about the user (name, preferences, background)
- Ongoing projects or tasks
- Significant decisions or conclusions
- User preferences and settings
- Corrections to your knowledge

**What NOT to Remember:**
- Temporary/ephemeral information
- Sensitive data (passwords, API keys, personal identifiable information)
- Every minor detail of every conversation
- Information the user explicitly asks you not to remember

**Memory Tools Available:**
- `search_memories`: **USE THIS FIRST** to find relevant past memories
- `add_memory`: Store new information
- `update_memory`: Update existing memories
- `delete_memory`: Remove outdated memories
- `get_memory_stats`: View memory statistics

**Best Practices:**
- **ALWAYS search memories at the start of conversations** to check for relevant context
- Tag memories appropriately for easy retrieval
- Set importance scores thoughtfully (0.5 = normal, 0.8+ = very important)
- Update memories when information changes rather than creating duplicates
- Delete memories that are no longer relevant or accurate
"""


def get_memory_system_prompt() -> str:
    """
    Get the system prompt text for memory awareness.

    Returns:
        System prompt text to be appended to user's system prompt
    """
    return MEMORY_SYSTEM_PROMPT
