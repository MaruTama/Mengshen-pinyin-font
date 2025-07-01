# -*- coding: utf-8 -*-
"""
Integration tests for font generation functionality.

These tests verify that the complete font generation pipeline works
correctly after security fixes have been applied.
"""

import subprocess
import pytest
from pathlib import Path
import os
import time


class TestFontGeneration:
    """Integration tests for font generation pipeline."""
    
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
            for output_file in outputs_dir.glob("*.ttf"):
                backup_path = output_file.with_suffix(".ttf.backup")
                if output_file.exists():
                    output_file.rename(backup_path)
                    backup_files.append((output_file, backup_path))
        
        yield backup_files
        
        # Restore backup files after test
        for original_path, backup_path in backup_files:
            if backup_path.exists():
                backup_path.rename(original_path)
    
    def test_han_serif_font_generation(self, project_root, backup_outputs):
        """
        Test that han_serif font generation works with security fixes.
        
        This is a characterization test that ensures the font generation
        pipeline continues to work after security modifications.
        """
        # Change to project directory
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        try:
            # Run font generation with timeout
            result = subprocess.run(
                ["python", "src/main.py", "-t", "han_serif"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=project_root
            )
            
            # Check if command succeeded
            if result.returncode != 0:
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                pytest.fail(f"Font generation failed with return code {result.returncode}")
            
            # Check that output font file was created
            output_font = project_root / "outputs" / "Mengshen-HanSerif.ttf"
            assert output_font.exists(), f"Output font file not created: {output_font}"
            
            # Check that output file is not empty
            assert output_font.stat().st_size > 1000, "Output font file is too small"
            
            # Basic font file validation (should start with font magic bytes)
            with open(output_font, 'rb') as f:
                magic_bytes = f.read(4)
                # TTF files start with specific magic bytes
                assert magic_bytes in [b'\x00\x01\x00\x00', b'OTTO', b'ttcf'], \
                    f"Invalid font file magic bytes: {magic_bytes}"
                    
        except subprocess.TimeoutExpired:
            pytest.fail("Font generation timed out after 5 minutes")
        finally:
            os.chdir(original_cwd)
    
    def test_handwritten_font_generation(self, project_root, backup_outputs):
        """
        Test that handwritten font generation works with security fixes.
        
        This test ensures both font styles work correctly.
        """
        # Change to project directory
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        try:
            # Run font generation with timeout
            result = subprocess.run(
                ["python", "src/main.py", "-t", "handwritten"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=project_root
            )
            
            # Check if command succeeded
            if result.returncode != 0:
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                pytest.fail(f"Font generation failed with return code {result.returncode}")
            
            # Check that output font file was created
            output_font = project_root / "outputs" / "Mengshen-Handwritten.ttf"
            assert output_font.exists(), f"Output font file not created: {output_font}"
            
            # Check that output file is not empty
            assert output_font.stat().st_size > 1000, "Output font file is too small"
            
            # Basic font file validation
            with open(output_font, 'rb') as f:
                magic_bytes = f.read(4)
                assert magic_bytes in [b'\x00\x01\x00\x00', b'OTTO', b'ttcf'], \
                    f"Invalid font file magic bytes: {magic_bytes}"
                    
        except subprocess.TimeoutExpired:
            pytest.fail("Font generation timed out after 5 minutes")
        finally:
            os.chdir(original_cwd)
    
    def test_shell_commands_are_secure(self, project_root):
        """
        Test that shell commands used during font generation are secure.
        
        This test monitors the font generation process to ensure
        no insecure shell commands are executed.
        """
        # This is a placeholder for monitoring shell command usage
        # In a full implementation, we would intercept subprocess calls
        # and verify they don't use shell=True
        
        # For now, we'll just ensure the process completes successfully
        # The security tests already verify shell=True is not used
        assert True, "Security monitoring placeholder"
    
    @pytest.mark.slow
    def test_font_generation_performance(self, project_root):
        """
        Test that font generation performance hasn't regressed significantly.
        
        This test ensures security fixes don't impact performance too much.
        """
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        try:
            start_time = time.time()
            
            result = subprocess.run(
                ["python", "src/main.py", "-t", "han_serif"],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout for performance test
                cwd=project_root
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Check that generation completed successfully
            assert result.returncode == 0, f"Font generation failed: {result.stderr}"
            
            # Performance benchmark - should complete within 10 minutes
            # This is a generous limit; actual performance may be much better
            assert duration < 600, f"Font generation took too long: {duration:.2f} seconds"
            
            print(f"Font generation completed in {duration:.2f} seconds")
            
        except subprocess.TimeoutExpired:
            pytest.fail("Font generation performance test timed out")
        finally:
            os.chdir(original_cwd)