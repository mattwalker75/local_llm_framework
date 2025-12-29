# Tool Execution Modes

## Overview

The Local LLM Framework supports different execution modes to balance streaming UX with tool calling accuracy. This feature addresses the fundamental incompatibility between streaming responses and tool execution.

## The Problem

**Streaming vs Tool Calling Incompatibility:**
- **Streaming**: Sends response chunks as they're generated (`"The"`, `" weather"`, `" is"`, `" sunny"`)
- **Tool Calling**: Requires complete JSON response (`{"tool_calls": [{"name": "get_weather", ...}]}`)

When memory tools are enabled, the LLM can make function calls to read/write data. However, these function calls cannot be streamed - they require the full JSON structure to be parsed.

**Previous Behavior:**
- When memory tools were enabled, streaming was automatically disabled
- User would see the full response appear all at once (poor UX)
- Memory operations would work correctly

## Solution: Configurable Execution Modes

The `tool_execution_mode` configuration parameter allows you to control how the framework handles this trade-off.

## Configuration

Add to `configs/config.json` under `llm_endpoint`:

```json
{
  "llm_endpoint": {
    "api_base_url": "http://127.0.0.1:8000/v1",
    "api_key": "EMPTY",
    "model_name": "Qwen/Qwen3-Coder-30B-A3B-Instruct-GGUF",
    "tools": {
      "xml_format": "enable"
    },
    "tool_execution_mode": "dual_pass_write_only"
  }
}
```

## Available Modes

### 1. `single_pass` (Default)

**How it works:**
- Makes a single LLM call
- Disables streaming when tools are available
- Full response appears at once

**Pros:**
- ✅ Always accurate
- ✅ Simple and predictable
- ✅ Memory reads work correctly

**Cons:**
- ❌ No streaming when memory enabled (poor UX)

**Best for:**
- When accuracy is more important than streaming UX
- Production environments requiring predictable behavior
- Applications where users expect non-streaming responses

**Example:**
```
User: "What's my name?"
[Pause while LLM thinks]
Assistant: "Your name is Matt." [appears all at once]
```

---

### 2. `dual_pass_write_only` (Recommended)

**How it works:**
- Automatically detects operation type:
  - **WRITE operations** ("Remember X"): Dual-pass execution
    - Pass 1: Stream acknowledgment to user
    - Pass 2: Execute with tools in background
  - **READ operations** ("What's my name?"): Single-pass with tools (accurate)
  - **GENERAL chat**: Stream only (no tools)

**Pros:**
- ✅ Streaming for write operations (good UX)
- ✅ Accurate for read operations (correct answers)
- ✅ Balanced approach - best of both worlds

**Cons:**
- ⚠️ 2x LLM calls for write operations (higher cost)
- ⚠️ Write operations may show acknowledgment before storage completes

**Best for:**
- Most use cases
- Interactive chat applications
- When users care about seeing responses stream

**Example:**
```
User: "Remember that I like pizza"
Assistant: "I'll remember that you like pizza." [streams in real-time]
[Background: Actually stores to memory]

User: "What do I like?"
[Pause while LLM retrieves from memory]
Assistant: "You like pizza." [accurate, from memory]
```

---

### 3. `dual_pass_all` (Advanced)

**How it works:**
- Always makes two LLM calls when tools are available:
  - Pass 1: Stream response to user (no tools)
  - Pass 2: Execute with tools in background

**Pros:**
- ✅ Always streams (best UX)

**Cons:**
- ❌ 2x LLM calls for all operations (highest cost)
- ❌ **Dangerous for reads**: User sees Pass 1 response (may be wrong), but Pass 2 retrieves actual data

**Best for:**
- Specific use cases where streaming is critical
- When you don't use memory reads, only writes
- Testing and experimentation

**Warning:**
```
User: "What's my name?"
Assistant: "I don't have that information." [streams, no memory access]
[Background: Pass 2 retrieves "Matt" from memory, but user never sees it]
```

This mode is **NOT recommended** for applications that read from memory.

---

## Operation Type Detection

The framework uses pattern matching to classify user messages:

### READ Operations
Patterns that retrieve information from memory:
- `"What's my name?"`
- `"Do you remember...?"`
- `"Can you recall...?"`
- `"Tell me about my preferences"`
- `"Show me my settings"`

### WRITE Operations
Patterns that store information to memory:
- `"Remember that..."`
- `"My name is..."`
- `"I like..."`
- `"Store this..."`
- `"Save my preference..."`

### GENERAL Operations
Everything else:
- `"Tell me a joke"`
- `"How's the weather?"`
- `"Explain quantum physics"`

## Implementation Details

### File Structure

```
llf/
├── config.py                 # Configuration loading with tool_execution_mode
├── operation_detector.py     # Pattern-based operation type detection
└── cli.py                   # Dual-pass execution logic

configs/
└── config.json              # User configuration with tool_execution_mode

tests/
├── test_config_tool_execution_mode.py  # Config tests
└── test_operation_detector.py          # Operation detection tests
```

### Code Flow (dual_pass_write_only mode)

