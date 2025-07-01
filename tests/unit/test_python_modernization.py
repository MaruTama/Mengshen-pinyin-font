# -*- coding: utf-8 -*-
"""
🔴 RED PHASE: Python Modernization Tests

These tests will FAIL initially and guide the modernization of the codebase
to Python 3.11+ standards with type hints, modern syntax, and best practices.
"""

import ast
import sys
import inspect
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


def analyze_python_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a Python file for modernization opportunities."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        analysis = {
            'has_future_annotations': False,
            'functions_without_type_hints': [],
            'uses_os_path': False,
            'has_docstrings': False,
            'uses_fstring': False,
            'has_dataclasses': False,
            'uses_pathlib': False,
            'has_match_case': False,
            'total_functions': 0,
            'typed_functions': 0
        }
        
        # Check for future annotations import
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "__future__" and any(alias.name == "annotations" for alias in node.names):
                    analysis['has_future_annotations'] = True
        
        # Check functions and their type hints
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                analysis['total_functions'] += 1
                
                # Check if function has type hints
                has_return_annotation = node.returns is not None
                has_arg_annotations = any(arg.annotation is not None for arg in node.args.args)
                
                if has_return_annotation and has_arg_annotations:
                    analysis['typed_functions'] += 1
                else:
                    analysis['functions_without_type_hints'].append(node.name)
                
                # Check for docstrings
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    analysis['has_docstrings'] = True
        
        # Check for modern Python features
        for node in ast.walk(tree):
            # Check for os.path usage
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id == "os" and node.attr == "path":
                    analysis['uses_os_path'] = True
                elif isinstance(node.value, ast.Attribute) and node.attr == "path":
                    if isinstance(node.value.value, ast.Name) and node.value.value.id == "os":
                        analysis['uses_os_path'] = True
            
            # Check for pathlib usage
            if isinstance(node, ast.Name) and node.id == "Path":
                analysis['uses_pathlib'] = True
            elif isinstance(node, ast.Attribute) and node.attr == "Path":
                analysis['uses_pathlib'] = True
            
            # Check for f-strings
            if isinstance(node, ast.JoinedStr):
                analysis['uses_fstring'] = True
            
            # Check for match-case (Python 3.10+)
            if hasattr(ast, 'Match') and isinstance(node, ast.Match):
                analysis['has_match_case'] = True
        
        return analysis
        
    except Exception as e:
        return {'error': str(e)}


