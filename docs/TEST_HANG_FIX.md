# Test Hang Fix - TTS/STT Module Loading & PyTorch Cleanup

## Problem

Tests in `tests/test_cli.py` and `tests/test_gui.py` were hanging when run, preventing the test suite from completing. Additionally, PyTorch cleanup was causing KeyboardInterrupt when running all GUI tests together.

### Root Causes

1. **Module Loading Issue**: Both `CLI` and `LLMFrameworkGUI` classes have a `_load_modules()` method in their `__init__()` that loads TTS and STT modules if they're enabled in the module registry. During tests:
   - The modules were enabled in `modules/modules_registry.json`
   - Test fixtures created `CLI` and `GUI` instances without mocking module loading
   - The `_load_modules()` method tried to initialize real TTS/STT engines
   - STT initialization specifically would try to access the microphone, causing tests to hang

2. **PyTorch Cleanup Issue**: When running all 85 GUI tests together, PyTorch/Gradio cleanup would trigger a KeyboardInterrupt after ~59 tests, preventing the remaining tests from running.

---

## Solution

### Part 1: Mock Module Loading in Test Fixtures

Mock the `_load_modules()` method in test fixtures to prevent actual module initialization during tests.

#### File: `tests/test_cli.py`

```python
@pytest.fixture
def cli(config):
    """Create CLI instance."""
    with patch.object(CLI, '_load_modules'):
        # Prevent loading TTS/STT modules during tests (causes hangs)
        cli_instance = CLI(config)
        # Ensure tts and stt are None (not loaded)
        cli_instance.tts = None
        cli_instance.stt = None
        return cli_instance
```

#### File: `tests/test_gui.py`

```python
@pytest.fixture
def gui(self, mock_config, mock_prompt_config):
    """Create GUI instance for testing."""
    with patch.object(LLMFrameworkGUI, '_load_modules'):
        # Prevent loading TTS/STT modules during tests (causes hangs)
        gui_instance = LLMFrameworkGUI(config=mock_config, prompt_config=mock_prompt_config)
        # Ensure tts and stt are None (not loaded)
        gui_instance.tts = None
        gui_instance.stt = None
        return gui_instance
```

#### File: `tests/test_gui.py` - TestShareModeTTS Class

All 8 tests in the `TestShareModeTTS` class were updated to use `patch.object(LLMFrameworkGUI, '_load_modules')` since they create GUI instances directly without using the fixture.

### Part 2: Mock Gradio and PyTorch to Prevent Cleanup Issues

Created comprehensive mocks in `tests/conftest.py` to prevent PyTorch from being loaded during tests.

#### File: `tests/conftest.py`

```python
def pytest_configure(config):
    """Configure pytest."""
    # Suppress PyTorch/Gradio warnings during tests
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="torch")
    warnings.filterwarnings("ignore", category=UserWarning, module="gradio")
    warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

    # Mock gradio to prevent PyTorch loading during tests
    if 'gradio' not in sys.modules:
        # Create mock gradio module with all necessary components
        mock_gradio = MagicMock()

        # Mock gr.Radio to preserve choices and value
        class MockRadio:
            def __init__(self, choices=None, value=None, **kwargs):
                if choices and isinstance(choices, list):
                    if choices and not isinstance(choices[0], tuple):
                        self.choices = [(c, c) for c in choices]
                    else:
                        self.choices = choices
                else:
                    self.choices = choices
                self.value = value

        mock_gradio.Radio = MockRadio

        # Mock gr.update() to return a dict
        def mock_update(**kwargs):
            return kwargs
        mock_gradio.update = mock_update

        # Mock all other Gradio components as MagicMocks
        # (Blocks, Textbox, Button, Chatbot, etc.)

        sys.modules['gradio'] = mock_gradio

    # Mock torch to prevent PyTorch loading
    if 'torch' not in sys.modules:
        mock_torch = MagicMock()
        mock_torch.nn = MagicMock()
        mock_torch.nn.init = MagicMock()
        sys.modules['torch'] = mock_torch
        sys.modules['torch.nn'] = mock_torch.nn
        sys.modules['torch.nn.init'] = mock_torch.nn.init
```

### Part 3: Rename Manual Test Scripts

Renamed manual test script to prevent pytest from collecting it:
- `modules/speech2text/test_sst.py` → `modules/speech2text/manual_test_sst.py`

---

## Results

### ✅ Final Results:
- **All 262 tests passing** in ~1.4 seconds
- **NO hangs** from microphone access
- **NO KeyboardInterrupt** from PyTorch cleanup
- **Single command**: `pytest` runs entire suite successfully

### Test Breakdown:
- CLI tests: 75 tests ✅
- Config tests: 29 tests ✅
- LLM Runtime tests: 37 tests ✅
- Model Manager tests: 22 tests ✅
- Prompt Config tests: 14 tests ✅
- GUI tests: 85 tests ✅
- **Total: 262/262 tests passing** ✅

---

## Testing Commands

### Run All Tests (Simple):
```bash
source llf_venv/bin/activate
pytest
```

**Expected**: `262 passed in ~1.4s`

### Run Specific Test Suites:
```bash
# CLI tests only (75 tests)
pytest tests/test_cli.py

# GUI tests only (85 tests)
pytest tests/test_gui.py

# All non-GUI tests (177 tests)
pytest tests/ -k "not gui"

# Verbose output
pytest -v

# Quiet output
pytest -q
```

---

## Why This Solution Works

1. **`patch.object()`** - Intercepts the `_load_modules()` method call, preventing real TTS/STT module initialization
2. **Gradio Mock** - Prevents Gradio (and its PyTorch dependency) from being loaded during tests
3. **PyTorch Mock** - Ensures PyTorch is never actually imported, preventing cleanup issues
4. **MockRadio Class** - Properly preserves component state for tests that check Gradio component attributes
5. **No Production Code Changes** - All mocks are test-only, production code remains unchanged

---

## Files Modified

### Test Files:
1. `tests/test_cli.py` - Updated `cli` fixture to mock `_load_modules()`
2. `tests/test_gui.py` - Updated `gui` fixture and TestShareModeTTS class to mock `_load_modules()`
3. `tests/conftest.py` - Added comprehensive Gradio and PyTorch mocks
4. `modules/speech2text/test_sst.py` → `modules/speech2text/manual_test_sst.py` - Renamed to avoid pytest collection

### Configuration Files:
- `pytest.ini` - Already configured with proper test discovery patterns

---

## Summary

✅ **Problem 1**: Tests hung due to TTS/STT module initialization attempting microphone access
✅ **Solution 1**: Mock `_load_modules()` in test fixtures

✅ **Problem 2**: PyTorch cleanup caused KeyboardInterrupt after ~59 GUI tests
✅ **Solution 2**: Mock Gradio and PyTorch modules to prevent real imports

✅ **Result**: All 262 tests pass in single `pytest` command with no hangs or interrupts

The test suite is now fully functional and fast!
