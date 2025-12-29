# Changelog: Tool Execution Modes Feature

## Date: 2025-12-27

## Summary

Implemented configurable tool execution modes to address the fundamental incompatibility between streaming responses and tool calling (memory operations). This allows users to choose between streaming UX and tool accuracy based on their use case.

## Changes

### New Files

1. **llf/operation_detector.py** (119 lines)
   - Pattern-based operation type detection (READ/WRITE/GENERAL)
   - Decision logic for dual-pass execution
   - `detect_operation_type()` function
   - `should_use_dual_pass()` function

2. **tests/test_operation_detector.py** (140 lines)
   - 12 comprehensive tests for operation detection
   - Tests for all three operation types
   - Tests for dual-pass decision logic
   - Edge case handling (empty messages, case sensitivity)

3. **tests/test_config_tool_execution_mode.py** (113 lines)
   - 10 tests for configuration loading and validation
   - Tests for all three execution modes
   - Invalid mode error handling
   - Backward compatibility tests

4. **docs/TOOL_EXECUTION_MODES.md** (471 lines)
   - Comprehensive documentation
   - Mode descriptions with pros/cons
   - Configuration examples
   - Troubleshooting guide
   - Migration guide
   - Performance considerations

5. **CHANGELOG_TOOL_EXECUTION_MODES.md** (This file)
   - Summary of all changes

### Modified Files

1. **configs/config.json**
   - Added `tool_execution_mode: "single_pass"` to `llm_endpoint` section

2. **llf/config.py**
   - Added `VALID_TOOL_EXECUTION_MODES` constant
   - Added `DEFAULT_TOOL_EXECUTION_MODE` constant
   - Added `tool_execution_mode` instance variable
   - Added validation in `_load_from_file()` method
   - Added `tool_execution_mode` to `to_dict()` output
   - Total changes: ~20 lines added

3. **llf/cli.py**
   - Replaced simple streaming auto-detection with mode-based execution
   - Implemented dual-pass execution logic
   - Added operation type detection
   - Added background thread execution for Pass 2
   - Total changes: ~50 lines modified/added

### Test Results

**Before:**
- 493 tests passing
- 70% coverage

**After:**
- 515 tests passing (+22 tests)
- 71% coverage (+1%)
- All tests passing
- New modules have 100% coverage:
  - `llf/operation_detector.py`: 100%
  - `llf/config.py`: 96% (was 96%, maintained)

## Feature Details

### Three Execution Modes

1. **single_pass** (default)
   - Single LLM call
   - No streaming when tools available
   - Always accurate
   - Same behavior as before this feature

2. **dual_pass_write_only** (recommended)
   - WRITE operations: Dual-pass (streaming + background tools)
   - READ operations: Single-pass with tools (accurate)
   - GENERAL chat: Streaming only
   - Best balance of UX and accuracy

3. **dual_pass_all** (advanced)
   - Always dual-pass when tools available
   - Best streaming UX
   - Not safe for READ operations
   - Only for write-heavy applications

### Operation Type Detection

Uses regex pattern matching to classify user messages:
- **READ**: `"What's my name?"`, `"Do you remember...?"`
- **WRITE**: `"Remember that..."`, `"My name is..."`
- **GENERAL**: `"Tell me a joke"`, `"How's the weather?"`

## Configuration

Add to `configs/config.json`:

```json
{
  "llm_endpoint": {
    "tool_execution_mode": "dual_pass_write_only"
  }
}
```

## Backward Compatibility

- ✅ Default mode (`single_pass`) maintains existing behavior
- ✅ No changes required to existing configurations
- ✅ Feature is opt-in via configuration
- ✅ All existing tests continue to pass

## Performance Impact

### single_pass mode
- No change from current behavior
- 1 LLM call per message

### dual_pass_write_only mode
- READ operations: 1 LLM call (no change)
- WRITE operations: 2 LLM calls (100% increase for writes only)
- GENERAL chat: 1 LLM call (no change)

### dual_pass_all mode
- READ operations: 2 LLM calls (100% increase)
- WRITE operations: 2 LLM calls (100% increase)
- GENERAL chat: 1 LLM call (no change)

## Breaking Changes

None. This feature is fully backward compatible.

## Migration Path

1. **No action required**: Default mode maintains current behavior
2. **Opt-in for better UX**: Add `tool_execution_mode: "dual_pass_write_only"` to config
3. **Test your use case**: Verify streaming and accuracy work as expected

## Known Limitations

1. **Pattern-based detection**: Operation type detection uses regex patterns, not semantic understanding
2. **Background execution**: Pass 2 in dual-pass modes runs in background thread
3. **Cost increase**: Dual-pass modes increase LLM API calls for certain operations

## Future Enhancements

Potential improvements:
1. Custom user-defined patterns for READ/WRITE detection
2. Per-tool execution modes
3. Cost tracking for dual-pass calls
4. LLM-based operation type classification
5. Streaming tool results (when API supports it)

## Testing

Run tests:
```bash
# All tests
python -m pytest tests/ -v

# Just new tests
python -m pytest tests/test_operation_detector.py tests/test_config_tool_execution_mode.py -v

# With coverage
python -m pytest tests/ --cov=llf --cov=tools --cov-report=term-missing
```

## Documentation

Full documentation available at:
- [docs/TOOL_EXECUTION_MODES.md](docs/TOOL_EXECUTION_MODES.md)

## Author

Implementation by Claude Sonnet 4.5 on 2025-12-27

## Related Issues

Addresses user request: "Can we have the LLM make 2 requests? Stream the request to the user... and if it needs to access a tool, then run it a second time in the background..."
