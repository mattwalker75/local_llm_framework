# Memory System Debug Guide

## Quick Start - Testing Steps

Follow these exact steps to test memory and capture diagnostic logs:

### Step 1: Disable Memory (Start Fresh)
```bash
llf memory disable main_memory
llf memory list
```

Expected output:
```
Main Memory                    disabled
```

### Step 2: Enable Memory
```bash
llf memory enable main_memory
llf memory list --enabled
```

Expected output:
```
Main Memory                    enabled
```

### Step 3: Start Chat Session
```bash
llf chat
```

**NOTE**: The system automatically detects if tools are available and disables streaming when needed. You don't need any special flags!

### Step 4: Test Conversations

Type these two messages exactly:

**Message 1:**
```
Do you have a memory?
```

**Message 2:**
```
Remember that my name is Matt
```

### Step 5: Exit Chat
```
/exit
```

## Where Are the Logs?

### Console Output (Default)
By default, logs appear in your terminal/console with color coding:
- **Green** = INFO level logs (what we need)
- **Yellow** = WARNING
- **Red** = ERROR

### Save Logs to File (Recommended)
To capture logs to a file for easier sharing:

```bash
llf --log-file memory_test.log chat
```

This will:
- Display logs in console (colored)
- Save logs to `memory_test.log` (no colors, easier to read/share)

The log file will be created in your current directory.

## What to Look For in the Logs

### 1. Memory Initialization (Should See)
```
PROMPT_CONFIG: get_memory_manager() called
PROMPT_CONFIG: Memory manager exists, has_enabled_memories=True
PROMPT_CONFIG: Enabled memories: ['main_memory']
PROMPT_CONFIG: get_memory_tools() called
PROMPT_CONFIG: Returning 6 memory tools
```

**If you DON'T see this**, memory is disabled or not loading properly.

### 2. Tool Loading (Should See)
```
TOOL_CALLING: Loaded 6 tools from prompt config
TOOL_CALLING: Available tools: ['add_memory', 'search_memories', 'get_memory', 'update_memory', 'delete_memory', 'get_memory_stats']
TOOL_CALLING: Adding tools to API parameters with tool_choice='auto'
TOOL_CALLING: Sending 6 tools to LLM API
```

**If you DON'T see this**, tools aren't being passed to the API.

### 3. API Call (Should See)
```
TOOL_CALLING: Iteration 1 - Calling LLM API
TOOL_CALLING: API params keys: ['messages', 'stream', 'tools', 'tool_choice', 'model', 'temperature', ...]
TOOL_CALLING: Number of messages: 2
TOOL_CALLING: Has 'tools' param: True
TOOL_CALLING: Number of tools: 6
TOOL_CALLING: tool_choice: auto
```

**If `Has 'tools' param: False`**, something went wrong in tool loading.

### 4A. SUCCESS - LLM Uses Tools (Hope to See)
```
TOOL_CALLING: API response received
TOOL_CALLING: Response finish_reason: tool_calls
TOOL_CALLING: Response has content: False
TOOL_CALLING: Response has tool_calls: True
TOOL_CALLING: message.tool_calls value: [...]
TOOL_CALLING: ✓ LLM requested 1 tool call(s)!
TOOL_CALLING: [1/1] Tool: add_memory
TOOL_CALLING: [1/1] Raw arguments: {"content": "User's name is Matt", "memory_type": "fact", ...}
TOOL_CALLING: [1/1] Parsed arguments: {'content': "User's name is Matt", ...}
TOOL_CALLING: [1/1] Executing add_memory...
TOOL_CALLING: [1/1] Result: {'success': True, 'memory_id': 'mem_...', ...}
TOOL_CALLING: [1/1] Tool result added to conversation
```

**This means it's WORKING!** 🎉

### 4B. FAILURE - LLM Doesn't Use Tools (Problem)
```
TOOL_CALLING: API response received
TOOL_CALLING: Response finish_reason: stop
TOOL_CALLING: Response has content: True
TOOL_CALLING: Response has tool_calls: False
TOOL_CALLING: message.tool_calls value: None
TOOL_CALLING: No tool calls in response (normal text response)
```

**This means the LLM isn't using function calling.** This could be because:
1. The model doesn't support function calling
2. llama-server doesn't support function calling
3. The model doesn't recognize it should use tools

## Diagnostic Checklist

Use this checklist to diagnose the issue:

