# Security Policy

## Overview

The Local LLM Framework (LLF) implements a multi-layered security model to protect your system when using AI-powered tools. This document outlines our security practices, threat model, and how to report vulnerabilities.

## Security Architecture

### 8-Layer Security Model

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Tool Registration & Validation                    │
│ - Only registered tools can be loaded                      │
│ - Config validation ensures proper tool structure          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Tool Enable/Disable Controls                      │
│ - Tools must be explicitly enabled                         │
│ - Disabled tools are never loaded or executed              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Whitelist-Based Access Control                    │
│ - File paths must match whitelist patterns                 │
│ - Commands must match whitelist patterns                   │
│ - No whitelist = no access                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Root Directory (chroot-like) Containment          │
│ - Relative paths resolved from configured root_dir         │
│ - Prevents access outside configured boundaries            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Dangerous Path/Command Detection                  │
│ - Automatic detection of system-critical paths             │
│ - Automatic detection of destructive commands              │
│ - Always requires approval for dangerous operations        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 6: Read-Only vs Read-Write Mode                      │
│ - 'ro' mode: read operations only                          │
│ - 'rw' mode: read and write operations                     │
│ - Mode enforced at execution time                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 7: Timeout Protection                                │
│ - Commands have configurable timeouts (1-300s)             │
│ - Prevents runaway processes                               │
│ - Automatic termination on timeout                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 8: User Approval for High-Risk Operations            │
│ - requires_approval flag for sensitive tools               │
│ - Human-in-the-loop for dangerous operations               │
│ - Explicit confirmation required                           │
└─────────────────────────────────────────────────────────────┘
```

## Threat Model

### What We Protect Against

1. **Unauthorized File Access**
   - **Threat**: LLM attempts to read sensitive files (credentials, SSH keys, etc.)
   - **Protection**: Whitelist patterns + dangerous path detection + approval requirements
   - **Example**: Reading `/etc/passwd` requires explicit approval even if whitelisted

2. **Destructive Commands**
   - **Threat**: LLM executes commands that could delete data or harm the system
   - **Protection**: Command whitelist + dangerous command detection + approval requirements
   - **Example**: `rm -rf /` is automatically flagged as dangerous and requires approval

3. **Path Traversal Attacks**
   - **Threat**: LLM uses `../` sequences to escape intended directories
   - **Protection**: Path normalization + root_dir containment + whitelist validation
   - **Example**: `/project/../../../etc/passwd` is normalized and blocked

4. **Privilege Escalation**
   - **Threat**: LLM attempts to run commands with elevated privileges
   - **Protection**: No automatic sudo/su, privilege commands flagged as dangerous
   - **Example**: `sudo rm` requires explicit approval

5. **Information Disclosure**
   - **Threat**: LLM reads and transmits sensitive information
   - **Protection**: Whitelist restricts access, dangerous paths require approval
   - **Example**: Cannot read `~/.ssh/id_rsa` without explicit approval

6. **Resource Exhaustion**
   - **Threat**: LLM runs infinite loops or resource-intensive commands
   - **Protection**: Configurable timeouts, automatic process termination
   - **Example**: Command timeout after 60 seconds (configurable)

### What We Don't Protect Against

1. **Social Engineering**: If a user approves a dangerous operation, it will execute
2. **Logic Bugs**: The LLM might make mistakes in code logic (separate from security)
3. **Network-Based Attacks**: LLF doesn't restrict network access (use firewalls)
4. **Physical Access**: If attacker has shell access, they bypass LLF entirely

## Dangerous Paths and Commands

### Automatically Flagged as Dangerous

These paths and commands **always** require approval, even if whitelisted:

#### Dangerous Paths (File Access Tool)

```python
DANGEROUS_PATHS = [
    '/etc/',                    # System configuration
    '/sys/',                    # System information
    '/proc/',                   # Process information
    '/dev/',                    # Device files
    '/boot/',                   # Boot files
    '~/.ssh/',                  # SSH keys
    '~/.aws/',                  # AWS credentials
    '~/.config/',               # User configuration
    '/var/log/',                # System logs
    '/root/',                   # Root user home
]

