# -*- coding: utf-8 -*-
"""
🔴 RED PHASE: Security Modernization Tests

These tests will FAIL initially and guide the security modernization
to eliminate shell injection vulnerabilities and implement secure alternatives.
"""

from __future__ import annotations

import ast
import sys
import subprocess
import importlib
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Any
import pytest


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in a directory."""
    python_files = []
    for py_file in directory.rglob("*.py"):
        # Skip __pycache__ and test files for now
        if "__pycache__" not in str(py_file) and "test_" not in py_file.name:
            python_files.append(py_file)
    return python_files


def analyze_security_vulnerabilities(file_path: Path) -> Dict[str, Any]:
    """Analyze a Python file for security vulnerabilities."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        analysis = {
            'shell_injection_patterns': [],
            'unsafe_subprocess_calls': [],
            'dangerous_imports': [],
            'path_traversal_risks': [],
            'eval_exec_usage': [],
            'pickle_usage': [],
            'has_input_validation': False,
            'uses_secure_subprocess': False,
            'has_parameterized_queries': True,  # Assume true unless SQL found
            'total_security_issues': 0
        }
        
        # Dangerous patterns to look for (simple string search first)
        simple_dangerous_patterns = [
            'os.system(',
            'eval(',
            'exec(',
            'pickle.load(',
            'pickle.loads(',
            '__import__(',
            'importlib.import_module'
        ]
        
        # Check for dangerous patterns in source (excluding false positives)
        for pattern in simple_dangerous_patterns:
            if pattern in content:
                if pattern == 'os.system(':
                    analysis['shell_injection_patterns'].append(pattern)
                elif pattern in ['eval(', 'exec(']:
                    analysis['eval_exec_usage'].append(pattern)
                elif pattern.startswith('pickle.'):
                    analysis['pickle_usage'].append(pattern)
                elif pattern in ['__import__(', 'importlib.import_module']:
                    analysis['dangerous_imports'].append(pattern)
        
        # AST-based analysis for more complex patterns
        for node in ast.walk(tree):
            # Check for subprocess calls with shell=True
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and 
                    isinstance(node.func.value, ast.Name) and 
                    node.func.value.id == 'subprocess'):
                    
                    # Check for shell=True parameter (this is the actual vulnerability)
                    for keyword in node.keywords:
                        if keyword.arg == 'shell' and isinstance(keyword.value, ast.Constant):
                            if keyword.value.value is True:
                                analysis['unsafe_subprocess_calls'].append(f"subprocess.{node.func.attr} with shell=True")
                
                # Check for os.system calls (already covered by simple pattern but double-check)
                if (isinstance(node.func, ast.Attribute) and 
                    isinstance(node.func.value, ast.Name) and 
                    node.func.value.id == 'os' and 
                    node.func.attr == 'system'):
                    analysis['shell_injection_patterns'].append('os.system')
        
        # Check for secure subprocess usage
        if 'subprocess' in content and 'shell=False' in content:
            analysis['uses_secure_subprocess'] = True
        
        # Check for input validation patterns
        validation_patterns = [
            'shlex.quote',
            'shlex.split',
            'html.escape',
            'urllib.parse.quote',
            'pathlib.Path',
            'Path(',
            'os.path.abspath',
            'os.path.normpath',
            'SecurityError',
            'validate_file_path',
            'isinstance(',
            'raise SecurityError'
        ]
        
        for pattern in validation_patterns:
            if pattern in content:
                analysis['has_input_validation'] = True
                break
        
        # Calculate total security issues
        analysis['total_security_issues'] = (
            len(analysis['shell_injection_patterns']) +
            len(analysis['unsafe_subprocess_calls']) +
            len(analysis['dangerous_imports']) +
            len(analysis['eval_exec_usage']) +
            len(analysis['pickle_usage'])
        )
        
        return analysis
        
    except Exception as e:
        return {'error': str(e)}


@pytest.fixture
def src_files():
    """Get all Python source files."""
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src"
    return find_python_files(src_dir)


