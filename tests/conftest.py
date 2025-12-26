"""
pytest configuration for test suite.
"""
import pytest
import warnings
import sys
from unittest.mock import MagicMock


def pytest_configure(config):
    """Configure pytest."""
    # Suppress PyTorch/Gradio warnings during tests
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="torch")
    warnings.filterwarnings("ignore", category=UserWarning, module="gradio")
    warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

    # Mock gradio to prevent PyTorch loading during tests
    # This avoids the PyTorch cleanup KeyboardInterrupt issue
    if 'gradio' not in sys.modules:
        # Create a mock gradio module with necessary components
        mock_gradio = MagicMock()

        # Mock the Blocks context manager
        mock_blocks = MagicMock()
        mock_blocks.__enter__ = MagicMock(return_value=mock_blocks)
        mock_blocks.__exit__ = MagicMock(return_value=False)
        mock_blocks.launch = MagicMock()
        mock_blocks.queue = MagicMock(return_value=mock_blocks)

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

        # Set up gradio components
        mock_gradio.Blocks = MagicMock(return_value=mock_blocks)
        mock_gradio.Textbox = MagicMock(return_value=MagicMock())
        mock_gradio.Button = MagicMock(return_value=MagicMock())
        mock_gradio.Chatbot = MagicMock(return_value=MagicMock())
        mock_gradio.Row = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
        mock_gradio.Column = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
        mock_gradio.Tab = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
        mock_gradio.Tabs = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
        mock_gradio.Dropdown = MagicMock(return_value=MagicMock())
        mock_gradio.Radio = MockRadio  # Use custom mock for Radio
        mock_gradio.Checkbox = MagicMock(return_value=MagicMock())
        mock_gradio.Markdown = MagicMock(return_value=MagicMock())
        mock_gradio.HTML = MagicMock(return_value=MagicMock())
        mock_gradio.Accordion = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
        mock_gradio.Group = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
        mock_gradio.Audio = MagicMock(return_value=MagicMock())

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
        mock_torch = MagicMock()
        mock_torch.nn = MagicMock()
        mock_torch.nn.init = MagicMock()
        sys.modules['torch'] = mock_torch
        sys.modules['torch.nn'] = mock_torch.nn
        sys.modules['torch.nn.init'] = mock_torch.nn.init
