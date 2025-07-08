# -*- coding: utf-8 -*-
"""
Dictionary Generation Integration Tests.
"""

import pytest
from pathlib import Path


class TestDictionaryGeneration:
    """Dictionary generation validation tests."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_pipeline_phase_dictionary_generation(self, project_root):
        """
        🧪 PIPELINE PHASE: Test dictionary generation step.
        """
        # Instead of shelling out, import and call the main function directly.
        from res.phonics.duo_yin_zi.scripts.make_pattern_table import main as make_pattern_table_main
        from res.phonics.unicode_mapping_table.make_unicode_pinyin_map_table import main as make_unicode_pinyin_map_table_main

        # Run dictionary generation scripts
        make_pattern_table_main()
        make_unicode_pinyin_map_table_main()

        # Add assertions to verify the output files are created and not empty.
        outputs_dir = project_root / "outputs"
        assert (outputs_dir / "duoyinzi_pattern_one.txt").exists()
        assert (outputs_dir / "duoyinzi_pattern_one.txt").stat().st_size > 0
        assert (outputs_dir / "duoyinzi_pattern_two.json").exists()
        assert (outputs_dir / "duoyinzi_pattern_two.json").stat().st_size > 0
        assert (outputs_dir / "duoyinzi_exceptional_pattern.json").exists()
        assert (outputs_dir / "duoyinzi_exceptional_pattern.json").stat().st_size > 0

        assert (project_root / "outputs" / "merged-mapping-table.txt").exists()
        assert (project_root / "outputs" / "merged-mapping-table.txt").stat().st_size > 0
