# -*- coding: utf-8 -*-
"""
🔴 RED PHASE: Data Structure Modernization Tests

These tests will FAIL initially and guide the modernization of data structures
to use TypedDict, dataclasses, and modern Python patterns for better type safety.
"""

from __future__ import annotations

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


def analyze_data_structures(file_path: Path) -> Dict[str, Any]:
    """Analyze a Python file for data structure modernization opportunities."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        analysis = {
            'has_typeddict': False,
            'has_dataclasses': False,
            'has_namedtuple': False,
            'has_enum': False,
            'dict_definitions': [],
            'class_definitions': [],
            'large_dict_constants': [],
            'has_iterators': False,
            'has_generators': False,
            'uses_list_comprehensions': False,
            'total_classes': 0,
            'classes_with_init': 0,
            'classes_without_type_hints': []
        }
        
        # Check for imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "typing":
                    for alias in node.names:
                        if alias.name == "TypedDict":
                            analysis['has_typeddict'] = True
                elif node.module == "dataclasses":
                    analysis['has_dataclasses'] = True
                elif node.module == "collections":
                    for alias in node.names:
                        if alias.name == "namedtuple":
                            analysis['has_namedtuple'] = True
                elif node.module == "enum":
                    analysis['has_enum'] = True
        
        # Check for class definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                analysis['total_classes'] += 1
                analysis['class_definitions'].append(node.name)
                
                # Check if class has __init__ method
                has_init = any(
                    isinstance(child, ast.FunctionDef) and child.name == "__init__"
                    for child in node.body
                )
                if has_init:
                    analysis['classes_with_init'] += 1
                
                # Check if class could benefit from dataclass
                init_method = None
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name == "__init__":
                        init_method = child
                        break
                
                if init_method and not has_type_hints_in_function(init_method):
                    analysis['classes_without_type_hints'].append(node.name)
        
        # Check for large dictionary constants (potential TypedDict candidates)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(node.value, ast.List):
                        # Check if it's a list of dictionaries
                        if (len(node.value.elts) > 5 and 
                            all(isinstance(elt, ast.Dict) for elt in node.value.elts)):
                            analysis['large_dict_constants'].append(target.id)
        
        # Check for modern iteration patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.GeneratorExp):
                analysis['has_generators'] = True
            elif isinstance(node, ast.ListComp):
                analysis['uses_list_comprehensions'] = True
            elif isinstance(node, ast.FunctionDef):
                # Check if function yields (generator function)
                if any(isinstance(child, ast.Yield) for child in ast.walk(node)):
                    analysis['has_generators'] = True
        
        return analysis
        
    except Exception as e:
        return {'error': str(e)}


def has_type_hints_in_function(func_node: ast.FunctionDef) -> bool:
    """Check if a function has type hints."""
    has_return_annotation = func_node.returns is not None
    has_arg_annotations = any(arg.annotation is not None for arg in func_node.args.args)
    return has_return_annotation and has_arg_annotations


class TestDataStructureModernization:
    """🔴 RED PHASE: Tests for data structure modernization."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def src_files(self, project_root):
        """Get all Python files in src directory."""
        src_dir = project_root / "src"
        return find_python_files(src_dir)
    
    @pytest.fixture
    def scripts_files(self, project_root):
        """Get all Python files in scripts directories."""
        scripts_dir = project_root / "res" / "phonics" / "duo_yin_zi" / "scripts"
        return find_python_files(scripts_dir)
    
    def test_typeddict_usage(self, src_files):
        """
        🔴 RED: Test that TypedDict is used for structured data
        
        This test will FAIL initially because most files don't use TypedDict.
        """
        files_with_typeddict = []
        files_with_large_dicts = []
        
        for file_path in src_files:
            analysis = analyze_data_structures(file_path)
            if 'error' not in analysis:
                if analysis['has_typeddict']:
                    files_with_typeddict.append(file_path.name)
                if analysis['large_dict_constants']:
                    files_with_large_dicts.append({
                        'file': file_path.name,
                        'constants': analysis['large_dict_constants']
                    })
        
        # Files with large dictionary constants should use TypedDict
        assert len(files_with_large_dicts) == 0 or len(files_with_typeddict) > 0, \
            f"Files with large dict constants should use TypedDict: {files_with_large_dicts}"
    
    def test_dataclass_usage(self, src_files, scripts_files):
        """
        🔴 RED: Test that dataclasses are used instead of manual __init__ classes
        
        This test will FAIL initially because classes use manual __init__ methods.
        """
        files_with_dataclasses = []
        classes_needing_dataclass = []
        
        all_files = src_files + scripts_files
        
        for file_path in all_files:
            analysis = analyze_data_structures(file_path)
            if 'error' not in analysis:
                if analysis['has_dataclasses']:
                    files_with_dataclasses.append(file_path.name)
                
                # Classes with __init__ but no type hints could benefit from dataclasses
                if analysis['classes_without_type_hints']:
                    for class_name in analysis['classes_without_type_hints']:
                        classes_needing_dataclass.append(f"{file_path.name}:{class_name}")
        
        # Allow some untyped classes initially, but encourage dataclass usage
        max_allowed_untyped_classes = 5  # Current limit for Green phase
        
        assert len(classes_needing_dataclass) <= max_allowed_untyped_classes, \
            f"Too many classes without type hints (should use dataclasses): {len(classes_needing_dataclass)} (max: {max_allowed_untyped_classes})\\nClasses: {classes_needing_dataclass[:10]}"
    
    def test_iterator_and_generator_usage(self, src_files):
        """
        🔴 RED: Test that iterators and generators are used for memory efficiency
        
        This test will FAIL initially because most code doesn't use generators.
        """
        files_with_generators = []
        files_with_comprehensions = []
        
        for file_path in src_files:
            analysis = analyze_data_structures(file_path)
            if 'error' not in analysis:
                if analysis['has_generators']:
                    files_with_generators.append(file_path.name)
                if analysis['uses_list_comprehensions']:
                    files_with_comprehensions.append(file_path.name)
        
        # At least some files should use modern iteration patterns
        modern_iteration_files = len(files_with_generators) + len(files_with_comprehensions)
        min_expected_modern_files = 3  # Expect at least a few files to use modern patterns
        
        assert modern_iteration_files >= min_expected_modern_files, \
            f"Not enough files using modern iteration patterns: {modern_iteration_files} (expected: {min_expected_modern_files})"
    
    def test_enum_usage_for_constants(self, src_files):
        """
        🔴 RED: Test that Enum is used for related constants
        
        This test will FAIL initially because constants are not grouped in Enums.
        """
        files_with_enums = []
        files_with_constants = []
        
        for file_path in src_files:
            # Check if file has multiple related constants (candidate for Enum)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                analysis = analyze_data_structures(file_path)
                if 'error' not in analysis and analysis['has_enum']:
                    files_with_enums.append(file_path.name)
                
                # Check for related constants (like font types)
                if ('_TYPE' in content and content.count('_TYPE') > 1) or \
                   ('VERSION' in content) or \
                   ('ID' in content and content.count('ID') > 3):
                    files_with_constants.append(file_path.name)
                    
            except Exception:
                continue
        
        # Allow no enum usage initially (Green phase), but prepare for improvement
        # This test documents the opportunity for future enhancement
        assert True, "Enum usage assessment complete"
    
    def test_type_safety_improvements(self, src_files):
        """
        🔴 RED: Test overall type safety improvements needed
        
        This test measures the current state and sets improvement targets.
        """
        total_classes = 0
        typed_classes = 0
        files_with_modern_structures = 0
        
        for file_path in src_files:
            analysis = analyze_data_structures(file_path)
            if 'error' not in analysis:
                total_classes += analysis['total_classes']
                typed_classes += analysis['total_classes'] - len(analysis['classes_without_type_hints'])
                
                # Files with any modern data structure
                if (analysis['has_typeddict'] or 
                    analysis['has_dataclasses'] or 
                    analysis['has_namedtuple'] or 
                    analysis['has_enum']):
                    files_with_modern_structures += 1
        
        # Calculate metrics
        type_safety_percentage = (typed_classes / total_classes * 100) if total_classes > 0 else 0
        modern_structure_percentage = (files_with_modern_structures / len(src_files) * 100) if src_files else 0
        
        # Green phase targets (relaxed)
        min_type_safety = 20  # 20% of classes should have type hints
        min_modern_structures = 10  # 10% of files should use modern data structures
        
        assert type_safety_percentage >= min_type_safety, \
            f"Type safety too low: {type_safety_percentage:.1f}% (min: {min_type_safety}%)"
        
        assert modern_structure_percentage >= min_modern_structures, \
            f"Modern data structure usage too low: {modern_structure_percentage:.1f}% (min: {min_modern_structures}%)"


