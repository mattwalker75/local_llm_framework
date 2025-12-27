"""
pytest configuration for test suite.
Uses simple manual mocks instead of MagicMock to avoid cleanup KeyboardInterrupt.
"""
import pytest
import warnings
import sys
import signal
import atexit
import gc


# Simple mock classes that don't use MagicMock (avoids cleanup issues)
class SimpleMock:
    """Simple mock object that accepts any attribute/method call."""
    def __init__(self, return_value=None, **kwargs):
        self._return_value = return_value
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __call__(self, *args, **kwargs):
        return self._return_value if self._return_value is not None else SimpleMock()

    def __getattr__(self, name):
        return SimpleMock()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


# Register an atexit handler to ignore signals during cleanup
def _ignore_signals():
    """Ignore interrupt signals during Python shutdown."""
    try:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    except:
        pass

atexit.register(_ignore_signals)


def pytest_configure(config):
    """Configure pytest."""
    # Suppress PyTorch/Gradio warnings during tests
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="torch")
    warnings.filterwarnings("ignore", category=UserWarning, module="gradio")
    warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

    # Mock gradio to prevent PyTorch loading during tests
    # This avoids the PyTorch cleanup KeyboardInterrupt issue
    if 'gradio' not in sys.modules:
        # Create a mock gradio module with necessary components using SimpleMock
        mock_gradio = SimpleMock()

        # Mock Radio component to preserve choices and value
        class MockRadio:
            """Mock Radio component that preserves choices and value."""
            def __init__(self, choices=None, value=None, **kwargs):
                # Convert simple list to tuples if needed
                if choices and isinstance(choices, list):
                    if choices and not isinstance(choices[0], tuple):
                        self.choices = [(c, c) for c in choices]
                    else:
                        self.choices = choices
                else:
                    self.choices = choices
                self.value = value
                # Add SimpleMock for method calls
                self.change = SimpleMock(return_value=SimpleMock())
                self.click = SimpleMock(return_value=SimpleMock())
                self.submit = SimpleMock(return_value=SimpleMock())

        # Set up gradio components using SimpleMock
        mock_gradio.Blocks = SimpleMock(return_value=SimpleMock())
        mock_gradio.Textbox = SimpleMock(return_value=SimpleMock())
        mock_gradio.Button = SimpleMock(return_value=SimpleMock())
        mock_gradio.Chatbot = SimpleMock(return_value=SimpleMock())
        mock_gradio.Row = SimpleMock(return_value=SimpleMock())
        mock_gradio.Column = SimpleMock(return_value=SimpleMock())
        mock_gradio.Tab = SimpleMock(return_value=SimpleMock())
        mock_gradio.Tabs = SimpleMock(return_value=SimpleMock())
        mock_gradio.Dropdown = SimpleMock(return_value=SimpleMock())
        mock_gradio.Radio = MockRadio  # Use custom mock for Radio
        mock_gradio.Checkbox = SimpleMock(return_value=SimpleMock())
        mock_gradio.Markdown = SimpleMock(return_value=SimpleMock())
        mock_gradio.HTML = SimpleMock(return_value=SimpleMock())
        mock_gradio.Accordion = SimpleMock(return_value=SimpleMock())
        mock_gradio.Group = SimpleMock(return_value=SimpleMock())
        mock_gradio.Audio = SimpleMock(return_value=SimpleMock())

        # Mock gr.update() to return a dict-like object with proper attribute access
        def mock_update(**kwargs):
            """Mock gr.update() to return a dict with the provided kwargs."""
            return kwargs

        mock_gradio.update = mock_update

        # Add to sys.modules BEFORE gradio is imported
        sys.modules['gradio'] = mock_gradio

    # Also mock torch to prevent PyTorch loading
    # Gradio may have already loaded PyTorch before we mock it
    if 'torch' not in sys.modules:
        mock_torch = SimpleMock()
        mock_torch.nn = SimpleMock()
        mock_torch.nn.init = SimpleMock()
        mock_torch.nn.functional = SimpleMock()
        mock_torch.cuda = SimpleMock()
        mock_torch.cuda.is_available = SimpleMock(return_value=False)

        sys.modules['torch'] = mock_torch
        sys.modules['torch.nn'] = mock_torch.nn
        sys.modules['torch.nn.init'] = mock_torch.nn.init
        sys.modules['torch.nn.functional'] = mock_torch.nn.functional
        sys.modules['torch.cuda'] = mock_torch.cuda

    # Mock whisper module to prevent PyTorch loading for STT tests
    if 'whisper' not in sys.modules:
        mock_whisper = SimpleMock()
        mock_whisper.load_model = SimpleMock(return_value=SimpleMock())
        sys.modules['whisper'] = mock_whisper
        sys.modules['whisper.audio'] = SimpleMock()
        sys.modules['whisper.model'] = SimpleMock()

    # Mock sounddevice to prevent audio device access
    if 'sounddevice' not in sys.modules:
        mock_sounddevice = SimpleMock()
        mock_sounddevice.InputStream = SimpleMock()
        # Create a proper exception class for PortAudioError
        class MockPortAudioError(Exception):
            """Mock PortAudioError exception."""
            pass
        mock_sounddevice.PortAudioError = MockPortAudioError
        sys.modules['sounddevice'] = mock_sounddevice

    # Mock pyttsx3 for TTS tests
    if 'pyttsx3' not in sys.modules:
        mock_pyttsx3 = SimpleMock()
        mock_pyttsx3.init = SimpleMock(return_value=SimpleMock())
        sys.modules['pyttsx3'] = mock_pyttsx3

    # Mock scipy.io.wavfile to prevent file I/O during tests
    if 'scipy.io.wavfile' not in sys.modules:
        mock_scipy = SimpleMock()
        mock_scipy.io = SimpleMock()
        mock_scipy.io.wavfile = SimpleMock()
        mock_scipy.io.wavfile.write = SimpleMock()
        sys.modules['scipy'] = mock_scipy
        sys.modules['scipy.io'] = mock_scipy.io
        sys.modules['scipy.io.wavfile'] = mock_scipy.io.wavfile



def pytest_sessionfinish(session, exitstatus):
    """Called after test run - do cleanup."""
    # Ignore all interrupts during cleanup
    _ignore_signals()

    # Force immediate garbage collection
    gc.collect()
    gc.collect()

    # Keep signals ignored
    _ignore_signals()


def pytest_keyboard_interrupt(excinfo):
    """Suppress KeyboardInterrupt - always return True to prevent display."""
    return True


# Wrap test execution to handle interrupts
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Wrap test execution to handle interrupts gracefully."""
    _ignore_signals()  # Ignore signals before test
    yield  # Run the test
    _ignore_signals()  # Ignore signals after test

