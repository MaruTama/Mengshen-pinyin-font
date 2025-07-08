# -*- coding: utf-8 -*-
"""
Generation Pipeline Integration Tests.
"""

import pytest
from pathlib import Path
import time


class TestGenerationPipeline:
    """Generation pipeline validation tests."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.mark.slow
    def test_pipeline_phase_font_generation(self, project_root, monkeypatch):
        """
        🧪 PIPELINE PHASE: Test font generation step.
        """
        # Instead of shelling out, import and call the main function directly.
        from src.main import main

        # Use monkeypatch to simulate command-line arguments
        monkeypatch.setattr('sys.argv', ['src/main.py', '-t', 'han_serif'])

        start_time = time.time()
        main()
        end_time = time.time()

        output_file = project_root / "outputs" / "Mengshen-HanSerif.ttf"
        assert output_file.exists(), "Font output must be created"
        assert output_file.stat().st_size > 1000000, "Font output must be reasonable size"

        duration = end_time - start_time
        assert duration < 300, f"Font generation took too long: {duration:.2f} seconds"
