# -*- coding: utf-8 -*-
"""
Secure shell command execution module.

This module provides safe alternatives to shell command execution,
preventing shell injection vulnerabilities.
"""

from __future__ import annotations

import shlex
import subprocess
import urllib.parse
from pathlib import Path
from typing import List, Union


class SecurityError(Exception):
    """Raised when a security violation is detected.

    This exception is thrown when potentially dangerous shell commands are detected,
    such as those that could lead to command injection or path traversal attacks.
    Legacy shell.py used shell=True which was vulnerable to command injection.
    """

    pass


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
    dangerous_patterns = [";", "&&", "||", "|", "`", "$(", "$()"]
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
            timeout=60,  # Increased timeout for font processing
        )
        # Convert stderr to text for error handling while keeping stdout as bytes
        if result.stderr and isinstance(result.stderr, bytes):
            result.stderr = result.stderr.decode("utf-8", "ignore")
        return result
    except subprocess.TimeoutExpired as e:
        raise SecurityError(f"Command timed out: {e}")
    except Exception as e:
        raise SecurityError(f"Command execution failed: {e}")


def validate_file_path(file_path: str) -> Path:
    """
    Validate a file path to prevent path traversal attacks.

    Args:
        file_path: Path to validate

    Returns:
        Validated Path object

    Raises:
        SecurityError: If path contains dangerous patterns
    """
    if not isinstance(file_path, str):
        raise SecurityError("File path must be a string")

    # Check path length limits (most filesystems have limits around 255-4096)
    if len(file_path) > 512:  # Conservative limit for security
        raise SecurityError(f"Path too long: {len(file_path)} characters (max 512)")

    # Normalize Unicode and decode URL encoding to detect obfuscated patterns
    normalized_path = file_path
    try:
        # URL decode the path to detect encoded dangerous patterns
        normalized_path = urllib.parse.unquote(normalized_path)
        # Normalize Unicode to detect Unicode escapes
        normalized_path = normalized_path.encode("utf-8").decode("unicode_escape")
    except (UnicodeDecodeError, UnicodeEncodeError):
        # If normalization fails, continue with original - better safe than sorry
        pass

    # Check for URL schemes (file://, http://, ftp://, etc.)
    if "://" in file_path or "://" in normalized_path:
        raise SecurityError(f"URL schemes not allowed in file paths: {file_path}")

    # Check for UNC paths (network shares)
    if file_path.startswith("\\\\") or normalized_path.startswith("\\\\"):
        raise SecurityError(f"UNC network paths not allowed: {file_path}")

    # Check for path traversal patterns in both original and normalized
    dangerous_patterns = ["../", "..\\", "/etc/", "/root/", "~/", "C:\\"]
    for pattern in dangerous_patterns:
        if pattern in file_path or pattern in normalized_path:
            raise SecurityError(
                f"Dangerous path pattern '{pattern}' detected in: {file_path}"
            )

    # Convert to Path and resolve
    try:
        path = Path(file_path).resolve()
    except Exception as e:
        raise SecurityError(f"Invalid path: {e}")

    # Ensure path is within project directory (go up to workspace root)
    project_root = Path(__file__).parent.parent.parent.parent.resolve()
    try:
        path.relative_to(project_root)
    except ValueError:
        raise SecurityError(f"Path outside project directory: {path}")

    return path


