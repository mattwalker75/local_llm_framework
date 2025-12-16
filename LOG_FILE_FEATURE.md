# Log File Feature Implementation

## Overview
Added `--log-file` option to enable logging to a file in addition to console output. This enables persistent logging for debugging, auditing, and troubleshooting purposes.

## Current Logging Behavior (Before)
- Logs were **only written to console (stdout)**
- Colored output for terminal display
- Configurable log level via `--log-level`
- No persistent logging capability

## New Logging Behavior (After)
- Logs can be written to **both console and file simultaneously**
- Console output: colored (if TTY)
- File output: plain text (no color codes)
- Both outputs respect the `--log-level` setting
- File logging is optional (opt-in)

## Implementation Details

### 1. CLI Argument
**File**: `llf/cli.py`
**Location**: Lines 659-664

Added `--log-file` argument to the main argument parser:
```python
parser.add_argument(
    '--log-file',
    type=Path,
    metavar='PATH',
    help='Path to log file. If specified, logs to both console and file.'
)
```

### 2. Setup Logging Call
**File**: `llf/cli.py`
**Location**: Lines 772-775

Modified to pass the log file path:
```python
# Setup logging
log_file = getattr(args, 'log_file', None)
setup_logging(level=args.log_level, log_file=log_file)
disable_external_loggers()
```

### 3. Logging Infrastructure
The `setup_logging()` function in `llf/logging_config.py` already supported file logging via the `log_file` parameter. This implementation simply exposes that capability through the CLI.

**Function signature** (llf/logging_config.py:66-80):
```python
def setup_logging(
    level: str = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[Path] = None,
    use_color: bool = True
) -> None:
```

When `log_file` is provided:
- Creates parent directories if needed
- Adds a FileHandler to the logger
- Uses plain text formatting (no ANSI color codes)
- Both console and file handlers receive all log messages

## Usage Examples

### Basic File Logging
```bash
llf --log-file llf.log chat
```

### Debug Logging to File
```bash
llf --log-level DEBUG --log-file debug.log download
```

### Production Logging
```bash
llf --log-file /var/log/llf/session.log server start
```

### Interactive Chat with Logging
```bash
llf --log-level INFO --log-file chat-$(date +%Y%m%d).log chat
```

### CLI Mode with Logging
```bash
llf --log-file queries.log chat --cli "What is Python?"
```

## Test Coverage

### New Tests
Added 3 comprehensive unit tests in `TestLogging` class:

1. **test_main_with_log_file**: Verifies `--log-file` argument is passed to setup_logging
2. **test_main_with_log_level_and_log_file**: Tests both `--log-level` and `--log-file` together
3. **test_main_without_log_file**: Ensures console-only logging still works (backward compatible)

**Location**: tests/test_cli.py:963-1042

### Test Results
- **Total Tests**: 122 (previously 119)
- **New Tests**: 3
- **All Passing**: ✓
- **Coverage**: 88% (maintained)

## Documentation Updates

### Main Help Menu (llf -h)
**File**: llf/cli.py
**Location**: Lines 620-624

Added examples:
```
# Configuration
llf -d /custom/path              Set custom download directory
llf --log-level DEBUG            Enable debug logging
llf --log-file llf.log           Log to file (in addition to console)
llf --log-level DEBUG --log-file /var/log/llf.log
```

### QUICK_REFERENCE.md

#### Global Options Table
Added row to the options table:
```markdown
| `--log-file PATH` | Log to file (in addition to console) | `llf --log-file llf.log` |
```

#### Examples Section
Added file logging examples:
```bash
# Debug mode with file logging
llf --log-level DEBUG download
llf --log-level DEBUG --log-file llf.log chat
llf --log-file /var/log/llf/session.log server start
```

## Log File Behavior

### File Creation
- Parent directories are created automatically if they don't exist
- File is created if it doesn't exist
- File is appended to if it already exists (not overwritten)

### Log Format
File logs use the standard format:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Example output:
```
2025-12-16 14:32:15,234 - llf.cli - INFO - Starting interactive chat...
2025-12-16 14:32:16,451 - llf.llm_runtime - INFO - llama-server is ready!
2025-12-16 14:32:18,123 - llf.llm_runtime - DEBUG - Generating chat completion with 1 messages (stream=True)
```

### Permissions
- Files are created with default user permissions
- No special permission handling required
- User must have write access to the target directory

## Use Cases

### Development & Debugging
```bash
llf --log-level DEBUG --log-file debug.log chat
```
Captures all debug information for troubleshooting.

### Production Monitoring
```bash
llf --log-file /var/log/llf/$(hostname)-$(date +%Y%m%d).log server start --daemon
```
Persistent logs for long-running server instances.

### Automated Scripts
```bash
#!/bin/bash
LOG_FILE="batch_queries_$(date +%Y%m%d_%H%M%S).log"
llf --log-file "$LOG_FILE" chat --cli "Process batch job" --no-server-start
```
Track automated LLM interactions.

### Support & Troubleshooting
```bash
llf --log-level DEBUG --log-file support-ticket-123.log chat
```
Capture detailed logs to attach to support tickets.

## Files Modified

1. **llf/cli.py**
   - Added `--log-file` argument (lines 659-664)
   - Modified setup_logging call to pass log_file (lines 772-775)
   - Updated help examples (lines 620-624)

2. **tests/test_cli.py**
   - Added `TestLogging` class with 3 new tests (lines 963-1042)
   - All tests passing

3. **QUICK_REFERENCE.md**
   - Added `--log-file` to Global Options table
   - Added file logging examples

4. **LOG_FILE_FEATURE.md** (this file)
   - Comprehensive documentation of the feature

## Backward Compatibility

✅ **Fully backward compatible**
- If `--log-file` is not specified, behavior is identical to before
- Logs only go to console
- No breaking changes to existing functionality
- All existing commands work exactly as before

## Future Enhancements

Potential additions (not implemented):
- **Log rotation**: Automatic log file rotation by size or date
- **Structured logging**: JSON format for parsing
- **Log compression**: Automatic gzip of old logs
- **Multiple log files**: Separate files for different log levels
- **Syslog support**: Send logs to system logger

## Verification

Run tests:
```bash
source llf_venv/bin/activate
python -m pytest tests/test_cli.py::TestLogging -v
python -m pytest tests/ --cov=llf
```

Check help:
```bash
llf -h | grep -A 2 log-file
```

Test functionality:
```bash
# Create a test log file
llf --log-file test.log --log-level DEBUG chat --cli "Test logging"

# Verify log file was created and contains logs
cat test.log
```

## Conclusion

The `--log-file` feature successfully adds persistent logging capability to LLF while maintaining full backward compatibility. The implementation leverages existing infrastructure, adds minimal code, and is thoroughly tested.
