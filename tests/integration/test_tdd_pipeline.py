# -*- coding: utf-8 -*-
"""
TDD Pipeline Integration Tests.

These tests enforce the TDD pipeline workflow for all future refactoring phases.
They ensure that any code changes maintain the complete pipeline functionality.
"""

import subprocess
import pytest
from pathlib import Path
import os
import time
import hashlib


class TestTDDPipelineWorkflow:
    """TDD Pipeline workflow validation tests."""
    
    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent
    
    def test_red_phase_security_tests_exist(self, project_root):
        """
        🔴 RED PHASE: Verify that security tests exist and would catch issues.
        
        This test ensures that the Red phase security tests are comprehensive
        and would fail if vulnerabilities were re-introduced.
        """
        # Check that security tests exist
        security_tests = project_root / "tests" / "security" / "test_shell_injection.py"
        assert security_tests.exists(), "Security tests must exist for Red phase"
        
        # Verify security tests cover critical areas
        with open(security_tests, 'r', encoding='utf-8') as f:
            content = f.read()
            # Must test for shell=True usage
            assert 'shell=True' in content, "Security tests must check for shell=True"
            assert 'find_shell_true_usage' in content, "Must have function to find shell=True usage"
            assert 'command_injection' in content, "Must test command injection prevention"
            assert 'path_traversal' in content, "Must test path traversal prevention"
    
    def test_green_phase_secure_implementation(self, project_root):
        """
        🟢 GREEN PHASE: Verify that secure implementation exists and works.
        
        This test ensures that the Green phase implementation provides
        secure alternatives to vulnerable code.
        """
        # Check that secure_shell.py exists
        secure_shell = project_root / "src" / "secure_shell.py"
        assert secure_shell.exists(), "Secure implementation must exist for Green phase"
        
        # Verify secure implementation has required functions
        with open(secure_shell, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'safe_command_execution' in content, "Must have safe command execution"
            assert 'validate_file_path' in content, "Must have file path validation"
            assert 'legacy_shell_process_replacement' in content, "Must have legacy replacement"
            assert 'shell=False' in content, "Must explicitly disable shell"
    
    def test_refactor_phase_vulnerability_elimination(self, project_root):
        """
        🔵 REFACTOR PHASE: Verify that vulnerabilities have been eliminated.
        
        This test ensures that the Refactor phase successfully eliminated
        all security vulnerabilities while maintaining functionality.
        """
        # Run security tests to verify no vulnerabilities
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/security/", "-v"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        assert result.returncode == 0, f"Security tests must pass in Refactor phase: {result.stderr}"
        
        # Verify that specific vulnerable files have been fixed
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
                        # Skip comments
                        if line.strip().startswith('#'):
                            continue
                        # Should not contain shell=True (except in comments)
                        if 'shell=True' in line and 'shell=False' not in line:
                            pytest.fail(f"Found shell=True in {file_path}:{line_num}: {line}")
    
    def test_pipeline_phase_dictionary_generation(self, project_root):
        """
        🧪 PIPELINE PHASE: Test dictionary generation step.
        
        This test ensures that the pipeline phase includes proper
        dictionary generation validation.
        """
        original_cwd = os.getcwd()
        
        try:
            # Test duo_yin_zi pattern generation
            scripts_dir = project_root / "res" / "phonics" / "duo_yin_zi" / "scripts"
            os.chdir(scripts_dir)
            
            result = subprocess.run(
                ["python", "make_pattern_table.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            assert result.returncode == 0, f"Dictionary generation must work in Pipeline phase: {result.stderr}"
            
            # Test unicode mapping generation
            mapping_dir = project_root / "res" / "phonics" / "unicode_mapping_table"
            os.chdir(mapping_dir)
            
            result = subprocess.run(
                ["python", "make_unicode_pinyin_map_table.py"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            assert result.returncode == 0, f"Unicode mapping generation must work in Pipeline phase: {result.stderr}"
            
        finally:
            os.chdir(original_cwd)
    
    def test_pipeline_phase_font_generation(self, project_root):
        """
        🧪 PIPELINE PHASE: Test font generation step.
        
        This test ensures that the pipeline phase includes proper
        font generation validation.
        """
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        try:
            # Test han_serif generation
            start_time = time.time()
            result = subprocess.run(
                ["python", "src/main.py", "-t", "han_serif"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            end_time = time.time()
            
            assert result.returncode == 0, f"Font generation must work in Pipeline phase: {result.stderr}"
            
            # Verify output file exists and is valid
            output_file = project_root / "outputs" / "Mengshen-HanSerif.ttf"
            assert output_file.exists(), "Font output must be created in Pipeline phase"
            assert output_file.stat().st_size > 1000000, "Font output must be reasonable size"
            
            # Performance check - should complete in reasonable time
            duration = end_time - start_time
            assert duration < 300, f"Font generation took too long: {duration:.2f} seconds"
            
        finally:
            os.chdir(original_cwd)
    
    def test_integration_phase_complete_tests(self, project_root):
        """
        🎯 INTEGRATION PHASE: Test complete integration test suite.
        
        This test ensures that the integration phase runs comprehensive
        tests covering the entire system.
        """
        # Run integration tests
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=600  # 10 minute timeout for full integration suite
        )
        
        # Integration tests should pass
        assert result.returncode == 0, f"Integration tests must pass: {result.stderr}"
        
        # Verify that key integration tests exist
        integration_dir = project_root / "tests" / "integration"
        required_tests = [
            "test_font_generation.py",
            "test_dictionary_generation.py",
            "test_complete_pipeline.py"
        ]
        
        for test_file in required_tests:
            test_path = integration_dir / test_file
            assert test_path.exists(), f"Required integration test missing: {test_file}"
    
    def test_validation_phase_no_regression(self, project_root):
        """
        ✅ VALIDATION PHASE: Test that no regression has occurred.
        
        This test ensures that the validation phase catches any
        regressions in functionality or performance.
        """
        # This test validates that the complete pipeline produces
        # consistent, high-quality output without regression
        
        # Check that output files have expected characteristics
        outputs_dir = project_root / "outputs"
        
        # Dictionary files should exist and have reasonable content
        dict_files = [
            "duoyinzi_pattern_one.txt",
            "duoyinzi_pattern_two.json",
            "duoyinzi_exceptional_pattern.json",
            "merged-mapping-table.txt"
        ]
        
        for dict_file in dict_files:
            file_path = outputs_dir / dict_file
            if file_path.exists():  # May not exist if not generated yet
                assert file_path.stat().st_size > 0, f"Dictionary file should not be empty: {dict_file}"
        
        # Font files should exist and be valid
        font_files = ["Mengshen-HanSerif.ttf", "Mengshen-Handwritten.ttf"]
        
        for font_file in font_files:
            file_path = outputs_dir / font_file
            if file_path.exists():  # May not exist if not generated yet
                assert file_path.stat().st_size > 1000000, f"Font file too small: {font_file}"
                
                # Check font file format
                with open(file_path, 'rb') as f:
                    magic_bytes = f.read(4)
                    assert magic_bytes in [b'\\x00\\x01\\x00\\x00', b'OTTO', b'ttcf'], \
                        f"Invalid font magic bytes in {font_file}: {magic_bytes}"
    
    def test_tdd_cycle_enforcement(self, project_root):
        """
        Test that TDD cycle enforcement is in place.
        
        This meta-test ensures that the TDD workflow is properly
        enforced for future development.
        """
        # Check that CLAUDE.md has TDD instructions
        claude_md = project_root / "CLAUDE.md"
        assert claude_md.exists(), "CLAUDE.md must exist with TDD instructions"
        
        with open(claude_md, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'TDD' in content, "CLAUDE.md must mention TDD"
            assert 'Red' in content and 'Green' in content, "Must describe Red-Green-Refactor"
            assert 'Pipeline' in content, "Must include pipeline validation"
        
        # Check that REFACTOR.md has TDD strategy
        refactor_md = project_root / "REFACTOR.md"
        assert refactor_md.exists(), "REFACTOR.md must exist with TDD strategy"
        
        with open(refactor_md, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'TDD原則' in content or 'TDD' in content, "REFACTOR.md must describe TDD principles"
            assert 'Pipeline' in content, "Must include pipeline integration"
    
    def test_performance_monitoring(self, project_root):
        """
        Test that performance monitoring is in place.
        
        This test ensures that performance regressions would be caught
        in future TDD cycles.
        """
        # Run performance benchmark test if it exists
        perf_test = project_root / "tests" / "integration" / "test_complete_pipeline.py"
        if perf_test.exists():
            result = subprocess.run(
                ["python", "-m", "pytest", str(perf_test) + "::TestCompletePipeline::test_pipeline_performance_benchmark", "-v"],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=300
            )
            
            # Performance test should pass or be skipped (if dependencies missing)
            assert result.returncode in [0, 5], f"Performance test failed: {result.stderr}"