- [ ] Memory is enabled (`llf memory list --enabled` shows main_memory)
- [ ] Using `llf chat` (the system auto-detects tools and disables streaming)
- [ ] Logs show `PROMPT_CONFIG: Enabled memories: ['main_memory']`
- [ ] Logs show `TOOL_CALLING: Loaded 6 tools from prompt config`
- [ ] Logs show `TOOL_CALLING: Has 'tools' param: True`
- [ ] Logs show `TOOL_CALLING: Number of tools: 6`
- [ ] LLM server is running (check `ps aux | grep llama-server`)
- [ ] Model supports function calling (Qwen3-Coder should)
- [ ] llama-server version supports function calling (need recent build)

## Common Issues and Solutions

### Issue 1: No logs appear at all
**Solution**: Change log level to INFO in config
```bash
# Edit configs/config.json
"log_level": "INFO"   # Change from "ERROR"
```

### Issue 2: Memory manager not initializing
**Check**:
```bash
llf memory list
cat memory/memory_registry.json
```

**Solution**: Ensure `"enabled": true` in registry

### Issue 3: Tools not being loaded
**Logs show**: `TOOL_CALLING: No tools loaded (memory may be disabled)`

**Solution**: Check Step 2 above, ensure memory is enabled

### Issue 4: Tools sent but LLM doesn't use them
**Logs show**:
```
TOOL_CALLING: Has 'tools' param: True
...
TOOL_CALLING: message.tool_calls value: None
```

**Possible causes**:
1. **Model doesn't support function calling**
   - Solution: Try a model known to support it (GPT-4, Claude, Llama-3+)

2. **llama-server too old**
   - Solution: Update llama-server to latest version
   - Check: `llama-server --version`

3. **Model needs explicit prompting**
   - The system prompt includes instructions, but some models ignore them
   - Solution: Try asking explicitly "use your add_memory function to remember this"

## Sharing Logs with Support

If you need help, please provide:

1. **Full log output** from the chat session
2. **Memory status**: Output of `llf memory list`
3. **Server info**: Output of `llama-server --version` (if using local)
4. **Model info**: What model you're using (from `configs/config.json`)

### How to capture and share:

```bash
# Start with log file
llf --log-file memory_debug.log chat

# Run your test messages
# Exit chat

# View and share the log
cat memory_debug.log
```

Or save to timestamped file:
```bash
llf --log-file "memory_test_$(date +%Y%m%d_%H%M%S).log" chat
```

## Advanced: Verify Memory Storage Manually

After testing, check if anything was actually stored:

```bash
# Check memory file directly
cat memory/main_memory/memory.jsonl

# Check index
cat memory/main_memory/index.json

# Check metadata
cat memory/main_memory/metadata.json

# Use CLI to search
python -c "
from llf.memory_manager import MemoryManager
from llf.memory_tools import execute_memory_tool

manager = MemoryManager()
result = execute_memory_tool('search_memories', {'query': 'Matt'}, manager)
print(result)
"
```

## Test Results Interpretation

### ✅ Success Indicators
- Tools loaded and sent to API
- API response contains `tool_calls`
- Tool execution logs show success
- Memory file contains new entries
- LLM responds with confirmation after storing memory

### ⚠️ Partial Success
- Tools loaded but LLM doesn't use them
- Likely cause: Model or server limitation, not code issue

### ❌ Failure Indicators
- Tools not loaded (memory disabled)
- Tools not sent to API (integration issue)
- API errors or crashes
- Tool execution fails

## Next Steps Based on Results

### If Tools Are Being Used Successfully
🎉 **Memory system is working!** You can now:
- Use memory in your normal conversations
- Build additional tool categories
- Integrate with other features

### If Tools NOT Being Used (LLM Doesn't Call Them)
This is **NOT a code bug** - the infrastructure is working. The issue is:

**Option A: Use a different model**
- Try a model explicitly trained for function calling
- OpenAI GPT-4, Claude 3+, or Llama-3+ recommended

**Option B: Update llama-server**
```bash
cd ../llama.cpp
git pull
cmake --build build --config Release
```

**Option C: Wait for better local model support**
- Function calling support in local models is improving rapidly
- Check llama.cpp releases for updates

### If Tools Not Loading At All
This IS a code issue. Check:
1. Memory registry file exists and is valid JSON
2. Memory is enabled in registry
3. No errors in memory manager initialization

## Conclusion

The comprehensive logging will show you exactly where things are working or failing. Share the log output with the specific markers above, and we can diagnose the exact issue!
