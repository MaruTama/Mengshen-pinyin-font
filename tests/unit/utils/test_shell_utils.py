# -*- coding: utf-8 -*-
"""
Tests for shell_utils security module.

This module tests secure shell command execution functionality, ensuring that
shell injection vulnerabilities are prevented while maintaining functionality.
Following TDD principles with comprehensive security coverage.
"""

import subprocess
from unittest.mock import Mock, patch

import pytest

from refactored.utils.shell_utils import (
    SecurityError,
    ShellExecutor,
    safe_command_execution,
)


class TestSecurityError:
    """Test SecurityError exception functionality."""

    def test_security_error_creation(self):
        """Test creating SecurityError with message."""
        error = SecurityError("Test security violation")
        assert str(error) == "Test security violation"
        assert isinstance(error, Exception)

    def test_security_error_inheritance(self):
        """Test SecurityError is proper exception subclass."""
        error = SecurityError("Test message")
        assert isinstance(error, Exception)


class TestSafeCommandExecution:
    """Test safe_command_execution function."""

    def test_safe_command_execution_list_format(self):
        """Test that safe commands in list format are executed properly."""
        # Test with a simple, safe command
        result = safe_command_execution(["echo", "hello"])
        assert result is not None
        assert isinstance(result, subprocess.CompletedProcess)
        assert b"hello" in result.stdout

    def test_safe_command_execution_rejects_string(self):
        """Test that string commands are rejected for security."""
        with pytest.raises(SecurityError, match="String commands not allowed"):
            safe_command_execution("echo hello")

    def test_safe_command_execution_rejects_non_list(self):
        """Test that non-list commands are rejected."""
        with pytest.raises(SecurityError, match="Command must be a list"):
            safe_command_execution(123)

        with pytest.raises(SecurityError, match="Command must be a list"):
            safe_command_execution(None)

    def test_safe_command_execution_validates_list_elements(self):
        """Test that all command elements must be strings."""
        with pytest.raises(
            SecurityError, match="All command arguments must be strings"
        ):
            safe_command_execution(["echo", 123])

        with pytest.raises(
            SecurityError, match="All command arguments must be strings"
        ):
            safe_command_execution(["echo", None])

    def test_safe_command_execution_empty_list(self):
        """Test that empty command lists are handled."""
        # This should either work or raise a specific error
        try:
            result = safe_command_execution([])
            # If it works, it should return a CompletedProcess
            assert isinstance(result, subprocess.CompletedProcess)
        except (SecurityError, FileNotFoundError, subprocess.SubprocessError):
            # These are acceptable errors for empty commands
            pass

    @patch("subprocess.run")
    def test_safe_command_execution_calls_subprocess(self, mock_run):
        """Test that safe_command_execution properly calls subprocess.run."""
        mock_result = Mock(spec=subprocess.CompletedProcess)
        mock_result.stdout = b"test output"
        mock_result.stderr = b""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = safe_command_execution(["echo", "test"])

        # Verify subprocess.run was called with correct arguments
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["echo", "test"]  # First positional argument
        assert call_args[1]["shell"] is False  # Keyword argument
        assert call_args[1]["capture_output"] is True
        assert result == mock_result


class TestShellExecutor:
    """Test ShellExecutor class."""

    def test_shell_executor_initialization(self):
        """Test ShellExecutor can be initialized."""
        executor = ShellExecutor()
        assert executor is not None

    def test_shell_executor_execute_list_command(self):
        """Test ShellExecutor.execute with list command."""
        executor = ShellExecutor()
        result = executor.execute(["echo", "test"])
        assert isinstance(result, subprocess.CompletedProcess)
        assert b"test" in result.stdout

    def test_shell_executor_execute_rejects_string(self):
        """Test ShellExecutor.execute rejects string commands."""
        executor = ShellExecutor()
        with pytest.raises(SecurityError):
            executor.execute("echo test")

    def test_shell_executor_execute_validates_input(self):
        """Test ShellExecutor.execute validates input."""
        executor = ShellExecutor()

        with pytest.raises(SecurityError):
            executor.execute(["echo", 123])  # Non-string argument

        with pytest.raises(SecurityError):
            executor.execute(None)  # None input


class TestSecurityValidation:
    """Test security validation and edge cases."""

    def test_command_injection_prevention(self):
        """Test that command injection attacks are prevented."""
        malicious_commands = [
            "echo hello && rm -rf /",
            "echo hello; cat /etc/passwd",
            "echo hello | sh",
            'echo "hello"; rm -rf /',
            "echo hello`rm -rf /`",
            "echo hello$(rm -rf /)",
        ]

        for malicious_cmd in malicious_commands:
            with pytest.raises(SecurityError):
                safe_command_execution(malicious_cmd)

    def test_shell_operator_in_arguments_blocked(self):
        """Test that shell operators in arguments are blocked for security."""
        # The security implementation blocks shell operators even in arguments
        with pytest.raises(SecurityError, match="Dangerous shell operator"):
            safe_command_execution(["echo", "hello && world"])

        with pytest.raises(SecurityError, match="Dangerous shell operator"):
            safe_command_execution(["echo", "hello; world"])

    def test_complex_valid_commands(self):
        """Test complex but valid commands work."""
        # Test command with multiple arguments
        result = safe_command_execution(["echo", "-n", "hello world"])
        assert b"hello world" in result.stdout

        # Test command with special characters in arguments
        result = safe_command_execution(["echo", "special!@#$%chars"])
        assert b"special!@#$%chars" in result.stdout

    def test_subprocess_error_handling(self):
        """Test that subprocess errors are handled properly."""
        # Test with non-existent command - should fail at allowlist validation
        with pytest.raises(SecurityError, match="Command not in allowlist"):
            safe_command_execution(["non_existent_command_12345"])

    @patch("subprocess.run")
    def test_subprocess_run_parameters(self, mock_run):
        """Test that subprocess.run is called with security parameters."""
        mock_result = Mock(spec=subprocess.CompletedProcess)
        mock_result.stdout = b"test output"
        mock_result.stderr = b""
        mock_result.returncode = 0
        mock_result.args = ["echo", "test"]
        mock_run.return_value = mock_result

        safe_command_execution(["echo", "test"])

        # Verify security-critical parameters
        call_args = mock_run.call_args
        assert call_args[1]["shell"] is False  # Most important security parameter
        assert call_args[1]["capture_output"] is True
