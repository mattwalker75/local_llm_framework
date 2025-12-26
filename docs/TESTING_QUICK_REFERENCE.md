# Testing Quick Reference

## Test Status
✅ **262/262 tests passing** (100%)
✅ **58% total code coverage**

---

## Quick Commands

### Run All Tests (Fastest)
```bash
source llf_venv/bin/activate
pytest
```
**Time**: ~5 seconds
**Output**: Pass/fail only

---

### Run Tests with Coverage (Recommended)
```bash
./run_coverage.sh
```
**Time**: ~6 seconds
**Output**: Coverage report in terminal

---

### Generate HTML Coverage Report
```bash
./run_coverage.sh html
open htmlcov/index.html
```
**Time**: ~6 seconds
**Output**: Interactive HTML coverage browser

---

### Run Specific Test File
```bash
source llf_venv/bin/activate
pytest tests/test_cli.py
pytest tests/test_gui.py -v
```

---

### Run Tests Matching Pattern
```bash
source llf_venv/bin/activate
pytest -k "test_chat"      # All tests with "chat" in name
pytest -k "not slow"       # Skip tests marked as slow
```

---

## Common Issues

### ❌ "pytest: command not found"
**Fix**: Activate virtual environment first
```bash
source llf_venv/bin/activate
```

### ❌ Coverage shows traceback (but tests pass)
**Fix**: Use the `-p no:unraisableexception` flag or the convenience script
```bash
# Don't do this:
pytest --cov  # ❌ Will show traceback

# Do this instead:
pytest --cov -p no:unraisableexception  # ✅
# OR
./run_coverage.sh  # ✅ Built-in flag
```

### ⚠️ Tests hang forever
**Check**: Are TTS/STT modules enabled?
```bash
# Disable modules for testing
llf module disable text2speech
llf module disable speech2text

# Then run tests again
pytest
```

---

## Test Files Overview

| File | Tests | Coverage |
|------|-------|----------|
| `test_cli.py` | 61 | CLI chat interface |
| `test_config.py` | 29 | Configuration handling |
| `test_gui.py` | 85 | Gradio GUI interface |
| `test_llm_runtime.py` | 35 | LLM server runtime |
| `test_model_manager.py` | 22 | Model downloads |
| `test_prompt_config.py` | 14 | Prompt templates |
| **TOTAL** | **262** | **All components** |

---

## Coverage Reports

### Terminal Report
```bash
./run_coverage.sh
```
Shows line-by-line coverage percentages in terminal.

### HTML Report (Best for Exploration)
```bash
./run_coverage.sh html
open htmlcov/index.html
```
Interactive browser showing:
- Which lines are covered (green)
- Which lines are missed (red)
- Execution counts
- Branch coverage

### Both Reports
```bash
./run_coverage.sh both
```
Terminal output + HTML files generated.

---

## Module Coverage Notes

### Low Coverage (Expected)
Some modules have low coverage because they're platform-specific or optional:

- **tts_pyttsx3.py** (0%): Windows/Linux only, not used on macOS
- **list_voices.py** (0%): Utility script, not tested
- **stt_engine.py** (25%): Requires speech2text module enabled
- **tts_macos.py** (34%): Requires text2speech module enabled

### High Coverage (Core Components)
- **config.py**: 96%
- **prompt_config.py**: 94%
- **llm_runtime.py**: 83%
- **gui.py**: 73%

---

## Advanced Testing

### Run with Verbose Output
```bash
source llf_venv/bin/activate
pytest -v
```

### Show Print Statements
```bash
source llf_venv/bin/activate
pytest -s
```

### Stop on First Failure
```bash
source llf_venv/bin/activate
pytest -x
```

### Run Tests in Parallel (requires pytest-xdist)
```bash
source llf_venv/bin/activate
pip install pytest-xdist
pytest -n auto
```

### Profile Test Performance
```bash
source llf_venv/bin/activate
pytest --durations=10  # Show 10 slowest tests
```

---

## CI/CD Integration

For automated testing in CI/CD pipelines:

```bash
#!/bin/bash
source llf_venv/bin/activate
pytest --cov -p no:unraisableexception --cov-report=xml --cov-report=term
# Upload coverage.xml to CodeCov, Coveralls, etc.
```

---

## Troubleshooting

### Module Not Found Errors
```bash
# Reinstall dependencies
source llf_venv/bin/activate
pip install -e .
```

### Import Errors
```bash
# Check Python path
source llf_venv/bin/activate
python -c "import sys; print('\n'.join(sys.path))"
```

### Stale .pyc Files
```bash
# Clean compiled Python files
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

---

## Summary

**For Day-to-Day Testing**:
```bash
pytest                # Quick check
./run_coverage.sh     # With coverage
```

**For Detailed Investigation**:
```bash
./run_coverage.sh html
open htmlcov/index.html
```

**Remember**: All 262 tests should pass. If any fail, investigate before committing changes.
