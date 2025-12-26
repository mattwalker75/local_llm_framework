"""
Tests for logging configuration module.
"""

import pytest
import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch

from llf.logging_config import (
    ColoredFormatter,
    setup_logging,
    get_logger,
    set_level,
    LLF_LOGGER_PREFIX
)


class TestColoredFormatter:
    """Test ColoredFormatter class."""

    def test_format_with_color(self):
        """Test formatting with color enabled."""
        # Mock sys.stdout.isatty() to return True so colors are enabled in tests
        with patch('sys.stdout.isatty', return_value=True):
            formatter = ColoredFormatter("%(levelname)s - %(message)s", use_color=True)

            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None
            )

            result = formatter.format(record)

            # Should contain color codes for INFO in the result
            assert "Test message" in result
            # Check that result contains ANSI color codes
            assert "\033[" in result or "\x1b[" in result

    def test_format_without_color(self):
        """Test formatting with color disabled."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s", use_color=False)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        result = formatter.format(record)

        # Should not contain color codes
        assert "\033[" not in result
        assert "INFO - Test message" in result

    def test_format_different_levels(self):
        """Test formatting different log levels with color."""
        formatter = ColoredFormatter("%(levelname)s", use_color=True)

        for level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg="Test",
                args=(),
                exc_info=None
            )

            result = formatter.format(record)
            # Should have formatted the level name
            assert result  # Non-empty result

    def test_format_unknown_level_no_color(self):
        """Test formatting unknown log level doesn't crash."""
        formatter = ColoredFormatter("%(levelname)s", use_color=True)

        # Create record with custom level not in COLORS dict
        record = logging.LogRecord(
            name="test",
            level=25,  # Between INFO and WARNING
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.levelname = "CUSTOM"

        result = formatter.format(record)
        # Should not apply color for unknown level
        assert "CUSTOM" in result


class TestSetupLogging:
    """Test setup_logging function."""

    def teardown_method(self):
        """Clean up loggers after each test."""
        # Remove all handlers from LLF logger
        logger = logging.getLogger(LLF_LOGGER_PREFIX)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)

    def test_setup_logging_defaults(self):
        """Test setup with default parameters."""
        setup_logging()

        logger = logging.getLogger(LLF_LOGGER_PREFIX)

        # Check logger was configured
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert not logger.propagate

    def test_setup_logging_custom_level(self):
        """Test setup with custom log level."""
        setup_logging(level="DEBUG")

        logger = logging.getLogger(LLF_LOGGER_PREFIX)

        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.DEBUG

    def test_setup_logging_custom_format(self):
        """Test setup with custom format string."""
        custom_format = "%(name)s - %(message)s"
        setup_logging(log_format=custom_format)

        logger = logging.getLogger(LLF_LOGGER_PREFIX)

        # Check formatter uses custom format
        formatter = logger.handlers[0].formatter
        assert isinstance(formatter, ColoredFormatter)

    def test_setup_logging_with_file(self, tmp_path):
        """Test setup with file logging."""
        log_file = tmp_path / "logs" / "test.log"

        setup_logging(log_file=log_file)

        logger = logging.getLogger(LLF_LOGGER_PREFIX)

        # Should have 2 handlers: console + file
        assert len(logger.handlers) == 2

        # Find file handler
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1

        # Verify directory was created
        assert log_file.parent.exists()

    def test_setup_logging_without_color(self):
        """Test setup with color disabled."""
        setup_logging(use_color=False)

        logger = logging.getLogger(LLF_LOGGER_PREFIX)

        # Check formatter has color disabled
        formatter = logger.handlers[0].formatter
        assert isinstance(formatter, ColoredFormatter)
        assert not formatter.use_color

    def test_setup_logging_clears_existing_handlers(self):
        """Test that setup clears existing handlers."""
        # Setup logging twice
        setup_logging()
        setup_logging()

        logger = logging.getLogger(LLF_LOGGER_PREFIX)

        # Should only have 1 console handler, not 2
        assert len(logger.handlers) == 1

    def test_setup_logging_invalid_level_uses_info(self):
        """Test that invalid log level defaults to INFO."""
        setup_logging(level="INVALID")

        logger = logging.getLogger(LLF_LOGGER_PREFIX)

        # Should fall back to INFO
        assert logger.level == logging.INFO

    def test_setup_logging_case_insensitive_level(self):
        """Test that log level is case-insensitive."""
        setup_logging(level="warning")

        logger = logging.getLogger(LLF_LOGGER_PREFIX)

        assert logger.level == logging.WARNING


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_with_module_name(self):
        """Test getting logger with simple module name."""
        logger = get_logger("test_module")

        assert logger.name == f"{LLF_LOGGER_PREFIX}.test_module"

    def test_get_logger_with_prefix(self):
        """Test getting logger when name already has prefix."""
        full_name = f"{LLF_LOGGER_PREFIX}.test_module"
        logger = get_logger(full_name)

        # Should not double-prefix
        assert logger.name == full_name
        assert logger.name.count(LLF_LOGGER_PREFIX) == 1

    def test_get_logger_different_names(self):
        """Test getting multiple loggers."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name != logger2.name
        assert "module1" in logger1.name
        assert "module2" in logger2.name


class TestSetLevel:
    """Test set_level function."""

    def setup_method(self):
        """Set up logging before each test."""
        setup_logging(level="INFO")

    def teardown_method(self):
        """Clean up after each test."""
        logger = logging.getLogger(LLF_LOGGER_PREFIX)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)

    def test_set_level_changes_logger_level(self):
        """Test that set_level changes the logger level."""
        set_level("DEBUG")

        logger = logging.getLogger(LLF_LOGGER_PREFIX)

        assert logger.level == logging.DEBUG

    def test_set_level_changes_handler_levels(self):
        """Test that set_level changes all handler levels."""
        set_level("WARNING")

        logger = logging.getLogger(LLF_LOGGER_PREFIX)

        for handler in logger.handlers:
            assert handler.level == logging.WARNING

    def test_set_level_case_insensitive(self):
        """Test that set_level is case-insensitive."""
        set_level("error")

        logger = logging.getLogger(LLF_LOGGER_PREFIX)

        assert logger.level == logging.ERROR

    def test_set_level_invalid_defaults_to_info(self):
        """Test that invalid level defaults to INFO."""
        set_level("INVALID")

        logger = logging.getLogger(LLF_LOGGER_PREFIX)

        assert logger.level == logging.INFO

    def test_set_level_multiple_handlers(self, tmp_path):
        """Test set_level with multiple handlers."""
        # Setup with file handler
        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file, level="INFO")

        # Change level
        set_level("DEBUG")

        logger = logging.getLogger(LLF_LOGGER_PREFIX)

        # All handlers should have new level
        assert logger.level == logging.DEBUG
        for handler in logger.handlers:
            assert handler.level == logging.DEBUG
