# Prompt Configuration Examples

This directory contains example prompt configurations that control how messages are formatted and enhanced when sent to LLMs.

## Overview

Prompt configurations are separate from infrastructure configuration (`config.json`) and focus purely on **how you communicate with the LLM**. They allow you to:

- Add system prompts that define the LLM's role and behavior
- Include master prompts with overarching guidelines
- Inject prefix/suffix messages into every conversation
- Prime the assistant with specific response patterns
- Create consistent conversation formats across all interactions

## Quick Start

Copy an example to `config_prompt.json` in the project root:

```bash
# Minimal configuration (no prompt enhancements)
cp config_prompt_examples/config_prompt.minimal.json config_prompt.json

# Helpful assistant personality
cp config_prompt_examples/config_prompt.helpful_assistant.json config_prompt.json

# Coding assistant with best practices
cp config_prompt_examples/config_prompt.coding_assistant.json config_prompt.json

# Creative writing assistant
cp config_prompt_examples/config_prompt.creative_writer.json config_prompt.json

# Structured conversation format
cp config_prompt_examples/config_prompt.structured_conversation.json config_prompt.json

# Socratic tutoring approach
cp config_prompt_examples/config_prompt.socratic_tutor.json config_prompt.json
```

The framework automatically loads `config_prompt.json` if it exists. If the file doesn't exist, no prompt enhancements are applied (raw messages only).

---

## Available Configurations

### 1. config_prompt.minimal.json

**Use case**: No prompt enhancements - send raw messages to the LLM

**What it does**:
- All prompt fields set to `null`
- Messages sent exactly as provided
- Most direct communication with the LLM

**When to use**:
- You want complete control over every message
- Testing LLM behavior without any system prompts
- You're building your own prompt system

**Example**:
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

### 2. config_prompt.helpful_assistant.json

**Use case**: General-purpose helpful assistant

**What it does**:
- Sets a system prompt defining the assistant as helpful, friendly, and knowledgeable
- Encourages clear, accurate, and concise responses
- No additional formatting or conversation structure

**When to use**:
- General Q&A and information requests
- Default assistant personality
- Balanced between helpful and concise

**System Prompt**:
> "You are a helpful, friendly, and knowledgeable assistant. Provide clear, accurate, and concise responses to user questions."

---

### 3. config_prompt.coding_assistant.json

**Use case**: Software development and coding tasks

**What it does**:
- System prompt: Defines assistant as expert software engineer
- Master prompt: Guidelines for code examples (comments, best practices, edge cases)
- Suffix messages: Reminder about code formatting with syntax highlighting

**When to use**:
- Writing or reviewing code
- Debugging problems
- Learning programming concepts
- System design discussions

**Key Features**:
- Emphasizes code comments and explanation
- Considers edge cases and error handling
- Suggests optimizations
- Follows language-specific best practices

---

### 4. config_prompt.creative_writer.json

**Use case**: Creative writing and storytelling

**What it does**:
- System prompt: Defines expertise in storytelling and literary genres
- Master prompt: Guidelines for character development, plot, pacing
- Assistant prompt: Primes responses with encouraging, collaborative tone

**When to use**:
- Writing fiction, poetry, or creative content
- Developing story ideas and characters
- Getting feedback on creative work
- Exploring narrative techniques

**Assistant Priming**:
> "I'm here to help bring your creative vision to life. What aspect of your writing would you like to explore?"

---

### 5. config_prompt.structured_conversation.json

**Use case**: Structured, consistent response format

**What it does**:
- Master prompt: Defines 4-part response structure
  1. Understanding (confirm the question)
  2. Answer (provide solution)
  3. Explanation (reasoning/context)
  4. Next Steps (follow-up suggestions)
- Prefix messages: Maintains professional yet friendly tone

**When to use**:
- Business communications
- Technical documentation
- Educational content
- Situations requiring consistent formatting

**Response Structure**:
Every response follows the same pattern for clarity and completeness.

---

### 6. config_prompt.socratic_tutor.json

**Use case**: Teaching and learning through guided discovery

**What it does**:
- System prompt: Defines Socratic teaching methodology
- Master prompt: Guidelines for asking leading questions
- Assistant prompt: Opens with collaborative question
- Suffix messages: Reminder to guide rather than tell

**When to use**:
- Learning new concepts
- Developing problem-solving skills
- Teaching or tutoring scenarios
- Situations where understanding the "why" is important

