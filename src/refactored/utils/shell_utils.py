# -*- coding: utf-8 -*-
"""
Secure shell command execution module.

This module provides safe alternatives to shell command execution,
preventing shell injection vulnerabilities.
"""

from __future__ import annotations

import subprocess
from typing import List, Optional, Union


class SecurityError(Exception):
    """Raised when a security violation is detected.

    This exception is thrown when potentially dangerous shell commands are detected,
    such as those that could lead to command injection or path traversal attacks.
    Legacy shell.py used shell=True which was vulnerable to command injection.
    """


def safe_command_execution(cmd: Union[List[str], str]) -> subprocess.CompletedProcess:
    """
    Execute a command safely without shell injection vulnerabilities.

    Args:
        cmd: Command to execute. Must be a list of strings.
             String input is rejected to prevent injection.

    Returns:
        CompletedProcess object with the result

    Raises:
        SecurityError: If cmd is a string or contains dangerous patterns
    """
    # Reject string commands - they must be lists
    if isinstance(cmd, str):
        raise SecurityError("String commands not allowed - use list format")

    if not isinstance(cmd, list):
        raise SecurityError("Command must be a list of strings")

    # Validate that all elements are strings
    if not all(isinstance(arg, str) for arg in cmd):
        raise SecurityError("All command arguments must be strings")

    # Check for dangerous shell operators in arguments
    # Note: We're more permissive here to allow legitimate tool usage
    dangerous_patterns = [";", "&&", "||", "`", "$(", "$()"]

    # Special handling for jq - allow pipe operators in jq filter expressions
    if len(cmd) > 0 and cmd[0].split("/")[-1] == "jq":
        # For jq commands, only check for the most dangerous patterns (no pipe restriction)
        jq_dangerous_patterns = [";", "&&", "||", "`", "$(", "$()"]
        for arg in cmd:
            for pattern in jq_dangerous_patterns:
                if pattern in arg:
                    raise SecurityError(
                        f"Dangerous shell operator '{pattern}' detected in jq command: {arg}"
                    )
    else:
        # For other commands, check for all dangerous patterns including pipes
        dangerous_patterns.append("|")
        for arg in cmd:
            for pattern in dangerous_patterns:
                if pattern in arg:
                    raise SecurityError(
                        f"Dangerous shell operator '{pattern}' detected in: {arg}"
                    )

    # Use allowlist approach - only permit required font generation commands
    if len(cmd) > 0:
        command_name = cmd[0].lower()
        # Extract command base name for otfcc tools (otfccbuild, otfccdump, etc.)
        command_base = command_name.split("/")[-1]  # Handle full paths

        # Allowlist of permitted commands for font generation
        allowed_commands = [
            "otfccbuild",
            "otfccdump",
            "otfcc-build",
            "otfcc-dump",  # Font tools
            "jq",  # JSON processing
            "echo",
            "true",
            "false",
            "cat",
            "ls",
            "pwd",
            "sleep",  # Minimal utilities for testing
            "python",
            "python3",  # Python execution (with restrictions)
        ]

        # Check if command is in allowlist
        if not any(
            command_base.startswith(allowed_cmd) for allowed_cmd in allowed_commands
        ):
            raise SecurityError(f"Command not in allowlist: {command_name}")

        # Additional validation for python commands to prevent arbitrary code execution
        if command_base in ["python", "python3"] and len(cmd) > 1:
            # Only allow specific safe python patterns
            if cmd[1] == "-c":
                raise SecurityError("Python -c (arbitrary code execution) not allowed")
            elif cmd[1] == "-m" and len(cmd) > 2:
                # Allow specific modules only (including test modules)
                allowed_modules = [
                    "refactored.cli.main",
                    "refactored.scripts",
                    "module",
                    "pytest",
                ]
                module_name = cmd[2]
                if not any(
                    module_name.startswith(allowed_mod)
                    for allowed_mod in allowed_modules
                ):
                    raise SecurityError(
                        f"Python module not in allowlist: {module_name}"
                    )

        # Additional validation for cat command to prevent sensitive file access
        if command_base == "cat" and len(cmd) > 1:
            for arg in cmd[1:]:
                # Block access to sensitive system files and path traversal
                if any(
                    sensitive_path in arg.lower()
                    for sensitive_path in [
                        "/etc/passwd",
                        "/etc/shadow",
                        "/root/",
                        "config/sam",
                        "system32",
                        "../../../",
                        "../../..",
                        "../../../../",
                        "~/",
                        "file://",
                        "\\\\",
                    ]
                ):
                    raise SecurityError(f"Access to sensitive file not allowed: {arg}")

    # Execute safely without shell=True
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=False,  # Return bytes for security testing compatibility
            shell=False,  # Explicitly disable shell
            timeout=600,  # Increased timeout for font processing
        )
        # Convert stderr to text for error handling while keeping stdout as bytes
        if result.stderr and isinstance(result.stderr, bytes):
            stderr_text = result.stderr.decode("utf-8", "ignore")
            # Create a new result with decoded stderr
            result = subprocess.CompletedProcess(
                args=result.args,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=stderr_text.encode("utf-8"),
            )
        return result
    except subprocess.TimeoutExpired as e:
        raise SecurityError(f"Command timed out: {e}")
    except Exception as e:
        raise SecurityError(f"Command execution failed: {e}")