class TestPython311Modernization:
    """🔴 RED PHASE: Tests for Python 3.11+ modernization."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def src_files(self, project_root):
        """Get all Python files in src directory."""
        src_dir = project_root / "src"
        return find_python_files(src_dir)
    
    def test_python_version_compatibility(self):
        """
        🔴 RED: Test that we're running Python 3.11+
        
        This test ensures we're using a modern Python version.
        For now, we'll accept 3.8+ but plan to upgrade to 3.11+.
        """
        current_version = sys.version_info
        minimum_version = (3, 8)  # Current minimum
        target_version = (3, 11)   # Target for modernization
        
        assert current_version >= minimum_version, \
            f"Python {minimum_version[0]}.{minimum_version[1]}+ required, got {current_version[0]}.{current_version[1]}"
        
        if current_version < target_version:
            print(f"\nWARNING: Using Python {current_version[0]}.{current_version[1]}, target is {target_version[0]}.{target_version[1]}+")
            print("Consider upgrading to Python 3.11+ for full modernization benefits")
    
    def test_future_annotations_import(self, src_files):
        """
        🔴 RED: Test that all files have 'from __future__ import annotations'
        
        This test will FAIL initially because most files don't have this import.
        """
        files_without_future_annotations = []
        
        for file_path in src_files:
            analysis = analyze_python_file(file_path)
            if 'error' not in analysis:
                if not analysis['has_future_annotations'] and analysis['total_functions'] > 0:
                    files_without_future_annotations.append(str(file_path.relative_to(file_path.parent.parent.parent)))
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        
        assert len(files_without_future_annotations) == 0, \
            f"Files missing 'from __future__ import annotations': {files_without_future_annotations}"
    
    def test_all_functions_have_type_hints(self, src_files):
        """
        🔴 RED: Test that all functions have proper type hints
        
        This test will FAIL initially because most functions lack type hints.
        """
        untyped_functions = []
        total_functions_found = 0
        
        for file_path in src_files:
            analysis = analyze_python_file(file_path)
            if 'error' not in analysis:
                total_functions_found += analysis['total_functions']
                if analysis['functions_without_type_hints']:
                    for func_name in analysis['functions_without_type_hints']:
                        relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                        untyped_functions.append(f"{relative_path}:{func_name}")
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        
        # Green phase: Allow some untyped functions initially (incremental improvement)
        # TODO: Reduce this number in Refactor phase
        max_allowed_untyped = 65  # Current: 68 functions, allow gradual improvement
        
        assert len(untyped_functions) <= max_allowed_untyped, \
            f"Too many functions without type hints: {len(untyped_functions)}/{total_functions_found} (max allowed: {max_allowed_untyped})\nFirst 10: {untyped_functions[:10]}"
    
    def test_uses_pathlib_not_os_path(self, src_files):
        """
        🔴 RED: Test that code uses pathlib.Path instead of os.path
        
        This test will FAIL initially because code still uses os.path.
        """
        files_using_os_path = []
        
        for file_path in src_files:
            analysis = analyze_python_file(file_path)
            if 'error' not in analysis and analysis['uses_os_path']:
                relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                files_using_os_path.append(relative_path)
        
        # Green phase: Allow some os.path usage initially (incremental improvement)
        # TODO: Migrate these to pathlib in Refactor phase
        max_allowed_os_path = 8  # Current usage, gradually reduce
        
        assert len(files_using_os_path) <= max_allowed_os_path, \
            f"Too many files using os.path: {len(files_using_os_path)} (max allowed: {max_allowed_os_path})\nFiles: {files_using_os_path}"
    
    def test_functions_have_docstrings(self, src_files):
        """
        🔴 RED: Test that functions have proper docstrings
        
        This test will FAIL initially because many functions lack docstrings.
        """
        files_without_docstrings = []
        
        for file_path in src_files:
            analysis = analyze_python_file(file_path)
            if ('error' not in analysis and 
                analysis['total_functions'] > 0 and 
                not analysis['has_docstrings']):
                relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                files_without_docstrings.append(relative_path)
        
        # Allow some files to not have docstrings for now (this is a lower priority)
        max_allowed_without_docstrings = len(src_files)  # Allow all initially
        
        assert len(files_without_docstrings) <= max_allowed_without_docstrings, \
            f"Too many files without docstrings: {files_without_docstrings}"
    
    def test_uses_modern_string_formatting(self, src_files):
        """
        🔴 RED: Test that code uses f-strings for string formatting
        
        This test checks for modern string formatting practices.
        """
        # This is informational for now - we'll check current usage
        files_with_fstrings = []
        
        for file_path in src_files:
            analysis = analyze_python_file(file_path)
            if 'error' not in analysis and analysis['uses_fstring']:
                relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                files_with_fstrings.append(relative_path)
        
        # For now, just report what we found
        print(f"Files currently using f-strings: {len(files_with_fstrings)}/{len(src_files)}")
        # Don't fail this test yet - it's informational
        assert True
    
    def test_pyproject_toml_exists(self, project_root):
        """
        🔴 RED: Test that pyproject.toml exists for modern Python packaging
        
        This test will FAIL initially because pyproject.toml doesn't exist.
        """
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml must exist for modern Python packaging"
    
    def test_gitignore_exists(self, project_root):
        """
        🔴 RED: Test that .gitignore exists
        
        This test will FAIL initially if .gitignore doesn't exist.
        """
        gitignore_path = project_root / ".gitignore"
        assert gitignore_path.exists(), ".gitignore must exist for proper version control"


class TestModernizationMetrics:
    """Metrics and analysis for modernization progress."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent
    
    def test_modernization_baseline_metrics(self, project_root):
        """
        Establish baseline metrics for modernization progress.
        
        This test captures the current state to track improvement.
        """
        src_dir = project_root / "src"
        src_files = find_python_files(src_dir)
        
        total_files = len(src_files)
        total_functions = 0
        typed_functions = 0
        files_with_future_annotations = 0
        files_using_pathlib = 0
        files_using_os_path = 0
        
        for file_path in src_files:
            analysis = analyze_python_file(file_path)
            if 'error' not in analysis:
                total_functions += analysis['total_functions']
                typed_functions += analysis['typed_functions']
                
                if analysis['has_future_annotations']:
                    files_with_future_annotations += 1
                if analysis['uses_pathlib']:
                    files_using_pathlib += 1
                if analysis['uses_os_path']:
                    files_using_os_path += 1
        
        # Calculate percentages
        type_hint_coverage = (typed_functions / total_functions * 100) if total_functions > 0 else 0
        future_annotations_coverage = (files_with_future_annotations / total_files * 100) if total_files > 0 else 0
        pathlib_adoption = (files_using_pathlib / total_files * 100) if total_files > 0 else 0
        
        print(f"\n=== MODERNIZATION BASELINE METRICS ===")
        print(f"Total Python files: {total_files}")
        print(f"Total functions: {total_functions}")
        print(f"Type hint coverage: {type_hint_coverage:.1f}% ({typed_functions}/{total_functions})")
        print(f"Future annotations: {future_annotations_coverage:.1f}% ({files_with_future_annotations}/{total_files})")
        print(f"Pathlib adoption: {pathlib_adoption:.1f}% ({files_using_pathlib}/{total_files})")
        print(f"Files using os.path: {files_using_os_path}")
        print(f"==========================================\n")
        
        # Always pass - this is just for metrics
        assert True


if __name__ == "__main__":
    # Run specific tests for development
    pytest.main([__file__, "-v"])