"""
pytest configuration for test suite.
"""
import pytest
import warnings


def pytest_configure(config):
    """Configure pytest."""
    # Suppress PyTorch/Gradio warnings during tests
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="torch")
    warnings.filterwarnings("ignore", category=UserWarning, module="gradio")
    warnings.filterwarnings("ignore", category=FutureWarning, module="torch")
