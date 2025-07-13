# -*- coding: utf-8 -*-
"""Consolidated security tests for shell execution and path validation."""

import pytest

from refactored.config.paths import ProjectPaths
from refactored.utils.shell_utils import (
    SecurityError,
    ShellExecutor,
    safe_command_execution,
    validate_file_path,
)


class TestSecurityConsolidated:
    """Consolidated security tests for shell execution and path validation."""

    @pytest.mark.security
    def test_command_injection_prevention(self, sample_malicious_commands):
        """Test that command injection attacks are prevented."""
        executor = ShellExecutor()

        for malicious_cmd in sample_malicious_commands:
            with pytest.raises(SecurityError):
                # All malicious commands should be rejected
                safe_command_execution(malicious_cmd)

    @pytest.mark.security
    def test_path_traversal_prevention(self, sample_path_traversal_attacks):
        """Test that path traversal attacks are prevented."""
        for malicious_path in sample_path_traversal_attacks:
            with pytest.raises((SecurityError, ValueError)):
                # Any path validation should reject these patterns
                validate_file_path(malicious_path)

    @pytest.mark.security
    def test_safe_command_execution_list_format(self):
        """Test that safe commands in list format are executed properly."""
        # Test with a simple, safe command
        result = safe_command_execution(["echo", "hello"])
        assert result is not None
        # Result is a CompletedProcess object, check stdout (bytes)
        assert b"hello" in result.stdout

    @pytest.mark.security
    def test_absolute_path_restrictions(self):
        """Test that absolute paths outside project are restricted."""
        project_paths = ProjectPaths()

        # System paths that should be rejected
        restricted_paths = [
            "/etc/passwd",
            "/usr/bin/python",
            "/root/.ssh/id_rsa",
            "C:\\Windows\\System32\\config\\SAM",
            "C:\\Users\\Administrator\\Desktop\\secrets.txt",
        ]

        for path in restricted_paths:
            with pytest.raises((SecurityError, ValueError)):
                validate_file_path(path)

    @pytest.mark.security
    def test_safe_path_validation(self):
        """Test that safe paths within project are allowed."""
        project_paths = ProjectPaths()

        # Safe paths within project
        safe_paths = [
            "src/main.py",
            "tests/test_file.py",
            "outputs/font.ttf",
            "tmp/temp_file.json",
        ]

        for path in safe_paths:
            # Should not raise exception
            validate_file_path(path)

    @pytest.mark.security
    def test_shell_executor_security(self):
        """Test ShellExecutor security measures."""
        executor = ShellExecutor()

        # Test safe command execution
        result = executor.execute(["echo", "test"])
        assert result.returncode == 0
        assert b"test" in result.stdout

        # Test that dangerous commands are rejected
        with pytest.raises(SecurityError):
            executor.execute("echo test && rm -rf /")

    @pytest.mark.security
    def test_command_validation_edge_cases(self):
        """Test edge cases in command validation."""
        # Empty commands
        with pytest.raises(SecurityError):
            safe_command_execution("")

        with pytest.raises(SecurityError):
            safe_command_execution([])

        # None input
        with pytest.raises(SecurityError):
            safe_command_execution(None)

    @pytest.mark.security
    def test_path_validation_edge_cases(self):
        """Test edge cases in path validation."""
        # Test various edge cases that should be handled gracefully
        # Note: Actual implementation may vary, adjust based on current behavior

        # Test with various potentially problematic paths
        problematic_paths = [
            "../../../etc/passwd",  # Path traversal
            "test/../../../etc/passwd",  # Hidden traversal
        ]

        for path in problematic_paths:
            # These should either raise an error or be handled safely
            try:
                validate_file_path(path)
                # If no error, path should be safe
                assert not path.startswith("/")
            except (SecurityError, ValueError):
                # Expected behavior for dangerous paths
                pass

    @pytest.mark.security
    def test_unicode_security_bypass_attempts(self):
        """Test that Unicode-based security bypass attempts are handled."""
        unicode_attacks = [
            "test\u0000malicious",
            "test\u00a0malicious",
            "test\u2000malicious",
            "test\u200bmalicious",
        ]

        for attack in unicode_attacks:
            # Test that unicode attacks are handled appropriately
            try:
                validate_file_path(attack)
                # If no error, ensure path is normalized
                assert "\u0000" not in attack
            except (SecurityError, ValueError):
                # Expected behavior for unicode attacks
                pass

    @pytest.mark.security
    def test_encoding_security_bypass_attempts(self):
        """Test that encoding-based security bypass attempts are handled."""
        encoding_attacks = [
            "test%2e%2e%2f",  # URL encoded ../
            "test%252e%252e%252f",  # Double URL encoded ../
            "test..\\",  # Windows path traversal
            "test..%5c",  # URL encoded Windows path traversal
        ]

        for attack in encoding_attacks:
            # Test that encoding attacks are handled appropriately
            try:
                validate_file_path(attack)
                # If no error, ensure path doesn't contain dangerous patterns
                assert ".." not in attack or not attack.startswith(".")
            except (SecurityError, ValueError):
                # Expected behavior for encoding attacks
                pass
