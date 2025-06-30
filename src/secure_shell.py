# -*- coding: utf-8 -*-
"""
Secure shell command execution module.

This module provides safe alternatives to shell command execution,
preventing shell injection vulnerabilities.
"""

from __future__ import annotations

import subprocess
import shlex
from pathlib import Path
from typing import List, Union


class SecurityError(Exception):
    """Raised when a security violation is detected."""
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
    dangerous_patterns = [';', '&&', '||', '|', '`', '$()']
    for arg in cmd:
        for pattern in dangerous_patterns:
            if pattern in arg:
                raise SecurityError(f"Dangerous shell operator '{pattern}' detected in: {arg}")
    
    # Execute safely without shell=True
    try:
        return subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            shell=False,  # Explicitly disable shell
            timeout=60    # Increased timeout for font processing
        )
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
    
    # Check for path traversal patterns
    dangerous_patterns = ['../', '..\\', '/etc/', '/root/', '~/', 'C:\\']
    for pattern in dangerous_patterns:
        if pattern in file_path:
            raise SecurityError(f"Dangerous path pattern '{pattern}' detected in: {file_path}")
    
    # Convert to Path and resolve
    try:
        path = Path(file_path).resolve()
    except Exception as e:
        raise SecurityError(f"Invalid path: {e}")
    
    # Ensure path is within project directory
    project_root = Path(__file__).parent.parent.resolve()
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
    if ' | ' in cmd and ' > ' in cmd:
        # Find the redirection part (should be at the end)
        redirection_split = cmd.rsplit(' > ', 1)
        if len(redirection_split) == 2:
            pipeline_part = redirection_split[0].strip()
            output_file = redirection_split[1].strip()
            
            # Validate output file path
            output_path = validate_file_path(output_file)
            
            # Execute the pipeline part
            pipeline_result = safe_pipeline_execution(pipeline_part)
            
            # Write result to file
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(pipeline_result)
                return pipeline_result
            except Exception as e:
                raise SecurityError(f"Failed to write output file: {e}")
    
    # Handle pipeline without redirection
    elif ' | ' in cmd:
        # Split pipeline into individual commands
        commands = cmd.split(' | ')
        
        # Process each command in the pipeline
        input_data = None
        for i, single_cmd in enumerate(commands):
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
                    input_bytes = input_data.encode('utf-8') if isinstance(input_data, str) else input_data
                    result = subprocess.run(
                        cmd_list,
                        input=input_bytes,
                        capture_output=True,
                        shell=False,
                        timeout=60
                    )
                else:
                    # First command in pipeline
                    result = subprocess.run(
                        cmd_list,
                        capture_output=True,
                        shell=False,
                        timeout=60
                    )
                
                if result.returncode != 0:
                    error_msg = result.stderr.decode('utf-8', 'ignore') if result.stderr else f"Command failed with return code {result.returncode}"
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
                return input_data.decode('utf-8')
            except UnicodeDecodeError:
                # For binary data, return empty string to match original behavior
                return ""
        return input_data or ""
    
    # Handle redirection (>) 
    elif ' > ' in cmd:
        parts = cmd.split(' > ')
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
                cmd_list,
                capture_output=True,
                shell=False,
                timeout=60
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', 'ignore') if result.stderr else f"Command failed with return code {result.returncode}"
                raise Exception(error_msg)
            
            # Write output to file (handle binary data)
            if isinstance(result.stdout, bytes):
                try:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(result.stdout.decode('utf-8'))
                    return result.stdout.decode('utf-8')
                except UnicodeDecodeError:
                    # Write as binary file
                    with open(output_path, 'wb') as f:
                        f.write(result.stdout)
                    return ""
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
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
            error_msg = result.stderr or f"Command failed with return code {result.returncode}"
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