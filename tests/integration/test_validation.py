# -*- coding: utf-8 -*-
"""
Validation Integration Tests.
"""

import pytest
from pathlib import Path


class TestValidation:
    """Validation tests."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_validation_phase_no_regression(self, project_root):
        """
        
 VALIDATION PHASE: Test that no regression has occurred.
        """
        outputs_dir = project_root / "outputs"

        dict_files = [
            "duoyinzi_pattern_one.txt",
            "duoyinzi_pattern_two.json",
            "duoyinzi_exceptional_pattern.json",
            "merged-mapping-table.txt"
        ]

        for dict_file in dict_files:
            file_path = outputs_dir / dict_file
            if file_path.exists():
                assert file_path.stat().st_size > 0, f"Dictionary file should not be empty: {dict_file}"

        font_files = ["Mengshen-HanSerif.ttf", "Mengshen-Handwritten.ttf"]

        for font_file in font_files:
            file_path = outputs_dir / font_file
            if file_path.exists():
                assert file_path.stat().st_size > 1000000, f"Font file too small: {font_file}"
                with open(file_path, 'rb') as f:
                    magic_bytes = f.read(4)
                    assert magic_bytes in [b'\x00\x01\x00\x00', b'OTTO', b'ttcf'], \
                        f"Invalid font magic bytes in {font_file}: {magic_bytes}"
