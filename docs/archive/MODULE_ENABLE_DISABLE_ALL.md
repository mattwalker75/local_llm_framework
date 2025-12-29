# Module Enable/Disable All - Bulk Operations

## Overview

Added bulk enable/disable operations to manage all modules at once using the `all` keyword.

---

## New Commands

### Enable All Modules
```bash
llf module enable all
```

**What it does:**
- Enables all registered modules in the registry
- Shows count of modules enabled
- Lists modules that were already enabled (if any)

### Disable All Modules
```bash
llf module disable all
```

**What it does:**
- Disables all registered modules in the registry
- Shows count of modules disabled
- Lists modules that were already disabled (if any)

---

## Usage Examples

### Example 1: Enable All Modules

```bash
$ llf module enable all
Enabled 2 module(s) successfully
```

**Result**: All modules (text2speech, speech2text) are now enabled.

---

### Example 2: Enable All When Already Enabled

```bash
$ llf module enable all
Already enabled: text2speech, speech2text
```

**Result**: No changes made, informational message shown.

---

### Example 3: Disable All Modules

```bash
$ llf module disable all
Disabled 2 module(s) successfully
```

**Result**: All modules are now disabled.

---

### Example 4: Disable All When Already Disabled

```bash
$ llf module disable all
Already disabled: text2speech, speech2text
```

**Result**: No changes made, informational message shown.

---

### Example 5: Mixed State

```bash
# If text2speech is enabled but speech2text is disabled:
$ llf module enable all
Enabled 1 module(s) successfully
Already enabled: text2speech
```

**Result**: speech2text is now enabled, text2speech was already enabled.

---

## Command Reference

| Command | Action | When to Use |
|---------|--------|-------------|
| `llf module enable all` | Enable all modules | Quick setup for full voice features |
| `llf module disable all` | Disable all modules | Testing text-only mode, troubleshooting |
| `llf module enable MODULE_NAME` | Enable specific module | Selective feature activation |
| `llf module disable MODULE_NAME` | Disable specific module | Disable one feature |
| `llf module list` | List all modules | Check current state |

---

## Use Cases

### Quick Full Voice Setup
```bash
# One command to enable both TTS and STT:
llf module enable all
llf gui
```

**Result**: GUI has both voice input and output ready to use.

---

### Troubleshooting - Disable All
```bash
# Disable all modules to test text-only mode:
llf module disable all
llf chat
```

**Result**: Pure text interaction, no voice features.

---

### Testing - Toggle All
```bash
# Test GUI dynamic module reload with bulk operations:
llf gui &

# In another terminal:
llf module disable all
# In GUI: Click "Reload Modules" - voice controls disappear

llf module enable all
# In GUI: Click "Reload Modules" - voice controls appear
```

**Result**: Verify GUI correctly shows/hides controls based on module state.

---

## Implementation Details

### File: [`llf/cli.py`](llf/cli.py)

**Enable All Logic** (lines 1830-1849):
```python
if args.module_name.lower() == 'all':
    enabled_count = 0
    already_enabled = []
    for module in modules:
        if module.get('enabled', False):
            already_enabled.append(module.get('name'))
        else:
            module['enabled'] = True
            enabled_count += 1

    # Write back to registry
    with open(modules_registry_path, 'w') as f:
        json.dump(registry, f, indent=2)

    if enabled_count > 0:
        console.print(f"[green]Enabled {enabled_count} module(s) successfully[/green]")
    if already_enabled:
        console.print(f"[dim]Already enabled: {', '.join(already_enabled)}[/dim]")
```

**Disable All Logic** (lines 1895-1914):
```python
if args.module_name.lower() == 'all':
    disabled_count = 0
    already_disabled = []
    for module in modules:
        if not module.get('enabled', False):
            already_disabled.append(module.get('name'))
        else:
            module['enabled'] = False
            disabled_count += 1

    # Write back to registry
    with open(modules_registry_path, 'w') as f:
        json.dump(registry, f, indent=2)

    if disabled_count > 0:
        console.print(f"[green]Disabled {disabled_count} module(s) successfully[/green]")
    if already_disabled:
        console.print(f"[dim]Already disabled: {', '.join(already_disabled)}[/dim]")
```

---

## Features

### Case-Insensitive
```bash
llf module enable all    # Works
llf module enable All    # Works
llf module enable ALL    # Works
```

All variations of "all" are accepted (converted to lowercase internally).

---

### Idempotent
```bash
# Running multiple times is safe:
llf module enable all
llf module enable all   # No error, just shows "Already enabled"
```

No errors or side effects from repeated execution.

---

### Clear Feedback

**Success with count:**
```
Enabled 2 module(s) successfully
```

**Already in desired state:**
```
Already enabled: text2speech, speech2text
```

**Mixed state:**
```
Enabled 1 module(s) successfully
Already enabled: text2speech
```

---

## Help Documentation

### Main Help (`llf -h`)

```bash
# Module management
llf module list                  List modules
llf module list --enabled        List only enabled modules
llf module enable MODULE_NAME    Enable a module
llf module enable all            Enable all modules
llf module disable MODULE_NAME   Disable a module
llf module disable all           Disable all modules
llf module info MODULE_NAME      Show module information
```

### Module Help (`llf module -h`)

```bash
actions:
  list                      List modules
  list --enabled            List only enabled modules
  enable MODULE_NAME        Enable a module
  enable all                Enable all modules
  disable MODULE_NAME       Disable a module
  disable all               Disable all modules
  info MODULE_NAME          Show module information
```

---

## Testing

### Test Suite

```bash
# Test 1: Enable all from disabled state
llf module disable all
llf module enable all
llf module list  # Should show all enabled

# Test 2: Disable all from enabled state
llf module enable all
llf module disable all
llf module list  # Should show all disabled

# Test 3: Idempotency
llf module enable all
llf module enable all  # Should show "Already enabled"

# Test 4: Mixed state
llf module enable text2speech
llf module disable speech2text
llf module enable all  # Should enable speech2text only
```

---

## Current Modules

As of this implementation:
1. **text2speech** - Text-to-Speech voice output
2. **speech2text** - Speech-to-Text voice input

Future modules will automatically work with `enable all` / `disable all`.

---

## Error Handling

### No Modules Available
```bash
# If registry has no modules:
llf module enable all
# Output: No modules available to enable
```

### Registry Not Found
```bash
# If modules_registry.json missing:
llf module enable all
# Output: Error: Modules registry not found at [path]
```

### Invalid JSON
```bash
# If registry file corrupted:
llf module enable all
# Output: Error: Invalid JSON in modules registry: [details]
```

---

## Benefits

✅ **Quick Setup**: One command to enable full voice features
✅ **Easy Testing**: Quick disable/enable for troubleshooting
✅ **Clear Feedback**: Shows exactly what happened
✅ **Idempotent**: Safe to run multiple times
✅ **Case-Insensitive**: Flexible input
✅ **Future-Proof**: Works with any number of modules

---

## Backward Compatibility

✅ **Existing commands unchanged**: Single module enable/disable still works
✅ **No breaking changes**: All previous functionality preserved
✅ **Additive feature**: New capability without removing old behavior

---

## Summary

The `llf module enable all` and `llf module disable all` commands provide:

- **Bulk operations** for managing all modules at once
- **Clear feedback** about what changed
- **Idempotent behavior** for safe repeated use
- **Helpful messages** for all scenarios
- **Updated help documentation** showing new usage

**Quick reference:**
```bash
llf module enable all   # Enable all modules (TTS + STT)
llf module disable all  # Disable all modules
llf module list         # Check current state
```