DANGEROUS_EXTENSIONS = [
    '.key',                     # Private keys
    '.pem',                     # SSL certificates
    '.p12',                     # Certificate bundles
    '.pfx',                     # Certificate bundles
    '.keystore',                # Java keystores
    '.jks',                     # Java keystores
    '.env',                     # Environment files
]

DANGEROUS_FILENAMES = [
    'credentials',
    'secrets',
    'password',
    'passwd',
    'shadow',
    'id_rsa',
    'id_dsa',
    'id_ecdsa',
    'id_ed25519',
]
```

#### Dangerous Commands (Command Execution Tool)

```python
DANGEROUS_COMMANDS = [
    'rm',                       # File deletion
    'rmdir',                    # Directory deletion
    'dd',                       # Low-level disk operations
    'mkfs',                     # Format filesystem
    'fdisk',                    # Partition manipulation
    'parted',                   # Partition editor
    'chmod',                    # Permission changes
    'chown',                    # Ownership changes
    'kill',                     # Process termination
    'killall',                  # Mass process termination
    'pkill',                    # Pattern-based termination
    'sudo',                     # Privilege escalation
    'su',                       # User switching
    'shutdown',                 # System shutdown
    'reboot',                   # System reboot
    'poweroff',                 # System power off
    'init',                     # System initialization
]
```

## Security Best Practices

### For Users

1. **Start with Read-Only Mode**
   ```bash
   python -m llf.cli tool enable file_access --mode ro
   ```
   Enable read-write only when necessary.

2. **Use Restrictive Whitelists**
   ```bash
   # Good: Specific paths
   python -m llf.cli tool whitelist add file_access "/path/to/project/**"

   # Bad: Too permissive
   python -m llf.cli tool whitelist add file_access "/**"
   ```

3. **Set Appropriate Timeouts**
   ```bash
   # For quick commands
   python -m llf.cli tool config set command_exec timeout 10

   # For long-running operations
   python -m llf.cli tool config set command_exec timeout 300
   ```

4. **Enable Approval for Sensitive Tools**
   ```bash
   python -m llf.cli tool config set file_access requires_approval true
   python -m llf.cli tool config set command_exec requires_approval true
   ```

5. **Review Tool Configuration Regularly**
   ```bash
   python -m llf.cli tool list --verbose
   ```

6. **Use Project-Specific Root Directories**
   ```bash
   python -m llf.cli tool config set file_access root_dir "/path/to/project"
   ```

### For Tool Developers

1. **Always Validate Input**
   ```python
   def execute(params: dict) -> dict:
       # Validate required parameters
       if 'required_param' not in params:
           return {
               'success': False,
               'error': 'Missing required parameter: required_param'
           }
   ```

2. **Use Whitelist Checks**
   ```python
   from llf.tools_manager import ToolsManager

   manager = ToolsManager()
   tool_info = manager.get_tool('your_tool')

   if not manager.check_whitelist('your_tool', user_path):
       return {
           'success': False,
           'error': f'Path not whitelisted: {user_path}'
       }
   ```

3. **Detect Dangerous Operations**
   ```python
   def is_dangerous_path(path: str) -> bool:
       dangerous = ['/etc/', '/sys/', '/proc/', '~/.ssh/']
       normalized = os.path.normpath(os.path.expanduser(path))

       for danger in dangerous:
           if normalized.startswith(os.path.expanduser(danger)):
               return True
       return False
   ```

4. **Implement Timeout Protection**
   ```python
   import subprocess

   timeout = tool_info['metadata'].get('timeout', 60)

   try:
       result = subprocess.run(
           command,
           timeout=timeout,
           capture_output=True
       )
   except subprocess.TimeoutExpired:
       return {'success': False, 'error': 'Command timed out'}
   ```

5. **Return Structured Error Messages**
   ```python
   return {
       'success': False,
       'error': 'Clear, actionable error message',
       'error_code': 'SPECIFIC_ERROR_TYPE',  # Optional
       'details': {...}  # Optional debugging info
   }
   ```

## Configuration Security

### Tool Configuration File Structure

```json
{
  "name": "file_access",
  "type": "llm_invokable",
  "directory": "file_access",
  "metadata": {
    "mode": "ro",                          // Start with read-only
    "root_dir": "/path/to/project",        // Restrict to project
    "requires_approval": true,             // Require approval
    "timeout": 60,                         // Timeout in seconds
    "whitelist": [
      "/path/to/project/**/*.py",          // Specific patterns
      "/path/to/project/data/*.json"
    ]
  }
}
```

### Registry File Security

The `tools_registry.json` file contains all tool configurations:

- **Location**: `~/.local/share/llf/tools_registry.json` (Linux/Mac) or `%APPDATA%/llf/tools_registry.json` (Windows)
- **Permissions**: Should be readable/writable only by the user (600)
- **Backup**: Keep backups before making changes
- **Validation**: Registry is validated on load

### Environment Variables

LLF respects these security-relevant environment variables:

```bash
# Override default registry location
export LLF_TOOLS_REGISTRY="/custom/path/tools_registry.json"

