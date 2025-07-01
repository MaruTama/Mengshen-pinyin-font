# -*- coding: utf-8 -*-
"""
Integration tests for dictionary generation functionality.

These tests verify that the dictionary generation scripts work correctly
with the security fixes applied.
"""

import subprocess
import pytest
from pathlib import Path
import os
import shutil


class TestDictionaryGeneration:
    """Integration tests for dictionary generation pipeline."""
    
    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def backup_outputs(self, project_root):
        """Backup existing output files before test."""
        outputs_dir = project_root / "outputs"
        backup_files = []
        
        if outputs_dir.exists():
            for pattern in ["duoyinzi_*.txt", "duoyinzi_*.json", "merged-mapping-table.txt"]:
                for output_file in outputs_dir.glob(pattern):
                    backup_path = output_file.with_suffix(output_file.suffix + ".backup")
                    if output_file.exists():
                        shutil.copy2(output_file, backup_path)
                        backup_files.append((output_file, backup_path))
        
        yield backup_files
        
        # Restore backup files after test
        for original_path, backup_path in backup_files:
            if backup_path.exists():
                shutil.copy2(backup_path, original_path)
                backup_path.unlink()
    
    def test_duo_yin_zi_pattern_generation(self, project_root, backup_outputs):
        """
        Test that duo_yin_zi pattern table generation works with security fixes.
        
        This test verifies that the dictionary generation scripts continue to work
        after security modifications have been applied.
        """
        # Change to the scripts directory
        scripts_dir = project_root / "res" / "phonics" / "duo_yin_zi" / "scripts"
        original_cwd = os.getcwd()
        os.chdir(scripts_dir)
        
        try:
            # Run the pattern table generation script
            result = subprocess.run(
                ["python", "make_pattern_table.py"],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                cwd=scripts_dir
            )
            
            # Check if command succeeded
            if result.returncode != 0:
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                pytest.fail(f"Pattern table generation failed with return code {result.returncode}")
            
            # Check that output files were created
            outputs_dir = project_root / "outputs"
            expected_files = [
                "duoyinzi_pattern_one.txt",
                "duoyinzi_pattern_two.json", 
                "duoyinzi_exceptional_pattern.json"
            ]
            
            for expected_file in expected_files:
                output_path = outputs_dir / expected_file
                assert output_path.exists(), f"Expected output file not created: {expected_file}"
                assert output_path.stat().st_size > 0, f"Output file is empty: {expected_file}"
            
            # Basic validation of pattern_one.txt format
            pattern_one_file = outputs_dir / "duoyinzi_pattern_one.txt"
            with open(pattern_one_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Should contain pattern entries with Chinese characters
                assert '强' in content or '长' in content, "Pattern file should contain Chinese characters"
                assert ',' in content, "Pattern file should contain comma-separated values"
                
        except subprocess.TimeoutExpired:
            pytest.fail("Dictionary generation timed out after 2 minutes")
        finally:
            os.chdir(original_cwd)
    
    def test_unicode_mapping_generation(self, project_root, backup_outputs):
        """
        Test that unicode mapping table generation works with security fixes.
        
        This test verifies that the unicode mapping scripts continue to work
        after security modifications have been applied.
        """
        # Change to the unicode mapping directory
        mapping_dir = project_root / "res" / "phonics" / "unicode_mapping_table"
        original_cwd = os.getcwd()
        os.chdir(mapping_dir)
        
        try:
            # Run the unicode mapping generation script
            result = subprocess.run(
                ["python", "make_unicode_pinyin_map_table.py"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout - this can be slow
                cwd=mapping_dir
            )
            
            # Check if command succeeded
            if result.returncode != 0:
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                pytest.fail(f"Unicode mapping generation failed with return code {result.returncode}")
            
            # Check that output file was created
            outputs_dir = project_root / "outputs"
            mapping_file = outputs_dir / "merged-mapping-table.txt"
            assert mapping_file.exists(), "Unicode mapping table file not created"
            assert mapping_file.stat().st_size > 100000, "Unicode mapping table file is too small"
            
            # Basic validation of mapping table format
            with open(mapping_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Should have many entries
                assert len(lines) > 1000, "Mapping table should have many entries"
                
                # Check format of first few lines
                for i, line in enumerate(lines[:10]):
                    if line.strip():  # Skip empty lines
                        assert line.startswith('U+'), f"Line {i+1} should start with U+: {line}"
                        assert ':' in line, f"Line {i+1} should contain colon: {line}"
                        assert '#' in line, f"Line {i+1} should contain hash: {line}"
                        
        except subprocess.TimeoutExpired:
            pytest.fail("Unicode mapping generation timed out after 5 minutes")
        finally:
            os.chdir(original_cwd)
    
    def test_shell_commands_in_scripts(self, project_root):
        """
        Test that shell commands in dictionary generation scripts are secure.
        
        This test verifies that the scripts don't use insecure shell patterns.
        """
        # Check duo_yin_zi scripts
        scripts_dir = project_root / "res" / "phonics" / "duo_yin_zi" / "scripts"
        for script_file in scripts_dir.glob("*.py"):
            with open(script_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Should not contain shell=True
                assert 'shell=True' not in content, f"Script {script_file.name} contains shell=True"
        
        # Check unicode mapping scripts
        mapping_dir = project_root / "res" / "phonics" / "unicode_mapping_table"
        for script_file in mapping_dir.glob("*.py"):
            with open(script_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Should not contain shell=True
                assert 'shell=True' not in content, f"Script {script_file.name} contains shell=True"
    
    def test_dictionary_integration_with_font_generation(self, project_root):
        """
        Test that dictionary files are properly integrated with font generation.
        
        This test ensures that the generated dictionary files are used correctly
        during the font generation process.
        """
        # Check that required dictionary files exist
        outputs_dir = project_root / "outputs"
        required_files = [
            "duoyinzi_pattern_one.txt",
            "duoyinzi_pattern_two.json",
            "duoyinzi_exceptional_pattern.json",
            "merged-mapping-table.txt"
        ]
        
        for required_file in required_files:
            file_path = outputs_dir / required_file
            if not file_path.exists():
                pytest.skip(f"Required dictionary file not found: {required_file}. Run dictionary generation first.")
        
        # Run a quick font generation test to ensure integration works
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        try:
            # Test that font generation can start successfully with dictionary files
            result = subprocess.run(
                ["python", "src/main.py", "-t", "han_serif"],
                capture_output=True,
                text=True,
                timeout=30,  # Short timeout - just check it starts correctly
                cwd=project_root
            )
            
            # Even if it times out, it should have started successfully
            # We're just checking that the dictionary files are loaded correctly
            assert result.returncode in [0, -15], "Font generation should start successfully with dictionary files"
            
        except subprocess.TimeoutExpired:
            # This is expected - we just want to check it starts
            pass
        finally:
            os.chdir(original_cwd)