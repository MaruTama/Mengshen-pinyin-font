# -*- coding: utf-8 -*-
"""
Complete pipeline integration tests.

These tests verify that the entire font generation pipeline works correctly
from dictionary generation to final font output with security fixes applied.
"""

import subprocess
import pytest
from pathlib import Path
import os
import shutil
import time


class TestCompletePipeline:
    """Integration tests for complete font generation pipeline."""
    
    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def clean_outputs(self, project_root):
        """Clean outputs directory before test."""
        outputs_dir = project_root / "outputs"
        backup_dir = outputs_dir.parent / "outputs_backup"
        
        # Backup existing outputs
        if outputs_dir.exists():
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(outputs_dir, backup_dir)
            
            # Clean dictionary files for fresh generation
            for pattern in ["duoyinzi_*.txt", "duoyinzi_*.json", "merged-mapping-table.txt"]:
                for file_path in outputs_dir.glob(pattern):
                    file_path.unlink()
        
        yield
        
        # Restore backup
        if backup_dir.exists():
            if outputs_dir.exists():
                shutil.rmtree(outputs_dir)
            shutil.copytree(backup_dir, outputs_dir)
            shutil.rmtree(backup_dir)
    
    @pytest.mark.slow
    def test_complete_pipeline_han_serif(self, project_root, clean_outputs):
        """
        Test complete pipeline: dictionary generation → font generation.
        
        This test runs the complete pipeline from scratch to ensure
        all components work together with security fixes.
        """
        original_cwd = os.getcwd()
        
        try:
            # Step 1: Generate duo_yin_zi patterns
            scripts_dir = project_root / "res" / "phonics" / "duo_yin_zi" / "scripts"
            os.chdir(scripts_dir)
            
            print("Step 1: Generating duo_yin_zi patterns...")
            result = subprocess.run(
                ["python", "make_pattern_table.py"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            assert result.returncode == 0, f"Pattern generation failed: {result.stderr}"
            print("✓ Duo_yin_zi patterns generated successfully")
            
            # Step 2: Generate unicode mapping table
            mapping_dir = project_root / "res" / "phonics" / "unicode_mapping_table"
            os.chdir(mapping_dir)
            
            print("Step 2: Generating unicode mapping table...")
            result = subprocess.run(
                ["python", "make_unicode_pinyin_map_table.py"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            assert result.returncode == 0, f"Unicode mapping generation failed: {result.stderr}"
            print("✓ Unicode mapping table generated successfully")
            
            # Step 3: Generate font
            os.chdir(project_root)
            
            print("Step 3: Generating han_serif font...")
            start_time = time.time()
            result = subprocess.run(
                ["python", "src/main.py", "-t", "han_serif"],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for complete pipeline
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert result.returncode == 0, f"Font generation failed: {result.stderr}"
            print(f"✓ Font generated successfully in {duration:.2f} seconds")
            
            # Verify all outputs exist
            outputs_dir = project_root / "outputs"
            
            # Dictionary files
            dictionary_files = [
                "duoyinzi_pattern_one.txt",
                "duoyinzi_pattern_two.json", 
                "duoyinzi_exceptional_pattern.json",
                "merged-mapping-table.txt"
            ]
            
            for dict_file in dictionary_files:
                file_path = outputs_dir / dict_file
                assert file_path.exists(), f"Dictionary file not found: {dict_file}"
                assert file_path.stat().st_size > 0, f"Dictionary file is empty: {dict_file}"
            
            # Font file
            font_file = outputs_dir / "Mengshen-HanSerif.ttf"
            assert font_file.exists(), "Font file not created"
            assert font_file.stat().st_size > 1000000, "Font file is too small"
            
            # Validate font file format
            with open(font_file, 'rb') as f:
                magic_bytes = f.read(4)
                assert magic_bytes in [b'\\x00\\x01\\x00\\x00', b'OTTO', b'ttcf'], \
                    f"Invalid font file magic bytes: {magic_bytes}"
            
            print("✓ Complete pipeline validation successful")
            
        except subprocess.TimeoutExpired as e:
            pytest.fail(f"Pipeline step timed out: {e}")
        finally:
            os.chdir(original_cwd)
    
    def test_pipeline_security_validation(self, project_root):
        """
        Test that the complete pipeline doesn't use insecure shell commands.
        
        This test validates that all scripts in the pipeline are secure.
        """
        # Check all Python files in the pipeline
        check_dirs = [
            project_root / "src",
            project_root / "res" / "phonics" / "duo_yin_zi" / "scripts",
            project_root / "res" / "phonics" / "unicode_mapping_table",
            project_root / "tools"
        ]
        
        insecure_files = []
        
        for check_dir in check_dirs:
            if not check_dir.exists():
                continue
                
            for py_file in check_dir.glob("**/*.py"):
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        stripped = line.strip()
                        # Skip comments
                        if stripped.startswith('#'):
                            continue
                        # Check for shell=True (but not shell=False)
                        if 'shell=True' in line and 'shell=False' not in line:
                            relative_path = py_file.relative_to(project_root)
                            insecure_files.append(f"{relative_path}:{line_num}")
        
        assert len(insecure_files) == 0, \
            f"Found insecure shell=True usage in: {insecure_files}"
    
    def test_pipeline_performance_benchmark(self, project_root):
        """
        Test that the complete pipeline performance is acceptable.
        
        This test ensures that security fixes don't severely impact performance.
        """
        # This is a lightweight performance check
        # Run just the font generation part (assume dictionaries exist)
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        try:
            # Check if dictionary files exist, skip if not
            outputs_dir = project_root / "outputs"
            required_files = [
                "duoyinzi_pattern_one.txt",
                "duoyinzi_pattern_two.json",
                "duoyinzi_exceptional_pattern.json", 
                "merged-mapping-table.txt"
            ]
            
            for required_file in required_files:
                if not (outputs_dir / required_file).exists():
                    pytest.skip(f"Dictionary file not found: {required_file}")
            
            # Time the font generation
            start_time = time.time()
            result = subprocess.run(
                ["python", "src/main.py", "-t", "han_serif"],
                capture_output=True,
                text=True,
                timeout=600
            )
            end_time = time.time()
            
            assert result.returncode == 0, f"Font generation failed: {result.stderr}"
            
            duration = end_time - start_time
            
            # Performance benchmark: should complete within 10 minutes
            assert duration < 600, f"Font generation too slow: {duration:.2f} seconds"
            
            # Log performance for monitoring
            print(f"Font generation performance: {duration:.2f} seconds")
            
        except subprocess.TimeoutExpired:
            pytest.fail("Font generation performance test timed out")
        finally:
            os.chdir(original_cwd)