# Override tools directory
export LLF_TOOLS_DIR="/custom/path/tools"
```

## Security Updates

### Reporting Vulnerabilities

If you discover a security vulnerability in LLF:

1. **DO NOT** open a public GitHub issue
2. Email security details to: [Your security contact email]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Security Response Timeline

- **24 hours**: Initial response acknowledging receipt
- **7 days**: Initial assessment and severity classification
- **30 days**: Fix development and testing
- **Public disclosure**: After fix is released and users have time to update

### Security Advisories

Security advisories will be published:
- In the project's GitHub Security tab
- In release notes for patched versions
- On the project website/documentation

## Compliance and Standards

### Principle of Least Privilege

LLF implements least privilege through:
- Tools disabled by default
- Read-only mode as default
- Explicit whitelist requirements
- Approval requirements for sensitive operations

### Defense in Depth

Multiple security layers ensure that:
- Single point of failure doesn't compromise security
- Even if one check is bypassed, others still protect
- Security is maintained even with configuration errors

### Secure by Default

Default configurations prioritize security:
```json
{
  "enabled": false,              // Must explicitly enable
  "mode": "ro",                  // Read-only by default
  "requires_approval": true,     // Approval required
  "whitelist": [],               // Empty whitelist (no access)
  "timeout": 60                  // Conservative timeout
}
```

## Audit and Logging

### Tool Execution Logging

LLF logs all tool executions (implementation dependent):

```python
# Example logging structure
{
  "timestamp": "2025-01-06T10:30:00Z",
  "tool": "file_access",
  "operation": "write",
  "path": "/project/data/output.txt",
  "success": true,
  "approved": true,
  "user": "username"
}
```

### Audit Recommendations

1. **Enable logging** for sensitive tools
2. **Review logs** regularly for suspicious activity
3. **Monitor** approval patterns (many denials = potential issue)
4. **Archive** logs for compliance requirements

## Security Checklist

### Before Enabling a Tool

- [ ] Do I understand what this tool does?
- [ ] Have I configured appropriate whitelists?
- [ ] Is the mode set correctly (ro vs rw)?
- [ ] Have I set a reasonable timeout?
- [ ] Does this tool need approval requirements?
- [ ] Have I tested with safe data first?

### Before Granting Approval

- [ ] Do I understand what operation will be performed?
- [ ] Is the path/command what I expect?
- [ ] Could this operation cause data loss?
- [ ] Could this operation expose sensitive information?
- [ ] Is there a safer alternative?

### Regular Security Review

- [ ] Review enabled tools (disable unused ones)
- [ ] Review whitelist patterns (tighten if possible)
- [ ] Review approval logs (look for patterns)
- [ ] Update LLF to latest version
- [ ] Review security advisories

## Additional Resources

- [Tool Development Guide](README.md#creating-new-tools)
- [Security Architecture](README.md#security-architecture)
- [Whitelist Pattern Documentation](README.md#whitelist-patterns)
- [Testing Security Features](README.md#testing-security-features)

## License

This security policy is part of the Local LLM Framework project and subject to the same license terms.

---

**Last Updated**: 2025-01-06
**Version**: 1.0