**Teaching Philosophy**:
- Guide learners to discover answers themselves
- Ask clarifying questions
- Build on existing knowledge
- Only provide direct answers when truly stuck

---

## Configuration Structure

All prompt configurations use this JSON structure:

```json
{
  "system_prompt": "High-level role and behavior definition",
  "master_prompt": "Overarching guidelines and context",
  "assistant_prompt": "Prime the assistant's response",
  "conversation_format": "standard|structured|custom",
  "prefix_messages": [
    {"role": "system", "content": "Injected before user message"}
  ],
  "suffix_messages": [
    {"role": "system", "content": "Injected after user message"}
  ],
  "custom_format": {
    "additional": "Custom formatting rules (optional)"
  }
}
```

### Field Descriptions

| Field | Type | Purpose |
|-------|------|---------|
| `system_prompt` | string or null | Defines the LLM's role, personality, and high-level behavior |
| `master_prompt` | string or null | Overarching guidelines that apply to all responses |
| `assistant_prompt` | string or null | Primes the assistant to respond in a certain way |
| `conversation_format` | string | Hints at the type of conversation (standard, structured, custom) |
| `prefix_messages` | array | Messages injected **before** the user's message in every request |
| `suffix_messages` | array | Messages injected **after** the user's message in every request |
| `custom_format` | object or null | Additional custom formatting rules (reserved for future use) |

---

## How Prompt Configs Work

When you send a message to the LLM with prompt configuration enabled:

**Your input**:
```python
messages = [{"role": "user", "content": "What is Python?"}]
```

**What gets sent to the LLM** (example with coding_assistant config):
```python
[
  {"role": "system", "content": "You are an expert software engineer..."},
  {"role": "system", "content": "When providing code examples:\n- Always include clear comments..."},
  {"role": "user", "content": "What is Python?"},
  {"role": "system", "content": "Remember to format code blocks with proper syntax highlighting..."}
]
```

The framework automatically:
1. Adds system prompts at the beginning
2. Preserves conversation history (if any)
3. Injects prefix messages before your message
4. Adds your user message
5. Injects suffix messages after your message
6. Adds assistant prompt (if configured) to prime the response

---

## Creating Custom Prompt Configurations

To create your own prompt configuration:

1. **Copy an example**:
   ```bash
   cp config_prompt_examples/config_prompt.minimal.json my_custom_prompt.json
   ```

2. **Edit the fields**:
   ```json
   {
     "system_prompt": "You are an expert in...",
     "master_prompt": "Guidelines:\n- Guideline 1\n- Guideline 2",
     "assistant_prompt": "I'm ready to help with...",
     "conversation_format": "standard",
     "prefix_messages": [],
     "suffix_messages": []
   }
   ```

3. **Use it**:
   ```bash
   # Copy to default location
   cp my_custom_prompt.json config_prompt.json

   # Or use programmatically
   from llf.prompt_config import PromptConfig
   config = PromptConfig("my_custom_prompt.json")
   ```

---

## Tips for Writing Effective Prompts

### System Prompts
- **Be specific**: "You are an expert Python developer" > "You are helpful"
- **Define boundaries**: Clarify what the assistant should/shouldn't do
- **Set tone**: Professional, friendly, concise, creative, etc.

### Master Prompts
- **Provide guidelines**: Format rules, response structure, quality standards
- **List priorities**: What's most important in responses
- **Give examples**: Show the desired behavior

### Prefix/Suffix Messages
- **Prefix**: Context that applies to every message (like "Be concise")
- **Suffix**: Reminders or formatting instructions
- **Keep them short**: They're added to every request

### Assistant Prompts
- **Prime the tone**: Start the assistant's response pattern
- **Set expectations**: "Let's explore this step by step..."
- **Be natural**: Write how you want the assistant to begin responding

---

## Switching Between Configurations

You can easily switch prompt configurations based on your task:

```bash
# Morning: General Q&A
cp config_prompt_examples/config_prompt.helpful_assistant.json config_prompt.json

# Afternoon: Coding session
cp config_prompt_examples/config_prompt.coding_assistant.json config_prompt.json

# Evening: Creative writing
cp config_prompt_examples/config_prompt.creative_writer.json config_prompt.json

# Or keep multiple configs and switch programmatically
```

---

## Relationship to config.json

