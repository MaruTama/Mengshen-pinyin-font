"""Tests for version utility functions."""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from refactored.utils.version_utils import get_project_version, parse_version_to_float


class TestGetProjectVersion:
    """Test get_project_version function."""

    def test_get_project_version_from_pyproject_toml(self) -> None:
        """Test that version is loaded from pyproject.toml."""
        version = get_project_version()
        assert version == "2.0.0"
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_project_version_with_mock_content(self) -> None:
        """Test version parsing from mock pyproject.toml content."""
        mock_content = """
[project]
name = "test-project"
version = "1.5.3"
description = "Test project"
"""

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=mock_content):
                version = get_project_version()
                assert version == "1.5.3"

    def test_get_project_version_fallback_when_file_not_found(self) -> None:
        """Test fallback behavior when pyproject.toml is not found."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch(
                "importlib.metadata.version",
                side_effect=ModuleNotFoundError("Not installed"),
            ):
                version = get_project_version()
                assert version == "2.0.0"

    def test_get_project_version_fallback_when_parsing_fails(self) -> None:
        """Test fallback behavior when version parsing fails."""
        mock_content = """
[project]
name = "test"
# No version field
"""

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=mock_content):
                with patch(
                    "importlib.metadata.version",
                    side_effect=ModuleNotFoundError("Not installed"),
                ):
                    version = get_project_version()
                    assert version == "2.0.0"


class TestParseVersionToFloat:
    """Test parse_version_to_float function."""

    def test_parse_version_to_float_semantic_version(self) -> None:
        """Test parsing semantic version strings."""
        assert parse_version_to_float("2.0.0") == 2.0
        assert parse_version_to_float("1.4.2") == 1.4
        assert parse_version_to_float("3.14.159") == 3.14

    def test_parse_version_to_float_simple_version(self) -> None:
        """Test parsing simple version strings."""
        assert parse_version_to_float("1.04") == 1.04
        assert parse_version_to_float("2.5") == 2.5

    def test_parse_version_to_float_single_number(self) -> None:
        """Test parsing single number versions."""
        assert parse_version_to_float("3") == 3.0
        assert parse_version_to_float("1") == 1.0

    def test_parse_version_to_float_invalid_input(self) -> None:
        """Test parsing invalid version strings."""
        assert parse_version_to_float("invalid") == 1.0
        assert parse_version_to_float("") == 1.0
        assert parse_version_to_float("abc.def") == 1.0

    def test_parse_version_to_float_edge_cases(self) -> None:
        """Test parsing edge case version strings."""
        assert parse_version_to_float("0.0.1") == 0.0
        assert parse_version_to_float("10.20.30") == 10.20
        assert parse_version_to_float("1.0") == 1.0


class TestVersionUtilsIntegration:
    """Test integration between version utility functions."""

    def test_integration_get_and_parse_version(self) -> None:
        """Test integration between get_project_version and parse_version_to_float."""
        version_str = get_project_version()
        version_float = parse_version_to_float(version_str)

        assert isinstance(version_str, str)
        assert isinstance(version_float, float)
        assert version_float > 0.0

    def test_integration_consistent_behavior(self) -> None:
        """Test that both functions handle the same input consistently."""
        test_version = "2.0.0"

        # Mock get_project_version to return test_version
        with patch("pathlib.Path.exists", return_value=True):
            with patch(
                "pathlib.Path.read_text", return_value=f'version = "{test_version}"'
            ):
                version_str = get_project_version()
                version_float = parse_version_to_float(version_str)

                assert version_str == test_version
                assert version_float == 2.0
