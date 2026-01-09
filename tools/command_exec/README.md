# Command Execution Tool

Secure command execution for the LLM with whitelist validation, parameter support, and comprehensive security controls.

## Features

- **Command Whitelist**: Only whitelisted commands can be executed
- **Pattern Matching**: Support for command patterns (e.g., `git*`)
- **Parameter Support**: Pass arguments to commands safely
- **Timeout Protection**: Commands timeout after configurable duration
- **Output Capture**: Captures both stdout and stderr
- **Dangerous Command Detection**: Extra protection for destructive commands
- **Comprehensive Logging**: All command executions are logged

## Configuration

### Whitelist Commands

Add commands to whitelist via CLI:
```bash
# Add specific command
llf tool whitelist add command_exec "ls"

# Add command with pattern
llf tool whitelist add command_exec "git*"

# List whitelisted commands
llf tool whitelist list command_exec
```

Or edit tools_registry.json directly:
```json
{
  "metadata": {
    "whitelist": [
      "ls",
      "pwd",
      "cat",
      "grep",
      "find",
      "git*",
      "npm",
      "python"
    ]
  }
}
```

### Pattern Matching

Patterns use standard glob matching:
- `ls` - Exact match
- `git*` - Matches `git`, `git-log`, `git-status`, etc.
- `python*` - Matches `python`, `python3`, `python3.9`, etc.

## Security

### Dangerous Command Detection

Certain commands are always considered dangerous and require approval:
- `rm` - Remove files
- `del` - Delete files (Windows)
- `format` - Format drive
- `mkfs` - Make filesystem
- `dd` - Disk utility

These commands will be blocked unless `requires_approval` is explicitly enabled.

### Safe Execution

- **No Shell Injection**: Commands are executed without shell interpretation
- **Parameter Escaping**: All parameters are properly escaped
- **Timeout Protection**: Commands automatically timeout (default: 30s, max: 300s)
- **No Wildcards in Tool**: The LLM cannot use shell wildcards directly

### Best Practices

1. **Whitelist specific commands only**: Don't use overly broad patterns
2. **Enable approval for write operations**: Set `requires_approval: true`
3. **Use read-only commands**: Prefer `ls`, `cat`, `grep` over `rm`, `mv`
4. **Set appropriate timeouts**: Prevent long-running commands from blocking
5. **Review logs regularly**: Check what commands are being executed

## Usage Examples

### Enable Tool with Safe Commands

```bash
# Import tool
llf tool import command_exec

# Configure whitelist (edit tools_registry.json)
{
  "metadata": {
    "whitelist": ["ls", "pwd", "cat", "grep", "find"],
    "requires_approval": false
  }
}

# Enable tool
llf tool enable command_exec
```

### LLM Usage

Once enabled, the LLM can execute commands:

```
User: List files in the current directory
Assistant: [Calls command_exec with command="ls", arguments=["-la"]]

User: Search for Python files
Assistant: [Calls command_exec with command="find", arguments=[".", "-name", "*.py"]]

User: Show the contents of README.md
Assistant: [Calls command_exec with command="cat", arguments=["README.md"]]
```

## Operations

### Execute Command

Execute a whitelisted command with parameters.

Parameters:
- `command`: Command name (must be whitelisted)
- `arguments`: Array of command arguments (optional)
- `timeout`: Timeout in seconds (optional, default: 30, max: 300)

Returns:
- `command`: Full command that was executed
- `return_code`: Exit code (0 = success)
- `stdout`: Standard output
- `stderr`: Standard error
- `timed_out`: Boolean indicating if command timed out

## Examples

### List Directory

```json
{
  "command": "ls",
  "arguments": ["-la", "/path/to/dir"]
}
```

### Search Files

```json
{
  "command": "find",
  "arguments": [".", "-name", "*.py", "-type", "f"]
}
```

### Git Status

```json
{
  "command": "git",
  "arguments": ["status", "--short"]
}
```

### Grep with Timeout

```json
{
  "command": "grep",
  "arguments": ["-r", "pattern", "/large/directory"],
  "timeout": 60
}
```

## Limitations

- **Whitelist Required**: All commands must be explicitly whitelisted
- **No Shell Features**: Cannot use pipes, redirects, or shell variables
- **No Interactive Commands**: Commands that require user input will fail
- **Timeout Limits**: Maximum timeout is 300 seconds (5 minutes)
- **Platform Dependent**: Some commands may not be available on all platforms

## Error Messages

### "Command is not whitelisted"
The requested command doesn't match any whitelist pattern. Add the command to the whitelist.

### "Command not found"
The command doesn't exist on the system. Check that the command is installed.

### "Dangerous command requires approval"
The command matches dangerous operations. Enable `requires_approval` to proceed.

### "Command timed out"
The command exceeded the timeout duration. Increase timeout or optimize the command.

## Common Whitelist Configurations

### Development Tools
```json
{
  "whitelist": ["git*", "npm", "python*", "pip*", "ls", "cat", "grep", "find"]
}
```

### System Administration
```json
{
  "whitelist": ["ls", "ps", "top", "df", "du", "free", "uname", "hostname"],
  "requires_approval": true
}
```

### File Management (Safe)
```json
{
  "whitelist": ["ls", "pwd", "cat", "head", "tail", "grep", "find", "wc", "file"]
}
```

### Docker Operations
```json
{
  "whitelist": ["docker*"],
  "requires_approval": true
}
```
