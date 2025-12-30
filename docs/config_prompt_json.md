# Prompt Configuration Guide: config_prompt.json

This document explains how to configure LLM prompts and conversation formatting using the `configs/config_prompt.json` file.

**Last Updated:** 2025-12-28

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Structure](#configuration-structure)
3. [Parameters Reference](#parameters-reference)
4. [Message Flow](#message-flow)
5. [Configuration Examples](#configuration-examples)
6. [Use Cases](#use-cases)
7. [Best Practices](#best-practices)

---

## Overview

The `config_prompt.json` file controls how prompts are structured and sent to the LLM. It allows you to:

- Define system-level instructions for the LLM
- Set the LLM's persona and behavior
- Add custom messages before/after user input
- Configure conversation formatting
- Integrate with RAG (Retrieval-Augmented Generation) automatically
- Integrate with memory system automatically

**Location:** `configs/config_prompt.json`

---

## Configuration Structure

A minimal configuration looks like this:

```json
{
  "system_prompt": null,
  "master_prompt": null,
  "assistant_prompt": null,
  "conversation_format": "standard",
  "prefix_messages": [],
  "suffix_messages": []
}
```

---

## Parameters Reference

### Core Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `system_prompt` | String or null | No | `null` | High-level instructions sent as the first system message |
| `master_prompt` | String or null | No | `null` | Additional system-level guidelines sent after `system_prompt` |
| `assistant_prompt` | String or null | No | `null` | Primes the assistant's response style (added as assistant message) |
| `conversation_format` | String | No | `"standard"` | Conversation format type (currently only `"standard"` is supported) |
| `prefix_messages` | Array | No | `[]` | Messages injected before the user's message |
| `suffix_messages` | Array | No | `[]` | Messages injected after the user's message |
| `custom_format` | Object or null | No | `null` | Reserved for future custom formatting rules |

---

## Message Flow

When you send a message to the LLM, the framework builds the complete message list in this order:

```
1. system_prompt (if configured)
   ↓
2. RAG context (if vector stores attached)
   ↓
3. Memory system instructions (if memory enabled)
   ↓
4. master_prompt (if configured)
   ↓
5. conversation_history (previous messages)
   ↓
6. prefix_messages (if configured)
   ↓
7. user_message (your input)
   ↓
8. suffix_messages (if configured)
   ↓
9. assistant_prompt (if configured)
```

### Automatic Integrations

The framework automatically adds:

**RAG Context** - If any data stores are attached (`attached: true` in [data_store_registry.json](data_store_registry_json.md)):
- Queries all attached vector stores with the user's message
- Retrieves relevant context
- Adds it to the system prompt with instructions

**Memory Instructions** - If any memory instances are enabled (`enabled: true` in [memory_registry.json](memory_registry_json.md)):
- Loads memory tool definitions
- Adds memory system instructions to the prompt
- Enables the LLM to call memory functions

You don't need to configure anything in `config_prompt.json` for these features - they activate automatically based on the respective registry files.

---

## Parameters Reference (Detailed)

### `system_prompt`

**Type:** String or null
**Purpose:** Define the LLM's core identity and capabilities

The system prompt is the first message sent to the LLM. It sets the overall context and behavior.

**Example:**
```json
{
  "system_prompt": "You are a helpful AI assistant specialized in Python programming."
}
```

**Notes:**
- Use `null` for minimal/default behavior
- Keep it concise and focused
- RAG context and memory instructions are automatically appended if applicable

---

### `master_prompt`

**Type:** String or null
**Purpose:** Add overarching guidelines or constraints

The master prompt provides additional system-level instructions that apply to all interactions.

**Example:**
```json
{
  "master_prompt": "When providing code examples:\n- Always include clear comments\n- Follow PEP 8 style guide\n- Consider edge cases and error handling"
}
```

**Notes:**
- Sent as a separate system message after `system_prompt`
- Useful for setting formatting rules or behavioral guidelines
- Can include newlines using `\n` for structured instructions

---

### `assistant_prompt`

**Type:** String or null
**Purpose:** Prime the assistant's response style

The assistant prompt is added as an assistant message at the end of the conversation. The LLM will continue from this point.

**Example:**
```json
{
  "assistant_prompt": "I'll help you with that. Let me provide a detailed explanation:"
}
```

**Notes:**
- Useful for controlling response format
- Added after the user's message
- Can establish a consistent tone or structure

**Warning:** Use sparingly - this adds tokens to every request and may produce unexpected results with some models.

---

### `conversation_format`

**Type:** String
**Purpose:** Specify conversation formatting style

Currently, only `"standard"` format is supported, which uses OpenAI's chat completion format.

**Example:**
```json
{
  "conversation_format": "standard"
}
```

**Notes:**
- Reserved for future formatting options
- Always use `"standard"` for now

---

### `prefix_messages`

**Type:** Array of message objects
**Purpose:** Add messages before the user's input

Prefix messages are injected before the user's message in every conversation.

**Format:**
```json
{
  "prefix_messages": [
    {
      "role": "system",
      "content": "Today's date is 2025-12-28."
    },
    {
      "role": "user",
      "content": "Remember to follow the coding standards."
    }
  ]
}
```

**Message Object Structure:**
- `role`: `"system"`, `"user"`, or `"assistant"`
- `content`: The message text

**Use Cases:**
- Add current date/time information
- Inject context-specific reminders
- Provide session-specific instructions

---

### `suffix_messages`

**Type:** Array of message objects
**Purpose:** Add messages after the user's input

Suffix messages are injected after the user's message but before the assistant responds.

**Format:**
```json
{
  "suffix_messages": [
    {
      "role": "system",
      "content": "Remember to format code blocks with proper syntax highlighting."
    }
  ]
}
```

**Use Cases:**
- Add formatting reminders
- Inject tool usage instructions
- Provide response guidelines

---

## Configuration Examples

### Example 1: Minimal Configuration

No special prompts - let the LLM use its default behavior:

```json
{
  "system_prompt": null,
  "master_prompt": null,
  "assistant_prompt": null,
  "conversation_format": "standard",
  "prefix_messages": [],
  "suffix_messages": []
}
```

---

### Example 2: Coding Assistant

Configure the LLM as an expert programmer:

```json
{
  "system_prompt": "You are an expert software engineer and coding assistant with deep knowledge of programming languages, frameworks, best practices, and software design patterns.",
  "master_prompt": "When providing code examples:\n- Always include clear comments explaining the logic\n- Follow language-specific best practices and conventions\n- Consider edge cases and error handling\n- Suggest optimizations when relevant\n- Explain the reasoning behind your implementation choices",
  "assistant_prompt": null,
  "conversation_format": "standard",
  "prefix_messages": [],
  "suffix_messages": [
    {
      "role": "system",
      "content": "Remember to format code blocks with proper syntax highlighting using markdown code fences."
    }
  ]
}
```

**See:** [`configs/config_prompt_examples/config_prompt.coding_assistant.json`](../configs/config_prompt_examples/config_prompt.coding_assistant.json)

---

### Example 3: Creative Writer

Configure the LLM as a creative writing partner:

```json
{
  "system_prompt": "You are a creative writing assistant specializing in fiction, poetry, and storytelling. You help writers develop ideas, overcome writer's block, and refine their prose.",
  "master_prompt": "When assisting with creative writing:\n- Ask clarifying questions to understand the writer's vision\n- Provide specific, actionable suggestions\n- Respect the writer's voice and style\n- Offer multiple alternatives when appropriate\n- Balance encouragement with constructive feedback",
  "assistant_prompt": null,
  "conversation_format": "standard",
  "prefix_messages": [],
  "suffix_messages": []
}
```

**See:** [`configs/config_prompt_examples/config_prompt.creative_writer.json`](../configs/config_prompt_examples/config_prompt.creative_writer.json)

---

### Example 4: Socratic Tutor

Configure the LLM to teach through questions:

```json
{
  "system_prompt": "You are a Socratic tutor who guides students to discover answers through thoughtful questioning rather than directly providing solutions.",
  "master_prompt": "Teaching approach:\n- Ask leading questions that encourage critical thinking\n- Build on the student's existing knowledge\n- Use analogies and examples to illustrate concepts\n- Encourage students to explain their reasoning\n- Provide hints rather than answers\n- Celebrate progress and learning moments",
  "assistant_prompt": null,
  "conversation_format": "standard",
  "prefix_messages": [
    {
      "role": "system",
      "content": "Guide the student through discovery, don't give away the answer immediately."
    }
  ],
  "suffix_messages": []
}
```

**See:** [`configs/config_prompt_examples/config_prompt.socratic_tutor.json`](../configs/config_prompt_examples/config_prompt.socratic_tutor.json)

---

### Example 5: Structured Conversation

Add consistent structure to all responses:

```json
{
  "system_prompt": "You are a professional business analyst who provides structured analysis and recommendations.",
  "master_prompt": null,
  "assistant_prompt": "I'll analyze this systematically:\n\n## Analysis\n",
  "conversation_format": "standard",
  "prefix_messages": [],
  "suffix_messages": [
    {
      "role": "system",
      "content": "Structure your response with clear sections: Analysis, Key Findings, Recommendations."
    }
  ]
}
```

**See:** [`configs/config_prompt_examples/config_prompt.structured_conversation.json`](../configs/config_prompt_examples/config_prompt.structured_conversation.json)

---

## Use Cases

### 1. Role-Based Personas

Use `system_prompt` to define the LLM's role:

```json
{
  "system_prompt": "You are a senior DevOps engineer with expertise in Kubernetes, Docker, and cloud infrastructure."
}
```

### 2. Response Formatting Rules

Use `master_prompt` for consistent formatting:

```json
{
  "master_prompt": "Always:\n- Start with a brief summary\n- Use bullet points for lists\n- Include code examples when relevant\n- End with actionable next steps"
}
```

### 3. Context Injection

Use `prefix_messages` to add dynamic context:

```json
{
  "prefix_messages": [
    {
      "role": "system",
      "content": "The user is working on a React project with TypeScript and Tailwind CSS."
    }
  ]
}
```

### 4. Response Priming

Use `assistant_prompt` to establish response patterns:

```json
{
  "assistant_prompt": "Let me break this down step by step:\n\n1. "
}
```

---

## Best Practices

### General Guidelines

1. **Keep It Simple**: Start with minimal configuration and add complexity only when needed
2. **Be Specific**: Clear, specific instructions work better than vague guidelines
3. **Test Incrementally**: Change one parameter at a time to see its effect
4. **Avoid Contradictions**: Ensure `system_prompt`, `master_prompt`, and other messages don't conflict

### Performance Considerations

1. **Token Usage**: Every message in `prefix_messages` and `suffix_messages` adds tokens to every request
2. **Keep Prompts Concise**: Longer prompts cost more and may dilute focus
3. **Use `null` When Unnecessary**: Empty strings still consume tokens - use `null` instead

### Prompt Engineering Tips

1. **System Prompt**: Define "what" the LLM is
2. **Master Prompt**: Define "how" the LLM should behave
3. **Suffix Messages**: Add last-minute reminders or formatting rules
4. **Assistant Prompt**: Prime the response format (use sparingly)

### Common Patterns

**For Coding Assistants:**
- Use `system_prompt` to establish expertise
- Use `master_prompt` for code quality guidelines
- Use `suffix_messages` for formatting reminders

**For Creative Work:**
- Use `system_prompt` to define creative role
- Use `master_prompt` for stylistic guidelines
- Avoid `assistant_prompt` (reduces creative freedom)

**For Teaching:**
- Use `system_prompt` to establish teaching philosophy
- Use `master_prompt` for pedagogical approach
- Use `prefix_messages` for session-specific context

---

## Advanced Features

### Automatic RAG Integration

When you attach data stores (set `attached: true` in [data_store_registry.json](data_store_registry_json.md)), the framework automatically:

1. Queries all attached vector stores with the user's message
2. Retrieves relevant context
3. Adds RAG context to the system prompt:

```
---

# Knowledge Base Context

The following information has been retrieved from attached knowledge bases...

[Retrieved context here]

# RAG Instructions

- Use the context above when it's relevant to the user's question
- Cite specific information from the context when applicable
- If the context doesn't contain relevant information, rely on your general knowledge
```

**You don't need to configure this** - it happens automatically when stores are attached.

### Automatic Memory Integration

When you enable memory (set `enabled: true` in [memory_registry.json](memory_registry_json.md)), the framework automatically:

1. Loads memory tool definitions
2. Adds memory system instructions to the prompt
3. Enables the LLM to call memory functions (`add_memory`, `search_memories`, `get_memory`, `update_memory`, `delete_memory`)

**You don't need to configure this** - it happens automatically when memory is enabled.

---

## Troubleshooting

### Prompts Not Taking Effect

**Problem:** Changes to `config_prompt.json` aren't reflected in LLM responses

**Solutions:**
1. Restart the framework to reload configuration
2. In GUI mode, use the "Reload Config" button
3. Check for JSON syntax errors (use a JSON validator)
4. Verify the file is saved in the correct location (`configs/config_prompt.json`)

### Conflicting Instructions

**Problem:** LLM seems confused or ignores some instructions

**Solutions:**
1. Check for contradictions between `system_prompt` and `master_prompt`
2. Ensure `prefix_messages` and `suffix_messages` don't conflict
3. Simplify configuration - remove one prompt type and test
4. Be more explicit and specific in instructions

### High Token Usage

**Problem:** API costs are too high or context window is filling up

**Solutions:**
1. Shorten `system_prompt` and `master_prompt`
2. Remove unnecessary `prefix_messages` and `suffix_messages`
3. Use `null` instead of empty strings
4. Consider using `assistant_prompt` only when essential

---

## Related Documentation

- [Main Configuration](config_json.md) - LLM endpoint and server configuration
- [Data Store Registry](data_store_registry_json.md) - RAG vector store configuration
- [Memory Registry](memory_registry_json.md) - Memory system configuration
- [Tools Registry](tools_registryi_json.md) - Tool system configuration

---

## Example Files

Pre-configured examples are available in `configs/config_prompt_examples/`:
- [config_prompt.minimal.json](../configs/config_prompt_examples/config_prompt.minimal.json) - Bare minimum configuration
- [config_prompt.helpful_assistant.json](../configs/config_prompt_examples/config_prompt.helpful_assistant.json) - General-purpose assistant
- [config_prompt.coding_assistant.json](../configs/config_prompt_examples/config_prompt.coding_assistant.json) - Programming expert
- [config_prompt.creative_writer.json](../configs/config_prompt_examples/config_prompt.creative_writer.json) - Creative writing partner
- [config_prompt.socratic_tutor.json](../configs/config_prompt_examples/config_prompt.socratic_tutor.json) - Teaching through questions
- [config_prompt.structured_conversation.json](../configs/config_prompt_examples/config_prompt.structured_conversation.json) - Structured responses

---

For additional help, refer to the main [README.md](../README.md) or open an issue on GitHub.
