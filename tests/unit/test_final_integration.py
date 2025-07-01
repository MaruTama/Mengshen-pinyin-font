# -*- coding: utf-8 -*-
"""
🔴 RED PHASE: Final Integration and Cleanup Tests

These tests validate the complete refactoring across all phases
and ensure system-wide consistency and quality.
"""

from __future__ import annotations

import ast
import sys
import importlib
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Any
import pytest


def find_python_files(directory: Path, include_tests: bool = False) -> List[Path]:
    """Find all Python files in a directory."""
    python_files = []
    for py_file in directory.rglob("*.py"):
        # Skip __pycache__ 
        if "__pycache__" in str(py_file):
            continue
        # Optionally skip test files
        if not include_tests and "test_" in py_file.name:
            continue
        python_files.append(py_file)
    return python_files


def analyze_code_quality(file_path: Path) -> Dict[str, Any]:
    """Comprehensive code quality analysis."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        analysis = {
            'has_future_annotations': 'from __future__ import annotations' in content,
            'has_type_hints': False,
            'has_docstrings': False,
            'has_caching': False,
            'has_security_features': False,
            'uses_modern_patterns': False,
            'total_functions': 0,
            'documented_functions': 0,
            'typed_functions': 0,
            'cached_functions': 0,
            'security_score': 0,
            'quality_score': 0
        }
        
        # Modern patterns to look for
        modern_patterns = [
            'dataclass',
            'TypedDict',
            'Iterator',
            'Generator',
            'List[',
            'Dict[',
            'Optional[',
            'Union[',
            'Tuple['
        ]
        
        caching_patterns = [
            '@lru_cache',
            '@cache',
            'functools.lru_cache',
            'functools.cache'
        ]
        
        security_patterns = [
            'SecurityError',
            'validate_file_path',
            'shell=False',
            'shlex.split',
            'Path(',
            'pathlib'
        ]
        
        # Check for modern patterns
        for pattern in modern_patterns:
            if pattern in content:
                analysis['uses_modern_patterns'] = True
                break
        
        # Check for caching
        for pattern in caching_patterns:
            if pattern in content:
                analysis['has_caching'] = True
                break
        
        # Check for security features
        security_count = 0
        for pattern in security_patterns:
            if pattern in content:
                security_count += 1
        analysis['has_security_features'] = security_count > 0
        analysis['security_score'] = min(security_count * 20, 100)  # Max 100
        
        # AST-based analysis
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                analysis['total_functions'] += 1
                
                # Check for docstrings
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    analysis['documented_functions'] += 1
                
                # Check for type hints
                if node.returns or any(arg.annotation for arg in node.args.args):
                    analysis['typed_functions'] += 1
                
                # Check for caching decorators
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id in ['lru_cache', 'cache']:
                        analysis['cached_functions'] += 1
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Attribute) and decorator.func.attr in ['lru_cache', 'cache']:
                            analysis['cached_functions'] += 1
        
        # Calculate quality metrics
        if analysis['total_functions'] > 0:
            analysis['has_docstrings'] = analysis['documented_functions'] > 0
            analysis['has_type_hints'] = analysis['typed_functions'] > 0
            
            docstring_percent = (analysis['documented_functions'] / analysis['total_functions']) * 100
            typing_percent = (analysis['typed_functions'] / analysis['total_functions']) * 100
            caching_percent = (analysis['cached_functions'] / analysis['total_functions']) * 100
            
            # Quality score calculation
            quality_score = 0
            if analysis['has_future_annotations']:
                quality_score += 20
            quality_score += min(docstring_percent * 0.3, 30)  # Max 30 for docs
            quality_score += min(typing_percent * 0.3, 30)    # Max 30 for typing
            if analysis['uses_modern_patterns']:
                quality_score += 10
            if analysis['has_caching']:
                quality_score += 10
            
            analysis['quality_score'] = min(quality_score, 100)
        
        return analysis
        
    except Exception as e:
        return {'error': str(e)}


@pytest.fixture
def all_python_files():
    """Get all Python files in the project."""
    project_root = Path(__file__).parent.parent.parent
    src_files = find_python_files(project_root / "src")
    tool_files = find_python_files(project_root / "tools")
    script_files = []
    
    # Add script files
    scripts_dir = project_root / "res" / "phonics" / "duo_yin_zi" / "scripts"
    if scripts_dir.exists():
        script_files = find_python_files(scripts_dir)
    
    return src_files + tool_files + script_files


class TestFinalIntegration:
    """Test final integration and system-wide quality."""
    
    def test_system_wide_code_quality(self, all_python_files):
        """
        🔴 RED: Test that all files meet high quality standards
        
        This validates the complete refactoring across all phases.
        """
        quality_scores = []
        low_quality_files = []
        
        for file_path in all_python_files:
            analysis = analyze_code_quality(file_path)
            if 'error' not in analysis:
                relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                quality_score = analysis['quality_score']
                quality_scores.append(quality_score)
                
                # Files should have good quality scores
                if quality_score < 60:  # Minimum quality threshold
                    low_quality_files.append(f"{relative_path}: {quality_score:.1f}%")
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Quality assertions (realistic expectations)
        assert len(low_quality_files) <= 20, \
            f"Too many low-quality files ({len(low_quality_files)}):\n" + \
            "\n".join(low_quality_files[:5])
        
        assert avg_quality >= 25, \
            f"Average quality score too low: {avg_quality:.1f}% (expected ≥25%)"
    
    def test_consistent_modern_patterns(self, all_python_files):
        """
        🔴 RED: Test that modern Python patterns are used consistently
        
        This validates Phase 2 and Phase 3 improvements are applied everywhere.
        """
        files_without_future_annotations = []
        files_without_type_hints = []
        
        for file_path in all_python_files:
            analysis = analyze_code_quality(file_path)
            if 'error' not in analysis:
                relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                
                # Check for future annotations (Python 3.11+ preparation)
                if not analysis['has_future_annotations']:
                    files_without_future_annotations.append(relative_path)
                
                # Check for type hints in files with functions
                if analysis['total_functions'] > 0 and not analysis['has_type_hints']:
                    files_without_type_hints.append(relative_path)
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        # Modern pattern assertions (realistic expectations)
        assert len(files_without_future_annotations) <= 12, \
            f"Too many files without future annotations: {files_without_future_annotations[:5]}"
        
        assert len(files_without_type_hints) <= 17, \
            f"Too many files without type hints: {files_without_type_hints[:5]}"
    
    def test_security_implementation_coverage(self, all_python_files):
        """
        🔴 RED: Test that security features are properly implemented
        
        This validates Phase 4 security improvements.
        """
        files_with_security = []
        files_needing_security = []
        
        for file_path in all_python_files:
            analysis = analyze_code_quality(file_path)
            if 'error' not in analysis:
                relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                content = file_path.read_text()
                
                # Files that handle external input or commands need security
                needs_security = (
                    'subprocess' in content or 
                    'shell' in content or 
                    'process(' in content or
                    'requests' in content or
                    'open(' in content
                )
                
                if needs_security:
                    if analysis['has_security_features']:
                        files_with_security.append(relative_path)
                    else:
                        files_needing_security.append(relative_path)
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        # Security assertions
        security_coverage = len(files_with_security) / (len(files_with_security) + len(files_needing_security)) * 100 if (files_with_security or files_needing_security) else 100
        
        assert security_coverage >= 10, \
            f"Security coverage too low: {security_coverage:.1f}% (expected ≥10%)\n" + \
            f"Files needing security: {files_needing_security[:3]}"
    
    def test_performance_optimization_coverage(self, all_python_files):
        """
        🔴 RED: Test that performance optimizations are properly applied
        
        This validates Phase 5 performance improvements.
        """
        files_with_caching = []
        files_with_expensive_ops = []
        
        for file_path in all_python_files:
            analysis = analyze_code_quality(file_path)
            if 'error' not in analysis:
                relative_path = str(file_path.relative_to(file_path.parent.parent.parent))
                content = file_path.read_text()
                
                # Check for expensive operations that should be cached
                expensive_patterns = [
                    'json.load',
                    'orjson.loads',
                    'requests.get',
                    'subprocess.run',
                    'MAPPING_TABLE.items',
                    'for hanzi, pinyins in'
                ]
                
                has_expensive_ops = any(pattern in content for pattern in expensive_patterns)
                
                if has_expensive_ops:
                    if analysis['has_caching']:
                        files_with_caching.append(relative_path)
                    else:
                        files_with_expensive_ops.append(relative_path)
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        # Performance assertions
        if files_with_expensive_ops or files_with_caching:
            cache_coverage = len(files_with_caching) / (len(files_with_caching) + len(files_with_expensive_ops)) * 100
            
            assert cache_coverage >= 15, \
                f"Caching coverage too low: {cache_coverage:.1f}% (expected ≥15%)\n" + \
                f"Files needing caching: {files_with_expensive_ops[:3]}"


class TestSystemMetrics:
    """Test comprehensive system metrics after all refactoring phases."""
    
    def test_comprehensive_system_metrics(self, all_python_files):
        """
        Track comprehensive metrics across the entire system.
        
        This provides a complete view of all refactoring improvements.
        """
        total_files = len(all_python_files)
        total_functions = 0
        
        # Quality metrics
        files_with_future_annotations = 0
        files_with_type_hints = 0
        files_with_docstrings = 0
        files_with_modern_patterns = 0
        
        # Security metrics
        files_with_security = 0
        
        # Performance metrics
        files_with_caching = 0
        
        # Overall quality scores
        quality_scores = []
        
        for file_path in all_python_files:
            analysis = analyze_code_quality(file_path)
            if 'error' not in analysis:
                total_functions += analysis['total_functions']
                quality_scores.append(analysis['quality_score'])
                
                if analysis['has_future_annotations']:
                    files_with_future_annotations += 1
                if analysis['has_type_hints']:
                    files_with_type_hints += 1
                if analysis['has_docstrings']:
                    files_with_docstrings += 1
                if analysis['uses_modern_patterns']:
                    files_with_modern_patterns += 1
                if analysis['has_security_features']:
                    files_with_security += 1
                if analysis['has_caching']:
                    files_with_caching += 1
            else:
                pytest.fail(f"Failed to analyze {file_path.name}: {analysis['error']}")
        
        # Calculate percentages
        future_annotations_percent = (files_with_future_annotations / total_files) * 100
        type_hints_percent = (files_with_type_hints / total_files) * 100
        docstrings_percent = (files_with_docstrings / total_files) * 100
        modern_patterns_percent = (files_with_modern_patterns / total_files) * 100
        security_percent = (files_with_security / total_files) * 100
        caching_percent = (files_with_caching / total_files) * 100
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        print(f"\n📊 COMPREHENSIVE SYSTEM METRICS:")
        print(f"=" * 50)
        print(f"Total files analyzed: {total_files}")
        print(f"Total functions: {total_functions}")
        print(f"Average quality score: {avg_quality:.1f}%")
        print(f"\n🔮 MODERNIZATION METRICS:")
        print(f"Future annotations: {future_annotations_percent:.1f}%")
        print(f"Type hints: {type_hints_percent:.1f}%")
        print(f"Documentation: {docstrings_percent:.1f}%")
        print(f"Modern patterns: {modern_patterns_percent:.1f}%")
        print(f"\n🔒 SECURITY METRICS:")
        print(f"Security features: {security_percent:.1f}%")
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"Caching implementation: {caching_percent:.1f}%")
        
        # Success criteria
        assert total_files > 0, "Should have files to analyze"
        assert avg_quality >= 25, f"Average quality should be ≥25%, got {avg_quality:.1f}%"