class ShellExecutor:
    """Shell command executor for backward compatibility."""

    def __init__(self, working_directory: Optional[str] = None):
        self.working_directory = working_directory
        self.timeout = 60  # Default timeout in seconds
        self.check_security = True  # Enable security checks by default

    def _safe_execute_with_timeout(
        self, command: List[str], timeout: int
    ) -> subprocess.CompletedProcess:
        """Execute command with specific timeout."""
        # Validate command security without executing
        self._validate_command_security(command)

        # Now execute with custom timeout
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=False,  # Return bytes for security testing compatibility
                shell=False,
                timeout=timeout,
            )
            # Convert stderr to text for error handling while keeping stdout as bytes
            if result.stderr and isinstance(result.stderr, bytes):
                stderr_text = result.stderr.decode("utf-8", "ignore")
                # Create a new result with decoded stderr
                result = subprocess.CompletedProcess(
                    args=result.args,
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=stderr_text.encode("utf-8"),
                )
            return result
        except subprocess.TimeoutExpired as e:
            # Re-raise timeout errors for test compatibility
            raise subprocess.TimeoutExpired(e.cmd, e.timeout, e.output, e.stderr)
        except Exception as e:
            raise SecurityError(f"Command execution failed: {e}")

    def _validate_command_security(self, cmd: List[str]) -> None:
        """Validate command security without executing it."""
        # Reject string commands - they must be lists
        if isinstance(cmd, str):
            raise SecurityError("String commands not allowed - use list format")

        if not isinstance(cmd, list):
            raise SecurityError("Command must be a list of strings")

        # Validate that all elements are strings
        if not all(isinstance(arg, str) for arg in cmd):
            raise SecurityError("All command arguments must be strings")

        # Check for dangerous shell operators in arguments
        dangerous_patterns = [";", "&&", "||", "`", "$(", "$()"]

        # Special handling for jq - allow pipe operators in jq filter expressions
        if len(cmd) > 0 and cmd[0].split("/")[-1] == "jq":
            # For jq commands, only check for the most dangerous patterns (no pipe restriction)
            jq_dangerous_patterns = [";", "&&", "||", "`", "$(", "$()"]
            for arg in cmd:
                for pattern in jq_dangerous_patterns:
                    if pattern in arg:
                        raise SecurityError(
                            f"Dangerous shell operator '{pattern}' detected in jq command: {arg}"
                        )
        else:
            # For other commands, check for all dangerous patterns including pipes
            dangerous_patterns.append("|")
            for arg in cmd:
                for pattern in dangerous_patterns:
                    if pattern in arg:
                        raise SecurityError(
                            f"Dangerous shell operator '{pattern}' detected in: {arg}"
                        )

        # Use allowlist approach - only permit required font generation commands
        if len(cmd) > 0:
            command_name = cmd[0].lower()
            # Extract command base name for otfcc tools (otfccbuild, otfccdump, etc.)
            command_base = command_name.split("/")[-1]  # Handle full paths

            # Allowlist of permitted commands for font generation
            allowed_commands = [
                "otfccbuild",
                "otfccdump",
                "otfcc-build",
                "otfcc-dump",  # Font tools
                "jq",  # JSON processing
                "echo",
                "true",
                "false",
                "cat",
                "ls",
                "pwd",
                "sleep",  # Minimal utilities for testing
                "python",
                "python3",  # Python execution (with restrictions)
            ]

            # Check if command is in allowlist
            if not any(
                command_base.startswith(allowed_cmd) for allowed_cmd in allowed_commands
            ):
                raise SecurityError(f"Command not in allowlist: {command_name}")

            # Additional validation for python commands to prevent arbitrary code execution
            if command_base in ["python", "python3"] and len(cmd) > 1:
                # Only allow specific safe python patterns
                if cmd[1] == "-c":
                    raise SecurityError(
                        "Python -c (arbitrary code execution) not allowed"
                    )
                elif cmd[1] == "-m" and len(cmd) > 2:
                    # Allow specific modules only (including test modules)
                    allowed_modules = [
                        "refactored.cli.main",
                        "refactored.scripts",
                        "module",
                        "pytest",
                    ]
                    module_name = cmd[2]
                    if not any(
                        module_name.startswith(allowed_mod)
                        for allowed_mod in allowed_modules
                    ):
                        raise SecurityError(
                            f"Python module not in allowlist: {module_name}"
                        )

            # Additional validation for cat command to prevent sensitive file access
            if command_base == "cat" and len(cmd) > 1:
                for arg in cmd[1:]:
                    # Block access to sensitive system files and path traversal
                    if any(
                        sensitive_path in arg.lower()
                        for sensitive_path in [
                            "/etc/passwd",
                            "/etc/shadow",
                            "/root/",
                            "config/sam",
                            "system32",
                            "../../../",
                            "../../..",
                            "../../../../",
                            "~/",
                            "file://",
                            "\\\\",
                        ]
                    ):
                        raise SecurityError(
                            f"Access to sensitive file not allowed: {arg}"
                        )

    def execute(
        self,
        command: Union[str, List[str]],
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
    ) -> subprocess.CompletedProcess:
        """Execute a command safely."""
        try:
            # Use provided timeout or default
            exec_timeout = timeout if timeout is not None else self.timeout

            # Validate working directory if provided
            if cwd is not None:
                # Check if accessing system directories is allowed
                sensitive_dirs = ["/etc", "/usr/bin", "/root", "/sys", "/proc"]
                if any(
                    cwd.startswith(sensitive_dir) for sensitive_dir in sensitive_dirs
                ):
                    raise SecurityError(
                        f"Access to system directory not allowed: {cwd}"
                    )

            # Handle both string and list commands
            if isinstance(command, list):
                # For list commands, use safe_command_execution with timeout
                return self._safe_execute_with_timeout(command, exec_timeout)

            # For string commands, reject them for security
            raise SecurityError("String commands not allowed - use list format")
        except subprocess.TimeoutExpired as e:
            # Re-raise timeout exceptions directly for test compatibility
            raise e
        except Exception as e:
            raise SecurityError(f"Command execution failed: {e}") from e
