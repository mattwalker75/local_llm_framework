# File Access Tool

Secure file access for the LLM with whitelist validation, read-only/read-write modes, and comprehensive security controls.

## Features

- **Read-Only (ro) and Read-Write (rw) Modes**: Control whether LLM can write files
- **Whitelist Validation**: Only allow access to explicitly whitelisted paths
- **Root Directory (chroot-like)**: Set a root directory for relative paths
- **Dangerous Path Detection**: Extra protection for system files and credentials
- **Size Limits**: Prevent reading/writing extremely large files (10MB max)
- **Comprehensive Logging**: All file operations are logged

## Configuration

### Mode Setting

- `ro` (read-only): LLM can only read and list files
- `rw` (read-write): LLM can read, write, create, and list files

Set mode in tools_registry.json:
```json
{
  "metadata": {
    "mode": "ro"  // or "rw"
  }
}
```

### Root Directory

The `root_dir` setting acts like a chroot for relative paths. When set, all relative paths are resolved from this directory.

Example:
```json
{
  "metadata": {
    "root_dir": "/path/to/project/docs"
  }
}
```

Now when LLM references "test.txt", it resolves to "/path/to/project/docs/test.txt".

### Whitelist Patterns

Whitelist patterns control which files/directories the LLM can access. Patterns can be:

1. **Glob patterns**: `*.txt`, `*.py`, `*.md`
2. **Directory patterns**: `/path/to/dir/*`
3. **Fully qualified paths**: `/path/to/specific/file.txt`
4. **Relative patterns** (resolved from root_dir): `docs/*`, `src/**/*.py`

Add patterns via CLI:
```bash
# Add glob pattern
llf tool whitelist add file_access "*.txt"

# Add directory pattern
llf tool whitelist add file_access "/path/to/docs/*"

# List current patterns
llf tool whitelist list file_access
```

Or edit tools_registry.json directly:
```json
{
  "metadata": {
    "whitelist": [
      "*.txt",
      "*.md",
      "docs/*",
      "/path/to/project/*"
    ]
  }
}
```

## Security

### Dangerous Path Detection

Even with write permissions, certain paths always require approval:

- System directories: `/etc/*`, `/sys/*`, `/proc/*`, `/dev/*`, `/boot/*`, `/root/*`
- SSH keys: `~/.ssh/*`
- AWS credentials: `~/.aws/*`
- GPG keys: `~/.gnupg/*`
- Key files: `*.key`, `*.pem`
- Credential files: `*credentials*`, `*password*`, `*.env`

These paths will be blocked unless `requires_approval` is explicitly enabled.

### Best Practices

1. **Start with ro mode**: Only enable rw when necessary
2. **Use specific whitelists**: Don't use overly broad patterns like `/*`
3. **Set appropriate root_dir**: Limit scope to specific project directory
4. **Enable approval for sensitive operations**: Set `requires_approval: true` in metadata

## Usage Examples

### Enable Tool in Read-Only Mode

```bash
# Import tool
llf tool import file_access

# Configure whitelist for docs directory
llf tool whitelist add file_access "docs/*"

# Set root_dir (edit tools_registry.json)
{
  "metadata": {
    "mode": "ro",
    "root_dir": "/path/to/project",
    "whitelist": ["docs/*", "*.txt"]
  }
}

# Enable tool
llf tool enable file_access
```

### Enable Tool in Read-Write Mode

```bash
# Edit tools_registry.json
{
  "metadata": {
    "mode": "rw",
    "root_dir": "/path/to/project",
    "whitelist": ["docs/*", "output/*"],
    "requires_approval": true  // Require approval for writes
  }
}

# Enable tool
llf tool enable file_access
```

### LLM Usage

Once enabled, the LLM can use the tool:

```
User: Read the contents of test.txt
Assistant: [Calls file_access with operation="read", path="test.txt"]

User: Write "Hello World" to output.txt
Assistant: [Calls file_access with operation="write", path="output.txt", content="Hello World"]

User: List the files in the docs directory
Assistant: [Calls file_access with operation="list", path="docs"]
```

## Operations

### Read

Read contents of a text file.

Parameters:
- `operation`: "read"
- `path`: File path (relative to root_dir or absolute)

Returns:
- `content`: File contents
- `size`: File size in bytes

### Write

Write content to a file (requires rw mode).

Parameters:
- `operation`: "write"
- `path`: File path (relative to root_dir or absolute)
- `content`: Content to write

Returns:
- `message`: Success message
- `size`: Bytes written

### List

List contents of a directory.

Parameters:
- `operation`: "list"
- `path`: Directory path (relative to root_dir or absolute)

Returns:
- `items`: Array of items with name, type, and size
- `count`: Number of items

## Limitations

- **File Size**: Maximum 10MB per file (read and write)
- **Text Files Only**: Binary files are not supported
- **No Deletion**: Use rw mode for create/write, but not delete (for safety)
- **No Symbolic Links**: Symlinks are not followed

## Error Messages

### "Path is not whitelisted"
The requested path doesn't match any whitelist pattern. Add the path or pattern to the whitelist.

### "Write operation not permitted"
Tool is in `ro` mode. Change to `rw` mode to allow writes.

### "Write to dangerous path requires approval"
The path matches dangerous system files. Enable `requires_approval` to proceed.

### "File too large"
File exceeds 10MB limit. Consider splitting the file or increasing the limit in code.

### "File not found"
The requested file doesn't exist. Check the path and root_dir settings.
