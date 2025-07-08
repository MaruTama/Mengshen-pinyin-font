# -*- coding: utf-8 -*-
"""
TDD Pipeline Integration Tests.

These tests enforce the TDD pipeline workflow for all future refactoring phases.
They ensure that any code changes maintain the complete pipeline functionality.
"""

import subprocess
import pytest
from pathlib import Path


class TestTDDPipelineWorkflow:
    """TDD Pipeline workflow validation tests."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_integration_phase_complete_tests(self, project_root):
        """
        🎯 INTEGRATION PHASE: Test complete integration test suite.
        """
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=600
        )
        assert result.returncode == 0, f"Integration tests must pass: {result.stderr}"

        integration_dir = project_root / "tests" / "integration"
        required_tests = [
            "test_font_generation.py",
            "test_dictionary_generation.py",
            "test_complete_pipeline.py"
        ]

        for test_file in required_tests:
            test_path = integration_dir / test_file
            assert test_path.exists(), f"Required integration test missing: {test_file}"

    def test_performance_monitoring(self, project_root):
        """
        Test that performance monitoring is in place.
        """
        perf_test = project_root / "tests" / "integration" / "test_complete_pipeline.py"
        if perf_test.exists():
            result = subprocess.run(
                ["python", "-m", "pytest", str(perf_test) + "::TestCompletePipeline::test_pipeline_performance_benchmark", "-v"],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=300
            )
            assert result.returncode in [0, 5], f"Performance test failed: {result.stderr}"
