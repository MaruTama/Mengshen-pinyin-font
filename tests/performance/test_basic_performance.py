"""
Basic performance tests for the Mengshen font generation pipeline.

These tests provide baseline performance benchmarks for CI/CD pipeline.
"""

import time
from typing import List

import pytest


class TestBasicPerformance:
    """Basic performance benchmark tests."""

    @pytest.mark.benchmark(group="string_operations")
    def test_string_concatenation_performance(self, benchmark):
        """Benchmark string concatenation operations."""

        def string_concat():
            result = ""
            for i in range(1000):
                result += f"test_{i}_"
            return result

        result = benchmark(string_concat)
        assert len(result) > 0

    @pytest.mark.benchmark(group="list_operations")
    def test_list_comprehension_performance(self, benchmark):
        """Benchmark list comprehension operations."""

        def list_comprehension():
            return [i * 2 for i in range(10000)]

        result = benchmark(list_comprehension)
        assert len(result) == 10000

    @pytest.mark.benchmark(group="dict_operations")
    def test_dict_creation_performance(self, benchmark):
        """Benchmark dictionary creation operations."""

        def dict_creation():
            return {f"key_{i}": f"value_{i}" for i in range(1000)}

        result = benchmark(dict_creation)
        assert len(result) == 1000

    @pytest.mark.benchmark(group="file_operations")
    def test_mock_file_processing_performance(self, benchmark):
        """Benchmark mock file processing operations."""

        def mock_file_processing():
            # Simulate file processing without actual I/O
            data = []
            for i in range(100):
                line = f"Unicode_{i:04d}:pinyin_{i}"
                data.append(line.split(":"))
            return data

        result = benchmark(mock_file_processing)
        assert len(result) == 100
        assert all(len(row) == 2 for row in result)