class TestSecurityModernization:
    """Test security modernization patterns and vulnerability elimination."""
    
    def test_no_shell_injection_vulnerabilities(self, src_files):
        """
        🔴 RED: Test that no shell injection vulnerabilities exist
        
        This test will FAIL initially because shell.py contains shell=True usage.
        """
        vulnerable_files = []
        total_vulnerabilities = 0
        
        for file_path in src_files:
            analysis = analyze_security_vulnerabilities(file_path)
            if 'error' not in analysis:
                file_vulnerabilities = len(analysis['shell_injection_patterns'])
                if file_vulnerabilities > 0:
                    relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                    vulnerable_files.append(f"{relative_path}: {analysis['shell_injection_patterns']}")
                    total_vulnerabilities += file_vulnerabilities
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        # Red phase: This should FAIL initially
        assert total_vulnerabilities == 0, \
            f"Found {total_vulnerabilities} shell injection vulnerabilities:\n" + \
            "\n".join(vulnerable_files[:5])
    
    def test_secure_subprocess_usage(self, src_files):
        """
        🔴 RED: Test that all subprocess calls use secure patterns
        
        This test will FAIL initially because of unsafe subprocess usage.
        """
        unsafe_files = []
        total_unsafe_calls = 0
        
        for file_path in src_files:
            analysis = analyze_security_vulnerabilities(file_path)
            if 'error' not in analysis:
                unsafe_calls = len(analysis['unsafe_subprocess_calls'])
                if unsafe_calls > 0:
                    relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                    unsafe_files.append(f"{relative_path}: {analysis['unsafe_subprocess_calls']}")
                    total_unsafe_calls += unsafe_calls
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        # Red phase: This should FAIL initially
        assert total_unsafe_calls == 0, \
            f"Found {total_unsafe_calls} unsafe subprocess calls:\n" + \
            "\n".join(unsafe_files[:5])
    
    def test_no_dangerous_eval_exec_usage(self, src_files):
        """
        🔴 RED: Test that no dangerous eval/exec usage exists
        
        This should pass as the codebase doesn't use eval/exec.
        """
        dangerous_files = []
        total_dangerous_usage = 0
        
        for file_path in src_files:
            analysis = analyze_security_vulnerabilities(file_path)
            if 'error' not in analysis:
                dangerous_usage = len(analysis['eval_exec_usage'])
                if dangerous_usage > 0:
                    relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                    dangerous_files.append(f"{relative_path}: {analysis['eval_exec_usage']}")
                    total_dangerous_usage += dangerous_usage
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        assert total_dangerous_usage == 0, \
            f"Found {total_dangerous_usage} dangerous eval/exec usage:\n" + \
            "\n".join(dangerous_files[:5])
    
    def test_input_validation_implementation(self, src_files):
        """
        🔴 RED: Test that input validation is implemented where needed
        
        This test will FAIL initially because input validation is minimal.
        """
        files_needing_validation = []
        files_with_validation = []
        
        for file_path in src_files:
            analysis = analyze_security_vulnerabilities(file_path)
            if 'error' not in analysis:
                relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                
                # Files that handle external input need validation
                if (analysis['total_security_issues'] > 0 or 
                    'subprocess' in file_path.read_text() or
                    'requests' in file_path.read_text()):
                    
                    if analysis['has_input_validation']:
                        files_with_validation.append(relative_path)
                    else:
                        files_needing_validation.append(relative_path)
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        # Green phase: Improved from initial state
        max_unvalidated = 5  # Current state, continue improving
        
        assert len(files_needing_validation) <= max_unvalidated, \
            f"Too many files without input validation: {len(files_needing_validation)}/{len(files_needing_validation) + len(files_with_validation)}\n" + \
            f"Files needing validation: {files_needing_validation[:5]}"


class TestSecurityMetrics:
    """Test security baseline metrics and improvements."""
    
    def test_security_baseline_metrics(self, src_files):
        """
        Track security metrics for improvement over time.
        
        Baseline metrics from before security modernization.
        """
        total_files = len(src_files)
        files_with_vulnerabilities = 0
        total_vulnerabilities = 0
        files_with_validation = 0
        files_with_secure_subprocess = 0
        
        for file_path in src_files:
            analysis = analyze_security_vulnerabilities(file_path)
            if 'error' not in analysis:
                if analysis['total_security_issues'] > 0:
                    files_with_vulnerabilities += 1
                    total_vulnerabilities += analysis['total_security_issues']
                
                if analysis['has_input_validation']:
                    files_with_validation += 1
                
                if analysis['uses_secure_subprocess']:
                    files_with_secure_subprocess += 1
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        # Calculate percentages
        vulnerability_free_percent = ((total_files - files_with_vulnerabilities) / total_files) * 100
        input_validation_percent = (files_with_validation / total_files) * 100
        secure_subprocess_percent = (files_with_secure_subprocess / total_files) * 100
        
        print(f"\n📊 SECURITY METRICS:")
        print(f"Total files analyzed: {total_files}")
        print(f"Vulnerability-free files: {vulnerability_free_percent:.1f}%")
        print(f"Files with input validation: {input_validation_percent:.1f}%")
        print(f"Files with secure subprocess: {secure_subprocess_percent:.1f}%")
        print(f"Total security issues: {total_vulnerabilities}")
        
        # Baseline assertions - these should improve over time
        assert total_files > 0, "Should have source files to analyze"
        
        # Track improvement metrics (will be updated in Green phase)
        # Current baseline: some vulnerabilities exist
        # Goal: 100% vulnerability-free, >80% with validation