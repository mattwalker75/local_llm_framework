# CLI Mode Implementation Summary

## Overview
Added non-interactive CLI mode to the LLF chat command, enabling single-question scripting capability. This allows users to interact with the LLM from shell scripts without entering interactive mode.

## User Request
> "Lets add the functionality to allow the ability to pass in your question to the LLM via a command line parameter. This would mean you do not have to go into an interactive prompt engagement with the LLM. This would enable the ability to interact with the LLM via an automated script. Maybe do something like this: llf chat --cli \"YOUR QUESTION HERE\". It would be good to have it also support the existing auto server start, no server start, and model flag like it currently does for the interactive method. Obviously with the CLI method, you can not do a streaming response, which is fine. Still want to keep the streaming response for interactive mode. Remember to update all unit tests when complete"

## Implementation Details

### 1. New CLI Argument
Added `--cli QUESTION` argument to the chat command:
- **File**: `llf/cli.py`
- **Location**: Lines 688-692
- **Purpose**: Accept a single question for non-interactive mode

```python
chat_parser.add_argument(
    '--cli',
    metavar='QUESTION',
    help='Non-interactive mode: ask a single question and exit (for scripting)'
)
```

### 2. CLI Question Handler Method
Created `cli_question()` method in the CLI class:
- **File**: `llf/cli.py`
- **Location**: Lines 288-321
- **Purpose**: Handle non-interactive question processing
- **Behavior**:
  - Ensures model is ready
  - Starts server (respects auto-start/no-start flags)
  - Sends question to LLM with `stream=False`
  - Prints response and exits
  - Returns 0 on success, 1 on failure

```python
def cli_question(self, question: str) -> int:
    """Handle non-interactive CLI question mode."""
    try:
        if not self.ensure_model_ready():
            return 1
        if not self.start_server():
            return 1

        messages = [{'role': 'user', 'content': question}]
        response = self.runtime.chat(messages, stream=False)  # NO streaming
        console.print(response)
        return 0
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1
```

### 3. Modified Run Method
Updated `run()` method to support CLI mode:
- **File**: `llf/cli.py`
- **Location**: Lines 328-357
- **Changes**:
  - Added `cli_question` parameter (Optional[str])
  - Routes to `cli_question()` if parameter provided
  - Otherwise uses interactive mode as before

```python
def run(self, cli_question: Optional[str] = None) -> int:
    try:
        # CLI mode: single question and exit
        if cli_question:
            return self.cli_question(cli_question)

        # Interactive mode
        self.print_welcome()
        # ... rest of interactive mode
```

### 4. Main Function Integration
Updated `main()` to pass --cli argument to CLI.run():
- **File**: `llf/cli.py`
- **Location**: Lines 788-802
- **Changes**:
  - Extract `cli_question` from args
  - Pass to `cli.run(cli_question=cli_question)`

```python
# Get CLI question if provided
cli_question = getattr(args, 'cli', None)

# Default to chat
cli = CLI(config, auto_start_server=auto_start, no_server_start=no_start)
return cli.run(cli_question=cli_question)
```

## Test Coverage

### New Test Class: TestCLIQuestionMode
Added 10 comprehensive unit tests:

1. **test_cli_question_basic**: Basic CLI question functionality
   - Verifies message structure
   - Confirms `stream=False` is used

2. **test_cli_question_model_not_ready**: Model not ready error handling

3. **test_cli_question_server_fails**: Server start failure handling

4. **test_cli_question_chat_error**: Chat API error handling

5. **test_run_with_cli_question**: Run method routes to CLI mode correctly

6. **test_run_without_cli_question**: Run method still uses interactive mode when no CLI question

7. **test_main_with_cli_argument**: Main function integration with --cli

8. **test_main_with_cli_and_model**: CLI mode with --model flag

9. **test_main_with_cli_and_auto_start**: CLI mode with --auto-start-server flag

10. **test_main_with_cli_and_no_server_start**: CLI mode with --no-server-start flag

### Test Results
- **Total Tests**: 119 (previously 109)
- **New Tests**: 10
- **All Passing**: ✓
- **Coverage**: 88% (maintained)

## Documentation Updates

