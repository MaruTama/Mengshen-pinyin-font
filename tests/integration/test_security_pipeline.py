# -*- coding: utf-8 -*-
"""
Security Pipeline Integration Tests.
"""

import subprocess
import pytest
from pathlib import Path


class TestSecurityPipeline:
    """Security pipeline validation tests."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_red_phase_security_tests_exist(self, project_root):
        """
        
 RED PHASE: Verify that security tests exist and would catch issues.
        """
        security_tests = project_root / "tests" / "security" / "test_shell_injection.py"
        assert security_tests.exists(), "Security tests must exist for Red phase"

        with open(security_tests, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'shell=True' in content, "Security tests must check for shell=True"
            assert 'find_shell_true_usage' in content, "Must have function to find shell=True usage"
            assert 'command_injection' in content, "Must test command injection prevention"
            assert 'path_traversal' in content, "Must test path traversal prevention"

    def test_green_phase_secure_implementation(self, project_root):
        """
        
 GREEN PHASE: Verify that secure implementation exists and works.
        """
        secure_shell = project_root / "src" / "secure_shell.py"
        assert secure_shell.exists(), "Secure implementation must exist for Green phase"

        with open(secure_shell, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'safe_command_execution' in content, "Must have safe command execution"
            assert 'validate_file_path' in content, "Must have file path validation"
            assert 'legacy_shell_process_replacement' in content, "Must have legacy replacement"
            assert 'shell=False' in content, "Must explicitly disable shell"

    def test_refactor_phase_vulnerability_elimination(self, project_root):
        """
        
 REFACTOR PHASE: Verify that vulnerabilities have been eliminated.
        """
        result = subprocess.run(
            ["python", "-", "pytest", "tests/security/", "-v"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        assert result.returncode == 0, f"Security tests must pass in Refactor phase: {result.stderr}"

        vulnerable_files = [
            "src/shell.py",
            "tools/shell.py",
            "src/retrieve_latin_alphabet.py"
        ]

        for file_path in vulnerable_files:
            full_path = project_root / file_path
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for line_num, line in enumerate(lines, 1):
                        if line.strip().startswith('#'):
                            continue
                        if 'shell=True' in line and 'shell=False' not in line:
                            pytest.fail(f"Found shell=True in {file_path}:{line_num}: {line}")