def safe_pipeline_execution(cmd: str) -> str:
    """
    Execute shell pipelines safely by breaking them into individual commands.

    Args:
        cmd: Command string containing pipes and/or redirections

    Returns:
        Final command output as string
    """
    # Handle complex pipeline + redirection patterns like "cat file | jq '.glyf' > output"
    if " | " in cmd and " > " in cmd:
        # Find the redirection part (should be at the end)
        redirection_split = cmd.rsplit(" > ", 1)
        if len(redirection_split) == 2:
            pipeline_part = redirection_split[0].strip()
            output_file = redirection_split[1].strip()

            # Validate output file path
            output_path = validate_file_path(output_file)

            # Execute the pipeline part
            pipeline_result = safe_pipeline_execution(pipeline_part)

            # Write result to file
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(pipeline_result)
                return pipeline_result
            except Exception as e:
                raise SecurityError(f"Failed to write output file: {e}")

    # Handle pipeline without redirection
    elif " | " in cmd:
        # Split pipeline into individual commands
        commands = cmd.split(" | ")

        # Process each command in the pipeline
        input_data = None
        for single_cmd in commands:
            single_cmd = single_cmd.strip()

            # Parse the individual command
            try:
                cmd_list = shlex.split(single_cmd)
            except ValueError as e:
                raise SecurityError(f"Invalid command syntax in pipeline: {e}")

            # Execute the command
            try:
                if input_data is not None:
                    # Pass output from previous command as input
                    # Handle binary data properly
                    input_bytes = (
                        input_data.encode("utf-8")
                        if isinstance(input_data, str)
                        else input_data
                    )
                    result = subprocess.run(
                        cmd_list,
                        input=input_bytes,
                        capture_output=True,
                        shell=False,
                        timeout=60,
                    )
                else:
                    # First command in pipeline
                    result = subprocess.run(
                        cmd_list, capture_output=True, shell=False, timeout=60
                    )

                if result.returncode != 0:
                    error_msg = (
                        result.stderr.decode("utf-8", "ignore")
                        if result.stderr
                        else f"Command failed with return code {result.returncode}"
                    )
                    raise Exception(error_msg)

                # Output becomes input for next command (keep as bytes)
                input_data = result.stdout

            except subprocess.TimeoutExpired as e:
                raise SecurityError(f"Command timed out: {e}")
            except Exception as e:
                if "Command failed with return code" in str(e):
                    raise e  # Re-raise the original error
                raise SecurityError(f"Command execution failed: {e}")

        # Convert final result to string for backward compatibility
        if isinstance(input_data, bytes):
            try:
                return input_data.decode("utf-8")
            except UnicodeDecodeError:
                # For binary data, return empty string to match original behavior
                return ""
        return input_data or ""

    # Handle redirection (>)
    elif " > " in cmd:
        parts = cmd.split(" > ")
        if len(parts) != 2:
            raise SecurityError("Invalid redirection syntax")

        command_part = parts[0].strip()
        output_file = parts[1].strip()

        # Validate output file path
        output_path = validate_file_path(output_file)

        # Execute command and write to file
        try:
            cmd_list = shlex.split(command_part)
            result = subprocess.run(
                cmd_list, capture_output=True, shell=False, timeout=60
            )

            if result.returncode != 0:
                error_msg = (
                    result.stderr.decode("utf-8", "ignore")
                    if result.stderr
                    else f"Command failed with return code {result.returncode}"
                )
                raise Exception(error_msg)

            # Write output to file (handle binary data)
            if isinstance(result.stdout, bytes):
                try:
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(result.stdout.decode("utf-8"))
                    return result.stdout.decode("utf-8")
                except UnicodeDecodeError:
                    # Write as binary file
                    with open(output_path, "wb") as f:
                        f.write(result.stdout)
                    return ""
            else:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result.stdout)
                return result.stdout

        except subprocess.TimeoutExpired as e:
            raise SecurityError(f"Command timed out: {e}")
        except Exception as e:
            if "Command failed with return code" in str(e):
                raise e
            raise SecurityError(f"Command execution failed: {e}")

    else:
        # Simple command without pipes or redirection
        try:
            cmd_list = shlex.split(cmd)
        except ValueError as e:
            raise SecurityError(f"Invalid command syntax: {e}")

        result = safe_command_execution(cmd_list)

        if result.returncode != 0:
            error_msg = (
                result.stderr or f"Command failed with return code {result.returncode}"
            )
            raise Exception(error_msg)

        return result.stdout


def legacy_shell_process_replacement(cmd: str) -> str:
    """
    Safe replacement for the legacy shell.process() function.

    This function provides backward compatibility while ensuring security.
    Handles pipelines and redirections safely.

    Args:
        cmd: Command string (will be safely parsed)

    Returns:
        Command output as string

    Raises:
        SecurityError: If command is deemed unsafe
    """
    return safe_pipeline_execution(cmd)


def secure_shell_process(cmd: List[str]) -> None:
    """
    Secure shell process execution for font generation.

    Args:
        cmd: Command as list of strings for safe execution

    Raises:
        SecurityError: If command execution fails
    """
    result = safe_command_execution(cmd)

    if result.returncode != 0:
        error_msg = (
            result.stderr or f"Command failed with return code {result.returncode}"
        )
        raise SecurityError(f"Font conversion failed: {error_msg}")


class ShellExecutor:
    """Shell command executor for backward compatibility."""

    def __init__(self, working_directory: str = None):
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
                result.stderr = result.stderr.decode("utf-8", "ignore")
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
        dangerous_patterns = [";", "&&", "||", "|", "`", "$(", "$()"]
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
        capture_output: bool = False,
        timeout: int = None,
        cwd: str = None,
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
                result = self._safe_execute_with_timeout(command, exec_timeout)
                return result
            else:
                # For string commands, use pipeline execution
                if capture_output:
                    output = legacy_shell_process_replacement(command)
                    # Return a mock result for compatibility
                    stdout_bytes = (
                        output.encode("utf-8")
                        if isinstance(output, str)
                        else (output if isinstance(output, bytes) else b"")
                    )
                    return type(
                        "MockResult",
                        (),
                        {"returncode": 0, "stdout": stdout_bytes, "stderr": b""},
                    )()
                else:
                    legacy_shell_process_replacement(command)
                    return type(
                        "MockResult",
                        (),
                        {"returncode": 0, "stdout": b"", "stderr": b""},
                    )()
        except subprocess.TimeoutExpired as e:
            # Re-raise timeout exceptions directly for test compatibility
            raise e
        except Exception as e:
            raise SecurityError(f"Command execution failed: {e}")