### Main Help Menu (llf -h / llf --help)
Updated main help examples to include CLI mode:
- **File**: `llf/cli.py`
- **Location**: Lines 591-603
- Added section "# CLI mode (non-interactive, for scripting)" with three examples:
  - `llf chat --cli "What is 2+2?"` - Basic usage
  - `llf chat --cli "Explain Python" --auto-start-server` - With auto-start
  - `llf chat --cli "Code review" --model custom/model` - With model selection

### QUICK_REFERENCE.md
Added new sections:

1. **Chat Modes**: Documents both interactive and CLI modes
2. **Examples**: Shows CLI mode usage patterns including:
   - Basic usage: `llf chat --cli "question"`
   - With auto-start: `llf chat --cli "question" --auto-start-server`
   - With model selection: `llf chat --cli "question" --model "custom/model"`
   - Shell script integration example

## Key Features

### Supported Flags
CLI mode works with all existing chat flags:
- `--model NAME`: Select specific model
- `--auto-start-server`: Auto-start server without prompt
- `--no-server-start`: Exit if server not running

### Streaming Behavior
- **Interactive Mode**: Streaming enabled (`stream=True`)
- **CLI Mode**: Streaming disabled (`stream=False`)

This design decision ensures:
- Clean, parseable output for scripting
- Faster response collection for automation
- Maintains real-time feedback for human interaction

## Usage Examples

### Basic Usage
```bash
llf chat --cli "What is 2+2?"
```

### With Server Control
```bash
# Auto-start server if needed
llf chat --cli "Explain Python generators" --auto-start-server

# Require running server
llf chat --cli "Write a haiku" --no-server-start
```

### With Model Selection
```bash
llf chat --cli "Code review this function" --model "Qwen/Qwen2.5-Coder-7B"
```

### Shell Script Integration
```bash
#!/bin/bash
ANSWER=$(llf chat --cli "What is the capital of France?" --no-server-start)
echo "The LLM says: $ANSWER"

# Process multiple questions
for question in "What is AI?" "What is ML?" "What is DL?"; do
    llf chat --cli "$question" --no-server-start
    echo "---"
done
```

## Files Modified

1. **llf/cli.py**
   - Added `--cli` argument to chat_parser (lines 688-692)
   - Created `cli_question()` method (lines 288-321)
   - Modified `run()` to accept `cli_question` parameter (lines 328-357)
   - Updated `main()` to extract and pass CLI question (lines 788-802)
   - **Updated main help menu** with CLI mode examples (lines 591-603)

2. **tests/test_cli.py**
   - Added `TestCLIQuestionMode` class with 10 new tests (lines 783-960)
   - All tests passing

3. **QUICK_REFERENCE.md**
   - Added "Chat Modes" section
   - Added CLI mode examples
   - Added shell script integration examples

4. **CLI_MODE_IMPLEMENTATION.md** (this file)
   - Comprehensive documentation of changes

## Verification

Run tests:
```bash
source llf_venv/bin/activate
python -m pytest tests/test_cli.py::TestCLIQuestionMode -v
python -m pytest tests/ --cov=llf
```

Check help:
```bash
llf chat -h
```

Manual test (requires running server):
```bash
# Terminal 1
llf server start

# Terminal 2
llf chat --cli "What is 2+2?"
```

## Design Considerations

### Why No Streaming in CLI Mode?
1. **Parseable Output**: Scripts need clean, complete responses
2. **Simpler Integration**: Single output block easier to capture
3. **Performance**: Collecting chunks then printing is fast enough for automation
4. **User Request**: Explicitly stated "Obviously with the CLI method, you can not do a streaming response"

### Why Separate Method Instead of Flag?
1. **Clear Separation**: Different code paths for different use cases
2. **Error Handling**: Different error reporting for CLI vs interactive
3. **Future Extension**: Easy to add CLI-specific features
4. **Testing**: Simpler to test in isolation

## Future Enhancements

Potential additions (not implemented):
- `--output FILE`: Save response to file
- `--json`: Output in JSON format for parsing
- `--quiet`: Suppress all output except response
- `--timeout SECONDS`: Set custom timeout
- Batch mode: `--cli-file questions.txt`

## Conclusion

The CLI mode implementation successfully adds non-interactive scripting capability to LLF while maintaining backward compatibility with interactive mode. All tests pass, coverage is maintained at 88%, and the feature integrates cleanly with existing server control and model selection flags.
