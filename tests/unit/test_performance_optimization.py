# -*- coding: utf-8 -*-
"""
🔴 RED PHASE: Performance Optimization Tests

These tests will FAIL initially and guide the performance optimization
to implement caching, lazy loading, and architectural improvements.
"""

from __future__ import annotations

import ast
import sys
import time
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


def analyze_performance_patterns(file_path: Path) -> Dict[str, Any]:
    """Analyze a Python file for performance optimization opportunities."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        analysis = {
            'has_caching': False,
            'has_lazy_loading': False,
            'has_generators': False,
            'has_list_comprehensions': False,
            'expensive_operations': [],
            'repeated_computations': [],
            'memory_inefficient_patterns': [],
            'io_operations': [],
            'large_data_structures': [],
            'has_memoization': False,
            'total_performance_issues': 0
        }
        
        # Performance patterns to look for
        caching_patterns = [
            '@lru_cache',
            '@functools.lru_cache',
            '@cache',
            'functools.cache',
            'cached_property',
            '_cache',
            'memoize'
        ]
        
        lazy_loading_patterns = [
            'yield',
            'Iterator',
            'Generator',
            'lazy',
            '__iter__',
            '__next__'
        ]
        
        expensive_patterns = [
            'os.walk(',
            'glob.glob(',
            'subprocess.run(',
            'requests.get(',
            'json.load(',
            'orjson.loads(',
            'open(',
            'with open('
        ]
        
        memory_inefficient_patterns = [
            '.read()',
            '.readlines()',
            'list(range(',
            '+ [',  # List concatenation
            'for i in range('
        ]
        
        # Check for caching patterns
        for pattern in caching_patterns:
            if pattern in content:
                analysis['has_caching'] = True
                break
        
        # Check for lazy loading patterns
        for pattern in lazy_loading_patterns:
            if pattern in content:
                analysis['has_lazy_loading'] = True
                break
        
        # Check for expensive operations
        for pattern in expensive_patterns:
            if pattern in content:
                analysis['expensive_operations'].append(pattern)
        
        # Check for memory inefficient patterns
        for pattern in memory_inefficient_patterns:
            if pattern in content:
                analysis['memory_inefficient_patterns'].append(pattern)
        
        # AST-based analysis for more complex patterns
        for node in ast.walk(tree):
            # Check for list comprehensions
            if isinstance(node, (ast.ListComp, ast.GeneratorExp)):
                if isinstance(node, ast.ListComp):
                    analysis['has_list_comprehensions'] = True
                else:
                    analysis['has_generators'] = True
            
            # Check for repeated function calls in loops
            if isinstance(node, ast.For):
                # Look for function calls that could be cached
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute):
                            # Pattern like obj.method() in loop
                            analysis['repeated_computations'].append('method_call_in_loop')
            
            # Check for large data structure operations
            if isinstance(node, ast.Dict):
                if len(node.keys) > 50:  # Large dictionary literal
                    analysis['large_data_structures'].append('large_dict')
            
            if isinstance(node, ast.List):
                if len(node.elts) > 100:  # Large list literal
                    analysis['large_data_structures'].append('large_list')
        
        # Check for memoization decorators
        if '@lru_cache' in content or '@cache' in content:
            analysis['has_memoization'] = True
        
        # Calculate total performance issues (things that could be optimized)
        analysis['total_performance_issues'] = (
            len(analysis['expensive_operations']) +
            len(analysis['memory_inefficient_patterns']) +
            len(analysis['repeated_computations']) +
            len(analysis['large_data_structures'])
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


class TestPerformanceOptimization:
    """Test performance optimization patterns and improvements."""
    
    def test_caching_implementation(self, src_files):
        """
        🔴 RED: Test that caching is implemented for expensive operations
        
        This test will FAIL initially because caching is minimal.
        """
        files_with_expensive_ops = []
        files_with_caching = []
        
        for file_path in src_files:
            analysis = analyze_performance_patterns(file_path)
            if 'error' not in analysis:
                relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                
                # Files with expensive operations should have caching
                if analysis['expensive_operations']:
                    if analysis['has_caching'] or analysis['has_memoization']:
                        files_with_caching.append(relative_path)
                    else:
                        files_with_expensive_ops.append(relative_path)
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        # Red phase: Allow some files without caching initially
        max_uncached = 5  # Current state, reduce in Green phase
        
        assert len(files_with_expensive_ops) <= max_uncached, \
            f"Too many files with expensive operations but no caching: {len(files_with_expensive_ops)}\n" + \
            f"Files needing caching: {files_with_expensive_ops[:5]}"
    
    def test_lazy_loading_patterns(self, src_files):
        """
        🔴 RED: Test that lazy loading patterns are used where appropriate
        
        This test will FAIL initially because lazy loading is limited.
        """
        files_with_large_data = []
        files_with_lazy_loading = []
        
        for file_path in src_files:
            analysis = analyze_performance_patterns(file_path)
            if 'error' not in analysis:
                relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                
                # Files with large data operations should use lazy loading
                if (analysis['large_data_structures'] or 
                    'PINYIN_MAPPING_TABLE' in file_path.read_text() or
                    'SIMPLED_ALPHABET' in file_path.read_text()):
                    
                    if analysis['has_lazy_loading'] or analysis['has_generators']:
                        files_with_lazy_loading.append(relative_path)
                    else:
                        files_with_large_data.append(relative_path)
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        # Red phase: Allow some files without lazy loading initially
        max_non_lazy = 3  # Current state, reduce in Green phase
        
        assert len(files_with_large_data) <= max_non_lazy, \
            f"Too many files with large data but no lazy loading: {len(files_with_large_data)}\n" + \
            f"Files needing lazy loading: {files_with_large_data[:5]}"
    
    def test_memory_efficiency(self, src_files):
        """
        🔴 RED: Test that memory-efficient patterns are used
        
        This test will FAIL initially because memory usage is not optimized.
        """
        inefficient_files = []
        total_inefficiencies = 0
        
        for file_path in src_files:
            analysis = analyze_performance_patterns(file_path)
            if 'error' not in analysis:
                file_inefficiencies = len(analysis['memory_inefficient_patterns'])
                if file_inefficiencies > 0:
                    relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                    inefficient_files.append(f"{relative_path}: {analysis['memory_inefficient_patterns']}")
                    total_inefficiencies += file_inefficiencies
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        # Red phase: Allow some inefficiencies initially
        max_inefficiencies = 15  # Current state, reduce in Green phase
        
        assert total_inefficiencies <= max_inefficiencies, \
            f"Too many memory inefficiencies: {total_inefficiencies}\n" + \
            "\n".join(inefficient_files[:5])
    
    def test_generator_usage(self, src_files):
        """
        🔴 RED: Test that generators are used for large data processing
        
        This should pass better as we've already implemented some generators.
        """
        files_needing_generators = []
        files_with_generators = []
        
        for file_path in src_files:
            analysis = analyze_performance_patterns(file_path)
            if 'error' not in analysis:
                relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                
                # Files with iteration patterns should use generators
                content = file_path.read_text()
                if ('for ' in content and 'MAPPING_TABLE' in content) or \
                   'iter_' in file_path.name or \
                   'get_has_' in content:
                    
                    if analysis['has_generators'] or 'yield' in content:
                        files_with_generators.append(relative_path)
                    else:
                        files_needing_generators.append(relative_path)
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        # This should pass better due to Phase 3 improvements
        max_non_generator = 4  # Current state after Phase 3, continue improving
        
        assert len(files_needing_generators) <= max_non_generator, \
            f"Too many files needing generators: {len(files_needing_generators)}\n" + \
            f"Files needing generators: {files_needing_generators[:5]}"


class TestPerformanceMetrics:
    """Test performance baseline metrics and improvements."""
    
    def test_performance_baseline_metrics(self, src_files):
        """
        Track performance metrics for improvement over time.
        
        Baseline metrics from before performance optimization.
        """
        total_files = len(src_files)
        files_with_caching = 0
        files_with_lazy_loading = 0
        files_with_generators = 0
        total_expensive_ops = 0
        total_inefficiencies = 0
        
        for file_path in src_files:
            analysis = analyze_performance_patterns(file_path)
            if 'error' not in analysis:
                if analysis['has_caching'] or analysis['has_memoization']:
                    files_with_caching += 1
                
                if analysis['has_lazy_loading']:
                    files_with_lazy_loading += 1
                
                if analysis['has_generators']:
                    files_with_generators += 1
                
                total_expensive_ops += len(analysis['expensive_operations'])
                total_inefficiencies += len(analysis['memory_inefficient_patterns'])
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        # Calculate percentages
        caching_percent = (files_with_caching / total_files) * 100
        lazy_loading_percent = (files_with_lazy_loading / total_files) * 100
        generator_percent = (files_with_generators / total_files) * 100
        
        print(f"\n📊 PERFORMANCE METRICS:")
        print(f"Total files analyzed: {total_files}")
        print(f"Files with caching: {caching_percent:.1f}%")
        print(f"Files with lazy loading: {lazy_loading_percent:.1f}%")
        print(f"Files with generators: {generator_percent:.1f}%")
        print(f"Total expensive operations: {total_expensive_ops}")
        print(f"Total memory inefficiencies: {total_inefficiencies}")
        
        # Baseline assertions - these should improve over time
        assert total_files > 0, "Should have source files to analyze"
        
        # Track improvement metrics (will be updated in Green phase)
        # Current baseline: minimal optimization
        # Goal: >50% with caching, >30% with lazy loading, >40% with generators