```python
# 1. Detect operation type
operation_type = detect_operation_type(user_input)

# 2. Determine execution strategy
use_dual_pass = should_use_dual_pass(
    operation_type,
    config.tool_execution_mode,
    tools_available
)

# 3. Execute based on strategy
if use_dual_pass:
    # Pass 1: Stream for UX
    stream = runtime.chat(conversation_history, stream=True)
    for chunk in stream:
        print(chunk)

    # Pass 2: Execute with tools in background
    threading.Thread(
        target=lambda: runtime.chat(conversation_history, stream=False)
    ).start()

elif tools_available:
    # Single-pass with tools (accurate)
    response = runtime.chat(conversation_history, stream=False)
    print(response)

else:
    # Stream only (no tools)
    stream = runtime.chat(conversation_history, stream=True)
    for chunk in stream:
        print(chunk)
```

## Performance Considerations

### Cost Comparison (per message)

| Mode | READ Operations | WRITE Operations | GENERAL Chat |
|------|----------------|------------------|--------------|
| `single_pass` | 1 LLM call | 1 LLM call | 1 LLM call |
| `dual_pass_write_only` | 1 LLM call | **2 LLM calls** | 1 LLM call |
| `dual_pass_all` | **2 LLM calls** | **2 LLM calls** | 1 LLM call |

### Latency

- **Streaming modes**: User sees first token immediately
- **Non-streaming**: User waits for complete response
- **Dual-pass**: Background execution happens after user sees response

### Memory Usage

- Dual-pass modes run background thread for tool execution
- Minimal memory overhead (one additional chat call)

## Migration Guide

### From Default Behavior

If you're currently using memory without this configuration:

**Before:**
- Streaming automatically disabled when memory enabled
- All responses appear at once

**After (single_pass):**
- Same behavior, but now configurable

**After (dual_pass_write_only):**
- Write operations stream (better UX)
- Read operations work correctly (accurate)

### Configuration Steps

1. **Add to config.json:**
```json
{
  "llm_endpoint": {
    "tool_execution_mode": "dual_pass_write_only"
  }
}
```

2. **Test your use cases:**
```bash
# Enable memory
llf memory enable main_memory

# Test write operation (should stream)
> Remember that I like pizza

# Test read operation (should be accurate)
> What do I like?
```

3. **Adjust mode if needed:**
- Too much cost? → `single_pass`
- Want more streaming? → `dual_pass_all` (only if you don't read from memory)

## Troubleshooting

### Issue: Responses not streaming

**Check:**
1. Is `tool_execution_mode` set to `single_pass`?
2. Are you using a READ operation? (intentionally non-streaming)
3. Is memory disabled? (should stream by default)

**Solution:**
- For writes to stream: Use `dual_pass_write_only` or `dual_pass_all`
- For general chat: Disable memory or use mode that allows streaming

### Issue: Memory reads return wrong data

**Check:**
1. Are you using `dual_pass_all` mode?

**Solution:**
- Switch to `dual_pass_write_only` or `single_pass`
- `dual_pass_all` is not safe for memory reads

### Issue: High API costs

**Check:**
1. Are you using `dual_pass_all` mode?
2. How many write operations are you performing?

**Solution:**
- Switch to `dual_pass_write_only` (only doubles writes)
- Switch to `single_pass` (never doubles calls)

## Future Enhancements

Potential improvements being considered:

1. **Custom patterns**: Allow users to define their own READ/WRITE patterns
2. **Per-tool modes**: Different execution modes for different tools
3. **Cost tracking**: Monitor LLM call costs in dual-pass modes
4. **Smart detection**: Use LLM to classify operation type instead of regex
5. **Streaming tool results**: Future LLM APIs may support streaming with tools

## Examples

### Example 1: Personal Assistant

```json
{
  "llm_endpoint": {
    "tool_execution_mode": "dual_pass_write_only"
  }
}
```

**Interaction:**
```
User: "Remember that my birthday is June 15th"
Assistant: "I'll remember that your birthday is June 15th." [streams]

User: "When is my birthday?"
[Short pause]
Assistant: "Your birthday is June 15th." [accurate from memory]

User: "Tell me a joke"
Assistant: "Why did the... [streams naturally]
```

### Example 2: Data Entry System (Write-Heavy)

```json
{
  "llm_endpoint": {
    "tool_execution_mode": "dual_pass_write_only"
  }
}
```

**Good fit** - lots of writes, occasional reads, streaming improves UX

### Example 3: Q&A System (Read-Heavy)

```json
{
  "llm_endpoint": {
    "tool_execution_mode": "single_pass"
  }
}
```

**Good fit** - accuracy matters more than streaming for factual answers

### Example 4: Chat Bot (No Memory)

```json
{
  "llm_endpoint": {
    "tool_execution_mode": "single_pass"
  }
}
```

**Note:** If memory is disabled, mode doesn't matter - will always stream

## References

- Configuration: [llf/config.py](../llf/config.py)
- Operation Detection: [llf/operation_detector.py](../llf/operation_detector.py)
- CLI Implementation: [llf/cli.py](../llf/cli.py)
- Tests: [tests/test_operation_detector.py](../tests/test_operation_detector.py)