**Infrastructure config (`config.json`)**:
- Server settings, API endpoints, models
- Inference parameters (temperature, max_tokens)
- File paths and directories

**Prompt config (`config_prompt.json`)**:
- How to communicate with the LLM
- System prompts and conversation structure
- Message formatting and enhancement

These are **completely separate** concerns:
- You can change prompt behavior without changing your server setup
- You can switch LLM providers without changing your prompts
- They work together: infrastructure delivers messages, prompts shape them

---

## Disabling Prompt Configuration

To send raw messages without any prompt enhancements:

**Option 1**: Don't create `config_prompt.json` (default behavior)

**Option 2**: Use minimal configuration:
```bash
cp config_prompt_examples/config_prompt.minimal.json config_prompt.json
```

**Option 3**: Disable in code:
```python
runtime.chat(messages, use_prompt_config=False)
```

---

## Advanced: Prompt Config in Code

### Loading Configuration

```python
from llf.prompt_config import PromptConfig, get_prompt_config

# Load from default location (config_prompt.json)
prompt_config = get_prompt_config()

# Load from specific file
from pathlib import Path
prompt_config = PromptConfig(Path("my_prompts.json"))
```

### Building Messages

```python
# Simple message
messages = prompt_config.build_messages("What is Python?")

# With conversation history
history = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
]
messages = prompt_config.build_messages("How are you?", conversation_history=history)
```

### Using with LLMRuntime

```python
from llf.llm_runtime import LLMRuntime
from llf.prompt_config import PromptConfig

# Initialize runtime with prompt config
prompt_config = PromptConfig("config_prompt.json")
runtime = LLMRuntime(config, model_manager, prompt_config)

# Prompt config is automatically applied
response = runtime.chat([{"role": "user", "content": "Hello"}])

# Or disable it for specific requests
response = runtime.chat(messages, use_prompt_config=False)
```

---

## Examples in Practice

### Example 1: Teaching Session

**Config**: `config_prompt.socratic_tutor.json`

**User**: "What is recursion?"

**LLM Response** (guided discovery):
> "Great question! Let's explore this together. What do you already know about functions calling other functions?"

---

### Example 2: Code Review

**Config**: `config_prompt.coding_assistant.json`

**User**: "Review this function: [code]"

**LLM Response** (structured with best practices):
> "I'll review this code focusing on correctness, efficiency, and best practices.
>
> **Correctness**: The function handles the happy path correctly...
>
> **Edge Cases**: Consider what happens when...
>
> **Suggested Improvements**:
> 1. Add error handling for...
> 2. Extract this into a helper function...
> ```python
> # Improved version with error handling
> def improved_function(data):
>     # Clear comment explaining logic
>     ...
> ```"

---

### Example 3: Structured Business Response

**Config**: `config_prompt.structured_conversation.json`

**User**: "How do I implement OAuth in my app?"

**LLM Response** (follows 4-part structure):
> **Understanding**: You want to add OAuth authentication to your application.
>
> **Answer**: The process involves registering with an OAuth provider, implementing the authorization flow, and handling tokens securely.
>
> **Explanation**: OAuth 2.0 uses authorization grants to obtain access tokens without exposing user credentials...
>
> **Next Steps**:
> 1. Choose an OAuth provider (Google, GitHub, etc.)
> 2. Register your application to get client credentials
> 3. Implement the authorization code flow
>
> Would you like me to walk through a specific OAuth provider implementation?

---

## Troubleshooting

**Prompt config not being applied**:
- Check that `config_prompt.json` exists in project root
- Verify JSON syntax is valid
- Ensure `use_prompt_config=True` (default)

**Messages too long**:
- Reduce prefix/suffix messages
- Shorten system and master prompts
- Consider token limits of your LLM

**Responses don't match expected format**:
- LLMs may not always follow instructions perfectly
- Make prompts more explicit and specific
- Consider using examples in master prompt
- Try different temperature settings in `config.json`

---

## Security Notes

**Never include sensitive information in prompt configs**:
- No API keys or credentials
- No personal or confidential data
- Prompt configs may be shared or committed to version control

**The `.gitignore` already excludes**:
- `config_prompt.json` (your actual config)

**But allows**:
- `config_prompt_examples/*.json` (safe templates)

---

For more information, see:
- [Main README](../README.md)
- [Infrastructure Configuration Guide](../config_examples/README.md)
- [PromptConfig API Documentation](../llf/prompt_config.py)