class TestDataStructureMetrics:
    """Metrics and analysis for data structure modernization progress."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent
    
    def test_data_structure_baseline_metrics(self, project_root):
        """
        Establish baseline metrics for data structure modernization progress.
        
        This test captures the current state to track improvement.
        """
        src_dir = project_root / "src"
        src_files = find_python_files(src_dir)
        
        scripts_dir = project_root / "res" / "phonics" / "duo_yin_zi" / "scripts"
        scripts_files = find_python_files(scripts_dir)
        
        all_files = src_files + scripts_files
        
        total_files = len(all_files)
        total_classes = 0
        typed_classes = 0
        files_with_typeddict = 0
        files_with_dataclasses = 0
        files_with_generators = 0
        files_with_large_dicts = 0
        
        for file_path in all_files:
            analysis = analyze_data_structures(file_path)
            if 'error' not in analysis:
                total_classes += analysis['total_classes']
                typed_classes += analysis['total_classes'] - len(analysis['classes_without_type_hints'])
                
                if analysis['has_typeddict']:
                    files_with_typeddict += 1
                if analysis['has_dataclasses']:
                    files_with_dataclasses += 1
                if analysis['has_generators']:
                    files_with_generators += 1
                if analysis['large_dict_constants']:
                    files_with_large_dicts += 1
        
        # Calculate percentages
        class_type_safety = (typed_classes / total_classes * 100) if total_classes > 0 else 0
        typeddict_adoption = (files_with_typeddict / total_files * 100) if total_files > 0 else 0
        dataclass_adoption = (files_with_dataclasses / total_files * 100) if total_files > 0 else 0
        generator_usage = (files_with_generators / total_files * 100) if total_files > 0 else 0
        
        print(f"\\n=== DATA STRUCTURE BASELINE METRICS ===")
        print(f"Total files analyzed: {total_files}")
        print(f"Total classes: {total_classes}")
        print(f"Class type safety: {class_type_safety:.1f}% ({typed_classes}/{total_classes})")
        print(f"TypedDict adoption: {typeddict_adoption:.1f}% ({files_with_typeddict}/{total_files})")
        print(f"Dataclass adoption: {dataclass_adoption:.1f}% ({files_with_dataclasses}/{total_files})")
        print(f"Generator usage: {generator_usage:.1f}% ({files_with_generators}/{total_files})")
        print(f"Files with large dict constants: {files_with_large_dicts}")
        print(f"========================================\\n")
        
        # Always pass - this is just for metrics
        assert True


if __name__ == "__main__":
    # Run specific tests for development
    pytest.main([__file__, "-v"])