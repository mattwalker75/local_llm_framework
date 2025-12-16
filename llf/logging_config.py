"""
Logging configuration for Local LLM Framework.

This module provides centralized logging configuration for all LLF components.

Design: Uses Python's standard logging library with configurable levels and formats.
Future: Can be extended to support file logging, log rotation, and structured logging.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


# Logger name prefix for all LLF loggers
LLF_LOGGER_PREFIX = "llf"


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds color to log levels for console output.

    Only applies colors when outputting to a TTY terminal.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def __init__(self, fmt: Optional[str] = None, use_color: bool = True):
        """
        Initialize colored formatter.

        Args:
            fmt: Log format string.
            use_color: Whether to use colors (automatically disabled for non-TTY).
        """
        super().__init__(fmt)
        self.use_color = use_color and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with optional color.

        Args:
            record: Log record to format.

        Returns:
            Formatted log message.
        """
        if self.use_color and record.levelname in self.COLORS:
            # Add color to level name
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[Path] = None,
    use_color: bool = True
) -> None:
    """
    Configure logging for the entire LLF application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Custom log format string. If None, uses default.
        log_file: Optional path to log file. If provided, logs to both console and file.
        use_color: Whether to use colored output for console logging.
    """
    # Default format if not provided
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Get root logger for LLF
    logger = logging.getLogger(LLF_LOGGER_PREFIX)
    logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with optional color
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = ColoredFormatter(log_format, use_color=use_color)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        # File logs should not have color codes
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific LLF module.

    Args:
        name: Name of the module (will be prefixed with 'llf.').

    Returns:
        Logger instance for the module.
    """
    if name.startswith(LLF_LOGGER_PREFIX):
        return logging.getLogger(name)
    return logging.getLogger(f"{LLF_LOGGER_PREFIX}.{name}")


def set_level(level: str) -> None:
    """
    Change the logging level for all LLF loggers.

    Args:
        level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger = logging.getLogger(LLF_LOGGER_PREFIX)
    logger.setLevel(numeric_level)
    for handler in logger.handlers:
        handler.setLevel(numeric_level)


def disable_external_loggers(libraries: Optional[list] = None) -> None:
    """
    Reduce verbosity of external library loggers.

    Args:
        libraries: List of library names to quiet. If None, uses common defaults.
    """
    if libraries is None:
        # Common noisy libraries
        libraries = [
            'transformers',
            'torch',
            'vllm',
            'openai',
            'httpx',
            'httpcore',
            'urllib3',
        ]

    for lib in libraries:
        logging.getLogger(lib).setLevel(logging.WARNING)
