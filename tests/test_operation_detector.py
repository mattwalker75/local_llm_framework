"""
Unit tests for operation type detection.
"""

import pytest
from llf.operation_detector import (
    detect_operation_type,
    should_use_dual_pass,
    OperationType
)


class TestOperationDetector:
    """Test operation type detection functionality."""

    def test_detect_read_operations(self):
        """Test detection of READ operations."""
        read_messages = [
            "What's my name?",
            "What is my favorite color?",
            "Do you remember my birthday?",
            "Can you recall what I said?",
            "Tell me about my preferences",
            "What did I tell you earlier?",
            "Retrieve my user information",
            "Show me my settings",
        ]

        for msg in read_messages:
            assert detect_operation_type(msg) == OperationType.READ, f"Failed to detect READ: {msg}"

    def test_detect_write_operations(self):
        """Test detection of WRITE operations."""
        write_messages = [
            "Remember that my name is John",
            "My favorite color is blue",
            "I like pizza",
            "Store this information",
            "Save my preference",
            "Keep track of my birthday",
            "Add this to memory",
            "I prefer dark mode",
        ]

        for msg in write_messages:
            assert detect_operation_type(msg) == OperationType.WRITE, f"Failed to detect WRITE: {msg}"

    def test_detect_general_operations(self):
        """Test detection of GENERAL operations."""
        general_messages = [
            "Tell me a joke",
            "How's the weather?",
            "Explain quantum physics",
            "Write a poem",
            "What is 2 + 2?",
            "Hello, how are you?",
        ]

        for msg in general_messages:
            assert detect_operation_type(msg) == OperationType.GENERAL, f"Failed to detect GENERAL: {msg}"

    def test_case_insensitivity(self):
        """Test that detection is case-insensitive."""
        assert detect_operation_type("WHAT'S MY NAME?") == OperationType.READ
        assert detect_operation_type("remember this") == OperationType.WRITE
        assert detect_operation_type("TELL ME A JOKE") == OperationType.GENERAL

    def test_empty_message(self):
        """Test handling of empty messages."""
        assert detect_operation_type("") == OperationType.GENERAL
        assert detect_operation_type("   ") == OperationType.GENERAL


class TestDualPassDecision:
    """Test dual-pass execution decision logic."""

    def test_single_pass_mode_never_dual_pass(self):
        """Test that single_pass mode never uses dual-pass."""
        assert should_use_dual_pass(OperationType.READ, "single_pass", True) is False
        assert should_use_dual_pass(OperationType.WRITE, "single_pass", True) is False
        assert should_use_dual_pass(OperationType.GENERAL, "single_pass", True) is False

    def test_dual_pass_all_mode_always_dual_pass(self):
        """Test that dual_pass_all mode always uses dual-pass when tools available."""
        assert should_use_dual_pass(OperationType.READ, "dual_pass_all", True) is True
        assert should_use_dual_pass(OperationType.WRITE, "dual_pass_all", True) is True
        assert should_use_dual_pass(OperationType.GENERAL, "dual_pass_all", True) is True

        # But not when tools are unavailable
        assert should_use_dual_pass(OperationType.READ, "dual_pass_all", False) is False

    def test_dual_pass_write_only_mode(self):
        """Test that dual_pass_write_only only uses dual-pass for WRITE operations."""
        # WRITE operations should use dual-pass
        assert should_use_dual_pass(OperationType.WRITE, "dual_pass_write_only", True) is True

        # READ and GENERAL should not
        assert should_use_dual_pass(OperationType.READ, "dual_pass_write_only", True) is False
        assert should_use_dual_pass(OperationType.GENERAL, "dual_pass_write_only", True) is False

    def test_no_tools_available_never_dual_pass(self):
        """Test that dual-pass is never used when tools are unavailable."""
        assert should_use_dual_pass(OperationType.WRITE, "dual_pass_all", False) is False
        assert should_use_dual_pass(OperationType.WRITE, "dual_pass_write_only", False) is False
        assert should_use_dual_pass(OperationType.READ, "dual_pass_all", False) is False

    def test_unknown_mode_defaults_to_single_pass(self):
        """Test that unknown modes default to single-pass (safe behavior)."""
        assert should_use_dual_pass(OperationType.WRITE, "unknown_mode", True) is False
        assert should_use_dual_pass(OperationType.READ, "invalid", True) is False


class TestOperationTypeEnum:
    """Test OperationType enum."""

    def test_enum_values(self):
        """Test that enum has expected values."""
        assert OperationType.READ == "READ"
        assert OperationType.WRITE == "WRITE"
        assert OperationType.GENERAL == "GENERAL"

    def test_enum_membership(self):
        """Test enum membership checks."""
        assert OperationType.READ in OperationType
        assert OperationType.WRITE in OperationType
        assert OperationType.GENERAL in OperationType
